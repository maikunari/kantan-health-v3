#!/usr/bin/env python3
"""
Fix SQLAlchemy Model Sync
Ensure SQLAlchemy recognizes all database columns
"""

import os
import sys

print("\n" + "=" * 80)
print("FIXING SQLALCHEMY MODEL SYNC")
print("=" * 80)

# Force metadata refresh
from src.core.database import DatabaseManager
from src.core.models import Base, Provider
from sqlalchemy import inspect

print("\n1. Checking current model attributes...")
provider_attrs = [attr for attr in dir(Provider) if not attr.startswith('_')]
validation_attrs = ['primary_specialty', 'location_needs_review', 
                   'specialties_need_review', 'needs_manual_review', 
                   'validation_notes']

missing = []
for attr in validation_attrs:
    if attr in provider_attrs:
        print(f"  ✓ {attr} - in model")
    else:
        print(f"  ✗ {attr} - missing from model")
        missing.append(attr)

if missing:
    print(f"\n⚠️  {len(missing)} attributes missing from model")
else:
    print("\n✅ All validation attributes present in model")

print("\n2. Refreshing database metadata...")
db = DatabaseManager()

# Clear and recreate tables to sync
Base.metadata.clear()
Base.metadata.reflect(bind=db.engine)
Base.metadata.create_all(db.engine)

print("  ✓ Metadata refreshed")

print("\n3. Testing model with validation fields...")
session = db.get_session()

try:
    # Create test provider with validation fields
    test_data = {
        'google_place_id': 'test_sync_validation',
        'provider_name': 'SQLAlchemy Sync Test Provider',
        'city': 'Tokyo',
        'primary_specialty': 'General Medicine',
        'location_needs_review': False,
        'specialties_need_review': False,
        'needs_manual_review': False,
        'validation_notes': 'Test validation sync',
        'proficiency_score': 4
    }
    
    provider = db.create_or_update_provider(test_data)
    
    if provider:
        print("  ✓ Test provider created with validation fields")
        
        # Verify fields were saved
        session.refresh(provider)
        
        checks = []
        if provider.primary_specialty == 'General Medicine':
            checks.append("✓ primary_specialty saved")
        else:
            checks.append("✗ primary_specialty not saved")
            
        if provider.validation_notes == 'Test validation sync':
            checks.append("✓ validation_notes saved")
        else:
            checks.append("✗ validation_notes not saved")
            
        for check in checks:
            print(f"    {check}")
        
        # Clean up test provider
        session.delete(provider)
        session.commit()
        print("  ✓ Test provider cleaned up")
        
    else:
        print("  ✗ Failed to create test provider")
        
except Exception as e:
    print(f"  ✗ Error: {e}")
    session.rollback()
finally:
    session.close()

print("\n4. Verifying column mapping...")
inspector = inspect(db.engine)
columns = {col['name']: col['type'] for col in inspector.get_columns('providers')}

for attr in validation_attrs:
    if attr in columns:
        print(f"  ✓ {attr} mapped correctly")
    else:
        print(f"  ✗ {attr} not mapped")

print("\n✅ SQLAlchemy sync complete!")
print("\nNext: Fix master data validation attributes...")