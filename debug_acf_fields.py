#!/usr/bin/env python3
"""
Debug script to test ACF field formatting
"""

from wordpress_integration import WordPressIntegration
from postgres_integration import PostgresIntegration, Provider

def debug_acf_fields():
    """Debug ACF field formatting"""
    print("🔍 Debugging ACF Field Formatting")
    print("=" * 50)
    
    # Get a provider from the database
    db = PostgresIntegration()
    session = db.Session()
    
    # Get the first provider with description_generated status
    provider = session.query(Provider).filter(
        Provider.status == 'description_generated'
    ).first()
    
    if not provider:
        print("❌ No providers found with description_generated status")
        return
    
    print(f"📋 Testing with provider: {provider.provider_name}")
    print(f"   Wheelchair accessible: {provider.wheelchair_accessible} (type: {type(provider.wheelchair_accessible)})")
    print(f"   Parking available: {provider.parking_available} (type: {type(provider.parking_available)})")
    print(f"   Business hours: {provider.business_hours} (type: {type(provider.business_hours)})")
    
    # Test WordPress formatting
    wp = WordPressIntegration()
    
    wheelchair_formatted = wp.format_wheelchair_accessibility(provider.wheelchair_accessible)
    parking_formatted = wp.format_parking_availability(provider.parking_available)
    business_hours_formatted = wp.format_business_hours(provider.business_hours)
    
    print(f"\n🔄 Formatted values:")
    print(f"   Wheelchair: {wheelchair_formatted} (type: {type(wheelchair_formatted)})")
    print(f"   Parking: {parking_formatted} (type: {type(parking_formatted)})")
    print(f"   Business hours: {business_hours_formatted[:100]}...")
    
    # Test individual day hours
    print(f"\n📅 Individual day hours:")
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for day in days:
        day_hours = wp.get_day_hours(provider.business_hours, day)
        print(f"   {day}: {day_hours}")
    
    # Test open now status
    open_now = wp.get_open_now_status(provider.business_hours)
    print(f"\n🕒 Open now status: {open_now}")
    
    session.close()

if __name__ == "__main__":
    debug_acf_fields() 