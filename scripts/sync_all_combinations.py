#!/usr/bin/env python3
"""
Comprehensive sync for all 477 tc_combination pages
1. Fetch all from WordPress
2. Check what's in database
3. Generate missing content
4. Update all WordPress posts with content
"""

import os
import sys
import time
import logging
import requests
from typing import List, Dict, Set
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.generate_taxonomy_content_updated import TaxonomyContentGenerator
from src.core.database import DatabaseManager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv('config/.env')


class CombinationSyncer:
    def __init__(self):
        self.db = DatabaseManager()
        self.generator = TaxonomyContentGenerator()
        
        self.wp_url = os.getenv('WORDPRESS_URL')
        self.wp_user = os.getenv('WORDPRESS_USERNAME')
        self.wp_pass = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        
        if not all([self.wp_url, self.wp_user, self.wp_pass]):
            raise ValueError("WordPress credentials not found")
    
    def fetch_all_wordpress_combinations(self) -> List[Dict]:
        """Fetch all tc_combination posts from WordPress"""
        
        all_posts = []
        page = 1
        per_page = 100
        
        logger.info("📥 Fetching all tc_combination posts from WordPress...")
        
        while True:
            try:
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
                        # Parse the slug to extract location/specialty
                        slug = post['slug']
                        parsed = self.parse_slug(slug)
                        
                        # Check if content exists
                        acf = post.get('acf', {})
                        has_content = bool(acf.get('brief_intro')) and bool(acf.get('full_description'))
                        
                        all_posts.append({
                            'wp_id': post['id'],
                            'slug': slug,
                            'title': post['title']['rendered'],
                            'location': parsed['location'],
                            'specialty': parsed['specialty'],
                            'ward': parsed['ward'],
                            'has_content': has_content,
                            'current_brief': acf.get('brief_intro', ''),
                            'current_full': acf.get('full_description', '')
                        })
                    
                    page += 1
                else:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching WordPress posts: {e}")
                break
        
        logger.info(f"✅ Found {len(all_posts)} tc_combination posts")
        return all_posts
    
    def parse_slug(self, slug: str) -> Dict:
        """Parse WordPress slug to extract location, specialty, ward"""
        
        result = {'location': None, 'specialty': None, 'ward': None}
        
        # Remove 'english-' prefix and split by '-in-'
        if 'english-' in slug and '-in-' in slug:
            parts = slug.replace('english-', '').split('-in-')
            if len(parts) == 2:
                # Parse specialty
                specialty_part = parts[0].replace('-', ' ').replace('_', ' ')
                
                # Fix common specialty names
                specialty_map = {
                    'general medicine': 'General Medicine',
                    'internal medicine': 'Internal Medicine',
                    'ent ear nose throat': 'ENT (Ear, Nose & Throat)',
                    'dentist': 'Dentist',
                    'dentistry': 'Dentist',
                    'gynecology': 'Gynecology',
                    'pediatrics': 'Pediatrics',
                    'dermatology': 'Dermatology',
                    'ophthalmology': 'Ophthalmology',
                    'cardiology': 'Cardiology',
                    'orthopedics': 'Orthopedics'
                }
                
                specialty_lower = specialty_part.lower()
                result['specialty'] = specialty_map.get(specialty_lower, specialty_part.title())
                
                # Parse location
                location_part = parts[1].replace('-', ' ').title()
                
                # Check if it's a Tokyo ward
                tokyo_wards = ['Shibuya', 'Shinjuku', 'Minato', 'Chiyoda', 'Chuo', 
                             'Meguro', 'Setagaya', 'Ota', 'Bunkyo', 'Taito', 
                             'Sumida', 'Koto', 'Shinagawa', 'Nakano', 'Suginami',
                             'Toshima', 'Kita', 'Arakawa', 'Itabashi', 'Nerima',
                             'Adachi', 'Katsushika', 'Edogawa']
                
                if location_part in tokyo_wards:
                    result['ward'] = location_part
                    result['location'] = 'Tokyo'
                else:
                    result['location'] = location_part
        
        return result
    
    def get_database_content(self) -> Dict:
        """Get all content from database"""
        
        session = self.db.get_session()
        try:
            result = session.execute(text("""
                SELECT 
                    location,
                    specialty,
                    ward,
                    title,
                    meta_description,
                    brief_intro,
                    full_description,
                    wordpress_post_id
                FROM taxonomy_content
            """)).fetchall()
            
            db_content = {}
            for row in result:
                # Create key from location/specialty/ward
                key = f"{row[0]}|{row[1]}|{row[2] or ''}"
                db_content[key] = {
                    'title': row[3],
                    'meta_description': row[4],
                    'brief_intro': row[5],
                    'full_description': row[6],
                    'wordpress_post_id': row[7]
                }
            
            return db_content
            
        finally:
            session.close()
    
    def generate_missing_content(self, wp_posts: List[Dict], db_content: Dict) -> List[Dict]:
        """Generate content for posts that don't have it"""
        
        missing = []
        
        for post in wp_posts:
            if not post['location'] or not post['specialty']:
                logger.warning(f"Skipping post {post['wp_id']} - couldn't parse: {post['slug']}")
                continue
            
            # Check if content exists in database
            key = f"{post['location']}|{post['specialty']}|{post['ward'] or ''}"
            
            if key not in db_content or not db_content[key].get('brief_intro'):
                missing.append(post)
        
        logger.info(f"📝 Need to generate content for {len(missing)} combinations")
        
        if not missing:
            return []
        
        generated = []
        batch_size = 5
        
        for i in range(0, len(missing), batch_size):
            batch = missing[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(missing) + batch_size - 1) // batch_size
            
            logger.info(f"\nBatch {batch_num}/{total_batches}:")
            
            # Convert to generator format
            items = []
            for post in batch:
                items.append((
                    'combination',
                    post['location'],
                    post['specialty'],
                    post['ward'],
                    0  # Provider count
                ))
                
                loc = f"{post['ward']}, {post['location']}" if post['ward'] else post['location']
                logger.info(f"   - {post['specialty']} in {loc}")
            
            # Generate content
            try:
                content_batch = self.generator.generate_mega_batch(items, len(items))
                
                # Match generated content with WordPress posts
                for j, content in enumerate(content_batch):
                    if j < len(batch):
                        generated.append({
                            'wp_id': batch[j]['wp_id'],
                            'content': content
                        })
                
                # Save to database
                self.generator.save_content(content_batch)
                
                logger.info(f"✅ Generated {len(content_batch)} items")
                
            except Exception as e:
                logger.error(f"❌ Error in batch {batch_num}: {e}")
            
            # Rate limiting
            if i + batch_size < len(missing):
                time.sleep(2)
        
        return generated
    
    def update_wordpress_posts(self, wp_posts: List[Dict], db_content: Dict) -> int:
        """Update all WordPress posts with content from database"""
        
        session = self.db.get_session()
        updated = 0
        
        try:
            for post in wp_posts:
                if not post['location'] or not post['specialty']:
                    continue
                
                # Get content from database
                key = f"{post['location']}|{post['specialty']}|{post['ward'] or ''}"
                
                if key in db_content and db_content[key].get('brief_intro'):
                    content = db_content[key]
                    
                    # Check if update needed
                    if (post['current_brief'] == content['brief_intro'] and 
                        post['current_full'] == content['full_description']):
                        continue  # Already up to date
                    
                    # Update WordPress
                    update_data = {
                        # DO NOT change the title - it's auto-generated by another plugin
                        # 'title': content['title'],  # DON'T DO THIS
                        'acf': {
                            'brief_intro': content['brief_intro'],
                            'full_description': content['full_description'],
                            'seo_title': content['title'],
                            'seo_meta_description': content['meta_description']
                        },
                        # Yoast fields
                        '_yoast_wpseo_title': content['title'],
                        '_yoast_wpseo_metadesc': content['meta_description']
                    }
                    
                    try:
                        response = requests.post(
                            f"{self.wp_url}/wp-json/wp/v2/tc_combination/{post['wp_id']}",
                            auth=(self.wp_user, self.wp_pass),
                            json=update_data,
                            timeout=30
                        )
                        
                        if response.status_code in [200, 201]:
                            updated += 1
                            
                            # Update database with WordPress ID if not set
                            if not content.get('wordpress_post_id'):
                                session.execute(text("""
                                    UPDATE taxonomy_content
                                    SET wordpress_post_id = :wp_id
                                    WHERE location = :location
                                    AND specialty = :specialty
                                    AND COALESCE(ward, '') = COALESCE(:ward, '')
                                """), {
                                    'wp_id': post['wp_id'],
                                    'location': post['location'],
                                    'specialty': post['specialty'],
                                    'ward': post['ward']
                                })
                            
                            if updated % 10 == 0:
                                logger.info(f"   Updated {updated} posts...")
                        else:
                            logger.error(f"Failed to update post {post['wp_id']}: {response.status_code}")
                            
                    except Exception as e:
                        logger.error(f"Error updating post {post['wp_id']}: {e}")
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
        finally:
            session.close()
        
        return updated
    
    def run_full_sync(self):
        """Main sync process"""
        
        logger.info("=" * 60)
        logger.info("FULL COMBINATION SYNC")
        logger.info("=" * 60)
        
        # Step 1: Fetch all WordPress posts
        wp_posts = self.fetch_all_wordpress_combinations()
        
        # Analyze
        with_content = sum(1 for p in wp_posts if p['has_content'])
        without_content = len(wp_posts) - with_content
        
        logger.info(f"📊 WordPress Status:")
        logger.info(f"   Total posts: {len(wp_posts)}")
        logger.info(f"   With content: {with_content}")
        logger.info(f"   Without content: {without_content}")
        
        # Step 2: Get database content
        db_content = self.get_database_content()
        logger.info(f"📊 Database has content for {len(db_content)} combinations")
        
        # Step 3: Generate missing content
        self.generate_missing_content(wp_posts, db_content)
        
        # Re-fetch database content after generation
        db_content = self.get_database_content()
        
        # Step 4: Update all WordPress posts
        logger.info("\n📤 Updating WordPress posts...")
        updated = self.update_wordpress_posts(wp_posts, db_content)
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ SYNC COMPLETE")
        logger.info(f"   Total WordPress posts: {len(wp_posts)}")
        logger.info(f"   Database content entries: {len(db_content)}")
        logger.info(f"   Posts updated: {updated}")
        logger.info("=" * 60)


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync all tc_combination posts')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check status without updating')
    
    args = parser.parse_args()
    
    syncer = CombinationSyncer()
    
    if args.check_only:
        # Just check status
        wp_posts = syncer.fetch_all_wordpress_combinations()
        db_content = syncer.get_database_content()
        
        with_content = sum(1 for p in wp_posts if p['has_content'])
        without_content = len(wp_posts) - with_content
        
        logger.info("=" * 60)
        logger.info("STATUS CHECK")
        logger.info("=" * 60)
        logger.info(f"WordPress: {len(wp_posts)} total posts")
        logger.info(f"  - With content: {with_content}")
        logger.info(f"  - Without content: {without_content}")
        logger.info(f"Database: {len(db_content)} content entries")
        
        # Show examples of posts without content
        if without_content > 0:
            logger.info("\nExamples of posts without content:")
            for post in wp_posts[:10]:
                if not post['has_content']:
                    loc = f"{post['ward']}, {post['location']}" if post['ward'] else post['location']
                    logger.info(f"  - {post['specialty']} in {loc}")
    else:
        syncer.run_full_sync()


if __name__ == "__main__":
    main()