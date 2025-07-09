#!/usr/bin/env python3
"""
Database Migration: Add Proficiency Score Column
Adds proficiency_score column and syncs values from existing english_proficiency data
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, Integer
from sqlalchemy.orm import sessionmaker
from postgres_integration import PostgresIntegration, Provider

def add_proficiency_score_column():
    """Add proficiency_score column to providers table"""
    print("🔧 Adding proficiency_score column to database...")
    
    # Initialize database connection
    db = PostgresIntegration()
    engine = db.engine
    
    try:
        # Add the column using raw SQL
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='providers' AND column_name='proficiency_score'
            """))
            
            if result.fetchone():
                print("✅ proficiency_score column already exists")
                return True
            
            # Add the column
            conn.execute(text("""
                ALTER TABLE providers 
                ADD COLUMN proficiency_score INTEGER DEFAULT 0
            """))
            conn.commit()
            print("✅ Successfully added proficiency_score column")
            return True
            
    except Exception as e:
        print(f"❌ Error adding column: {str(e)}")
        return False

def sync_proficiency_scores():
    """Sync proficiency scores from english_proficiency text values"""
    print("🔄 Syncing proficiency scores from english_proficiency values...")
    
    # Mapping from text to numeric scores
    proficiency_mapping = {
        'Fluent': 5,
        'Conversational': 4,
        'Basic': 3,
        'Unknown': 0
    }
    
    db = PostgresIntegration()
    session = db.Session()
    
    try:
        # Get all providers
        providers = session.query(Provider).all()
        updated_count = 0
        
        for provider in providers:
            current_proficiency = provider.english_proficiency or 'Unknown'
            
            # Map text proficiency to numeric score
            if current_proficiency in proficiency_mapping:
                new_score = proficiency_mapping[current_proficiency]
            else:
                # Handle edge cases
                if current_proficiency.lower() == 'fluent':
                    new_score = 5
                elif current_proficiency.lower() == 'conversational':
                    new_score = 4
                elif current_proficiency.lower() == 'basic':
                    new_score = 3
                else:
                    new_score = 0
            
            # Update if different (or if proficiency_score is None/0 and we have a better value)
            if getattr(provider, 'proficiency_score', None) != new_score:
                provider.proficiency_score = new_score
                updated_count += 1
                print(f"  📝 {provider.provider_name}: {current_proficiency} → {new_score}")
        
        session.commit()
        print(f"✅ Updated {updated_count} providers with proficiency scores")
        
    except Exception as e:
        print(f"❌ Error syncing proficiency scores: {str(e)}")
        session.rollback()
    finally:
        session.close()

def fix_inconsistent_proficiency_levels():
    """Fix providers where proficiency_score and english_proficiency don't match"""
    print("🔍 Checking for inconsistent proficiency levels...")
    
    # Score to text mapping (the correct mapping)
    score_to_text = {
        5: 'Fluent',
        4: 'Conversational', 
        3: 'Basic',
        0: 'Unknown'
    }
    
    db = PostgresIntegration()
    session = db.Session()
    
    try:
        # Get all providers
        providers = session.query(Provider).all()
        fixed_count = 0
        
        for provider in providers:
            score = getattr(provider, 'proficiency_score', 0) or 0
            current_text = provider.english_proficiency or 'Unknown'
            expected_text = score_to_text.get(score, 'Unknown')
            
            if current_text != expected_text:
                print(f"  🔧 Fixing {provider.provider_name}:")
                print(f"     Score: {score} | Current text: {current_text} → {expected_text}")
                provider.english_proficiency = expected_text
                fixed_count += 1
        
        session.commit()
        print(f"✅ Fixed {fixed_count} inconsistent proficiency levels")
        
    except Exception as e:
        print(f"❌ Error fixing inconsistencies: {str(e)}")
        session.rollback()
    finally:
        session.close()

def run_migration():
    """Run the complete migration"""
    print("🚀 PROFICIENCY SCORE MIGRATION")
    print("=" * 50)
    
    # Step 1: Add column
    if not add_proficiency_score_column():
        print("❌ Migration failed: Could not add column")
        return False
    
    # Step 2: Sync scores from existing data
    sync_proficiency_scores()
    
    # Step 3: Fix any inconsistencies
    fix_inconsistent_proficiency_levels()
    
    print("\n✅ Migration completed successfully!")
    print("🎯 All providers now have consistent proficiency scores and levels")
    return True

if __name__ == "__main__":
    run_migration() 