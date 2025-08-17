#!/usr/bin/env python3
"""
Publish Taxonomy Content to WordPress
Reads generated content from database and publishes to WordPress via REST API
"""

import os
import sys
import json
import time
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment
load_dotenv('config/.env')


class TaxonomyPublisher:
    """Publishes taxonomy content to WordPress"""
    
    def __init__(self):
        """Initialize publisher with WordPress credentials"""
        self.db = DatabaseManager()
        
        # WordPress configuration
        self.wp_url = os.getenv('WORDPRESS_URL')
        self.wp_user = os.getenv('WORDPRESS_USERNAME')
        self.wp_pass = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        
        if not all([self.wp_url, self.wp_user, self.wp_pass]):
            raise ValueError("WordPress credentials not found in environment")
        
        self.published_count = 0
        self.failed_count = 0
        
        logger.info("✅ Taxonomy publisher initialized")
    
    def get_unpublished_content(self, priority_tier: Optional[int] = None, limit: Optional[int] = None) -> List[Dict]:
        """Get content from database that hasn't been published"""
        session = self.db.get_session()
        try:
            query = """
                SELECT 
                    id, taxonomy_type, location, specialty, ward,
                    title, meta_description, brief_intro, full_description,
                    provider_count, priority_tier, created_at
                FROM taxonomy_content
                WHERE wordpress_post_id IS NULL
            """
            
            params = {}
            
            if priority_tier:
                query += " AND priority_tier = :tier"
                params['tier'] = priority_tier
            
            query += " ORDER BY priority_tier ASC, provider_count DESC"
            
            if limit:
                query += " LIMIT :limit"
                params['limit'] = limit
            
            result = session.execute(text(query), params).fetchall()
            
            content_list = []
            for row in result:
                content_list.append({
                    'id': row[0],
                    'taxonomy_type': row[1],
                    'location': row[2],
                    'specialty': row[3],
                    'ward': row[4],
                    'title': row[5],
                    'meta_description': row[6],
                    'brief_intro': row[7],
                    'full_description': row[8],
                    'provider_count': row[9],
                    'priority_tier': row[10],
                    'created_at': row[11]
                })
            
            return content_list
            
        finally:
            session.close()
    
    def find_or_create_wordpress_post(self, content: Dict) -> Optional[int]:
        """Find existing WordPress post or create new one"""
        
        # Generate slug from location and specialty
        location = content['location'].lower().replace(' ', '-')
        specialty = content['specialty'].lower().replace(' ', '-') if content['specialty'] else ''
        ward = content['ward'].lower().replace(' ', '-') if content['ward'] else ''
        
        if content['taxonomy_type'] == 'combination':
            if ward:
                slug = f"english-{specialty}-in-{ward}"
            else:
                slug = f"english-{specialty}-in-{location}"
        elif content['taxonomy_type'] == 'location':
            slug = f"english-healthcare-in-{location}"
        else:  # specialty
            slug = f"english-{specialty}"
        
        # Search for existing post by slug
        search_endpoint = f"{self.wp_url}/wp-json/wp/v2/tc_combination"
        
        try:
            # Search for existing post
            response = requests.get(
                search_endpoint,
                params={'slug': slug},
                auth=(self.wp_user, self.wp_pass),
                timeout=10
            )
            
            if response.status_code == 200:
                posts = response.json()
                if posts and len(posts) > 0:
                    # Post exists, return its ID
                    post_id = posts[0]['id']
                    logger.info(f"✅ Found existing post: {slug} (ID: {post_id})")
                    return post_id
            
            # Post doesn't exist, create it
            logger.info(f"📝 Creating new post: {slug}")
            
            # Prepare post data
            post_data = {
                'title': content['title'],
                'slug': slug,
                'status': 'publish',
                'content': '',  # Minimal content as we use ACF fields
                'acf': {
                    'brief_intro': content['brief_intro'],
                    'full_description': content['full_description']
                }
            }
            
            # Create the post
            create_response = requests.post(
                search_endpoint,
                auth=(self.wp_user, self.wp_pass),
                json=post_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if create_response.status_code in [200, 201]:
                new_post = create_response.json()
                post_id = new_post['id']
                logger.info(f"✅ Created post: {slug} (ID: {post_id})")
                return post_id
            else:
                logger.error(f"❌ Failed to create post: {create_response.status_code}")
                logger.error(f"   Response: {create_response.text[:500]}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error with WordPress: {e}")
            return None
    
    def update_wordpress_acf_fields(self, post_id: int, content: Dict) -> bool:
        """Update ACF fields for existing WordPress post"""
        
        endpoint = f"{self.wp_url}/wp-json/wp/v2/tc_combination/{post_id}"
        
        # Prepare ACF data
        data = {
            'acf': {
                'brief_intro': content['brief_intro'],
                'full_description': content['full_description']
            }
        }
        
        try:
            response = requests.post(
                endpoint,
                auth=(self.wp_user, self.wp_pass),
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Updated ACF fields for post {post_id}")
                return True
            else:
                # Try alternative ACF endpoint
                alt_endpoint = f"{self.wp_url}/wp-json/acf/v3/tc_combination/{post_id}"
                alt_response = requests.post(
                    alt_endpoint,
                    auth=(self.wp_user, self.wp_pass),
                    json={'fields': {
                        'brief_intro': content['brief_intro'],
                        'full_description': content['full_description']
                    }},
                    timeout=30
                )
                
                if alt_response.status_code in [200, 201]:
                    logger.info(f"✅ Updated ACF fields via alternative endpoint")
                    return True
                else:
                    logger.error(f"❌ Failed to update ACF fields: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error updating ACF fields: {e}")
            return False
    
    def mark_as_published(self, content_id: int, wordpress_post_id: int):
        """Mark content as published in database"""
        session = self.db.get_session()
        try:
            # Add wordpress_post_id column if it doesn't exist
            session.execute(text("""
                ALTER TABLE taxonomy_content 
                ADD COLUMN IF NOT EXISTS wordpress_post_id INTEGER
            """))
            session.commit()
            
            # Update the record
            session.execute(text("""
                UPDATE taxonomy_content 
                SET wordpress_post_id = :wp_id,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """), {
                'wp_id': wordpress_post_id,
                'id': content_id
            })
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error marking as published: {e}")
        finally:
            session.close()
    
    def publish_content(self, content: Dict) -> bool:
        """Publish a single content item to WordPress"""
        
        logger.info(f"📤 Publishing: {content['title']}")
        
        # Find or create WordPress post
        post_id = self.find_or_create_wordpress_post(content)
        
        if not post_id:
            self.failed_count += 1
            return False
        
        # Update ACF fields
        success = self.update_wordpress_acf_fields(post_id, content)
        
        if success:
            # Mark as published in database
            self.mark_as_published(content['id'], post_id)
            self.published_count += 1
            
            # Generate URL
            location = content['location'].lower().replace(' ', '-')
            specialty = content['specialty'].lower().replace(' ', '-') if content['specialty'] else ''
            ward = content['ward'].lower().replace(' ', '-') if content['ward'] else ''
            
            if ward:
                url = f"{self.wp_url}/english-{specialty}-in-{ward}/"
            else:
                url = f"{self.wp_url}/english-{specialty}-in-{location}/"
            
            logger.info(f"   View at: {url}")
            return True
        else:
            self.failed_count += 1
            return False
    
    def publish_batch(self, priority_tier: Optional[int] = None, limit: Optional[int] = None):
        """Publish a batch of content to WordPress"""
        
        # Get unpublished content
        content_list = self.get_unpublished_content(priority_tier, limit)
        
        if not content_list:
            logger.info("📭 No unpublished content found")
            return
        
        logger.info(f"📚 Found {len(content_list)} items to publish")
        logger.info("=" * 60)
        
        # Publish each item
        for i, content in enumerate(content_list, 1):
            logger.info(f"\n[{i}/{len(content_list)}] Processing...")
            
            success = self.publish_content(content)
            
            # Rate limiting
            if i < len(content_list):
                time.sleep(2)  # Be nice to WordPress API
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 PUBLISHING SUMMARY")
        logger.info(f"   ✅ Successfully published: {self.published_count}")
        logger.info(f"   ❌ Failed: {self.failed_count}")
        logger.info(f"   📈 Success rate: {self.published_count/(self.published_count + self.failed_count)*100:.1f}%")
        logger.info("=" * 60)


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Publish taxonomy content to WordPress')
    parser.add_argument('--mode', choices=['tier1', 'tier2', 'all'], 
                       help='Publish by priority tier')
    parser.add_argument('--limit', type=int, 
                       help='Limit number of items to publish')
    parser.add_argument('--test', action='store_true',
                       help='Test with single item')
    
    args = parser.parse_args()
    
    publisher = TaxonomyPublisher()
    
    if args.test:
        logger.info("🧪 Test mode - publishing single item...")
        publisher.publish_batch(limit=1)
    
    elif args.mode == 'tier1':
        logger.info("🏆 Publishing Tier 1 content (5+ providers)...")
        publisher.publish_batch(priority_tier=1, limit=args.limit)
    
    elif args.mode == 'tier2':
        logger.info("📈 Publishing Tier 2 content (1-4 providers)...")
        publisher.publish_batch(priority_tier=2, limit=args.limit)
    
    elif args.mode == 'all':
        logger.info("🌟 Publishing all unpublished content...")
        publisher.publish_batch(limit=args.limit)
    
    else:
        # Default: publish with optional limit
        logger.info("📤 Publishing unpublished content...")
        publisher.publish_batch(limit=args.limit)


if __name__ == "__main__":
    main()