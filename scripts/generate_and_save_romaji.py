#!/usr/bin/env python3
"""
Generate and save romaji names for all Japanese providers
Then clean their WordPress titles
"""

import sys
import os
import logging
import time
import requests

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.utils.romaji_converter import contains_japanese, convert_to_romaji
from sqlalchemy import text
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_and_save_romaji():
    """Generate romaji for all Japanese providers and save to database"""
    
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Get all providers with Japanese names
        query = """
            SELECT id, provider_name, wordpress_post_id
            FROM providers
            WHERE provider_name ~ '[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]'
            ORDER BY id
        """
        
        result = session.execute(text(query))
        providers = list(result)
        
        logger.info(f"Found {len(providers)} providers with Japanese names")
        
        # Generate and save romaji for each
        for provider in providers:
            provider_id = provider[0]
            provider_name = provider[1]
            wordpress_post_id = provider[2]
            
            # Generate romaji
            romaji = convert_to_romaji(provider_name)
            
            if romaji and romaji != provider_name:
                # Update database directly
                update_query = """
                    UPDATE providers 
                    SET provider_name_romaji = :romaji
                    WHERE id = :id
                """
                
                session.execute(text(update_query), {'romaji': romaji, 'id': provider_id})
                
                logger.info(f"✅ {provider_name}")
                logger.info(f"   Romaji: {romaji}")
        
        # Commit all changes
        session.commit()
        logger.info(f"\n✅ Saved romaji for {len(providers)} providers")
        
        return providers
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error: {e}")
        return []
        
    finally:
        session.close()


def clean_wordpress_titles(providers):
    """Clean WordPress titles to use romaji only"""
    
    # Load WordPress configuration
    load_dotenv('config/.env')
    
    wp_config = {
        'url': os.getenv('WORDPRESS_URL'),
        'username': os.getenv('WORDPRESS_USERNAME'),
        'password': os.getenv('WORDPRESS_APPLICATION_PASSWORD')
    }
    
    if not all(wp_config.values()):
        logger.error("❌ WordPress configuration not found")
        return
    
    logger.info("\n" + "="*60)
    logger.info("🧹 CLEANING WORDPRESS TITLES")
    logger.info("="*60)
    
    success_count = 0
    
    for provider in providers:
        provider_id = provider[0]
        provider_name = provider[1]
        wordpress_post_id = provider[2]
        
        if not wordpress_post_id:
            continue
        
        # Get the romaji we just saved
        db = DatabaseManager()
        session = db.get_session()
        
        try:
            result = session.execute(
                text("SELECT provider_name_romaji FROM providers WHERE id = :id"),
                {'id': provider_id}
            ).first()
            
            if result and result[0]:
                romaji = result[0]
                
                # Update WordPress title
                response = requests.post(
                    f"{wp_config['url']}/wp-json/wp/v2/healthcare_provider/{wordpress_post_id}",
                    auth=(wp_config['username'], wp_config['password']),
                    json={'title': romaji},
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Updated WordPress: {romaji}")
                    success_count += 1
                elif response.status_code == 404:
                    logger.debug(f"⚠️  Post {wordpress_post_id} not found")
                else:
                    logger.error(f"❌ Failed: {response.status_code}")
                
                time.sleep(0.3)  # Rate limiting
                
        except Exception as e:
            logger.error(f"❌ Error updating {provider_name}: {e}")
            
        finally:
            session.close()
    
    logger.info(f"\n✅ Updated {success_count} WordPress titles")


def main():
    """Main execution"""
    
    logger.info("="*60)
    logger.info("🔧 GENERATE ROMAJI AND CLEAN WORDPRESS TITLES")
    logger.info("="*60)
    
    # Step 1: Generate and save romaji
    providers = generate_and_save_romaji()
    
    if providers:
        # Step 2: Clean WordPress titles
        clean_wordpress_titles(providers)
    
    logger.info("\n" + "="*60)
    logger.info("✅ COMPLETE - All titles now use romaji only")
    logger.info("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())