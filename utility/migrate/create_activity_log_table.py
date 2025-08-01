#!/usr/bin/env python3
"""
Create Activity Log Table Migration
Creates a comprehensive activity log table for tracking all system operations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from postgres_integration import get_postgres_config
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_activity_log_table():
    """Create the activity_log table for tracking all system operations"""
    
    config = get_postgres_config()
    engine = create_engine(f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}")
    
    # Create activity_log table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS activity_log (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        activity_type VARCHAR(50) NOT NULL,
        activity_category VARCHAR(50) NOT NULL,
        user_id INTEGER,
        provider_id INTEGER,
        provider_name VARCHAR(255),
        description TEXT NOT NULL,
        details JSONB,
        status VARCHAR(50),
        duration_ms INTEGER,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes for common queries
    CREATE INDEX IF NOT EXISTS idx_activity_log_timestamp ON activity_log(timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_activity_log_type ON activity_log(activity_type);
    CREATE INDEX IF NOT EXISTS idx_activity_log_category ON activity_log(activity_category);
    CREATE INDEX IF NOT EXISTS idx_activity_log_provider ON activity_log(provider_id);
    CREATE INDEX IF NOT EXISTS idx_activity_log_status ON activity_log(status);
    CREATE INDEX IF NOT EXISTS idx_activity_log_timestamp_category ON activity_log(timestamp DESC, activity_category);
    
    -- Activity categories:
    -- 'provider_creation' - New providers added
    -- 'content_generation' - AI content generation
    -- 'data_quality' - Data quality updates (geocoding, Google Places, etc.)
    -- 'wordpress_sync' - WordPress sync operations
    -- 'duplicate_cleanup' - WordPress duplicate management
    -- 'settings_update' - Configuration changes
    -- 'authentication' - Login/logout events
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
            logger.info("✅ Activity log table created successfully")
            
            # Verify table was created
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'activity_log'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            logger.info(f"📊 Activity log table has {len(columns)} columns:")
            for col in columns:
                logger.info(f"   - {col[0]}: {col[1]}")
                
    except Exception as e:
        logger.error(f"❌ Error creating activity log table: {str(e)}")
        raise

if __name__ == "__main__":
    create_activity_log_table()