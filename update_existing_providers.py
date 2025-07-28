#!/usr/bin/env python3
"""
Update Existing Providers Script

This script provides multiple methods to update existing providers with new fixes:
1. Enhanced AI descriptions (2 paragraphs, 140-150 words)
2. AI excerpts (50-100 words) 
3. Location data (latitude/longitude for Google Maps)
4. ACF field synchronization

Usage Examples:
    python3 update_existing_providers.py --descriptions --city "Yokohama" --limit 10
    python3 update_existing_providers.py --locations --limit 20
    python3 update_existing_providers.py --all --city "Tokyo" --limit 5
"""

import argparse
import os
import sys
import time
import requests
from typing import List, Optional
from google_places_integration import GooglePlacesHealthcareCollector
from postgres_integration import Provider
from claude_description_generator import ClaudeDescriptionGenerator
from dotenv import load_dotenv

def load_google_api_key():
    """Load Google API key from environment"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    load_dotenv(config_path)
    return os.getenv("GOOGLE_PLACES_API_KEY")

def get_providers_for_update(session, city: Optional[str] = None, limit: int = 50, status_filter: Optional[str] = None):
    """Get providers that need updates"""
    query = session.query(Provider)
    
    # Apply city filter if specified
    if city:
        query = query.filter(Provider.city == city)
    
    # Apply status filter if specified  
    if status_filter:
        query = query.filter(Provider.status == status_filter)
    
    # Limit results
    providers = query.limit(limit).all()
    
    return providers

def update_descriptions_and_excerpts(providers: List[Provider], batch_size: int = 3, force: bool = False):
    """Update AI descriptions and excerpts for existing providers"""
    if not providers:
        print("No providers to update")
        return
    
    print(f"🤖 UPDATING DESCRIPTIONS & EXCERPTS FOR {len(providers)} PROVIDERS")
    print("=" * 60)
    
    generator = ClaudeDescriptionGenerator()
    collector = GooglePlacesHealthcareCollector()
    session = collector.Session()
    
    # Prepare provider data
    providers_to_update = []
    
    for provider in providers:
        # Skip if already has good description (unless forcing)
        if not force and provider.ai_description and len(provider.ai_description.split()) > 120:
            print(f"⏭️ Skipping {provider.provider_name}: Already has good description ({len(provider.ai_description.split())} words)")
            continue
            
        providers_to_update.append(provider)
    
    if not providers_to_update:
        print("✅ All providers already have enhanced descriptions")
        session.close()
        return
    
    print(f"🚀 Processing {len(providers_to_update)} providers...")
    
    # Process in batches
    updated_count = 0
    failed_count = 0
    
    for i in range(0, len(providers_to_update), batch_size):
        batch = providers_to_update[i:i + batch_size]
        
        # Prepare provider data for batch generation
        provider_data_list = []
        for provider in batch:
            provider_data = {
                'provider_name': provider.provider_name,
                'city': provider.city,
                'prefecture': provider.prefecture or '',
                'specialties': provider.specialties or ['General Medicine'],
                'english_proficiency': provider.english_proficiency or 'Unknown',
                'rating': provider.rating or 0,
                'total_reviews': provider.total_reviews or 0,
                'review_content': provider.review_content or '',
                'wheelchair_accessible': provider.wheelchair_accessible or False,
                'parking_available': provider.parking_available or False,
                'website': provider.website or '',
                'phone': provider.phone or ''
            }
            provider_data_list.append(provider_data)
        
        try:
            print(f"📝 Generating batch {i//batch_size + 1} ({len(batch)} providers)...")
            
            # Generate descriptions and excerpts
            descriptions = generator.generate_batch_descriptions(provider_data_list, batch_size)
            excerpts = generator.generate_batch_excerpts(provider_data_list, batch_size)
            
            # Update database
            for provider, description, excerpt in zip(batch, descriptions, excerpts):
                try:
                    # Re-query the provider to attach to current session
                    db_provider = session.query(Provider).filter_by(
                        provider_name=provider.provider_name,
                        city=provider.city
                    ).first()
                    
                    if db_provider:
                        db_provider.ai_description = description
                        db_provider.ai_excerpt = excerpt
                        db_provider.status = 'description_generated'
                        session.commit()
                        
                        word_count = len(description.split())
                        paragraph_count = description.count('\n\n') + 1
                        print(f"   ✅ {provider.provider_name}: {word_count} words, {paragraph_count} paragraphs")
                        updated_count += 1
                    else:
                        print(f"   ❌ Provider not found in database: {provider.provider_name}")
                        failed_count += 1
                    
                except Exception as e:
                    print(f"   ❌ Failed to update {provider.provider_name}: {str(e)}")
                    session.rollback()
                    failed_count += 1
            
            # Rate limiting between batches
            if i + batch_size < len(providers_to_update):
                time.sleep(1)
                
        except Exception as e:
            print(f"❌ Batch generation failed: {str(e)}")
            failed_count += len(batch)
    
    session.close()
    
    print(f"\n📊 DESCRIPTION UPDATE SUMMARY:")
    print(f"   ✅ Updated: {updated_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📈 Success rate: {(updated_count/(updated_count+failed_count)*100):.1f}%")

def update_locations(providers: List[Provider], api_key: str):
    """Update latitude/longitude for providers"""
    if not providers:
        print("No providers to update")
        return
    
    print(f"🗺️ UPDATING LOCATIONS FOR {len(providers)} PROVIDERS")
    print("=" * 60)
    
    collector = GooglePlacesHealthcareCollector()
    session = collector.Session()
    
    updated_count = 0
    skipped_count = 0
    failed_count = 0
    
    for i, provider in enumerate(providers, 1):
        # Skip if already has location data
        if provider.latitude and provider.longitude:
            print(f"⏭️ {i}/{len(providers)}: {provider.provider_name} - Already has location")
            skipped_count += 1
            continue
        
        print(f"📍 {i}/{len(providers)}: Processing {provider.provider_name}")
        
        try:
            # Create search query
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
            params = {"address": query, "key": api_key}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "OK" and data["results"]:
                    location = data["results"][0]["geometry"]["location"]
                    lat, lng = location["lat"], location["lng"]
                    
                    # Update provider
                    provider.latitude = lat
                    provider.longitude = lng
                    session.commit()
                    
                    print(f"   ✅ Updated: {lat:.6f}, {lng:.6f}")
                    updated_count += 1
                else:
                    print(f"   ⚠️ Geocoding failed: {data.get('status', 'Unknown error')}")
                    failed_count += 1
            else:
                print(f"   ❌ API request failed: {response.status_code}")
                failed_count += 1
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            failed_count += 1
        
        # Rate limiting
        if i < len(providers):
            time.sleep(0.2)
    
    session.close()
    
    print(f"\n📊 LOCATION UPDATE SUMMARY:")
    print(f"   ✅ Updated: {updated_count}")
    print(f"   ⏭️ Skipped: {skipped_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📈 Success rate: {(updated_count/(len(providers)-skipped_count)*100):.1f}%")

def clear_descriptions(providers: List[Provider]):
    """Clear existing descriptions to force regeneration"""
    print(f"🧹 CLEARING DESCRIPTIONS FOR {len(providers)} PROVIDERS")
    print("=" * 60)
    
    collector = GooglePlacesHealthcareCollector()
    session = collector.Session()
    
    cleared_count = 0
    
    for provider in providers:
        try:
            provider.ai_description = None
            provider.ai_excerpt = None
            provider.status = 'pending'
            session.commit()
            
            print(f"✅ Cleared: {provider.provider_name}")
            cleared_count += 1
            
        except Exception as e:
            print(f"❌ Failed to clear {provider.provider_name}: {str(e)}")
            session.rollback()
    
    session.close()
    print(f"\n📊 Cleared descriptions for {cleared_count} providers")
    print("💡 Run --descriptions next to regenerate with enhanced format")

def update_google_places_data(providers: List[Provider], api_key: str):
    """Update Google Places data (hours, ratings, accessibility) for providers"""
    if not providers:
        print("No providers to update")
        return
    
    print(f"🏪 UPDATING GOOGLE PLACES DATA FOR {len(providers)} PROVIDERS")
    print("=" * 60)
    
    collector = GooglePlacesHealthcareCollector()
    session = collector.Session()
    
    updated_count = 0
    skipped_count = 0
    failed_count = 0
    
    for i, provider in enumerate(providers, 1):
        print(f"🏪 {i}/{len(providers)}: Processing {provider.provider_name}")
        
        # Skip if no Google Place ID
        if not provider.google_place_id:
            print(f"   ⏭️ No Google Place ID found")
            skipped_count += 1
            continue
        
        try:
            # Get place details from Google Places API
            details = collector.get_place_details(provider.google_place_id)
            
            if not details:
                print(f"   ❌ No details found for Place ID: {provider.google_place_id}")
                failed_count += 1
                continue
            
            # Re-query the provider to attach to current session
            db_provider = session.query(Provider).filter_by(id=provider.id).first()
            
            if not db_provider:
                print(f"   ❌ Provider not found in database")
                failed_count += 1
                continue
            
            updates_made = []
            
            # Update business hours
            if 'opening_hours' in details and details['opening_hours']:
                db_provider.business_hours = details['opening_hours']
                updates_made.append('hours')
            
            # Update rating and review count
            if 'rating' in details:
                db_provider.rating = details['rating']
                updates_made.append('rating')
            
            if 'user_ratings_total' in details:
                db_provider.total_reviews = details['user_ratings_total']
                updates_made.append('reviews')
            
            # Update accessibility info
            if 'wheelchair_accessible_entrance' in details:
                db_provider.wheelchair_accessible = str(details['wheelchair_accessible_entrance']).lower()
                updates_made.append('wheelchair')
            
            # Update phone and website if missing
            if not db_provider.phone and 'formatted_phone_number' in details:
                db_provider.phone = details['formatted_phone_number']
                updates_made.append('phone')
            
            if not db_provider.website and 'website' in details:
                db_provider.website = details['website']
                updates_made.append('website')
            
            # Update photo URLs
            if 'photos' in details and details['photos']:
                photo_urls = []
                for photo in details['photos'][:5]:  # Limit to 5 photos
                    if 'photo_reference' in photo:
                        photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo['photo_reference']}&key={api_key}"
                        photo_urls.append(photo_url)
                
                if photo_urls:
                    db_provider.photo_urls = photo_urls
                    updates_made.append('photos')
            
            if updates_made:
                session.commit()
                print(f"   ✅ Updated: {', '.join(updates_made)}")
                updated_count += 1
            else:
                print(f"   ℹ️ No new data available")
                skipped_count += 1
            
            # Rate limiting
            time.sleep(0.1)  # Small delay to avoid rate limits
            
        except Exception as e:
            print(f"   ❌ Failed to update: {str(e)}")
            session.rollback()
            failed_count += 1
    
    session.close()
    
    print(f"\n📊 GOOGLE PLACES DATA UPDATE SUMMARY:")
    print(f"   ✅ Updated: {updated_count}")
    print(f"   ⏭️ Skipped: {skipped_count}")
    print(f"   ❌ Failed: {failed_count}")
    if updated_count + failed_count > 0:
        print(f"   📈 Success rate: {(updated_count/(updated_count+failed_count)*100):.1f}%")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Update existing providers with fixes")
    
    # Update options
    parser.add_argument("--descriptions", action='store_true', help="Update AI descriptions and excerpts")
    parser.add_argument("--locations", action='store_true', help="Update latitude/longitude for Google Maps")
    parser.add_argument("--google-data", action='store_true', help="Update Google Places data (hours, ratings, accessibility)")
    parser.add_argument("--clear", action='store_true', help="Clear existing descriptions to force regeneration")
    parser.add_argument("--all", action='store_true', help="Update everything (descriptions + locations + google data)")
    
    # Filters
    parser.add_argument("--city", type=str, help="Filter by specific city")
    parser.add_argument("--limit", type=int, default=50, help="Limit number of providers to process")
    parser.add_argument("--status", type=str, help="Filter by status (pending, description_generated, published)")
    parser.add_argument("--force", action='store_true', help="Force update even if content already exists")
    
    # Processing options
    parser.add_argument("--batch-size", type=int, default=3, help="Batch size for AI generation")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not any([args.descriptions, args.locations, getattr(args, 'google_data', False), args.clear, args.all]):
        print("❌ Please specify what to update: --descriptions, --locations, --google-data, --clear, or --all")
        sys.exit(1)
    
    try:
        # Initialize database connection
        collector = GooglePlacesHealthcareCollector()
        session = collector.Session()
        
        # Get providers for update
        providers = get_providers_for_update(session, args.city, args.limit, args.status)
        
        if not providers:
            print("❌ No providers found matching criteria")
            session.close()
            sys.exit(1)
        
        print(f"🔍 Found {len(providers)} providers to process")
        if args.city:
            print(f"📍 City filter: {args.city}")
        if args.status:
            print(f"📊 Status filter: {args.status}")
        print()
        
        # Execute updates based on arguments
        if args.clear:
            clear_descriptions(providers)
        
        if args.descriptions or args.all:
            update_descriptions_and_excerpts(providers, args.batch_size, args.force)
        
        if args.locations or args.all:
            api_key = load_google_api_key()
            if not api_key:
                print("❌ Google API key required for location updates")
                sys.exit(1)
            update_locations(providers, api_key)
        
        if getattr(args, 'google_data', False) or args.all:
            api_key = load_google_api_key()
            if not api_key:
                print("❌ Google API key required for Google Places data updates")
                sys.exit(1)
            update_google_places_data(providers, api_key)
        
        session.close()
        
        print("\n🎉 Update process completed!")
        print("💡 Next steps:")
        print("   - Run WordPress sync to update published posts")
        print("   - Check ACF fields in WordPress admin")
        print("   - Verify Google Maps are now showing")
        
    except Exception as e:
        print(f"❌ Update failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 