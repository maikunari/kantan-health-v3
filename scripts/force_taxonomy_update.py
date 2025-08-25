#!/usr/bin/env python3
"""
Force update all WordPress posts with proper taxonomies
This script updates ALL providers that have WordPress posts with their location and specialty taxonomies
"""

import sys
import os
import logging
import argparse
from typing import List, Dict, Any
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.publishers.wordpress import WordPressPublisher
import requests
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def update_taxonomies_batch(publisher: WordPressPublisher, providers: List, dry_run: bool = False) -> Dict[str, int]:
    """Update taxonomies for a batch of providers
    
    Args:
        publisher: WordPress publisher instance
        providers: List of provider objects
        dry_run: If True, show what would be updated without making changes
        
    Returns:
        Dictionary with success/failed counts
    """
    results = {"success": 0, "failed": 0, "skipped": 0}
    
    for provider in providers:
        if not provider.wordpress_post_id:
            logger.warning(f"⚠️  {provider.provider_name} has no WordPress post ID")
            results["skipped"] += 1
            continue
        
        try:
            # Get taxonomy term IDs
            taxonomies = publisher._get_taxonomies(provider)
            
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
                
                results["success"] += 1
                continue
            
            # Prepare minimal update data with just taxonomies
            update_data = taxonomies
            
            # Make API request to update only taxonomies
            response = requests.post(
                f"{publisher.wp_url}/wp-json/wp/v2/healthcare_provider/{provider.wordpress_post_id}",
                auth=(publisher.wp_username, publisher.wp_password),
                json=update_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Updated {provider.provider_name}")
                
                # Log what was set
                if 'location' in taxonomies:
                    logger.info(f"   Locations: {provider.city}, {provider.district}")
                if 'specialties' in taxonomies:
                    logger.info(f"   Specialties: {provider.specialties}")
                
                results["success"] += 1
            else:
                logger.error(f"❌ Failed {provider.provider_name}: {response.status_code}")
                logger.error(f"   Response: {response.text[:200]}")
                results["failed"] += 1
                
        except Exception as e:
            logger.error(f"❌ Error updating {provider.provider_name}: {e}")
            results["failed"] += 1
        
        # Small delay to avoid overwhelming the API
        if not dry_run:
            time.sleep(0.5)
    
    return results


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Force update all WordPress posts with taxonomies')
    parser.add_argument('--batch-size', type=int, default=10, 
                       help='Number of providers to update per batch (default: 10)')
    parser.add_argument('--limit', type=int, 
                       help='Total number of providers to update (default: all)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be updated without making changes')
    parser.add_argument('--provider-ids', type=str, 
                       help='Comma-separated list of specific provider IDs to update')
    parser.add_argument('--city', type=str,
                       help='Only update providers in specific city')
    parser.add_argument('--skip-existing', action='store_true',
                       help='Skip providers that already have taxonomies')
    
    args = parser.parse_args()
    
    # Initialize services
    db = DatabaseManager()
    publisher = WordPressPublisher()
    
    # Get providers to update
    session = db.get_session()
    
    try:
        # Build query
        query = """
            SELECT id, provider_name, city, district, specialties, 
                   wordpress_post_id, content_hash
            FROM providers 
            WHERE wordpress_post_id IS NOT NULL
        """
        
        # Add filters
        conditions = []
        params = {}
        
        if args.provider_ids:
            provider_ids = [int(pid.strip()) for pid in args.provider_ids.split(',')]
            conditions.append("id = ANY(:provider_ids)")
            params['provider_ids'] = provider_ids
        
        if args.city:
            conditions.append("LOWER(city) = LOWER(:city)")
            params['city'] = args.city
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        # Add ordering
        query += " ORDER BY id"
        
        # Add limit if specified
        if args.limit:
            query += f" LIMIT {args.limit}"
        
        # Execute query
        result = session.execute(text(query), params)
        
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
        
        # Display summary
        logger.info("="*60)
        logger.info(f"{'🔍 DRY RUN MODE' if args.dry_run else '🚀 FORCE TAXONOMY UPDATE'}")
        logger.info(f"Found {len(providers)} providers with WordPress posts")
        logger.info(f"Batch size: {args.batch_size}")
        logger.info("="*60)
        
        # Process in batches
        total_results = {"success": 0, "failed": 0, "skipped": 0}
        batch_num = 0
        
        for i in range(0, len(providers), args.batch_size):
            batch = providers[i:i+args.batch_size]
            batch_num += 1
            
            logger.info(f"\n📦 Processing batch {batch_num} ({len(batch)} providers)...")
            logger.info("-"*40)
            
            batch_results = update_taxonomies_batch(publisher, batch, args.dry_run)
            
            # Update totals
            for key in total_results:
                total_results[key] += batch_results[key]
            
            # Show batch summary
            logger.info(f"Batch {batch_num} complete: "
                       f"✅ {batch_results['success']} | "
                       f"❌ {batch_results['failed']} | "
                       f"⏭️  {batch_results['skipped']}")
        
        # Final summary
        logger.info("\n" + "="*60)
        if args.dry_run:
            logger.info("🔍 DRY RUN COMPLETE")
            logger.info(f"   Would update: {total_results['success']} providers")
        else:
            logger.info("✅ TAXONOMY UPDATE COMPLETE")
            logger.info(f"   Successfully updated: {total_results['success']}")
            if total_results['failed'] > 0:
                logger.info(f"   Failed: {total_results['failed']}")
            if total_results['skipped'] > 0:
                logger.info(f"   Skipped: {total_results['skipped']}")
        
        logger.info("="*60)
        
        # Show sample WordPress admin URLs
        if not args.dry_run and total_results['success'] > 0:
            logger.info("\n📌 Check results in WordPress:")
            logger.info("   https://kantanhealth.jp/wp-admin/edit.php?post_type=healthcare_provider")
            logger.info("   Filter by Location or Specialty to see the taxonomy assignments")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
        
    finally:
        session.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())