#!/usr/bin/env python3
"""
Database migration to add wheelchair_accessible and parking_available columns to providers table
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def migrate_add_accessibility_parking():
    """Add wheelchair_accessible and parking_available columns to providers table"""
    print("🔄 Adding accessibility and parking columns to providers table...")
    
    # Load environment variables
    config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    load_dotenv(config_path)
    
    # Create database connection
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "password")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    
    engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:5432/directory")
    
    try:
        with engine.connect() as conn:
            # Check if wheelchair_accessible column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'providers' 
                AND column_name = 'wheelchair_accessible'
            """))
            
            if not result.fetchone():
                # Add wheelchair_accessible column
                conn.execute(text("""
                    ALTER TABLE providers 
                    ADD COLUMN wheelchair_accessible VARCHAR(50)
                """))
                print("✅ Added wheelchair_accessible column")
            else:
                print("✅ wheelchair_accessible column already exists")
            
            # Check if parking_available column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'providers' 
                AND column_name = 'parking_available'
            """))
            
            if not result.fetchone():
                # Add parking_available column
                conn.execute(text("""
                    ALTER TABLE providers 
                    ADD COLUMN parking_available VARCHAR(50)
                """))
                print("✅ Added parking_available column")
            else:
                print("✅ parking_available column already exists")
            
            # Commit the transaction
            conn.commit()
            
            print("✅ Successfully added accessibility and parking columns")
            return True
            
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Running Accessibility & Parking Migration")
    print("=" * 50)
    
    success = migrate_add_accessibility_parking()
    
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("❌ Migration failed!") 