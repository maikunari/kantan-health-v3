#!/usr/bin/env python3
"""
Update SEO fields for taxonomy pages
Handles Yoast SEO or Rank Math SEO plugin fields
"""

import os
import sys
import logging
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv('config/.env')


class SEOUpdater:
    """Update SEO meta fields in WordPress"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.wp_url = os.getenv('WORDPRESS_URL')
        self.wp_user = os.getenv('WORDPRESS_USERNAME')
        self.wp_pass = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        
        if not all([self.wp_url, self.wp_user, self.wp_pass]):
            raise ValueError("WordPress credentials not found")
    
    def update_yoast_seo(self, post_id: int, title: str, description: str) -> bool:
        """Update Yoast SEO fields via REST API
        
        Note: Requires Yoast SEO plugin with REST API enabled
        """
        
        endpoint = f"{self.wp_url}/wp-json/yoast/v1/post/{post_id}"
        
        data = {
            'yoast_meta': {
                'yoast_wpseo_title': title,
                'yoast_wpseo_metadesc': description,
                'yoast_wpseo_focuskw': title.split(' in ')[0] if ' in ' in title else title
            }
        }
        
        try:
            response = requests.post(
                endpoint,
                auth=(self.wp_user, self.wp_pass),
                json=data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Updated Yoast SEO for post {post_id}")
                return True
            else:
                logger.warning(f"Yoast API not available: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating Yoast: {e}")
            return False
    
    def update_rankmath_seo(self, post_id: int, title: str, description: str) -> bool:
        """Update Rank Math SEO fields
        
        Note: Rank Math stores data differently
        """
        
        endpoint = f"{self.wp_url}/wp-json/rankmath/v1/updateMeta"
        
        data = {
            'objectID': post_id,
            'objectType': 'post',
            'meta': {
                'rank_math_title': title,
                'rank_math_description': description,
                'rank_math_focus_keyword': title.split(' in ')[0] if ' in ' in title else title
            }
        }
        
        try:
            response = requests.post(
                endpoint,
                auth=(self.wp_user, self.wp_pass),
                json=data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Updated Rank Math SEO for post {post_id}")
                return True
            else:
                logger.warning(f"Rank Math API not available: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating Rank Math: {e}")
            return False
    
    def update_via_custom_endpoint(self, post_id: int, title: str, description: str) -> bool:
        """Update via custom WordPress endpoint
        
        This requires adding a custom endpoint to your WordPress theme/plugin:
        
        add_action('rest_api_init', function() {
            register_rest_route('custom/v1', '/update-seo/(?P<id>\d+)', [
                'methods' => 'POST',
                'callback' => 'update_seo_fields',
                'permission_callback' => function() {
                    return current_user_can('edit_posts');
                }
            ]);
        });
        
        function update_seo_fields($request) {
            $post_id = $request['id'];
            $title = $request->get_param('title');
            $description = $request->get_param('description');
            
            // Update Yoast
            update_post_meta($post_id, '_yoast_wpseo_title', $title);
            update_post_meta($post_id, '_yoast_wpseo_metadesc', $description);
            
            // Or update Rank Math
            update_post_meta($post_id, 'rank_math_title', $title);
            update_post_meta($post_id, 'rank_math_description', $description);
            
            return ['success' => true];
        }
        """
        
        endpoint = f"{self.wp_url}/wp-json/custom/v1/update-seo/{post_id}"
        
        data = {
            'title': title,
            'description': description
        }
        
        try:
            response = requests.post(
                endpoint,
                auth=(self.wp_user, self.wp_pass),
                json=data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Updated SEO via custom endpoint for post {post_id}")
                return True
            else:
                logger.warning(f"Custom endpoint not available: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error with custom endpoint: {e}")
            return False
    
    def update_all_seo_fields(self):
        """Update SEO fields for all published taxonomy pages"""
        
        session = self.db.get_session()
        try:
            # Get all published content with WordPress IDs
            result = session.execute(text("""
                SELECT 
                    wordpress_post_id,
                    title,
                    meta_description
                FROM taxonomy_content
                WHERE wordpress_post_id IS NOT NULL
                ORDER BY wordpress_post_id
            """)).fetchall()
            
            logger.info(f"Found {len(result)} posts to update")
            
            success_count = 0
            for post_id, title, description in result:
                logger.info(f"Updating post {post_id}: {title[:50]}...")
                
                # Try different methods
                success = (
                    self.update_yoast_seo(post_id, title, description) or
                    self.update_rankmath_seo(post_id, title, description) or
                    self.update_via_custom_endpoint(post_id, title, description)
                )
                
                if success:
                    success_count += 1
                else:
                    logger.warning(f"Could not update SEO for post {post_id}")
            
            logger.info(f"✅ Updated {success_count}/{len(result)} posts")
            
        finally:
            session.close()


def main():
    """Update SEO fields for published content"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Update SEO fields in WordPress')
    parser.add_argument('--post-id', type=int, help='Update specific post')
    parser.add_argument('--all', action='store_true', help='Update all posts')
    
    args = parser.parse_args()
    
    updater = SEOUpdater()
    
    if args.post_id:
        # Get content from database
        session = updater.db.get_session()
        result = session.execute(text("""
            SELECT title, meta_description
            FROM taxonomy_content
            WHERE wordpress_post_id = :id
        """), {'id': args.post_id}).fetchone()
        session.close()
        
        if result:
            title, description = result
            updater.update_yoast_seo(args.post_id, title, description)
        else:
            logger.error(f"Post {args.post_id} not found in database")
    
    elif args.all:
        updater.update_all_seo_fields()
    
    else:
        print("Usage: python3 update_seo_fields.py --all")
        print("   or: python3 update_seo_fields.py --post-id 123")


if __name__ == "__main__":
    main()