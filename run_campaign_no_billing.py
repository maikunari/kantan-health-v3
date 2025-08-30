#!/usr/bin/env python3
"""
Run Campaign Without Google Cloud Billing
Uses environment variable to disable billing API
"""

import os
import sys

# Disable Google Cloud Billing API to avoid auth issues
os.environ['DISABLE_GOOGLE_BILLING'] = 'true'

import logging
from src.campaign import EnhancedCampaignPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def main():
    """Run campaign with billing disabled"""
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            print("\n" + "=" * 80)
            print("RUNNING TEST CAMPAIGN (NO BILLING API)")
            print("=" * 80)
            daily_limit = 20
            query_limit = 10
        elif sys.argv[1] == '--status':
            pipeline = EnhancedCampaignPipeline()
            pipeline.show_progress_dashboard()
            return
        elif sys.argv[1] == '--resume':
            print("\n" + "=" * 80)
            print("RESUMING CAMPAIGN (NO BILLING API)")
            print("=" * 80)
            pipeline = EnhancedCampaignPipeline()
            pipeline.resume_campaign()
            pipeline.run_with_state_management(daily_limit=200)
            return
        else:
            print("Usage: python3 run_campaign_no_billing.py [--test|--status|--resume]")
            return
    else:
        print("\n" + "=" * 80)
        print("RUNNING PRODUCTION CAMPAIGN (NO BILLING API)")
        print("=" * 80)
        daily_limit = 200
        query_limit = 1000
    
    # Initialize pipeline
    pipeline = EnhancedCampaignPipeline()
    
    # Check if campaign already exists
    if pipeline.state.total_queries > 0:
        print(f"\nFound existing campaign with {pipeline.state.total_queries} queries")
        print(f"Progress: {pipeline.state.completed_queries}/{pipeline.state.total_queries}")
        response = input("Resume existing campaign? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            return
    else:
        # Initialize new campaign
        print("\nInitializing new campaign...")
        pipeline.initialize_campaign(
            locations=None,      # Use default priority locations
            specialties=None,    # Use default priority specialties
            query_limit=query_limit
        )
    
    # Run campaign
    print(f"\nProcessing up to {daily_limit} providers...")
    print("Note: Google Cloud billing API disabled - using estimate-based cost tracking")
    print("-" * 80)
    
    providers_collected = pipeline.run_with_state_management(
        daily_limit=daily_limit,
        test_mode=(daily_limit == 20)
    )
    
    print("\n" + "=" * 80)
    print("CAMPAIGN BATCH COMPLETE")
    print("=" * 80)
    print(f"Providers collected: {providers_collected}")
    
    # Show final dashboard
    pipeline.show_progress_dashboard()
    
    print("\n💡 Tips:")
    print("- Run with --status to check progress")
    print("- Run with --resume to continue")
    print("- Run with --test for small test batch")
    print("- Google auth not required with billing disabled")


if __name__ == "__main__":
    main()