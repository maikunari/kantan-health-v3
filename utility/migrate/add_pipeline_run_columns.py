#!/usr/bin/env python3
"""
Add missing columns to pipeline_runs table
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from postgres_integration import get_postgres_config
from sqlalchemy import create_engine, text


def add_missing_columns():
    """Add missing columns to pipeline_runs table"""
    
    # Get database connection
    config = get_postgres_config()
    connection_string = f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
    engine = create_engine(connection_string)
    
    print("🔧 Adding missing columns to pipeline_runs table...")
    
    try:
        with engine.begin() as conn:
            # Add collection_count column
            try:
                conn.execute(text('''
                    ALTER TABLE pipeline_runs 
                    ADD COLUMN collection_count INTEGER DEFAULT 0
                '''))
                print("  ✅ Added collection_count column")
            except Exception as e:
                if "already exists" in str(e):
                    print("  ⏩ collection_count column already exists")
                else:
                    raise
            
            # Add content_generated column
            try:
                conn.execute(text('''
                    ALTER TABLE pipeline_runs 
                    ADD COLUMN content_generated INTEGER DEFAULT 0
                '''))
                print("  ✅ Added content_generated column")
            except Exception as e:
                if "already exists" in str(e):
                    print("  ⏩ content_generated column already exists")
                else:
                    raise
            
            # Add wordpress_synced column
            try:
                conn.execute(text('''
                    ALTER TABLE pipeline_runs 
                    ADD COLUMN wordpress_synced INTEGER DEFAULT 0
                '''))
                print("  ✅ Added wordpress_synced column")
            except Exception as e:
                if "already exists" in str(e):
                    print("  ⏩ wordpress_synced column already exists")
                else:
                    raise
            
            # Add api_calls column
            try:
                conn.execute(text('''
                    ALTER TABLE pipeline_runs 
                    ADD COLUMN api_calls INTEGER DEFAULT 0
                '''))
                print("  ✅ Added api_calls column")
            except Exception as e:
                if "already exists" in str(e):
                    print("  ⏩ api_calls column already exists")
                else:
                    raise
            
            # Add total_cost column
            try:
                conn.execute(text('''
                    ALTER TABLE pipeline_runs 
                    ADD COLUMN total_cost FLOAT DEFAULT 0.0
                '''))
                print("  ✅ Added total_cost column")
            except Exception as e:
                if "already exists" in str(e):
                    print("  ⏩ total_cost column already exists")
                else:
                    raise
        
        print("\n✅ All columns added successfully!")
        
        # Show current table structure
        with engine.connect() as conn:
            result = conn.execute(text('''
                SELECT column_name, data_type, column_default
                FROM information_schema.columns
                WHERE table_name = 'pipeline_runs'
                ORDER BY ordinal_position
            '''))
            
            print("\n📊 Current pipeline_runs columns:")
            for row in result:
                default = f" DEFAULT {row[2]}" if row[2] else ""
                print(f"  - {row[0]}: {row[1]}{default}")
                
    except Exception as e:
        print(f"❌ Error adding columns: {str(e)}")
        raise


def main():
    """Main entry point"""
    print("="*60)
    print("ADD PIPELINE RUN COLUMNS")
    print("="*60)
    print()
    
    try:
        add_missing_columns()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())