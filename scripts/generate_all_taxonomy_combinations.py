#!/usr/bin/env python3
"""
Generate content for ALL possible taxonomy combinations
Creates pages for every city × specialty combination, even if no providers yet
"""

import os
import sys
import time
import logging
from typing import List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.generate_taxonomy_content_updated import TaxonomyContentGenerator
from src.core.database import DatabaseManager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Define all cities/locations we want pages for
CITIES = [
    # Major cities
    ('Tokyo', None),
    ('Yokohama', None),
    ('Osaka', None),
    ('Nagoya', None),
    ('Sapporo', None),
    ('Fukuoka', None),
    ('Kobe', None),
    ('Kyoto', None),
    ('Kawasaki', None),
    ('Saitama', None),
    ('Hiroshima', None),
    ('Sendai', None),
    
    # Tokyo Wards
    ('Tokyo', 'Shibuya'),
    ('Tokyo', 'Shinjuku'),
    ('Tokyo', 'Minato'),
    ('Tokyo', 'Chiyoda'),
    ('Tokyo', 'Chuo'),
    ('Tokyo', 'Meguro'),
    ('Tokyo', 'Setagaya'),
    ('Tokyo', 'Ota'),
    ('Tokyo', 'Bunkyo'),
    ('Tokyo', 'Taito'),
    ('Tokyo', 'Sumida'),
    ('Tokyo', 'Koto'),
    ('Tokyo', 'Shinagawa'),
    ('Tokyo', 'Nakano'),
    ('Tokyo', 'Toshima'),
    ('Tokyo', 'Suginami'),
    ('Tokyo', 'Itabashi'),
    ('Tokyo', 'Nerima'),
    ('Tokyo', 'Adachi'),
    ('Tokyo', 'Katsushika'),
    ('Tokyo', 'Edogawa'),
    ('Tokyo', 'Arakawa'),
    ('Tokyo', 'Kita'),
    
    # Other cities with wards/districts
    ('Yokohama', 'Naka'),
    ('Yokohama', 'Nishi'),
    ('Yokohama', 'Minami'),
    ('Yokohama', 'Hodogaya'),
    ('Yokohama', 'Isogo'),
    ('Yokohama', 'Kanagawa'),
    ('Yokohama', 'Asahi'),
    ('Yokohama', 'Konan'),
    ('Yokohama', 'Kanazawa'),
    ('Yokohama', 'Kohoku'),
    ('Yokohama', 'Midori'),
    ('Yokohama', 'Aoba'),
    ('Yokohama', 'Tsuzuki'),
    ('Yokohama', 'Totsuka'),
    ('Yokohama', 'Sakae'),
    ('Yokohama', 'Izumi'),
    ('Yokohama', 'Seya'),
    ('Yokohama', 'Tsurumi'),
    
    ('Osaka', 'Kita'),
    ('Osaka', 'Chuo'),
    ('Osaka', 'Minami'),
    ('Osaka', 'Nishi'),
    ('Osaka', 'Tennoji'),
    ('Osaka', 'Naniwa'),
    ('Osaka', 'Yodogawa'),
    ('Osaka', 'Higashiyodogawa'),
    ('Osaka', 'Ikuno'),
    ('Osaka', 'Asahi'),
    ('Osaka', 'Joto'),
    ('Osaka', 'Tsurumi'),
    ('Osaka', 'Abeno'),
    ('Osaka', 'Sumiyoshi'),
    ('Osaka', 'Higashisumiyoshi'),
    ('Osaka', 'Hirano'),
    ('Osaka', 'Nishinari'),
    
    # Additional cities
    ('Nara', None),
    ('Kobe', None),
    ('Himeji', None),
    ('Nishinomiya', None),
    ('Amagasaki', None),
    ('Nagano', None),
    ('Kanazawa', None),
    ('Niigata', None),
    ('Hamamatsu', None),
    ('Shizuoka', None),
    ('Okayama', None),
    ('Kumamoto', None),
    ('Kagoshima', None),
    ('Matsuyama', None),
    ('Takamatsu', None),
    ('Kochi', None),
    ('Naha', None),
    ('Gifu', None),
    ('Toyama', None),
    ('Fukui', None),
    ('Kofu', None),
    ('Matsumoto', None),
    ('Utsunomiya', None),
    ('Maebashi', None),
    ('Takasaki', None),
    ('Mito', None),
    ('Tsukuba', None),
    ('Chiba', None),
    ('Funabashi', None),
    ('Kashiwa', None),
    ('Matsudo', None),
    ('Ichikawa', None),
    ('Fuchu', None),
    ('Chofu', None),
    ('Machida', None),
    ('Hachioji', None),
    ('Tachikawa', None),
    ('Musashino', None),
    ('Mitaka', None),
    ('Sagamihara', None),
    ('Fujisawa', None),
    ('Kamakura', None),
    ('Odawara', None),
    ('Atsugi', None),
    ('Yamagata', None),
    ('Fukushima', None),
    ('Koriyama', None),
    ('Iwaki', None),
    ('Akita', None),
    ('Aomori', None),
    ('Hakodate', None),
    ('Asahikawa', None),
    ('Kushiro', None),
    ('Obihiro', None),
    ('Kitakyushu', None),
    ('Kurume', None),
    ('Saga', None),
    ('Sasebo', None),
    ('Nagasaki', None),
    ('Oita', None),
    ('Miyazaki', None),
    ('Matsue', None),
    ('Tottori', None),
    ('Yamaguchi', None),
    ('Ube', None),
    ('Wakayama', None),
    ('Tsu', None),
    ('Suzuka', None),
    ('Yokkaichi', None),
    ('Otsu', None),
    ('Kusatsu', None),
    ('Kutchan', None),  # For Niseko area
]

# Define all specialties we want pages for
SPECIALTIES = [
    'General Medicine',
    'Dentist',
    'Pediatrics',
    'Gynecology',
    'Dermatology',
    'Ophthalmology',
    'ENT (Ear, Nose & Throat)',
    'Orthopedics',
    'Cardiology',
    'Gastroenterology',
    'Neurology',
    'Psychiatry',
    'Urology',
    'Plastic Surgery',
    'Emergency Medicine',
    'Internal Medicine',
    'Family Medicine',
    'Sports Medicine',
    'Rheumatology',
    'Endocrinology',
    'Allergy & Immunology',
    'Radiology',
    'Oncology',
    'Nephrology',
    'Pulmonology',
    'Obstetrics',
    'Oral Surgery',
    'Orthodontics',
    'Cosmetic Dentistry',
    'Pediatric Dentistry',
]


def get_all_theoretical_combinations() -> List[Tuple]:
    """Generate all theoretical combinations of cities and specialties"""
    
    all_combinations = []
    
    # Create combination for each city × specialty
    for city, ward in CITIES:
        for specialty in SPECIALTIES:
            # Add combination (type, city, specialty, ward, count)
            # Count is 0 for now since these are theoretical
            all_combinations.append((
                'combination',
                city,
                specialty,
                ward,
                0  # No providers yet
            ))
    
    logger.info(f"Created {len(all_combinations)} theoretical combinations")
    logger.info(f"  Cities/Locations: {len(CITIES)}")
    logger.info(f"  Specialties: {len(SPECIALTIES)}")
    
    return all_combinations


def check_existing_content() -> set:
    """Check what content already exists in database"""
    
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        result = session.execute(text("""
            SELECT DISTINCT 
                location || '|' || COALESCE(ward, '') || '|' || specialty as combo_key
            FROM taxonomy_content
        """)).fetchall()
        
        existing = set(row[0] for row in result)
        logger.info(f"Found {len(existing)} existing content entries")
        return existing
        
    finally:
        session.close()


def main():
    """Generate content for all theoretical combinations"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate content for all theoretical combinations')
    parser.add_argument('--batch-size', type=int, default=5,
                       help='Number of items per API call (default 5)')
    parser.add_argument('--skip-existing', action='store_true',
                       help='Skip combinations that already have content')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be generated without actually doing it')
    
    args = parser.parse_args()
    
    # Get all theoretical combinations
    all_combinations = get_all_theoretical_combinations()
    
    if args.skip_existing:
        # Check what already exists
        existing = check_existing_content()
        
        # Filter out existing combinations
        filtered_combinations = []
        for combo in all_combinations:
            _, city, specialty, ward, _ = combo
            combo_key = f"{city}|{ward or ''}|{specialty}"
            if combo_key not in existing:
                filtered_combinations.append(combo)
        
        logger.info(f"After filtering: {len(filtered_combinations)} combinations need content")
        all_combinations = filtered_combinations
    
    if args.dry_run:
        logger.info("DRY RUN - Would generate content for:")
        for i, (_, city, specialty, ward, _) in enumerate(all_combinations[:10], 1):
            location = f"{ward}, {city}" if ward else city
            logger.info(f"  {i}. {specialty} in {location}")
        logger.info(f"  ... and {len(all_combinations) - 10} more")
        return
    
    if not all_combinations:
        logger.info("No combinations to generate!")
        return
    
    # Initialize generator
    generator = TaxonomyContentGenerator()
    
    logger.info("=" * 60)
    logger.info(f"GENERATING CONTENT FOR {len(all_combinations)} COMBINATIONS")
    logger.info("=" * 60)
    
    total_generated = 0
    batch_size = args.batch_size
    
    # Process in batches
    for i in range(0, len(all_combinations), batch_size):
        batch = all_combinations[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(all_combinations) + batch_size - 1) // batch_size
        
        logger.info(f"\n📝 Processing batch {batch_num}/{total_batches}...")
        
        # Show what's in this batch
        for _, city, specialty, ward, _ in batch:
            location = f"{ward}, {city}" if ward else city
            logger.info(f"   - {specialty} in {location}")
        
        # Generate content
        try:
            content_batch = generator.generate_mega_batch(batch, len(batch))
            generator.save_content(content_batch)
            total_generated += len(content_batch)
            
            logger.info(f"✅ Batch {batch_num} complete ({total_generated}/{len(all_combinations)} total)")
            
        except Exception as e:
            logger.error(f"❌ Error in batch {batch_num}: {e}")
            # Continue with next batch
        
        # Rate limiting
        if i + batch_size < len(all_combinations):
            time.sleep(2)
    
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