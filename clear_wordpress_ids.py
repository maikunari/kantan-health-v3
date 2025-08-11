#!/usr/bin/env python3
"""
Clear WordPress Post IDs
Clears wordpress_post_id for providers so they can be republished
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from src.core.database import get_postgres_config

# Get database connection
config = get_postgres_config()
engine = create_engine(f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}")
Session = sessionmaker(bind=engine)
session = Session()

# Find providers with WordPress IDs that need clearing
print("🔍 Finding providers with WordPress post IDs...")
providers = session.execute(text("""
    SELECT id, provider_name, wordpress_post_id 
    FROM providers 
    WHERE wordpress_post_id IS NOT NULL 
    AND ai_description IS NOT NULL
    ORDER BY id DESC
    LIMIT 20
""")).fetchall()

print(f"\n📊 Found {len(providers)} providers with WordPress posts:")
for p in providers:
    print(f"   ID {p.id}: {p.provider_name} (WP ID: {p.wordpress_post_id})")

# Ask for confirmation
response = input("\n⚠️  Clear WordPress IDs for these providers? (yes/no): ")
if response.lower() != 'yes':
    print("Cancelled.")
    sys.exit(0)

# Clear the WordPress IDs
provider_ids = [p.id for p in providers]
result = session.execute(text("""
    UPDATE providers 
    SET wordpress_post_id = NULL, 
        last_wordpress_sync = NULL,
        content_hash = NULL
    WHERE id = ANY(:ids)
"""), {'ids': provider_ids})

session.commit()
print(f"\n✅ Cleared WordPress IDs for {result.rowcount} providers")
session.close()