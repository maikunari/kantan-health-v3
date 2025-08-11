#!/usr/bin/env python3
"""
Refresh all photo references and update WordPress with current references
This ensures WordPress has the same photo references as our database
"""

import os
import sys
import json
import logging
import requests
from requests.auth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database import DatabaseManager
from src.collectors.google_places import GooglePlacesCollector
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WordPress configuration
WP_URL = os.getenv('WORDPRESS_URL', 'https://kantanhealth.jp')
WP_USERNAME = os.getenv('WORDPRESS_USERNAME')
WP_PASSWORD = os.getenv('WORDPRESS_APPLICATION_PASSWORD')

# Production API URL
PRODUCTION_API_URL = "https://kantanhealth.jp/api/photo/"

def refresh_provider_photos(provider_id: int, provider_name: str, google_place_id: str, wordpress_post_id: int) -> dict:
    """Refresh a single provider's photos"""
    try:
        # Get fresh photo references from Google
        collector = GooglePlacesCollector()
        details = collector.get_place_details(google_place_id, force_refresh=True)
        
        if not details or 'photos' not in details:
            return {
                'provider_id': provider_id,
                'provider_name': provider_name,
                'status': 'no_photos',
                'message': 'No photos available from Google'
            }
        
        # Extract new references
        new_refs = [p.get('photo_reference') for p in details['photos'] if p.get('photo_reference')][:10]
        
        if not new_refs:
            return {
                'provider_id': provider_id,
                'provider_name': provider_name,
                'status': 'no_references',
                'message': 'No photo references in Google response'
            }
        
        # Update database
        db = DatabaseManager()
        session = db.get_session()
        
        session.execute(text("""
            UPDATE providers 
            SET photo_references = :refs
            WHERE id = :id
        """), {
            'refs': new_refs,
            'id': provider_id
        })
        session.commit()
        session.close()
        
        # Update WordPress with new URLs
        photo_urls = [f"{PRODUCTION_API_URL}{ref}" for ref in new_refs]
        
        update_data = {
            'acf': {
                'photo_urls': '\n'.join(photo_urls),
                'external_featured_image': photo_urls[0],
                'photo_count': len(photo_urls)
            }
        }
        
        response = requests.post(
            f"{WP_URL}/wp-json/wp/v2/healthcare_provider/{wordpress_post_id}",
            json=update_data,
            auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD),
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            return {
                'provider_id': provider_id,
                'provider_name': provider_name,
                'status': 'success',
                'message': f'Updated with {len(new_refs)} photos'
            }
        else:
            return {
                'provider_id': provider_id,
                'provider_name': provider_name,
                'status': 'wp_error',
                'message': f'WordPress update failed: {response.status_code}'
            }
            
    except Exception as e:
        return {
            'provider_id': provider_id,
            'provider_name': provider_name,
            'status': 'error',
            'message': str(e)
        }

def main():
    """Main function to refresh all WordPress photo URLs with fresh references"""
    logger.info("🔧 Starting complete photo refresh for all WordPress providers...")
    logger.info(f"📍 Using production API URL: {PRODUCTION_API_URL}")
    
    # Initialize database
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Get all providers with WordPress posts
        providers = session.execute(text("""
            SELECT id, provider_name, google_place_id, wordpress_post_id
            FROM providers
            WHERE wordpress_post_id IS NOT NULL 
            AND wordpress_post_id > 0
            AND google_place_id IS NOT NULL
            ORDER BY id
        """)).fetchall()
        
        logger.info(f"📊 Found {len(providers)} providers to refresh")
        
        # Process in parallel for speed
        results = {
            'success': 0,
            'no_photos': 0,
            'wp_error': 0,
            'error': 0
        }
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all tasks
            futures = {
                executor.submit(
                    refresh_provider_photos,
                    p.id,
                    p.provider_name,
                    p.google_place_id,
                    p.wordpress_post_id
                ): p for p in providers
            }
            
            # Process results as they complete
            for future in as_completed(futures):
                provider = futures[future]
                result = future.result()
                
                status = result['status']
                results[status] = results.get(status, 0) + 1
                
                if status == 'success':
                    logger.info(f"✅ {result['provider_name']}: {result['message']}")
                elif status == 'no_photos':
                    logger.warning(f"📷 {result['provider_name']}: {result['message']}")
                elif status == 'wp_error':
                    logger.error(f"🌐 {result['provider_name']}: {result['message']}")
                else:
                    logger.error(f"❌ {result['provider_name']}: {result['message']}")
        
        logger.info(f"""
        ✅ Photo refresh complete!
        📊 Results:
           - Success: {results['success']} providers
           - No photos: {results.get('no_photos', 0)} providers  
           - WordPress errors: {results.get('wp_error', 0)} providers
           - Other errors: {results.get('error', 0)} providers
           - Total: {len(providers)} providers
        
        🌐 All photos now use fresh references via: {PRODUCTION_API_URL}
        """)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        
    finally:
        session.close()

if __name__ == "__main__":
    main()