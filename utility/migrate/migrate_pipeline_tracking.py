#!/usr/bin/env python3
"""
Migration script to add pipeline tracking tables
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from postgres_integration import get_postgres_config
from sqlalchemy import create_engine, text

def create_pipeline_tracking_tables():
    """Create tables for tracking pipeline runs"""
    
    # Get database connection
    config = get_postgres_config()
    connection_string = f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
    engine = create_engine(connection_string)
    
    print("🔧 Creating pipeline tracking tables...")
    
    try:
        with engine.begin() as conn:  # Use begin for transaction
            # Create pipeline_runs table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(255) UNIQUE NOT NULL,
                    run_type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'running',
                    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    total_providers INTEGER DEFAULT 0,
                    successful_providers INTEGER DEFAULT 0,
                    failed_providers INTEGER DEFAULT 0,
                    config JSONB DEFAULT '{}',
                    errors JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            
            # Create pipeline_steps table
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS pipeline_steps (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(255) NOT NULL,
                    provider_id INTEGER,
                    provider_name VARCHAR(255),
                    step_name VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'running',
                    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    details JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (provider_id) REFERENCES providers(id)
                )
            '''))
            
            # Create indexes
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_pipeline_runs_run_id ON pipeline_runs(run_id)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started_at ON pipeline_runs(started_at DESC)'))
            
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_pipeline_steps_run_id ON pipeline_steps(run_id)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_pipeline_steps_provider_id ON pipeline_steps(provider_id)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_pipeline_steps_status ON pipeline_steps(status)'))
            
            # Add update trigger for updated_at
            conn.execute(text('''
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            '''))
            
            conn.execute(text('''
                DROP TRIGGER IF EXISTS update_pipeline_runs_updated_at ON pipeline_runs;
                CREATE TRIGGER update_pipeline_runs_updated_at
                BEFORE UPDATE ON pipeline_runs
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            '''))
            
            # Commit is handled automatically by context manager
            
        print("✅ Pipeline tracking tables created successfully!")
        
        # Show table info
        with engine.connect() as conn:
            result = conn.execute(text('''
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('pipeline_runs', 'pipeline_steps')
                ORDER BY table_name
            '''))
            
            print("\n📊 Created tables:")
            for row in result:
                print(f"  - {row[0]}")
                
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        raise


def main():
    """Main entry point"""
    print("="*60)
    print("PIPELINE TRACKING MIGRATION")
    print("="*60)
    print()
    
    try:
        create_pipeline_tracking_tables()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())