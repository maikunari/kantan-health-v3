#!/usr/bin/env python3
"""
Add Geographic Providers Script (Unified Pipeline Version)

Searches and adds healthcare providers by geographic area (city, ward, prefecture).
This version uses the new unified pipeline architecture.

Usage:
    # Add providers in specific city
    python3 add_geographic_providers.py --city Tokyo --limit 20
    
    # Add providers in specific wards
    python3 add_geographic_providers.py --city Tokyo --wards "Shibuya,Minato" --limit 10
    
    # Filter by specialty
    python3 add_geographic_providers.py --city Osaka --specialty "Dentistry" --limit 15
    
    # Dry run to preview
    python3 add_geographic_providers.py --city Kyoto --dry-run
"""

import argparse
import sys
import os
import json
from typing import List, Dict, Optional

# Add src to path for new modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import from new unified modules
from src.core.pipeline import UnifiedPipeline, PipelineMode
from src.collectors.google_places import GooglePlacesCollector
from src.core.database import DatabaseManager


class GeographicProviderAdder:
    """Add providers by geographic area using unified pipeline"""
    
    def __init__(self):
        self.pipeline = UnifiedPipeline()
        self.collector = GooglePlacesCollector()
        self.db = DatabaseManager()
        
    def add_by_geographic_area(
        self,
        cities: List[str],
        wards: Optional[List[str]] = None,
        specialties: Optional[List[str]] = None,
        limit: int = 20,
        dry_run: bool = False
    ) -> Dict:
        """Add providers from specified geographic areas"""
        
        # Prepare collection options
        options = {
            'cities': cities,
            'limit': limit,
            'dry_run': dry_run,
            'queries_per_type': 2,  # Limit queries to control costs
            'results_per_query': 20
        }
        
        # Add optional filters
        if wards:
            options['wards'] = wards
        if specialties:
            options['specialties'] = specialties
        
        print(f"🌍 Searching for healthcare providers in: {', '.join(cities)}")
        if wards:
            print(f"   Wards: {', '.join(wards)}")
        if specialties:
            print(f"   Specialties: {', '.join(specialties)}")
        print(f"   Limit: {limit} providers")
        
        if dry_run:
            print("\n🔍 DRY RUN MODE - No changes will be made")
        
        # Run collection phase only
        results = self.pipeline.run(mode=PipelineMode.COLLECT, **options)
        
        # Extract collection results
        collection_results = results.get('collection', {})
        
        return {
            'success': results.get('status') == 'completed',
            'providers_found': collection_results.get('total_queries', 0) * 20,  # Approximate
            'providers_added': collection_results.get('new_providers', 0),
            'duplicates_skipped': collection_results.get('duplicates_skipped', 0),
            'rejected_proficiency': collection_results.get('rejected_proficiency', 0),
            'cost_estimate': collection_results.get('cost_summary', {}).get('total_cost', 0),
            'dry_run': dry_run
        }
    
    def run_pipeline_for_recent(self, provider_count: int, skip_content: bool = False, skip_wordpress: bool = False):
        """Run pipeline for recently added providers"""
        print(f"\n🚀 Running pipeline for {provider_count} recently added providers")
        
        # Get recently added providers
        session = self.db.get_session()
        try:
            from sqlalchemy import text
            recent_providers = session.execute(text("""
                SELECT id FROM providers 
                WHERE created_at = CURRENT_DATE
                ORDER BY id DESC
                LIMIT :limit
            """), {'limit': provider_count}).fetchall()
            
            provider_ids = [row.id for row in recent_providers]
        finally:
            session.close()
        
        if not provider_ids:
            print("❌ No recently added providers found")
            return
        
        print(f"📍 Found {len(provider_ids)} recent providers")
        
        # Prepare options
        options = {
            'provider_ids': provider_ids,
            'regenerate': False  # Only process those without content
        }
        
        # Determine pipeline mode
        if not skip_content and not skip_wordpress:
            mode = PipelineMode.FULL
        elif not skip_content:
            mode = PipelineMode.PROCESS
        elif not skip_wordpress:
            mode = PipelineMode.PUBLISH
        else:
            print("⚠️ Both content and WordPress sync skipped")
            return
        
        # Skip collection since we're working with existing providers
        options['skip_collection'] = True
        
        # Run pipeline
        results = self.pipeline.run(mode=mode, **options)
        
        # Show results
        if results.get('status') == 'completed':
            print("✅ Pipeline completed successfully")
            if 'processing' in results:
                print(f"   - Content generated: {results['processing'].get('successful', 0)}")
            if 'publishing' in results:
                print(f"   - WordPress synced: {results['publishing'].get('synced', 0)}")
        else:
            print("❌ Pipeline failed")


def main():
    parser = argparse.ArgumentParser(
        description='Add healthcare providers by geographic area',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Add providers from Tokyo
    python3 add_geographic_providers.py --city Tokyo --limit 20
    
    # Add dentists in specific Osaka wards
    python3 add_geographic_providers.py --city Osaka --wards "Kita,Chuo" --specialty Dentistry
    
    # Add from multiple cities
    python3 add_geographic_providers.py --cities "Tokyo,Yokohama,Osaka" --limit 50
    
    # Dry run to see what would be added
    python3 add_geographic_providers.py --city Kyoto --dry-run
        """
    )
    
    # Geographic parameters
    location_group = parser.add_mutually_exclusive_group()
    location_group.add_argument('--city', help='Single city to search in')
    location_group.add_argument('--cities', help='Comma-separated list of cities')
    
    parser.add_argument('--wards', help='Comma-separated list of wards/districts')
    parser.add_argument('--specialty', help='Medical specialty to filter by')
    
    # Collection parameters
    parser.add_argument('--limit', type=int, default=20,
                       help='Maximum number of providers to add (default: 20)')
    
    # Pipeline control
    parser.add_argument('--skip-content-generation', action='store_true',
                       help='Skip AI content generation')
    parser.add_argument('--skip-wordpress-sync', action='store_true',
                       help='Skip WordPress synchronization')
    
    # Other options
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview without making changes')
    parser.add_argument('--json-output', action='store_true',
                       help='Output results as JSON')
    
    args = parser.parse_args()
    
    # Prepare cities list
    if args.city:
        cities = [args.city]
    elif args.cities:
        cities = [c.strip() for c in args.cities.split(',')]
    else:
        parser.error('Either --city or --cities is required')
    
    # Prepare optional lists
    wards = [w.strip() for w in args.wards.split(',')] if args.wards else None
    specialties = [args.specialty] if args.specialty else None
    
    # Initialize adder
    adder = GeographicProviderAdder()
    
    # Add providers
    result = adder.add_by_geographic_area(
        cities=cities,
        wards=wards,
        specialties=specialties,
        limit=args.limit,
        dry_run=args.dry_run
    )
    
    # Handle output
    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        if result['success']:
            print(f"\n✅ Geographic search completed successfully")
            print(f"📊 Providers found: ~{result['providers_found']}")
            print(f"✨ New providers added: {result['providers_added']}")
            print(f"⏭️  Duplicates skipped: {result['duplicates_skipped']}")
            print(f"❌ Rejected (low English): {result['rejected_proficiency']}")
            print(f"💰 Estimated API cost: ${result['cost_estimate']:.2f}")
        else:
            print(f"\n❌ Geographic search failed")
    
    # Run pipeline for newly added providers if requested
    if result['success'] and not args.dry_run and result['providers_added'] > 0:
        if not args.skip_content_generation or not args.skip_wordpress_sync:
            adder.run_pipeline_for_recent(
                result['providers_added'],
                skip_content=args.skip_content_generation,
                skip_wordpress=args.skip_wordpress_sync
            )
    
    return 0 if result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())