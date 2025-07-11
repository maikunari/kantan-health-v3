#!/usr/bin/env python3
"""
Migration script to add selected_featured_image column to Provider table
For Claude Vision API image selection feature
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def load_environment():
    """Load environment variables from config/.env"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', '.env')
    load_dotenv(config_path)
    
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', ''),
        'database': 'directory'
    }

def migrate_add_selected_featured_image():
    """Add selected_featured_image column to Provider table"""
    try:
        # Load database configuration
        config = load_environment()
        
        # Connect to PostgreSQL
        print("🔗 Connecting to PostgreSQL database...")
        conn = psycopg2.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if column already exists
        print("🔍 Checking if selected_featured_image column exists...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'providers' 
            AND column_name = 'selected_featured_image'
        """)
        
        if cursor.fetchone():
            print("✅ Column 'selected_featured_image' already exists")
            return True
        
        # Add the column
        print("➕ Adding selected_featured_image column...")
        cursor.execute("""
            ALTER TABLE providers 
            ADD COLUMN selected_featured_image TEXT;
        """)
        
        # Add comment to the column
        cursor.execute("""
            COMMENT ON COLUMN providers.selected_featured_image 
            IS 'Claude Vision API selected best photo URL for featured image';
        """)
        
        print("✅ Successfully added selected_featured_image column")
        
        # Verify the column was added
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'providers' 
            AND column_name = 'selected_featured_image'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"🔍 Column verification: {result[0]} ({result[1]}, nullable: {result[2]})")
        
        # Get table statistics
        cursor.execute("SELECT COUNT(*) FROM providers")
        total_providers = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM providers 
            WHERE selected_featured_image IS NOT NULL 
            AND selected_featured_image != ''
        """)
        providers_with_selected_image = cursor.fetchone()[0]
        
        print(f"📊 Database statistics:")
        print(f"   Total providers: {total_providers}")
        print(f"   Providers with selected featured image: {providers_with_selected_image}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 SELECTED FEATURED IMAGE MIGRATION")
    print("=" * 50)
    
    success = migrate_add_selected_featured_image()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("   ✅ selected_featured_image column added to providers table")
        print("   🎨 Ready for Claude Vision API image selection")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1) 