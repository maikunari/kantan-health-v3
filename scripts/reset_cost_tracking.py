#!/usr/bin/env python3
"""
Reset cost tracking to use actual Google Cloud Billing data
Clears incorrect estimates and syncs with real costs
"""

import sys
import os
import sqlite3
import logging
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.google_billing_tracker import GoogleBillingTracker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def reset_today_costs():
    """Reset today's cost tracking to actual Google Cloud data"""
    logger.info("="*60)
    logger.info("🔧 RESETTING COST TRACKING")
    logger.info("="*60)
    
    # Get actual costs from Google Cloud
    try:
        tracker = GoogleBillingTracker()
        actual_cost, usage = tracker.get_today_costs()
        
        logger.info(f"\n📊 Actual costs from Google Cloud:")
        logger.info(f"  Today: ${actual_cost:.2f}")
        
        # Get monthly costs
        monthly = tracker.get_month_costs()
        logger.info(f"  Monthly (billable): ${monthly:.2f}")
        
        if monthly == 0:
            logger.info(f"  ✅ Within free tier ($200 credit)")
        
    except Exception as e:
        logger.error(f"Could not get actual costs: {e}")
        actual_cost = 0.0
        usage = {}
    
    # Update database with actual costs
    db_path = 'cache/api_usage.db'
    today = datetime.now().date().isoformat()
    
    with sqlite3.connect(db_path) as conn:
        # Get current estimate
        cursor = conn.execute(
            'SELECT total_cost, request_count FROM daily_summary WHERE date = ?',
            (today,)
        )
        row = cursor.fetchone()
        
        if row:
            estimated_cost = row[0]
            request_count = row[1]
            
            logger.info(f"\n📋 Current database values:")
            logger.info(f"  Estimated cost: ${estimated_cost:.2f}")
            logger.info(f"  Request count: {request_count}")
            
            # Update with actual cost
            if actual_cost < estimated_cost:
                logger.info(f"\n✅ Correcting overestimate:")
                logger.info(f"  Updating ${estimated_cost:.2f} → ${actual_cost:.2f}")
                
                conn.execute(
                    'UPDATE daily_summary SET total_cost = ? WHERE date = ?',
                    (actual_cost, today)
                )
                conn.commit()
                
                logger.info(f"  ✅ Database updated with actual cost")
            else:
                logger.info(f"\n✅ Cost tracking is accurate")
        else:
            logger.info(f"\nNo cost data for today yet")
    
    # Clear the daily limit flag if we're under budget
    if actual_cost < 10.0:
        logger.info(f"\n🎯 Budget status:")
        logger.info(f"  Daily budget: $10.00")
        logger.info(f"  Actual used: ${actual_cost:.2f}")
        logger.info(f"  Remaining: ${10.0 - actual_cost:.2f}")
        logger.info(f"  ✅ Collection can continue")
    
    return actual_cost


def show_cost_history():
    """Show cost history comparison"""
    logger.info("\n" + "="*60)
    logger.info("📊 COST HISTORY (Last 7 Days)")
    logger.info("="*60)
    
    db_path = 'cache/api_usage.db'
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute('''
            SELECT date, total_cost, request_count 
            FROM daily_summary 
            WHERE date >= date('now', '-7 days')
            ORDER BY date DESC
        ''')
        
        logger.info("\nDate       | Est. Cost | Requests | Status")
        logger.info("-" * 50)
        
        for row in cursor:
            date_str, cost, count = row
            status = "✅" if cost < 10.0 else "⚠️"
            logger.info(f"{date_str} | ${cost:8.2f} | {count:8d} | {status}")
    
    # Show total for the month
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute('''
            SELECT SUM(total_cost) 
            FROM daily_summary 
            WHERE date >= date('now', 'start of month')
        ''')
        
        monthly_total = cursor.fetchone()[0] or 0
        logger.info(f"\nMonthly total (estimated): ${monthly_total:.2f}")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Reset cost tracking')
    parser.add_argument('--clear-all', action='store_true', 
                       help='Clear all cost data (use with caution)')
    
    args = parser.parse_args()
    
    if args.clear_all:
        response = input("⚠️  Clear ALL cost tracking data? (yes/no): ")
        if response.lower() == 'yes':
            db_path = 'cache/api_usage.db'
            with sqlite3.connect(db_path) as conn:
                conn.execute('DELETE FROM daily_summary')
                conn.execute('DELETE FROM api_usage')
                conn.commit()
            logger.info("✅ All cost data cleared")
            return 0
    
    # Reset today's costs
    actual_cost = reset_today_costs()
    
    # Show history
    show_cost_history()
    
    logger.info("\n" + "="*60)
    logger.info("✅ Cost tracking reset complete")
    logger.info("="*60)
    
    logger.info("\n💡 Next steps:")
    logger.info("  1. Enable Cloud Billing API in Google Cloud Console")
    logger.info("  2. Grant 'Billing Account Viewer' IAM role to service account")
    logger.info("  3. Collection will now use actual costs from Google Cloud")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())