#!/usr/bin/env python3
"""
Geographic Provider Addition Script

Allows bulk addition of healthcare providers by geographic targeting:
1. City-level targeting (e.g., "Tokyo", "Osaka")
2. Ward-level targeting (e.g., "Tokyo Shibuya", "Tokyo Minato") 
3. Custom geographic queries

Features:
- Intelligent query generation for geographic areas
- Duplicate prevention using existing fingerprint system
- Configurable provider limits per area
- Full pipeline integration (Google Places → AI Content → WordPress)
- Progress tracking and resumable operations

Usage:
    # Add 10 providers from Tokyo (all areas)
    python3 add_geographic_providers.py --city "Tokyo" --limit 10
    
    # Add 5 providers from specific Tokyo wards
    python3 add_geographic_providers.py --city "Tokyo" --wards "Shibuya,Minato,Shinjuku" --limit 5
    
    # Add 15 providers from multiple cities
    python3 add_geographic_providers.py --cities "Tokyo,Osaka,Yokohama" --limit 15
    
    # Dry run to see what would be found
    python3 add_geographic_providers.py --city "Tokyo" --limit 5 --dry-run
    
    # Generate all content immediately
    python3 add_geographic_providers.py --city "Tokyo" --limit 10 --generate-content --sync-wordpress
"""

import argparse
import sys
import time
import json
from typing import List, Dict, Set, Optional
from google_places_integration import GooglePlacesHealthcareCollector
from claude_mega_batch_processor import ClaudeMegaBatchProcessor
from wordpress_sync_manager import WordPressSyncManager
from postgres_integration import Provider

class GeographicProviderAdder:
    """Add healthcare providers by geographic targeting"""
    
    def __init__(self):
        self.collector = GooglePlacesHealthcareCollector()
        self.session = self.collector.Session()
        
        # Load geographic data
        with open("cities.json", "r") as f:
            self.geographic_data = json.load(f)
        
        # Load medical specialties
        with open("specialties-full.json", "r") as f:
            self.specialties_data = json.load(f)
        
        # Extended Tokyo wards (all 23 special wards)
        self.tokyo_wards = [
            "Adachi", "Arakawa", "Bunkyo", "Chiyoda", "Chuo", "Edogawa",
            "Itabashi", "Katsushika", "Kita", "Koto", "Meguro", "Minato",
            "Nakano", "Nerima", "Ota", "Setagaya", "Shibuya", "Shinagawa",
            "Shinjuku", "Suginami", "Sumida", "Taito", "Toshima"
        ]
        
        # Comprehensive specialty mappings and aliases
        self.specialty_mappings = {
            # ENT variations
            'ent': ['ENT', 'ear nose throat', 'otolaryngologist', 'otolaryngology', 'throat doctor'],
            'ear nose throat': ['ENT', 'ear nose throat', 'otolaryngologist', 'otolaryngology'],
            'otolaryngology': ['ENT', 'ear nose throat', 'otolaryngologist', 'otolaryngology'],
            
            # Cardiology variations
            'cardiology': ['cardiologist', 'cardiology', 'heart doctor', 'heart specialist'],
            'cardiologist': ['cardiologist', 'cardiology', 'heart doctor', 'heart specialist'],
            
            # Dermatology variations
            'dermatology': ['dermatologist', 'dermatology', 'skin doctor', 'skin specialist'],
            'dermatologist': ['dermatologist', 'dermatology', 'skin doctor', 'skin specialist'],
            
            # Gynecology variations
            'gynecology': ['gynecologist', 'gynecology', 'women health', 'womens clinic'],
            'gynecologist': ['gynecologist', 'gynecology', 'women health', 'womens clinic'],
            
            # Pediatrics variations
            'pediatrics': ['pediatrician', 'pediatrics', 'children doctor', 'kids doctor'],
            'pediatrician': ['pediatrician', 'pediatrics', 'children doctor', 'kids doctor'],
            
            # Orthopedics variations
            'orthopedics': ['orthopedic surgeon', 'orthopedics', 'bone doctor', 'joint specialist'],
            'orthopedic': ['orthopedic surgeon', 'orthopedics', 'bone doctor', 'joint specialist'],
            
            # Ophthalmology variations
            'ophthalmology': ['ophthalmologist', 'ophthalmology', 'eye doctor', 'eye specialist'],
            'ophthalmologist': ['ophthalmologist', 'ophthalmology', 'eye doctor', 'eye specialist'],
            
            # Neurology variations
            'neurology': ['neurologist', 'neurology', 'brain doctor', 'nerve specialist'],
            'neurologist': ['neurologist', 'neurology', 'brain doctor', 'nerve specialist'],
            
            # Psychiatry variations
            'psychiatry': ['psychiatrist', 'psychiatry', 'mental health', 'psychological'],
            'psychiatrist': ['psychiatrist', 'psychiatry', 'mental health', 'psychological'],
            
            # General medicine variations
            'general medicine': ['general practitioner', 'family medicine', 'internal medicine', 'primary care'],
            'internal medicine': ['internal medicine', 'general practitioner', 'family medicine'],
            
            # Dentistry variations
            'dentistry': ['dentist', 'dentistry', 'dental clinic', 'oral health'],
            'dentist': ['dentist', 'dentistry', 'dental clinic', 'oral health'],
            
            # Oncology variations
            'oncology': ['oncologist', 'oncology', 'cancer doctor', 'cancer specialist'],
            'oncologist': ['oncologist', 'oncology', 'cancer doctor', 'cancer specialist'],
            
            # Urology variations
            'urology': ['urologist', 'urology', 'kidney doctor', 'bladder specialist'],
            'urologist': ['urologist', 'urology', 'kidney doctor', 'bladder specialist'],
            
            # Emergency medicine
            'emergency medicine': ['emergency medicine', 'emergency doctor', 'urgent care'],
            'emergency': ['emergency medicine', 'emergency doctor', 'urgent care'],
            
            # Surgery variations
            'surgery': ['surgeon', 'surgery', 'surgical specialist'],
            'surgeon': ['surgeon', 'surgery', 'surgical specialist']
        }
        
        # Healthcare search terms for geographic targeting
        self.search_terms = [
            "clinic", "hospital", "medical center", "doctor", "healthcare",
            "internal medicine", "family medicine", "general practice",
            "cardiology", "dermatology", "gynecology", "pediatrics",
            "orthopedics", "ophthalmology", "dentist", "dental clinic"
        ]
        
        # English-focused modifiers
        self.english_modifiers = [
            "english speaking", "international", "foreign friendly",
            "bilingual", "expat friendly", "english support"
        ]
    
    def add_by_city(self, city: str, limit: int, wards: Optional[List[str]] = None, 
                   specialty: Optional[str] = None, dry_run: bool = False) -> Dict:
        """Add providers from specific city or city areas"""
        specialty_text = f" {specialty} specialists" if specialty else ""
        print(f"🏙️ Adding {limit}{specialty_text} providers from {city}")
        
        if wards:
            print(f"📍 Targeting wards: {', '.join(wards)}")
            queries = self._generate_ward_queries(city, wards, specialty)
        else:
            queries = self._generate_city_queries(city, specialty)
        
        area_desc = f"{city} city{specialty_text}"
        return self._execute_geographic_search(queries, limit, dry_run, area_desc)
    
    def add_by_cities(self, cities: List[str], limit: int, specialty: Optional[str] = None, 
                     dry_run: bool = False) -> Dict:
        """Add providers from multiple cities"""
        specialty_text = f" {specialty} specialists" if specialty else ""
        print(f"🌆 Adding {limit}{specialty_text} providers from {len(cities)} cities: {', '.join(cities)}")
        
        # Distribute limit across cities
        limit_per_city = max(1, limit // len(cities))
        remaining_limit = limit - (limit_per_city * len(cities))
        
        all_results = []
        total_added = 0
        
        for i, city in enumerate(cities):
            city_limit = limit_per_city + (1 if i < remaining_limit else 0)
            print(f"\n🏙️ Processing {city} (target: {city_limit}{specialty_text} providers)")
            
            queries = self._generate_city_queries(city, specialty)
            result = self._execute_geographic_search(
                queries, city_limit, dry_run, f"{city} city{specialty_text}"
            )
            
            all_results.append({
                'city': city,
                'result': result
            })
            
            total_added += result.get('providers_added', 0)
            
            if total_added >= limit:
                break
        
        return {
            'success': True,
            'providers_added': total_added,
            'cities_processed': len(all_results),
            'city_results': all_results
        }
    
    def _generate_city_queries(self, city: str, specialty: Optional[str] = None) -> List[str]:
        """Generate search queries for a city with optional specialty filtering"""
        queries = []
        
        if specialty:
            # Get specialty variations
            specialty_terms = self._get_specialty_terms(specialty)
            
            # Specialty-focused queries
            for term in specialty_terms:
                queries.append(f"{term} {city}")
                queries.append(f"{term} clinic {city}")
                queries.append(f"{term} doctor {city}")
            
            # English-focused specialty queries
            for modifier in self.english_modifiers:
                for term in specialty_terms[:3]:  # Use top 3 terms to avoid too many queries
                    queries.append(f"{modifier} {term} {city}")
            
            # Location + specialty combinations
            queries.extend([
                f"{specialty} specialist {city}",
                f"{specialty} doctor {city}",
                f"{specialty} clinic {city}",
                f"private {specialty} {city}"
            ])
        else:
            # Basic geographic terms (original behavior)
            for term in self.search_terms:
                queries.append(f"{term} {city}")
            
            # English-focused queries
            for modifier in self.english_modifiers:
                for term in ["clinic", "doctor", "hospital"]:
                    queries.append(f"{modifier} {term} {city}")
            
            # Location-specific queries
            queries.extend([
                f"healthcare {city}",
                f"medical services {city}",
                f"private clinic {city}",
                f"specialist doctor {city}"
            ])
        
        return queries
    
    def _generate_ward_queries(self, city: str, wards: List[str], specialty: Optional[str] = None) -> List[str]:
        """Generate search queries for specific wards with optional specialty filtering"""
        queries = []
        
        for ward in wards:
            if specialty:
                # Get specialty variations
                specialty_terms = self._get_specialty_terms(specialty)
                
                # Ward + specialty combinations
                for term in specialty_terms[:3]:  # Limit to top 3 terms
                    queries.append(f"{term} {ward} {city}")
                    queries.append(f"{term} {ward}")
                
                # English-focused ward + specialty queries
                for modifier in ["english speaking", "international", "foreign friendly"]:
                    queries.append(f"{modifier} {specialty} {ward}")
                    queries.append(f"{modifier} {specialty} doctor {ward}")
                
                # Specific combinations
                queries.extend([
                    f"{specialty} specialist {ward} {city}",
                    f"{specialty} clinic {ward}",
                    f"private {specialty} {ward}"
                ])
            else:
                # Ward-specific queries (original behavior)
                for term in ["clinic", "hospital", "doctor", "medical center"]:
                    queries.append(f"{term} {ward} {city}")
                    queries.append(f"{term} {ward}")
                
                # English-focused ward queries
                for modifier in ["english speaking", "international", "foreign friendly"]:
                    queries.append(f"{modifier} doctor {ward}")
                    queries.append(f"{modifier} clinic {ward} {city}")
        
        return queries
    
    def _get_specialty_terms(self, specialty: str) -> List[str]:
        """Get all search terms and variations for a specialty"""
        if not specialty:
            return []
        
        specialty_lower = specialty.lower()
        
        # Check if we have predefined mappings
        if specialty_lower in self.specialty_mappings:
            return self.specialty_mappings[specialty_lower]
        
        # If no mapping found, return the original specialty plus common variations
        terms = [specialty, f"{specialty} doctor", f"{specialty} specialist"]
        
        # Add common suffix variations
        if not specialty_lower.endswith('ist') and not specialty_lower.endswith('logy'):
            if specialty_lower in ['cardio', 'neuro', 'dermato', 'uro', 'gyneco', 'pediatr']:
                terms.append(f"{specialty}logist")
                terms.append(f"{specialty}logy")
        
        return terms
    
    def _execute_geographic_search(self, queries: List[str], limit: int, 
                                 dry_run: bool, area_name: str) -> Dict:
        """Execute geographic search with the given queries"""
        print(f"🔍 Generated {len(queries)} search queries for {area_name}")
        
        # Get existing providers to avoid duplicates
        existing_fingerprints = self._get_existing_fingerprints()
        print(f"📊 Found {len(existing_fingerprints)} existing provider fingerprints")
        
        providers_found = []
        processed_place_ids = set()
        queries_processed = 0
        
        for query in queries:
            if len(providers_found) >= limit:
                break
            
            print(f"🔍 Query {queries_processed + 1}/{len(queries)}: {query}")
            
            # Search Google Places
            search_results = self.collector.search_healthcare_providers(query)
            queries_processed += 1
            
            if not search_results:
                continue
            
            # Process results
            for result in search_results:
                if len(providers_found) >= limit:
                    break
                
                place_id = result.get('place_id')
                if not place_id or place_id in processed_place_ids:
                    continue
                
                processed_place_ids.add(place_id)
                
                # Get detailed information
                place_data = self.collector.get_place_details(place_id)
                if not place_data:
                    continue
                
                # Check for duplicates
                if self._is_duplicate_provider(place_data, existing_fingerprints):
                    provider_name = place_data.get('name', 'Unknown')
                    print(f"⏭️ Skipping duplicate: {provider_name}")
                    continue
                
                # Create provider record
                try:
                    provider_record = self.collector.create_comprehensive_provider_record(place_data)
                    
                    # Validate photos (system requirement)
                    if not self._validate_provider_photos(provider_record):
                        print(f"📸 Skipping {provider_record.get('provider_name', 'Unknown')}: No photos")
                        continue
                    
                    providers_found.append(provider_record)
                    print(f"✅ Found: {provider_record.get('provider_name', 'Unknown')}")
                    
                    # Add to existing fingerprints to prevent duplicates within this session
                    provider_fingerprints = self._generate_provider_fingerprints(provider_record)
                    existing_fingerprints.update(provider_fingerprints)
                    
                except Exception as e:
                    print(f"❌ Error processing provider: {str(e)}")
                    continue
            
            # Rate limiting
            time.sleep(0.5)
        
        print(f"📋 Search complete: Found {len(providers_found)} unique providers")
        
        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'providers_found': len(providers_found),
                'queries_processed': queries_processed,
                'provider_names': [p.get('provider_name', 'Unknown') for p in providers_found]
            }
        
        # Save providers to database
        if providers_found:
            saved_count = self.collector.save_to_postgres(providers_found)
            
            return {
                'success': True,
                'providers_added': saved_count,
                'providers_found': len(providers_found),
                'queries_processed': queries_processed,
                'area_name': area_name
            }
        else:
            return {
                'success': False,
                'error': f'No valid providers found in {area_name}',
                'queries_processed': queries_processed
            }
    
    def _get_existing_fingerprints(self) -> Set[str]:
        """Get all existing provider fingerprints for duplicate detection"""
        fingerprints = set()
        
        # Get Google Place IDs
        place_ids = self.session.query(Provider.google_place_id).filter(
            Provider.google_place_id.isnot(None)
        ).all()
        for pid in place_ids:
            if pid.google_place_id:
                fingerprints.add(pid.google_place_id)
        
        # Get fingerprint data
        fp_results = self.session.query(
            Provider.primary_fingerprint,
            Provider.secondary_fingerprint,
            Provider.fuzzy_fingerprint
        ).filter(Provider.primary_fingerprint.isnot(None)).all()
        
        for fp in fp_results:
            if fp.primary_fingerprint:
                fingerprints.add(fp.primary_fingerprint)
            if fp.secondary_fingerprint:
                fingerprints.add(fp.secondary_fingerprint)
            if fp.fuzzy_fingerprint:
                fingerprints.add(fp.fuzzy_fingerprint)
        
        return fingerprints
    
    def _is_duplicate_provider(self, place_data: Dict, existing_fingerprints: Set[str]) -> bool:
        """Check if provider is duplicate using fingerprint system"""
        from provider_fingerprinting import ProviderFingerprinter
        
        fingerprinter = ProviderFingerprinter()
        
        # Create provider data for fingerprinting
        provider_data = {
            'provider_name': place_data.get('name', ''),
            'address': place_data.get('formatted_address', ''),
            'city': self._extract_city_from_place_data(place_data),
            'phone': place_data.get('formatted_phone_number', ''),
            'google_place_id': place_data.get('place_id', '')
        }
        
        is_duplicate, _ = fingerprinter.check_duplicate(provider_data, existing_fingerprints)
        return is_duplicate
    
    def _generate_provider_fingerprints(self, provider_record: Dict) -> Set[str]:
        """Generate fingerprints for a provider record"""
        from provider_fingerprinting import ProviderFingerprinter
        
        fingerprinter = ProviderFingerprinter()
        fingerprints = fingerprinter.generate_all_fingerprints(provider_record)
        
        result = set()
        if fingerprints.google_place_id:
            result.add(fingerprints.google_place_id)
        if fingerprints.primary:
            result.add(fingerprints.primary)
        if fingerprints.secondary:
            result.add(fingerprints.secondary)
        if fingerprints.fuzzy:
            result.add(fingerprints.fuzzy)
        
        return result
    
    def _extract_city_from_place_data(self, place_data: Dict) -> str:
        """Extract city from Google Places address components"""
        address_components = place_data.get('address_components', [])
        
        # Look for locality first
        for component in address_components:
            if 'locality' in component.get('types', []):
                return component.get('long_name', '')
        
        # Tokyo special case
        administrative_area = next(
            (comp['long_name'] for comp in address_components 
             if 'administrative_area_level_1' in comp['types']), ''
        )
        
        if administrative_area in ['Tokyo', '東京都', 'Tokyo Metropolis']:
            return 'Tokyo'
        
        return administrative_area
    
    def _validate_provider_photos(self, provider_record: Dict) -> bool:
        """Validate provider has photos (system requirement)"""
        photo_urls = provider_record.get('photo_urls', '')
        
        if not photo_urls or photo_urls == '[]':
            return False
        
        try:
            if isinstance(photo_urls, str):
                photo_list = json.loads(photo_urls)
            else:
                photo_list = photo_urls
            
            return len(photo_list) > 0
        except:
            return False
    
    def generate_ai_content_bulk(self, limit: int = None) -> Dict:
        """Generate AI content for recently added providers"""
        print("🤖 Generating AI content for new providers...")
        
        try:
            # Get recently added providers without AI content
            query = self.session.query(Provider).filter(
                Provider.ai_description.is_(None),
                Provider.status == 'pending'
            ).order_by(Provider.created_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            providers = query.all()
            
            if not providers:
                return {
                    'success': True,
                    'message': 'No providers need AI content generation'
                }
            
            print(f"📋 Found {len(providers)} providers needing AI content")
            
            # Use mega batch processor
            processor = ClaudeMegaBatchProcessor()
            results = processor.process_providers(providers, dry_run=False)
            
            return {
                'success': True,
                'providers_processed': results['providers_processed'],
                'message': f'AI content generated for {results["providers_processed"]} providers'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error generating AI content: {str(e)}'
            }
    
    def sync_to_wordpress_bulk(self, limit: int = None) -> Dict:
        """Sync recently added providers to WordPress"""
        print("🌐 Syncing new providers to WordPress...")
        
        try:
            sync_manager = WordPressSyncManager()
            
            # Get providers ready for WordPress sync
            query = self.session.query(Provider).filter(
                Provider.ai_description.isnot(None),
                Provider.wordpress_post_id.is_(None),
                Provider.status.in_(['description_generated', 'pending'])
            ).order_by(Provider.created_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            providers = query.all()
            
            if not providers:
                return {
                    'success': True,
                    'message': 'No providers need WordPress sync'
                }
            
            print(f"📋 Found {len(providers)} providers ready for WordPress")
            
            synced_count = 0
            for provider in providers:
                try:
                    result = sync_manager.sync_single_provider(provider.provider_name)
                    if result.get('status') == 'success':
                        synced_count += 1
                except Exception as e:
                    print(f"❌ Error syncing {provider.provider_name}: {str(e)}")
            
            return {
                'success': True,
                'providers_synced': synced_count,
                'message': f'Synced {synced_count} providers to WordPress'
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
    parser = argparse.ArgumentParser(description='Add healthcare providers by geographic targeting')
    
    # Geographic targeting options
    geo_group = parser.add_mutually_exclusive_group(required=True)
    geo_group.add_argument('--city', help='Target specific city (e.g., "Tokyo", "Osaka")')
    geo_group.add_argument('--cities', help='Target multiple cities (comma-separated)')
    
    # Optional geographic refinement
    parser.add_argument('--wards', help='Specific wards/districts (comma-separated, works with --city)')
    
    # Specialty filtering
    parser.add_argument('--specialty', help='Medical specialty to target (e.g., "ENT", "cardiology", "dermatology")')
    
    # Provider limits
    parser.add_argument('--limit', type=int, required=True,
                       help='Number of providers to add')
    
    # Processing options
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be found without adding')
    parser.add_argument('--generate-content', action='store_true',
                       help='Generate AI content after adding')
    parser.add_argument('--sync-wordpress', action='store_true',
                       help='Sync to WordPress after adding')
    
    args = parser.parse_args()
    
    print("🗺️ GEOGRAPHIC PROVIDER ADDITION")
    print("=" * 50)
    
    adder = GeographicProviderAdder()
    
    try:
        # Execute geographic addition
        if args.city:
            wards = args.wards.split(',') if args.wards else None
            result = adder.add_by_city(args.city, args.limit, wards, args.specialty, args.dry_run)
        else:
            cities = args.cities.split(',')
            result = adder.add_by_cities(cities, args.limit, args.specialty, args.dry_run)
        
        # Display results
        if result['success']:
            if result.get('dry_run'):
                print(f"\n✅ DRY RUN COMPLETE")
                print(f"📊 Would find {result.get('providers_found', 0)} providers")
                if 'provider_names' in result:
                    print(f"🏥 Sample providers:")
                    for name in result['provider_names'][:10]:
                        print(f"   - {name}")
            else:
                providers_added = result.get('providers_added', 0)
                print(f"\n✅ SUCCESS: Added {providers_added} providers")
                
                # Generate AI content if requested
                if args.generate_content and providers_added > 0:
                    print("\n" + "="*50)
                    content_result = adder.generate_ai_content_bulk(providers_added)
                    if content_result['success']:
                        print(f"✅ {content_result['message']}")
                    else:
                        print(f"❌ AI Content Error: {content_result['error']}")
                
                # Sync to WordPress if requested
                if args.sync_wordpress and providers_added > 0:
                    print("\n" + "="*50)
                    sync_result = adder.sync_to_wordpress_bulk(providers_added)
                    if sync_result['success']:
                        print(f"✅ {sync_result['message']}")
                    else:
                        print(f"❌ WordPress Error: {sync_result['error']}")
        else:
            print(f"❌ ERROR: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)
    finally:
        adder.close()

if __name__ == "__main__":
    main() 