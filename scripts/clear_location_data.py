#!/usr/bin/env python3
"""
Clear both cache and database entries for a specific location
WARNING: This will DELETE provider data from the database!
"""

import sys
import os
import sqlite3
import logging
from typing import List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.core.models import Provider

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clear_cache_for_location(location: str) -> int:
    """Clear cache entries for a specific location"""
    db_path = 'cache/google_places_cache.db'
    
    with sqlite3.connect(db_path) as conn:
        # Delete cache entries
        result = conn.execute('''
            DELETE FROM place_cache 
            WHERE place_id LIKE ? 
               OR CAST(data AS TEXT) LIKE ?
        ''', (f'%{location}%', f'%{location}%'))
        
        deleted = result.rowcount
        conn.commit()
        
        if deleted > 0:
            logger.info(f"✅ Deleted {deleted} cache entries for '{location}'")
        return deleted


def clear_database_providers(location: str) -> int:
    """Clear provider records from database for a specific location"""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Find providers matching the location
        providers = session.query(Provider).filter(
            (Provider.city.ilike(f'%{location}%')) |
            (Provider.state.ilike(f'%{location}%')) |
            (Provider.formatted_address.ilike(f'%{location}%'))
        ).all()
        
        if not providers:
            logger.info(f"No database providers found for location: {location}")
            return 0
        
        logger.info(f"Found {len(providers)} providers in database for '{location}'")
        
        # Show what will be deleted
        for i, provider in enumerate(providers[:3]):
            logger.info(f"  Sample {i+1}: {provider.provider_name} ({provider.city})")
        
        if len(providers) > 3:
            logger.info(f"  ... and {len(providers) - 3} more")
        
        # Get place IDs for processed_places cleanup
        place_ids = [p.place_id for p in providers]
        
        # Delete providers
        for provider in providers:
            session.delete(provider)
        
        # Also clear from processed_places cache
        if place_ids:
            with sqlite3.connect('cache/google_places_cache.db') as conn:
                placeholders = ','.join('?' * len(place_ids))
                conn.execute(f'''
                    DELETE FROM processed_places 
                    WHERE place_id IN ({placeholders})
                ''', place_ids)
                conn.commit()
                logger.info(f"✅ Cleared {len(place_ids)} entries from processed_places")
        
        session.commit()
        logger.info(f"✅ Deleted {len(providers)} providers from database")
        return len(providers)
        
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        session.rollback()
        return 0
    finally:
        session.close()


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clear cache and database for specific location')
    parser.add_argument('location', type=str, help='Location to clear (e.g., Tokyo, Nagoya)')
    parser.add_argument('--cache-only', action='store_true', help='Only clear cache, not database')
    parser.add_argument('--database-only', action='store_true', help='Only clear database, not cache')
    
    args = parser.parse_args()
    
    if args.database_only:
        # Only clear database
        db_count = clear_database_providers(args.location)
        logger.info(f"\n📊 Summary: Cleared {db_count} providers from database")
    elif args.cache_only:
        # Only clear cache
        cache_count = clear_cache_for_location(args.location)
        logger.info(f"\n📊 Summary: Cleared {cache_count} cache entries")
    else:
        # Clear both (with confirmation for database)
        response = input(f"⚠️  This will DELETE all {args.location} providers from the database. Continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Operation cancelled")
            return 0
        
        cache_count = clear_cache_for_location(args.location)
        db_count = clear_database_providers(args.location)
        
        logger.info(f"\n📊 Summary:")
        logger.info(f"  Cache entries cleared: {cache_count}")
        logger.info(f"  Database providers cleared: {db_count}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())