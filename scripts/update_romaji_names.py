#!/usr/bin/env python3
"""
Update romaji names for all Japanese providers
Generates romanized versions of Japanese provider names and updates WordPress titles
"""

import sys
import os
import logging
from typing import List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.utils.romaji_converter import contains_japanese, convert_to_romaji, get_display_name
from sqlalchemy import text
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_japanese_providers(db) -> List:
    """Find all providers with Japanese names"""
    
    session = db.get_session()
    
    try:
        # Get all providers
        query = """
            SELECT id, provider_name, provider_name_romaji, wordpress_post_id
            FROM providers
            ORDER BY id
        """
        
        result = session.execute(text(query))
        
        japanese_providers = []
        for row in result:
            # Check if name contains Japanese
            if contains_japanese(row.provider_name):
                class ProviderData:
                    def __init__(self, row):
                        self.id = row[0]
                        self.provider_name = row[1]
                        self.provider_name_romaji = row[2]
                        self.wordpress_post_id = row[3]
                
                japanese_providers.append(ProviderData(row))
        
        return japanese_providers
        
    finally:
        session.close()


def update_provider_romaji(db, provider) -> bool:
    """Update romaji name for a provider"""
    
    try:
        # Generate romaji if not already present
        if not provider.provider_name_romaji:
            romaji = convert_to_romaji(provider.provider_name)
            
            if romaji and romaji != provider.provider_name:
                # Update database
                success = db.update_provider_field(provider.id, 'provider_name_romaji', romaji)
                
                if success:
                    logger.info(f"✅ Updated romaji for {provider.provider_name}")
                    logger.info(f"   Romaji: {romaji}")
                    provider.provider_name_romaji = romaji
                    return True
                else:
                    logger.error(f"❌ Failed to update database for {provider.provider_name}")
                    return False
            else:
                logger.warning(f"⚠️  Could not generate romaji for {provider.provider_name}")
                return False
        else:
            logger.info(f"✓ Already has romaji: {provider.provider_name_romaji}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error updating {provider.provider_name}: {e}")
        return False


def update_wordpress_title(provider, wp_config) -> bool:
    """Update WordPress post title with romaji version"""
    
    if not provider.wordpress_post_id:
        return True  # Skip if no WordPress post
    
    try:
        # Get display name with romaji
        display_name = get_display_name(provider.provider_name, provider.provider_name_romaji)
        
        # Update WordPress post title
        response = requests.post(
            f"{wp_config['url']}/wp-json/wp/v2/healthcare_provider/{provider.wordpress_post_id}",
            auth=(wp_config['username'], wp_config['password']),
            json={'title': display_name},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Updated WordPress title to: {display_name}")
            return True
        elif response.status_code == 404:
            logger.warning(f"⚠️  WordPress post {provider.wordpress_post_id} not found")
            return False
        else:
            logger.error(f"❌ Failed to update WordPress: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating WordPress: {e}")
        return False


def main():
    """Main execution"""
    
    # Initialize database
    db = DatabaseManager()
    
    # Get WordPress config from environment
    from dotenv import load_dotenv
    load_dotenv('config/.env')
    
    wp_config = {
        'url': os.getenv('WORDPRESS_URL'),
        'username': os.getenv('WORDPRESS_USERNAME'),
        'password': os.getenv('WORDPRESS_APPLICATION_PASSWORD')
    }
    
    logger.info("="*60)
    logger.info("🔧 UPDATING ROMAJI NAMES FOR JAPANESE PROVIDERS")
    logger.info("="*60)
    
    # Find providers with Japanese names
    japanese_providers = find_japanese_providers(db)
    
    if not japanese_providers:
        logger.info("No providers with Japanese names found")
        return 0
    
    logger.info(f"Found {len(japanese_providers)} providers with Japanese names")
    logger.info("-"*60)
    
    # Process each provider
    db_success = 0
    wp_success = 0
    
    for i, provider in enumerate(japanese_providers, 1):
        logger.info(f"\n[{i}/{len(japanese_providers)}] {provider.provider_name}")
        
        # Update romaji in database
        if update_provider_romaji(db, provider):
            db_success += 1
            
            # Update WordPress title if applicable
            if provider.wordpress_post_id and update_wordpress_title(provider, wp_config):
                wp_success += 1
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("✅ ROMAJI UPDATE COMPLETE")
    logger.info(f"   Database updates: {db_success}/{len(japanese_providers)}")
    if any(p.wordpress_post_id for p in japanese_providers):
        wp_count = sum(1 for p in japanese_providers if p.wordpress_post_id)
        logger.info(f"   WordPress updates: {wp_success}/{wp_count}")
    logger.info("="*60)
    
    # Show examples
    if db_success > 0:
        logger.info("\n📌 Example romaji conversions:")
        for provider in japanese_providers[:5]:
            if provider.provider_name_romaji:
                display = get_display_name(provider.provider_name, provider.provider_name_romaji)
                logger.info(f"   {display}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())