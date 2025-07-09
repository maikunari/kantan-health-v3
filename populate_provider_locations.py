#!/usr/bin/env python3
"""
Populate latitude/longitude for existing providers using Google Places API
"""

import os
import sys
import time
import requests
from google_places_integration import GooglePlacesHealthcareCollector
from postgres_integration import Provider
from dotenv import load_dotenv

def load_google_api_key():
    """Load Google API key from environment"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    load_dotenv(config_path)
    return os.getenv("GOOGLE_PLACES_API_KEY")

def geocode_provider(provider, api_key):
    """Get latitude/longitude for a provider using Google Geocoding API"""
    try:
        # Create search query from provider address and name
        query_parts = []
        if provider.provider_name:
            query_parts.append(provider.provider_name)
        if provider.address:
            query_parts.append(provider.address)
        if provider.city:
            query_parts.append(provider.city)
        if provider.prefecture:
            query_parts.append(provider.prefecture)
            
        query = ", ".join(query_parts)
        
        # Use Google Geocoding API
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": query,
            "key": api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "OK" and data["results"]:
                location = data["results"][0]["geometry"]["location"]
                return location["lat"], location["lng"]
        
        return None, None
        
    except Exception as e:
        print(f"⚠️ Error geocoding {provider.provider_name}: {str(e)}")
        return None, None

def main():
    """Main function to populate provider locations"""
    try:
        # Load API key
        api_key = load_google_api_key()
        if not api_key:
            print("❌ Google API key not found in config/.env")
            sys.exit(1)
        
        # Initialize database connection
        collector = GooglePlacesHealthcareCollector()
        session = collector.Session()
        
        # Get providers without location data
        providers_without_location = session.query(Provider).filter(
            Provider.latitude.is_(None)
        ).limit(50).all()  # Limit to 50 to avoid API costs
        
        print(f"🗺️ POPULATING LOCATIONS FOR {len(providers_without_location)} PROVIDERS")
        print("=" * 60)
        
        if not providers_without_location:
            print("✅ All providers already have location data!")
            session.close()
            return
        
        updated_count = 0
        skipped_count = 0
        
        for i, provider in enumerate(providers_without_location, 1):
            print(f"📍 Processing {i}/{len(providers_without_location)}: {provider.provider_name}")
            
            # Get coordinates
            lat, lng = geocode_provider(provider, api_key)
            
            if lat and lng:
                # Update provider with coordinates
                provider.latitude = lat
                provider.longitude = lng
                session.commit()
                
                print(f"   ✅ Updated: {lat:.6f}, {lng:.6f}")
                updated_count += 1
            else:
                print(f"   ⚠️ Could not geocode address")
                skipped_count += 1
            
            # Rate limiting - pause between requests
            if i < len(providers_without_location):
                time.sleep(0.2)  # 200ms delay between requests
        
        session.close()
        
        print()
        print(f"📊 SUMMARY:")
        print(f"   ✅ Updated: {updated_count}")
        print(f"   ⚠️ Skipped: {skipped_count}")
        print(f"   📈 Success rate: {(updated_count/len(providers_without_location)*100):.1f}%")
        
        if updated_count > 0:
            print()
            print("🎉 Location data populated! Google Maps will now work for these providers.")
            print("💡 Re-run WordPress sync to update maps in published posts.")
        
    except Exception as e:
        print(f"❌ Error populating locations: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 