#!/usr/bin/env python3
"""
Tokyo Provider Collection Test
Simple script to validate the user-search approach
"""

import googlemaps
import json
import time
from datetime import datetime
from collections import defaultdict

# Configuration
GOOGLE_API_KEY = "AIzaSyDaxKYWh-94rc18EQPHHTfPymRjGQP4Jlc"  # Add your actual API key

def test_tokyo_collection():
    """Test collection using actual user search patterns."""
    
    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
    all_providers = {}  # Use dict to deduplicate by place_id
    
    # What real users search for
    search_queries = [
        "English speaking doctor Tokyo",
        "International clinic Tokyo", 
        "English dentist Tokyo",
        "International hospital Tokyo",
        "Foreign friendly medical Tokyo",
        "English pediatrician Tokyo",
        "Expat doctor Tokyo"
    ]
    
    print("="*50)
    print("TOKYO COLLECTION TEST")
    print("="*50)
    
    # Phase 1: Collect basic results
    for query in search_queries:
        print(f"\nSearching: {query}")
        
        try:
            results = gmaps.places(query=query)
            
            # Process first page
            for place in results.get('results', []):
                if place['place_id'] not in all_providers:
                    all_providers[place['place_id']] = {
                        'name': place['name'],
                        'address': place.get('formatted_address', ''),
                        'place_id': place['place_id'],
                        'from_query': query,
                        'basic_rating': place.get('rating', 0)
                    }
            
            print(f"  Found {len(results.get('results', []))} results")
            
            # Get additional pages if available
            while results.get('next_page_token'):
                time.sleep(2)  # Required delay
                results = gmaps.places(query=query, page_token=results['next_page_token'])
                
                for place in results.get('results', []):
                    if place['place_id'] not in all_providers:
                        all_providers[place['place_id']] = {
                            'name': place['name'],
                            'address': place.get('formatted_address', ''),
                            'place_id': place['place_id'],
                            'from_query': query,
                            'basic_rating': place.get('rating', 0)
                        }
                
                print(f"  Found {len(results.get('results', []))} more results")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\n{'='*50}")
    print(f"PHASE 1 COMPLETE")
    print(f"Total unique providers found: {len(all_providers)}")
    print(f"API calls used: ~{len(search_queries) * 2}")
    print(f"Estimated cost: ${len(search_queries) * 2 * 0.032:.2f}")
    
    # Phase 2: Get details for subset to test English scoring
    print(f"\n{'='*50}")
    print("PHASE 2: TESTING ENGLISH PROFICIENCY")
    print(f"{'='*50}")
    
    # Test first 20 providers
    test_sample = list(all_providers.values())[:20]
    english_capable = []
    
    for provider in test_sample:
        print(f"\nAnalyzing: {provider['name']}")
        
        try:
            # Get full details
            details = gmaps.place(place_id=provider['place_id'])['result']
            
            # Calculate English score
            score = calculate_english_score(details)
            provider['english_score'] = score
            provider['reviews_count'] = details.get('user_ratings_total', 0)
            
            print(f"  English score: {score}")
            print(f"  Reviews: {provider['reviews_count']}")
            
            if score >= 10:
                english_capable.append(provider)
                print(f"  ✓ QUALIFIED")
            else:
                print(f"  ✗ Not qualified")
                
            time.sleep(0.5)  # Be nice to API
            
        except Exception as e:
            print(f"  Error getting details: {e}")
    
    # Results summary
    print(f"\n{'='*50}")
    print("TEST RESULTS SUMMARY")
    print(f"{'='*50}")
    print(f"Providers tested: {len(test_sample)}")
    print(f"Qualified (English score ≥10): {len(english_capable)}")
    print(f"Pass rate: {len(english_capable)/len(test_sample)*100:.1f}%")
    print(f"\nDetail API calls: {len(test_sample)}")
    print(f"Detail cost: ${len(test_sample) * 0.017:.2f}")
    
    # Project full collection
    if len(test_sample) > 0:
        pass_rate = len(english_capable) / len(test_sample)
        projected_qualified = int(len(all_providers) * pass_rate)
        
        print(f"\n{'='*50}")
        print("PROJECTION FOR FULL TOKYO")
        print(f"{'='*50}")
        print(f"Total providers found: {len(all_providers)}")
        print(f"Projected qualified: {projected_qualified}")
        print(f"Cost to get all details: ${len(all_providers) * 0.017:.2f}")
        print(f"Cost per qualified provider: ${(len(all_providers) * 0.017) / max(projected_qualified, 1):.2f}")
    
    # Save results
    with open('tokyo_test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_found': len(all_providers),
            'tested': len(test_sample),
            'qualified': len(english_capable),
            'providers': english_capable
        }, f, indent=2)
    
    print(f"\nResults saved to tokyo_test_results.json")
    
    return all_providers, english_capable

def calculate_english_score(details):
    """Simple English proficiency scoring."""
    score = 0
    
    # Check for English in reviews
    reviews = details.get('reviews', [])
    for review in reviews:
        text = review.get('text', '')
        # Check if review is in English (simple ASCII check)
        if len(text) > 0 and sum(1 for c in text if ord(c) < 128) / len(text) > 0.7:
            score += 5
    
    # Check name for English/International indicators
    name = details.get('name', '').lower()
    if any(word in name for word in ['international', 'english', 'foreign']):
        score += 20
    
    # Has website (often indicates more established/international)
    if details.get('website'):
        score += 10
    
    # Has many reviews (established)
    if details.get('user_ratings_total', 0) > 50:
        score += 5
    
    return score

if __name__ == "__main__":
    test_tokyo_collection()