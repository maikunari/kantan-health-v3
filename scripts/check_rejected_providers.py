#!/usr/bin/env python3
"""
Check proficiency scores of providers that were evaluated but not saved
"""

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.collectors.google_places import GooglePlacesCollector
from src.core.cache import PersistentCache

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_rejected_providers(place_ids):
    """Check proficiency scores for specific place IDs"""
    collector = GooglePlacesCollector()
    cache = PersistentCache()
    
    logger.info("=" * 60)
    logger.info("📊 CHECKING REJECTED NAGOYA PROVIDERS")
    logger.info("=" * 60)
    
    results = []
    
    for place_id in place_ids:
        # Check cache for details
        cache_key = f"details_{place_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            details = cached_data
            
            # Calculate proficiency score
            score, signals = collector._calculate_proficiency_score(details)
            
            # Get basic info
            name = details.get('name', 'Unknown')
            address = details.get('formatted_address', 'No address')
            rating = details.get('rating', 0)
            reviews_count = details.get('user_ratings_total', 0)
            
            results.append({
                'name': name,
                'place_id': place_id,
                'score': score,
                'signals': signals,
                'rating': rating,
                'reviews': reviews_count,
                'address': address
            })
            
            logger.info(f"\n{'='*50}")
            logger.info(f"Provider: {name}")
            logger.info(f"Place ID: {place_id}")
            logger.info(f"Address: {address}")
            logger.info(f"Rating: {rating} ⭐ ({reviews_count} reviews)")
            logger.info(f"Proficiency Score: {score} {'✅ ACCEPTED' if score >= 10 else '❌ REJECTED'}")
            
            if signals:
                logger.info("English Signals Found:")
                for signal in signals:
                    logger.info(f"  • {signal}")
            else:
                logger.info("No English signals found")
                
        else:
            logger.info(f"\n❌ No cached details for {place_id}")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 SUMMARY")
    logger.info("="*60)
    
    if results:
        accepted = [r for r in results if r['score'] >= 10]
        rejected = [r for r in results if r['score'] < 10]
        
        logger.info(f"Total checked: {len(results)}")
        logger.info(f"Would accept (score >= 10): {len(accepted)}")
        logger.info(f"Rejected (score < 10): {len(rejected)}")
        
        # Score distribution
        score_ranges = {
            '0': 0,
            '1-5': 0,
            '6-9': 0,
            '10-19': 0,
            '20+': 0
        }
        
        for r in results:
            score = r['score']
            if score == 0:
                score_ranges['0'] += 1
            elif score <= 5:
                score_ranges['1-5'] += 1
            elif score <= 9:
                score_ranges['6-9'] += 1
            elif score <= 19:
                score_ranges['10-19'] += 1
            else:
                score_ranges['20+'] += 1
        
        logger.info("\nScore Distribution:")
        for range_name, count in score_ranges.items():
            if count > 0:
                logger.info(f"  Score {range_name}: {count} providers")
        
        # Show rejected providers that were close
        close_rejects = [r for r in rejected if 5 <= r['score'] < 10]
        if close_rejects:
            logger.info(f"\n⚠️ Close to threshold (score 5-9): {len(close_rejects)} providers")
            for r in close_rejects:
                logger.info(f"  • {r['name']} (score: {r['score']})")


def main():
    """Main execution"""
    # Place IDs found in Nagoya search
    nagoya_place_ids = [
        'ChIJ43BAeu1GGGARHGT3jjD-Gk0',
        'ChIJ6w5auw8WGGARrtbkc6hcUl8',
        'ChIJB83O1NOMGGARviqiBHmUSQs',
        'ChIJd5N88NxFGGARyzX1Hd_BsnY',
        'ChIJG49tAvFGGGARg7oGLPKjNtk',
        'ChIJhy5geoxGGGARjw5Unn_0EAw',
        'ChIJIyCKCe1GGGAR6jCnRK2J1s4',
        'ChIJjQfrMPNGGGARODLVrZgNxis',
        'ChIJm0ShxPJGGGARVEh-y39OSU4',
        'ChIJNyyZT3VAGGARwVaYmRkN_ko',  # This one is in DB (Tokyo)
        'ChIJu70V-_JGGGARzx_44VEAwLU',
        'ChIJvQA5fQCtGWARTP6PybyhHCo',
        'ChIJx_1CiBNHGGARwN7yaC_eLyI'
    ]
    
    check_rejected_providers(nagoya_place_ids)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())