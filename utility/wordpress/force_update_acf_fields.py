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
                
                # Get photo URLs and counts
                photo_urls_str = provider.get('photo_urls', '')
                photo_urls = [url.strip() for url in photo_urls_str.split('\n') if url.strip()] if photo_urls_str else []
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
                
                # Prepare ACF field updates
                acf_fields = {
                    'external_featured_image': external_featured_image,
                    'featured_image_source': featured_image_source,
                    'photo_count': photo_count,
                    'image_selection_status': image_selection_status,
                    'photo_urls': '\n'.join(photo_urls) if photo_urls else ''
                }
                
                # Update WordPress post with ACF fields
                success = wp.update_post_acf_fields(wordpress_post_id, acf_fields)
                
                if success:
                    print(f"✅ {name}: Updated ACF fields")
                    print(f"   📸 Featured Image: {featured_image_source}")
                    print(f"   🔢 Photo Count: {photo_count}")
                    print(f"   📊 Status: {image_selection_status}")
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
            print(f"\n🎉 ACF fields have been populated! Your Greenshift integration should now work with:")
            print(f"   {{acf:external_featured_image}} - Featured image URL")
            print(f"   {{acf:featured_image_source}} - Image source method")
            print(f"   {{acf:photo_count}} - Number of photos")
            print(f"   {{acf:image_selection_status}} - Selection status")
        
    except Exception as e:
        print(f"💥 Fatal error: {str(e)}")
        return False
    
    finally:
        # Close database connection
        session.close()
    
    return True

if __name__ == "__main__":
    force_update_acf_fields() 