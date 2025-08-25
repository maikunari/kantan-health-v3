#!/usr/bin/env python3
"""
Set or view cost limits for API usage
Updates the environment configuration
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv, set_key

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_current_limits():
    """Get current cost limits from environment"""
    load_dotenv('config/.env')
    
    daily = float(os.getenv('DAILY_COST_LIMIT', '10.0'))
    monthly = float(os.getenv('MONTHLY_COST_LIMIT', '85.0'))
    
    return daily, monthly


def set_limits(daily: float = None, monthly: float = None):
    """Set new cost limits in environment file"""
    env_path = 'config/.env'
    
    # Ensure file exists
    Path(env_path).touch()
    
    if daily is not None:
        set_key(env_path, 'DAILY_COST_LIMIT', str(daily))
        logger.info(f"✅ Set daily limit to ${daily:.2f}")
    
    if monthly is not None:
        set_key(env_path, 'MONTHLY_COST_LIMIT', str(monthly))
        logger.info(f"✅ Set monthly limit to ${monthly:.2f}")


def show_current_status():
    """Show current limits and usage"""
    from src.core.cost_tracker import CostTracker
    
    logger.info("="*60)
    logger.info("💰 COST LIMITS AND USAGE")
    logger.info("="*60)
    
    # Get current limits
    daily_limit, monthly_limit = get_current_limits()
    
    logger.info(f"\n📋 Current Limits:")
    logger.info(f"  Daily:   ${daily_limit:.2f}")
    logger.info(f"  Monthly: ${monthly_limit:.2f}")
    
    # Get actual usage
    try:
        tracker = CostTracker()
        daily_used = tracker._get_daily_cost()
        monthly_used = tracker._get_monthly_cost()
        
        logger.info(f"\n📊 Current Usage:")
        logger.info(f"  Today:   ${daily_used:.2f} / ${daily_limit:.2f} ({(daily_used/daily_limit*100):.1f}%)")
        logger.info(f"  Month:   ${monthly_used:.2f} / ${monthly_limit:.2f} ({(monthly_used/monthly_limit*100):.1f}%)")
        
        logger.info(f"\n💵 Remaining Budget:")
        logger.info(f"  Today:   ${daily_limit - daily_used:.2f}")
        logger.info(f"  Month:   ${monthly_limit - monthly_used:.2f}")
        
        # Check if collection is blocked
        if daily_used >= daily_limit:
            logger.warning(f"\n⚠️  Daily limit reached! Collection is blocked.")
        elif monthly_used >= monthly_limit:
            logger.warning(f"\n⚠️  Monthly limit reached! Collection is blocked.")
        else:
            logger.info(f"\n✅ Collection can proceed")
            
    except Exception as e:
        logger.error(f"Could not get usage data: {e}")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage API cost limits')
    parser.add_argument('--daily', type=float, help='Set daily limit in USD')
    parser.add_argument('--monthly', type=float, help='Set monthly limit in USD')
    parser.add_argument('--show', action='store_true', help='Show current limits and usage')
    
    args = parser.parse_args()
    
    if args.daily or args.monthly:
        # Set new limits
        logger.info("🔧 Setting new cost limits...")
        set_limits(args.daily, args.monthly)
        
        # Show updated status
        show_current_status()
        
    elif args.show or (not args.daily and not args.monthly):
        # Just show current status
        show_current_status()
    
    logger.info("\n" + "="*60)
    logger.info("💡 To change limits:")
    logger.info("  python3 scripts/set_cost_limits.py --daily 25 --monthly 100")
    logger.info("\nOr add to config/.env:")
    logger.info("  DAILY_COST_LIMIT=25.0")
    logger.info("  MONTHLY_COST_LIMIT=100.0")
    logger.info("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())