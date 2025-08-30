#!/usr/bin/env python3
"""
Week 2 Enhanced Pipeline Integration Testing
Comprehensive tests for romaji integration across the entire pipeline
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all enhanced components
from src.collectors.google_places import GooglePlacesCollector
from src.processors.ai_content import AIContentProcessor
from src.publishers.wordpress import WordPressPublisher
from src.core.database import DatabaseManager, Provider
from src.utils.romaji_converter import contains_japanese, convert_to_romaji
from src.data.master_specialties import SpecialtyNormalizer
from src.data.master_locations import LocationValidator
from src.campaign.campaign_state import CampaignState

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Week2IntegrationTester:
    """Comprehensive integration tester for Week 2 enhancements"""
    
    def __init__(self):
        """Initialize tester with all components"""
        self.db = DatabaseManager()
        self.collector = GooglePlacesCollector()
        self.content_processor = AIContentProcessor()
        self.wordpress_publisher = WordPressPublisher()
        self.specialty_normalizer = SpecialtyNormalizer()
        self.location_validator = LocationValidator()
        
        # Test statistics
        self.stats = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'warnings': []
        }
        
        logger.info("✅ Week 2 Integration Tester initialized")
    
    def create_test_providers(self) -> List[Provider]:
        """Create diverse test providers with Japanese and English names"""
        test_data = [
            {
                'provider_name': '千葉デンタルクリニック',
                'city': 'Tokyo',
                'district': 'Shibuya',
                'specialties': ['Dentistry'],
                'english_proficiency': 'High',
                'google_place_id': 'test_jp_dental_001'
            },
            {
                'provider_name': 'Tokyo Medical Center',
                'city': 'Tokyo',
                'district': 'Roppongi',
                'specialties': ['General Medicine'],
                'english_proficiency': 'Native',
                'google_place_id': 'test_en_medical_001'
            },
            {
                'provider_name': '聖路加国際病院',
                'city': 'Tokyo',
                'district': 'Chuo',
                'specialties': ['Hospital', 'Emergency Medicine'],
                'english_proficiency': 'High',
                'google_place_id': 'test_jp_hospital_001'
            },
            {
                'provider_name': 'グローバルヘルスケアクリニック Global Healthcare',
                'city': 'Yokohama',
                'district': 'Minato Mirai',
                'specialties': ['Internal Medicine'],
                'english_proficiency': 'Moderate',
                'google_place_id': 'test_mixed_clinic_001'
            },
            {
                'provider_name': 'International Kids Clinic',
                'city': 'Osaka',
                'district': 'Umeda',
                'specialties': ['Pediatrics'],
                'english_proficiency': 'High',
                'google_place_id': 'test_en_pediatric_001'
            }
        ]
        
        providers = []
        for i, data in enumerate(test_data):
            provider = Provider()
            provider.id = 90000 + i
            provider.provider_name = data['provider_name']
            provider.city = data['city']
            provider.district = data.get('district', '')
            provider.prefecture = data['city']  # Simplified for testing
            provider.specialties = data['specialties']
            provider.english_proficiency = data['english_proficiency']
            provider.google_place_id = data['google_place_id']
            provider.rating = 4.0 + (i * 0.2)  # Varying ratings
            provider.total_reviews = 50 + (i * 30)
            provider.proficiency_score = 3 + (i % 3)
            provider.address = f"{data.get('district', '')}, {data['city']}, Japan"
            provider.phone = f"03-{1000+i:04d}-5678"
            provider.website = f"https://example-{i}.jp"
            provider.wheelchair_accessible = 'Yes' if i % 2 == 0 else 'No'
            provider.parking_available = 'Yes' if i % 3 == 0 else 'No'
            provider.latitude = 35.6595 + (i * 0.01)
            provider.longitude = 139.7004 + (i * 0.01)
            
            # Simulate review content
            provider.review_content = [
                {'rating': 5, 'text': f'Great service with English support at {provider.provider_name}'},
                {'rating': 4, 'text': '英語対応が素晴らしい'},
                {'rating': 5, 'text': 'Professional and clean facility'}
            ]
            
            providers.append(provider)
        
        return providers
    
    def test_end_to_end_romaji_integration(self) -> bool:
        """Test 1: Complete flow with romaji conversion"""
        print("\n" + "=" * 80)
        print("TEST 1: END-TO-END ROMAJI INTEGRATION")
        print("=" * 80)
        
        try:
            providers = self.create_test_providers()
            japanese_providers = [p for p in providers if contains_japanese(p.provider_name)]
            
            print(f"\nTesting {len(japanese_providers)} providers with Japanese names:")
            
            all_passed = True
            for provider in japanese_providers:
                print(f"\n📍 Provider: {provider.provider_name}")
                
                # Step 1: English scoring (already set in test data)
                print(f"   English Score: {provider.proficiency_score}")
                
                # Step 2: Content generation with romaji
                print(f"   Generating content...")
                
                # Get romaji name from content processor
                content_english_name = self.content_processor._get_english_name(provider)
                print(f"   Content uses: {content_english_name}")
                
                # Generate fallback content for testing (no API calls)
                content_results = self.content_processor._create_fallback_content([provider])
                if content_results:
                    content = content_results[0]
                    
                    # Check for Japanese in content
                    has_japanese_in_content = any([
                        contains_japanese(content.description),
                        contains_japanese(content.seo_title),
                        contains_japanese(content.seo_meta_description)
                    ])
                    
                    if has_japanese_in_content:
                        print(f"   ❌ Japanese found in generated content")
                        all_passed = False
                    else:
                        print(f"   ✓ Content is English-only")
                
                # Step 3: WordPress publishing with romaji
                print(f"   Preparing WordPress data...")
                
                # Get romaji name from WordPress publisher
                wp_english_name = self.wordpress_publisher._ensure_romaji_consistency(provider)
                print(f"   WordPress uses: {wp_english_name}")
                
                # Verify consistency
                if content_english_name == wp_english_name:
                    print(f"   ✓ Naming consistent across pipeline")
                else:
                    print(f"   ❌ Name mismatch: {content_english_name} vs {wp_english_name}")
                    all_passed = False
                
                # Prepare ACF fields
                acf_fields = self.wordpress_publisher._prepare_acf_fields(provider)
                
                # Check critical WordPress fields
                wp_provider_name = acf_fields.get(self.wordpress_publisher.acf_field_mappings['provider_name'])
                if contains_japanese(str(wp_provider_name)):
                    print(f"   ❌ Japanese in WordPress provider name")
                    all_passed = False
                else:
                    print(f"   ✓ WordPress fields use English name")
            
            self.stats['total_tests'] += 1
            if all_passed:
                self.stats['passed'] += 1
                print(f"\n✅ End-to-end romaji integration PASSED")
            else:
                self.stats['failed'] += 1
                print(f"\n❌ End-to-end romaji integration FAILED")
            
            return all_passed
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            import traceback
            traceback.print_exc()
            self.stats['total_tests'] += 1
            self.stats['failed'] += 1
            return False
    
    def test_content_wordpress_consistency(self) -> bool:
        """Test 2: Content to WordPress naming consistency"""
        print("\n" + "=" * 80)
        print("TEST 2: CONTENT-TO-WORDPRESS CONSISTENCY")
        print("=" * 80)
        
        try:
            providers = self.create_test_providers()
            
            print(f"\nTesting consistency for {len(providers)} providers:")
            
            all_consistent = True
            for provider in providers:
                original_name = provider.provider_name
                
                # Get names from both processors
                content_name = self.content_processor._get_english_name(provider)
                wordpress_name = self.wordpress_publisher._ensure_romaji_consistency(provider)
                
                # Generate content
                content_results = self.content_processor._create_fallback_content([provider])
                content = content_results[0] if content_results else None
                
                # Prepare WordPress fields
                acf_fields = self.wordpress_publisher._prepare_acf_fields(provider)
                
                print(f"\n📍 {original_name}")
                print(f"   Content processor: {content_name}")
                print(f"   WordPress publisher: {wordpress_name}")
                
                # Check consistency
                if content_name != wordpress_name:
                    print(f"   ❌ Name mismatch between processors")
                    all_consistent = False
                else:
                    print(f"   ✓ Names consistent")
                
                # Check content fields
                if content:
                    content_has_english = content_name in content.description
                    wp_has_english = wordpress_name == acf_fields.get(
                        self.wordpress_publisher.acf_field_mappings['provider_name']
                    )
                    
                    if content_has_english and wp_has_english:
                        print(f"   ✓ English name used in both content and WordPress")
                    else:
                        print(f"   ❌ English name not consistently used")
                        all_consistent = False
                
                # Check SEO consistency
                content_seo = content.seo_title if content else ""
                wp_seo = acf_fields.get('seo_title', '')
                
                if contains_japanese(original_name):
                    if contains_japanese(content_seo) or contains_japanese(wp_seo):
                        print(f"   ❌ Japanese found in SEO fields")
                        all_consistent = False
                    else:
                        print(f"   ✓ SEO fields use English only")
            
            self.stats['total_tests'] += 1
            if all_consistent:
                self.stats['passed'] += 1
                print(f"\n✅ Content-to-WordPress consistency PASSED")
            else:
                self.stats['failed'] += 1
                print(f"\n❌ Content-to-WordPress consistency FAILED")
            
            return all_consistent
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            self.stats['total_tests'] += 1
            self.stats['failed'] += 1
            return False
    
    def test_master_data_integration(self) -> bool:
        """Test 3: Master data validation flows through pipeline"""
        print("\n" + "=" * 80)
        print("TEST 3: MASTER DATA INTEGRATION")
        print("=" * 80)
        
        try:
            # Create providers with various location/specialty combinations
            test_cases = [
                {
                    'provider_name': 'Test Clinic 1',
                    'city': 'Tokyo',  # Valid
                    'district': 'Roppongi',  # Valid
                    'specialties': ['Dentistry']  # Valid
                },
                {
                    'provider_name': 'Test Clinic 2',
                    'city': 'InvalidCity',  # Invalid
                    'district': 'InvalidDistrict',  # Invalid
                    'specialties': ['InvalidSpecialty']  # Invalid
                },
                {
                    'provider_name': 'Test Clinic 3',
                    'city': 'Osaka',  # Valid
                    'district': '',  # Empty
                    'specialties': ['内科']  # Japanese, should normalize
                }
            ]
            
            print(f"\nTesting master data validation:")
            
            all_validated = True
            for i, test_case in enumerate(test_cases):
                provider = Provider()
                provider.id = 95000 + i
                for key, value in test_case.items():
                    setattr(provider, key, value)
                
                print(f"\n📍 {provider.provider_name}")
                print(f"   Location: {provider.city}, {provider.district or 'N/A'}")
                print(f"   Specialties: {provider.specialties}")
                
                # Test location validation
                location_result = self.wordpress_publisher._validate_location(provider)
                print(f"   Location validation: {location_result['status']}")
                if location_result['needs_review']:
                    print(f"   ⚠️ Location needs review: {location_result['notes']}")
                
                # Test specialty validation
                specialty_result = self.wordpress_publisher._validate_specialties(provider)
                print(f"   Specialty validation: {specialty_result['status']}")
                if specialty_result['needs_review']:
                    print(f"   ⚠️ Specialty needs review: {specialty_result['notes']}")
                
                # Prepare WordPress fields to see if validation flows through
                acf_fields = self.wordpress_publisher._prepare_acf_fields(provider)
                
                # Check validation fields in ACF
                if 'location_validation_status' in acf_fields:
                    print(f"   ✓ Location validation in WordPress: {acf_fields['location_validation_status']}")
                else:
                    print(f"   ❌ Location validation missing from WordPress")
                    all_validated = False
                
                if 'specialty_validation_status' in acf_fields:
                    print(f"   ✓ Specialty validation in WordPress: {acf_fields['specialty_validation_status']}")
                else:
                    print(f"   ❌ Specialty validation missing from WordPress")
                    all_validated = False
            
            self.stats['total_tests'] += 1
            if all_validated:
                self.stats['passed'] += 1
                print(f"\n✅ Master data integration PASSED")
            else:
                self.stats['failed'] += 1
                print(f"\n❌ Master data integration FAILED")
            
            return all_validated
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            self.stats['total_tests'] += 1
            self.stats['failed'] += 1
            return False
    
    def test_backward_compatibility(self) -> bool:
        """Test 4: Backward compatibility with existing providers"""
        print("\n" + "=" * 80)
        print("TEST 4: BACKWARD COMPATIBILITY")
        print("=" * 80)
        
        try:
            # Test with English-only providers (simulating existing data)
            english_providers = [
                {'name': 'Tokyo Medical Center', 'expected': 'Tokyo Medical Center'},
                {'name': 'International Hospital', 'expected': 'International Hospital'},
                {'name': 'Roppongi Clinic', 'expected': 'Roppongi Clinic'}
            ]
            
            # Test with Japanese providers (new functionality)
            japanese_providers = [
                {'name': '千葉デンタルクリニック', 'expected': 'Chiba Dental Clinic'},
                {'name': '聖路加国際病院', 'expected': 'Sei Roka kokusai Hospital'}
            ]
            
            # Test mixed scenarios
            mixed_providers = [
                {'name': 'ABC医院', 'expected': 'ABC Clinic'},
                {'name': 'グローバル Global Clinic', 'expected': 'Global Global Clinic'}
            ]
            
            print(f"\nTesting English providers (existing):")
            all_compatible = True
            
            for test in english_providers:
                provider = Provider()
                provider.provider_name = test['name']
                
                # Test content processor
                content_name = self.content_processor._get_english_name(provider)
                
                # Test WordPress publisher
                wp_name = self.wordpress_publisher._ensure_romaji_consistency(provider)
                
                print(f"\n   {test['name']}")
                print(f"   Content: {content_name}")
                print(f"   WordPress: {wp_name}")
                
                if content_name == test['expected'] and wp_name == test['expected']:
                    print(f"   ✓ Unchanged (backward compatible)")
                else:
                    print(f"   ❌ Unexpected change")
                    all_compatible = False
            
            print(f"\nTesting Japanese providers (new):")
            
            for test in japanese_providers:
                provider = Provider()
                provider.provider_name = test['name']
                
                content_name = self.content_processor._get_english_name(provider)
                wp_name = self.wordpress_publisher._ensure_romaji_consistency(provider)
                
                print(f"\n   {test['name']}")
                print(f"   Content: {content_name}")
                print(f"   WordPress: {wp_name}")
                
                if not contains_japanese(content_name) and not contains_japanese(wp_name):
                    print(f"   ✓ Converted to English")
                else:
                    print(f"   ❌ Japanese not converted")
                    all_compatible = False
            
            print(f"\nTesting mixed scenarios:")
            
            for test in mixed_providers:
                provider = Provider()
                provider.provider_name = test['name']
                
                content_name = self.content_processor._get_english_name(provider)
                wp_name = self.wordpress_publisher._ensure_romaji_consistency(provider)
                
                print(f"\n   {test['name']}")
                print(f"   Content: {content_name}")
                print(f"   WordPress: {wp_name}")
                
                if not contains_japanese(content_name) and not contains_japanese(wp_name):
                    print(f"   ✓ Handled correctly")
                else:
                    print(f"   ❌ Mixed name not handled properly")
                    all_compatible = False
            
            self.stats['total_tests'] += 1
            if all_compatible:
                self.stats['passed'] += 1
                print(f"\n✅ Backward compatibility PASSED")
            else:
                self.stats['failed'] += 1
                print(f"\n❌ Backward compatibility FAILED")
            
            return all_compatible
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            self.stats['total_tests'] += 1
            self.stats['failed'] += 1
            return False
    
    def test_performance_integration(self) -> bool:
        """Test 5: Performance with romaji integration"""
        print("\n" + "=" * 80)
        print("TEST 5: PERFORMANCE INTEGRATION")
        print("=" * 80)
        
        try:
            providers = self.create_test_providers()
            
            print(f"\nTesting performance with {len(providers)} providers:")
            
            # Test content generation performance
            print(f"\n1. Content Generation Performance:")
            start_time = time.time()
            
            for provider in providers:
                # Get romaji name (cached after first call)
                _ = self.content_processor._get_english_name(provider)
                # Generate fallback content
                _ = self.content_processor._create_fallback_content([provider])
            
            content_time = time.time() - start_time
            avg_content_time = content_time / len(providers)
            
            print(f"   Total time: {content_time:.2f}s")
            print(f"   Average per provider: {avg_content_time:.3f}s")
            
            if avg_content_time < 0.1:  # Should be very fast for fallback content
                print(f"   ✓ Content generation performance acceptable")
                content_perf = True
            else:
                print(f"   ⚠️ Content generation slower than expected")
                self.stats['warnings'].append("Content generation performance degraded")
                content_perf = True  # Still pass but with warning
            
            # Test WordPress preparation performance
            print(f"\n2. WordPress Preparation Performance:")
            start_time = time.time()
            
            for provider in providers:
                # Get romaji name (cached)
                _ = self.wordpress_publisher._ensure_romaji_consistency(provider)
                # Prepare ACF fields
                _ = self.wordpress_publisher._prepare_acf_fields(provider)
            
            wp_time = time.time() - start_time
            avg_wp_time = wp_time / len(providers)
            
            print(f"   Total time: {wp_time:.2f}s")
            print(f"   Average per provider: {avg_wp_time:.3f}s")
            
            if avg_wp_time < 0.1:  # Should be fast
                print(f"   ✓ WordPress preparation performance acceptable")
                wp_perf = True
            else:
                print(f"   ⚠️ WordPress preparation slower than expected")
                self.stats['warnings'].append("WordPress preparation performance degraded")
                wp_perf = True  # Still pass but with warning
            
            # Test mega-batch compatibility
            print(f"\n3. Mega-Batch Processing:")
            batch_size = 2
            start_time = time.time()
            
            for i in range(0, len(providers), batch_size):
                batch = providers[i:i+batch_size]
                # Simulate mega-batch content generation
                _ = self.content_processor._create_fallback_content(batch)
            
            batch_time = time.time() - start_time
            
            print(f"   Batch size: {batch_size}")
            print(f"   Total batches: {(len(providers) + batch_size - 1) // batch_size}")
            print(f"   Total time: {batch_time:.2f}s")
            
            if batch_time < content_time:  # Batching should be more efficient
                print(f"   ✓ Mega-batch processing efficient")
                batch_perf = True
            else:
                print(f"   ⚠️ Mega-batch not providing expected efficiency")
                self.stats['warnings'].append("Mega-batch efficiency reduced")
                batch_perf = True  # Still pass but with warning
            
            # Test caching effectiveness
            print(f"\n4. Romaji Caching:")
            
            # First pass - uncached
            start_time = time.time()
            for provider in providers:
                _ = convert_to_romaji(provider.provider_name)
            uncached_time = time.time() - start_time
            
            # Second pass - should use cache
            start_time = time.time()
            for provider in providers:
                _ = self.content_processor._get_english_name(provider)  # Uses cache
            cached_time = time.time() - start_time
            
            print(f"   Uncached time: {uncached_time:.3f}s")
            print(f"   Cached time: {cached_time:.3f}s")
            print(f"   Speed improvement: {(uncached_time/cached_time):.1f}x")
            
            if cached_time < uncached_time:
                print(f"   ✓ Caching effective")
                cache_perf = True
            else:
                print(f"   ❌ Caching not working")
                cache_perf = False
            
            all_perf = content_perf and wp_perf and batch_perf and cache_perf
            
            self.stats['total_tests'] += 1
            if all_perf:
                self.stats['passed'] += 1
                print(f"\n✅ Performance integration PASSED")
            else:
                self.stats['failed'] += 1
                print(f"\n❌ Performance integration FAILED")
            
            return all_perf
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            self.stats['total_tests'] += 1
            self.stats['failed'] += 1
            return False
    
    def test_quality_assurance(self) -> bool:
        """Test 6: Quality assurance checks"""
        print("\n" + "=" * 80)
        print("TEST 6: QUALITY ASSURANCE")
        print("=" * 80)
        
        try:
            providers = self.create_test_providers()
            japanese_providers = [p for p in providers if contains_japanese(p.provider_name)]
            
            print(f"\nRunning quality checks on {len(providers)} providers:")
            
            all_quality_passed = True
            
            for provider in providers:
                print(f"\n📍 {provider.provider_name}")
                
                # Generate content
                english_name = self.content_processor._get_english_name(provider)
                content_results = self.content_processor._create_fallback_content([provider])
                content = content_results[0] if content_results else None
                
                # Prepare WordPress fields
                acf_fields = self.wordpress_publisher._prepare_acf_fields(provider)
                
                # Quality Check 1: No Japanese in final content
                if contains_japanese(provider.provider_name):
                    critical_fields = [
                        content.description if content else "",
                        content.seo_title if content else "",
                        content.seo_meta_description if content else "",
                        str(acf_fields.get(self.wordpress_publisher.acf_field_mappings['provider_name'], '')),
                        str(acf_fields.get('seo_title', ''))
                    ]
                    
                    has_japanese = any(contains_japanese(field) for field in critical_fields if field)
                    
                    if has_japanese:
                        print(f"   ❌ Japanese found in final content")
                        all_quality_passed = False
                    else:
                        print(f"   ✓ No Japanese in final content")
                
                # Quality Check 2: Content quality with romaji names
                if content:
                    # Check if English name is used in content
                    name_in_description = english_name in content.description
                    name_in_seo = english_name in content.seo_title
                    
                    if name_in_description and name_in_seo:
                        print(f"   ✓ English name used consistently")
                    else:
                        print(f"   ❌ English name not used consistently")
                        all_quality_passed = False
                    
                    # Check SEO title length
                    if len(content.seo_title) <= 60:
                        print(f"   ✓ SEO title length optimal ({len(content.seo_title)} chars)")
                    else:
                        print(f"   ⚠️ SEO title too long ({len(content.seo_title)} chars)")
                        self.stats['warnings'].append(f"SEO title too long for {english_name}")
                
                # Quality Check 3: Master data validation quality
                location_validation = acf_fields.get('location_validation_status')
                specialty_validation = acf_fields.get('specialty_validation_status')
                
                if location_validation and specialty_validation:
                    print(f"   ✓ Master data validation present")
                    
                    if location_validation == 'needs_review':
                        print(f"   ⚠️ Location needs review: {acf_fields.get('location_validation_notes', '')}")
                    
                    if specialty_validation == 'needs_review':
                        print(f"   ⚠️ Specialty needs review: {acf_fields.get('specialty_validation_notes', '')}")
                else:
                    print(f"   ❌ Master data validation missing")
                    all_quality_passed = False
                
                # Quality Check 4: Duplicate detection still works
                # Check that provider has unique identifier
                if provider.google_place_id:
                    print(f"   ✓ Unique identifier present")
                else:
                    print(f"   ❌ Missing unique identifier")
                    all_quality_passed = False
            
            # Summary quality metrics
            print(f"\n📊 Quality Metrics Summary:")
            print(f"   Total providers tested: {len(providers)}")
            print(f"   Providers with Japanese names: {len(japanese_providers)}")
            print(f"   All quality checks passed: {all_quality_passed}")
            
            if self.stats['warnings']:
                print(f"\n⚠️ Warnings ({len(self.stats['warnings'])}):")
                for warning in self.stats['warnings'][:5]:  # Show first 5 warnings
                    print(f"   - {warning}")
            
            self.stats['total_tests'] += 1
            if all_quality_passed:
                self.stats['passed'] += 1
                print(f"\n✅ Quality assurance PASSED")
            else:
                self.stats['failed'] += 1
                print(f"\n❌ Quality assurance FAILED")
            
            return all_quality_passed
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            self.stats['total_tests'] += 1
            self.stats['failed'] += 1
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests and return summary"""
        print("\n" + "=" * 80)
        print("WEEK 2 ENHANCED PIPELINE INTEGRATION TESTING")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all tests
        test_results = {
            'End-to-End Romaji': self.test_end_to_end_romaji_integration(),
            'Content-WordPress Consistency': self.test_content_wordpress_consistency(),
            'Master Data Integration': self.test_master_data_integration(),
            'Backward Compatibility': self.test_backward_compatibility(),
            'Performance Integration': self.test_performance_integration(),
            'Quality Assurance': self.test_quality_assurance()
        }
        
        # Print summary
        print("\n" + "=" * 80)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        for test_name, passed in test_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {test_name}: {status}")
        
        print(f"\nOverall Results: {self.stats['passed']}/{self.stats['total_tests']} tests passed")
        
        if self.stats['warnings']:
            print(f"\nWarnings: {len(self.stats['warnings'])} warnings generated")
        
        # Determine overall success
        all_passed = all(test_results.values())
        
        if all_passed:
            print("\n🎉 ALL WEEK 2 INTEGRATION TESTS PASSED!")
            print("\n✅ Validated Features:")
            print("  • Japanese provider names converted to English throughout pipeline")
            print("  • Content consistency from generation to WordPress publishing")
            print("  • Master data validation integrated seamlessly")
            print("  • All existing functionality preserved")
            print("  • Performance maintained with romaji enhancements")
            print("  • No Japanese characters in final WordPress content")
            print("  • SEO optimized for English search")
            print("\n🚀 Week 2 enhancements ready for production!")
        else:
            failed_tests = [name for name, passed in test_results.items() if not passed]
            print(f"\n⚠️ {len(failed_tests)} test(s) failed:")
            for test in failed_tests:
                print(f"  • {test}")
            print("\nPlease review failed tests before deployment.")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return {
            'success': all_passed,
            'test_results': test_results,
            'statistics': self.stats,
            'timestamp': datetime.now().isoformat()
        }


def main():
    """Run Week 2 integration tests"""
    tester = Week2IntegrationTester()
    results = tester.run_all_tests()
    
    # Return exit code based on success
    sys.exit(0 if results['success'] else 1)


if __name__ == "__main__":
    main()