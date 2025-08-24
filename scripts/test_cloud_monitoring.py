#!/usr/bin/env python3
"""
Test Google Cloud Monitoring Integration
Shows actual API usage vs estimated costs
"""

import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.cost_tracker import CostTracker, CLOUD_MONITORING_AVAILABLE

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_cloud_monitoring():
    """Test Cloud Monitoring API integration"""
    
    print("\n" + "="*60)
    print("Google Cloud Monitoring - API Usage Test")
    print("="*60)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Check if Cloud Monitoring is available
    if not CLOUD_MONITORING_AVAILABLE:
        print("❌ Google Cloud Monitoring is not available")
        print("   Please install: pip install google-cloud-monitoring")
        print("   And set up Google Cloud credentials")
        return
    
    print("✅ Google Cloud Monitoring library is available")
    print()
    
    # Initialize cost tracker
    try:
        tracker = CostTracker(use_cloud_monitoring=True)
        print("✅ Cost tracker initialized with Cloud Monitoring")
    except Exception as e:
        print(f"❌ Failed to initialize cost tracker: {e}")
        return
    
    # Check if Cloud Monitoring is actually connected
    if not tracker.cloud_monitor:
        print("⚠️  Cloud Monitoring not connected - using estimate-based tracking")
        print("   Make sure:")
        print("   1. Cloud Monitoring API is enabled in Google Cloud Console")
        print("   2. Application Default Credentials are configured")
        print("   3. Your service account has monitoring.timeSeries.list permission")
        return
    
    print("✅ Cloud Monitoring connected successfully")
    print()
    
    # Get actual vs estimated comparison
    print("=== Actual vs Estimated Usage ===")
    try:
        comparison = tracker.get_actual_vs_estimated()
        
        # Display API calls breakdown
        api_calls = comparison.get('api_calls', {})
        if api_calls:
            print("\nAPI Calls Today (from Cloud Monitoring):")
            for api_type, count in api_calls.items():
                print(f"  {api_type:20}: {count:,} calls")
            print(f"  {'Total':20}: {comparison['total_calls']:,} calls")
        else:
            print("\nNo API calls detected in Cloud Monitoring")
        
        print()
        print("Cost Analysis:")
        print(f"  Estimated cost (local tracking): ${comparison['estimated_cost']:.2f}")
        print(f"  Actual cost (Cloud Monitoring):  ${comparison['actual_cost']:.2f}")
        
        if comparison['estimated_cost'] > 0:
            savings = comparison['estimated_cost'] - comparison['actual_cost']
            print(f"  Difference:                      ${savings:.2f}")
            
            if comparison['savings_percent'] > 0:
                print(f"  Savings from estimates:          {comparison['savings_percent']:.1f}%")
        
        print()
        print("Budget Status:")
        daily_remaining = tracker.DAILY_LIMIT - comparison['actual_cost']
        print(f"  Daily limit:                     ${tracker.DAILY_LIMIT:.2f}")
        print(f"  Used today:                      ${comparison['actual_cost']:.2f}")
        print(f"  Remaining:                       ${daily_remaining:.2f}")
        
        # Get usage stats from local tracking
        print("\n=== Local Tracking Stats ===")
        stats = tracker.get_usage_stats(days=1)
        
        print(f"Cached API calls saved: {stats['cache_hits']:,}")
        print(f"Cache hit rate:         {stats['cache_rate']:.1f}%")
        print(f"Estimated savings:      ${stats['estimated_savings']:.2f}")
        
        if stats['by_type']:
            print("\nBreakdown by API type (local tracking):")
            for item in stats['by_type']:
                print(f"  {item['type']:20}: {item['count']:,} calls (${item['cost']:.2f})")
        
    except Exception as e:
        print(f"❌ Error getting usage data: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("Notes:")
    print("- Cloud Monitoring data may have a few minutes delay")
    print("- Free tier and discounts are not reflected in retail pricing")
    print("- Actual costs may be lower due to Google Cloud credits")
    print("="*60 + "\n")


def check_credentials():
    """Check if Google Cloud credentials are configured"""
    try:
        import google.auth
        credentials, project = google.auth.default()
        print(f"✅ Google Cloud credentials found for project: {project}")
        return True
    except Exception as e:
        print(f"❌ Google Cloud credentials not configured: {e}")
        print("\nTo set up credentials:")
        print("1. Install gcloud CLI: https://cloud.google.com/sdk/install")
        print("2. Run: gcloud auth application-default login")
        print("3. Or set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        return False


def main():
    """Main execution"""
    print("\n🔍 Checking Google Cloud setup...")
    
    if not check_credentials():
        return
    
    test_cloud_monitoring()


if __name__ == "__main__":
    main()