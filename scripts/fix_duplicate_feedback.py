#!/usr/bin/env python3
"""
Fix duplicate patient feedback that was incorrectly applied to multiple providers
This script identifies and clears duplicate content to restore data integrity
"""

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def analyze_duplicates():
    """Analyze extent of duplicate content in database"""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        logger.info("="*60)
        logger.info("📊 ANALYZING DUPLICATE CONTENT")
        logger.info("="*60)
        
        # Check for generic fallback content
        generic_fallback = "English language support is available for international patients."
        
        result = session.execute(text("""
            SELECT COUNT(*) as count 
            FROM providers 
            WHERE english_experience_summary = :fallback
        """), {'fallback': generic_fallback})
        
        fallback_count = result.scalar()
        
        if fallback_count > 0:
            logger.warning(f"⚠️  Found {fallback_count} providers with generic fallback content")
            
            # Get sample of affected providers
            providers = session.execute(text("""
                SELECT id, provider_name, city
                FROM providers
                WHERE english_experience_summary = :fallback
                LIMIT 5
            """), {'fallback': generic_fallback}).fetchall()
            
            logger.info("\nSample affected providers:")
            for p in providers:
                logger.info(f"  - {p.provider_name} ({p.city}) [ID: {p.id}]")
        
        # Check for other duplicates
        logger.info("\n📋 Checking for other duplicate content...")
        
        duplicates = session.execute(text("""
            SELECT english_experience_summary, COUNT(*) as count 
            FROM providers 
            WHERE english_experience_summary IS NOT NULL
            GROUP BY english_experience_summary 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 10
        """)).fetchall()
        
        if duplicates:
            logger.warning(f"\n⚠️  Found {len(duplicates)} different duplicate summaries:")
            for dup in duplicates:
                summary_preview = dup.english_experience_summary[:100] if dup.english_experience_summary else ""
                logger.info(f"  - {dup.count} providers: {summary_preview}...")
                
                # Show which providers have this duplicate
                providers = session.execute(text("""
                    SELECT provider_name
                    FROM providers
                    WHERE english_experience_summary = :summary
                    LIMIT 3
                """), {'summary': dup.english_experience_summary}).fetchall()
                
                for p in providers:
                    logger.info(f"    • {p.provider_name}")
        
        # Check review summaries too
        logger.info("\n📋 Checking review_summary for duplicates...")
        
        review_duplicates = session.execute(text("""
            SELECT review_summary, COUNT(*) as count 
            FROM providers 
            WHERE review_summary IS NOT NULL
            GROUP BY review_summary 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 5
        """)).fetchall()
        
        if review_duplicates:
            logger.warning(f"\n⚠️  Found duplicate review summaries:")
            for dup in review_duplicates:
                summary_preview = dup.review_summary[:80] if dup.review_summary else ""
                logger.info(f"  - {dup.count} providers: {summary_preview}...")
        
        # Overall statistics
        total_providers = session.execute(text("""
            SELECT COUNT(*) FROM providers WHERE english_experience_summary IS NOT NULL
        """)).scalar()
        
        unique_summaries = session.execute(text("""
            SELECT COUNT(DISTINCT english_experience_summary) 
            FROM providers 
            WHERE english_experience_summary IS NOT NULL
        """)).scalar()
        
        logger.info("\n📊 Overall Statistics:")
        logger.info(f"  Total providers with content: {total_providers}")
        logger.info(f"  Unique summaries: {unique_summaries}")
        logger.info(f"  Duplicate rate: {((total_providers - unique_summaries) / total_providers * 100):.1f}%")
        
        return fallback_count, duplicates
        
    finally:
        session.close()


def fix_duplicate_content(dry_run=False):
    """Fix duplicate content by clearing affected records"""
    db = DatabaseManager()
    session = db.get_session()
    
    try:
        logger.info("\n" + "="*60)
        logger.info("🔧 FIXING DUPLICATE CONTENT")
        logger.info("="*60)
        
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
        
        # Clear generic fallback content
        generic_fallback = "English language support is available for international patients."
        
        affected = session.execute(text("""
            SELECT COUNT(*) 
            FROM providers 
            WHERE english_experience_summary = :fallback
        """), {'fallback': generic_fallback}).scalar()
        
        if affected > 0:
            logger.info(f"\n🎯 Found {affected} providers with generic fallback content")
            
            if not dry_run:
                # Clear the generic content and reset status
                result = session.execute(text("""
                    UPDATE providers 
                    SET english_experience_summary = NULL,
                        review_summary = NULL,
                        ai_description = NULL,
                        ai_excerpt = NULL,
                        seo_title = NULL,
                        seo_meta_description = NULL,
                        status = 'pending'
                    WHERE english_experience_summary = :fallback
                """), {'fallback': generic_fallback})
                
                session.commit()
                logger.info(f"✅ Cleared content for {result.rowcount} providers")
            else:
                logger.info(f"Would clear content for {affected} providers")
        
        # Clear other significant duplicates (3+ occurrences)
        duplicates = session.execute(text("""
            SELECT english_experience_summary, COUNT(*) as count 
            FROM providers 
            WHERE english_experience_summary IS NOT NULL
            AND english_experience_summary != :fallback
            GROUP BY english_experience_summary 
            HAVING COUNT(*) >= 3
        """), {'fallback': generic_fallback}).fetchall()
        
        for dup in duplicates:
            logger.info(f"\n🎯 Found {dup.count} providers with duplicate content")
            logger.info(f"   Preview: {dup.english_experience_summary[:100]}...")
            
            if not dry_run:
                # Get the IDs of affected providers (keep the first one)
                affected_ids = session.execute(text("""
                    SELECT id 
                    FROM providers 
                    WHERE english_experience_summary = :summary
                    ORDER BY id
                    OFFSET 1
                """), {'summary': dup.english_experience_summary}).fetchall()
                
                if affected_ids:
                    ids_to_clear = [row.id for row in affected_ids]
                    
                    result = session.execute(text("""
                        UPDATE providers 
                        SET english_experience_summary = NULL,
                            review_summary = NULL,
                            ai_description = NULL,
                            ai_excerpt = NULL,
                            seo_title = NULL,
                            seo_meta_description = NULL,
                            status = 'pending'
                        WHERE id = ANY(:ids)
                    """), {'ids': ids_to_clear})
                    
                    session.commit()
                    logger.info(f"✅ Cleared duplicate content for {result.rowcount} providers (kept first occurrence)")
            else:
                logger.info(f"Would clear duplicate content for {dup.count - 1} providers (keeping first)")
        
        # Summary
        if not dry_run:
            # Get final statistics
            remaining_duplicates = session.execute(text("""
                SELECT COUNT(*) 
                FROM (
                    SELECT english_experience_summary, COUNT(*) as count 
                    FROM providers 
                    WHERE english_experience_summary IS NOT NULL
                    GROUP BY english_experience_summary 
                    HAVING COUNT(*) > 1
                ) as dups
            """)).scalar()
            
            logger.info("\n" + "="*60)
            logger.info("✅ DUPLICATE CONTENT FIXED")
            logger.info(f"   Remaining duplicates: {remaining_duplicates}")
            logger.info("   Re-run content generation for affected providers")
            logger.info("="*60)
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error: {e}")
        raise
        
    finally:
        session.close()


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix duplicate patient feedback')
    parser.add_argument('--analyze', action='store_true', help='Only analyze, don\'t fix')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    
    args = parser.parse_args()
    
    if args.analyze:
        analyze_duplicates()
    else:
        # Analyze first
        fallback_count, duplicates = analyze_duplicates()
        
        if fallback_count > 0 or duplicates:
            # Prompt for confirmation if not dry-run
            if not args.dry_run:
                response = input("\n⚠️  Proceed with fixing duplicate content? (yes/no): ")
                if response.lower() != 'yes':
                    logger.info("Operation cancelled")
                    return 1
            
            # Fix duplicates
            fix_duplicate_content(dry_run=args.dry_run)
        else:
            logger.info("\n✅ No duplicate content found!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())