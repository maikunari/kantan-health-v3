#!/usr/bin/env python3
"""
Database Migration: Add Provider Fingerprints
Adds fingerprint columns and indexes for reliable deduplication
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, String, Index
from sqlalchemy.orm import sessionmaker
from postgres_integration import PostgresIntegration, Provider, Base

def add_fingerprint_columns():
    """Add fingerprint columns to providers table"""
    print("🔄 Adding fingerprint columns to providers table...")
    
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
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'providers' 
                AND column_name IN ('primary_fingerprint', 'secondary_fingerprint', 'fuzzy_fingerprint')
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            
            if 'primary_fingerprint' in existing_columns:
                print("✅ Fingerprint columns already exist, skipping column creation")
            else:
                print("📝 Adding fingerprint columns...")
                
                # Add fingerprint columns
                conn.execute(text("""
                    ALTER TABLE providers 
                    ADD COLUMN primary_fingerprint VARCHAR(32),
                    ADD COLUMN secondary_fingerprint VARCHAR(32),
                    ADD COLUMN fuzzy_fingerprint VARCHAR(32)
                """))
                
                print("✅ Successfully added fingerprint columns")
            
            # Create indexes for fast duplicate checking
            print("📇 Creating indexes for fingerprints...")
            
            indexes_to_create = [
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_providers_primary_fingerprint ON providers(primary_fingerprint)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_providers_secondary_fingerprint ON providers(secondary_fingerprint) WHERE secondary_fingerprint IS NOT NULL",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_providers_fuzzy_fingerprint ON providers(fuzzy_fingerprint)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_providers_google_place_id ON providers(google_place_id) WHERE google_place_id IS NOT NULL"
            ]
            
            for index_sql in indexes_to_create:
                try:
                    conn.execute(text(index_sql))
                    print(f"✅ Created index")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"⏭️ Index already exists")
                    else:
                        print(f"⚠️ Error creating index: {e}")
            
            # Commit the transaction
            conn.commit()
            
            print("✅ Database migration completed successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        return False

def update_provider_fingerprints():
    """Update existing providers with fingerprints"""
    print("\n🔄 Updating existing providers with fingerprints...")
    
    from provider_fingerprinting import ProviderFingerprinter
    
    postgres = PostgresIntegration()
    session = postgres.Session()
    fingerprinter = ProviderFingerprinter()
    
    try:
        # Get all providers without fingerprints
        providers = session.query(Provider).filter(
            Provider.primary_fingerprint.is_(None)
        ).all()
        
        print(f"📊 Found {len(providers)} providers needing fingerprints")
        
        updated_count = 0
        error_count = 0
        
        for provider in providers:
            try:
                # Convert provider to dict for fingerprinting
                provider_data = {
                    'provider_name': provider.provider_name,
                    'address': provider.address or '',
                    'city': provider.city or '',
                    'phone': provider.phone or '',
                    'google_place_id': provider.google_place_id
                }
                
                # Generate fingerprints
                fingerprints = fingerprinter.generate_all_fingerprints(provider_data)
                
                # Update provider
                provider.primary_fingerprint = fingerprints.primary
                provider.secondary_fingerprint = fingerprints.secondary if fingerprints.secondary else None
                provider.fuzzy_fingerprint = fingerprints.fuzzy
                
                updated_count += 1
                
                if updated_count % 50 == 0:
                    session.commit()
                    print(f"   ✅ Updated {updated_count} providers...")
                    
            except Exception as e:
                print(f"   ❌ Error updating {provider.provider_name}: {str(e)}")
                error_count += 1
                session.rollback()
        
        # Final commit
        session.commit()
        
        print(f"📊 Fingerprint update complete:")
        print(f"   ✅ Updated: {updated_count}")
        print(f"   ❌ Errors: {error_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating fingerprints: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()

def detect_existing_duplicates():
    """Detect existing duplicates using new fingerprinting system"""
    print("\n🔍 Detecting existing duplicates using fingerprints...")
    
    postgres = PostgresIntegration()
    session = postgres.Session()
    
    try:
        # Find duplicates by primary fingerprint
        result = session.execute(text("""
            SELECT primary_fingerprint, COUNT(*) as count, 
                   STRING_AGG(provider_name, ', ') as names
            FROM providers 
            WHERE primary_fingerprint IS NOT NULL
            GROUP BY primary_fingerprint 
            HAVING COUNT(*) > 1 
            ORDER BY count DESC
        """))
        
        primary_duplicates = result.fetchall()
        
        # Find duplicates by secondary fingerprint
        result = session.execute(text("""
            SELECT secondary_fingerprint, COUNT(*) as count,
                   STRING_AGG(provider_name, ', ') as names
            FROM providers 
            WHERE secondary_fingerprint IS NOT NULL
            GROUP BY secondary_fingerprint 
            HAVING COUNT(*) > 1 
            ORDER BY count DESC
        """))
        
        secondary_duplicates = result.fetchall()
        
        print(f"📊 Duplicate Detection Results:")
        print(f"   Primary fingerprint duplicates: {len(primary_duplicates)} groups")
        print(f"   Secondary fingerprint duplicates: {len(secondary_duplicates)} groups")
        
        if primary_duplicates:
            print(f"\n🔍 Top primary fingerprint duplicates:")
            for fp, count, names in primary_duplicates[:5]:
                print(f"   {count} duplicates: {names[:100]}...")
        
        return {
            'primary_duplicates': len(primary_duplicates),
            'secondary_duplicates': len(secondary_duplicates)
        }
        
    except Exception as e:
        print(f"❌ Error detecting duplicates: {str(e)}")
        return None
    finally:
        session.close()

if __name__ == "__main__":
    print("🏗️  PROVIDER FINGERPRINTING DATABASE MIGRATION")
    print("=" * 60)
    
    # Step 1: Add columns and indexes
    if add_fingerprint_columns():
        
        # Step 2: Update existing providers
        if update_provider_fingerprints():
            
            # Step 3: Detect duplicates
            duplicate_stats = detect_existing_duplicates()
            
            print(f"\n🎉 Migration completed successfully!")
            if duplicate_stats:
                print(f"📊 Found {duplicate_stats['primary_duplicates']} primary duplicate groups")
                print(f"📊 Found {duplicate_stats['secondary_duplicates']} secondary duplicate groups")
        else:
            print("❌ Failed to update provider fingerprints")
    else:
        print("❌ Failed to add fingerprint columns") 