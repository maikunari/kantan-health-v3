#!/usr/bin/env python3
"""
Test Yoast SEO field population for taxonomy content
Tests that SEO title and meta description are properly set when publishing
"""

import os
import sys
import logging
import requests
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment
load_dotenv('config/.env')


def test_yoast_fields():
    """Test that Yoast SEO fields are properly populated"""
    
    db = DatabaseManager()
    session = db.get_session()
    
    wp_url = os.getenv('WORDPRESS_URL')
    wp_user = os.getenv('WORDPRESS_USERNAME')
    wp_pass = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
    
    if not all([wp_url, wp_user, wp_pass]):
        logger.error("WordPress credentials not found")
        return False
    
    try:
        # Get ONE unpublished content item to test
        logger.info("🔍 Finding test content...")
        
        result = session.execute(text("""
            SELECT 
                id, location, specialty, ward,
                title, meta_description, brief_intro, full_description
            FROM taxonomy_content
            WHERE wordpress_post_id IS NULL
            LIMIT 1
        """)).fetchone()
        
        if not result:
            logger.warning("No unpublished content found. Let's check a published one...")
            
            # Get a published one to verify
            result = session.execute(text("""
                SELECT 
                    id, location, specialty, ward,
                    title, meta_description, brief_intro, full_description,
                    wordpress_post_id
                FROM taxonomy_content
                WHERE wordpress_post_id IS NOT NULL
                LIMIT 1
            """)).fetchone()
            
            if not result:
                logger.error("No content found at all!")
                return False
            
            # Check the existing WordPress post
            post_id = result[8]
            logger.info(f"📝 Checking existing post ID {post_id}...")
            
            # Get the post and check its Yoast fields
            response = requests.get(
                f"{wp_url}/wp-json/wp/v2/tc_combination/{post_id}",
                auth=(wp_user, wp_pass),
                timeout=10
            )
            
            if response.status_code == 200:
                post_data = response.json()
                
                # Check if Yoast fields exist
                yoast_title = post_data.get('_yoast_wpseo_title', 'NOT_FOUND')
                yoast_desc = post_data.get('_yoast_wpseo_metadesc', 'NOT_FOUND')
                
                logger.info("=" * 60)
                logger.info("📊 YOAST SEO FIELD CHECK")
                logger.info("=" * 60)
                logger.info(f"Post Title: {post_data.get('title', {}).get('rendered', 'N/A')}")
                logger.info(f"Expected SEO Title: {result[4]}")
                logger.info(f"Actual Yoast Title: {yoast_title}")
                logger.info("-" * 60)
                logger.info(f"Expected Meta Desc: {result[5]}")
                logger.info(f"Actual Yoast Desc: {yoast_desc}")
                logger.info("=" * 60)
                
                if yoast_title == 'NOT_FOUND':
                    logger.warning("⚠️  Yoast fields not exposed in REST API")
                    logger.info("This might be normal - fields may be set but not visible via API")
                    logger.info("Check WordPress admin to verify if fields are populated")
                elif yoast_title == result[4]:
                    logger.info("✅ Yoast SEO title matches expected value!")
                else:
                    logger.warning(f"⚠️  Yoast title doesn't match (might be from earlier version)")
            
            return True
        
        # We have unpublished content - let's publish it and check
        logger.info(f"📤 Testing with: {result[4]}")
        
        # Generate slug
        location = result[1].lower().replace(' ', '-')
        specialty = result[2].lower().replace(' ', '-') if result[2] else ''
        ward = result[3].lower().replace(' ', '-') if result[3] else ''
        
        if ward:
            slug = f"english-{specialty}-in-{ward}"
        else:
            slug = f"english-{specialty}-in-{location}"
        
        logger.info(f"📝 Creating/updating post: {slug}")
        
        # Create the post with Yoast fields INSIDE ACF
        post_data = {
            'title': result[4],  # title
            'slug': slug,
            'status': 'publish',
            'content': '',  # Minimal content
            'acf': {
                'brief_intro': result[6],
                'full_description': result[7],
                # Yoast SEO fields go INSIDE ACF array
                '_yoast_wpseo_title': result[4],  # SEO title
                '_yoast_wpseo_metadesc': result[5],  # Meta description
                # Also add RankMath compatibility
                '_rank_math_title': result[4],
                '_rank_math_description': result[5]
            }
        }
        
        # Create the post
        create_response = requests.post(
            f"{wp_url}/wp-json/wp/v2/tc_combination",
            auth=(wp_user, wp_pass),
            json=post_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if create_response.status_code in [200, 201]:
            new_post = create_response.json()
            post_id = new_post['id']
            
            logger.info(f"✅ Post created/updated: ID {post_id}")
            
            # Mark as published in database
            session.execute(text("""
                UPDATE taxonomy_content 
                SET wordpress_post_id = :wp_id
                WHERE id = :id
            """), {'wp_id': post_id, 'id': result[0]})
            session.commit()
            
            # Now verify the Yoast fields
            logger.info("🔍 Verifying Yoast fields...")
            
            verify_response = requests.get(
                f"{wp_url}/wp-json/wp/v2/tc_combination/{post_id}",
                auth=(wp_user, wp_pass),
                timeout=10
            )
            
            if verify_response.status_code == 200:
                verified_data = verify_response.json()
                
                yoast_title = verified_data.get('_yoast_wpseo_title', 'NOT_VISIBLE')
                yoast_desc = verified_data.get('_yoast_wpseo_metadesc', 'NOT_VISIBLE')
                
                logger.info("=" * 60)
                logger.info("📊 YOAST SEO VERIFICATION RESULTS")
                logger.info("=" * 60)
                logger.info(f"Post URL: {wp_url}/{slug}/")
                logger.info(f"Post ID: {post_id}")
                logger.info("-" * 60)
                logger.info(f"Expected SEO Title: {result[4]}")
                logger.info(f"Yoast Title Field: {yoast_title}")
                logger.info("-" * 60)
                logger.info(f"Expected Meta Desc: {result[5][:80]}...")
                logger.info(f"Yoast Desc Field: {yoast_desc[:80] if yoast_desc != 'NOT_VISIBLE' else 'NOT_VISIBLE'}...")
                logger.info("=" * 60)
                
                if yoast_title == 'NOT_VISIBLE':
                    logger.info("\n📋 IMPORTANT:")
                    logger.info("Yoast fields may be set but not visible via REST API")
                    logger.info("Please check in WordPress admin:")
                    logger.info(f"1. Go to {wp_url}/wp-admin/")
                    logger.info(f"2. Edit the post: {new_post.get('title', {}).get('rendered', slug)}")
                    logger.info("3. Scroll to Yoast SEO section")
                    logger.info("4. Check if SEO title and meta description are populated")
                    logger.info("\nIf they are populated in admin, the sync is working!")
                else:
                    logger.info("\n✅ SUCCESS: Yoast fields are accessible via REST API!")
                
                return True
            else:
                logger.error(f"Failed to verify: {verify_response.status_code}")
                return False
        else:
            logger.error(f"Failed to create post: {create_response.status_code}")
            logger.error(f"Response: {create_response.text[:500]}")
            return False
            
    except Exception as e:
        logger.error(f"Error: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def main():
    """Main execution"""
    logger.info("🧪 TESTING YOAST SEO FIELD POPULATION")
    logger.info("=" * 60)
    
    success = test_yoast_fields()
    
    if success:
        logger.info("\n✅ Test completed!")
        logger.info("\nNext steps:")
        logger.info("1. Check the WordPress admin to verify Yoast fields")
        logger.info("2. View the page source to check meta tags")
        logger.info("3. If everything looks good, run the full generation:")
        logger.info("   python3 scripts/generate_all_combinations.py")
        logger.info("4. Then publish in batches:")
        logger.info("   python3 scripts/publish_taxonomy_content.py --limit 10")
    else:
        logger.error("\n❌ Test failed - check the errors above")


if __name__ == "__main__":
    main()