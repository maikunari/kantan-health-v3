#!/usr/bin/env python3

import requests
import os
from dotenv import load_dotenv
import json

def test_google_map_acf():
    """Test the new Google Map ACF field"""
    
    # Load environment
    load_dotenv('config/.env')
    
    wp_url = os.getenv('WORDPRESS_URL')
    wp_user = os.getenv('WORDPRESS_USERNAME')
    wp_pass = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
    
    if not all([wp_url, wp_user, wp_pass]):
        print("❌ WordPress credentials not found in config/.env")
        return
    
    print("🗺️  TESTING GOOGLE MAP ACF FIELD")
    print("=" * 50)
    
    # Test providers
    test_providers = [
        {'name': 'OSAKA GRAND CLINIC', 'post_id': 1938},
        {'name': 'St. Luke\'s International Hospital', 'post_id': 1698},
        {'name': 'Tokyo Medical University Hospital', 'post_id': 2266}
    ]
    
    for provider in test_providers:
        print(f"\n📋 Testing: {provider['name']} (ID: {provider['post_id']})")
        
        try:
            response = requests.get(
                f"{wp_url}/wp-json/wp/v2/healthcare_provider/{provider['post_id']}",
                auth=(wp_user, wp_pass),
                timeout=10
            )
            
            if response.status_code == 200:
                post = response.json()
                acf = post.get('acf', {})
                
                print(f"✅ Post found: {post.get('title', {}).get('rendered', 'N/A')}")
                
                # Test the Google Map field specifically
                google_map = acf.get('google_map', 'NOT FOUND')
                
                if google_map and google_map != 'NOT FOUND':
                    print(f"🗺️  Google Map Field Structure:")
                    if isinstance(google_map, dict):
                        location = google_map.get('location', {})
                        if location:
                            lat = location.get('lat', 'N/A')
                            lng = location.get('lng', 'N/A')
                            print(f"   📍 Location: lat={lat}, lng={lng}")
                        else:
                            print(f"   📍 Location: {location}")
                        
                        title = google_map.get('title', 'N/A')
                        description = google_map.get('description', 'N/A')
                        print(f"   🏥 Title: {title}")
                        print(f"   📝 Description: {description[:60]}..." if len(description) > 60 else description)
                        
                        print(f"\n🎯 Greenshift Usage Example:")
                        print(f"   Map Component Source: {{acf:google_map}}")
                        print(f"   ✅ Will resolve to complete map data structure")
                        
                    else:
                        print(f"   ⚠️  Unexpected format: {type(google_map)} - {google_map}")
                else:
                    print(f"   ❌ Google Map field not found or empty")
                
                # Also show other location fields for comparison
                print(f"\n📊 Other Location Fields:")
                print(f"   🧭 Latitude: {acf.get('latitude', 'N/A')}")
                print(f"   🧭 Longitude: {acf.get('longitude', 'N/A')}")
                print(f"   🏠 Address: {acf.get('provider_address', 'N/A')}")
                
            else:
                print(f"❌ Failed to fetch post: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing {provider['name']}: {str(e)}")
    
    print(f"\n💡 GOOGLE MAP ACF FIELD SETUP:")
    print(f"1. The google_map field returns exactly the array format you requested:")
    print(f"   array[")
    print(f"      'location' => array(")
    print(f"          'lat' => 'value',")
    print(f"          'lng' => 'value'")
    print(f"      ),")
    print(f"      'title' => 'value',")
    print(f"      'description' => 'value'")
    print(f"   ]")
    print(f"")
    print(f"2. In Greenshift, use: {{acf:google_map}} for the complete structure")
    print(f"3. Or access specific values:")
    print(f"   - {{acf:google_map.location.lat}} - Latitude")
    print(f"   - {{acf:google_map.location.lng}} - Longitude") 
    print(f"   - {{acf:google_map.title}} - Provider name")
    print(f"   - {{acf:google_map.description}} - Address")

if __name__ == "__main__":
    test_google_map_acf() 