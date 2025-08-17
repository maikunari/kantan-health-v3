#!/usr/bin/env python3
"""
Generate content for ALL combination pages, regardless of provider count
Uses Claude Sonnet 3.5 for higher quality SEO content
"""

import os
import sys
import json
import time
import logging
from typing import List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.generate_taxonomy_content import TaxonomyContentGenerator
from src.core.database import DatabaseManager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_all_combinations() -> List[Tuple]:
    """Get all unique location-specialty combinations from database"""
    
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        # Get all unique combinations
        result = session.execute(text("""
            SELECT 
                city,
                ward,
                specialties::text,
                COUNT(*) as provider_count
            FROM providers
            WHERE city IS NOT NULL AND city != ''
            GROUP BY city, ward, specialties::text
            ORDER BY COUNT(*) DESC
        """)).fetchall()
        
        # Process into combination items
        all_combinations = []
        seen_combos = set()  # Track unique combinations
        
        for city, ward, specialties_str, count in result:
            # Parse specialties
            specialties = []
            
            if specialties_str:
                if specialties_str.startswith('['):
                    try:
                        # Parse JSON array
                        spec_list = json.loads(specialties_str.replace("'", '"'))
                        specialties = spec_list if isinstance(spec_list, list) else [spec_list]
                    except:
                        specialties = ['Healthcare']
                else:
                    specialties = [specialties_str]
            else:
                specialties = ['Healthcare']
            
            # Create combination for each specialty
            for specialty in specialties:
                # Create unique key to avoid duplicates
                combo_key = f"{city}|{ward or ''}|{specialty}"
                
                if combo_key not in seen_combos:
                    seen_combos.add(combo_key)
                    all_combinations.append((
                        'combination',
                        city,
                        specialty,
                        ward,
                        count
                    ))
        
        logger.info(f"Found {len(all_combinations)} unique combinations")
        
        # Sort by provider count (highest first)
        all_combinations.sort(key=lambda x: x[4], reverse=True)
        
        return all_combinations
        
    finally:
        session.close()


def main():
    """Generate content for all combinations"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate content for all combinations')
    parser.add_argument('--batch-size', type=int, default=5,
                       help='Number of items per API call (default 5)')
    parser.add_argument('--start-from', type=int, default=0,
                       help='Start from index (for resuming)')
    parser.add_argument('--limit', type=int,
                       help='Limit total number to generate')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be generated without doing it')
    
    args = parser.parse_args()
    
    # Get all combinations
    all_combinations = get_all_combinations()
    
    if args.limit:
        all_combinations = all_combinations[:args.limit]
    
    if args.start_from:
        all_combinations = all_combinations[args.start_from:]
    
    logger.info("=" * 60)
    logger.info(f"📊 CONTENT GENERATION PLAN")
    logger.info(f"   Total combinations: {len(all_combinations)}")
    logger.info(f"   Batch size: {args.batch_size}")
    logger.info(f"   Estimated batches: {len(all_combinations) // args.batch_size + 1}")
    logger.info(f"   Estimated time: {(len(all_combinations) // args.batch_size * 3) // 60} minutes")
    logger.info("=" * 60)
    
    if args.dry_run:
        logger.info("DRY RUN - Showing first 10 combinations:")
        for i, (_, city, specialty, ward, count) in enumerate(all_combinations[:10], 1):
            location = f"{ward}, {city}" if ward else city
            logger.info(f"   {i}. {specialty} in {location} ({count} providers)")
        return
    
    # Initialize generator
    generator = TaxonomyContentGenerator()
    
    # Process in batches
    total_generated = 0
    batch_size = args.batch_size
    
    for i in range(0, len(all_combinations), batch_size):
        batch = all_combinations[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(all_combinations) - 1) // batch_size + 1
        
        logger.info(f"\n📝 Processing batch {batch_num}/{total_batches}...")
        
        # Show what's in this batch
        for _, city, specialty, ward, count in batch:
            location = f"{ward}, {city}" if ward else city
            logger.info(f"   - {specialty} in {location} ({count} providers)")
        
        try:
            # Generate content
            content_batch = generator.generate_mega_batch(batch, len(batch))
            
            # Save to database
            generator.save_content(content_batch)
            
            total_generated += len(content_batch)
            logger.info(f"✅ Batch {batch_num} complete. Total generated: {total_generated}")
            
        except Exception as e:
            logger.error(f"❌ Error in batch {batch_num}: {e}")
            logger.info("Continuing with next batch...")
        
        # Rate limiting
        if i + batch_size < len(all_combinations):
            logger.info("⏳ Waiting 3 seconds...")
            time.sleep(3)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ GENERATION COMPLETE")
    logger.info(f"   Total combinations processed: {len(all_combinations)}")
    logger.info(f"   Total content generated: {total_generated}")
    logger.info(f"   Success rate: {total_generated/len(all_combinations)*100:.1f}%")
    logger.info("=" * 60)
    logger.info("\nNext step: Run publish_taxonomy_content.py to publish to WordPress")


if __name__ == "__main__":
    main()