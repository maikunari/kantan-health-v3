#!/usr/bin/env python3
"""
Real-time API Cost Monitoring Dashboard
Shows actual vs estimated costs with Cloud Monitoring
"""

import sys
import os
import time
import argparse
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.cost_tracker import CostTracker, CLOUD_MONITORING_AVAILABLE


def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def format_bar(value, max_value, width=30):
    """Create a visual progress bar"""
    if max_value <= 0:
        return '░' * width
    
    filled = int((value / max_value) * width)
    filled = min(filled, width)  # Cap at width
    
    if value >= max_value:
        # Over budget - use red blocks
        return '█' * width + ' ⚠️'
    elif filled > width * 0.8:
        # Near limit - use yellow blocks
        return '█' * filled + '░' * (width - filled) + ' ⚡'
    else:
        # Normal - use green blocks
        return '█' * filled + '░' * (width - filled)


def display_dashboard(tracker, refresh_rate=60):
    """Display real-time monitoring dashboard"""
    
    while True:
        clear_screen()
        
        print("="*70)
        print(" "*20 + "📊 API COST MONITORING DASHBOARD")
        print("="*70)
        print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Get comparison data
        comparison = tracker.get_actual_vs_estimated()
        
        # Display Cloud Monitoring status
        if tracker.cloud_monitor:
            print("✅ Cloud Monitoring: CONNECTED")
        else:
            print("⚠️  Cloud Monitoring: NOT AVAILABLE (using estimates)")
        print()
        
        # API Calls section
        print("📡 API CALLS TODAY")
        print("-" * 50)
        
        api_calls = comparison.get('api_calls', {})
        if api_calls:
            for api_type, count in api_calls.items():
                print(f"  {api_type:20}: {count:6,} calls")
            print(f"  {'TOTAL':20}: {comparison['total_calls']:6,} calls")
        else:
            print("  No API calls recorded yet")
        print()
        
        # Cost Analysis section
        print("💰 COST ANALYSIS")
        print("-" * 50)
        
        actual_cost = comparison.get('actual_cost', 0)
        estimated_cost = comparison.get('estimated_cost', 0)
        
        print(f"  Actual Cost:    ${actual_cost:7.2f}")
        print(f"  Estimated Cost: ${estimated_cost:7.2f}")
        
        if actual_cost != estimated_cost:
            diff = estimated_cost - actual_cost
            if diff > 0:
                print(f"  Overestimated:  ${diff:7.2f} ({comparison.get('savings_percent', 0):.1f}%)")
            else:
                print(f"  Underestimated: ${abs(diff):7.2f}")
        print()
        
        # Budget Usage section
        print("📊 DAILY BUDGET USAGE")
        print("-" * 50)
        
        daily_limit = tracker.DAILY_LIMIT
        daily_used = tracker.get_daily_usage()
        daily_remaining = daily_limit - daily_used
        daily_percent = (daily_used / daily_limit * 100) if daily_limit > 0 else 0
        
        print(f"  Limit:     ${daily_limit:.2f}")
        print(f"  Used:      ${daily_used:.2f} ({daily_percent:.1f}%)")
        print(f"  Remaining: ${daily_remaining:.2f}")
        print(f"  [{format_bar(daily_used, daily_limit, 40)}]")
        print()
        
        # Monthly Budget section
        print("📅 MONTHLY BUDGET USAGE")
        print("-" * 50)
        
        monthly_limit = tracker.MONTHLY_LIMIT
        monthly_used = tracker.get_monthly_usage()
        monthly_remaining = monthly_limit - monthly_used
        monthly_percent = (monthly_used / monthly_limit * 100) if monthly_limit > 0 else 0
        
        print(f"  Limit:     ${monthly_limit:.2f}")
        print(f"  Used:      ${monthly_used:.2f} ({monthly_percent:.1f}%)")
        print(f"  Remaining: ${monthly_remaining:.2f}")
        print(f"  [{format_bar(monthly_used, monthly_limit, 40)}]")
        print()
        
        # Cache Statistics
        stats = tracker.get_usage_stats(days=1)
        if stats['cache_hits'] > 0:
            print("💾 CACHE PERFORMANCE")
            print("-" * 50)
            print(f"  Cache Hits:      {stats['cache_hits']:,}")
            print(f"  Hit Rate:        {stats['cache_rate']:.1f}%")
            print(f"  Money Saved:     ${stats['estimated_savings']:.2f}")
            print()
        
        # Warnings
        if daily_percent > 90:
            print("⚠️  WARNING: Daily budget nearly exhausted!")
        if daily_percent >= 100:
            print("❌ ALERT: Daily budget exceeded! API calls will be blocked.")
        
        print("="*70)
        print(f"Refreshing in {refresh_rate} seconds... (Press Ctrl+C to exit)")
        
        try:
            time.sleep(refresh_rate)
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped")
            break


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Monitor API costs in real-time')
    parser.add_argument('--refresh', type=int, default=60, 
                      help='Refresh interval in seconds (default: 60)')
    parser.add_argument('--no-cloud', action='store_true',
                      help='Disable Cloud Monitoring (use estimates only)')
    
    args = parser.parse_args()
    
    # Check Cloud Monitoring availability
    if not args.no_cloud and not CLOUD_MONITORING_AVAILABLE:
        print("⚠️  Google Cloud Monitoring not available")
        print("   Install with: pip install google-cloud-monitoring")
        print("   Or use --no-cloud flag to use estimates only")
        print()
    
    # Initialize tracker
    try:
        tracker = CostTracker(use_cloud_monitoring=not args.no_cloud)
        print("✅ Cost tracker initialized")
        print(f"   Starting dashboard (refresh every {args.refresh}s)...")
        time.sleep(2)
        
        # Run dashboard
        display_dashboard(tracker, args.refresh)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())