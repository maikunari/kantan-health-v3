#!/usr/bin/env python3
"""
Test script for real Google Places API integration with business hours
"""

import json
from google_places_integration import GooglePlacesHealthcareCollector

def test_real_google_places():
    """Test with a real Google Places API query"""
    print("🧪 Testing Real Google Places API Integration")
    print("=" * 50)
    
    try:
        collector = GooglePlacesHealthcareCollector()
        
        # Test with a simple query for medical clinics in Tokyo
        search_query = "medical clinic Tokyo"
        print(f"🔍 Searching for: {search_query}")
        
        # Search for providers
        results = collector.search_healthcare_providers(search_query)
        
        if not results:
            print("❌ No results found")
            return False
        
        print(f"✅ Found {len(results)} results")
        
        # Take the first result and get detailed information
        first_result = results[0]
        place_id = first_result.get('place_id')
        provider_name = first_result.get('name', 'Unknown')
        
        print(f"📍 Testing with: {provider_name}")
        print(f"   Place ID: {place_id}")
        
        # Get detailed place information
        detailed_data = collector.get_place_details(place_id)
        
        if not detailed_data:
            print("❌ Could not get detailed data")
            return False
        
        print("✅ Got detailed data")
        
        # Check if opening hours are present
        opening_hours = detailed_data.get('opening_hours', {})
        print(f"   Opening hours present: {bool(opening_hours)}")
        
        if opening_hours:
            print(f"   Open now: {opening_hours.get('open_now', 'Unknown')}")
            print(f"   Weekday text: {len(opening_hours.get('weekday_text', []))} entries")
            print(f"   Periods: {len(opening_hours.get('periods', []))} entries")
            
            if opening_hours.get('weekday_text'):
                print("   Sample weekday text:")
                for day in opening_hours['weekday_text'][:3]:  # Show first 3
                    print(f"     {day}")
        
        # Test our processing function
        processed_hours = collector.process_opening_hours(detailed_data)
        print(f"\n✅ Processed hours keys: {list(processed_hours.keys())}")
        
        if processed_hours.get('formatted_hours'):
            print("   Sample formatted hours:")
            for day, hours in list(processed_hours['formatted_hours'].items())[:3]:
                print(f"     {day}: {hours.get('open', 'N/A')} - {hours.get('close', 'N/A')}")
        
        # Test creating comprehensive record
        record = collector.create_comprehensive_provider_record(detailed_data)
        
        if record is None:
            print(f"\n⚠️ Provider filtered out due to English proficiency requirements")
            print("   (Score below 3 - Basic level required)")
            return True  # This is expected behavior, not a failure
        
        print(f"\n✅ Created comprehensive record")
        print(f"   Provider: {record.get('provider_name', 'Unknown')}")
        print(f"   English Proficiency: {record.get('english_proficiency', 'Unknown')} (Score: {record.get('proficiency_score', 0)})")
        print(f"   Business hours present: {bool(record.get('business_hours'))}")
        
        if record.get('business_hours'):
            business_hours = record['business_hours']
            print(f"   Business hours keys: {list(business_hours.keys())}")
            
            # Show the JSON structure
            print("\n📋 Business Hours JSON Structure:")
            print(json.dumps(business_hours, indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Real Google Places API Test")
    print("=" * 50)
    
    success = test_real_google_places()
    
    if success:
        print("\n🎉 Real API test completed successfully!")
    else:
        print("\n❌ Real API test failed!") 