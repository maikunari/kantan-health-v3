#!/usr/bin/env python3
"""
Database Migration Script
Adds missing columns to the providers table for WordPress integration
"""

import os
from dotenv import load_dotenv
import psycopg2

def run_migration():
    """Run database migration to add missing columns"""
    
    # Load database credentials
    config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    load_dotenv(config_path)
    db_user = os.getenv('POSTGRES_USER', 'postgres')
    db_password = os.getenv('POSTGRES_PASSWORD', 'password')  
    db_host = os.getenv('POSTGRES_HOST', 'localhost')

    print('🔄 Starting database migration...')

    try:
        conn = psycopg2.connect(
            host=db_host,
            database='directory',
            user=db_user,
            password=db_password
        )
        cur = conn.cursor()
        
        # Check which columns exist
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'providers'
        """)
        existing_columns = [row[0] for row in cur.fetchall()]
        print(f'📋 Existing columns: {existing_columns}')
        
        # Add missing columns
        columns_to_add = [
            ('ai_description', 'TEXT'),
            ('google_place_id', 'VARCHAR(255)'),
            ('wordpress_post_id', 'INTEGER')
        ]
        
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                try:
                    cur.execute(f'ALTER TABLE providers ADD COLUMN {column_name} {column_type}')
                    print(f'✅ Added column: {column_name}')
                except Exception as e:
                    print(f'❌ Error adding {column_name}: {e}')
            else:
                print(f'⏭️ Column {column_name} already exists')
        
        conn.commit()
        cur.close()
        conn.close()
        print('✅ Database migration completed successfully')
        return True
        
    except Exception as e:
        print(f'❌ Database migration failed: {e}')
        return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\n🎉 Migration complete! You can now run the automation script.")
    else:
        print("\n💥 Migration failed. Please check the error messages above.") 