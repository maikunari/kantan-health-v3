#!/usr/bin/env python3
"""
Force update WordPress taxonomies for existing posts
This script updates the Location and Specialty taxonomies for providers that already have WordPress posts
"""

import sys
import os
import logging
import argparse
from typing import List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.publishers.wordpress import WordPressPublisher
import requests

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def update_taxonomies_only(publisher: WordPressPublisher, provider, dry_run: bool = False):
    """Update only the taxonomies for a WordPress post
    
    Args:
        publisher: WordPress publisher instance
        provider: Provider object with WordPress post ID
        dry_run: If True, show what would be updated without making changes
        
    Returns:
        Success status
    """
    if not provider.wordpress_post_id:
        logger.warning(f"⚠️  {provider.provider_name} has no WordPress post ID")
        return False
    
    try:
        # Debug: Show provider data
        logger.info(f"🔍 Processing {provider.provider_name}")
        logger.info(f"   City: {provider.city}")
        logger.info(f"   District: {provider.district}")
        logger.info(f"   Specialties: {provider.specialties}")
        
        # Get taxonomy term IDs
        taxonomies = publisher._get_taxonomies(provider)
        logger.info(f"   Retrieved taxonomies: {taxonomies}")
        
        if dry_run:
            logger.info(f"🔍 DRY RUN - Would update {provider.provider_name} (Post ID: {provider.wordpress_post_id})")
            
            # Show what taxonomies would be set
            if 'location' in taxonomies:
                location_ids = taxonomies['location']
                logger.info(f"   Locations: {location_ids} - City: {provider.city}, District: {provider.district}")
            else:
                logger.info(f"   Locations: None")
            
            if 'specialties' in taxonomies:
                specialty_ids = taxonomies['specialties']
                specialties_str = provider.specialties if provider.specialties else "parsed from name"
                logger.info(f"   Specialties: {specialty_ids} - {specialties_str}")
            else:
                logger.info(f"   Specialties: None")
            
            return True
        
        # Prepare minimal update data with just taxonomies
        update_data = taxonomies
        
        # Make API request to update only taxonomies
        response = requests.post(
            f"{publisher.wp_url}/wp-json/wp/v2/healthcare_provider/{provider.wordpress_post_id}",
            auth=(publisher.wp_username, publisher.wp_password),
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Updated taxonomies for {provider.provider_name}")
            
            # Log what was set
            if 'location' in taxonomies:
                logger.info(f"   Set locations: {provider.city}, {provider.district}")
            if 'specialties' in taxonomies:
                logger.info(f"   Set specialties from: {provider.specialties}")
            
            return True
        else:
            logger.error(f"❌ Failed to update {provider.provider_name}: {response.status_code}")
            logger.error(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating {provider.provider_name}: {e}")
        return False


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Update WordPress taxonomies for existing posts')
    parser.add_argument('--limit', type=int, default=5, help='Number of providers to update (default: 5)')
    parser.add_argument('--all', action='store_true', help='Update all providers with WordPress posts')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')
    parser.add_argument('--provider-ids', type=str, help='Comma-separated list of provider IDs to update')
    
    args = parser.parse_args()
    
    # Initialize services
    db = DatabaseManager()
    publisher = WordPressPublisher()
    
    # Get providers to update
    session = db.get_session()
    
    try:
        if args.provider_ids:
            # Update specific providers
            provider_ids = [int(pid.strip()) for pid in args.provider_ids.split(',')]
            providers = []
            for pid in provider_ids:
                provider = db.get_provider_by_id(pid)
                if provider and provider.wordpress_post_id:
                    providers.append(provider)
                else:
                    logger.warning(f"Provider {pid} not found or has no WordPress post")
        else:
            # Get providers with WordPress posts using raw SQL to avoid ORM issues
            from sqlalchemy import text
            
            limit_clause = "" if args.all else f"LIMIT {args.limit}"
            
            result = session.execute(text(f"""
                SELECT id, provider_name, city, district, specialties, 
                       wordpress_post_id, content_hash
                FROM providers 
                WHERE wordpress_post_id IS NOT NULL
                {limit_clause}
            """))
            
            # Convert to provider-like objects
            providers = []
            for row in result:
                # Create a simple object to hold the data
                class ProviderData:
                    def __init__(self, row):
                        self.id = row[0]
                        self.provider_name = row[1]
                        self.city = row[2]
                        self.district = row[3]
                        self.specialties = row[4]
                        self.wordpress_post_id = row[5]
                        self.content_hash = row[6]
                
                providers.append(ProviderData(row))
        
        if not providers:
            logger.info("No providers found to update")
            return
        
        logger.info(f"{'🔍 DRY RUN MODE' if args.dry_run else '🚀 UPDATING'} {len(providers)} providers")
        logger.info("="*60)
        
        # Update each provider
        success_count = 0
        failed_count = 0
        
        for provider in providers:
            success = update_taxonomies_only(publisher, provider, args.dry_run)
            if success:
                success_count += 1
            else:
                failed_count += 1
        
        # Summary
        logger.info("="*60)
        if args.dry_run:
            logger.info(f"🔍 DRY RUN COMPLETE")
            logger.info(f"   Would update: {success_count} providers")
        else:
            logger.info(f"✅ TAXONOMY UPDATE COMPLETE")
            logger.info(f"   Successfully updated: {success_count}")
            if failed_count > 0:
                logger.info(f"   Failed: {failed_count}")
        
    finally:
        session.close()


if __name__ == "__main__":
    main()