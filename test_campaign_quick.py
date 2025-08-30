#!/usr/bin/env python3
"""
Quick Campaign Test - Single Query
Tests if the system works without Google Cloud auth
"""

import os
import sys
import logging

# Disable Google Cloud Billing API
os.environ['DISABLE_GOOGLE_BILLING'] = 'true'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

print("\n" + "=" * 80)
print("QUICK CAMPAIGN TEST - SINGLE QUERY")
print("=" * 80)

try:
    from src.campaign import EnhancedCampaignPipeline
    
    # Initialize pipeline
    print("\nInitializing pipeline...")
    pipeline = EnhancedCampaignPipeline(state_file='quick_test_state.json')
    
    # Initialize with just 1 query
    print("Creating single test query...")
    pipeline.initialize_campaign(
        locations=['Roppongi'],
        specialties=['General Medicine'],
        query_limit=1  # Just 1 query
    )
    
    print("\nRunning search...")
    print("-" * 40)
    
    # Run with timeout
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Operation timed out")
    
    # Set 30 second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)
    
    try:
        providers = pipeline.run_with_state_management(
            daily_limit=1,  # Stop after 1 provider
            test_mode=True
        )
        signal.alarm(0)  # Cancel alarm
        
        print(f"\n✅ Test completed successfully!")
        print(f"   Providers collected: {providers}")
        
    except TimeoutError:
        print("\n⚠️  Operation timed out after 30 seconds")
        print("   This suggests the Google auth issue persists")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    # Cleanup
    if os.path.exists('quick_test_state.json'):
        os.remove('quick_test_state.json')
    print("\nTest complete.")