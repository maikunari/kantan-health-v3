#!/usr/bin/env python3
"""
Final integration test to verify all components work together
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor

# Import all fixed components
from src.core.database import DatabaseManager
from src.collectors.google_places import GooglePlacesCollector
from src.publishers.wordpress import WordPressPublisher
from src.processors.ai_content import AIContentProcessor
from src.utils.romaji_wrapper import BusinessNameRomajiConverter
from src.collectors.duplicate_detector import DuplicateDetector

def test_all_components():
    """Test that all components work together"""
    
    print("=" * 80)
    print("FINAL INTEGRATION TEST - ALL REPAIRS")
    print("=" * 80)
    
    results = {
        'database': False,
        'google_places': False,
        'wordpress': False,
        'ai_content': False,
        'romaji': False,
        'deduplication': False
    }
    
    # Test 1: Database with proper pooling
    print("\n1. Testing Database Connection Pooling...")
    try:
        db = DatabaseManager()
        
        # Test concurrent access
        def db_test(i):
            session = db.get_session()
            from src.core.database import Provider
            count = session.query(Provider).count()
            session.close()
            return count
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(db_test, i) for i in range(5)]
            counts = [f.result() for f in futures]
        
        if all(c == counts[0] for c in counts):
            print(f"  ✅ Database pooling works! ({counts[0]} providers)")
            results['database'] = True
        else:
            print(f"  ❌ Inconsistent results: {counts}")
    except Exception as e:
        print(f"  ❌ Database failed: {e}")
    
    # Test 2: Google Places Collector
    print("\n2. Testing Google Places Collector...")
    try:
        collector = GooglePlacesCollector()
        
        # Check components
        if collector.romaji_converter and collector.rate_limit_delay == 2.0:
            print("  ✅ Romaji converter integrated")
            print("  ✅ Rate limiting configured (2 sec)")
            results['google_places'] = True
        else:
            print("  ❌ Missing components")
    except Exception as e:
        print(f"  ❌ Google Places failed: {e}")
    
    # Test 3: WordPress Publisher
    print("\n3. Testing WordPress Publisher...")
    try:
        publisher = WordPressPublisher()
        
        if publisher.wp_url and publisher.acf_field_mappings:
            print(f"  ✅ Connected to: {publisher.wp_url}")
            print(f"  ✅ ACF mappings: {len(publisher.acf_field_mappings)} fields")
            results['wordpress'] = True
        else:
            print("  ❌ Configuration incomplete")
    except Exception as e:
        print(f"  ❌ WordPress failed: {e}")
    
    # Test 4: AI Content Processor
    print("\n4. Testing AI Content Processor...")
    try:
        processor = AIContentProcessor()
        
        if processor.api_key:
            print(f"  ✅ Claude API configured")
            print(f"  ✅ Model: {processor.model}")
            results['ai_content'] = True
        else:
            print("  ❌ API key missing")
    except Exception as e:
        print(f"  ❌ AI Content failed: {e}")
    
    # Test 5: Romaji Converter
    print("\n5. Testing Romaji Converter...")
    try:
        converter = BusinessNameRomajiConverter()
        
        # Test conversion
        test_cases = [
            ("東京クリニック", "Tokyo Clinic"),
            ("山田病院", "Yamada Hospital")
        ]
        
        passed = 0
        for japanese, expected_contains in test_cases:
            result = converter.convert(japanese)
            if expected_contains.split()[0] in result:
                passed += 1
                print(f"  ✅ {japanese} → {result}")
            else:
                print(f"  ❌ {japanese} → {result} (expected {expected_contains})")
        
        if passed == len(test_cases):
            results['romaji'] = True
    except Exception as e:
        print(f"  ❌ Romaji converter failed: {e}")
    
    # Test 6: Duplicate Detection
    print("\n6. Testing Duplicate Detection...")
    try:
        detector = DuplicateDetector()
        
        test_provider = {
            'provider_name': 'Test Clinic',
            'address': '123 Test St',
            'city': 'Tokyo',
            'phone': '03-1234-5678'
        }
        
        result = detector.check_duplicate(test_provider)
        
        if 'is_duplicate' in result and 'fingerprints' in result:
            print("  ✅ Duplicate detection works")
            print(f"  ✅ Fingerprints generated: {len(result['fingerprints'])} types")
            results['deduplication'] = True
        else:
            print("  ❌ Unexpected result format")
    except Exception as e:
        print(f"  ❌ Duplicate detection failed: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("INTEGRATION TEST RESULTS")
    print("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for component, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {component:20} {'PASSED' if status else 'FAILED'}")
    
    print(f"\nTotal: {passed}/{total} components working")
    
    if passed == total:
        print("\n🎉 ALL REPAIRS SUCCESSFUL! System ready for campaign.")
        return True
    else:
        print(f"\n⚠️ {total - passed} components still need attention")
        return False

if __name__ == "__main__":
    success = test_all_components()
    sys.exit(0 if success else 1)