#!/usr/bin/env python3
"""
Database migration to add business_hours column to providers table
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def migrate_add_business_hours():
    """Add business_hours column to providers table"""
    print("🔄 Adding business_hours column to providers table...")
    
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
            # First, check if the column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'providers' 
                AND column_name = 'business_hours'
            """))
            
            if result.fetchone():
                print("✅ business_hours column already exists, skipping migration")
                return True
            
            # Add the business_hours column
            conn.execute(text("""
                ALTER TABLE providers 
                ADD COLUMN business_hours JSON
            """))
            
            # Commit the transaction
            conn.commit()
            
            print("✅ Successfully added business_hours column to providers table")
            return True
            
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Running Database Migration")
    print("=" * 50)
    
    success = migrate_add_business_hours()
    
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("❌ Migration failed!") 