#!/usr/bin/env python3
"""
Test script for business hours functionality
"""

import json
from google_places_integration import GooglePlacesHealthcareCollector
from wordpress_integration import WordPressIntegration

def test_business_hours_processing():
    """Test the business hours processing with sample data"""
    print("🧪 Testing Business Hours Processing")
    print("=" * 50)
    
    # Sample Google Places API response data
    sample_place_data = {
        "name": "Test Medical Clinic",
        "opening_hours": {
            "open_now": True,
            "weekday_text": [
                "Monday: 9:00 AM – 5:00 PM",
                "Tuesday: 9:00 AM – 5:00 PM", 
                "Wednesday: 9:00 AM – 5:00 PM",
                "Thursday: 9:00 AM – 5:00 PM",
                "Friday: 9:00 AM – 5:00 PM",
                "Saturday: 9:00 AM – 1:00 PM",
                "Sunday: Closed"
            ],
            "periods": [
                {
                    "open": {"day": 1, "time": "0900"},
                    "close": {"day": 1, "time": "1700"}
                },
                {
                    "open": {"day": 2, "time": "0900"},
                    "close": {"day": 2, "time": "1700"}
                },
                {
                    "open": {"day": 3, "time": "0900"},
                    "close": {"day": 3, "time": "1700"}
                },
                {
                    "open": {"day": 4, "time": "0900"},
                    "close": {"day": 4, "time": "1700"}
                },
                {
                    "open": {"day": 5, "time": "0900"},
                    "close": {"day": 5, "time": "1700"}
                },
                {
                    "open": {"day": 6, "time": "0900"},
                    "close": {"day": 6, "time": "1300"}
                }
            ]
        }
    }
    
    try:
        # Test Google Places integration
        collector = GooglePlacesHealthcareCollector()
        processed_hours = collector.process_opening_hours(sample_place_data)
        
        print("✅ Google Places Hours Processing:")
        print(f"   Open now: {processed_hours.get('open_now', 'Unknown')}")
        print(f"   Weekday text: {len(processed_hours.get('weekday_text', []))} days")
        print(f"   Formatted hours: {len(processed_hours.get('formatted_hours', {}))} days")
        
        # Print formatted hours
        for day, hours in processed_hours.get('formatted_hours', {}).items():
            print(f"   {day}: {hours.get('open', 'N/A')} - {hours.get('close', 'N/A')}")
        
        print("\n✅ JSON Output:")
        print(json.dumps(processed_hours, indent=2))
        
        # Test WordPress integration formatting
        wp_integration = WordPressIntegration()
        
        # Create a mock provider object
        class MockProvider:
            def __init__(self, business_hours):
                self.business_hours = business_hours
                
        mock_provider = MockProvider(processed_hours)
        
        print("\n✅ WordPress ACF Field Formatting:")
        print("   Complete hours:", wp_integration.format_business_hours(processed_hours))
        print("   Monday hours:", wp_integration.get_day_hours(processed_hours, 'Monday'))
        print("   Wednesday hours:", wp_integration.get_day_hours(processed_hours, 'Wednesday'))
        print("   Saturday hours:", wp_integration.get_day_hours(processed_hours, 'Saturday'))
        print("   Sunday hours:", wp_integration.get_day_hours(processed_hours, 'Sunday'))
        print("   Open now status:", wp_integration.get_open_now_status(processed_hours))
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        return False

def test_edge_cases():
    """Test edge cases for business hours"""
    print("\n🧪 Testing Edge Cases")
    print("=" * 50)
    
    # Test empty data
    collector = GooglePlacesHealthcareCollector()
    wp_integration = WordPressIntegration()
    
    # Test with no opening hours
    empty_data = {"name": "Test Clinic"}
    result = collector.process_opening_hours(empty_data)
    print(f"✅ Empty data test: {result}")
    
    # Test WordPress formatting with empty data
    formatted = wp_integration.format_business_hours({})
    print(f"✅ Empty hours formatting: '{formatted}'")
    
    # Test with malformed data
    malformed_data = {"opening_hours": {"malformed": True}}
    result = collector.process_opening_hours(malformed_data)
    print(f"✅ Malformed data test: {result}")

if __name__ == "__main__":
    print("🚀 Starting Business Hours Tests")
    print("=" * 50)
    
    success = test_business_hours_processing()
    test_edge_cases()
    
    if success:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Some tests failed!") 