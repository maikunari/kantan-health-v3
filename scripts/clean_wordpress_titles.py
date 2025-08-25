#!/usr/bin/env python3
"""
Clean WordPress titles to use romaji only (no Japanese in parentheses)
Updates all WordPress posts to have clean, romaji-only titles
"""

import sys
import os
import logging
import time
import requests
from typing import List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from sqlalchemy import text
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_providers_with_romaji(db) -> List:
    """Get all providers that have romaji names and WordPress posts"""
    
    session = db.get_session()
    
    try:
        query = """
            SELECT id, provider_name, provider_name_romaji, wordpress_post_id
            FROM providers
            WHERE provider_name_romaji IS NOT NULL
            AND wordpress_post_id IS NOT NULL
            ORDER BY id
        """
        
        result = session.execute(text(query))
        
        providers = []
        for row in result:
            class ProviderData:
                def __init__(self, row):
                    self.id = row[0]
                    self.provider_name = row[1]
                    self.provider_name_romaji = row[2]
                    self.wordpress_post_id = row[3]
            
            providers.append(ProviderData(row))
        
        return providers
        
    finally:
        session.close()


def clean_wordpress_title(provider, wp_config) -> bool:
    """Update WordPress post title to use romaji only"""
    
    try:
        # Use clean romaji title only (no Japanese in parentheses)
        clean_title = provider.provider_name_romaji
        
        # Update WordPress post
        response = requests.post(
            f"{wp_config['url']}/wp-json/wp/v2/healthcare_provider/{provider.wordpress_post_id}",
            auth=(wp_config['username'], wp_config['password']),
            json={'title': clean_title},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Cleaned title: {clean_title}")
            return True
        elif response.status_code == 404:
            logger.warning(f"⚠️  Post {provider.wordpress_post_id} not found")
            return False
        else:
            logger.error(f"❌ Failed to update: {response.status_code}")
            logger.debug(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


def main():
    """Main execution"""
    
    # Initialize database
    db = DatabaseManager()
    
    # Load WordPress configuration
    load_dotenv('config/.env')
    
    wp_config = {
        'url': os.getenv('WORDPRESS_URL'),
        'username': os.getenv('WORDPRESS_USERNAME'),
        'password': os.getenv('WORDPRESS_APPLICATION_PASSWORD')
    }
    
    if not all(wp_config.values()):
        logger.error("❌ WordPress configuration not found in environment")
        return 1
    
    logger.info("="*60)
    logger.info("🧹 CLEANING WORDPRESS TITLES (ROMAJI ONLY)")
    logger.info("="*60)
    
    # Get all providers with romaji names
    providers = get_providers_with_romaji(db)
    
    if not providers:
        logger.info("No providers with romaji names found")
        return 0
    
    logger.info(f"Found {len(providers)} posts to clean")
    logger.info("-"*60)
    
    # Show preview
    logger.info("\n📋 Preview of changes:")
    for provider in providers[:3]:
        old_format = f"{provider.provider_name_romaji} ({provider.provider_name})"
        new_format = provider.provider_name_romaji
        logger.info(f"\nProvider: {provider.provider_name}")
        logger.info(f"  Old: {old_format}")
        logger.info(f"  New: {new_format}")
    
    logger.info("\n" + "-"*60)
    logger.info("Processing all providers...\n")
    
    # Process each provider
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, provider in enumerate(providers, 1):
        logger.info(f"[{i}/{len(providers)}] {provider.provider_name}")
        
        if clean_wordpress_title(provider, wp_config):
            success_count += 1
        else:
            failed_count += 1
        
        # Rate limiting
        if i % 10 == 0:
            logger.info(f"   Progress: {i}/{len(providers)} processed")
            time.sleep(1)  # Small delay every 10 requests
        else:
            time.sleep(0.3)  # Smaller delay between requests
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("✅ TITLE CLEANUP COMPLETE")
    logger.info(f"   Total processed: {len(providers)}")
    logger.info(f"   Successfully cleaned: {success_count}")
    if failed_count > 0:
        logger.info(f"   Failed: {failed_count}")
    if skipped_count > 0:
        logger.info(f"   Skipped: {skipped_count}")
    logger.info("="*60)
    
    # Show examples
    if success_count > 0:
        logger.info("\n📌 WordPress titles are now clean:")
        logger.info("   Examples:")
        for provider in providers[:5]:
            if provider.provider_name_romaji:
                logger.info(f"   • {provider.provider_name_romaji}")
    
    logger.info("\n✨ All titles now use romaji only, without Japanese in parentheses")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())