#!/usr/bin/env python3
"""
Fix WordPress Photo URLs to use proxy endpoint instead of direct Google API
This ensures compliance with Google Places TOS and protects API keys
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any
import requests
from requests.auth import HTTPBasicAuth

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database import DatabaseManager
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

# Your API proxy endpoint
API_BASE_URL = "https://kantanhealth.jp/api/photo/"

def convert_to_proxy_urls(photo_urls: List[str]) -> List[str]:
    """Convert Google API URLs to proxy URLs
    
    Args:
        photo_urls: List of Google API URLs with exposed keys
        
    Returns:
        List of proxy URLs
    """
    proxy_urls = []
    
    for url in photo_urls:
        if 'photoreference=' in url:
            # Extract the photo reference from the URL
            start = url.find('photoreference=') + len('photoreference=')
            end = url.find('&', start)
            if end == -1:
                end = len(url)
            reference = url[start:end]
            
            # Create proxy URL
            proxy_url = f"{API_BASE_URL}{reference}"
            proxy_urls.append(proxy_url)
            logger.debug(f"Converted to proxy: {proxy_url[:100]}...")
        else:
            # Keep original if it's already a proxy URL or different format
            proxy_urls.append(url)
    
    return proxy_urls

def update_wordpress_acf_fields(post_id: int, photo_urls: List[str]) -> bool:
    """Update WordPress ACF fields with corrected photo URLs
    
    Args:
        post_id: WordPress post ID
        photo_urls: List of proxy photo URLs
        
    Returns:
        Success status
    """
    try:
        # Prepare ACF data - must be under 'acf' key for standard REST API
        update_data = {
            'acf': {
                'photo_urls': '\n'.join(photo_urls[:10]),  # ACF stores as newline-separated
                'external_featured_image': photo_urls[0] if photo_urls else '',
                'photo_count': len(photo_urls)
            }
        }
        
        # Update via standard WordPress REST API
        response = requests.post(
            f"{WP_URL}/wp-json/wp/v2/healthcare_provider/{post_id}",
            json=update_data,
            auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD),
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Updated WordPress post {post_id}")
            return True
        else:
            logger.error(f"❌ Failed to update post {post_id}: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating post {post_id}: {str(e)}")
        return False

def main():
    """Main function to fix all WordPress photo URLs"""
    logger.info("🔧 Starting WordPress photo URL fix...")
    
    # Initialize database
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Get all providers with WordPress posts and photo URLs
        providers = session.execute(text("""
            SELECT id, provider_name, wordpress_post_id, photo_urls, photo_references
            FROM providers
            WHERE wordpress_post_id IS NOT NULL 
            AND wordpress_post_id > 0
            AND photo_urls IS NOT NULL
            ORDER BY id
        """)).fetchall()
        
        logger.info(f"📊 Found {len(providers)} providers to check")
        
        updated_count = 0
        error_count = 0
        
        for provider in providers:
            try:
                # Parse existing photo URLs
                if provider.photo_urls:
                    if isinstance(provider.photo_urls, str):
                        current_urls = json.loads(provider.photo_urls)
                    else:
                        current_urls = provider.photo_urls
                    
                    # Check if URLs need conversion
                    if current_urls and any('maps.googleapis.com' in url for url in current_urls):
                        logger.info(f"🔄 Processing: {provider.provider_name}")
                        
                        # Convert to proxy URLs
                        proxy_urls = convert_to_proxy_urls(current_urls)
                        
                        # Update in database
                        session.execute(text("""
                            UPDATE providers 
                            SET photo_urls = :photo_urls
                            WHERE id = :id
                        """), {
                            'photo_urls': json.dumps(proxy_urls),
                            'id': provider.id
                        })
                        
                        # Update in WordPress
                        if update_wordpress_acf_fields(provider.wordpress_post_id, proxy_urls):
                            updated_count += 1
                        else:
                            error_count += 1
                    else:
                        logger.debug(f"⏭️  Skipping {provider.provider_name} - already using proxy URLs")
                        
            except Exception as e:
                logger.error(f"❌ Error processing provider {provider.id}: {str(e)}")
                error_count += 1
        
        # Commit database changes
        session.commit()
        
        logger.info(f"""
        ✅ Photo URL fix complete!
        📊 Results:
           - Updated: {updated_count} providers
           - Errors: {error_count} providers
           - Total: {len(providers)} providers
        """)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        session.rollback()
        
    finally:
        session.close()

if __name__ == "__main__":
    main()