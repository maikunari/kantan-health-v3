#!/usr/bin/env python3
"""
Reset Data for Testing Script

This script allows you to selectively clear data to test the Data Quality Dashboard
and data completion functionality. Use with caution!
"""

import os
import sys
import argparse
from postgres_integration import get_postgres_config, Provider
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def get_session():
    """Get database session"""
    config = get_postgres_config()
    engine = create_engine(f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}")
    Session = sessionmaker(bind=engine)
    return Session()

def reset_ai_content(limit=None, dry_run=False):
    """Reset AI-generated content to test AI completion"""
    session = get_session()
    
    query = session.query(Provider)
    if limit:
        query = query.limit(limit)
    
    providers = query.all()
    
    print(f"{'DRY RUN: ' if dry_run else ''}Resetting AI content for {len(providers)} providers...")
    
    if not dry_run:
        for provider in providers:
            provider.ai_description = None
            provider.ai_excerpt = None
            provider.seo_title = None
            provider.seo_meta_description = None
            provider.english_experience_summary = None
            provider.review_summary = None
            provider.selected_featured_image = None
        
        session.commit()
        print(f"✅ Reset AI content for {len(providers)} providers")
    else:
        print(f"DRY RUN: Would reset AI content for {len(providers)} providers")
    
    session.close()

def reset_location_data(limit=None, dry_run=False):
    """Reset location data to test geocoding"""
    session = get_session()
    
    query = session.query(Provider)
    if limit:
        query = query.limit(limit)
    
    providers = query.all()
    
    print(f"{'DRY RUN: ' if dry_run else ''}Resetting location data for {len(providers)} providers...")
    
    if not dry_run:
        for provider in providers:
            provider.latitude = None
            provider.longitude = None
        
        session.commit()
        print(f"✅ Reset location data for {len(providers)} providers")
    else:
        print(f"DRY RUN: Would reset location data for {len(providers)} providers")
    
    session.close()

def reset_google_data(limit=None, dry_run=False):
    """Reset Google Places data to test Google API completion"""
    session = get_session()
    
    query = session.query(Provider)
    if limit:
        query = query.limit(limit)
    
    providers = query.all()
    
    print(f"{'DRY RUN: ' if dry_run else ''}Resetting Google Places data for {len(providers)} providers...")
    
    if not dry_run:
        for provider in providers:
            provider.business_hours = None
            provider.rating = None
            provider.total_reviews = None
            provider.wheelchair_accessible = None
            provider.parking_available = None
            provider.photo_urls = None
        
        session.commit()
        print(f"✅ Reset Google Places data for {len(providers)} providers")
    else:
        print(f"DRY RUN: Would reset Google Places data for {len(providers)} providers")
    
    session.close()

def reset_wordpress_data(limit=None, dry_run=False):
    """Reset WordPress sync data to test WordPress integration"""
    session = get_session()
    
    query = session.query(Provider)
    if limit:
        query = query.limit(limit)
    
    providers = query.all()
    
    print(f"{'DRY RUN: ' if dry_run else ''}Resetting WordPress data for {len(providers)} providers...")
    
    if not dry_run:
        for provider in providers:
            provider.wordpress_post_id = None
            provider.last_wordpress_sync = None
            provider.content_hash = None
            provider.wordpress_status = None
        
        session.commit()
        print(f"✅ Reset WordPress data for {len(providers)} providers")
    else:
        print(f"DRY RUN: Would reset WordPress data for {len(providers)} providers")
    
    session.close()

def show_current_completeness():
    """Show current data completeness statistics"""
    session = get_session()
    
    total = session.execute(text('SELECT COUNT(*) FROM providers')).scalar()
    
    stats = {
        'AI Content': {
            'ai_description': session.execute(text('SELECT COUNT(*) FROM providers WHERE ai_description IS NOT NULL')).scalar(),
            'seo_title': session.execute(text('SELECT COUNT(*) FROM providers WHERE seo_title IS NOT NULL')).scalar(),
            'seo_meta_description': session.execute(text('SELECT COUNT(*) FROM providers WHERE seo_meta_description IS NOT NULL')).scalar()
        },
        'Location': {
            'latitude': session.execute(text('SELECT COUNT(*) FROM providers WHERE latitude IS NOT NULL')).scalar(),
            'longitude': session.execute(text('SELECT COUNT(*) FROM providers WHERE longitude IS NOT NULL')).scalar()
        },
        'Google Data': {
            'business_hours': session.execute(text('SELECT COUNT(*) FROM providers WHERE business_hours IS NOT NULL')).scalar(),
            'rating': session.execute(text('SELECT COUNT(*) FROM providers WHERE rating IS NOT NULL')).scalar(),
            'wheelchair_accessible': session.execute(text('SELECT COUNT(*) FROM providers WHERE wheelchair_accessible IS NOT NULL')).scalar()
        },
        'WordPress': {
            'wordpress_post_id': session.execute(text('SELECT COUNT(*) FROM providers WHERE wordpress_post_id IS NOT NULL')).scalar()
        }
    }
    
    print(f"\n📊 CURRENT COMPLETENESS (Total: {total} providers)")
    print("=" * 50)
    
    for category, fields in stats.items():
        print(f"\n{category}:")
        for field, count in fields.items():
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  {field}: {count}/{total} ({percentage:.1f}%)")
    
    session.close()

def main():
    parser = argparse.ArgumentParser(description="Reset data for testing Data Quality Dashboard")
    
    parser.add_argument('--ai-content', action='store_true', help='Reset AI-generated content')
    parser.add_argument('--location', action='store_true', help='Reset location data (lat/lng)')
    parser.add_argument('--google-data', action='store_true', help='Reset Google Places data')
    parser.add_argument('--wordpress', action='store_true', help='Reset WordPress sync data')
    parser.add_argument('--all', action='store_true', help='Reset all data types')
    
    parser.add_argument('--limit', type=int, help='Limit number of providers to affect')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be reset without making changes')
    parser.add_argument('--stats', action='store_true', help='Show current completeness statistics')
    
    args = parser.parse_args()
    
    if args.stats:
        show_current_completeness()
        return
    
    if not any([args.ai_content, args.location, args.google_data, args.wordpress, args.all]):
        print("❌ Please specify what to reset or use --stats to see current completeness")
        print("Options: --ai-content, --location, --google-data, --wordpress, --all")
        sys.exit(1)
    
    print("⚠️  WARNING: This will modify your database!")
    if not args.dry_run:
        confirm = input("Are you sure you want to proceed? (type 'yes' to confirm): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
    
    if args.ai_content or args.all:
        reset_ai_content(args.limit, args.dry_run)
    
    if args.location or args.all:
        reset_location_data(args.limit, args.dry_run)
    
    if args.google_data or args.all:
        reset_google_data(args.limit, args.dry_run)
    
    if args.wordpress or args.all:
        reset_wordpress_data(args.limit, args.dry_run)
    
    if not args.dry_run:
        print("\n🎉 Reset complete! Check the Data Quality Dashboard to see the changes.")
        print("💡 You can now test the data completion functions.")

if __name__ == "__main__":
    main()