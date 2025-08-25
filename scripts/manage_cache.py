#!/usr/bin/env python3
"""
Manage Google Places API cache
Clear cache for specific locations or view cache statistics
"""

import sys
import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.cache import PersistentCache

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CacheManager:
    """Manage Google Places API cache"""
    
    def __init__(self):
        self.cache = PersistentCache()
        self.db_path = 'cache/google_places_cache.db'
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Total cache entries
            total = conn.execute('SELECT COUNT(*) FROM cache_entries').fetchone()[0]
            
            # Entries by type
            type_stats = conn.execute('''
                SELECT cache_type, COUNT(*) as count 
                FROM cache_entries 
                GROUP BY cache_type
            ''').fetchall()
            
            # Cache size
            size = conn.execute('''
                SELECT SUM(LENGTH(data)) / 1024.0 / 1024.0 as size_mb
                FROM cache_entries
            ''').fetchone()[0] or 0
            
            # Age statistics
            oldest = conn.execute('''
                SELECT MIN(created_at) FROM cache_entries
            ''').fetchone()[0]
            
            newest = conn.execute('''
                SELECT MAX(created_at) FROM cache_entries
            ''').fetchone()[0]
            
            return {
                'total_entries': total,
                'by_type': dict(type_stats),
                'size_mb': round(size, 2),
                'oldest': oldest,
                'newest': newest
            }
    
    def clear_cache_for_location(self, location: str) -> int:
        """Clear cache entries for a specific location
        
        Args:
            location: City, ward, or location string to clear
            
        Returns:
            Number of entries cleared
        """
        with sqlite3.connect(self.db_path) as conn:
            # First, find entries that match the location
            cursor = conn.execute('''
                SELECT cache_key, data 
                FROM cache_entries 
                WHERE cache_key LIKE ? 
                   OR data LIKE ?
            ''', (f'%{location}%', f'%{location}%'))
            
            matches = cursor.fetchall()
            
            if not matches:
                logger.info(f"No cache entries found for location: {location}")
                return 0
            
            logger.info(f"Found {len(matches)} cache entries for '{location}'")
            
            # Show sample of what will be deleted
            for i, (key, data) in enumerate(matches[:3]):
                logger.info(f"  Sample {i+1}: {key[:80]}...")
            
            if len(matches) > 3:
                logger.info(f"  ... and {len(matches) - 3} more")
            
            # Delete the entries
            result = conn.execute('''
                DELETE FROM cache_entries 
                WHERE cache_key LIKE ? 
                   OR data LIKE ?
            ''', (f'%{location}%', f'%{location}%'))
            
            deleted = result.rowcount
            conn.commit()
            
            logger.info(f"✅ Deleted {deleted} cache entries for '{location}'")
            return deleted
    
    def clear_old_cache(self, days: int = 30) -> int:
        """Clear cache entries older than specified days
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of entries cleared
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute('''
                DELETE FROM cache_entries 
                WHERE created_at < ?
            ''', (cutoff_date,))
            
            deleted = result.rowcount
            conn.commit()
            
            logger.info(f"✅ Deleted {deleted} cache entries older than {days} days")
            return deleted
    
    def clear_cache_by_type(self, cache_type: str) -> int:
        """Clear all cache entries of a specific type
        
        Args:
            cache_type: Type of cache to clear (search, details, photos)
            
        Returns:
            Number of entries cleared
        """
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute('''
                DELETE FROM cache_entries 
                WHERE cache_type = ?
            ''', (cache_type,))
            
            deleted = result.rowcount
            conn.commit()
            
            logger.info(f"✅ Deleted {deleted} cache entries of type '{cache_type}'")
            return deleted
    
    def search_cache(self, query: str) -> list:
        """Search cache for specific content
        
        Args:
            query: Search string
            
        Returns:
            List of matching cache entries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT cache_key, cache_type, created_at, expires_at
                FROM cache_entries 
                WHERE cache_key LIKE ? 
                   OR data LIKE ?
                LIMIT 20
            ''', (f'%{query}%', f'%{query}%'))
            
            results = cursor.fetchall()
            
            return [{
                'key': r[0],
                'type': r[1],
                'created': r[2],
                'expires': r[3]
            } for r in results]
    
    def clear_all_cache(self) -> int:
        """Clear entire cache (use with caution)
        
        Returns:
            Number of entries cleared
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM cache_entries')
            total = cursor.fetchone()[0]
            
            conn.execute('DELETE FROM cache_entries')
            conn.commit()
            
            logger.info(f"✅ Cleared entire cache ({total} entries)")
            return total


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage Google Places API cache')
    parser.add_argument('--stats', action='store_true', help='Show cache statistics')
    parser.add_argument('--clear-location', type=str, help='Clear cache for specific location')
    parser.add_argument('--clear-old', type=int, metavar='DAYS', 
                       help='Clear cache entries older than N days')
    parser.add_argument('--clear-type', choices=['search', 'details', 'photos'],
                       help='Clear all cache of specific type')
    parser.add_argument('--search', type=str, help='Search cache for content')
    parser.add_argument('--clear-all', action='store_true', 
                       help='Clear entire cache (use with caution)')
    
    args = parser.parse_args()
    
    manager = CacheManager()
    
    if args.stats or not any(vars(args).values()):
        # Show statistics
        stats = manager.get_cache_stats()
        
        logger.info("="*60)
        logger.info("📊 CACHE STATISTICS")
        logger.info("="*60)
        logger.info(f"Total entries: {stats['total_entries']:,}")
        logger.info(f"Cache size: {stats['size_mb']:.2f} MB")
        
        if stats['by_type']:
            logger.info("\nEntries by type:")
            for cache_type, count in stats['by_type'].items():
                logger.info(f"  {cache_type}: {count:,}")
        
        if stats['oldest']:
            logger.info(f"\nOldest entry: {stats['oldest']}")
        if stats['newest']:
            logger.info(f"Newest entry: {stats['newest']}")
        
        logger.info("\n" + "="*60)
        logger.info("💡 Cache Management Commands:")
        logger.info("  Clear for location: --clear-location Tokyo")
        logger.info("  Clear old entries:  --clear-old 30")
        logger.info("  Clear by type:      --clear-type search")
        logger.info("  Search cache:       --search 'dental clinic'")
        logger.info("  Clear all:          --clear-all")
        logger.info("="*60)
    
    elif args.clear_location:
        manager.clear_cache_for_location(args.clear_location)
    
    elif args.clear_old:
        manager.clear_old_cache(args.clear_old)
    
    elif args.clear_type:
        manager.clear_cache_by_type(args.clear_type)
    
    elif args.search:
        results = manager.search_cache(args.search)
        
        if results:
            logger.info(f"\nFound {len(results)} matching cache entries:")
            for r in results:
                logger.info(f"  Type: {r['type']}, Created: {r['created']}")
                logger.info(f"    Key: {r['key'][:100]}...")
        else:
            logger.info(f"No cache entries found matching '{args.search}'")
    
    elif args.clear_all:
        response = input("⚠️  Clear ENTIRE cache? This cannot be undone (yes/no): ")
        if response.lower() == 'yes':
            manager.clear_all_cache()
        else:
            logger.info("Operation cancelled")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())