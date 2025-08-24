#!/usr/bin/env python3
"""
Regenerate content for failed combinations that got default "Healthcare Directory" content
"""

import os
import sys
import time
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.generate_taxonomy_content_updated import TaxonomyContentGenerator
from src.core.database import DatabaseManager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_failed_combinations():
    """Get combinations that need content regeneration"""
    
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # First, let's see what we deleted
        result = session.execute(text("""
            SELECT DISTINCT location, specialty, ward
            FROM taxonomy_content
            WHERE title = 'Healthcare Directory'
        """)).fetchall()
        
        failed_combos = []
        for row in result:
            failed_combos.append({
                'location': row[0],
                'specialty': row[1],
                'ward': row[2]
            })
        
        logger.info(f"Found {len(failed_combos)} combinations needing regeneration")
        return failed_combos
        
    finally:
        session.close()


def main():
    """Regenerate content for failed combinations"""
    
    # Get failed combinations before deleting
    failed_combos = get_failed_combinations()
    
    if not failed_combos:
        logger.info("No failed combinations found!")
        return
    
    # Delete the bad entries
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        result = session.execute(text("""
            DELETE FROM taxonomy_content 
            WHERE title = 'Healthcare Directory'
            RETURNING id
        """))
        deleted_count = result.rowcount
        session.commit()
        logger.info(f"✅ Deleted {deleted_count} bad entries")
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting bad entries: {e}")
        return
    finally:
        session.close()
    
    # Now regenerate content
    generator = TaxonomyContentGenerator()
    
    logger.info("=" * 60)
    logger.info(f"REGENERATING CONTENT FOR {len(failed_combos)} COMBINATIONS")
    logger.info("=" * 60)
    
    # Process in batches of 5
    batch_size = 5
    total_generated = 0
    
    for i in range(0, len(failed_combos), batch_size):
        batch = failed_combos[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(failed_combos) + batch_size - 1) // batch_size
        
        logger.info(f"\n📝 Processing batch {batch_num}/{total_batches}...")
        
        # Convert to generator format
        items = []
        for combo in batch:
            items.append((
                'combination',
                combo['location'],
                combo['specialty'],
                combo['ward'],
                0  # Provider count - will be updated later
            ))
            
            # Log what we're generating
            loc = f"{combo['ward']}, {combo['location']}" if combo['ward'] else combo['location']
            logger.info(f"   - {combo['specialty']} in {loc}")
        
        # Generate content
        try:
            content_batch = generator.generate_mega_batch(items, len(items))
            generator.save_content(content_batch)
            total_generated += len(content_batch)
            
            logger.info(f"✅ Batch {batch_num} complete ({total_generated}/{len(failed_combos)} total)")
            
        except Exception as e:
            logger.error(f"❌ Error in batch {batch_num}: {e}")
            # Try individual generation as fallback
            for item in items:
                try:
                    logger.info(f"   Trying individual generation for {item[2]} in {item[1]}")
                    individual_content = generator._generate_individual(item)
                    generator.save_content([individual_content])
                    total_generated += 1
                except Exception as e2:
                    logger.error(f"   Failed individual generation: {e2}")
        
        # Rate limiting
        if i + batch_size < len(failed_combos):
            time.sleep(2)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ REGENERATION COMPLETE")
    logger.info(f"   Total combinations processed: {len(failed_combos)}")
    logger.info(f"   Successfully regenerated: {total_generated}")
    logger.info(f"   Success rate: {total_generated/len(failed_combos)*100:.1f}%")
    logger.info("=" * 60)
    logger.info("\nNext step: Run publish_taxonomy_content.py to update WordPress")


if __name__ == "__main__":
    main()