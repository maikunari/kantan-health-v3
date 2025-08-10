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
    
    def __init__(self, daily_limit_usd: float = 10.0, 
                 monthly_limit_usd: float = 85.0,
                 db_path: str = 'cache/api_usage.db'):
        """Initialize cost tracker
        
        Args:
            daily_limit_usd: Daily spending limit in USD
            monthly_limit_usd: Monthly spending limit in USD
            db_path: Path to SQLite database
        """
        self.DAILY_LIMIT = self.daily_limit = daily_limit_usd
        self.MONTHLY_LIMIT = self.monthly_limit = monthly_limit_usd
        self.db_path = db_path
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
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
        """Get today's total cost"""
        today = datetime.now().date().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT total_cost FROM daily_summary 
                WHERE date = ?
            ''', (today,))
            
            row = cursor.fetchone()
            return row[0] if row else 0.0
    
    def _get_monthly_cost(self) -> float:
        """Get current month's total cost"""
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT SUM(cost) FROM api_usage 
                WHERE timestamp >= ?
            ''', (start_of_month.isoformat(),))
            
            result = cursor.fetchone()[0]
            return result if result else 0.0
    
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
        return self._get_daily_cost()
    
    def get_monthly_usage(self) -> float:
        """Get this month's total API usage cost
        
        Returns:
            Total cost for current month
        """
        return self._get_monthly_cost()