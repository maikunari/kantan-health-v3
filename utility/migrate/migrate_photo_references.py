#!/usr/bin/env python3
"""
Migration: Add photo_references column to providers table
This column will store Google photo references (permanent) instead of URLs (expire)
"""

import os
import sys
import json
import re
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from src.core.database import get_postgres_config

def extract_reference_from_url(url):
    """Extract photo reference from a Google Places photo URL"""
    if not url:
        return None
    
    # Pattern to match photoreference parameter
    match = re.search(r'photoreference=([^&]+)', url)
    if match:
        return match.group(1)
    return None

def run_migration():
    """Add photo_references column and populate from existing URLs"""
    
    print("🔄 Starting photo_references migration...")
    
    # Get database connection
    config = get_postgres_config()
    engine = create_engine(f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}")
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'providers' 
            AND column_name = 'photo_references'
        """))
        
        if result.fetchone():
            print("✅ photo_references column already exists")
        else:
            # Add column
            print("📊 Adding photo_references column...")
            try:
                conn.execute(text("""
                    ALTER TABLE providers 
                    ADD COLUMN photo_references TEXT[]
                """))
                conn.commit()
                print("✅ Added photo_references column")
            except ProgrammingError as e:
                print(f"❌ Error adding column: {e}")
                return
        
        # Extract references from existing photo URLs
        print("\n🔍 Extracting photo references from existing URLs...")
        
        # Get providers with photo URLs
        providers = conn.execute(text("""
            SELECT id, provider_name, photo_urls
            FROM providers
            WHERE photo_urls IS NOT NULL
            AND photo_references IS NULL
            ORDER BY id
        """)).fetchall()
        
        print(f"📊 Found {len(providers)} providers to process")
        
        updated_count = 0
        error_count = 0
        
        for provider in providers:
            try:
                # Parse photo URLs
                photo_urls = []
                if provider.photo_urls:
                    if isinstance(provider.photo_urls, str):
                        photo_urls = json.loads(provider.photo_urls)
                    elif isinstance(provider.photo_urls, list):
                        photo_urls = provider.photo_urls
                
                # Extract references
                references = []
                for url in photo_urls:
                    ref = extract_reference_from_url(url)
                    if ref:
                        references.append(ref)
                
                if references:
                    # Update provider with references
                    conn.execute(text("""
                        UPDATE providers
                        SET photo_references = :references
                        WHERE id = :id
                    """), {
                        'id': provider.id,
                        'references': references
                    })
                    updated_count += 1
                    
                    if updated_count % 10 == 0:
                        print(f"  Processed {updated_count} providers...")
                
            except Exception as e:
                print(f"❌ Error processing provider {provider.id} ({provider.provider_name}): {e}")
                error_count += 1
        
        conn.commit()
        
        print(f"\n✅ Migration complete!")
        print(f"   - Updated: {updated_count} providers")
        print(f"   - Errors: {error_count}")
        
        # Show sample data
        print("\n📋 Sample migrated data:")
        samples = conn.execute(text("""
            SELECT id, provider_name, 
                   array_length(photo_references, 1) as ref_count,
                   photo_references[1] as first_ref
            FROM providers
            WHERE photo_references IS NOT NULL
            LIMIT 5
        """)).fetchall()
        
        for sample in samples:
            print(f"   ID {sample.id}: {sample.provider_name}")
            print(f"      References: {sample.ref_count}, First: {sample.first_ref[:50]}...")

if __name__ == "__main__":
    run_migration()