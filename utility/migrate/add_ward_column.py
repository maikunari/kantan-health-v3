#!/usr/bin/env python3
"""
Add ward column to providers table
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.database import DatabaseManager
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_ward_column():
    """Add ward column to providers table if it doesn't exist"""
    
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Check if column already exists
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='providers' AND column_name='ward'
        """)).fetchone()
        
        if result:
            logger.info("✅ Ward column already exists")
            return
        
        # Add the ward column
        logger.info("Adding ward column to providers table...")
        session.execute(text("""
            ALTER TABLE providers 
            ADD COLUMN ward VARCHAR(100)
        """))
        
        session.commit()
        logger.info("✅ Ward column added successfully")
        
        # Update ward data for Tokyo providers
        logger.info("Updating ward data for existing providers...")
        session.execute(text("""
            UPDATE providers 
            SET ward = 'Minato' 
            WHERE address LIKE '%Minato%' AND city = 'Tokyo'
        """))
        
        session.execute(text("""
            UPDATE providers 
            SET ward = 'Shibuya' 
            WHERE address LIKE '%Shibuya%' AND city = 'Tokyo'
        """))
        
        session.execute(text("""
            UPDATE providers 
            SET ward = 'Shinjuku' 
            WHERE address LIKE '%Shinjuku%' AND city = 'Tokyo'
        """))
        
        session.execute(text("""
            UPDATE providers 
            SET ward = 'Chiyoda' 
            WHERE address LIKE '%Chiyoda%' AND city = 'Tokyo'
        """))
        
        session.commit()
        logger.info("✅ Ward data updated")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    add_ward_column()