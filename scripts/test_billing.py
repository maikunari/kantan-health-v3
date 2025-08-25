#!/usr/bin/env python3
"""
Test Google Cloud Billing API integration
Verifies actual costs vs estimates and identifies discrepancies
"""

import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.google_billing_tracker import GoogleBillingTracker
from src.core.cost_tracker import CostTracker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_billing_tracker():
    """Test the Google Billing API tracker"""
    logger.info("="*60)
    logger.info("🔍 TESTING GOOGLE CLOUD BILLING API")
    logger.info("="*60)
    
    try:
        # Initialize billing tracker
        tracker = GoogleBillingTracker()
        
        # Get billing account info
        logger.info("\n📊 Billing Account:")
        account = tracker.get_billing_account()
        if account:
            logger.info(f"  Account: {account}")
        else:
            logger.warning("  No billing account found or insufficient permissions")
        
        # Get today's actual costs
        logger.info("\n💰 Today's Costs:")
        cost, usage = tracker.get_today_costs()
        logger.info(f"  Actual cost from Google Cloud: ${cost:.2f}")
        
        if usage:
            logger.info(f"  API usage breakdown:")
            for api_type, count in usage.items():
                if count > 0:
                    api_cost = count * tracker.GOOGLE_MAPS_PRICING.get(api_type, 0)
                    logger.info(f"    - {api_type}: {count} calls (${api_cost:.2f})")
        
        # Get monthly costs
        logger.info("\n📅 Monthly Costs:")
        monthly = tracker.get_month_costs()
        logger.info(f"  Monthly billable cost: ${monthly:.2f}")
        
        if monthly == 0:
            logger.info(f"  ✅ Within free tier (${tracker.FREE_TIER_CREDITS} credit)")
        
        # Get quota status
        logger.info("\n📈 API Quota Status:")
        quotas = tracker.get_api_quota_status()
        for api, status in quotas.items():
            logger.info(f"  {api}:")
            logger.info(f"    Current: {status['current']:,} / {status['limit']:,}")
            logger.info(f"    Usage: {status['percentage']:.1f}%")
            logger.info(f"    Remaining: {status['remaining']:,}")
        
        return cost, usage
        
    except ImportError as e:
        logger.error(f"❌ Missing dependencies: {e}")
        logger.info("Run: pip install google-cloud-billing google-cloud-monitoring")
        return 0, {}
        
    except Exception as e:
        logger.error(f"❌ Error testing billing tracker: {e}")
        return 0, {}


def compare_with_estimates():
    """Compare actual costs with system estimates"""
    logger.info("\n" + "="*60)
    logger.info("🔍 COMPARING ACTUAL VS ESTIMATED COSTS")
    logger.info("="*60)
    
    try:
        # Get actual costs
        actual_cost, usage = test_billing_tracker()
        
        # Get estimated costs from system
        cost_tracker = CostTracker()
        estimated_daily = cost_tracker._get_daily_cost()
        estimated_monthly = cost_tracker._get_monthly_cost()
        
        logger.info("\n📊 Cost Comparison:")
        logger.info(f"  Daily:")
        logger.info(f"    System estimate: ${estimated_daily:.2f}")
        logger.info(f"    Google Cloud actual: ${actual_cost:.2f}")
        
        if estimated_daily > 0:
            discrepancy = ((estimated_daily - actual_cost) / estimated_daily) * 100
            if abs(discrepancy) > 10:
                logger.warning(f"    ⚠️  Discrepancy: {discrepancy:.1f}%")
                if discrepancy > 0:
                    logger.info(f"    System is OVERESTIMATING costs")
                else:
                    logger.info(f"    System is UNDERESTIMATING costs")
            else:
                logger.info(f"    ✅ Estimates are accurate (within 10%)")
        
        logger.info(f"  Monthly:")
        logger.info(f"    System estimate: ${estimated_monthly:.2f}")
        
        # Check budget limits
        logger.info("\n🎯 Budget Status:")
        logger.info(f"  Daily limit: ${cost_tracker.daily_limit:.2f}")
        logger.info(f"  Daily used: ${actual_cost:.2f} ({(actual_cost/cost_tracker.daily_limit)*100:.1f}%)")
        
        if actual_cost < cost_tracker.daily_limit:
            logger.info(f"  ✅ Within daily budget (${cost_tracker.daily_limit - actual_cost:.2f} remaining)")
        else:
            logger.warning(f"  ⚠️  Over daily budget by ${actual_cost - cost_tracker.daily_limit:.2f}")
        
        logger.info(f"\n  Monthly limit: ${cost_tracker.monthly_limit:.2f}")
        logger.info(f"  Monthly used: ${estimated_monthly:.2f} ({(estimated_monthly/cost_tracker.monthly_limit)*100:.1f}%)")
        
        # Recommendations
        logger.info("\n💡 Recommendations:")
        if estimated_daily > actual_cost * 1.5:
            logger.info("  • System is significantly overestimating costs")
            logger.info("  • Consider adjusting cost calculation factors")
            logger.info("  • You may have free tier credits or promotional pricing")
        elif actual_cost > estimated_daily * 1.5:
            logger.info("  • System is underestimating actual costs")
            logger.info("  • Review API pricing tiers")
            logger.info("  • Check for additional API calls not being tracked")
        else:
            logger.info("  • Cost tracking is reasonably accurate")
            logger.info("  • Continue monitoring for changes")
        
    except Exception as e:
        logger.error(f"❌ Error comparing costs: {e}")


def main():
    """Main execution"""
    logger.info("🚀 Google Cloud Billing API Test")
    logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run comparison
    compare_with_estimates()
    
    logger.info("\n" + "="*60)
    logger.info("✅ Test complete")
    logger.info("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())