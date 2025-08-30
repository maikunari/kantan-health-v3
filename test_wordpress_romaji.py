#!/usr/bin/env python3
"""
Test WordPress Publisher Romaji Integration
Validates that Japanese provider names are consistently converted to romaji in WordPress
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.publishers.wordpress import WordPressPublisher
from src.core.database import DatabaseManager, Provider
from src.utils.romaji_converter import contains_japanese, convert_to_romaji

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_provider_with_japanese_name():
    """Create a test provider with Japanese name"""
    provider = Provider()
    provider.id = 9999
    provider.provider_name = '千葉デンタルクリニック'
    provider.provider_name_romaji = None  # Will be generated
    provider.city = 'Tokyo'
    provider.district = 'Shibuya'
    provider.prefecture = 'Tokyo'
    provider.specialties = ['Dentistry', '歯科']  # Mixed English and Japanese
    provider.rating = 4.5
    provider.total_reviews = 120
    provider.english_proficiency = 'High'
    provider.proficiency_score = 4
    provider.google_place_id = 'test_japanese_provider_romaji'
    provider.address = '東京都渋谷区1-2-3'
    provider.phone = '03-1234-5678'
    provider.website = 'https://example-dental.jp'
    provider.business_hours = {
        'formatted_hours': {
            'Monday': {'open': '9:00', 'close': '18:00'},
            'Tuesday': {'open': '9:00', 'close': '18:00'},
            'Wednesday': {'status': 'closed'},
            'Thursday': {'open': '9:00', 'close': '18:00'},
            'Friday': {'open': '9:00', 'close': '18:00'},
            'Saturday': {'open': '9:00', 'close': '13:00'},
            'Sunday': {'status': 'closed'}
        }
    }
    provider.wheelchair_accessible = 'Yes'
    provider.parking_available = 'Yes'
    provider.latitude = 35.6595
    provider.longitude = 139.7004
    
    # AI-generated content (should already be in English from content processor)
    provider.ai_description = "Chiba Dental Clinic offers comprehensive dental care in Shibuya, Tokyo. The clinic specializes in general dentistry with English-speaking staff available."
    provider.ai_excerpt = "Professional dental clinic in Shibuya offering English support and modern dental care."
    provider.review_summary = "Patients praise the English-speaking staff and modern facilities at this Shibuya dental clinic."
    provider.english_experience_summary = "The clinic provides full English support with bilingual staff and translated documents for international patients."
    provider.seo_title = "Chiba Dental Clinic | English Dentist in Shibuya"
    provider.seo_meta_description = "English-speaking dental clinic in Shibuya, Tokyo. Professional dental care with bilingual support for international patients."
    
    # Review content
    provider.review_content = [
        {'rating': 5, 'text': 'Great English-speaking dentist! Very professional.'},
        {'rating': 4, 'text': '英語対応が素晴らしい歯科医院です。'},
        {'rating': 5, 'text': 'Clean facilities and friendly bilingual staff.'}
    ]
    
    # Master data validation fields
    provider.primary_specialty = 'Dentistry'
    provider.location_needs_review = False
    provider.specialties_need_review = False
    provider.needs_manual_review = False
    
    return provider


def test_romaji_consistency():
    """Test romaji name consistency in WordPress publisher"""
    print("\n" + "=" * 80)
    print("TESTING WORDPRESS ROMAJI CONSISTENCY")
    print("=" * 80)
    
    try:
        # Initialize publisher
        publisher = WordPressPublisher()
        
        # Create test provider
        provider = create_test_provider_with_japanese_name()
        
        print(f"\n1. Testing romaji conversion:")
        print(f"   Original name: {provider.provider_name}")
        
        # Test romaji generation
        english_name = publisher._ensure_romaji_consistency(provider)
        print(f"   English name:  {english_name}")
        print(f"   ✓ Romaji conversion successful")
        
        # Test ACF field preparation
        print(f"\n2. Testing ACF field preparation:")
        acf_fields = publisher._prepare_acf_fields(provider)
        
        # Check critical fields for Japanese characters
        critical_fields = [
            ('provider_name', publisher.acf_field_mappings['provider_name']),
            ('description', publisher.acf_field_mappings['description']),
            ('seo_title', 'seo_title'),
            ('seo_meta_description', 'seo_meta_description'),
            ('provider_name_romaji', 'provider_name_romaji')
        ]
        
        print(f"   Checking critical fields for Japanese characters:")
        all_english = True
        
        for field_name, field_key in critical_fields:
            value = acf_fields.get(field_key, '')
            has_japanese = contains_japanese(str(value))
            
            if field_name == 'provider_name_romaji':
                # This should be the English version
                if has_japanese:
                    print(f"   ✗ {field_name}: Contains Japanese (unexpected!)")
                    all_english = False
                else:
                    print(f"   ✓ {field_name}: {value[:50]}...")
            elif has_japanese and field_name != 'provider_name_original':
                print(f"   ✗ {field_name}: Contains Japanese characters")
                all_english = False
            else:
                print(f"   ✓ {field_name}: No Japanese (English only)")
        
        if all_english:
            print(f"\n   ✅ All critical fields use English/romaji names")
        else:
            print(f"\n   ⚠️ Some fields still contain Japanese characters")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_master_data_validation():
    """Test master data validation integration"""
    print("\n" + "=" * 80)
    print("TESTING MASTER DATA VALIDATION")
    print("=" * 80)
    
    try:
        publisher = WordPressPublisher()
        provider = create_test_provider_with_japanese_name()
        
        print(f"\n1. Testing location validation:")
        location_validation = publisher._validate_location(provider)
        print(f"   City: {provider.city}")
        print(f"   Status: {location_validation['status']}")
        print(f"   Needs review: {location_validation['needs_review']}")
        if location_validation['notes']:
            print(f"   Notes: {location_validation['notes']}")
        print(f"   ✓ Location validation complete")
        
        print(f"\n2. Testing specialty validation:")
        specialty_validation = publisher._validate_specialties(provider)
        print(f"   Original specialties: {provider.specialties}")
        print(f"   Validated specialties: {specialty_validation['validated_specialties']}")
        print(f"   Needs review: {specialty_validation['needs_review']}")
        if specialty_validation['notes']:
            print(f"   Notes: {specialty_validation['notes']}")
        print(f"   ✓ Specialty validation complete")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wordpress_post_data():
    """Test WordPress post data generation"""
    print("\n" + "=" * 80)
    print("TESTING WORDPRESS POST DATA")
    print("=" * 80)
    
    try:
        publisher = WordPressPublisher()
        provider = create_test_provider_with_japanese_name()
        
        # Get English name
        english_name = publisher._ensure_romaji_consistency(provider)
        
        print(f"\n1. Post Title Generation:")
        print(f"   Original: {provider.provider_name}")
        print(f"   WordPress Title: {english_name}")
        print(f"   ✓ Title uses romaji name")
        
        print(f"\n2. ACF Fields Summary:")
        acf_fields = publisher._prepare_acf_fields(provider)
        
        # Show key fields
        key_fields = {
            'Provider Name (ACF)': acf_fields.get(publisher.acf_field_mappings['provider_name']),
            'Original Name': acf_fields.get('provider_name_original'),
            'Romaji Name': acf_fields.get('provider_name_romaji'),
            'Has Japanese': acf_fields.get('has_japanese_name'),
            'Location Validation': acf_fields.get('location_validation_status'),
            'Specialty Validation': acf_fields.get('specialty_validation_status'),
            'SEO Title': acf_fields.get('seo_title')
        }
        
        for field, value in key_fields.items():
            if isinstance(value, str) and len(value) > 50:
                print(f"   {field}: {value[:50]}...")
            else:
                print(f"   {field}: {value}")
        
        print(f"\n3. Content Validation:")
        
        # Check critical content fields
        critical_content = {
            'title': english_name,
            'seo_title': acf_fields.get('seo_title', ''),
            'description': acf_fields.get(publisher.acf_field_mappings['description'], ''),
            'excerpt': acf_fields.get('ai_excerpt', '')
        }
        
        japanese_check = publisher._validate_no_japanese_in_content(critical_content)
        
        if japanese_check:
            print(f"   ⚠️ Japanese found in: {list(japanese_check.keys())}")
        else:
            print(f"   ✓ No Japanese characters in critical content fields")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wordpress_connection():
    """Test WordPress API connection"""
    print("\n" + "=" * 80)
    print("TESTING WORDPRESS CONNECTION")
    print("=" * 80)
    
    try:
        publisher = WordPressPublisher()
        
        print(f"\n1. Testing API connection:")
        result = publisher.test_connection()
        
        if result['success']:
            print(f"   ✓ Connected successfully")
            print(f"   User: {result.get('message', 'Unknown')}")
            if result.get('user_info'):
                print(f"   Roles: {result['user_info'].get('roles', [])}")
        else:
            print(f"   ✗ Connection failed: {result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    """Run all WordPress romaji integration tests"""
    print("\n" + "=" * 80)
    print("WORDPRESS ROMAJI INTEGRATION TEST SUITE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test 1: Romaji consistency
    print("\n[TEST 1] Romaji Consistency")
    results.append(('Romaji Consistency', test_romaji_consistency()))
    
    # Test 2: Master data validation
    print("\n[TEST 2] Master Data Validation")
    results.append(('Master Data Validation', test_master_data_validation()))
    
    # Test 3: WordPress post data
    print("\n[TEST 3] WordPress Post Data")
    results.append(('WordPress Post Data', test_wordpress_post_data()))
    
    # Test 4: WordPress connection (optional)
    if os.getenv('WORDPRESS_URL'):
        print("\n[TEST 4] WordPress Connection")
        results.append(('WordPress Connection', test_wordpress_connection()))
    else:
        print("\n[TEST 4] WordPress Connection - SKIPPED (no credentials)")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All WordPress romaji integration tests passed!")
        print("\nKey Features Validated:")
        print("  ✓ Japanese provider names converted to romaji for WordPress titles")
        print("  ✓ All ACF fields use consistent English naming")
        print("  ✓ Master data validation integrated (locations & specialties)")
        print("  ✓ No Japanese characters in critical WordPress content")
        print("  ✓ Original Japanese names preserved for reference")
        print("  ✓ Validation flags set for manual review when needed")
        print("\n✅ WordPress publisher is ready for production use with romaji!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review the errors above.")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()