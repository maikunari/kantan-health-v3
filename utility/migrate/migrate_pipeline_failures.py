#!/usr/bin/env python3
"""
Create pipeline_failures table for tracking content generation failures
"""

import sys
import os
# Add the parent directory to the path so we can import postgres_integration
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine, text
from postgres_integration import get_postgres_config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_pipeline_failures_table():
    """Create the pipeline_failures table"""
    config = get_postgres_config()
    engine = create_engine(
        f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
    )
    
    with engine.connect() as conn:
        # Check if table already exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'pipeline_failures'
            );
        """))
        
        if result.scalar():
            logger.info("Table pipeline_failures already exists")
            return
        
        # Create the table
        conn.execute(text("""
            CREATE TABLE pipeline_failures (
                id SERIAL PRIMARY KEY,
                provider_id INTEGER NOT NULL,
                provider_name VARCHAR(255),
                pipeline_run_id VARCHAR(255),
                step VARCHAR(50) NOT NULL,
                failure_reason VARCHAR(255) NOT NULL,
                error_details TEXT,
                retry_count INTEGER DEFAULT 0,
                resolved BOOLEAN DEFAULT FALSE,
                resolved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE
            );
        """))
        
        # Create indexes for common queries
        conn.execute(text("""
            CREATE INDEX idx_pipeline_failures_provider_id ON pipeline_failures(provider_id);
        """))
        
        conn.execute(text("""
            CREATE INDEX idx_pipeline_failures_resolved ON pipeline_failures(resolved);
        """))
        
        conn.execute(text("""
            CREATE INDEX idx_pipeline_failures_step ON pipeline_failures(step);
        """))
        
        conn.execute(text("""
            CREATE INDEX idx_pipeline_failures_reason ON pipeline_failures(failure_reason);
        """))
        
        conn.execute(text("""
            CREATE INDEX idx_pipeline_failures_run_id ON pipeline_failures(pipeline_run_id);
        """))
        
        conn.commit()
        logger.info("✅ Successfully created pipeline_failures table with indexes")

def create_pipeline_runs_table():
    """Create the pipeline_runs table for tracking overall pipeline executions"""
    config = get_postgres_config()
    engine = create_engine(
        f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
    )
    
    with engine.connect() as conn:
        # Check if table already exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'pipeline_runs'
            );
        """))
        
        if result.scalar():
            logger.info("Table pipeline_runs already exists")
            return
        
        # Create the table
        conn.execute(text("""
            CREATE TABLE pipeline_runs (
                id VARCHAR(255) PRIMARY KEY,
                run_type VARCHAR(50) NOT NULL, -- 'add_provider', 'bulk_update', 'retry'
                total_providers INTEGER DEFAULT 0,
                successful_providers INTEGER DEFAULT 0,
                failed_providers INTEGER DEFAULT 0,
                status VARCHAR(50) DEFAULT 'running', -- 'running', 'completed', 'failed'
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                metadata JSONB
            );
        """))
        
        # Create index
        conn.execute(text("""
            CREATE INDEX idx_pipeline_runs_status ON pipeline_runs(status);
        """))
        
        conn.execute(text("""
            CREATE INDEX idx_pipeline_runs_started_at ON pipeline_runs(started_at);
        """))
        
        conn.commit()
        logger.info("✅ Successfully created pipeline_runs table with indexes")

if __name__ == "__main__":
    try:
        create_pipeline_runs_table()
        create_pipeline_failures_table()
        logger.info("✅ Database migration completed successfully")
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        raise