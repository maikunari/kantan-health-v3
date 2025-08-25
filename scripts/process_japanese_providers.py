#!/usr/bin/env python3
"""
Process all Japanese providers: generate romaji and update WordPress titles
This is the unified script for handling Japanese provider names
"""

import sys
import os
import logging
import time
import requests
from typing import List, Dict, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.utils.romaji_converter import contains_japanese, convert_to_romaji
from sqlalchemy import text
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class JapaneseProviderProcessor:
    """Process Japanese provider names for romaji and WordPress"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.wp_config = self._load_wordpress_config()
        self.stats = {
            'total_japanese': 0,
            'romaji_generated': 0,
            'romaji_updated': 0,
            'wordpress_updated': 0,
            'errors': 0
        }
    
    def _load_wordpress_config(self) -> Dict:
        """Load WordPress configuration from environment"""
        load_dotenv('config/.env')
        
        config = {
            'url': os.getenv('WORDPRESS_URL'),
            'username': os.getenv('WORDPRESS_USERNAME'),
            'password': os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        }
        
        if not all(config.values()):
            logger.warning("WordPress configuration incomplete")
        
        return config
    
    def get_japanese_providers(self) -> List:
        """Get all providers with Japanese names"""
        session = self.db.get_session()
        
        try:
            # Get providers with Japanese names
            query = """
                SELECT id, provider_name, provider_name_romaji, wordpress_post_id
                FROM providers
                WHERE provider_name ~ '[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]'
                ORDER BY id
            """
            
            result = session.execute(text(query))
            providers = []
            
            for row in result:
                providers.append({
                    'id': row[0],
                    'provider_name': row[1],
                    'provider_name_romaji': row[2],
                    'wordpress_post_id': row[3]
                })
            
            return providers
            
        finally:
            session.close()
    
    def generate_romaji(self, provider: Dict) -> Optional[str]:
        """Generate romaji for a provider"""
        try:
            if not contains_japanese(provider['provider_name']):
                return None
            
            romaji = convert_to_romaji(provider['provider_name'])
            
            # Only return if different from original and not empty
            if romaji and romaji != provider['provider_name']:
                return romaji
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating romaji for {provider['provider_name']}: {e}")
            return None
    
    def update_database_romaji(self, provider_id: int, romaji: str) -> bool:
        """Update romaji in database"""
        session = self.db.get_session()
        
        try:
            update_query = """
                UPDATE providers 
                SET provider_name_romaji = :romaji
                WHERE id = :id
            """
            
            session.execute(text(update_query), {'romaji': romaji, 'id': provider_id})
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating database: {e}")
            return False
            
        finally:
            session.close()
    
    def update_wordpress_title(self, wordpress_post_id: int, title: str) -> bool:
        """Update WordPress post title"""
        if not all(self.wp_config.values()):
            return False
        
        try:
            response = requests.post(
                f"{self.wp_config['url']}/wp-json/wp/v2/healthcare_provider/{wordpress_post_id}",
                auth=(self.wp_config['username'], self.wp_config['password']),
                json={'title': title},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                return True
            elif response.status_code == 404:
                logger.debug(f"WordPress post {wordpress_post_id} not found")
            else:
                logger.error(f"WordPress update failed: {response.status_code}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating WordPress: {e}")
            return False
    
    def process_provider(self, provider: Dict) -> Dict:
        """Process a single provider"""
        result = {
            'romaji_generated': False,
            'romaji_updated': False,
            'wordpress_updated': False
        }
        
        # Check if romaji needs to be generated
        if not provider['provider_name_romaji']:
            romaji = self.generate_romaji(provider)
            
            if romaji:
                result['romaji_generated'] = True
                
                # Update database
                if self.update_database_romaji(provider['id'], romaji):
                    result['romaji_updated'] = True
                    provider['provider_name_romaji'] = romaji
                    logger.info(f"✅ Generated romaji: {provider['provider_name']} → {romaji}")
        
        # Update WordPress if we have romaji and a post ID
        if provider['provider_name_romaji'] and provider['wordpress_post_id']:
            if self.update_wordpress_title(provider['wordpress_post_id'], provider['provider_name_romaji']):
                result['wordpress_updated'] = True
                logger.info(f"✅ Updated WordPress: {provider['provider_name_romaji']}")
        
        return result
    
    def process_all(self, limit: Optional[int] = None):
        """Process all Japanese providers"""
        logger.info("="*60)
        logger.info("🔧 PROCESSING JAPANESE PROVIDERS")
        logger.info("="*60)
        
        # Get all Japanese providers
        providers = self.get_japanese_providers()
        
        if limit:
            providers = providers[:limit]
        
        self.stats['total_japanese'] = len(providers)
        
        logger.info(f"Found {len(providers)} Japanese providers")
        
        # Show preview
        logger.info("\n📋 Preview:")
        for provider in providers[:3]:
            if provider['provider_name_romaji']:
                logger.info(f"  {provider['provider_name']} → {provider['provider_name_romaji']}")
            else:
                romaji = self.generate_romaji(provider)
                if romaji:
                    logger.info(f"  {provider['provider_name']} → {romaji} (needs generation)")
        
        logger.info("\n" + "-"*60)
        logger.info("Processing providers...\n")
        
        # Process each provider
        for i, provider in enumerate(providers, 1):
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(providers)}")
            
            try:
                result = self.process_provider(provider)
                
                if result['romaji_generated']:
                    self.stats['romaji_generated'] += 1
                if result['romaji_updated']:
                    self.stats['romaji_updated'] += 1
                if result['wordpress_updated']:
                    self.stats['wordpress_updated'] += 1
                
                # Rate limiting
                if result['wordpress_updated']:
                    time.sleep(0.3)
                    
            except Exception as e:
                logger.error(f"Error processing {provider['provider_name']}: {e}")
                self.stats['errors'] += 1
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print processing summary"""
        logger.info("\n" + "="*60)
        logger.info("✅ PROCESSING COMPLETE")
        logger.info(f"   Total Japanese providers: {self.stats['total_japanese']}")
        logger.info(f"   Romaji generated: {self.stats['romaji_generated']}")
        logger.info(f"   Database updated: {self.stats['romaji_updated']}")
        logger.info(f"   WordPress updated: {self.stats['wordpress_updated']}")
        if self.stats['errors'] > 0:
            logger.info(f"   Errors: {self.stats['errors']}")
        logger.info("="*60)
        
        # Show examples
        if self.stats['romaji_updated'] > 0:
            logger.info("\n📌 Sample results:")
            session = self.db.get_session()
            try:
                query = """
                    SELECT provider_name, provider_name_romaji
                    FROM providers
                    WHERE provider_name_romaji IS NOT NULL
                    AND (
                        provider_name_romaji LIKE '%Clinic%'
                        OR provider_name_romaji LIKE '%Hospital%'
                        OR provider_name_romaji LIKE '%Dental%'
                    )
                    LIMIT 5
                """
                
                result = session.execute(text(query))
                for row in result:
                    logger.info(f"   {row[0]} → {row[1]}")
                    
            finally:
                session.close()


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process Japanese provider names')
    parser.add_argument('--limit', type=int, help='Limit number of providers to process')
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        # Just show preview
        processor = JapaneseProviderProcessor()
        providers = processor.get_japanese_providers()
        
        if args.limit:
            providers = providers[:args.limit]
        
        logger.info(f"\nWould process {len(providers)} Japanese providers:")
        for i, provider in enumerate(providers[:10], 1):
            romaji = processor.generate_romaji(provider)
            if romaji:
                logger.info(f"{i}. {provider['provider_name']} → {romaji}")
        
        if len(providers) > 10:
            logger.info(f"... and {len(providers) - 10} more")
        
        return 0
    
    # Run processing
    processor = JapaneseProviderProcessor()
    processor.process_all(limit=args.limit)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())