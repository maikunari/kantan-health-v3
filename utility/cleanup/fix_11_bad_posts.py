#!/usr/bin/env python3
"""
Fix the 11 WordPress posts that have "Healthcare Directory" title
by generating proper content and updating them
"""

import os
import sys
import time
import logging
import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.generate_taxonomy_content_updated import TaxonomyContentGenerator
from src.core.database import DatabaseManager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv('config/.env')


def find_bad_posts():
    """Find the 11 posts with Healthcare Directory title"""
    
    wp_url = os.getenv('WORDPRESS_URL')
    wp_user = os.getenv('WORDPRESS_USERNAME')
    wp_pass = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
    
    bad_posts = []
    page = 1
    
    logger.info("Finding posts with 'Healthcare Directory' title...")
    
    while True:
        response = requests.get(
            f"{wp_url}/wp-json/wp/v2/tc_combination",
            auth=(wp_user, wp_pass),
            params={'per_page': 100, 'page': page},
            timeout=30
        )
        
        if response.status_code == 200:
            posts = response.json()
            if not posts:
                break
            
            for post in posts:
                if 'Healthcare Directory' in post['title']['rendered']:
                    # Parse the slug to get location/specialty
                    slug = post['slug']
                    specialty = None
                    location = None
                    ward = None
                    
                    # Parse slug like "english-dentist-in-shibuya" or "english-general-medicine-in-minato"
                    if 'english-' in slug and '-in-' in slug:
                        parts = slug.replace('english-', '').split('-in-')
                        if len(parts) == 2:
                            # Handle specialty (may have hyphens)
                            specialty_part = parts[0].replace('-', ' ').title()
                            # Fix common specialty names
                            if specialty_part == 'General Medicine':
                                specialty = 'General Medicine'
                            elif specialty_part == 'Internal Medicine':
                                specialty = 'Internal Medicine'
                            elif specialty_part == 'Ent Ear Nose Throat':
                                specialty = 'ENT (Ear, Nose & Throat)'
                            else:
                                specialty = specialty_part
                            
                            # Handle location (may be ward, city)
                            location_part = parts[1].replace('-', ' ').title()
                            
                            # Check if it's a Tokyo ward
                            tokyo_wards = ['Shibuya', 'Shinjuku', 'Minato', 'Chiyoda', 'Chuo', 
                                         'Meguro', 'Setagaya', 'Ota', 'Bunkyo', 'Taito', 
                                         'Sumida', 'Koto', 'Shinagawa', 'Nakano', 'Suginami',
                                         'Toshima', 'Kita', 'Arakawa', 'Itabashi', 'Nerima',
                                         'Adachi', 'Katsushika', 'Edogawa']
                            
                            if location_part in tokyo_wards:
                                ward = location_part
                                location = 'Tokyo'
                            else:
                                location = location_part
                    
                    bad_posts.append({
                        'id': post['id'],
                        'slug': slug,
                        'title': post['title']['rendered'],
                        'specialty': specialty,
                        'location': location,
                        'ward': ward
                    })
            
            page += 1
        else:
            break
    
    logger.info(f"Found {len(bad_posts)} posts with bad content")
    return bad_posts


def generate_content_for_posts(posts):
    """Generate proper content for the bad posts"""
    
    generator = TaxonomyContentGenerator()
    db = DatabaseManager()
    session = db.get_session()
    
    generated_content = []
    
    try:
        # Process each post
        for post in posts:
            if not post['specialty'] or not post['location']:
                logger.warning(f"Skipping post {post['id']} - couldn't parse location/specialty from slug: {post['slug']}")
                continue
            
            logger.info(f"Generating content for: {post['specialty']} in {post['location']} {post['ward'] or ''}")
            
            # Create item for generator
            item = (
                'combination',
                post['location'],
                post['specialty'],
                post['ward'],
                0  # Provider count
            )
            
            # Generate content
            try:
                content = generator._generate_individual(item)
                
                # Save to database with WordPress ID
                session.execute(text("""
                    INSERT INTO taxonomy_content 
                    (taxonomy_type, location, specialty, ward, title, meta_description,
                     brief_intro, full_description, provider_count, priority_tier, wordpress_post_id)
                    VALUES 
                    (:type, :location, :specialty, :ward, :title, :meta,
                     :brief, :full, :count, :tier, :wp_id)
                    ON CONFLICT (wordpress_post_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        meta_description = EXCLUDED.meta_description,
                        brief_intro = EXCLUDED.brief_intro,
                        full_description = EXCLUDED.full_description,
                        updated_at = CURRENT_TIMESTAMP
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
                    'wp_id': post['id']
                })
                
                generated_content.append({
                    'post_id': post['id'],
                    'content': content
                })
                
                logger.info(f"✅ Generated: {content.title}")
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Failed to generate content for {post['slug']}: {e}")
        
        session.commit()
        logger.info(f"✅ Saved {len(generated_content)} content items to database")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
    finally:
        session.close()
    
    return generated_content


def update_wordpress_posts(content_list):
    """Update WordPress posts with the correct content"""
    
    wp_url = os.getenv('WORDPRESS_URL')
    wp_user = os.getenv('WORDPRESS_USERNAME')
    wp_pass = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
    
    updated = 0
    
    for item in content_list:
        post_id = item['post_id']
        content = item['content']
        
        # Prepare update data
        update_data = {
            'title': content.title,
            '_yoast_wpseo_title': content.title,
            '_yoast_wpseo_metadesc': content.meta_description,
            'acf': {
                'brief_intro': content.brief_intro,
                'full_description': content.full_description,
                'seo_title': content.title,
                'seo_meta_description': content.meta_description
            }
        }
        
        # Update the post
        try:
            response = requests.post(
                f"{wp_url}/wp-json/wp/v2/tc_combination/{post_id}",
                auth=(wp_user, wp_pass),
                json=update_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Updated post {post_id}: {content.title}")
                updated += 1
            else:
                logger.error(f"❌ Failed to update post {post_id}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error updating post {post_id}: {e}")
    
    return updated


def main():
    """Main execution"""
    
    logger.info("=" * 60)
    logger.info("FIXING 11 BAD WORDPRESS POSTS")
    logger.info("=" * 60)
    
    # Step 1: Find the bad posts
    bad_posts = find_bad_posts()
    
    if not bad_posts:
        logger.info("No bad posts found!")
        return
    
    logger.info("\nBad posts found:")
    for post in bad_posts:
        loc = f"{post['ward']}, {post['location']}" if post['ward'] else post['location']
        logger.info(f"  - {post['specialty']} in {loc} (ID: {post['id']})")
    
    # Step 2: Generate content
    logger.info("\n" + "=" * 60)
    logger.info("GENERATING CONTENT")
    logger.info("=" * 60)
    
    generated = generate_content_for_posts(bad_posts)
    
    # Step 3: Update WordPress
    logger.info("\n" + "=" * 60)
    logger.info("UPDATING WORDPRESS")
    logger.info("=" * 60)
    
    updated = update_wordpress_posts(generated)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Bad posts found: {len(bad_posts)}")
    logger.info(f"Content generated: {len(generated)}")
    logger.info(f"Posts updated: {updated}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()