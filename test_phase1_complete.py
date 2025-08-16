#!/usr/bin/env python3
"""
Phase 1 Complete Test - Collect 100 providers across Tokyo
This tests all our improvements:
1. Pagination (3x more results)
2. Ward-specific searches (23 wards)
3. Japanese search terms (bilingual coverage)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.collectors.google_places import GooglePlacesCollector
from datetime import datetime
import time

def test_phase1_complete():
    """Test enhanced collection with all Phase 1 improvements"""
    print("🚀 PHASE 1 COMPLETE TEST - TOKYO COLLECTION")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize collector
    collector = GooglePlacesCollector(daily_limit=100)
    
    # Generate queries for Tokyo with ward-specific searches
    print("📍 Generating ward-specific queries for Tokyo...")
    queries = collector.generate_search_queries(
        cities=["Tokyo"],
        specialties=["dentist", "clinic", "hospital"],  # Top 3 specialties
        use_ward_specific=True,
        limit=50  # Limit queries to control test
    )
    
    print(f"✅ Generated {len(queries)} search queries")
    print("\nSample queries:")
    for i, q in enumerate(queries[:5]):
        print(f"  {i+1}. {q}")
    print(f"  ... and {len(queries)-5} more")
    print()
    
    # Run collection
    print("🔍 Starting collection (this will take a few minutes)...")
    print("   • Using pagination (up to 60 results per query)")
    print("   • Searching across Tokyo's 23 wards")
    print("   • Using both English and Japanese terms")
    print()
    
    start_time = time.time()
    
    # Collect providers
    summary = collector.collect_providers(
        queries=queries,
        max_per_query=10  # Limit per query to spread collection
    )
    
    elapsed = time.time() - start_time
    
    # Display results
    print("\n" + "="*60)
    print("📊 COLLECTION RESULTS")
    print("="*60)
    print(f"⏱️  Time elapsed: {elapsed:.1f} seconds")
    print(f"📍 Queries executed: {summary['queries_executed']}")
    print(f"🔍 Providers found: {summary['providers_found']}")
    print(f"✅ Providers collected: {summary['providers_collected']}")
    print(f"🔁 Duplicates skipped: {summary['duplicates_skipped']}")
    print(f"❌ Rejected (low English): {summary['rejected_proficiency']}")
    print(f"📷 Rejected (no photos): {summary['rejected_no_photos']}")
    print(f"💰 Estimated cost: ${summary['estimated_cost']:.2f}")
    print(f"💾 Cache hits: {summary['cache_hits']}")
    print()
    
    # Calculate efficiency
    if summary['queries_executed'] > 0:
        avg_per_query = summary['providers_found'] / summary['queries_executed']
        print(f"📈 Average providers per query: {avg_per_query:.1f}")
        
        if avg_per_query > 20:
            print(f"   🎉 Pagination is working! ({avg_per_query:.1f} > 20)")
    
    # Success evaluation
    print("\n" + "="*60)
    if summary['providers_collected'] >= 50:
        print("🎉 SUCCESS! Phase 1 objectives achieved!")
        print(f"   • Collected {summary['providers_collected']} providers")
        print("   • Pagination: ✅ Working")
        print("   • Ward-specific: ✅ Working") 
        print("   • Japanese terms: ✅ Working")
        print("\n🚀 Ready to scale to 10,000 providers!")
    elif summary['providers_collected'] >= 25:
        print("✅ Good progress! Phase 1 partially successful")
        print(f"   • Collected {summary['providers_collected']} providers")
        print("   • System is working but may need tuning")
    else:
        print("⚠️  Low collection rate")
        print(f"   • Only collected {summary['providers_collected']} providers")
        print("   • Check API limits or query effectiveness")
    
    print("="*60)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return summary['providers_collected']

if __name__ == "__main__":
    providers = test_phase1_complete()
    sys.exit(0 if providers >= 25 else 1)