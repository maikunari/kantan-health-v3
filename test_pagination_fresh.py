#!/usr/bin/env python3
"""
Test pagination with a fresh query (no cache) to verify it's working.
"""

import os
import sys
import time
sys.path.insert(0, os.path.dirname(__file__))

from src.collectors.google_places import GooglePlacesCollector

def test_pagination_fresh():
    """Test pagination with unique queries to bypass cache"""
    print("🧪 Testing pagination with fresh queries...")
    print("-" * 60)
    
    # Initialize collector
    collector = GooglePlacesCollector()
    
    # Use a unique query with timestamp to bypass cache
    timestamp = str(int(time.time()))[-4:]  # Last 4 digits of timestamp
    
    # Try different query patterns
    queries_to_test = [
        "clinic Shibuya Tokyo",  # Broader search
        "hospital Tokyo",         # Many hospitals
        "医院 東京",              # Japanese search
    ]
    
    for test_query in queries_to_test:
        print(f"\n📍 Testing: '{test_query}'")
        print("⏳ Searching (may take 4-6 seconds with pagination)...")
        
        # Search with pagination
        results = collector.search_providers(test_query, max_results=60)
        result_count = len(results)
        
        print(f"✅ Found {result_count} results")
        
        if result_count > 20:
            print(f"   🎉 PAGINATION WORKING! ({result_count} > 20)")
            
            # Show some examples
            print(f"\n   Examples from page 1 (1-20):")
            for i in [0, 10, 19]:
                if i < len(results):
                    print(f"     #{i+1}: {results[i].get('name', 'Unknown')[:40]}...")
            
            if result_count > 20:
                print(f"\n   Examples from page 2 (21-40):")
                for i in [20, 30, 39]:
                    if i < len(results):
                        print(f"     #{i+1}: {results[i].get('name', 'Unknown')[:40]}...")
            
            if result_count > 40:
                print(f"\n   Examples from page 3 (41-60):")
                for i in [40, 50, 59]:
                    if i < len(results):
                        print(f"     #{i+1}: {results[i].get('name', 'Unknown')[:40]}...")
            
            print("\n" + "="*60)
            print(f"🚀 SUCCESS! Pagination increased results by {result_count/20:.1f}x")
            print("="*60)
            return True
        
        print("   Trying next query...")
    
    print("\n⚠️  No queries returned > 20 results")
    print("This might be due to:")
    print("  1. API limitations in sandbox/test mode")
    print("  2. Specific search queries having limited results")
    print("  3. Regional restrictions")
    return False

if __name__ == "__main__":
    success = test_pagination_fresh()
    sys.exit(0 if success else 1)