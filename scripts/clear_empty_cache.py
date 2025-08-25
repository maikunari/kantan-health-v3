#!/usr/bin/env python3
"""
Clear empty search results from cache
Removes cached searches that returned 0 results to allow retry
"""

import sys
import os
import sqlite3
import json
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clear_empty_cache_results():
    """Clear cache entries that contain empty search results"""
    db_path = 'cache/google_places_cache.db'
    
    with sqlite3.connect(db_path) as conn:
        # First, find entries with empty results
        cursor = conn.execute('''
            SELECT place_id, cache_type, data 
            FROM place_cache 
            WHERE cache_type = 'search'
        ''')
        
        empty_entries = []
        for place_id, cache_type, data_blob in cursor:
            try:
                # Parse the cached data
                data = json.loads(data_blob)
                
                # Check if results are empty
                if isinstance(data, dict):
                    results = data.get('results', [])
                    if len(results) == 0:
                        empty_entries.append(place_id)
                elif isinstance(data, list) and len(data) == 0:
                    empty_entries.append(place_id)
                    
            except (json.JSONDecodeError, TypeError):
                continue
        
        if not empty_entries:
            logger.info("No empty cache entries found")
            return 0
        
        logger.info(f"Found {len(empty_entries)} empty cache entries")
        
        # Show samples
        for i, entry in enumerate(empty_entries[:5]):
            logger.info(f"  Sample {i+1}: {entry[:80]}...")
        if len(empty_entries) > 5:
            logger.info(f"  ... and {len(empty_entries) - 5} more")
        
        # Delete empty entries
        placeholders = ','.join('?' * len(empty_entries))
        result = conn.execute(
            f'DELETE FROM place_cache WHERE place_id IN ({placeholders})',
            empty_entries
        )
        
        deleted = result.rowcount
        conn.commit()
        
        logger.info(f"✅ Deleted {deleted} empty cache entries")
        return deleted


def clear_location_empty_cache(location: str = None):
    """Clear empty cache entries for a specific location"""
    db_path = 'cache/google_places_cache.db'
    
    with sqlite3.connect(db_path) as conn:
        # Build query based on location
        if location:
            cursor = conn.execute('''
                SELECT place_id, cache_type, data 
                FROM place_cache 
                WHERE cache_type = 'search'
                AND place_id LIKE ?
            ''', (f'%{location}%',))
            logger.info(f"Checking cache entries for location: {location}")
        else:
            cursor = conn.execute('''
                SELECT place_id, cache_type, data 
                FROM place_cache 
                WHERE cache_type = 'search'
            ''')
            logger.info("Checking all cache entries")
        
        empty_entries = []
        total_checked = 0
        
        for place_id, cache_type, data_blob in cursor:
            total_checked += 1
            try:
                # Parse the cached data - handle both JSON and pickle formats
                if isinstance(data_blob, bytes):
                    try:
                        import pickle
                        data = pickle.loads(data_blob)
                    except:
                        data = json.loads(data_blob.decode('utf-8'))
                else:
                    data = json.loads(data_blob)
                
                # Check if results are empty or have low/no results
                empty = False
                if isinstance(data, dict):
                    results = data.get('results', [])
                    # Consider it empty if 0 results or only 1-2 non-useful results
                    if len(results) <= 2:
                        empty = True
                elif isinstance(data, list) and len(data) <= 2:
                    empty = True
                
                if empty:
                    empty_entries.append(place_id)
                    
            except (json.JSONDecodeError, TypeError):
                continue
        
        logger.info(f"Checked {total_checked} cache entries")
        
        if not empty_entries:
            logger.info("No empty/low-result cache entries found")
            return 0
        
        logger.info(f"Found {len(empty_entries)} empty/low-result cache entries")
        
        # Delete empty entries
        placeholders = ','.join('?' * len(empty_entries))
        result = conn.execute(
            f'DELETE FROM place_cache WHERE place_id IN ({placeholders})',
            empty_entries
        )
        
        deleted = result.rowcount
        conn.commit()
        
        logger.info(f"✅ Deleted {deleted} empty/low-result cache entries")
        return deleted


def show_cache_stats():
    """Show cache statistics"""
    db_path = 'cache/google_places_cache.db'
    
    with sqlite3.connect(db_path) as conn:
        # Total cache entries
        total = conn.execute('SELECT COUNT(*) FROM place_cache').fetchone()[0]
        
        # Search cache entries
        search_count = conn.execute(
            "SELECT COUNT(*) FROM place_cache WHERE cache_type = 'search'"
        ).fetchone()[0]
        
        # Details cache entries
        details_count = conn.execute(
            "SELECT COUNT(*) FROM place_cache WHERE cache_type = 'details'"
        ).fetchone()[0]
        
        logger.info("=" * 60)
        logger.info("📊 CACHE STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total cache entries: {total}")
        logger.info(f"Search results cached: {search_count}")
        logger.info(f"Provider details cached: {details_count}")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clear empty cache results')
    parser.add_argument('--location', type=str, help='Clear empty cache for specific location (e.g., Nagoya)')
    parser.add_argument('--stats', action='store_true', help='Show cache statistics')
    parser.add_argument('--all', action='store_true', help='Clear all empty cache entries')
    
    args = parser.parse_args()
    
    if args.stats:
        show_cache_stats()
    elif args.location:
        clear_location_empty_cache(args.location)
    elif args.all:
        response = input("⚠️  Clear ALL empty cache entries? (yes/no): ")
        if response.lower() == 'yes':
            clear_location_empty_cache()
        else:
            logger.info("Operation cancelled")
    else:
        # Default: show stats and prompt
        show_cache_stats()
        logger.info("\n💡 Options:")
        logger.info("  --location Nagoya  : Clear empty cache for Nagoya")
        logger.info("  --all             : Clear all empty cache entries")
        logger.info("  --stats           : Show cache statistics")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())