#!/usr/bin/env python3
"""
Add Specific Provider Script (Unified Pipeline Version)

Allows adding individual healthcare providers to the system either by:
1. Google Place ID (most reliable)
2. Provider name + location (searches Google Places)

This version uses the new unified pipeline architecture.

Usage:
    # Add by Google Place ID (most reliable)
    python3 add_specific_provider.py --place-id "ChIJN1t_tDeuEmsRUsoyG83frY4"
    
    # Add by name and location
    python3 add_specific_provider.py --name "Daikanyama Women's Clinic" --location "Tokyo"
    
    # Add by name only (searches Japan-wide)
    python3 add_specific_provider.py --name "Tokyo Medical University Hospital"
    
    # Dry run to check before adding
    python3 add_specific_provider.py --name "Clinic Name" --dry-run
"""

import argparse
import sys
import os
import json
from typing import Optional, Dict

# Add src to path for new modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import from new unified modules
from src.collectors.google_places import GooglePlacesCollector
from src.core.database import DatabaseManager, Provider
from src.core.pipeline import UnifiedPipeline, PipelineMode


class SpecificProviderAdder:
    """Add specific healthcare providers using unified pipeline"""
    
    def __init__(self):
        self.collector = GooglePlacesCollector()
        self.db = DatabaseManager()
        self.pipeline = UnifiedPipeline()
        
    def add_by_place_id(self, place_id: str, dry_run: bool = False) -> Dict:
        """Add provider using Google Place ID"""
        print(f"🔍 Adding provider by Place ID: {place_id}")
        
        # Get detailed place information
        place_data = self.collector.get_place_details(place_id)
        if not place_data:
            return {
                'success': False,
                'message': f'Could not find place with ID: {place_id}',
                'provider_id': None
            }
        
        # Check if already exists
        existing = self.db.get_provider_by_place_id(place_id)
        if existing:
            return {
                'success': True,
                'message': f'Provider already exists: {existing.provider_name} (ID: {existing.id})',
                'provider_id': existing.id,
                'provider_name': existing.provider_name,
                'already_exists': True
            }
        
        if dry_run:
            # Just show what would be added
            provider_name = place_data.get('name', 'Unknown')
            return {
                'success': True,
                'message': f'[DRY RUN] Would add: {provider_name}',
                'provider_data': {
                    'name': provider_name,
                    'address': place_data.get('formatted_address'),
                    'phone': place_data.get('formatted_phone_number'),
                    'rating': place_data.get('rating'),
                    'reviews': place_data.get('user_ratings_total', 0)
                },
                'dry_run': True
            }
        
        # Create provider record
        provider_record = self.collector.create_provider_record(place_data)
        if not provider_record:
            return {
                'success': False,
                'message': 'Provider filtered out (likely due to low English proficiency)',
                'provider_id': None
            }
        
        # Save provider
        saved_providers = self.collector.save_providers([provider_record])
        if not saved_providers:
            return {
                'success': False,
                'message': 'Failed to save provider',
                'provider_id': None
            }
        
        provider_id = saved_providers[0]['id']
        provider_name = saved_providers[0]['name']
        
        return {
            'success': True,
            'message': f'Successfully added: {provider_name}',
            'provider_id': provider_id,
            'provider_name': provider_name,
            'google_place_id': place_id
        }
    
    def add_by_name(self, name: str, location: str = "Japan", dry_run: bool = False) -> Dict:
        """Add provider by searching for name and location"""
        print(f"🔍 Searching for: {name} in {location}")
        
        # Build search query
        query_parts = [name]
        if location != "Japan":
            query_parts.append(location)
        
        query = " ".join(query_parts)
        search_results = self.collector.search_providers(query, max_results=5)
        
        if not search_results:
            return {
                'success': False,
                'message': f'No providers found matching: {name} in {location}',
                'provider_id': None
            }
        
        # Use the first result
        best_match = search_results[0]
        place_id = best_match['place_id']
        
        # Check if already exists
        existing = self.db.get_provider_by_place_id(place_id)
        if existing:
            return {
                'success': True,
                'message': f'Provider already exists: {existing.provider_name} (ID: {existing.id})',
                'provider_id': existing.id,
                'provider_name': existing.provider_name,
                'already_exists': True
            }
        
        if dry_run:
            return {
                'success': True,
                'message': f'[DRY RUN] Would add: {best_match["name"]}',
                'provider_data': best_match,
                'search_results': search_results,
                'dry_run': True
            }
        
        # Add the provider using place ID
        return self.add_by_place_id(place_id, dry_run=False)
    
    def run_pipeline_for_provider(self, provider_id: int, skip_content: bool = False, skip_wordpress: bool = False):
        """Run the pipeline for a specific provider"""
        print(f"\n🚀 Running pipeline for provider ID: {provider_id}")
        
        # Prepare options
        options = {
            'provider_ids': [provider_id],
            'regenerate': True  # Process even if content exists
        }
        
        # Run appropriate pipeline mode
        if not skip_content and not skip_wordpress:
            # Run full pipeline (process + publish)
            mode = PipelineMode.FULL
        elif not skip_content:
            # Just process content
            mode = PipelineMode.PROCESS
        elif not skip_wordpress:
            # Just publish
            mode = PipelineMode.PUBLISH
        else:
            print("⚠️ Both content and WordPress sync skipped - nothing to do")
            return
        
        # Skip collection phase since we're working with existing provider
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
            if results.get('errors'):
                for error in results['errors'][:3]:
                    print(f"   - {error}")


def main():
    parser = argparse.ArgumentParser(
        description='Add specific healthcare provider to the system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Add by Google Place ID
    python3 add_specific_provider.py --place-id "ChIJN1t_tDeuEmsRUsoyG83frY4"
    
    # Add by name and location
    python3 add_specific_provider.py --name "Tokyo Medical Clinic" --location "Shibuya"
    
    # Dry run to preview
    python3 add_specific_provider.py --name "Test Clinic" --dry-run
    
    # Add and generate content immediately
    python3 add_specific_provider.py --place-id "ChIJ..." --generate-content
    
    # Add without running pipeline
    python3 add_specific_provider.py --place-id "ChIJ..." --skip-content-generation --skip-wordpress-sync
        """
    )
    
    # Provider identification
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--place-id', help='Google Place ID of the provider')
    group.add_argument('--name', help='Name of the healthcare provider')
    
    # Additional parameters
    parser.add_argument('--location', default='Japan', 
                       help='Location to search in (default: Japan)')
    parser.add_argument('--specialty', help='Medical specialty (optional)')
    
    # Pipeline control
    parser.add_argument('--generate-content', action='store_true',
                       help='Generate AI content immediately after adding')
    parser.add_argument('--skip-content-generation', action='store_true',
                       help='Skip AI content generation')
    parser.add_argument('--skip-wordpress-sync', action='store_true',
                       help='Skip WordPress synchronization')
    
    # Other options
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview what would be added without making changes')
    parser.add_argument('--json-output', action='store_true',
                       help='Output results as JSON')
    
    args = parser.parse_args()
    
    # Initialize adder
    adder = SpecificProviderAdder()
    
    # Add provider
    if args.place_id:
        result = adder.add_by_place_id(args.place_id, dry_run=args.dry_run)
    else:
        result = adder.add_by_name(args.name, args.location, dry_run=args.dry_run)
    
    # Handle output
    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        if result['success']:
            print(f"\n✅ {result['message']}")
            if 'provider_id' in result and result['provider_id']:
                print(f"📍 Provider ID: {result['provider_id']}")
            if 'dry_run' in result and result['dry_run']:
                if 'search_results' in result:
                    print(f"\n🔍 Found {len(result['search_results'])} matches:")
                    for i, match in enumerate(result['search_results'][:3], 1):
                        print(f"   {i}. {match['name']} - {match.get('vicinity', 'No address')}")
        else:
            print(f"\n❌ {result['message']}")
    
    # Run pipeline if requested and not dry run
    if result['success'] and not args.dry_run and result.get('provider_id'):
        if args.generate_content or (not args.skip_content_generation or not args.skip_wordpress_sync):
            adder.run_pipeline_for_provider(
                result['provider_id'],
                skip_content=args.skip_content_generation,
                skip_wordpress=args.skip_wordpress_sync
            )
    
    return 0 if result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())