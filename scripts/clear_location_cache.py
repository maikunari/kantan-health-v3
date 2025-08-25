#!/usr/bin/env python3
"""
Clear Google Places API cache for a specific location
"""

import sys
import os
import sqlite3
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clear_cache_for_location(location: str):
    """Clear cache entries for a specific location"""
    db_path = 'cache/google_places_cache.db'
    
    with sqlite3.connect(db_path) as conn:
        # Find entries that match the location
        cursor = conn.execute('''
            SELECT place_id, cache_type, data 
            FROM place_cache 
            WHERE place_id LIKE ? 
               OR CAST(data AS TEXT) LIKE ?
        ''', (f'%{location}%', f'%{location}%'))
        
        matches = cursor.fetchall()
        
        if not matches:
            logger.info(f"No cache entries found for location: {location}")
            return 0
        
        logger.info(f"Found {len(matches)} cache entries for '{location}'")
        
        # Show sample of what will be deleted
        for i, (place_id, cache_type, data) in enumerate(matches[:3]):
            logger.info(f"  Sample {i+1}: {place_id[:50]} ({cache_type})")
        
        if len(matches) > 3:
            logger.info(f"  ... and {len(matches) - 3} more")
        
        # Delete the entries
        result = conn.execute('''
            DELETE FROM place_cache 
            WHERE place_id LIKE ? 
               OR CAST(data AS TEXT) LIKE ?
        ''', (f'%{location}%', f'%{location}%'))
        
        deleted = result.rowcount
        conn.commit()
        
        logger.info(f"✅ Deleted {deleted} cache entries for '{location}'")
        return deleted


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clear cache for specific location')
    parser.add_argument('location', type=str, help='Location to clear (e.g., Tokyo, Shibuya)')
    
    args = parser.parse_args()
    
    clear_cache_for_location(args.location)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())