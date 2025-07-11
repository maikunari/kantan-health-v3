#!/usr/bin/env python3
"""
Cleanup Providers Without Photos
Removes providers that don't have photos from the database and WordPress.
"""

import json
from postgres_integration import PostgresIntegration, Provider
from wordpress_integration import WordPressIntegration
import requests

def cleanup_providers_without_photos():
    """Remove providers without photos from database and WordPress"""
    
    # Initialize database connection
    db = PostgresIntegration()
    session = db.Session()
    
    try:
        # Find providers without photos
        providers_without_photos = []
        
        # Get all providers with WordPress posts
        providers = session.query(Provider).filter(
            Provider.wordpress_post_id.isnot(None)
        ).all()
        
        print(f"🔍 Checking {len(providers)} providers for photo availability...")
        
        for provider in providers:
            if not provider.photo_urls:
                providers_without_photos.append(provider)
                print(f"📸 NO PHOTOS: {provider.provider_name}")
                continue
            
            try:
                # Parse photo URLs
                if isinstance(provider.photo_urls, str):
                    photo_list = json.loads(provider.photo_urls)
                else:
                    photo_list = provider.photo_urls
                
                if not photo_list or len(photo_list) == 0:
                    providers_without_photos.append(provider)
                    print(f"📸 EMPTY PHOTOS: {provider.provider_name}")
                else:
                    print(f"📸 HAS PHOTOS: {provider.provider_name} ({len(photo_list)} photos)")
                    
            except json.JSONDecodeError:
                providers_without_photos.append(provider)
                print(f"📸 INVALID PHOTOS: {provider.provider_name}")
        
        print(f"\n📊 Found {len(providers_without_photos)} providers without photos:")
        for provider in providers_without_photos:
            print(f"   - {provider.provider_name} (WP ID: {provider.wordpress_post_id})")
        
        if not providers_without_photos:
            print("✅ All providers have photos! Nothing to cleanup.")
            return
        
        # Ask for confirmation
        response = input(f"\n⚠️  Do you want to remove these {len(providers_without_photos)} providers from database and WordPress? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cleanup cancelled.")
            return
        
        # Remove from WordPress first
        wp_integration = WordPressIntegration()
        wp_removed = 0
        
        for provider in providers_without_photos:
            if provider.wordpress_post_id:
                try:
                    # Delete WordPress post
                    delete_url = f"{wp_integration.wordpress_url}/wp-json/wp/v2/healthcare_provider/{provider.wordpress_post_id}"
                    response = requests.delete(
                        delete_url,
                        auth=(wp_integration.username, wp_integration.application_password)
                    )
                    
                    if response.status_code == 200:
                        print(f"🗑️  Removed from WordPress: {provider.provider_name}")
                        wp_removed += 1
                    else:
                        print(f"⚠️  Failed to remove from WordPress: {provider.provider_name} ({response.status_code})")
                        
                except Exception as e:
                    print(f"❌ Error removing from WordPress: {provider.provider_name} - {str(e)}")
        
        # Remove from database
        db_removed = 0
        for provider in providers_without_photos:
            try:
                session.delete(provider)
                print(f"🗑️  Removed from database: {provider.provider_name}")
                db_removed += 1
            except Exception as e:
                print(f"❌ Error removing from database: {provider.provider_name} - {str(e)}")
        
        # Commit changes
        session.commit()
        
        print(f"\n✅ Cleanup completed:")
        print(f"   📊 Providers without photos found: {len(providers_without_photos)}")
        print(f"   🗑️  Removed from WordPress: {wp_removed}")
        print(f"   🗑️  Removed from database: {db_removed}")
        
        # Show remaining providers
        remaining = session.query(Provider).filter(
            Provider.wordpress_post_id.isnot(None)
        ).count()
        print(f"   ✅ Remaining providers with photos: {remaining}")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    cleanup_providers_without_photos() 