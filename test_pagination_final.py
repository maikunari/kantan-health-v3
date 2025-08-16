#!/usr/bin/env python3
"""
Final pagination test with a query we know has multiple pages.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.collectors.google_places import GooglePlacesCollector

def test_pagination_final():
    """Test with 'dental clinic Tokyo' which we confirmed has pagination"""
    print("🧪 FINAL PAGINATION TEST")
    print("="*60)
    
    # Initialize collector
    collector = GooglePlacesCollector()
    
    # This query has confirmed pagination available
    test_query = "dental clinic Tokyo"
    
    print(f"📍 Query: '{test_query}'")
    print("⏳ Fetching results with pagination...")
    print("   (This will take 4-6 seconds due to required delays)")
    print()
    
    # Clear any cached results for this query first
    # by using a slightly different query
    fresh_query = test_query + " "  # Add space to bypass cache
    
    # Search with pagination
    results = collector.search_providers(fresh_query, max_results=60)
    result_count = len(results)
    
    print(f"🎯 RESULTS: {result_count} providers found!")
    print()
    
    if result_count > 20:
        print("✅ SUCCESS! PAGINATION IS WORKING!")
        print(f"   • Old system (no pagination): 20 results max")
        print(f"   • New system (with pagination): {result_count} results")
        print(f"   • Improvement: {result_count/20:.1f}x more results")
        print()
        
        # Show distribution across pages
        print("📊 Results by page:")
        print(f"   • Page 1 (1-20): 20 results")
        if result_count > 20:
            page2_count = min(20, result_count - 20)
            print(f"   • Page 2 (21-40): {page2_count} results")
        if result_count > 40:
            page3_count = result_count - 40
            print(f"   • Page 3 (41-60): {page3_count} results")
        
        # Show some examples from each page
        print("\n📋 Sample results from each page:")
        
        print("\nPage 1 samples:")
        for i in [0, 9, 19]:
            if i < len(results):
                print(f"  #{i+1}: {results[i].get('name', 'Unknown')}")
        
        if result_count > 20:
            print("\nPage 2 samples:")
            for i in [20, 29, 39]:
                if i < len(results):
                    print(f"  #{i+1}: {results[i].get('name', 'Unknown')}")
        
        if result_count > 40:
            print("\nPage 3 samples:")
            for i in [40, 49, -1]:
                if i < len(results) and i >= 0:
                    idx = i if i >= 0 else result_count - 1
                    print(f"  #{idx+1}: {results[idx].get('name', 'Unknown')}")
        
        print("\n" + "="*60)
        print("🚀 PAGINATION IMPLEMENTATION: VERIFIED WORKING!")
        print("="*60)
        return True
    else:
        print(f"❌ Only got {result_count} results (expected > 20)")
        print("   Check if query was cached without pagination")
        return False

if __name__ == "__main__":
    success = test_pagination_final()
    sys.exit(0 if success else 1)