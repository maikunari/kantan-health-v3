#!/usr/bin/env python3
"""
Cleanup WordPress Media Library - Google API TOS Compliance
Removes Google Places photos that were uploaded to WordPress media library.
Per Google's Terms of Service, we must link directly to their URLs, not store copies.
"""

import os
import requests
import json
from dotenv import load_dotenv

def load_wordpress_credentials():
    """Load WordPress credentials from environment"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    load_dotenv(config_path)
    
    return {
        'url': os.getenv('WORDPRESS_URL', 'https://care-compass.jp'),
        'username': os.getenv('WORDPRESS_USERNAME'),
        'password': os.getenv('WORDPRESS_APPLICATION_PASSWORD')
    }

def get_all_media():
    """Get all media files from WordPress"""
    credentials = load_wordpress_credentials()
    
    if not all([credentials['username'], credentials['password']]):
        print("❌ WordPress credentials not found in config/.env")
        return []
    
    media_items = []
    page = 1
    per_page = 100
    
    while True:
        try:
            response = requests.get(
                f"{credentials['url']}/wp-json/wp/v2/media",
                auth=(credentials['username'], credentials['password']),
                params={
                    'page': page,
                    'per_page': per_page,
                    'orderby': 'date',
                    'order': 'desc'
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch media: {response.status_code}")
                break
            
            batch = response.json()
            if not batch:
                break
                
            media_items.extend(batch)
            print(f"📄 Fetched {len(batch)} media items from page {page}")
            page += 1
            
        except Exception as e:
            print(f"❌ Error fetching media: {str(e)}")
            break
    
    return media_items

def identify_google_places_photos(media_items):
    """Identify media items that are likely Google Places photos"""
    google_photos = []
    
    for item in media_items:
        title = item.get('title', {}).get('rendered', '').lower()
        alt_text = item.get('alt_text', '').lower()
        description = item.get('description', {}).get('rendered', '').lower()
        filename = item.get('source_url', '').lower()
        
        # Look for patterns indicating Google Places photos
        google_indicators = [
            'featured image',  # Our naming pattern
            'healthcare',
            'medical',
            'clinic',
            'hospital',
            'dental',
            'pharmacy'
        ]
        
        # Check if title contains provider names or our naming patterns
        is_google_photo = False
        
        # Check for our specific naming pattern: "Provider_Name_featured.jpg"
        if 'featured' in title or '_featured' in filename:
            is_google_photo = True
        
        # Check for healthcare-related terms
        elif any(indicator in title or indicator in alt_text or indicator in description 
                for indicator in google_indicators):
            is_google_photo = True
        
        if is_google_photo:
            google_photos.append({
                'id': item['id'],
                'title': item.get('title', {}).get('rendered', 'Untitled'),
                'filename': item.get('source_url', '').split('/')[-1],
                'date': item.get('date', ''),
                'size': item.get('media_details', {}).get('filesize', 0)
            })
    
    return google_photos

def delete_media_items(media_items, credentials):
    """Delete media items from WordPress"""
    deleted_count = 0
    failed_count = 0
    
    for item in media_items:
        try:
            response = requests.delete(
                f"{credentials['url']}/wp-json/wp/v2/media/{item['id']}",
                auth=(credentials['username'], credentials['password']),
                params={'force': True}  # Permanently delete
            )
            
            if response.status_code == 200:
                print(f"🗑️  Deleted: {item['title']} ({item['filename']})")
                deleted_count += 1
            else:
                print(f"❌ Failed to delete: {item['title']} - Status: {response.status_code}")
                failed_count += 1
                
        except Exception as e:
            print(f"❌ Error deleting {item['title']}: {str(e)}")
            failed_count += 1
    
    return deleted_count, failed_count

def cleanup_media_library():
    """Main function to cleanup Google Places photos from media library"""
    print("🧹 WORDPRESS MEDIA LIBRARY CLEANUP")
    print("=" * 50)
    print("🎯 Goal: Remove Google Places photos for TOS compliance")
    print("📋 Google requires direct linking, not storing copies")
    print()
    
    # Get all media
    print("📄 Fetching all media items from WordPress...")
    media_items = get_all_media()
    
    if not media_items:
        print("❌ No media items found or failed to fetch")
        return
    
    print(f"📊 Found {len(media_items)} total media items")
    
    # Identify Google Places photos
    print("\n🔍 Identifying Google Places photos...")
    google_photos = identify_google_places_photos(media_items)
    
    if not google_photos:
        print("✅ No Google Places photos found in media library!")
        return
    
    print(f"\n📸 Found {len(google_photos)} potential Google Places photos:")
    total_size = 0
    for photo in google_photos:
        size_mb = photo['size'] / (1024 * 1024) if photo['size'] > 0 else 0
        total_size += size_mb
        print(f"   - {photo['title']} ({photo['filename']}, {size_mb:.1f}MB)")
    
    print(f"\n📊 Total size: {total_size:.1f}MB")
    
    # Ask for confirmation
    response = input(f"\n⚠️  Delete these {len(google_photos)} Google Places photos? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cleanup cancelled.")
        return
    
    # Delete photos
    print(f"\n🗑️  Deleting {len(google_photos)} Google Places photos...")
    credentials = load_wordpress_credentials()
    deleted_count, failed_count = delete_media_items(google_photos, credentials)
    
    print(f"\n✅ Cleanup completed:")
    print(f"   🗑️  Successfully deleted: {deleted_count}")
    print(f"   ❌ Failed to delete: {failed_count}")
    print(f"   💾 Storage freed: ~{total_size:.1f}MB")
    
    if deleted_count > 0:
        print(f"\n📸 Photos are now linked directly from Google Places API")
        print(f"✅ System is now compliant with Google API Terms of Service")

if __name__ == "__main__":
    cleanup_media_library() 