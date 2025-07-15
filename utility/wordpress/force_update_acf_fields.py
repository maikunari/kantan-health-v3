#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from wordpress_integration import WordPressIntegration
from postgres_integration import PostgresIntegration, Provider
import json

def force_update_acf_fields():
    """Force update all provider posts to populate new ACF fields"""
    
    print("🔄 Starting ACF field population for all providers...")
    
    # Initialize services
    db = PostgresIntegration()
    wp = WordPressIntegration()
    
    try:
        # Get all providers from database
        session = db.Session()
        providers = session.query(Provider).all()
        print(f"Found {len(providers)} providers in database")
        
        # Convert providers to dict format for easier processing
        provider_dicts = []
        for provider in providers:
            provider_dict = {
                'id': provider.id,
                'name': provider.provider_name,
                'wordpress_post_id': provider.wordpress_post_id,
                'photo_urls': provider.photo_urls,
                'selected_featured_image': provider.selected_featured_image,
                'latitude': provider.latitude,
                'longitude': provider.longitude,
                'address': provider.address,
                'seo_title': provider.seo_title,
                'seo_meta_description': provider.seo_meta_description,
                'wheelchair_accessible': provider.wheelchair_accessible,
                'parking_available': provider.parking_available,
            }
            provider_dicts.append(provider_dict)
        
        providers = provider_dicts
        
        updated_count = 0
        error_count = 0
        
        for provider in providers:
            try:
                provider_id = provider.get('id')
                name = provider.get('name', 'Unknown')
                wordpress_post_id = provider.get('wordpress_post_id')
                
                if not wordpress_post_id:
                    print(f"⚠️  {name}: No WordPress post ID, skipping")
                    continue
                
                print(f"🔄 Updating {name} (Post ID: {wordpress_post_id})...")
                
                # Get photo URLs and counts - properly parse JSON format
                photo_urls_str = provider.get('photo_urls', '')
                photo_urls = []
                
                if photo_urls_str:
                    try:
                        # Parse JSON string to get list of URLs
                        if isinstance(photo_urls_str, str):
                            photo_urls = json.loads(photo_urls_str)
                        else:
                            photo_urls = photo_urls_str
                        
                        # Ensure it's a list
                        if not isinstance(photo_urls, list):
                            photo_urls = []
                            
                    except json.JSONDecodeError:
                        # If it's not JSON, try treating as newline-separated (fallback)
                        photo_urls = [url.strip() for url in photo_urls_str.split('\n') if url.strip()]
                    except Exception as e:
                        print(f"   ⚠️ Error parsing photo URLs: {str(e)}")
                        photo_urls = []
                
                photo_count = len(photo_urls)
                
                # Get Claude-selected featured image
                selected_featured_image = provider.get('selected_featured_image', '')
                
                # Determine featured image source and status
                if selected_featured_image:
                    featured_image_source = "Claude AI Selected"
                    image_selection_status = "selected"
                    external_featured_image = selected_featured_image
                elif photo_urls:
                    featured_image_source = "First Available Photo"
                    image_selection_status = "fallback"
                    external_featured_image = photo_urls[0]
                else:
                    featured_image_source = "No Image Available"
                    image_selection_status = "none"
                    external_featured_image = ""
                
                # Generate Google Map array
                google_map_data = ""
                latitude = provider.get('latitude', 0)
                longitude = provider.get('longitude', 0)
                name = provider.get('name', '')
                address = provider.get('address', '')
                
                if latitude and longitude:
                    google_map_data = {
                        'location': {
                            'lat': float(latitude),
                            'lng': float(longitude)
                        },
                        'title': name,
                        'description': address.replace(', Japan', '').strip() if address else ''
                    }
                
                # Get SEO data
                seo_title = provider.get('seo_title', '')
                seo_meta_description = provider.get('seo_meta_description', '')
                
                # Get and format accessibility data
                wheelchair_raw = provider.get('wheelchair_accessible', '')
                parking_raw = provider.get('parking_available', '')
                
                # Format wheelchair accessibility for ACF dropdown
                if wheelchair_raw == 'true':
                    wheelchair_formatted = "Wheelchair accessible"
                elif wheelchair_raw == 'false':
                    wheelchair_formatted = "Not wheelchair accessible"
                else:
                    wheelchair_formatted = "Wheelchair accessibility unknown"
                
                # Format parking availability for ACF dropdown  
                if parking_raw == 'true':
                    parking_formatted = "Parking is available"
                elif parking_raw == 'false':
                    parking_formatted = "Parking is not available"
                else:
                    parking_formatted = "Parking unknown"
                
                # Prepare ACF field updates
                acf_fields = {
                    'external_featured_image': external_featured_image,
                    'featured_image_source': featured_image_source,
                    'photo_count': photo_count,
                    'image_selection_status': image_selection_status,
                    'photo_urls': '\n'.join(photo_urls) if photo_urls else '',
                    'google_map': google_map_data,
                    'seo_title': seo_title,
                    'seo_meta_description': seo_meta_description,
                    'wheelchair_accessible': wheelchair_formatted,
                    'parking_available': parking_formatted
                }
                
                # Update WordPress post with ACF fields and SEO meta
                success = wp.update_post_with_seo_meta(wordpress_post_id, acf_fields, seo_title, seo_meta_description)
                
                if success:
                    print(f"✅ {name}: Updated ACF fields and SEO data")
                    print(f"   📸 Featured Image: {featured_image_source}")
                    print(f"   🔢 Photo Count: {photo_count}")
                    print(f"   📊 Status: {image_selection_status}")
                    print(f"   🎯 SEO Title: {seo_title[:40]}..." if len(seo_title) > 40 else f"   🎯 SEO Title: {seo_title}")
                    print(f"   ♿ Wheelchair: {wheelchair_formatted}")
                    print(f"   🅿️ Parking: {parking_formatted}")
                    updated_count += 1
                else:
                    print(f"❌ {name}: Failed to update ACF fields")
                    error_count += 1
                
            except Exception as e:
                print(f"❌ Error updating {name}: {str(e)}")
                error_count += 1
        
        print(f"\n📊 Update Summary:")
        print(f"✅ Successfully updated: {updated_count}")
        print(f"❌ Errors: {error_count}")
        print(f"📋 Total processed: {len(providers)}")
        
        if updated_count > 0:
            print(f"\n🎉 ACF fields, SEO data, and accessibility info have been populated! Available fields:")
            print(f"   {{acf:external_featured_image}} - Featured image URL")
            print(f"   {{acf:featured_image_source}} - Image source method")
            print(f"   {{acf:photo_count}} - Number of photos")
            print(f"   {{acf:image_selection_status}} - Selection status")
            print(f"   {{acf:seo_title}} - SEO optimized title")
            print(f"   {{acf:seo_meta_description}} - SEO meta description")
            print(f"   {{acf:wheelchair_accessible}} - Wheelchair accessibility")
            print(f"   {{acf:parking_available}} - Parking availability")
            print(f"   📊 Yoast SEO meta fields also populated for search engines")
        
    except Exception as e:
        print(f"💥 Fatal error: {str(e)}")
        return False
    
    finally:
        # Close database connection
        session.close()
    
    return True

if __name__ == "__main__":
    force_update_acf_fields() 