#!/usr/bin/env python3
"""
Database Migration: WordPress Sync Enhancement
Adds wordpress_sync_log table and enhances provider table for bidirectional sync tracking
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, Integer, String, Text, DateTime, TIMESTAMP, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from postgres_integration import PostgresIntegration, Provider

Base = declarative_base()

class WordPressSyncLog(Base):
    """Model for WordPress sync logging table"""
    __tablename__ = "wordpress_sync_log"
    
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, nullable=False)  # Foreign key to providers
    wordpress_post_id = Column(Integer)
    sync_type = Column(String(50), nullable=False)  # 'create', 'update', 'delete'
    sync_status = Column(String(20), nullable=False)  # 'success', 'failed', 'pending'
    content_hash = Column(String(64))  # SHA256 of synced content
    sync_timestamp = Column(TIMESTAMP, default=datetime.now)
    error_message = Column(Text)
    sync_duration_ms = Column(Integer)
    sync_metadata = Column(JSONB)  # Additional sync metadata

def create_wordpress_sync_log_table():
    """Create the wordpress_sync_log table"""
    print("🔄 Creating wordpress_sync_log table...")
    
    # Load environment variables
    config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    load_dotenv(config_path)
    
    # Create database connection
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "password")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_name = os.getenv("POSTGRES_DB", "directory")
    
    engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}")
    
    try:
        # Check if table already exists
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'wordpress_sync_log'
                );
            """))
            
            table_exists = result.scalar()
            
            if table_exists:
                print("✅ wordpress_sync_log table already exists")
                return True
            
            # Create the table
            conn.execute(text("""
                CREATE TABLE wordpress_sync_log (
                    id SERIAL PRIMARY KEY,
                    provider_id INTEGER NOT NULL,
                    wordpress_post_id INTEGER,
                    sync_type VARCHAR(50) NOT NULL,
                    sync_status VARCHAR(20) NOT NULL,
                    content_hash VARCHAR(64),
                    sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT,
                    sync_duration_ms INTEGER,
                    sync_metadata JSONB,
                    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE
                );
            """))
            
            # Create indexes for performance
            conn.execute(text("""
                CREATE INDEX idx_sync_log_provider ON wordpress_sync_log(provider_id);
                CREATE INDEX idx_sync_log_timestamp ON wordpress_sync_log(sync_timestamp);
                CREATE INDEX idx_sync_log_status ON wordpress_sync_log(sync_status);
                CREATE INDEX idx_sync_log_type ON wordpress_sync_log(sync_type);
            """))
            
            conn.commit()
            print("✅ wordpress_sync_log table created successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error creating wordpress_sync_log table: {str(e)}")
        return False

def add_provider_sync_columns():
    """Add sync tracking columns to providers table"""
    print("🔄 Adding sync tracking columns to providers table...")
    
    # Load environment variables
    config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    load_dotenv(config_path)
    
    # Create database connection
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "password")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_name = os.getenv("POSTGRES_DB", "directory")
    
    engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}")
    
    columns_to_add = [
        ("last_wordpress_sync", "TIMESTAMP"),
        ("content_hash", "VARCHAR(64)"),
        ("wordpress_status", "VARCHAR(20) DEFAULT 'pending'")
    ]
    
    try:
        with engine.connect() as conn:
            for column_name, column_type in columns_to_add:
                # Check if column already exists
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'providers'
                        AND column_name = :column_name
                    );
                """), {"column_name": column_name})
                
                column_exists = result.scalar()
                
                if column_exists:
                    print(f"✅ Column '{column_name}' already exists")
                    continue
                
                # Add the column
                conn.execute(text(f"""
                    ALTER TABLE providers ADD COLUMN {column_name} {column_type};
                """))
                
                print(f"✅ Added column: {column_name} ({column_type})")
            
            # Create indexes for performance
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_providers_sync_status ON providers(wordpress_status);
                CREATE INDEX IF NOT EXISTS idx_providers_last_sync ON providers(last_wordpress_sync);
                CREATE INDEX IF NOT EXISTS idx_providers_content_hash ON providers(content_hash);
            """))
            
            conn.commit()
            print("✅ Provider sync columns added successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error adding provider sync columns: {str(e)}")
        return False

def update_existing_provider_status():
    """Update existing providers with appropriate WordPress status"""
    print("🔄 Updating existing providers with WordPress status...")
    
    postgres = PostgresIntegration()
    session = postgres.Session()
    
    try:
        # Update providers that have WordPress post IDs
        published_count = session.query(Provider).filter(
            Provider.wordpress_post_id.isnot(None),
            Provider.wordpress_status.is_(None)
        ).update({
            Provider.wordpress_status: 'published'
        }, synchronize_session=False)
        
        # Update providers that have descriptions but no WordPress post ID
        ready_count = session.query(Provider).filter(
            Provider.ai_description.isnot(None),
            Provider.wordpress_post_id.is_(None),
            Provider.wordpress_status.is_(None)
        ).update({
            Provider.wordpress_status: 'ready'
        }, synchronize_session=False)
        
        # Update providers that are still pending
        pending_count = session.query(Provider).filter(
            Provider.wordpress_status.is_(None)
        ).update({
            Provider.wordpress_status: 'pending'
        }, synchronize_session=False)
        
        session.commit()
        
        print(f"✅ Updated provider statuses:")
        print(f"   📝 Published: {published_count}")
        print(f"   🎯 Ready: {ready_count}")
        print(f"   ⏳ Pending: {pending_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating provider statuses: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()

def verify_migration():
    """Verify that the migration was successful"""
    print("🔍 Verifying migration...")
    
    postgres = PostgresIntegration()
    session = postgres.Session()
    
    try:
        # Check wordpress_sync_log table
        sync_log_count = session.execute(text("SELECT COUNT(*) FROM wordpress_sync_log")).scalar()
        print(f"✅ wordpress_sync_log table accessible (0 records)")
        
        # Check provider table columns
        provider_count = session.query(Provider).count()
        providers_with_status = session.query(Provider).filter(
            Provider.wordpress_status.isnot(None)
        ).count()
        
        print(f"✅ Provider table enhanced:")
        print(f"   📊 Total providers: {provider_count}")
        print(f"   🎯 Providers with WordPress status: {providers_with_status}")
        
        # Check status distribution
        status_counts = session.execute(text("""
            SELECT wordpress_status, COUNT(*) as count
            FROM providers 
            WHERE wordpress_status IS NOT NULL
            GROUP BY wordpress_status
        """)).fetchall()
        
        print(f"✅ WordPress status distribution:")
        for status, count in status_counts:
            print(f"   {status}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration verification failed: {str(e)}")
        return False
    finally:
        session.close()

def main():
    """Run the WordPress sync enhancement migration"""
    print("🚀 Starting WordPress Sync Enhancement Migration...")
    print("=" * 60)
    
    # Step 1: Create wordpress_sync_log table
    if not create_wordpress_sync_log_table():
        print("❌ Failed to create wordpress_sync_log table")
        sys.exit(1)
    
    # Step 2: Add sync columns to providers table
    if not add_provider_sync_columns():
        print("❌ Failed to add provider sync columns")
        sys.exit(1)
    
    # Step 3: Update existing provider statuses
    if not update_existing_provider_status():
        print("❌ Failed to update provider statuses")
        sys.exit(1)
    
    # Step 4: Verify migration
    if not verify_migration():
        print("❌ Migration verification failed")
        sys.exit(1)
    
    print("=" * 60)
    print("✅ WordPress Sync Enhancement Migration Complete!")
    print("🎯 Ready to implement bidirectional sync functionality")

if __name__ == "__main__":
    main() 