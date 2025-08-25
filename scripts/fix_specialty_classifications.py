#!/usr/bin/env python3
"""
Fix specialty classifications for existing providers
Uses enhanced detection with review analysis to correct misclassifications
"""

import sys
import os
import logging
from typing import List, Dict

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.utils.specialty_detector import SpecialtyDetector
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def analyze_current_specialties():
    """Analyze current specialty distribution and identify problems"""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        logger.info("="*60)
        logger.info("📊 ANALYZING CURRENT SPECIALTIES")
        logger.info("="*60)
        
        # Get distribution
        result = session.execute(text("""
            SELECT specialties::text as specialty, COUNT(*) as count 
            FROM providers 
            WHERE specialties IS NOT NULL 
            GROUP BY specialties::text 
            ORDER BY count DESC 
            LIMIT 15
        """))
        
        logger.info("\n📋 Current Specialty Distribution:")
        for row in result:
            logger.info(f"  {row.count:3d} providers: {row.specialty[:50]}")
        
        # Count General Medicine misclassifications
        general_count = session.execute(text("""
            SELECT COUNT(*) 
            FROM providers 
            WHERE specialties::text LIKE '%General Medicine%'
        """)).scalar()
        
        total_count = session.execute(text("""
            SELECT COUNT(*) 
            FROM providers 
            WHERE specialties IS NOT NULL
        """)).scalar()
        
        logger.info(f"\n📊 General Medicine Classification:")
        logger.info(f"  {general_count} / {total_count} providers ({general_count/total_count*100:.1f}%)")
        
        # Find likely misclassified providers
        logger.info("\n⚠️  Likely Misclassified Providers:")
        
        misclassified = session.execute(text("""
            SELECT id, provider_name, specialties
            FROM providers
            WHERE (
                provider_name ILIKE '%women%' OR 
                provider_name ILIKE '%maternity%' OR
                provider_name ILIKE '%afterpill%' OR
                provider_name ILIKE '%dental%' OR
                provider_name ILIKE '%skin%' OR
                provider_name ILIKE '%eye%' OR
                provider_name ILIKE '%pediatric%' OR
                provider_name ILIKE '%children%'
            )
            AND specialties::text LIKE '%General Medicine%'
            LIMIT 10
        """))
        
        examples = []
        for row in misclassified:
            logger.info(f"  - {row.provider_name}")
            logger.info(f"    Current: {row.specialties}")
            examples.append(row)
        
        return examples
        
    finally:
        session.close()


def fix_provider_specialty(provider_id: int, dry_run: bool = False):
    """Fix specialty for a single provider using enhanced detection"""
    db = DatabaseManager()
    session = db.get_session()
    detector = SpecialtyDetector()
    
    try:
        # Get provider data
        result = session.execute(text("""
            SELECT id, provider_name, specialties, review_content, 
                   ai_description, city, district
            FROM providers
            WHERE id = :id
        """), {'id': provider_id}).first()
        
        if not result:
            return None
        
        # Use enhanced detection
        current_specialties = result.specialties if result.specialties else []
        
        best_specialty = detector.determine_specialty(
            provider_name=result.provider_name,
            reviews=result.review_content if result.review_content else [],
            google_types=[],  # TODO: Add if available
            description=result.ai_description,
            existing_specialties=current_specialties
        )
        
        # Clean up specialties
        if isinstance(current_specialties, list):
            cleaned = detector.clean_specialty_list(current_specialties)
        else:
            cleaned = [best_specialty]
        
        # Add detected specialty if not present
        if best_specialty not in cleaned and best_specialty != 'General Medicine':
            cleaned.insert(0, best_specialty)
        
        # Remove General Medicine if we have better options
        if len(cleaned) > 1 and 'General Medicine' in cleaned:
            cleaned = [s for s in cleaned if s != 'General Medicine']
        
        # Check if changed
        if cleaned != current_specialties:
            logger.info(f"\n✅ {result.provider_name}")
            logger.info(f"   Old: {current_specialties}")
            logger.info(f"   New: {cleaned}")
            
            if not dry_run:
                # Update database - convert to JSON format
                import json
                session.execute(text("""
                    UPDATE providers 
                    SET specialties = :specialties
                    WHERE id = :id
                """), {'specialties': json.dumps(cleaned), 'id': provider_id})
                session.commit()
            
            return {'id': provider_id, 'old': current_specialties, 'new': cleaned}
        
        return None
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error fixing provider {provider_id}: {e}")
        return None
        
    finally:
        session.close()


def fix_all_specialties(limit: int = None, dry_run: bool = False):
    """Fix specialties for all providers"""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        logger.info("\n" + "="*60)
        logger.info("🔧 FIXING SPECIALTY CLASSIFICATIONS")
        logger.info("="*60)
        
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
        
        # Get providers to fix (prioritize obvious misclassifications)
        query = """
            SELECT id
            FROM providers
            WHERE specialties IS NOT NULL
            ORDER BY 
                CASE 
                    WHEN provider_name ILIKE '%women%' THEN 1
                    WHEN provider_name ILIKE '%dental%' THEN 2
                    WHEN provider_name ILIKE '%pediatric%' THEN 3
                    WHEN provider_name ILIKE '%skin%' THEN 4
                    WHEN provider_name ILIKE '%eye%' THEN 5
                    WHEN specialties::text LIKE '%General Medicine%' THEN 6
                    ELSE 7
                END,
                id
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        providers = session.execute(text(query)).fetchall()
        
        logger.info(f"Processing {len(providers)} providers...")
        
        fixed_count = 0
        changes = []
        
        for i, row in enumerate(providers, 1):
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(providers)}")
            
            result = fix_provider_specialty(row.id, dry_run)
            if result:
                fixed_count += 1
                changes.append(result)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("✅ SPECIALTY FIX COMPLETE")
        logger.info(f"   Total processed: {len(providers)}")
        logger.info(f"   Fixed: {fixed_count}")
        logger.info("="*60)
        
        # Show some examples
        if changes and len(changes) <= 10:
            logger.info("\n📋 All Changes Made:")
            for change in changes:
                session = db.get_session()
                name = session.execute(text(
                    "SELECT provider_name FROM providers WHERE id = :id"
                ), {'id': change['id']}).scalar()
                session.close()
                
                logger.info(f"\n{name}:")
                logger.info(f"  Old: {change['old']}")
                logger.info(f"  New: {change['new']}")
        
        return fixed_count
        
    finally:
        session.close()


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix specialty classifications')
    parser.add_argument('--analyze', action='store_true', help='Only analyze, don\'t fix')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    parser.add_argument('--limit', type=int, help='Limit number of providers to process')
    parser.add_argument('--provider-id', type=int, help='Fix specific provider')
    
    args = parser.parse_args()
    
    if args.analyze:
        analyze_current_specialties()
    elif args.provider_id:
        result = fix_provider_specialty(args.provider_id, args.dry_run)
        if result:
            logger.info(f"✅ Fixed specialty for provider {args.provider_id}")
        else:
            logger.info(f"No changes needed for provider {args.provider_id}")
    else:
        # Analyze first
        examples = analyze_current_specialties()
        
        if examples or not args.analyze:
            # Fix specialties
            fix_all_specialties(limit=args.limit, dry_run=args.dry_run)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())