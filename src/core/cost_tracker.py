#!/usr/bin/env python3
"""
API Cost Tracking and Budget Management
Monitors API usage and enforces budget limits
"""

import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)

# Try to import Google Cloud Monitoring
try:
    from google.cloud import monitoring_v3
    from google.api_core import exceptions
    CLOUD_MONITORING_AVAILABLE = True
except ImportError:
    CLOUD_MONITORING_AVAILABLE = False
    logger.debug("Google Cloud Monitoring not available - using estimate-based tracking")


class CloudMonitoringCostTracker:
    """Track actual API usage using Google Cloud Monitoring"""
    
    # Calibrated Google Places API costs (after testing)
    ACTUAL_COSTS = {
        'text_search': 0.032,      # Text Search
        'nearby_search': 0.032,    # Nearby Search  
        'place_details': 0.017,    # Place Details
    }
    
    def __init__(self, project_id: str = None):
        """Initialize Cloud Monitoring client
        
        Args:
            project_id: Google Cloud project ID (uses default if None)
        """
        if not CLOUD_MONITORING_AVAILABLE:
            raise ImportError("Google Cloud Monitoring is not available. Install google-cloud-monitoring.")
        
        self.client = monitoring_v3.MetricServiceClient()
        
        # Get project ID from environment or use provided
        if project_id:
            self.project_id = project_id
        else:
            import google.auth
            _, self.project_id = google.auth.default()
        
        self.project_name = f"projects/{self.project_id}"
        logger.info(f"✅ Cloud Monitoring initialized for project: {self.project_id}")
    
    def get_actual_api_calls_today(self) -> Dict[str, int]:
        """Get actual API calls made today from Cloud Monitoring
        
        Returns:
            Dictionary with API call counts by type
        """
        results = {}
        
        # Define the metrics to query
        metrics = {
            'text_search': 'maps.googleapis.com/quotas/text_search_requests/usage',
            'nearby_search': 'maps.googleapis.com/quotas/nearby_search_requests/usage',
            'place_details': 'maps.googleapis.com/quotas/place_details_requests/usage',
        }
        
        # Calculate time interval for last 24 hours
        now = datetime.utcnow()
        start_time = now - timedelta(hours=24)
        
        interval = monitoring_v3.TimeInterval(
            {
                "end_time": {"seconds": int(now.timestamp())},
                "start_time": {"seconds": int(start_time.timestamp())},
            }
        )
        
        for api_type, metric_type in metrics.items():
            try:
                # Build the request
                request = monitoring_v3.ListTimeSeriesRequest(
                    name=self.project_name,
                    filter=f'metric.type="{metric_type}"',
                    interval=interval,
                    view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                )
                
                # Execute the request
                page_result = self.client.list_time_series(request=request)
                
                # Sum up the values
                total_calls = 0
                for time_series in page_result:
                    for point in time_series.points:
                        total_calls += point.value.int64_value
                
                results[api_type] = total_calls
                logger.debug(f"Cloud Monitoring - {api_type}: {total_calls} calls")
                
            except exceptions.NotFound:
                logger.debug(f"Metric {metric_type} not found - may not have any usage yet")
                results[api_type] = 0
            except Exception as e:
                logger.warning(f"Error querying {metric_type}: {e}")
                results[api_type] = 0
        
        return results
    
    def get_actual_cost_today(self) -> float:
        """Calculate actual cost based on real API usage
        
        Returns:
            Total cost for today based on actual usage
        """
        api_calls = self.get_actual_api_calls_today()
        
        total_cost = 0.0
        for api_type, count in api_calls.items():
            cost_per_call = self.ACTUAL_COSTS.get(api_type, 0)
            api_cost = count * cost_per_call
            total_cost += api_cost
            
            if count > 0:
                logger.debug(f"{api_type}: {count} calls × ${cost_per_call:.3f} = ${api_cost:.2f}")
        
        return round(total_cost, 2)
    
    def get_remaining_budget(self, daily_limit: float = 10.0) -> float:
        """Get remaining daily budget based on actual usage
        
        Args:
            daily_limit: Daily budget limit in USD
            
        Returns:
            Remaining budget for today
        """
        actual_cost = self.get_actual_cost_today()
        remaining = daily_limit - actual_cost
        return round(remaining, 2)
    
    def get_usage_comparison(self, estimated_cost: float) -> Dict[str, any]:
        """Compare actual usage with estimates
        
        Args:
            estimated_cost: Estimated cost from local tracking
            
        Returns:
            Comparison data
        """
        actual_cost = self.get_actual_cost_today()
        api_calls = self.get_actual_api_calls_today()
        total_calls = sum(api_calls.values())
        
        # Calculate savings
        retail_cost = actual_cost  # For now, same as actual
        savings_percent = 0.0
        if estimated_cost > 0:
            savings_percent = ((estimated_cost - actual_cost) / estimated_cost) * 100
        
        return {
            'api_calls': api_calls,
            'total_calls': total_calls,
            'actual_cost': actual_cost,
            'estimated_cost': estimated_cost,
            'savings_percent': round(savings_percent, 1),
            'retail_cost': retail_cost,
        }


class CostTracker:
    """Track API costs and enforce budget limits"""
    
    # Google Places API pricing (as of 2024)
    COSTS = {
        'place_search': 0.032,      # Text Search
        'place_details': 0.017,     # Place Details
        'atmosphere_data': 0.005,   # Atmosphere Data fields
        'contact_data': 0.003,      # Contact Data fields
        'basic_data': 0.00,         # Basic Data fields (free)
        'photos': 0.007,            # Place Photo
        'autocomplete': 0.00283,    # Autocomplete per request
        'query_autocomplete': 0.00283,  # Query Autocomplete
        'nearby_search': 0.032      # Nearby Search
    }
    
    def __init__(self, daily_limit_usd: float = None, 
                 monthly_limit_usd: float = None,
                 db_path: str = 'cache/api_usage.db',
                 use_cloud_monitoring: bool = True,
                 project_id: str = None):
        """Initialize cost tracker
        
        Args:
            daily_limit_usd: Daily spending limit in USD (uses env var if not provided)
            monthly_limit_usd: Monthly spending limit in USD (uses env var if not provided)
            db_path: Path to SQLite database
            use_cloud_monitoring: Try to use Cloud Monitoring for actual costs
            project_id: Google Cloud project ID (for Cloud Monitoring)
        """
        # Get limits from environment variables if not provided
        if daily_limit_usd is None:
            daily_limit_usd = float(os.getenv('DAILY_COST_LIMIT', '10.0'))
        if monthly_limit_usd is None:
            monthly_limit_usd = float(os.getenv('MONTHLY_COST_LIMIT', '85.0'))
            
        self.DAILY_LIMIT = self.daily_limit = daily_limit_usd
        self.MONTHLY_LIMIT = self.monthly_limit = monthly_limit_usd
        self.db_path = db_path
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        # Try to initialize Cloud Monitoring and Billing
        self.cloud_monitor = None
        self.billing_tracker = None
        
        # First try Google Billing API for most accurate costs
        try:
            from .google_billing_tracker import GoogleBillingTracker
            self.billing_tracker = GoogleBillingTracker(project_id)
            logger.info(f"✅ Google Billing API enabled for accurate cost tracking")
        except Exception as e:
            logger.debug(f"Google Billing API not available: {e}")
        
        # Fall back to Cloud Monitoring if available
        if not self.billing_tracker and use_cloud_monitoring and CLOUD_MONITORING_AVAILABLE:
            try:
                self.cloud_monitor = CloudMonitoringCostTracker(project_id)
                logger.info(f"✅ Cloud Monitoring enabled for real-time cost tracking")
            except Exception as e:
                logger.warning(f"Could not initialize Cloud Monitoring: {e}")
                logger.info("Falling back to estimate-based tracking")
        
        logger.info(f"✅ Cost tracker initialized (Daily: ${daily_limit_usd}, Monthly: ${monthly_limit_usd})")
    
    def _init_db(self):
        """Initialize SQLite database schema"""
        with sqlite3.connect(self.db_path) as conn:
            # API usage log
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_type TEXT NOT NULL,
                    cost REAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    place_id TEXT,
                    search_query TEXT,
                    cached BOOLEAN DEFAULT 0
                )
            ''')
            
            # Daily summaries for quick lookups
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_summary (
                    date DATE PRIMARY KEY,
                    total_cost REAL NOT NULL,
                    request_count INTEGER NOT NULL,
                    cache_hits INTEGER DEFAULT 0,
                    last_updated TIMESTAMP NOT NULL
                )
            ''')
            
            # Create indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_usage_timestamp ON api_usage(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_usage_type ON api_usage(request_type)')
            
            conn.commit()
    
    def can_make_request(self, request_type: str, 
                        estimated_count: int = 1) -> Tuple[bool, Optional[str]]:
        """Check if request is within budget limits
        
        Args:
            request_type: Type of API request
            estimated_count: Number of requests (for batch operations)
            
        Returns:
            Tuple of (allowed, reason_if_not)
        """
        cost_per_request = self.COSTS.get(request_type, 0)
        estimated_cost = cost_per_request * estimated_count
        
        # Get current usage
        daily_cost = self._get_daily_cost()
        monthly_cost = self._get_monthly_cost()
        
        # Check daily limit
        if daily_cost + estimated_cost > self.daily_limit:
            remaining = self.daily_limit - daily_cost
            reason = f"Daily budget limit exceeded. Used: ${daily_cost:.2f}, Limit: ${self.daily_limit:.2f}, Remaining: ${remaining:.2f}"
            logger.warning(f"❌ {reason}")
            return False, reason
        
        # Check monthly limit
        if monthly_cost + estimated_cost > self.monthly_limit:
            remaining = self.monthly_limit - monthly_cost
            reason = f"Monthly budget limit exceeded. Used: ${monthly_cost:.2f}, Limit: ${self.monthly_limit:.2f}, Remaining: ${remaining:.2f}"
            logger.warning(f"❌ {reason}")
            return False, reason
        
        return True, None
    
    def log_request(self, request_type: str, place_id: str = None,
                   search_query: str = None, cached: bool = False) -> None:
        """Log an API request
        
        Args:
            request_type: Type of API request
            place_id: Google Place ID (if applicable)
            search_query: Search query (if applicable)
            cached: Whether this was served from cache
        """
        cost = self.COSTS.get(request_type, 0) if not cached else 0
        timestamp = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO api_usage 
                (request_type, cost, timestamp, place_id, search_query, cached)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (request_type, cost, timestamp.isoformat(), 
                  place_id, search_query, cached))
            
            # Update daily summary
            date_str = timestamp.date().isoformat()
            conn.execute('''
                INSERT INTO daily_summary (date, total_cost, request_count, cache_hits, last_updated)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    total_cost = total_cost + ?,
                    request_count = request_count + 1,
                    cache_hits = cache_hits + ?,
                    last_updated = ?
            ''', (date_str, cost, 1 if cached else 0, timestamp.isoformat(),
                  cost, 1 if cached else 0, timestamp.isoformat()))
            
            conn.commit()
        
        if not cached:
            logger.debug(f"💰 Logged {request_type}: ${cost:.3f}")
        else:
            logger.debug(f"✅ Cache hit for {request_type} (saved ${cost:.3f})")
    
    def _get_daily_cost(self) -> float:
        """Get today's total cost
        
        Tries billing API first, then Cloud Monitoring, then falls back to estimates
        """
        # Try Google Billing API first for most accurate data
        if self.billing_tracker:
            try:
                actual_cost, _ = self.billing_tracker.get_today_costs()
                if actual_cost > 0:
                    logger.debug(f"Using actual cost from Billing API: ${actual_cost:.2f}")
                    return actual_cost
            except Exception as e:
                logger.debug(f"Could not get billing data: {e}")
        
        # Try Cloud Monitoring next
        if self.cloud_monitor:
            try:
                actual_cost = self.cloud_monitor.get_actual_cost_today()
                if actual_cost > 0:
                    logger.debug(f"Using actual cost from Cloud Monitoring: ${actual_cost:.2f}")
                    return actual_cost
            except Exception as e:
                logger.debug(f"Could not get monitoring data: {e}")
        
        # Fall back to estimate from database
        today = datetime.now().date().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT total_cost FROM daily_summary 
                WHERE date = ?
            ''', (today,))
            
            row = cursor.fetchone()
            estimated = row[0] if row else 0.0
            logger.debug(f"Using estimated cost from database: ${estimated:.2f}")
            return estimated
    
    def _get_monthly_cost(self) -> float:
        """Get current month's total cost
        
        Tries billing API first, then falls back to estimates
        """
        # Try Google Billing API first
        if self.billing_tracker:
            try:
                monthly_cost = self.billing_tracker.get_month_costs()
                if monthly_cost >= 0:  # Can be 0 if within free tier
                    logger.debug(f"Using actual monthly cost from Billing API: ${monthly_cost:.2f}")
                    return monthly_cost
            except Exception as e:
                logger.debug(f"Could not get monthly billing data: {e}")
        
        # Fall back to estimate from database
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT SUM(cost) FROM api_usage 
                WHERE timestamp >= ?
            ''', (start_of_month.isoformat(),))
            
            result = cursor.fetchone()[0]
            estimated = result if result else 0.0
            logger.debug(f"Using estimated monthly cost from database: ${estimated:.2f}")
            return estimated
    
    def get_usage_stats(self, days: int = 30) -> Dict[str, any]:
        """Get usage statistics
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with usage stats
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Total stats
            total_stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(cost) as total_cost,
                    SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END) as cache_hits
                FROM api_usage 
                WHERE timestamp >= ?
            ''', (cutoff_date,)).fetchone()
            
            # By request type
            by_type = conn.execute('''
                SELECT 
                    request_type,
                    COUNT(*) as count,
                    SUM(cost) as total_cost,
                    SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END) as cache_hits
                FROM api_usage 
                WHERE timestamp >= ?
                GROUP BY request_type
                ORDER BY total_cost DESC
            ''', (cutoff_date,)).fetchall()
            
            # Daily breakdown
            daily = conn.execute('''
                SELECT date, total_cost, request_count, cache_hits
                FROM daily_summary
                WHERE date >= date(?)
                ORDER BY date DESC
                LIMIT 7
            ''', (cutoff_date,)).fetchall()
        
        # Calculate savings from cache
        total_requests = total_stats[0] or 0
        cache_hits = total_stats[2] or 0
        cache_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate potential cost without cache
        savings = sum(
            self.COSTS.get(row[0], 0) * row[3]  # cost * cache_hits
            for row in by_type
        )
        
        return {
            'period_days': days,
            'total_requests': total_requests,
            'total_cost': round(total_stats[1] or 0, 2),
            'cache_hits': cache_hits,
            'cache_rate': round(cache_rate, 1),
            'estimated_savings': round(savings, 2),
            'by_type': [
                {
                    'type': row[0],
                    'count': row[1],
                    'cost': round(row[2], 2),
                    'cache_hits': row[3],
                    'avg_cost': round(row[2] / row[1], 3) if row[1] > 0 else 0
                }
                for row in by_type
            ],
            'daily': [
                {
                    'date': row[0],
                    'cost': round(row[1], 2),
                    'requests': row[2],
                    'cache_hits': row[3]
                }
                for row in daily
            ],
            'current_day_cost': round(self._get_daily_cost(), 2),
            'current_month_cost': round(self._get_monthly_cost(), 2),
            'daily_limit': self.daily_limit,
            'monthly_limit': self.monthly_limit,
            'daily_remaining': round(self.daily_limit - self._get_daily_cost(), 2),
            'monthly_remaining': round(self.monthly_limit - self._get_monthly_cost(), 2)
        }
    
    def get_cost_breakdown(self) -> Dict[str, float]:
        """Get current month's cost breakdown by type"""
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        with sqlite3.connect(self.db_path) as conn:
            breakdown = conn.execute('''
                SELECT request_type, SUM(cost) as total
                FROM api_usage
                WHERE timestamp >= ? AND cached = 0
                GROUP BY request_type
                ORDER BY total DESC
            ''', (start_of_month.isoformat(),)).fetchall()
        
        return {row[0]: round(row[1], 2) for row in breakdown}
    
    def get_daily_usage(self) -> float:
        """Get today's total API usage cost
        
        Returns:
            Total cost for today
        """
        estimated_cost = self._get_daily_cost()
        
        # Try to get actual cost from Cloud Monitoring
        if self.cloud_monitor:
            try:
                actual_cost = self.cloud_monitor.get_actual_cost_today()
                logger.info(f"📊 Cloud Monitoring - Actual: ${actual_cost:.2f}, Estimated: ${estimated_cost:.2f}")
                # Use the higher value to be conservative
                return max(actual_cost, estimated_cost)
            except Exception as e:
                logger.debug(f"Cloud Monitoring unavailable: {e}")
        
        return estimated_cost
    
    def get_monthly_usage(self) -> float:
        """Get this month's total API usage cost
        
        Returns:
            Total cost for current month
        """
        return self._get_monthly_cost()
    
    def get_actual_vs_estimated(self) -> Dict[str, any]:
        """Get comparison of actual vs estimated costs
        
        Returns:
            Dictionary with actual and estimated costs
        """
        estimated_cost = self._get_daily_cost()
        
        if self.cloud_monitor:
            try:
                comparison = self.cloud_monitor.get_usage_comparison(estimated_cost)
                return comparison
            except Exception as e:
                logger.warning(f"Could not get Cloud Monitoring data: {e}")
        
        return {
            'api_calls': {},
            'total_calls': 0,
            'actual_cost': estimated_cost,
            'estimated_cost': estimated_cost,
            'savings_percent': 0.0,
            'retail_cost': estimated_cost,
            'cloud_monitoring_available': False
        }