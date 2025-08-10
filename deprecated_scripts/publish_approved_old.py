#!/usr/bin/env python3
"""
Publish Approved Providers to WordPress
Syncs providers with status='approved' from PostgreSQL to WordPress CPTs.
INCLUDES DUPLICATE PREVENTION: Only creates WordPress posts for providers without existing wordpress_post_id
"""

from wordpress_sync import WordPressHealthcareSync
from postgres_integration import Provider, get_postgres_config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use proper database configuration
config = get_postgres_config()
engine = create_engine(f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}")
Session = sessionmaker(bind=engine)
session = Session()

# DUPLICATE PREVENTION: Only get approved providers WITHOUT wordpress_post_id
providers = session.query(Provider).filter(
    Provider.status == "approved",
    Provider.wordpress_post_id.is_(None)  # Only providers not yet published to WordPress
).limit(50).all()

print(f"🔍 Found {len(providers)} approved providers without WordPress posts")

if not providers:
    print("✅ No approved providers need WordPress publishing")
    session.close()
    exit(0)

sync = WordPressHealthcareSync()
created_count = 0
failed_count = 0

for provider in providers:
    try:
        print(f"\n📝 Creating WordPress post for: {provider.provider_name}")
        
        # Double-check the provider doesn't have a WordPress post ID
        if provider.wordpress_post_id:
            print(f"⏭️ Skipping {provider.provider_name}: Already has WordPress post ID {provider.wordpress_post_id}")
            continue
        
        # Create WordPress post
        wordpress_post_id = sync.create_wordpress_post(provider.__dict__)
        
        if wordpress_post_id:
            # Update provider with WordPress post ID and published status
            provider.wordpress_post_id = wordpress_post_id
            provider.status = "published"
            session.commit()
            
            print(f"✅ Created WordPress post {wordpress_post_id} for {provider.provider_name}")
            created_count += 1
        else:
            print(f"❌ Failed to create WordPress post for {provider.provider_name}")
            failed_count += 1
            
    except Exception as e:
        print(f"❌ Error processing {provider.provider_name}: {str(e)}")
        failed_count += 1
        session.rollback()

session.close()

print(f"\n📊 PUBLISHING SUMMARY:")
print(f"   ✅ Created: {created_count} WordPress posts")
print(f"   ❌ Failed: {failed_count} attempts")
print(f"   🛡️ Duplicates prevented by checking existing wordpress_post_id")

if created_count > 0:
    print(f"\n💡 Next steps:")
    print(f"   - Check WordPress admin for the {created_count} new posts")
    print(f"   - Verify posts display correctly with ACF fields")
    print(f"   - Run WordPress sync to update any content changes")