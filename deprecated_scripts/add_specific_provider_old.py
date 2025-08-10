#!/usr/bin/env python3
"""
Add Specific Provider Script

Allows adding individual healthcare providers to the system either by:
1. Google Place ID (most reliable)
2. Provider name + location (searches Google Places)

Features:
- Duplicate detection using existing fingerprint system
- Full pipeline integration (Google Places → Database → AI Content → WordPress)
- Dry-run mode for validation
- Status tracking and logging

Usage:
    # Add by Google Place ID (most reliable)
    python3 add_specific_provider.py --place-id "ChIJN1t_tDeuEmsRUsoyG83frY4"
    
    # Add by name and location
    python3 add_specific_provider.py --name "Daikanyama Women's Clinic" --location "Tokyo"
    
    # Add by name only (searches Japan-wide)
    python3 add_specific_provider.py --name "Tokyo Medical University Hospital"
    
    # Dry run to check before adding
    python3 add_specific_provider.py --name "Clinic Name" --dry-run
    
    # Generate AI content immediately after adding
    python3 add_specific_provider.py --place-id "ChIJ..." --generate-content
"""

import argparse
import sys
import os
import time
import json
from typing import Optional, Dict, List

# Add src to path for new modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import from new unified modules
from src.collectors.google_places import GooglePlacesCollector
from src.processors.ai_content import AIContentProcessor
from src.publishers.wordpress import WordPressPublisher
from src.collectors.deduplication import ProviderDeduplicator
from src.core.database import Provider, DatabaseManager

class SpecificProviderAdder:
    """Add specific healthcare providers to the system"""
    
    def __init__(self):
        self.collector = GooglePlacesCollector()
        self.db_manager = DatabaseManager()
        self.session = self.db_manager.get_session()
        self.deduplicator = ProviderDeduplicator()
        
    def add_by_place_id(self, place_id: str, dry_run: bool = False) -> Dict:
        """Add provider using Google Place ID"""
        print(f"🔍 Adding provider by Place ID: {place_id}")
        
        # Get detailed place information
        place_data = self.collector.get_place_details(place_id)
        if not place_data:
            return {
                'success': False,
                'error': f'Could not retrieve place details for {place_id}',
                'provider': None
            }
        
        provider_name = place_data.get('name', 'Unknown Provider')
        print(f"📋 Found provider: {provider_name}")
        
        # Check for duplicates
        duplicate_check = self._check_for_duplicates(place_data)
        if duplicate_check['is_duplicate']:
            return {
                'success': False,
                'error': f'Provider already exists (matched on: {duplicate_check["match_type"]})',
                'provider': duplicate_check['existing_provider']
            }
        
        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'message': f'Provider {provider_name} would be added (no duplicates found)',
                'provider': place_data
            }
        
        # Create comprehensive provider record
        try:
            provider_record = self.collector.create_provider_record(place_data)
            
            # Check if provider was filtered out due to English proficiency
            if provider_record is None:
                return {
                    'success': False,
                    'error': f'Provider {provider_name} rejected: English proficiency score below 3 (Basic level required)',
                    'provider': None
                }
            
            # Validate provider has photos (requirement)
            if not self._validate_provider_photos(provider_record):
                return {
                    'success': False,
                    'error': f'Provider {provider_name} rejected: No photos available',
                    'provider': provider_record
                }
            
            # Save to database
            # Save using new database manager
            saved_provider = self.collector.save_providers([provider_record])
            saved_count = len(saved_provider)
            if saved_count > 0:
                return {
                    'success': True,
                    'message': f'Successfully added {provider_name}',
                    'provider': provider_record
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to save {provider_name} to database',
                    'provider': provider_record
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing {provider_name}: {str(e)}',
                'provider': None
            }
    
    def add_by_name(self, provider_name: str, location: str = "Japan", 
                   specialty: Optional[str] = None, dry_run: bool = False) -> Dict:
        """Add provider by searching for name and location"""
        specialty_text = f" ({specialty})" if specialty else ""
        print(f"🔍 Searching for provider: {provider_name}{specialty_text} in {location}")
        
        # Search Google Places with specialty context
        query_parts = [provider_name]
        if specialty:
            query_parts.append(specialty)
        if location != "Japan":
            query_parts.append(location)
        
        query = " ".join(query_parts)
        search_results = self.collector.search_providers(query)
        
        if not search_results:
            return {
                'success': False,
                'error': f'No results found for "{provider_name}" in {location}',
                'provider': None
            }
        
        # Find best match by name similarity
        best_match = self._find_best_name_match(provider_name, search_results)
        if not best_match:
            return {
                'success': False,
                'error': f'No good name matches found for "{provider_name}"',
                'provider': None,
                'search_results': [r.get('name', 'Unknown') for r in search_results[:5]]
            }
        
        print(f"📍 Best match: {best_match.get('name')} (Place ID: {best_match.get('place_id')})")
        
        # Use place ID to add the provider
        return self.add_by_place_id(best_match.get('place_id'), dry_run)
    
    def _check_for_duplicates(self, place_data: Dict) -> Dict:
        """Check if provider already exists using fingerprint system"""
        try:
            # Get existing fingerprints
            existing_fingerprints = set()
            
            # Get Google Place IDs
            existing_providers = self.session.query(Provider.google_place_id).filter(
                Provider.google_place_id.isnot(None)
            ).all()
            for provider in existing_providers:
                if provider.google_place_id:
                    existing_fingerprints.add(provider.google_place_id)
            
            # Get fingerprint data
            fingerprint_results = self.session.query(
                Provider.primary_fingerprint,
                Provider.secondary_fingerprint,
                Provider.fuzzy_fingerprint,
                Provider.provider_name,
                Provider.id
            ).filter(Provider.primary_fingerprint.isnot(None)).all()
            
            for fp_result in fingerprint_results:
                if fp_result.primary_fingerprint:
                    existing_fingerprints.add(fp_result.primary_fingerprint)
                if fp_result.secondary_fingerprint:
                    existing_fingerprints.add(fp_result.secondary_fingerprint)
                if fp_result.fuzzy_fingerprint:
                    existing_fingerprints.add(fp_result.fuzzy_fingerprint)
            
            # Create provider data for fingerprinting
            provider_data = {
                'provider_name': place_data.get('name', ''),
                'address': place_data.get('formatted_address', ''),
                'city': self._extract_city_from_place_data(place_data),
                'phone': place_data.get('formatted_phone_number', ''),
                'google_place_id': place_data.get('place_id', '')
            }
            
            # Check for duplicates
            is_duplicate, match_type = self.fingerprinter.check_duplicate(
                provider_data, existing_fingerprints
            )
            
            if is_duplicate:
                # Find the existing provider for details
                existing_provider = None
                if match_type == "google_place_id":
                    existing_provider = self.session.query(Provider).filter(
                        Provider.google_place_id == provider_data['google_place_id']
                    ).first()
                
                return {
                    'is_duplicate': True,
                    'match_type': match_type,
                    'existing_provider': existing_provider
                }
            
            return {'is_duplicate': False, 'match_type': None, 'existing_provider': None}
            
        except Exception as e:
            print(f"⚠️ Error checking duplicates: {str(e)}")
            return {'is_duplicate': False, 'match_type': None, 'existing_provider': None}
    
    def _extract_city_from_place_data(self, place_data: Dict) -> str:
        """Extract city from Google Places address components"""
        address_components = place_data.get('address_components', [])
        
        # Look for locality first
        for component in address_components:
            if 'locality' in component.get('types', []):
                return component.get('long_name', '')
        
        # Tokyo special case - use sublocality_level_1 as city
        administrative_area = next(
            (comp['long_name'] for comp in address_components 
             if 'administrative_area_level_1' in comp['types']), ''
        )
        
        if administrative_area in ['Tokyo', '東京都', 'Tokyo Metropolis']:
            sublocality = next(
                (comp['long_name'] for comp in address_components 
                 if 'sublocality_level_1' in comp['types']), ''
            )
            if sublocality:
                return 'Tokyo'  # Use Tokyo as city for all wards
        
        # Fallback to administrative area
        return administrative_area
    
    def _find_best_name_match(self, target_name: str, search_results: List[Dict]) -> Optional[Dict]:
        """Find the best name match from search results"""
        target_lower = target_name.lower()
        best_match = None
        best_score = 0
        
        for result in search_results:
            result_name = result.get('name', '').lower()
            
            # Exact match
            if target_lower == result_name:
                return result
            
            # Contains match
            if target_lower in result_name or result_name in target_lower:
                # Calculate simple similarity score
                score = len(set(target_lower.split()) & set(result_name.split()))
                if score > best_score:
                    best_score = score
                    best_match = result
        
        # Only return if we have a reasonable match
        return best_match if best_score >= 2 else None
    
    def _validate_provider_photos(self, provider_record: Dict) -> bool:
        """Validate provider has photos (system requirement)"""
        photo_urls = provider_record.get('photo_urls', '')
        
        if not photo_urls or photo_urls == '[]':
            return False
        
        try:
            import json
            if isinstance(photo_urls, str):
                photo_list = json.loads(photo_urls)
            else:
                photo_list = photo_urls
            
            return len(photo_list) > 0
        except:
            return False
    
    def generate_ai_content(self, provider_name: str) -> Dict:
        """Generate AI content for the added provider"""
        print(f"🤖 Generating AI content for {provider_name}...")
        
        try:
            # Find the provider in database
            provider = self.session.query(Provider).filter(
                Provider.provider_name.ilike(f'%{provider_name}%')
            ).first()
            
            if not provider:
                return {
                    'success': False,
                    'error': f'Provider {provider_name} not found in database'
                }
            
            # Use mega batch processor for single provider
            processor = ClaudeMegaBatchProcessor()
            results = processor.process_providers([provider], dry_run=False)
            
            if results['providers_processed'] > 0:
                return {
                    'success': True,
                    'message': f'AI content generated for {provider_name}',
                    'provider_id': provider.id
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to generate AI content for {provider_name}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error generating AI content: {str(e)}'
            }
    
    def sync_to_wordpress(self, provider_name: str) -> Dict:
        """Sync provider to WordPress"""
        print(f"🌐 Syncing {provider_name} to WordPress...")
        
        try:
            sync_manager = WordPressSyncManager()
            result = sync_manager.sync_single_provider(provider_name)
            
            return {
                'success': result.get('status') == 'success',
                'message': result.get('message', 'Sync completed')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error syncing to WordPress: {str(e)}'
            }
    
    def close(self):
        """Close database session"""
        self.session.close()

def main():
    parser = argparse.ArgumentParser(description='Add specific healthcare provider to the system')
    
    # Provider identification
    provider_group = parser.add_mutually_exclusive_group(required=True)
    provider_group.add_argument('--place-id', help='Google Place ID')
    provider_group.add_argument('--name', help='Provider name to search for')
    
    # Optional parameters
    parser.add_argument('--location', default='Japan', 
                       help='Location to search in (default: Japan)')
    parser.add_argument('--specialty', 
                       help='Medical specialty to help filter search results (e.g., "ENT", "cardiology")')
    parser.add_argument('--dry-run', action='store_true',
                       help='Check for duplicates without adding')
    parser.add_argument('--skip-content-generation', action='store_true',
                       help='Skip AI content generation (default: generate content)')
    parser.add_argument('--skip-wordpress-sync', action='store_true',
                       help='Skip WordPress sync (default: sync to WordPress)')
    parser.add_argument('--json-output', action='store_true',
                       help='Output results in JSON format for API consumption')
    
    # Legacy flags (for backward compatibility)
    parser.add_argument('--generate-content', action='store_true',
                       help='Generate AI content after adding (default behavior)')
    parser.add_argument('--sync-wordpress', action='store_true',
                       help='Sync to WordPress after adding (default behavior)')
    
    args = parser.parse_args()
    
    if not args.json_output:
        print("🏥 SPECIFIC PROVIDER ADDITION")
        print("=" * 50)
    
    adder = SpecificProviderAdder()
    
    try:
        # Add provider
        if args.place_id:
            result = adder.add_by_place_id(args.place_id, args.dry_run)
        else:
            result = adder.add_by_name(args.name, args.location, args.specialty, args.dry_run)
        
        # Display result
        if result['success']:
            if result.get('dry_run'):
                print(f"✅ DRY RUN: {result['message']}")
            else:
                print(f"✅ SUCCESS: {result['message']}")
                
                provider_name = result['provider']['provider_name']
                
                # Determine if we should generate AI content (default: yes, unless skipped)
                should_generate_content = (
                    not args.skip_content_generation and 
                    not args.dry_run
                )
                
                # Generate AI content (default behavior)
                if should_generate_content:
                    print("\n" + "="*50)
                    print("🤖 GENERATING AI CONTENT (default behavior)")
                    content_result = adder.generate_ai_content(provider_name)
                    if content_result['success']:
                        print(f"✅ {content_result['message']}")
                    else:
                        print(f"❌ AI Content Error: {content_result['error']}")
                
                # Determine if we should sync to WordPress (default: yes, unless skipped)
                should_sync_wordpress = (
                    not args.skip_wordpress_sync and 
                    not args.dry_run
                )
                
                # Sync to WordPress (default behavior)
                if should_sync_wordpress:
                    print("\n" + "="*50)
                    print("🌐 SYNCING TO WORDPRESS (default behavior)")
                    sync_result = adder.sync_to_wordpress(provider_name)
                    if sync_result['success']:
                        print(f"✅ WordPress: {sync_result['message']}")
                    else:
                        print(f"❌ WordPress Error: {sync_result['error']}")
                        
                # Show what was skipped (if anything)
                if args.skip_content_generation:
                    print("\n⏭️ Skipped AI content generation (--skip-content-generation)")
                if args.skip_wordpress_sync:
                    print("⏭️ Skipped WordPress sync (--skip-wordpress-sync)")
        else:
            print(f"❌ ERROR: {result['error']}")
            if 'search_results' in result:
                print(f"🔍 Found these alternatives: {', '.join(result['search_results'])}")
            
            if result.get('provider'):
                print(f"📋 Provider found but not added: {result['provider'].get('provider_name', 'Unknown')}")
            
            if not args.json_output:
                sys.exit(1)
        
        # Output JSON result if requested
        if args.json_output:
            json_result = {
                'success': result['success'],
                'message': result['message'],
                'dry_run': result.get('dry_run', False),
                'provider_id': result.get('provider', {}).get('id') if result.get('provider') else None,
                'provider_name': result.get('provider', {}).get('provider_name') if result.get('provider') else None,
                'error': result.get('error') if not result['success'] else None
            }
            print(json.dumps(json_result, indent=2))
    
    except KeyboardInterrupt:
        if not args.json_output:
            print("\n⏹️ Operation cancelled by user")
        else:
            print(json.dumps({'success': False, 'error': 'Operation cancelled by user'}))
        sys.exit(1)
    except Exception as e:
        if not args.json_output:
            print(f"❌ Unexpected error: {str(e)}")
        else:
            print(json.dumps({'success': False, 'error': str(e)}))
        sys.exit(1)
    finally:
        adder.close()

if __name__ == "__main__":
    main() 