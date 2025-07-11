#!/usr/bin/env python3
"""
Test ACF Field Values for Greenshift Integration
Verifies that external_featured_image and related fields are properly populated
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def test_acf_fields():
    """Test ACF field values for providers with Claude-selected images"""
    
    # Load WordPress credentials
    load_dotenv('config/.env')
    wp_url = os.getenv('WORDPRESS_URL')
    wp_user = os.getenv('WORDPRESS_USERNAME') 
    wp_pass = os.getenv('WORDPRESS_PASSWORD')
    
    # Test providers (WordPress post IDs)
    test_providers = [
        {'name': 'OSAKA GRAND CLINIC', 'post_id': 1938},
        {'name': 'Ikuryo Clinic', 'post_id': 'unknown'},  # Would need to be found
        {'name': 'Shinjuku Skin Clinic', 'post_id': 'unknown'},  # Would need to be found
    ]
    
    print("🧪 TESTING ACF FIELDS FOR GREENSHIFT")
    print("=" * 60)
    
    for provider in test_providers:
        if provider['post_id'] == 'unknown':
            continue
            
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
                
                # Test the specific fields needed for Greenshift
                fields_to_test = [
                    'external_featured_image',
                    'featured_image_source', 
                    'photo_count',
                    'image_selection_status',
                    'photo_urls'
                ]
                
                print(f"📊 ACF Field Values:")
                for field in fields_to_test:
                    value = acf.get(field, 'NOT FOUND')
                    
                    if field == 'external_featured_image' and value and value != 'NOT FOUND':
                        # Show truncated URL for readability
                        display_value = f"{value[:50]}..." if len(value) > 50 else value
                        print(f"  🔗 {field}: {display_value}")
                    elif field == 'photo_urls' and value and value != 'NOT FOUND':
                        # Show first few characters of photo URLs
                        display_value = f"{value[:60]}..." if len(value) > 60 else value
                        print(f"  📸 {field}: {display_value}")
                    else:
                        print(f"  📊 {field}: {value}")
                
                # Greenshift usage examples
                print(f"\n🎯 Greenshift Usage:")
                external_image = acf.get('external_featured_image', '')
                if external_image:
                    print(f"  Image Block Source: {{acf:external_featured_image}}")
                    print(f"  ✅ Will resolve to: {external_image[:40]}...")
                else:
                    print(f"  ❌ external_featured_image is empty - check ACF field registration")
                
                source = acf.get('featured_image_source', '')
                if source and source != 'NOT FOUND':
                    print(f"  Badge Text: {{acf:featured_image_source}}")
                    print(f"  ✅ Will resolve to: {source}")
                else:
                    print(f"  ❌ featured_image_source is empty")
                    
            else:
                print(f"❌ Failed to fetch post: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing {provider['name']}: {str(e)}")
    
    print(f"\n💡 TROUBLESHOOTING:")
    print(f"If fields show 'NOT FOUND' or are empty:")
    print(f"1. Upload updated setup_acf_fields.php to WordPress")
    print(f"2. Verify ACF field group 'Photo Gallery & Featured Image' exists")
    print(f"3. Check that field names match exactly:")
    print(f"   - external_featured_image")
    print(f"   - featured_image_source") 
    print(f"   - photo_count")
    print(f"   - image_selection_status")
    print(f"4. Force update provider posts to populate new fields")

if __name__ == "__main__":
    test_acf_fields() 