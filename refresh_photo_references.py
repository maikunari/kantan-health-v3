#!/usr/bin/env python3
"""
Refresh Photo References from Google Places API
Updates expired or stale photo references to keep images working
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database import DatabaseManager
from src.collectors.google_places import GooglePlacesCollector
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def refresh_provider_photos(provider_id: int, place_id: str, collector: GooglePlacesCollector) -> bool:
    """Refresh photo references for a single provider
    
    Args:
        provider_id: Provider database ID
        place_id: Google Place ID
        collector: GooglePlacesCollector instance
        
    Returns:
        Success status
    """
    try:
        # Fetch fresh place details
        logger.info(f"  📷 Fetching fresh photos for place {place_id}")
        details = collector.get_place_details(place_id, skip_cache=True)
        
        if not details:
            logger.error(f"  ❌ Failed to fetch place details")
            return False
        
        # Extract photo references
        photos = details.get('photos', [])
        if not photos:
            logger.warning(f"  ⚠️  No photos found")
            return False
        
        # Get just the references
        references = [photo.get('photo_reference') for photo in photos if photo.get('photo_reference')]
        
        if references:
            # Update database
            db = DatabaseManager()
            session = db.get_session()
            
            try:
                session.execute(text("""
                    UPDATE providers 
                    SET photo_references = :references,
                        updated_at = NOW()
                    WHERE id = :id
                """), {
                    'references': json.dumps(references),
                    'id': provider_id
                })
                session.commit()
                logger.info(f"  ✅ Updated {len(references)} photo references")
                return True
                
            except Exception as e:
                session.rollback()
                logger.error(f"  ❌ Database error: {str(e)}")
                return False
            finally:
                session.close()
        else:
            logger.warning(f"  ⚠️  No valid references found")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ Error refreshing photos: {str(e)}")
        return False

def main():
    """Main function to refresh photo references"""
    logger.info("🔄 Starting photo reference refresh...")
    
    # Initialize services
    collector = GooglePlacesCollector()
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Get providers with photos that might need refresh
        # Prioritize those updated longest ago
        providers = session.execute(text("""
            SELECT id, provider_name, google_place_id, photo_references, created_at
            FROM providers
            WHERE google_place_id IS NOT NULL
            AND photo_references IS NOT NULL
            ORDER BY created_at ASC
            LIMIT 50
        """)).fetchall()
        
        logger.info(f"📊 Found {len(providers)} providers to check")
        
        refreshed_count = 0
        error_count = 0
        
        for provider in providers:
            # Check if references are likely stale (>30 days old)
            if provider.created_at:
                age_days = (datetime.now() - provider.created_at).days
                if age_days < 30:
                    logger.debug(f"⏭️  Skipping {provider.provider_name} - updated {age_days} days ago")
                    continue
            
            logger.info(f"🔄 Refreshing: {provider.provider_name}")
            
            if refresh_provider_photos(provider.id, provider.google_place_id, collector):
                refreshed_count += 1
            else:
                error_count += 1
            
            # Rate limiting - be nice to Google's API
            import time
            time.sleep(0.5)
        
        logger.info(f"""
        ✅ Photo reference refresh complete!
        📊 Results:
           - Refreshed: {refreshed_count} providers
           - Errors: {error_count} providers
           - Total checked: {len(providers)} providers
        """)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        
    finally:
        session.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Refresh Google Places photo references')
    parser.add_argument('--all', action='store_true', help='Refresh all providers (ignore age check)')
    parser.add_argument('--provider-id', type=int, help='Refresh specific provider by ID')
    args = parser.parse_args()
    
    main()