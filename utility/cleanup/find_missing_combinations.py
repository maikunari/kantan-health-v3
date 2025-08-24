#!/usr/bin/env python3
"""
Find which combinations are missing from our database
by comparing with WordPress tc_combination posts
"""

import os
import sys
import requests
import logging
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv('config/.env')


def get_wordpress_combinations():
    """Fetch all tc_combination posts from WordPress"""
    
    wp_url = os.getenv('WORDPRESS_URL')
    wp_user = os.getenv('WORDPRESS_USERNAME')
    wp_pass = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
    
    all_posts = []
    page = 1
    per_page = 100
    
    logger.info("Fetching WordPress tc_combination posts...")
    
    while True:
        response = requests.get(
            f"{wp_url}/wp-json/wp/v2/tc_combination",
            auth=(wp_user, wp_pass),
            params={'per_page': per_page, 'page': page},
            timeout=30
        )
        
        if response.status_code == 200:
            posts = response.json()
            if not posts:
                break
            
            for post in posts:
                # Check if this post has the bad content
                acf = post.get('acf', {})
                full_desc = acf.get('full_description', '')
                
                if 'Appointments can usually be made by phone' in full_desc or not full_desc:
                    all_posts.append({
                        'id': post['id'],
                        'title': post['title']['rendered'],
                        'slug': post['slug'],
                        'has_bad_content': True
                    })
                else:
                    all_posts.append({
                        'id': post['id'],
                        'title': post['title']['rendered'],
                        'slug': post['slug'],
                        'has_bad_content': False
                    })
            
            page += 1
        else:
            break
    
    logger.info(f"Found {len(all_posts)} WordPress posts")
    return all_posts


def get_database_combinations():
    """Get all combinations from our database"""
    
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        result = session.execute(text("""
            SELECT 
                wordpress_post_id,
                location,
                specialty,
                ward,
                title
            FROM taxonomy_content
            WHERE wordpress_post_id IS NOT NULL
        """)).fetchall()
        
        db_combos = {}
        for row in result:
            db_combos[row[0]] = {
                'location': row[1],
                'specialty': row[2],
                'ward': row[3],
                'title': row[4]
            }
        
        return db_combos
        
    finally:
        session.close()


def main():
    """Find missing and bad content"""
    
    # Get WordPress posts
    wp_posts = get_wordpress_combinations()
    
    # Get database content
    db_combos = get_database_combinations()
    
    # Analyze
    bad_content_posts = []
    missing_from_db = []
    
    for post in wp_posts:
        if post['has_bad_content']:
            bad_content_posts.append(post)
        
        if post['id'] not in db_combos:
            missing_from_db.append(post)
    
    logger.info("\n" + "=" * 60)
    logger.info("ANALYSIS RESULTS")
    logger.info("=" * 60)
    
    logger.info(f"Total WordPress posts: {len(wp_posts)}")
    logger.info(f"Posts with bad/empty content: {len(bad_content_posts)}")
    logger.info(f"Posts missing from database: {len(missing_from_db)}")
    
    if bad_content_posts:
        logger.info("\nPosts with bad content (first 10):")
        for post in bad_content_posts[:10]:
            logger.info(f"  - {post['title']} (ID: {post['id']}, slug: {post['slug']})")
    
    if missing_from_db:
        logger.info("\nPosts missing from database (first 10):")
        for post in missing_from_db[:10]:
            logger.info(f"  - {post['title']} (ID: {post['id']}, slug: {post['slug']})")
    
    # Extract location/specialty from slugs for missing posts
    if missing_from_db:
        logger.info("\n" + "=" * 60)
        logger.info("COMBINATIONS TO REGENERATE")
        logger.info("=" * 60)
        
        combos_to_generate = []
        for post in missing_from_db:
            slug = post['slug']
            # Parse slug like "english-dentist-in-shibuya"
            if 'english-' in slug and '-in-' in slug:
                parts = slug.replace('english-', '').split('-in-')
                if len(parts) == 2:
                    specialty = parts[0].replace('-', ' ').title()
                    location = parts[1].replace('-', ' ').title()
                    
                    combos_to_generate.append({
                        'specialty': specialty,
                        'location': location,
                        'wp_id': post['id']
                    })
                    
                    logger.info(f"  - {specialty} in {location} (WP ID: {post['id']})")
        
        logger.info(f"\nTotal combinations to regenerate: {len(combos_to_generate)}")


if __name__ == "__main__":
    main()