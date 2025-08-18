#!/usr/bin/env python3
"""
Fix terminology: Change "Dentistry" to "Dentist" in all content
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_dentistry_terminology():
    """Update all instances of Dentistry to Dentist"""
    
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # First, check what we have
        logger.info("Checking current terminology usage...")
        
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM taxonomy_content 
            WHERE specialty = 'Dentistry'
        """)).scalar()
        
        logger.info(f"Found {result} entries with 'Dentistry'")
        
        if result > 0:
            # Update specialty field
            logger.info("Updating specialty field...")
            session.execute(text("""
                UPDATE taxonomy_content
                SET specialty = 'Dentist'
                WHERE specialty = 'Dentistry'
            """))
            
            # Update titles
            logger.info("Updating titles...")
            session.execute(text("""
                UPDATE taxonomy_content
                SET title = REPLACE(title, 'Dentistry', 'Dentist')
                WHERE title LIKE '%Dentistry%'
            """))
            
            # Update meta descriptions
            logger.info("Updating meta descriptions...")
            session.execute(text("""
                UPDATE taxonomy_content
                SET meta_description = REPLACE(meta_description, 'dentistry', 'dentist')
                WHERE meta_description LIKE '%dentistry%'
            """))
            
            # Update brief intros
            logger.info("Updating brief intros...")
            session.execute(text("""
                UPDATE taxonomy_content
                SET brief_intro = REPLACE(brief_intro, 'dentistry', 'dentist')
                WHERE brief_intro LIKE '%dentistry%'
            """))
            
            # Update full descriptions
            logger.info("Updating full descriptions...")
            session.execute(text("""
                UPDATE taxonomy_content
                SET full_description = REPLACE(full_description, 'Dentistry', 'Dentist')
                WHERE full_description LIKE '%Dentistry%'
            """))
            
            session.commit()
            logger.info(f"✅ Updated {result} entries from Dentistry to Dentist")
            
            # Verify the changes
            verify = session.execute(text("""
                SELECT title, specialty 
                FROM taxonomy_content 
                WHERE specialty = 'Dentist'
                LIMIT 5
            """)).fetchall()
            
            logger.info("\nSample updated entries:")
            for title, specialty in verify:
                logger.info(f"  - {title} ({specialty})")
        else:
            logger.info("No entries with 'Dentistry' found")
        
        # Also check providers table
        provider_result = session.execute(text("""
            SELECT COUNT(*) 
            FROM providers 
            WHERE specialties::text LIKE '%Dentistry%'
        """)).scalar()
        
        if provider_result > 0:
            logger.info(f"\nFound {provider_result} providers with 'Dentistry' specialty")
            logger.info("Updating provider specialties...")
            
            session.execute(text("""
                UPDATE providers
                SET specialties = REPLACE(specialties::text, 'Dentistry', 'Dentist')::json
                WHERE specialties::text LIKE '%Dentistry%'
            """))
            
            session.commit()
            logger.info(f"✅ Updated {provider_result} provider records")
            
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating terminology: {e}")
    finally:
        session.close()


def update_wordpress_slugs():
    """Update WordPress post slugs from dentistry to dentist"""
    
    logger.info("\n📝 WordPress Slug Update Instructions:")
    logger.info("-" * 40)
    logger.info("Run these SQL commands in WordPress database:")
    print("""
    -- Update post slugs
    UPDATE wp_posts 
    SET post_name = REPLACE(post_name, 'dentistry', 'dentist')
    WHERE post_type = 'tc_combination' 
    AND post_name LIKE '%dentistry%';
    
    -- Update URLs in content if needed
    UPDATE wp_posts 
    SET post_content = REPLACE(post_content, '/dentistry-', '/dentist-')
    WHERE post_content LIKE '%/dentistry-%';
    
    -- Flush permalinks after running these queries
    """)
    logger.info("After running SQL, flush permalinks in WordPress admin")


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("FIXING DENTISTRY → DENTIST TERMINOLOGY")
    logger.info("=" * 60)
    
    # Fix database content
    fix_dentistry_terminology()
    
    # Show WordPress instructions
    update_wordpress_slugs()
    
    logger.info("\n✅ Database update complete!")
    logger.info("Next steps:")
    logger.info("1. Run the SQL commands shown above in WordPress")
    logger.info("2. Re-publish affected pages with publish_taxonomy_content.py")
    logger.info("3. Update any hardcoded links in templates")


if __name__ == "__main__":
    main()