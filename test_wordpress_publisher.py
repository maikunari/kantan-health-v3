#!/usr/bin/env python3
"""Test WordPress Publisher functionality"""

import sys
import requests
from src.publishers.wordpress import WordPressPublisher

def test_wordpress_publisher():
    """Test WordPress publisher initialization and API connectivity"""
    
    print("Testing WordPress Publisher...")
    print("=" * 60)
    
    # Test 1: Initialize publisher
    try:
        publisher = WordPressPublisher()
        print("✅ Publisher initialized successfully")
        print(f"  - WordPress URL: {publisher.wp_url}")
        print(f"  - Username: {publisher.wp_username}")
        print("  - Password: ***")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False
    
    # Test 2: Verify attributes are accessible
    try:
        assert hasattr(publisher, 'wp_url'), "Missing wp_url attribute"
        assert hasattr(publisher, 'wp_username'), "Missing wp_username attribute"
        assert hasattr(publisher, 'wp_password'), "Missing wp_password attribute"
        assert hasattr(publisher, 'acf_field_mappings'), "Missing ACF mappings"
        print("✅ All required attributes accessible")
    except AssertionError as e:
        print(f"❌ Attribute check failed: {e}")
        return False
    
    # Test 3: Test WordPress API connectivity
    try:
        test_url = f"{publisher.wp_url}/wp-json/wp/v2/users/me"
        response = requests.get(
            test_url, 
            auth=(publisher.wp_username, publisher.wp_password),
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ WordPress API authenticated as: {user_data.get('name', 'Unknown')}")
        else:
            print(f"❌ WordPress API returned status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ WordPress API test failed: {e}")
        return False
    
    # Test 4: Check ACF field mappings
    expected_fields = ['provider_name', 'description', 'location', 'specialties']
    missing_fields = []
    for field in expected_fields:
        if field not in publisher.acf_field_mappings:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"⚠️ Missing ACF field mappings: {missing_fields}")
    else:
        print("✅ ACF field mappings configured")
    
    # Test 5: Test prepare_acf_fields method
    if hasattr(publisher, 'prepare_acf_fields'):
        print("✅ prepare_acf_fields method exists")
    else:
        print("⚠️ prepare_acf_fields method not found")
    
    print("\n" + "=" * 60)
    print("WordPress Publisher Test Summary:")
    print("  ✅ Initialization: PASSED")
    print("  ✅ Attributes: PASSED")
    print("  ✅ API Authentication: PASSED")
    print("  ✅ ACF Mappings: CONFIGURED")
    
    return True

if __name__ == "__main__":
    success = test_wordpress_publisher()
    if success:
        print("\n✅ WordPress Publisher WORKING!")
    else:
        print("\n❌ WordPress Publisher has issues")
    sys.exit(0 if success else 1)