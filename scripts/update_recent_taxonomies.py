#!/usr/bin/env python3
"""
Update taxonomies for recently published providers (post IDs 4000+)
These are the ones most likely to be missing taxonomies
"""

import sys
import os
import logging
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.publishers.wordpress import WordPressPublisher
from sqlalchemy import text
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def update_provider_taxonomies(publisher: WordPressPublisher, provider) -> bool:
    """Update taxonomies for a single provider"""
    
    try:
        # Get taxonomy term IDs
        taxonomies = publisher._get_taxonomies(provider)
        
        if not taxonomies:
            logger.warning(f"   No taxonomies found for {provider.provider_name}")
            return False
        
        # Make API request to update taxonomies
        response = requests.post(
            f"{publisher.wp_url}/wp-json/wp/v2/healthcare_provider/{provider.wordpress_post_id}",
            auth=(publisher.wp_username, publisher.wp_password),
            json=taxonomies,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Updated {provider.provider_name}")
            if 'location' in taxonomies:
                logger.info(f"   Locations: {provider.city}, {provider.district}")
            if 'specialties' in taxonomies:
                logger.info(f"   Specialties: {provider.specialties}")
            return True
        elif response.status_code == 404:
            logger.warning(f"⚠️  Post {provider.wordpress_post_id} not found for {provider.provider_name}")
            return False
        else:
            logger.error(f"❌ Failed {provider.provider_name}: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


def main():
    """Main execution"""
    
    # Initialize services
    db = DatabaseManager()
    publisher = WordPressPublisher()
    
    logger.info("="*60)
    logger.info("🔧 UPDATING TAXONOMIES FOR RECENT WORDPRESS POSTS")
    logger.info("="*60)
    
    # Get session
    session = db.get_session()
    
    try:
        # Query for providers with WordPress post IDs >= 4000
        # These are the most recent ones likely missing taxonomies
        query = """
            SELECT id, provider_name, city, district, specialties, 
                   wordpress_post_id, content_hash
            FROM providers 
            WHERE wordpress_post_id >= 4000
            ORDER BY wordpress_post_id
        """
        
        result = session.execute(text(query))
        
        # Convert to provider-like objects
        providers = []
        for row in result:
            class ProviderData:
                def __init__(self, row):
                    self.id = row[0]
                    self.provider_name = row[1]
                    self.city = row[2]
                    self.district = row[3]
                    self.specialties = row[4]
                    self.wordpress_post_id = row[5]
                    self.content_hash = row[6]
                    # Parse provider type from name
                    name_lower = row[1].lower()
                    if 'hospital' in name_lower:
                        self.provider_type = 'hospital'
                    elif 'clinic' in name_lower:
                        self.provider_type = 'clinic'
                    elif 'pharmacy' in name_lower:
                        self.provider_type = 'pharmacy'
                    elif 'dental' in name_lower or 'dentist' in name_lower:
                        self.provider_type = 'dentist'
                    else:
                        self.provider_type = None
            
            providers.append(ProviderData(row))
        
        if not providers:
            logger.info("No recent providers found to update")
            return
        
        logger.info(f"Found {len(providers)} recent providers (Post IDs 4000+)")
        logger.info(f"WordPress Post ID range: {providers[0].wordpress_post_id} to {providers[-1].wordpress_post_id}")
        logger.info("-"*60)
        
        # Update each provider
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for i, provider in enumerate(providers, 1):
            logger.info(f"\n[{i}/{len(providers)}] {provider.provider_name} (Post {provider.wordpress_post_id})")
            
            success = update_provider_taxonomies(publisher, provider)
            
            if success:
                success_count += 1
            elif success is False:
                failed_count += 1
            else:
                skipped_count += 1
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.3)
            
            # Progress update every 10
            if i % 10 == 0:
                logger.info(f"\n📊 Progress: {i}/{len(providers)}")
                logger.info(f"   ✅ Success: {success_count} | ❌ Failed: {failed_count} | ⚠️  Skipped: {skipped_count}")
        
        # Final summary
        logger.info("\n" + "="*60)
        logger.info("✅ TAXONOMY UPDATE COMPLETE")
        logger.info(f"   Total processed: {len(providers)}")
        logger.info(f"   Successfully updated: {success_count}")
        if failed_count > 0:
            logger.info(f"   Failed/Not found: {failed_count}")
        if skipped_count > 0:
            logger.info(f"   Skipped: {skipped_count}")
        logger.info("="*60)
        
        # Show WordPress admin URL
        if success_count > 0:
            logger.info("\n📌 Check results in WordPress:")
            logger.info("   https://kantanhealth.jp/wp-admin/edit.php?post_type=healthcare_provider")
            logger.info("   The Location and Specialties columns should now show values")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        session.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())