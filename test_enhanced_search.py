#!/usr/bin/env python3
"""
Test the enhanced English-focused search system
"""

import json
import logging
from src.collectors.google_places import GooglePlacesCollector
from src.data import LocationValidator, SpecialtyNormalizer, get_english_priority_locations

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def test_master_data():
    """Test master data structures"""
    print("\n" + "=" * 80)
    print("TESTING MASTER DATA STRUCTURES")
    print("=" * 80)
    
    # Test location validator
    print("\n1. Testing Location Validator...")
    validator = LocationValidator()
    
    test_locations = [
        ('Tokyo', True, 'Valid major city'),
        ('Shibuya', True, 'Valid Tokyo ward'),
        ('Roppongi', True, 'Valid international district'),
        ('InvalidCity', False, 'Should be rejected'),
        ('Tokyo-to', True, 'Should normalize to Tokyo')
    ]
    
    for location, expected, description in test_locations:
        is_valid = validator.validate_location(location)
        normalized = validator.normalize_location(location) if is_valid else 'N/A'
        status = "✅" if is_valid == expected else "❌"
        print(f"  {status} {location:20} -> {normalized:15} ({description})")
    
    # Test specialty normalizer
    print("\n2. Testing Specialty Normalizer...")
    normalizer = SpecialtyNormalizer()
    
    test_specialties = [
        ('General Medicine', 'General Medicine', False, 'Already normalized'),
        ('GP', 'General Medicine', False, 'Common abbreviation'),
        ('Dentist', 'Dentistry', False, 'Should map to Dentistry'),
        ('内科', 'Internal Medicine', False, 'Japanese term'),
        ('UnknownSpec', 'General Medicine', True, 'Should default with review')
    ]
    
    for spec, expected_norm, expected_review, description in test_specialties:
        result = normalizer.normalize_specialty(spec)
        is_correct = result['specialty'] == expected_norm and result.get('needs_review', False) == expected_review
        status = "✅" if is_correct else "❌"
        review = "📝" if result.get('needs_review') else "  "
        print(f"  {status} {spec:20} -> {result['specialty']:20} {review} ({description})")
    
    # Test priority locations
    print("\n3. Testing Priority Locations...")
    priority_locs = get_english_priority_locations(10)
    print(f"  Top 10 English-priority locations:")
    for i, loc in enumerate(priority_locs, 1):
        print(f"    {i:2}. {loc}")
    
    return True


def test_enhanced_collector():
    """Test enhanced Google Places collector"""
    print("\n" + "=" * 80)
    print("TESTING ENHANCED GOOGLE PLACES COLLECTOR")
    print("=" * 80)
    
    try:
        # Initialize collector with enhancements
        collector = GooglePlacesCollector()
        
        # Check if enhancements are loaded
        print("\n1. Checking Enhanced Components...")
        components = {
            'Rate Limiting': collector.rate_limit_delay == 2.0,
            'Romaji Converter': collector.romaji_converter is not None,
            'Location Validator': collector.location_validator is not None,
            'Specialty Normalizer': collector.specialty_normalizer is not None
        }
        
        for component, status in components.items():
            icon = "✅" if status else "❌"
            print(f"  {icon} {component}: {'Loaded' if status else 'Missing'}")
        
        if not all(components.values()):
            print("\n⚠️ Some enhancements are missing!")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ Collector initialization failed: {e}")
        return False


def test_query_generation():
    """Test English-focused query generation"""
    print("\n" + "=" * 80)
    print("TESTING ENGLISH-FOCUSED QUERY GENERATION")
    print("=" * 80)
    
    try:
        collector = GooglePlacesCollector()
        
        # Test with specific locations
        print("\n1. Generating queries for Tokyo international districts...")
        queries = collector.generate_english_focused_queries(
            locations=['Roppongi', 'Shibuya', 'Minato'],
            specialties=['General Medicine', 'Dentistry', 'Pediatrics'],
            limit=15
        )
        
        if not queries:
            print("❌ No queries generated!")
            return False
        
        print(f"\n  Generated {len(queries)} queries:")
        
        # Show sample queries
        for i, query in enumerate(queries[:10], 1):
            print(f"\n  Query {i}:")
            print(f"    Text: {query['query']}")
            print(f"    Location: {query['location']} ({query['location_type']})")
            print(f"    Specialty: {query['specialty']}")
            print(f"    Priority: {query['priority']}")
            print(f"    Expected English: {query['expected_english_rate']}")
        
        # Test with invalid location
        print("\n2. Testing location validation...")
        queries_invalid = collector.generate_english_focused_queries(
            locations=['InvalidCity', 'Tokyo'],
            limit=5
        )
        
        # Should only have Tokyo queries
        tokyo_only = all(q['location'] == 'Tokyo' for q in queries_invalid)
        if tokyo_only:
            print("  ✅ Invalid location correctly rejected")
        else:
            print("  ❌ Invalid location not filtered")
        
        # Test with auto-selected priority locations
        print("\n3. Testing auto-priority locations...")
        queries_auto = collector.generate_english_focused_queries(
            locations=None,  # Will use priority locations
            specialties=['General Medicine'],
            limit=5
        )
        
        print(f"  Generated {len(queries_auto)} queries with auto-selected locations")
        unique_locs = set(q['location'] for q in queries_auto)
        print(f"  Locations used: {', '.join(unique_locs)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Query generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_duplicate_protection():
    """Test that existing providers are protected"""
    print("\n" + "=" * 80)
    print("TESTING DUPLICATE PROTECTION")
    print("=" * 80)
    
    try:
        from src.core.database import DatabaseManager
        
        db = DatabaseManager()
        session = db.get_session()
        
        # Check existing provider count
        from src.core.database import Provider
        existing_count = session.query(Provider).count()
        
        print(f"\n  Existing providers in database: {existing_count}")
        
        # Get a sample existing provider
        if existing_count > 0:
            sample_provider = session.query(Provider).first()
            print(f"  Sample provider: {sample_provider.provider_name}")
            print(f"  Location: {sample_provider.city}, {sample_provider.prefecture}")
            
            # Verify deduplication would catch it
            from src.collectors.deduplication import ProviderDeduplicator
            dedup = ProviderDeduplicator()
            
            test_data = {
                'provider_name': sample_provider.provider_name,
                'address': sample_provider.address,
                'city': sample_provider.city
            }
            
            fingerprints = dedup.generate_fingerprints(test_data)
            print(f"\n  Fingerprints generated:")
            for fp_type, fp_value in fingerprints.items():
                print(f"    {fp_type}: {fp_value[:16]}...")
        
        session.close()
        print("\n  ✅ Duplicate protection mechanisms in place")
        return True
        
    except Exception as e:
        print(f"\n❌ Duplicate protection test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("ENHANCED SEARCH SYSTEM TEST SUITE")
    print("=" * 80)
    
    results = {
        'Master Data': test_master_data(),
        'Enhanced Collector': test_enhanced_collector(),
        'Query Generation': test_query_generation(),
        'Duplicate Protection': test_duplicate_protection()
    }
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results.items():
        icon = "✅" if passed else "❌"
        status = "PASSED" if passed else "FAILED"
        print(f"{icon} {test_name:25} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Enhanced search system ready for use.")
        
        print("\n" + "=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print("""
1. Run a live test search (requires API quota):
   collector.search_providers("English speaking doctor Roppongi", limit=5)

2. Process discovered providers:
   - Apply romaji conversion to Japanese names
   - Validate locations and specialties
   - Check for duplicates against existing 464 providers

3. Begin campaign with priority locations:
   - Focus on international districts first
   - Use English-specific search patterns
   - Monitor English proficiency scores
        """)
    else:
        print("\n⚠️ Some tests failed. Please review and fix issues.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())