#!/usr/bin/env python3
"""
Persistent Caching System for Google Places API
Reduces API costs by caching responses in SQLite database
"""

import sqlite3
import os
import json
import pickle
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)


class PersistentCache:
    """SQLite-based persistent cache for API responses"""
    
    def __init__(self, db_path: str = 'cache/google_places_cache.db'):
        """Initialize the persistent cache
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
        logger.info(f"✅ Persistent cache initialized at {db_path}")
    
    def _init_db(self):
        """Initialize SQLite database schema"""
        with sqlite3.connect(self.db_path) as conn:
            # Place details cache
            conn.execute('''
                CREATE TABLE IF NOT EXISTS place_cache (
                    place_id TEXT NOT NULL,
                    cache_type TEXT NOT NULL,
                    data BLOB NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    hit_count INTEGER DEFAULT 0,
                    PRIMARY KEY (place_id, cache_type)
                )
            ''')
            
            # Processed places tracker
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processed_places (
                    place_id TEXT PRIMARY KEY,
                    processed_at TIMESTAMP NOT NULL,
                    last_updated TIMESTAMP NOT NULL,
                    search_query TEXT,
                    city TEXT,
                    specialty TEXT
                )
            ''')
            
            
            # Create indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_cache_expires ON place_cache(expires_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_processed_city ON processed_places(city)')
            
            conn.commit()
    
    def get(self, key: str, cache_type: str = 'details') -> Optional[Any]:
        """Retrieve cached data if not expired
        
        Args:
            key: Cache key (usually place_id)
            cache_type: Type of cache ('details', 'search', etc.)
            
        Returns:
            Cached data or None if not found/expired
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT data, expires_at FROM place_cache 
                WHERE place_id = ? AND cache_type = ?
            ''', (key, cache_type))
            
            row = cursor.fetchone()
            
            if row:
                data, expires_at = row
                expires_dt = datetime.fromisoformat(expires_at)
                
                if expires_dt > datetime.now():
                    # Update hit count
                    conn.execute('''
                        UPDATE place_cache 
                        SET hit_count = hit_count + 1 
                        WHERE place_id = ? AND cache_type = ?
                    ''', (key, cache_type))
                    conn.commit()
                    
                    logger.debug(f"✅ Cache hit for {key} ({cache_type})")
                    return pickle.loads(data)
                else:
                    # Remove expired entry
                    conn.execute('''
                        DELETE FROM place_cache 
                        WHERE place_id = ? AND cache_type = ?
                    ''', (key, cache_type))
                    conn.commit()
                    logger.debug(f"🗑️ Removed expired cache for {key} ({cache_type})")
        
        logger.debug(f"❌ Cache miss for {key} ({cache_type})")
        return None
    
    def set(self, key: str, data: Any, cache_type: str = 'details', 
            ttl_days: float = 30) -> None:
        """Store data in cache with expiration
        
        Args:
            key: Cache key (usually place_id)
            data: Data to cache
            cache_type: Type of cache
            ttl_days: Time to live in days (0.5 = 12 hours)
        """
        created_at = datetime.now()
        expires_at = created_at + timedelta(days=ttl_days)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO place_cache 
                (place_id, cache_type, data, created_at, expires_at, hit_count)
                VALUES (?, ?, ?, ?, ?, 0)
            ''', (key, cache_type, pickle.dumps(data), 
                  created_at.isoformat(), expires_at.isoformat()))
            conn.commit()
        
        logger.debug(f"💾 Cached {key} ({cache_type}) for {ttl_days} days")
    
    def is_processed(self, place_id: str, days_threshold: int = 30) -> bool:
        """Check if a place was processed recently
        
        Args:
            place_id: Google Place ID
            days_threshold: Consider processed if within this many days
            
        Returns:
            True if processed recently, False otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT last_updated FROM processed_places 
                WHERE place_id = ?
            ''', (place_id,))
            
            row = cursor.fetchone()
            
            if row:
                last_updated = datetime.fromisoformat(row[0])
                days_ago = (datetime.now() - last_updated).days
                
                if days_ago < days_threshold:
                    logger.debug(f"✅ {place_id} processed {days_ago} days ago")
                    return True
        
        return False
    
    def mark_processed(self, place_id: str, search_query: str = None,
                      city: str = None, specialty: str = None) -> None:
        """Mark a place as processed
        
        Args:
            place_id: Google Place ID
            search_query: Search query that found this place
            city: City location
            specialty: Medical specialty
        """
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO processed_places 
                (place_id, processed_at, last_updated, search_query, city, specialty)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (place_id, now, now, search_query, city, specialty))
            conn.commit()
        
        logger.debug(f"✅ Marked {place_id} as processed")
    
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        with sqlite3.connect(self.db_path) as conn:
            # Total cache entries
            total = conn.execute('SELECT COUNT(*) FROM place_cache').fetchone()[0]
            
            # Cache by type
            by_type = dict(conn.execute('''
                SELECT cache_type, COUNT(*) 
                FROM place_cache 
                GROUP BY cache_type
            ''').fetchall())
            
            # Hit rate
            hits = conn.execute('''
                SELECT SUM(hit_count) 
                FROM place_cache
            ''').fetchone()[0] or 0
            
            # Processed places
            processed = conn.execute('''
                SELECT COUNT(*) 
                FROM processed_places
            ''').fetchone()[0]
            
            # Cache size
            size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
        
        return {
            'total_entries': total,
            'by_type': by_type,
            'total_hits': hits,
            'processed_places': processed,
            'size_mb': round(size_mb, 2)
        }
    
    def cleanup_expired(self) -> int:
        """Remove expired cache entries
        
        Returns:
            Number of entries removed
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                DELETE FROM place_cache 
                WHERE expires_at < ?
            ''', (datetime.now().isoformat(),))
            
            deleted = cursor.rowcount
            conn.commit()
        
        if deleted > 0:
            logger.info(f"🗑️ Cleaned up {deleted} expired cache entries")
        
        return deleted