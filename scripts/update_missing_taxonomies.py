#!/usr/bin/env python3
"""
Update missing taxonomies for providers that were published without them
This specifically targets the last 86 providers that are missing taxonomy assignments
"""

import sys
import os
import logging
import time
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.publishers.wordpress import WordPressPublisher
from sqlalchemy import text
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def force_update_taxonomies(publisher: WordPressPublisher, provider) -> bool:
    """Force update taxonomies for a provider, bypassing hash check
    
    Args:
        publisher: WordPress publisher instance  
        provider: Provider object with WordPress post ID
        
    Returns:
        Success status
    """
    if not provider.wordpress_post_id:
        logger.warning(f"⚠️  {provider.provider_name} has no WordPress post ID")
        return False
    
    try:
        # Get taxonomy term IDs
        taxonomies = publisher._get_taxonomies(provider)
        
        logger.info(f"📝 Updating {provider.provider_name} (Post ID: {provider.wordpress_post_id})")
        logger.debug(f"   Taxonomies to set: {taxonomies}")
        
        # Prepare update data with ONLY taxonomies (don't update content)
        post_data = {}
        
        # Add taxonomies if we have them
        if taxonomies:
            post_data.update(taxonomies)
            
            # Log what we're setting
            if 'location' in taxonomies:
                logger.info(f"   Setting locations: {taxonomies['location']} (City: {provider.city}, District: {provider.district})")
            if 'specialties' in taxonomies:
                logger.info(f"   Setting specialties: {taxonomies['specialties']} (From: {provider.specialties})")
        else:
            logger.warning(f"   No taxonomies found for {provider.provider_name}")
            return False
        
        # Make API request to update taxonomies
        response = requests.post(
            f"{publisher.wp_url}/wp-json/wp/v2/healthcare_provider/{provider.wordpress_post_id}",
            auth=(publisher.wp_username, publisher.wp_password),
            json=post_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Successfully updated taxonomies for {provider.provider_name}")
            return True
        else:
            logger.error(f"❌ Failed to update {provider.provider_name}: {response.status_code}")
            logger.error(f"   Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating {provider.provider_name}: {e}")
        return False


def main():
    """Main execution"""
    
    # Initialize services
    db = DatabaseManager()
    publisher = WordPressPublisher()
    
    logger.info("="*60)
    logger.info("🔧 FIXING MISSING TAXONOMIES FOR WORDPRESS POSTS")
    logger.info("="*60)
    
    # Get session
    session = db.get_session()
    
    try:
        # Query for the last 86 providers that have WordPress posts
        # These are the ones likely missing taxonomies
        query = """
            SELECT id, provider_name, city, district, specialties, 
                   wordpress_post_id, content_hash
            FROM providers 
            WHERE wordpress_post_id IS NOT NULL
            ORDER BY id DESC
            LIMIT 86
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
                    # Parse provider type from name for specialty mapping
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
            logger.info("No providers found to update")
            return
        
        # Reverse the list to process in ascending ID order
        providers.reverse()
        
        logger.info(f"Found {len(providers)} providers to update")
        logger.info(f"Provider ID range: {providers[0].id} to {providers[-1].id}")
        logger.info("-"*60)
        
        # Update each provider
        success_count = 0
        failed_count = 0
        batch_size = 10
        
        for i, provider in enumerate(providers, 1):
            logger.info(f"\n[{i}/{len(providers)}] Processing {provider.provider_name}")
            
            success = force_update_taxonomies(publisher, provider)
            
            if success:
                success_count += 1
            else:
                failed_count += 1
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.5)
            
            # Progress update every batch
            if i % batch_size == 0:
                logger.info(f"\n📊 Progress: {i}/{len(providers)} processed")
                logger.info(f"   ✅ Success: {success_count} | ❌ Failed: {failed_count}")
        
        # Final summary
        logger.info("\n" + "="*60)
        logger.info("✅ TAXONOMY UPDATE COMPLETE")
        logger.info(f"   Total processed: {len(providers)}")
        logger.info(f"   Successfully updated: {success_count}")
        if failed_count > 0:
            logger.info(f"   Failed: {failed_count}")
        logger.info("="*60)
        
        # Show WordPress admin URL
        if success_count > 0:
            logger.info("\n📌 Check results in WordPress:")
            logger.info("   https://kantanhealth.jp/wp-admin/edit.php?post_type=healthcare_provider")
            logger.info("   The Location and Specialties columns should now show values instead of '—'")
        
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