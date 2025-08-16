#!/usr/bin/env python3
"""
Debug version to see exactly what's happening with pagination.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/.env')

def test_google_api_directly():
    """Test Google Places API directly to see pagination tokens"""
    
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return
    
    # Try a query that should have many results
    queries = [
        "dental clinic Tokyo",
        "clinic Tokyo Japan", 
        "病院 東京",  # Hospital Tokyo in Japanese
        "medical center Tokyo"
    ]
    
    for query in queries:
        print(f"\n🔍 Testing: '{query}'")
        print("-" * 40)
        
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'query': query,
            'key': api_key,
            'language': 'en',
            'region': 'jp'
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            status = data.get('status')
            results = data.get('results', [])
            next_token = data.get('next_page_token', '')
            
            print(f"Status: {status}")
            print(f"Results on page 1: {len(results)}")
            print(f"Has next_page_token: {'YES ✅' if next_token else 'NO ❌'}")
            
            if next_token:
                print(f"Token preview: {next_token[:50]}...")
                print("\n🎉 PAGINATION AVAILABLE for this query!")
                print("The implementation should work with this query.")
                return True
            else:
                if len(results) == 20:
                    print("⚠️  Got exactly 20 results but no next_page_token")
                    print("   Google determined no more results are available")
                else:
                    print(f"ℹ️  Query returned {len(results)} total results")
            
            # Show first few results
            print("\nFirst 3 results:")
            for i, r in enumerate(results[:3], 1):
                print(f"  {i}. {r.get('name', 'Unknown')}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "="*60)
    print("CONCLUSION: Google API may not be returning next_page_tokens")
    print("for these queries. This could be due to:")
    print("  1. The queries genuinely have ≤20 results in the region")
    print("  2. API account restrictions")
    print("  3. Regional/language settings affecting results")
    print("="*60)
    
    return False

if __name__ == "__main__":
    test_google_api_directly()