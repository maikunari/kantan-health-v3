#!/usr/bin/env python3
"""
Add provider_name_romaji column to providers table
This stores the romanized version of Japanese provider names
"""

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.database import DatabaseManager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def add_romaji_column():
    """Add provider_name_romaji column to providers table"""
    
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Check if column already exists
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'providers' 
            AND column_name = 'provider_name_romaji'
        """
        
        result = session.execute(text(check_query)).first()
        
        if result:
            logger.info("✅ Column 'provider_name_romaji' already exists")
            return True
        
        # Add the column
        logger.info("Adding provider_name_romaji column...")
        
        alter_query = """
            ALTER TABLE providers 
            ADD COLUMN provider_name_romaji VARCHAR(500)
        """
        
        session.execute(text(alter_query))
        session.commit()
        
        logger.info("✅ Successfully added provider_name_romaji column")
        
        # Add comment to describe the column
        comment_query = """
            COMMENT ON COLUMN providers.provider_name_romaji IS 
            'Romanized version of Japanese provider names for better readability'
        """
        
        session.execute(text(comment_query))
        session.commit()
        
        logger.info("✅ Added column comment")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error adding column: {e}")
        session.rollback()
        return False
        
    finally:
        session.close()


def main():
    """Main execution"""
    logger.info("="*60)
    logger.info("🔧 ADDING ROMAJI COLUMN TO PROVIDERS TABLE")
    logger.info("="*60)
    
    success = add_romaji_column()
    
    if success:
        logger.info("\n✅ Migration completed successfully")
        logger.info("   Column 'provider_name_romaji' is now available")
        logger.info("   Run the romaji population script to fill existing data")
    else:
        logger.error("\n❌ Migration failed")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())