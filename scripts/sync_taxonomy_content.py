#!/usr/bin/env python3
"""
Sync Taxonomy Content with WordPress
1. Fetches all existing taxonomy pages from WordPress (combinations, locations, specialties)
2. Generates AI content for pages that don't have content
3. Saves to database
4. Publishes back to WordPress
"""

import os
import sys
import json
import time
import logging
import requests
from typing import List, Dict, Tuple, Optional
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.generate_taxonomy_content_updated import TaxonomyContentGenerator
from src.core.database import DatabaseManager
from sqlalchemy import text
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv('config/.env')


class TaxonomySyncer:
    """Syncs taxonomy content between WordPress and local database"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.generator = TaxonomyContentGenerator()
        
        # WordPress credentials
        self.wp_url = os.getenv('WORDPRESS_URL')
        self.wp_user = os.getenv('WORDPRESS_USERNAME')
        self.wp_pass = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        
        if not all([self.wp_url, self.wp_user, self.wp_pass]):
            raise ValueError("WordPress credentials not found in environment")
        
        self.existing_pages = []
        self.content_needed = []
        
    def fetch_wordpress_taxonomies(self) -> List[Dict]:
        """Fetch all taxonomy pages from WordPress"""
        
        all_pages = []
        
        # Fetch tc_combination posts (location-specialty combinations)
        logger.info("📥 Fetching taxonomy pages from WordPress...")
        
        try:
            page = 1
            per_page = 100
            
            while True:
                response = requests.get(
                    f"{self.wp_url}/wp-json/wp/v2/tc_combination",
                    auth=(self.wp_user, self.wp_pass),
                    params={'per_page': per_page, 'page': page},
                    timeout=30
                )
                
                if response.status_code == 200:
                    posts = response.json()
                    if not posts:
                        break
                    
                    for post in posts:
                        # Parse the slug to determine type and details
                        slug = post.get('slug', '')
                        title = post.get('title', {}).get('rendered', '')
                        
                        # Determine taxonomy type from slug pattern
                        if 'english-healthcare-in-' in slug:
                            # Location page
                            location = slug.replace('english-healthcare-in-', '').replace('-', ' ').title()
                            all_pages.append({
                                'wp_id': post['id'],
                                'type': 'location',
                                'location': location,
                                'specialty': None,
                                'ward': None,
                                'slug': slug,
                                'title': title
                            })
                        elif 'english-' in slug and '-in-' in slug:
                            # Combination page
                            parts = slug.replace('english-', '').split('-in-')
                            if len(parts) == 2:
                                specialty = parts[0].replace('-', ' ').title()
                                location_part = parts[1].replace('-', ' ').title()
                                
                                # Check if it's a ward (has comma in title)
                                ward = None
                                city = location_part
                                if ',' in title:
                                    # It's a ward
                                    ward = location_part
                                    # Extract city from title
                                    city_part = title.split(' in ')[-1]
                                    if ',' in city_part:
                                        ward = city_part.split(',')[0].strip()
                                        city = city_part.split(',')[1].strip()
                                
                                all_pages.append({
                                    'wp_id': post['id'],
                                    'type': 'combination',
                                    'location': city,
                                    'specialty': specialty,
                                    'ward': ward,
                                    'slug': slug,
                                    'title': title
                                })
                        elif 'english-' in slug:
                            # Specialty page
                            specialty = slug.replace('english-', '').replace('-', ' ').title()
                            all_pages.append({
                                'wp_id': post['id'],
                                'type': 'specialty',
                                'location': None,
                                'specialty': specialty,
                                'ward': None,
                                'slug': slug,
                                'title': title
                            })
                    
                    page += 1
                else:
                    break
                    
            logger.info(f"✅ Found {len(all_pages)} taxonomy pages in WordPress")
            
            # Break down by type
            combos = [p for p in all_pages if p['type'] == 'combination']
            locations = [p for p in all_pages if p['type'] == 'location']
            specialties = [p for p in all_pages if p['type'] == 'specialty']
            
            logger.info(f"   - Combinations: {len(combos)}")
            logger.info(f"   - Locations: {len(locations)}")
            logger.info(f"   - Specialties: {len(specialties)}")
            
            return all_pages
            
        except Exception as e:
            logger.error(f"Error fetching from WordPress: {e}")
            return []
    
    def check_existing_content(self, pages: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Check which pages already have content in database"""
        
        session = self.db.get_session()
        try:
            # Get all existing content
            result = session.execute(text("""
                SELECT 
                    taxonomy_type,
                    location,
                    specialty,
                    ward,
                    wordpress_post_id
                FROM taxonomy_content
            """)).fetchall()
            
            # Create lookup set
            existing = set()
            for row in result:
                key = f"{row[0]}|{row[1] or ''}|{row[2] or ''}|{row[3] or ''}"
                existing.add(key)
            
            # Categorize pages
            has_content = []
            needs_content = []
            
            for page in pages:
                key = f"{page['type']}|{page['location'] or ''}|{page['specialty'] or ''}|{page['ward'] or ''}"
                if key in existing:
                    has_content.append(page)
                else:
                    needs_content.append(page)
            
            logger.info(f"📊 Content status:")
            logger.info(f"   - Pages with content: {len(has_content)}")
            logger.info(f"   - Pages needing content: {len(needs_content)}")
            
            return has_content, needs_content
            
        finally:
            session.close()
    
    def generate_content_batch(self, pages: List[Dict]) -> List[Dict]:
        """Generate content for a batch of pages"""
        
        # Convert to generator format
        items = []
        for page in pages:
            if page['type'] == 'combination':
                items.append((
                    'combination',
                    page['location'],
                    page['specialty'],
                    page['ward'],
                    0  # Provider count - will be updated later
                ))
            elif page['type'] == 'location':
                items.append((
                    'location',
                    page['location'],
                    None,
                    page['ward'],
                    0
                ))
            else:  # specialty
                items.append((
                    'specialty',
                    None,
                    page['specialty'],
                    None,
                    0
                ))
        
        # Generate content
        try:
            content_batch = self.generator.generate_mega_batch(items, len(items))
            
            # Add WordPress post IDs to content
            for i, content in enumerate(content_batch):
                content.wordpress_post_id = pages[i]['wp_id']
            
            return content_batch
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return []
    
    def save_content_with_wp_id(self, content_list: List):
        """Save content to database with WordPress post IDs"""
        
        session = self.db.get_session()
        try:
            for content in content_list:
                # Check if already exists
                existing = session.execute(text("""
                    SELECT id FROM taxonomy_content
                    WHERE taxonomy_type = :type
                    AND COALESCE(location, '') = COALESCE(:location, '')
                    AND COALESCE(specialty, '') = COALESCE(:specialty, '')
                    AND COALESCE(ward, '') = COALESCE(:ward, '')
                """), {
                    'type': content.taxonomy_type,
                    'location': content.location,
                    'specialty': content.specialty,
                    'ward': content.ward
                }).fetchone()
                
                if existing:
                    # Update existing
                    session.execute(text("""
                        UPDATE taxonomy_content
                        SET title = :title,
                            meta_description = :meta,
                            brief_intro = :brief,
                            full_description = :full,
                            wordpress_post_id = :wp_id,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                    """), {
                        'title': content.title,
                        'meta': content.meta_description,
                        'brief': content.brief_intro,
                        'full': content.full_description,
                        'wp_id': getattr(content, 'wordpress_post_id', None),
                        'id': existing[0]
                    })
                else:
                    # Insert new
                    session.execute(text("""
                        INSERT INTO taxonomy_content
                        (taxonomy_type, location, specialty, ward, title, meta_description,
                         brief_intro, full_description, provider_count, priority_tier, wordpress_post_id)
                        VALUES
                        (:type, :location, :specialty, :ward, :title, :meta,
                         :brief, :full, :count, :tier, :wp_id)
                    """), {
                        'type': content.taxonomy_type,
                        'location': content.location,
                        'specialty': content.specialty,
                        'ward': content.ward,
                        'title': content.title,
                        'meta': content.meta_description,
                        'brief': content.brief_intro,
                        'full': content.full_description,
                        'count': content.provider_count,
                        'tier': content.priority_tier,
                        'wp_id': getattr(content, 'wordpress_post_id', None)
                    })
            
            session.commit()
            logger.info(f"✅ Saved {len(content_list)} content items to database")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving content: {e}")
        finally:
            session.close()
    
    def sync_all(self, batch_size: int = 5):
        """Main sync process"""
        
        logger.info("=" * 60)
        logger.info("TAXONOMY CONTENT SYNC")
        logger.info("=" * 60)
        
        # Step 1: Fetch all WordPress taxonomy pages
        all_pages = self.fetch_wordpress_taxonomies()
        if not all_pages:
            logger.error("No pages found in WordPress!")
            return
        
        # Step 2: Check what content exists
        has_content, needs_content = self.check_existing_content(all_pages)
        
        if not needs_content:
            logger.info("✅ All pages already have content!")
            return
        
        # Step 3: Generate content for pages that need it
        logger.info(f"\n📝 Generating content for {len(needs_content)} pages...")
        
        total_generated = 0
        
        for i in range(0, len(needs_content), batch_size):
            batch = needs_content[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(needs_content) + batch_size - 1) // batch_size
            
            logger.info(f"\nBatch {batch_num}/{total_batches}:")
            
            # Show what's in this batch
            for page in batch:
                if page['type'] == 'combination':
                    loc = f"{page['ward']}, {page['location']}" if page['ward'] else page['location']
                    logger.info(f"   - {page['specialty']} in {loc}")
                elif page['type'] == 'location':
                    logger.info(f"   - Healthcare in {page['location']}")
                else:
                    logger.info(f"   - {page['specialty']} Services")
            
            # Generate content
            content_batch = self.generate_content_batch(batch)
            if content_batch:
                self.save_content_with_wp_id(content_batch)
                total_generated += len(content_batch)
            
            # Rate limiting
            if i + batch_size < len(needs_content):
                time.sleep(2)
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ SYNC COMPLETE")
        logger.info(f"   Total WordPress pages: {len(all_pages)}")
        logger.info(f"   Already had content: {len(has_content)}")
        logger.info(f"   Generated new content: {total_generated}")
        logger.info("=" * 60)
        logger.info("\nNext step: Run publish_taxonomy_content.py to update WordPress")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync taxonomy content with WordPress')
    parser.add_argument('--batch-size', type=int, default=5,
                       help='Number of items per API call (default 5)')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check status without generating')
    
    args = parser.parse_args()
    
    syncer = TaxonomySyncer()
    
    if args.check_only:
        # Just check status
        all_pages = syncer.fetch_wordpress_taxonomies()
        has_content, needs_content = syncer.check_existing_content(all_pages)
        
        logger.info("\n📊 DETAILED STATUS:")
        
        # Show some examples of what needs content
        if needs_content:
            logger.info("\nExamples of pages needing content:")
            for page in needs_content[:10]:
                logger.info(f"   - {page['title']} ({page['slug']})")
            if len(needs_content) > 10:
                logger.info(f"   ... and {len(needs_content) - 10} more")
    else:
        # Run full sync
        syncer.sync_all(batch_size=args.batch_size)


if __name__ == "__main__":
    main()