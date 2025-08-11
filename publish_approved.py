#!/usr/bin/env python3
"""
Publish Approved Providers to WordPress (Unified Pipeline Version)
Creates initial WordPress posts for providers that have content but no WordPress post yet.
This addresses the gap where providers get stuck in 'description_generated' status.

Usage:
    # Publish all approved providers without WordPress posts
    python3 publish_approved.py
    
    # Limit number to publish
    python3 publish_approved.py --limit 10
    
    # Dry run to see what would be published
    python3 publish_approved.py --dry-run
"""

import argparse
import sys
import os
from typing import List

# Add src to path for new modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import from new unified modules
from src.core.database import DatabaseManager, Provider
from src.core.pipeline import UnifiedPipeline, PipelineMode
from sqlalchemy import and_, or_


def get_providers_needing_wordpress(db: DatabaseManager, limit: int = None) -> List[Provider]:
    """Get providers with AI content but no WordPress post"""
    session = db.get_session()
    try:
        query = session.query(Provider).filter(
            and_(
                # Has AI content
                Provider.ai_description.isnot(None),
                Provider.ai_description != '',
                # No WordPress post yet
                Provider.wordpress_post_id.is_(None),
                # Status indicates content was generated
                or_(
                    Provider.status == 'approved',
                    Provider.status == 'description_generated'
                )
            )
        )
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description='Publish approved providers to WordPress',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script creates initial WordPress posts for providers that have AI-generated
content but haven't been published yet. It's useful for:

1. Publishing providers stuck in 'description_generated' status
2. Creating WordPress posts for manually approved providers
3. Bulk publishing after content generation

Examples:
    # Publish all pending providers
    python3 publish_approved.py
    
    # Publish up to 25 providers
    python3 publish_approved.py --limit 25
    
    # See what would be published
    python3 publish_approved.py --dry-run
        """
    )
    
    parser.add_argument('--limit', type=int, default=50,
                       help='Maximum number of providers to publish (default: 50)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be published without making changes')
    
    args = parser.parse_args()
    
    # Initialize
    db = DatabaseManager()
    pipeline = UnifiedPipeline()
    
    # Find providers needing WordPress posts
    print("🔍 Finding providers with content but no WordPress post...")
    providers = get_providers_needing_wordpress(db, limit=args.limit)
    
    if not providers:
        print("✅ No providers need WordPress publishing")
        return 0
    
    print(f"📊 Found {len(providers)} providers to publish:")
    for i, provider in enumerate(providers[:10], 1):
        print(f"   {i}. {provider.provider_name} (ID: {provider.id}, Status: {provider.status})")
    if len(providers) > 10:
        print(f"   ... and {len(providers) - 10} more")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - No changes will be made")
        return 0
    
    # Get provider IDs
    provider_ids = [p.id for p in providers]
    
    # Run publish phase of pipeline
    print(f"\n🚀 Publishing {len(provider_ids)} providers to WordPress...")
    
    try:
        results = pipeline.run(
            mode=PipelineMode.PUBLISH,
            provider_ids=provider_ids
        )
    except Exception as e:
        print(f"\n❌ Pipeline error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Show results
    publishing_phase = results.get('phases', {}).get('publishing', {})
    
    # Check if we actually had any providers to publish
    if publishing_phase.get('total_providers', 0) == 0:
        print(f"\n✅ No providers needed publishing (all already have WordPress posts)")
        return 0
    
    if publishing_phase and not publishing_phase.get('error'):
        print(f"\n✅ Publishing completed successfully")
        print(f"   - Created: {publishing_phase.get('created', 0)} posts")
        print(f"   - Updated: {publishing_phase.get('updated', 0)} posts")
        print(f"   - Failed: {publishing_phase.get('failed', 0)}")
        
        # Update status for successfully published providers
        if publishing_phase.get('created', 0) > 0 or publishing_phase.get('updated', 0) > 0:
            session = db.get_session()
            try:
                # Update status to 'published' for providers with WordPress posts
                session.execute("""
                    UPDATE providers 
                    SET status = 'published' 
                    WHERE id = ANY(:ids) 
                    AND wordpress_post_id IS NOT NULL
                    AND status IN ('approved', 'description_generated')
                """, {'ids': provider_ids})
                session.commit()
                print(f"   - Updated status to 'published' for successful posts")
            finally:
                session.close()
    else:
        print(f"\n❌ Publishing failed")
        if publishing_phase.get('error'):
            print(f"   Error: {publishing_phase.get('error')}")
        if publishing_phase.get('errors'):
            for error in publishing_phase.get('errors', [])[:5]:
                print(f"   - {error}")
    
    return 0 if not publishing_phase.get('error') else 1


if __name__ == '__main__':
    sys.exit(main())