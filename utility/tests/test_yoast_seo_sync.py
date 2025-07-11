#!/usr/bin/env python3

import requests
import os
from dotenv import load_dotenv
import json

def test_yoast_seo_sync():
    """Test Yoast SEO field registration and sync"""
    
    # Load environment
    load_dotenv('config/.env')
    
    wp_url = os.getenv('WORDPRESS_URL')
    wp_user = os.getenv('WORDPRESS_USERNAME')
    wp_pass = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
    
    if not all([wp_url, wp_user, wp_pass]):
        print("❌ WordPress credentials not found in config/.env")
        return
    
    print("🔬 TESTING YOAST SEO REST FIELD REGISTRATION")
    print("=" * 60)
    
    # Test post - Tokyo Medical and Dental University Hospital
    test_post_id = 2266
    
    # Step 1: Check if REST fields are registered
    print(f"1️⃣ Checking REST field registration...")
    
    try:
        # Get post to see available fields
        response = requests.get(
            f"{wp_url}/wp-json/wp/v2/healthcare_provider/{test_post_id}",
            auth=(wp_user, wp_pass),
            timeout=10
        )
        
        if response.status_code == 200:
            post_data = response.json()
            
            # Check if Yoast fields are now available
            yoast_title = post_data.get('_yoast_wpseo_title', 'NOT_REGISTERED')
            yoast_desc = post_data.get('_yoast_wpseo_metadesc', 'NOT_REGISTERED')
            
            print(f"   📋 Current Yoast title: {yoast_title}")
            print(f"   📋 Current Yoast desc: {yoast_desc}")
            
            if yoast_title == 'NOT_REGISTERED':
                print(f"   ⚠️  Yoast REST fields not yet registered")
                print(f"   💡 Upload updated setup_acf_fields.php to WordPress first")
                return False
            else:
                print(f"   ✅ Yoast REST fields are registered!")
                
        else:
            print(f"   ❌ Failed to fetch post: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking registration: {str(e)}")
        return False
    
    # Step 2: Test updating Yoast fields with new approach
    print(f"\n2️⃣ Testing Yoast field updates...")
    
    test_seo_data = {
        '_yoast_wpseo_title': 'TMDU Hospital: Medical & Dental Care in Tokyo',
        '_yoast_wpseo_metadesc': 'Leading university hospital in Tokyo offering comprehensive medical and dental care with English support. Expert specialists and modern facilities.',
        '_rank_math_title': 'TMDU Hospital: Medical & Dental Care in Tokyo',
        '_rank_math_description': 'Leading university hospital in Tokyo offering comprehensive medical and dental care with English support. Expert specialists and modern facilities.'
    }
    
    try:
        response = requests.post(
            f"{wp_url}/wp-json/wp/v2/healthcare_provider/{test_post_id}",
            auth=(wp_user, wp_pass),
            json=test_seo_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   📊 Update status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Yoast fields updated successfully!")
            
            # Verify the update
            verify_response = requests.get(
                f"{wp_url}/wp-json/wp/v2/healthcare_provider/{test_post_id}",
                auth=(wp_user, wp_pass),
                timeout=10
            )
            
            if verify_response.status_code == 200:
                verified_data = verify_response.json()
                new_title = verified_data.get('_yoast_wpseo_title', 'NOT_FOUND')
                new_desc = verified_data.get('_yoast_wpseo_metadesc', 'NOT_FOUND')
                
                print(f"\n   📋 Verification Results:")
                print(f"   🎯 Yoast Title: {new_title}")
                print(f"   📝 Yoast Desc: {new_desc[:80]}..." if len(new_desc) > 80 else f"   📝 Yoast Desc: {new_desc}")
                
                if new_title != 'NOT_FOUND' and new_desc != 'NOT_FOUND':
                    print(f"\n   🎉 SUCCESS: Yoast SEO sync is now working!")
                    return True
                else:
                    print(f"\n   ❌ Fields still not populated")
                    return False
            else:
                print(f"   ❌ Verification failed: {verify_response.status_code}")
                return False
        else:
            print(f"   ❌ Update failed: {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Error updating fields: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🎯 YOAST SEO SYNC TEST")
    print("=" * 30)
    
    success = test_yoast_seo_sync()
    
    if success:
        print(f"\n✅ YOAST SEO INTEGRATION WORKING!")
        print(f"📋 Next Steps:")
        print(f"   1. Run force_update_acf_fields.py to sync all providers")
        print(f"   2. Check WordPress admin for populated Yoast fields")
        print(f"   3. Verify frontend SEO meta tags")
    else:
        print(f"\n⚠️  SETUP REQUIRED:")
        print(f"📋 Steps to fix:")
        print(f"   1. Upload updated setup_acf_fields.php to WordPress")
        print(f"   2. Add the REST field registration code to functions.php")
        print(f"   3. Re-run this test to verify")

if __name__ == "__main__":
    main() 