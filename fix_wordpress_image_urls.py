#!/usr/bin/env python3
"""
Fix WordPress image URLs to use production API instead of localhost
"""

import os
import sys
import json
import logging
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

# Production API URL
PRODUCTION_API_URL = "https://kantanhealth.jp/api/photo/"

def update_wordpress_image_urls(post_id: int, photo_references: list) -> bool:
    """Update WordPress ACF fields with correct production API URLs
    
    Args:
        post_id: WordPress post ID
        photo_references: List of photo references
        
    Returns:
        Success status
    """
    try:
        # Create proper proxy URLs using production domain
        photo_urls = [f"{PRODUCTION_API_URL}{ref}" for ref in photo_references]
        
        # Prepare ACF data
        update_data = {
            'acf': {
                'photo_urls': '\n'.join(photo_urls[:10]),  # ACF stores as newline-separated
                'external_featured_image': photo_urls[0] if photo_urls else '',
                'photo_count': len(photo_urls)
            }
        }
        
        # Update via WordPress REST API
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
            logger.debug(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating post {post_id}: {str(e)}")
        return False

def main():
    """Main function to fix all WordPress image URLs"""
    logger.info("🔧 Starting WordPress image URL fix...")
    logger.info(f"📍 Using production API URL: {PRODUCTION_API_URL}")
    
    # Initialize database
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Get all providers with WordPress posts and photo references
        providers = session.execute(text("""
            SELECT id, provider_name, wordpress_post_id, photo_references
            FROM providers
            WHERE wordpress_post_id IS NOT NULL 
            AND wordpress_post_id > 0
            AND photo_references IS NOT NULL
            ORDER BY id
        """)).fetchall()
        
        logger.info(f"📊 Found {len(providers)} providers with WordPress posts")
        
        updated_count = 0
        error_count = 0
        
        for provider in providers:
            try:
                # Parse photo references
                if provider.photo_references:
                    # Handle PostgreSQL array format
                    if isinstance(provider.photo_references, list):
                        references = provider.photo_references
                    elif isinstance(provider.photo_references, str):
                        # Try parsing as JSON
                        try:
                            references = json.loads(provider.photo_references)
                        except:
                            # Might be PostgreSQL array string format
                            references = provider.photo_references.strip('{}').split(',')
                    else:
                        references = []
                    
                    if references:
                        logger.info(f"🔄 Updating: {provider.provider_name} (Post ID: {provider.wordpress_post_id})")
                        
                        # Update WordPress with correct production URLs
                        if update_wordpress_image_urls(provider.wordpress_post_id, references):
                            updated_count += 1
                        else:
                            error_count += 1
                    else:
                        logger.debug(f"⏭️  No references for {provider.provider_name}")
                        
            except Exception as e:
                logger.error(f"❌ Error processing provider {provider.id}: {str(e)}")
                error_count += 1
        
        logger.info(f"""
        ✅ WordPress image URL fix complete!
        📊 Results:
           - Updated: {updated_count} providers
           - Errors: {error_count} providers
           - Total: {len(providers)} providers
        
        🌐 All images now use: {PRODUCTION_API_URL}
        """)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        
    finally:
        session.close()

if __name__ == "__main__":
    main()