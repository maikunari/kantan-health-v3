#!/usr/bin/env python3
"""
Fix pipeline tracking tables to match new schema
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from postgres_integration import get_postgres_config
from sqlalchemy import create_engine, text


def fix_pipeline_tables():
    """Fix pipeline tables to match new schema"""
    
    # Get database connection
    config = get_postgres_config()
    connection_string = f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
    engine = create_engine(connection_string)
    
    print("🔧 Fixing pipeline tracking tables...")
    
    try:
        with engine.begin() as conn:
            # Drop existing tables
            print("  - Dropping old tables...")
            conn.execute(text('DROP TABLE IF EXISTS pipeline_steps CASCADE'))
            conn.execute(text('DROP TABLE IF EXISTS pipeline_runs CASCADE'))
            
            # Create new pipeline_runs table with correct schema
            print("  - Creating new pipeline_runs table...")
            conn.execute(text('''
                CREATE TABLE pipeline_runs (
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
            print("  - Creating pipeline_steps table...")
            conn.execute(text('''
                CREATE TABLE pipeline_steps (
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
            print("  - Creating indexes...")
            conn.execute(text('CREATE INDEX idx_pipeline_runs_run_id ON pipeline_runs(run_id)'))
            conn.execute(text('CREATE INDEX idx_pipeline_runs_status ON pipeline_runs(status)'))
            conn.execute(text('CREATE INDEX idx_pipeline_runs_started_at ON pipeline_runs(started_at DESC)'))
            
            conn.execute(text('CREATE INDEX idx_pipeline_steps_run_id ON pipeline_steps(run_id)'))
            conn.execute(text('CREATE INDEX idx_pipeline_steps_provider_id ON pipeline_steps(provider_id)'))
            conn.execute(text('CREATE INDEX idx_pipeline_steps_status ON pipeline_steps(status)'))
            
            # Add update trigger for updated_at
            print("  - Creating update triggers...")
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
                CREATE TRIGGER update_pipeline_runs_updated_at
                BEFORE UPDATE ON pipeline_runs
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            '''))
            
        print("✅ Pipeline tracking tables fixed successfully!")
        
        # Show table info
        with engine.connect() as conn:
            # Check pipeline_runs
            result = conn.execute(text('''
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'pipeline_runs'
                ORDER BY ordinal_position
            '''))
            
            print("\n📊 pipeline_runs columns:")
            for row in result:
                print(f"  - {row[0]}: {row[1]} {'NULL' if row[2] == 'YES' else 'NOT NULL'} {f'DEFAULT {row[3]}' if row[3] else ''}")
            
            # Check pipeline_steps
            result = conn.execute(text('''
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'pipeline_steps'
                ORDER BY ordinal_position
            '''))
            
            print("\n📊 pipeline_steps columns:")
            for row in result:
                print(f"  - {row[0]}: {row[1]} {'NULL' if row[2] == 'YES' else 'NOT NULL'} {f'DEFAULT {row[3]}' if row[3] else ''}")
                
    except Exception as e:
        print(f"❌ Error fixing tables: {str(e)}")
        raise


def main():
    """Main entry point"""
    print("="*60)
    print("FIX PIPELINE TRACKING TABLES")
    print("="*60)
    print()
    
    try:
        fix_pipeline_tables()
        print("\n✅ Tables fixed successfully!")
        
    except Exception as e:
        print(f"\n❌ Fix failed: {str(e)}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())