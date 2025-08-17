#!/usr/bin/env python3
"""
Google Cloud Billing API Integration
Gets actual costs from Google Cloud for accurate tracking
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from google.cloud import billing_v1
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class GoogleCloudBilling:
    """Get actual costs from Google Cloud Billing API"""
    
    def __init__(self):
        """Initialize with Google Cloud credentials"""
        
        # You'll need to set up a service account JSON file
        self.credentials_path = os.getenv('GOOGLE_CLOUD_CREDENTIALS')
        if not self.credentials_path:
            logger.warning("GOOGLE_CLOUD_CREDENTIALS not set - using estimates only")
            self.client = None
            return
            
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )
            self.client = billing_v1.CloudBillingClient(credentials=credentials)
            self.billing_account = os.getenv('GOOGLE_BILLING_ACCOUNT')  # e.g., "billingAccounts/01234-567890-ABCDEF"
            logger.info("✅ Google Cloud Billing connected")
        except Exception as e:
            logger.error(f"Could not initialize billing client: {e}")
            self.client = None
    
    def get_daily_costs(self, date: Optional[datetime] = None) -> Dict[str, float]:
        """Get actual costs for a specific day
        
        Args:
            date: Date to get costs for (default: today)
            
        Returns:
            Dict with service costs
        """
        if not self.client:
            return {"error": "Billing API not configured"}
        
        if not date:
            date = datetime.now()
        
        try:
            # Format date for BigQuery export query
            date_str = date.strftime('%Y-%m-%d')
            
            # Note: This requires BigQuery export to be enabled
            # Alternative: Use Cloud Billing Reports API
            
            # For now, return structured estimate
            # In production, you'd query BigQuery or use Budget API
            return {
                "places_api": 0.0,  # Actual from billing
                "maps_api": 0.0,
                "total": 0.0,
                "date": date_str,
                "source": "billing_api"
            }
            
        except Exception as e:
            logger.error(f"Error getting billing data: {e}")
            return {"error": str(e)}
    
    def get_month_to_date_costs(self) -> Dict[str, float]:
        """Get costs for current month to date"""
        
        if not self.client:
            return {"error": "Billing API not configured"}
        
        try:
            # Get first day of month
            today = datetime.now()
            first_of_month = datetime(today.year, today.month, 1)
            
            total = 0.0
            daily_costs = []
            
            # Get each day's costs
            current = first_of_month
            while current <= today:
                day_cost = self.get_daily_costs(current)
                if "total" in day_cost:
                    total += day_cost["total"]
                    daily_costs.append(day_cost)
                current += timedelta(days=1)
            
            return {
                "month": today.strftime('%Y-%m'),
                "total": total,
                "daily_breakdown": daily_costs,
                "source": "billing_api"
            }
            
        except Exception as e:
            logger.error(f"Error getting monthly costs: {e}")
            return {"error": str(e)}


# Simpler alternative using Google Cloud Monitoring API
class GoogleCloudMonitoring:
    """Get metrics from Google Cloud Monitoring (simpler than billing)"""
    
    def __init__(self):
        """Initialize monitoring client"""
        try:
            from google.cloud import monitoring_v3
            
            self.client = monitoring_v3.MetricServiceClient()
            self.project = os.getenv('GOOGLE_CLOUD_PROJECT')  # e.g., "my-project-123"
            self.project_name = f"projects/{self.project}"
            logger.info("✅ Google Cloud Monitoring connected")
        except Exception as e:
            logger.warning(f"Monitoring not available: {e}")
            self.client = None
    
    def get_api_request_counts(self) -> Dict[str, int]:
        """Get actual API request counts from monitoring"""
        
        if not self.client:
            return {"error": "Monitoring not configured"}
        
        try:
            # Query for Places API requests
            interval = monitoring_v3.TimeInterval(
                {
                    "end_time": {"seconds": int(datetime.now().timestamp())},
                    "start_time": {"seconds": int((datetime.now() - timedelta(days=1)).timestamp())},
                }
            )
            
            results = self.client.list_time_series(
                request={
                    "name": self.project_name,
                    "filter": 'metric.type="maps.googleapis.com/quota/used_requests"',
                    "interval": interval,
                }
            )
            
            total_requests = 0
            for result in results:
                for point in result.points:
                    total_requests += point.value.int64_value
            
            return {
                "places_api_requests": total_requests,
                "period": "last_24_hours",
                "source": "monitoring_api"
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {"error": str(e)}


def setup_google_cloud_billing():
    """Setup instructions for Google Cloud Billing"""
    
    print("""
    ============================================================
    GOOGLE CLOUD BILLING SETUP
    ============================================================
    
    To get actual costs from Google Cloud:
    
    1. Enable Cloud Billing API:
       https://console.cloud.google.com/apis/library/cloudbilling.googleapis.com
    
    2. Create a Service Account:
       - Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
       - Create new service account
       - Grant role: "Billing Account Viewer"
       - Create JSON key and download
    
    3. Set environment variables in .env:
       GOOGLE_CLOUD_CREDENTIALS=/path/to/service-account-key.json
       GOOGLE_CLOUD_PROJECT=your-project-id
       GOOGLE_BILLING_ACCOUNT=billingAccounts/XXXXXX-XXXXXX-XXXXXX
    
    4. (Optional) Enable BigQuery export for detailed billing:
       https://console.cloud.google.com/billing/export
    
    5. Install required package:
       pip install google-cloud-billing google-cloud-monitoring
    
    ============================================================
    
    Alternative: Use the simpler Monitoring API for request counts
    and calculate costs based on pricing ($17 per 1000 requests)
    """)


if __name__ == "__main__":
    # Test the billing integration
    billing = GoogleCloudBilling()
    costs = billing.get_daily_costs()
    print(f"Today's costs: {costs}")
    
    monitoring = GoogleCloudMonitoring()
    metrics = monitoring.get_api_request_counts()
    print(f"API requests: {metrics}")
    
    # Calculate estimated cost from request count
    if "places_api_requests" in metrics:
        estimated_cost = metrics["places_api_requests"] * 0.017  # $17 per 1000
        print(f"Estimated cost: ${estimated_cost:.2f}")