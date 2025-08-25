#!/usr/bin/env python3
"""
Fix romaji names with improved medical term translation
Re-processes all Japanese provider names with better romaji conversion
"""

import sys
import os
import logging
from typing import List
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.utils.romaji_converter import contains_japanese, convert_to_romaji, get_display_name
from sqlalchemy import text
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_all_japanese_providers(db) -> List:
    """Get all providers with Japanese names that have romaji"""
    
    session = db.get_session()
    
    try:
        # Get providers that already have romaji (we want to update them)
        query = """
            SELECT id, provider_name, provider_name_romaji, wordpress_post_id
            FROM providers
            WHERE provider_name_romaji IS NOT NULL
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


def compare_and_update_romaji(db, provider, wp_config) -> dict:
    """Compare old and new romaji, update if improved"""
    
    result = {
        'updated': False,
        'old_romaji': provider.provider_name_romaji,
        'new_romaji': None,
        'wp_updated': False
    }
    
    try:
        # Generate new romaji with improved converter
        new_romaji = convert_to_romaji(provider.provider_name)
        result['new_romaji'] = new_romaji
        
        # Check if it's different and better
        if new_romaji and new_romaji != provider.provider_name_romaji:
            # Check if new version has proper medical terms
            has_medical_terms = any(term in new_romaji for term in [
                'Clinic', 'Hospital', 'Dental', 'Pharmacy', 
                'Medical', 'Center', 'Pediatrics', 'Surgery',
                'Internal Medicine', 'ENT', 'Station'
            ])
            
            if has_medical_terms:
                # Update database
                success = db.update_provider_field(provider.id, 'provider_name_romaji', new_romaji)
                
                if success:
                    result['updated'] = True
                    logger.info(f"✅ Updated romaji for {provider.provider_name}")
                    logger.info(f"   Old: {provider.provider_name_romaji}")
                    logger.info(f"   New: {new_romaji}")
                    
                    # Update WordPress if applicable
                    if provider.wordpress_post_id and wp_config:
                        display_name = get_display_name(provider.provider_name, new_romaji)
                        
                        try:
                            response = requests.post(
                                f"{wp_config['url']}/wp-json/wp/v2/healthcare_provider/{provider.wordpress_post_id}",
                                auth=(wp_config['username'], wp_config['password']),
                                json={'title': display_name},
                                headers={'Content-Type': 'application/json'},
                                timeout=30
                            )
                            
                            if response.status_code == 200:
                                result['wp_updated'] = True
                                logger.info(f"   WordPress updated: {display_name}")
                            elif response.status_code == 404:
                                logger.debug(f"   WordPress post {provider.wordpress_post_id} not found")
                            
                        except Exception as e:
                            logger.debug(f"   WordPress update error: {e}")
                else:
                    logger.error(f"❌ Failed to update database for {provider.provider_name}")
            else:
                logger.debug(f"⏭  No improvement for {provider.provider_name} (no medical terms)")
        else:
            logger.debug(f"✓ Already optimal: {provider.provider_name}")
            
    except Exception as e:
        logger.error(f"❌ Error processing {provider.provider_name}: {e}")
    
    return result


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
    logger.info("🔧 FIXING ROMAJI NAMES WITH IMPROVED CONVERTER")
    logger.info("="*60)
    
    # Get all providers with existing romaji
    providers = get_all_japanese_providers(db)
    
    if not providers:
        logger.info("No providers with romaji found")
        return 0
    
    logger.info(f"Found {len(providers)} providers with existing romaji")
    logger.info("-"*60)
    
    # Process each provider
    stats = {
        'total': len(providers),
        'updated': 0,
        'wp_updated': 0,
        'unchanged': 0
    }
    
    # Show some examples first
    logger.info("\n📋 Preview of improvements:")
    preview_count = 0
    for provider in providers[:10]:
        new_romaji = convert_to_romaji(provider.provider_name)
        if new_romaji != provider.provider_name_romaji:
            preview_count += 1
            logger.info(f"\n{provider.provider_name}")
            logger.info(f"  Old: {provider.provider_name_romaji}")
            logger.info(f"  New: {new_romaji}")
            if preview_count >= 3:
                break
    
    logger.info("\n" + "-"*60)
    logger.info("Processing all providers...\n")
    
    for i, provider in enumerate(providers, 1):
        if i % 10 == 0:
            logger.info(f"Progress: {i}/{len(providers)}")
        
        result = compare_and_update_romaji(db, provider, wp_config)
        
        if result['updated']:
            stats['updated'] += 1
            if result['wp_updated']:
                stats['wp_updated'] += 1
        else:
            stats['unchanged'] += 1
        
        # Small delay to avoid overwhelming WordPress API
        if result['wp_updated']:
            time.sleep(0.3)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("✅ ROMAJI FIX COMPLETE")
    logger.info(f"   Total processed: {stats['total']}")
    logger.info(f"   Database updated: {stats['updated']}")
    logger.info(f"   WordPress updated: {stats['wp_updated']}")
    logger.info(f"   Unchanged: {stats['unchanged']}")
    logger.info("="*60)
    
    # Show final examples
    if stats['updated'] > 0:
        logger.info("\n📌 Examples of improved names:")
        
        # Get a few updated providers to show
        session = db.get_session()
        try:
            query = """
                SELECT provider_name, provider_name_romaji
                FROM providers
                WHERE provider_name_romaji IS NOT NULL
                AND provider_name_romaji LIKE '%Clinic%'
                OR provider_name_romaji LIKE '%Hospital%'
                OR provider_name_romaji LIKE '%Dental%'
                OR provider_name_romaji LIKE '%Station%'
                LIMIT 5
            """
            
            result = session.execute(text(query))
            for row in result:
                display = get_display_name(row[0], row[1])
                logger.info(f"   {display}")
                
        finally:
            session.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())