#!/usr/bin/env python3
"""
Test script to verify pagination is working correctly.
This will search for dentists in Tokyo and show how many results we get.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.collectors.google_places import GooglePlacesCollector

def test_pagination():
    """Test that pagination returns more than 20 results"""
    print("🧪 Testing pagination support...")
    print("-" * 60)
    
    # Initialize collector
    collector = GooglePlacesCollector()
    
    # Test query - dentists in Tokyo should have many results
    test_query = "dentist Tokyo"
    
    print(f"📍 Testing query: '{test_query}'")
    print("⏳ This will take a few seconds due to pagination delays...")
    print()
    
    # Search with pagination
    results = collector.search_providers(test_query, max_results=60)
    
    # Check results
    result_count = len(results)
    
    print(f"✅ Results found: {result_count}")
    print()
    
    if result_count > 20:
        print("🎉 SUCCESS! Pagination is working!")
        print(f"   - Old system would return: 20 results")
        print(f"   - New system returned: {result_count} results")
        print(f"   - Improvement: {result_count/20:.1f}x more results!")
    elif result_count == 20:
        print("⚠️  WARNING: Got exactly 20 results")
        print("   Pagination might not be working, or this query genuinely has only 20 results")
    else:
        print(f"ℹ️  Got {result_count} results (less than 20)")
        print("   This query might have limited results")
    
    # Show first few results as examples
    print("\n📋 First 5 results:")
    for i, result in enumerate(results[:5], 1):
        name = result.get('name', 'Unknown')
        address = result.get('formatted_address', 'No address')
        print(f"   {i}. {name}")
        print(f"      {address[:60]}...")
    
    print("\n" + "-" * 60)
    print("Test complete!")
    
    return result_count

if __name__ == "__main__":
    result_count = test_pagination()
    
    # Exit with status based on test result
    sys.exit(0 if result_count > 20 else 1)