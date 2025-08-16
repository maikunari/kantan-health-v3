#!/usr/bin/env python3
"""
Database migration to add geographic hierarchy fields
Adds prefecture, ward, neighborhood, and postal_code fields to providers table
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def add_geographic_hierarchy():
    """Add geographic hierarchy fields to providers table"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'database': os.getenv('POSTGRES_DB', 'directory'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', '')
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        print("🔍 Checking current table structure...")
        
        # Check which columns already exist
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'providers' 
            AND column_name IN ('prefecture', 'ward', 'neighborhood', 'postal_code')
        """)
        existing_columns = [row[0] for row in cur.fetchall()]
        
        columns_to_add = []
        
        # Define columns to add if they don't exist
        if 'prefecture' not in existing_columns:
            columns_to_add.append(('prefecture', 'VARCHAR(100)'))
            
        if 'ward' not in existing_columns:
            columns_to_add.append(('ward', 'VARCHAR(100)'))
            
        if 'neighborhood' not in existing_columns:
            columns_to_add.append(('neighborhood', 'VARCHAR(200)'))
            
        if 'postal_code' not in existing_columns:
            columns_to_add.append(('postal_code', 'VARCHAR(20)'))
        
        if not columns_to_add:
            print("✅ All geographic hierarchy columns already exist")
            return
        
        # Add missing columns
        for column_name, column_type in columns_to_add:
            print(f"➕ Adding column: {column_name} ({column_type})")
            cur.execute(sql.SQL("""
                ALTER TABLE providers 
                ADD COLUMN IF NOT EXISTS {} {}
            """).format(
                sql.Identifier(column_name),
                sql.SQL(column_type)
            ))
        
        # Create indexes for better query performance
        print("📍 Creating geographic indexes...")
        
        # Index for prefecture queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_providers_prefecture 
            ON providers(prefecture) 
            WHERE prefecture IS NOT NULL
        """)
        
        # Index for ward queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_providers_ward 
            ON providers(ward) 
            WHERE ward IS NOT NULL
        """)
        
        # Composite index for location queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_providers_location 
            ON providers(prefecture, city, ward) 
            WHERE prefecture IS NOT NULL
        """)
        
        # Index for postal code
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_providers_postal 
            ON providers(postal_code) 
            WHERE postal_code IS NOT NULL
        """)
        
        # Commit changes
        conn.commit()
        print("✅ Geographic hierarchy columns added successfully")
        
        # Show current structure
        print("\n📊 Current geographic fields:")
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'providers'
            AND column_name IN ('prefecture', 'city', 'district', 'ward', 'neighborhood', 'postal_code')
            ORDER BY column_name
        """)
        
        for row in cur.fetchall():
            print(f"  - {row[0]}: {row[1]}({row[2]})")
        
        # Get sample data to show current state
        print("\n📍 Sample geographic data:")
        cur.execute("""
            SELECT DISTINCT city, prefecture, ward
            FROM providers
            WHERE city IS NOT NULL
            LIMIT 10
        """)
        
        for row in cur.fetchall():
            print(f"  - City: {row[0]}, Prefecture: {row[1]}, Ward: {row[2]}")
        
        # Close connection
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


def populate_tokyo_wards():
    """Populate ward field for Tokyo providers based on district or address"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'database': os.getenv('POSTGRES_DB', 'directory'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', '')
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        print("\n🔄 Populating ward data for Tokyo providers...")
        
        # Tokyo ward mappings
        tokyo_wards = [
            "Chiyoda", "Chuo", "Minato", "Shinjuku", "Bunkyo",
            "Taito", "Sumida", "Koto", "Shinagawa", "Meguro",
            "Ota", "Setagaya", "Shibuya", "Nakano", "Suginami",
            "Toshima", "Kita", "Arakawa", "Itabashi", "Nerima",
            "Adachi", "Katsushika", "Edogawa"
        ]
        
        updated_count = 0
        
        for ward in tokyo_wards:
            # Update based on address containing ward name
            cur.execute("""
                UPDATE providers 
                SET ward = %s, prefecture = 'Tokyo'
                WHERE (city = 'Tokyo' OR city ILIKE %s)
                AND ward IS NULL
                AND (
                    address ILIKE %s 
                    OR district ILIKE %s
                )
            """, (ward, '%tokyo%', f'%{ward}%', f'%{ward}%'))
            
            updated_count += cur.rowcount
        
        # Set prefecture for all Tokyo providers
        cur.execute("""
            UPDATE providers 
            SET prefecture = 'Tokyo'
            WHERE city = 'Tokyo' 
            AND prefecture IS NULL
        """)
        
        conn.commit()
        print(f"✅ Updated {updated_count} providers with ward information")
        
        # Show ward distribution
        print("\n📊 Tokyo ward distribution:")
        cur.execute("""
            SELECT ward, COUNT(*) as count
            FROM providers
            WHERE city = 'Tokyo' AND ward IS NOT NULL
            GROUP BY ward
            ORDER BY count DESC
            LIMIT 10
        """)
        
        for row in cur.fetchall():
            print(f"  - {row[0]}: {row[1]} providers")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error populating wards: {str(e)}")


if __name__ == "__main__":
    print("🚀 Geographic Hierarchy Migration")
    print("=" * 50)
    print(f"Started: {datetime.now()}")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('config/.env')
    
    # Run migration
    add_geographic_hierarchy()
    
    # Populate ward data
    populate_tokyo_wards()
    
    print("\n" + "=" * 50)
    print(f"Completed: {datetime.now()}")
    print("✅ Migration complete!")