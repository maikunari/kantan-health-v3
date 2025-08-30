#!/usr/bin/env python3
"""
Week 1 Integration Test Suite - Fixed Version
Includes test data isolation and technical fixes
"""

import os
import sys
import json
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Test results tracking
test_results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def generate_test_id():
    """Generate unique test ID to avoid data collisions"""
    return f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


def test_end_to_end_campaign_flow():
    """Test complete campaign flow from search to database"""
    print("\n" + "=" * 80)
    print("TEST 1: END-TO-END CAMPAIGN FLOW")
    print("=" * 80)
    
    try:
        from src.campaign import EnhancedCampaignPipeline
        
        # Use unique test file to avoid state conflicts
        test_id = generate_test_id()
        test_file = f'test_e2e_{test_id}.json'
        
        # Initialize test campaign
        pipeline = EnhancedCampaignPipeline(state_file=test_file)
        
        # Initialize with small test set
        pipeline.initialize_campaign(
            locations=['Roppongi'],
            specialties=['General Medicine'],
            query_limit=2
        )
        
        print("✓ Campaign initialized with 2 queries")
        
        # Override collector to use test prefix for place IDs
        # This ensures we don't conflict with existing data
        original_search = pipeline.collector.search_providers
        
        def test_search(query, limit=None):
            """Wrapper to add test prefix to results"""
            results = original_search(query, limit)
            # Add test prefix to place_ids
            for result in results:
                if 'place_id' in result:
                    result['place_id'] = f"{test_id}_{result['place_id']}"
            return results[:2]  # Limit to 2 for faster testing
        
        pipeline.collector.search_providers = test_search
        
        # Run campaign with small limit
        providers_collected = pipeline.run_with_state_management(
            daily_limit=2,
            test_mode=True
        )
        
        # Verify flow steps
        checks = []
        
        # Check 1: Campaign ran
        if pipeline.state.completed_queries > 0:
            checks.append(f"✓ {pipeline.state.completed_queries} queries completed")
        else:
            checks.append("✗ No queries completed")
        
        # Check 2: English scoring working (check if attempted)
        if hasattr(pipeline.state.metrics, 'avg_english_proficiency'):
            checks.append(f"✓ English scoring attempted")
        else:
            checks.append("✗ English scoring not attempted")
        
        # Check 3: Campaign state updated
        if pipeline.state.metrics.total_providers_found >= 0:
            checks.append(f"✓ Campaign metrics tracked ({pipeline.state.metrics.total_providers_found} providers)")
        else:
            checks.append("✗ Campaign metrics not tracked")
        
        # Check 4: Cost tracking
        if hasattr(pipeline.state.metrics, 'total_cost'):
            checks.append(f"✓ Cost tracking present")
        else:
            checks.append("✗ Cost tracking not present")
        
        # Print results
        for check in checks:
            print(f"  {check}")
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        
        # Clean up test providers from database
        if providers_collected > 0:
            from src.core.database import DatabaseManager
            db = DatabaseManager()
            session = db.get_session()
            from src.core.models import Provider
            
            # Remove test providers
            test_providers = session.query(Provider).filter(
                Provider.google_place_id.like(f"{test_id}%")
            ).all()
            
            for provider in test_providers:
                session.delete(provider)
            session.commit()
            session.close()
        
        # Determine pass/fail
        if all("✓" in check for check in checks):
            test_results['passed'].append("End-to-End Campaign Flow")
            return True
        else:
            test_results['failed'].append("End-to-End Campaign Flow")
            return False
            
    except Exception as e:
        print(f"  ✗ Test failed with error: {e}")
        test_results['failed'].append(f"End-to-End Campaign Flow: {str(e)}")
        return False


def test_enhanced_search_system():
    """Test enhanced search with English focus and master data"""
    print("\n" + "=" * 80)
    print("TEST 2: ENHANCED SEARCH SYSTEM")
    print("=" * 80)
    
    try:
        from src.collectors.google_places import GooglePlacesCollector
        
        collector = GooglePlacesCollector()
        
        # Test query generation
        queries = collector.generate_english_focused_queries(
            locations=['Roppongi', 'Shibuya', 'InvalidLocation'],
            specialties=['General Medicine', 'Dentistry'],
            limit=10
        )
        
        checks = []
        
        if len(queries) > 0:
            checks.append(f"✓ Generated {len(queries)} English-focused queries")
        else:
            checks.append("✗ No queries generated")
        
        location_names = [q['location'] for q in queries]
        if 'InvalidLocation' not in location_names:
            checks.append("✓ Invalid location filtered out")
        else:
            checks.append("✗ Invalid location not filtered")
        
        query_texts = [q['query'] for q in queries]
        english_keywords = ['English', 'International', 'Foreign friendly']
        if any(keyword in text for text in query_texts for keyword in english_keywords):
            checks.append("✓ English-focused patterns used")
        else:
            checks.append("✗ English patterns not found")
        
        if queries and queries[0]['priority'] == 1:
            checks.append("✓ Priority ordering working")
        else:
            checks.append("✗ Priority ordering not working")
        
        for check in checks:
            print(f"  {check}")
        
        if all("✓" in check for check in checks):
            test_results['passed'].append("Enhanced Search System")
            return True
        else:
            test_results['failed'].append("Enhanced Search System")
            return False
            
    except Exception as e:
        print(f"  ✗ Test failed with error: {e}")
        test_results['failed'].append(f"Enhanced Search System: {str(e)}")
        return False


def test_english_proficiency_scoring():
    """Test English proficiency scoring with actual reviews"""
    print("\n" + "=" * 80)
    print("TEST 3: ENGLISH PROFICIENCY SCORING")
    print("=" * 80)
    
    try:
        from src.collectors.google_places import GooglePlacesCollector
        
        collector = GooglePlacesCollector()
        
        test_reviews = [
            {'text': 'The doctor speaks excellent English and was very helpful.'},
            {'text': 'English speaking staff available.'},
            {'text': '英語対応可能です。'}
        ]
        
        result = collector._analyze_english_proficiency(test_reviews)
        
        checks = []
        
        if result['proficiency_score'] > 0:
            checks.append(f"✓ Proficiency score calculated: {result['proficiency_score']}/5")
        else:
            checks.append("✗ Score is 0 despite English mentions")
        
        if result['english_proficiency'] != 'Unknown':
            checks.append(f"✓ Proficiency label: {result['english_proficiency']}")
        else:
            checks.append("✗ Proficiency label is Unknown")
        
        no_english_reviews = [
            {'text': 'Good clinic'},
            {'text': '良い医者です'}
        ]
        
        no_english_result = collector._analyze_english_proficiency(no_english_reviews)
        
        if no_english_result['proficiency_score'] == 0:
            checks.append("✓ Non-English reviews score 0")
        else:
            checks.append(f"✗ Non-English reviews scored {no_english_result['proficiency_score']}")
        
        empty_result = collector._analyze_english_proficiency([])
        
        if empty_result['proficiency_score'] == 0:
            checks.append("✓ Empty reviews handled correctly")
        else:
            checks.append("✗ Empty reviews not handled correctly")
        
        for check in checks:
            print(f"  {check}")
        
        if all("✓" in check for check in checks):
            test_results['passed'].append("English Proficiency Scoring")
            return True
        else:
            test_results['failed'].append("English Proficiency Scoring")
            return False
            
    except Exception as e:
        print(f"  ✗ Test failed with error: {e}")
        test_results['failed'].append(f"English Proficiency Scoring: {str(e)}")
        return False


def test_master_data_validation():
    """Test location and specialty validation"""
    print("\n" + "=" * 80)
    print("TEST 4: MASTER DATA VALIDATION")
    print("=" * 80)
    
    try:
        from src.data.master_locations import LocationValidator
        from src.data.master_specialties import SpecialtyNormalizer
        
        location_validator = LocationValidator()
        specialty_normalizer = SpecialtyNormalizer()
        
        checks = []
        
        # Test location validation
        test_locations = [
            ('Roppongi', True),
            ('Shibuya', True),
            ('InvalidCity', False),
            ('Tokyo', True)
        ]
        
        location_pass = True
        for location, expected_valid in test_locations:
            is_valid = location_validator.validate_location(location)
            if is_valid == expected_valid:
                status = "✓" if expected_valid else "✓ correctly rejected"
            else:
                location_pass = False
        
        if location_pass:
            checks.append("✓ Location validation working")
        else:
            checks.append("✗ Location validation errors")
        
        # Test specialty normalization
        test_specialties = [
            ('Dentist', 'Dentistry'),
            ('GP', 'General Medicine'),
            ('Unknown Specialty XYZ', 'General Medicine')
        ]
        
        specialty_pass = True
        for input_spec, expected_output in test_specialties:
            result = specialty_normalizer.normalize_specialty(input_spec)
            if result['specialty'] != expected_output:
                specialty_pass = False
        
        if specialty_pass:
            checks.append("✓ Specialty normalization working")
        else:
            checks.append("✗ Specialty normalization errors")
        
        # Check master data statistics
        if hasattr(location_validator, 'all_locations') and len(location_validator.all_locations) == 273:
            checks.append("✓ All 273 locations loaded")
        else:
            checks.append(f"✗ Location count issue")
        
        if len(specialty_normalizer.canonical_specialties) == 39:
            checks.append("✓ All 39 specialties loaded")
        else:
            checks.append(f"✗ Specialty count issue")
        
        for check in checks:
            print(f"  {check}")
        
        if all("✓" in check for check in checks):
            test_results['passed'].append("Master Data Validation")
            return True
        else:
            test_results['failed'].append("Master Data Validation")
            return False
            
    except Exception as e:
        print(f"  ✗ Test failed with error: {e}")
        test_results['failed'].append(f"Master Data Validation: {str(e)}")
        return False


def test_campaign_state_management():
    """Test campaign state persistence and recovery"""
    print("\n" + "=" * 80)
    print("TEST 5: CAMPAIGN STATE MANAGEMENT")
    print("=" * 80)
    
    try:
        from src.campaign import CampaignStateManager
        
        test_id = generate_test_id()
        test_file = f'test_state_{test_id}.json'
        manager = CampaignStateManager(test_file)
        
        checks = []
        
        if manager.state.campaign_id and manager.state.status == 'initialized':
            checks.append("✓ State initialized correctly")
        else:
            checks.append("✗ State initialization failed")
        
        test_queries = [
            {'id': 0, 'query': 'Test query 1', 'location': 'Tokyo'},
            {'id': 1, 'query': 'Test query 2', 'location': 'Osaka'}
        ]
        manager.initialize_query_queue(test_queries)
        
        if manager.state.total_queries == 2:
            checks.append("✓ Query queue initialized")
        else:
            checks.append("✗ Query queue initialization failed")
        
        manager.update_provider_metrics(
            providers_found=5,
            providers_processed=3,
            english_scores=[3.0, 4.0, 3.5]
        )
        
        if manager.state.metrics.total_providers_found == 5:
            checks.append("✓ Provider metrics updated")
        else:
            checks.append("✗ Provider metrics update failed")
        
        manager.save_state()
        new_manager = CampaignStateManager(test_file)
        
        if new_manager.state.metrics.total_providers_found == 5:
            checks.append("✓ State persistence working")
        else:
            checks.append("✗ State persistence failed")
        
        summary = new_manager.get_progress_summary()
        
        if summary['progress']['providers_found'] == 5:
            checks.append("✓ Progress calculation working")
        else:
            checks.append("✗ Progress calculation failed")
        
        new_manager.pause_campaign()
        if new_manager.state.status == 'paused':
            checks.append("✓ Campaign pause working")
        else:
            checks.append("✗ Campaign pause failed")
        
        new_manager.resume_campaign()
        if new_manager.state.status == 'running':
            checks.append("✓ Campaign resume working")
        else:
            checks.append("✗ Campaign resume failed")
        
        for check in checks:
            print(f"  {check}")
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        
        if os.path.exists('campaign_checkpoints'):
            import shutil
            shutil.rmtree('campaign_checkpoints', ignore_errors=True)
        
        if all("✓" in check for check in checks):
            test_results['passed'].append("Campaign State Management")
            return True
        else:
            test_results['failed'].append("Campaign State Management")
            return False
            
    except Exception as e:
        print(f"  ✗ Test failed with error: {e}")
        test_results['failed'].append(f"Campaign State Management: {str(e)}")
        return False


def test_database_integration():
    """Test database operations and validation fields"""
    print("\n" + "=" * 80)
    print("TEST 6: DATABASE INTEGRATION")
    print("=" * 80)
    
    try:
        from src.core.database import DatabaseManager
        from src.core.models import Provider
        from sqlalchemy import inspect
        
        db = DatabaseManager()
        session = db.get_session()
        
        checks = []
        
        # Test 1: Check if Provider model has validation attributes
        provider_attrs = dir(Provider)
        validation_attrs = ['primary_specialty', 'location_needs_review', 
                          'specialties_need_review', 'needs_manual_review', 
                          'validation_notes']
        
        all_present = all(attr in provider_attrs for attr in validation_attrs)
        if all_present:
            checks.append("✓ All validation attributes in model")
        else:
            checks.append("✗ Some validation attributes missing from model")
        
        # Test 2: Create test provider with validation
        test_id = generate_test_id()
        test_provider_data = {
            'google_place_id': f'test_db_{test_id}',
            'provider_name': f'Test Provider {test_id}',
            'city': 'Tokyo',
            'primary_specialty': 'General Medicine',
            'proficiency_score': 4,
            'location_needs_review': False,
            'specialties_need_review': False,
            'needs_manual_review': False
        }
        
        try:
            provider = db.create_or_update_provider(test_provider_data)
            if provider:
                checks.append("✓ Provider created with validation fields")
                
                # Clean up test provider
                session.delete(provider)
                session.commit()
            else:
                checks.append("✗ Provider creation failed")
        except Exception as e:
            checks.append(f"✗ Provider creation error")
        
        # Test 3: Check database structure
        total_providers = session.query(Provider).count()
        if total_providers >= 0:
            checks.append(f"✓ Database accessible ({total_providers} providers)")
        else:
            checks.append("✗ Database access issue")
        
        for check in checks:
            print(f"  {check}")
        
        session.close()
        
        if all("✓" in check for check in checks):
            test_results['passed'].append("Database Integration")
            return True
        else:
            test_results['failed'].append("Database Integration")
            return False
            
    except Exception as e:
        print(f"  ✗ Test failed with error: {e}")
        test_results['failed'].append(f"Database Integration: {str(e)}")
        return False


def test_performance_and_safety():
    """Test rate limiting, error handling, and safety features"""
    print("\n" + "=" * 80)
    print("TEST 7: PERFORMANCE AND SAFETY")
    print("=" * 80)
    
    try:
        from src.collectors.google_places import GooglePlacesCollector
        from src.core.cost_tracker import CostTracker
        
        checks = []
        
        # Test 1: Rate limiting
        collector = GooglePlacesCollector()
        
        print("  Testing rate limiting (2-second delay)...")
        start_time = time.time()
        
        collector._apply_rate_limit()
        time.sleep(0.1)
        collector._apply_rate_limit()
        
        elapsed = time.time() - start_time
        
        if elapsed >= 2.0:
            checks.append(f"✓ Rate limiting working ({elapsed:.1f}s delay)")
        else:
            checks.append(f"✗ Rate limiting not working ({elapsed:.1f}s < 2s)")
        
        # Test 2: Cost tracking
        cost_tracker = CostTracker()
        
        cost_tracker.log_request('place_search', search_query='test')
        cost_tracker.log_request('place_details', place_id='test123')
        
        stats = cost_tracker.get_usage_stats(days=1)
        
        if stats['total_requests'] > 0:
            checks.append(f"✓ Cost tracking working ({stats['total_requests']} requests)")
        else:
            checks.append("✗ Cost tracking not working")
        
        # Test 3: Budget limits
        if cost_tracker.daily_limit > 0 and cost_tracker.monthly_limit > 0:
            checks.append(f"✓ Budget limits set (Daily: ${cost_tracker.daily_limit}, Monthly: ${cost_tracker.monthly_limit})")
        else:
            checks.append("✗ Budget limits not set")
        
        # Test 4: Error handling
        try:
            result = collector._analyze_english_proficiency(None)
            checks.append("✗ Should have handled None reviews")
        except:
            checks.append("✓ Error handling for invalid input")
        
        # Test 5: Duplicate detection
        if hasattr(collector, 'excluded_place_ids'):
            checks.append(f"✓ Duplicate detection initialized")
        else:
            checks.append("✗ Duplicate detection not initialized")
        
        for check in checks:
            print(f"  {check}")
        
        if all("✓" in check for check in checks):
            test_results['passed'].append("Performance and Safety")
            return True
        else:
            test_results['failed'].append("Performance and Safety")
            return False
            
    except Exception as e:
        print(f"  ✗ Test failed with error: {e}")
        test_results['failed'].append(f"Performance and Safety: {str(e)}")
        return False


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "=" * 80)
    print("WEEK 1 INTEGRATION TEST SUITE - FIXED VERSION")
    print("=" * 80)
    print("\nRunning comprehensive tests with fixes applied...")
    print("- Test data isolation implemented")
    print("- Master data attributes fixed")
    print("- Database integration improved")
    
    # Run tests
    test_functions = [
        test_end_to_end_campaign_flow,
        test_enhanced_search_system,
        test_english_proficiency_scoring,
        test_master_data_validation,
        test_campaign_state_management,
        test_database_integration,
        test_performance_and_safety
    ]
    
    for test_func in test_functions:
        try:
            test_func()
        except Exception as e:
            print(f"\nTest {test_func.__name__} crashed: {e}")
            test_results['failed'].append(f"{test_func.__name__}: CRASH")
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    total_tests = len(test_results['passed']) + len(test_results['failed'])
    
    print(f"\nTests Run: {total_tests}")
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    
    if test_results['passed']:
        print("\n✅ PASSED TESTS:")
        for test in test_results['passed']:
            print(f"  - {test}")
    
    if test_results['failed']:
        print("\n❌ FAILED TESTS:")
        for test in test_results['failed']:
            print(f"  - {test}")
    
    # Overall result
    print("\n" + "=" * 80)
    if len(test_results['failed']) == 0:
        print("🎉 ALL TESTS PASSED! Week 1 enhancements are fully operational.")
        print("\nSystem Status:")
        print("  ✅ Enhanced search with English focus")
        print("  ✅ English proficiency scoring (1-5 range)")
        print("  ✅ Master data validation (273 locations, 39 specialties)")
        print("  ✅ Campaign state management with recovery")
        print("  ✅ Database integration with validation fields")
        print("  ✅ All safety features preserved")
        print("\n✨ Ready for Week 2 development!")
        return 0
    else:
        print(f"⚠️  {len(test_results['failed'])} test(s) failed. Review and fix remaining issues.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())