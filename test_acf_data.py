#!/usr/bin/env python3
"""
Test script to show exact ACF data that would be sent to WordPress
"""

import json
from wordpress_integration import WordPressIntegration
from postgres_integration import PostgresIntegration, Provider

def test_acf_data_format():
    """Test and display the exact ACF data format"""
    print("🔍 Testing ACF Data Format for WordPress")
    print("=" * 60)
    
    # Get a provider from the database
    db = PostgresIntegration()
    session = db.Session()
    
    # Get the first provider with description_generated status
    provider = session.query(Provider).filter(
        Provider.status == 'description_generated'
    ).first()
    
    if not provider:
        print("❌ No providers found with description_generated status")
        session.close()
        return
    
    print(f"📋 Testing with provider: {provider.provider_name}")
    
    # Create WordPress integration instance
    wp = WordPressIntegration()
    
    # Get the ACF data that would be sent
    acf_data = {
        # Provider Details Field Group
        "provider_phone": getattr(provider, 'phone', ''),
        "wheelchair_accessible": wp.format_wheelchair_accessibility(getattr(provider, 'wheelchair_accessible', False)),
        "parking_available": wp.format_parking_availability(getattr(provider, 'parking_available', False)),
        "business_status": wp.normalize_business_status(getattr(provider, 'business_status', 'Unknown')),
        "prefecture": getattr(provider, 'prefecture', ''),
        
        # Business Hours Field Group
        "business_hours": wp.format_business_hours(getattr(provider, 'business_hours', {})),
        "hours_monday": wp.get_day_hours(getattr(provider, 'business_hours', {}), 'Monday'),
        "hours_tuesday": wp.get_day_hours(getattr(provider, 'business_hours', {}), 'Tuesday'),
        "hours_wednesday": wp.get_day_hours(getattr(provider, 'business_hours', {}), 'Wednesday'),
        "hours_thursday": wp.get_day_hours(getattr(provider, 'business_hours', {}), 'Thursday'),
        "hours_friday": wp.get_day_hours(getattr(provider, 'business_hours', {}), 'Friday'),
        "hours_saturday": wp.get_day_hours(getattr(provider, 'business_hours', {}), 'Saturday'),
        "hours_sunday": wp.get_day_hours(getattr(provider, 'business_hours', {}), 'Sunday'),
        "open_now": wp.get_open_now_status(getattr(provider, 'business_hours', {})),
        
        # Location & Navigation Field Group
        "latitude": float(getattr(provider, 'latitude', 0)) if getattr(provider, 'latitude', None) else None,
        "longitude": float(getattr(provider, 'longitude', 0)) if getattr(provider, 'longitude', None) else None,
        "nearest_station": getattr(provider, 'nearest_station', ''),
        "google_maps_embed": wp.generate_google_maps_embed(getattr(provider, 'latitude', 0), getattr(provider, 'longitude', 0), provider.provider_name),
        
        # Language Support Field Group
        "english_proficiency": wp.determine_english_proficiency(provider),
        "proficiency_score": wp.calculate_proficiency_score(provider),
        "english_indicators": wp.extract_english_indicators(provider),
        
        # Photo Gallery Field Group
        "photo_urls": wp.convert_photo_urls_for_greenshift(getattr(provider, 'photo_urls', '')),
        
        # Accessibility & Services Field Group
        "accessibility_status": wp.format_accessibility_status(getattr(provider, 'wheelchair_accessible', False)),
        "parking_status": wp.format_parking_status(getattr(provider, 'parking_available', False)),
        
        # Patient Insights Field Group
        "review_keywords": wp.extract_patient_feedback_themes(getattr(provider, 'review_content', '')),
        "patient_highlights": wp.generate_patient_highlights(getattr(provider, 'review_content', '')),
        
        # Additional essential fields
        "provider_website": wp.clean_website_url(getattr(provider, 'website', '')),
        "provider_address": wp.clean_address(getattr(provider, 'address', '')),
        "provider_rating": str(getattr(provider, 'rating', 0)),
        "provider_reviews": str(getattr(provider, 'total_reviews', 0)),
        "postal_code": getattr(provider, 'postal_code', ''),
        "ai_description": getattr(provider, 'ai_description', ''),
        "provider_city": provider.city,
    }
    
    print("\n🔧 ACF Field Data Types and Values:")
    print("=" * 60)
    
    for field_name, value in acf_data.items():
        value_type = type(value).__name__
        value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
        print(f"  {field_name:25} | {value_type:10} | {value_preview}")
    
    print("\n📊 Critical Fields for WordPress Configuration:")
    print("=" * 60)
    
    critical_fields = {
        "wheelchair_accessible": acf_data["wheelchair_accessible"],
        "parking_available": acf_data["parking_available"],
        "business_hours": acf_data["business_hours"][:100] + "..." if len(acf_data["business_hours"]) > 100 else acf_data["business_hours"],
        "hours_monday": acf_data["hours_monday"],
        "open_now": acf_data["open_now"],
        "english_proficiency": acf_data["english_proficiency"]
    }
    
    for field, value in critical_fields.items():
        print(f"  {field}: '{value}' (type: {type(value).__name__})")
    
    print(f"\n📋 Complete ACF JSON Structure:")
    print("=" * 60)
    print(json.dumps(acf_data, indent=2, ensure_ascii=False))
    
    session.close()

if __name__ == "__main__":
    test_acf_data_format() 