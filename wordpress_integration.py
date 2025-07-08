#!/usr/bin/env python3
"""
WordPress Integration Module
Handles synchronization of healthcare provider data with a WordPress site via REST API.
"""

import os
import requests
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from postgres_integration import PostgresIntegration, Provider

class WordPressIntegration:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
        load_dotenv(config_path)
        self.wordpress_url = os.getenv('WORDPRESS_URL', 'https://care-compass.jp')
        self.username = os.getenv('WORDPRESS_USERNAME')
        self.application_password = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        if not all([self.wordpress_url, self.username, self.application_password]):
            raise ValueError("Missing WordPress credentials in .env")
        
        # Initialize database connection
        self.db = PostgresIntegration()
    
    def run_sync(self):
        """Main method to synchronize providers with WordPress"""
        print("🌐 Starting WordPress synchronization...")
        
        # Get providers ready for publishing
        session = self.db.Session()
        try:
            # Get providers ready for publishing (exclude those already published)
            providers = session.query(Provider).filter(
                Provider.status == 'description_generated',
                Provider.wordpress_post_id.is_(None)  # Only providers not yet published
            ).all()
            print(f"🔍 Found {len(providers)} providers ready for WordPress publishing")
            
            # Group providers by Google Place ID to prevent duplicates
            providers_by_place_id = {}
            for provider in providers:
                place_id = provider.google_place_id
                if place_id and place_id not in providers_by_place_id:
                    providers_by_place_id[place_id] = provider
                elif not place_id:
                    # Handle providers without Google Place ID (keep them)
                    providers_by_place_id[f"no_place_id_{provider.id}"] = provider
            
            unique_providers = list(providers_by_place_id.values())
            print(f"🔍 Deduplicated to {len(unique_providers)} unique providers (by Google Place ID)")
            
            if not unique_providers:
                print("ℹ️ No providers ready for publishing")
                return {"published": 0, "errors": 0, "skipped": 0}
            
            results = {"published": 0, "errors": 0, "skipped": 0}
            
            for provider in unique_providers:
                try:
                    # Double-check if already published to WordPress
                    if provider.wordpress_post_id:
                        print(f"⏭️ Already published: {provider.provider_name} (WordPress ID: {provider.wordpress_post_id})")
                        provider.status = 'published'
                        session.commit()
                        results["skipped"] += 1
                        continue
                    
                    # Check for duplicates by name/city in WordPress API as backup
                    duplicate_id = self.check_duplicate_post(provider.provider_name, provider.city)
                    if duplicate_id:
                        print(f"⏭️ Already exists in WordPress: {provider.provider_name} (ID: {duplicate_id})")
                        # Update database with existing WordPress post ID
                        provider.wordpress_post_id = duplicate_id
                        provider.status = 'published'
                        
                        # Also update all duplicate records with the same Google Place ID
                        if provider.google_place_id:
                            duplicate_providers = session.query(Provider).filter(
                                Provider.google_place_id == provider.google_place_id,
                                Provider.id != provider.id  # Exclude current provider
                            ).all()
                            
                            for duplicate in duplicate_providers:
                                duplicate.wordpress_post_id = duplicate_id
                                duplicate.status = 'published'
                                print(f"📄 Also marked duplicate as existing: {duplicate.provider_name} (ID: {duplicate.id})")
                        
                        session.commit()
                        results["skipped"] += 1
                        continue
                    
                    wordpress_post_id = self.create_wordpress_post(provider)
                    if wordpress_post_id:
                        # Update database with WordPress post ID and status
                        provider.wordpress_post_id = wordpress_post_id
                        provider.status = 'published'
                        
                        # Also update all duplicate records with the same Google Place ID
                        if provider.google_place_id:
                            duplicate_providers = session.query(Provider).filter(
                                Provider.google_place_id == provider.google_place_id,
                                Provider.id != provider.id  # Exclude current provider
                            ).all()
                            
                            for duplicate in duplicate_providers:
                                duplicate.wordpress_post_id = wordpress_post_id
                                duplicate.status = 'published'
                                print(f"📄 Also marked duplicate as published: {duplicate.provider_name} (ID: {duplicate.id})")
                        
                        session.commit()
                        results["published"] += 1
                        print(f"✅ Published: {provider.provider_name} (WordPress ID: {wordpress_post_id})")
                    else:
                        results["errors"] += 1
                        print(f"❌ Failed to publish: {provider.provider_name}")
                except Exception as e:
                    print(f"❌ Error publishing {provider.provider_name}: {str(e)}")
                    results["errors"] += 1
                    session.rollback()
            
            return results
            
        finally:
            session.close()
    
    def create_wordpress_post(self, provider):
        """Create a WordPress post for a healthcare provider"""
        try:
            # Process ALL specialties from provider (not just the first one)
            provider_specialties = []
            if provider.specialties:
                if isinstance(provider.specialties, list):
                    provider_specialties = provider.specialties
                elif isinstance(provider.specialties, str):
                    provider_specialties = [provider.specialties]
            
            # Default to General Medicine if no specialties found
            if not provider_specialties:
                provider_specialties = ["General Medicine"]
            
            print(f"🏥 Processing {len(provider_specialties)} specialties: {provider_specialties}")
            
            # Find or create location
            location_id = self.find_or_create_location(provider.city)
            if not location_id:
                print(f"❌ Failed to create/find location for {provider.city}")
                return None
            
            # Find or create ALL specialty terms
            specialty_ids = []
            primary_specialty = provider_specialties[0]  # Keep track of primary for content
            
            for specialty in provider_specialties:
                specialty_id = self.find_or_create_specialty(specialty)
                if specialty_id:
                    specialty_ids.append(specialty_id)
                    print(f"✅ Added specialty: {specialty} (ID: {specialty_id})")
                else:
                    print(f"⚠️ Failed to create/find specialty: {specialty}")
            
            if not specialty_ids:
                print(f"❌ Failed to create/find any specialties for {provider.provider_name}")
                return None
            
            print(f"🎯 Final specialty assignment: {len(specialty_ids)} specialties")
            
            # Prepare post data with comprehensive ACF fields
            post_data = {
                "title": provider.provider_name,
                "content": self.generate_provider_content(provider),
                "status": "publish",
                "type": "healthcare_provider",
                "location": [location_id],
                "specialties": specialty_ids,
                "acf": {
                    # Provider Details Field Group
                    "provider_phone": getattr(provider, 'phone', ''),
                    "wheelchair_accessible": self.format_wheelchair_accessibility(getattr(provider, 'wheelchair_accessible', False)),
                    "parking_available": self.format_parking_availability(getattr(provider, 'parking_available', False)),
                    "business_status": self.normalize_business_status(getattr(provider, 'business_status', 'Unknown')),
                    "prefecture": getattr(provider, 'prefecture', ''),
                    
                    # Business Hours Field Group
                    "business_hours": self.format_business_hours(getattr(provider, 'business_hours', {})),
                    "hours_monday": self.get_day_hours(getattr(provider, 'business_hours', {}), 'Monday'),
                    "hours_tuesday": self.get_day_hours(getattr(provider, 'business_hours', {}), 'Tuesday'),
                    "hours_wednesday": self.get_day_hours(getattr(provider, 'business_hours', {}), 'Wednesday'),
                    "hours_thursday": self.get_day_hours(getattr(provider, 'business_hours', {}), 'Thursday'),
                    "hours_friday": self.get_day_hours(getattr(provider, 'business_hours', {}), 'Friday'),
                    "hours_saturday": self.get_day_hours(getattr(provider, 'business_hours', {}), 'Saturday'),
                    "hours_sunday": self.get_day_hours(getattr(provider, 'business_hours', {}), 'Sunday'),
                    "open_now": self.get_open_now_status(getattr(provider, 'business_hours', {})),
                    
                    # Location & Navigation Field Group
                    "latitude": float(getattr(provider, 'latitude', 0)) if getattr(provider, 'latitude', None) else None,
                    "longitude": float(getattr(provider, 'longitude', 0)) if getattr(provider, 'longitude', None) else None,
                    "nearest_station": getattr(provider, 'nearest_station', ''),
                    "google_maps_embed": self.generate_google_maps_embed(getattr(provider, 'latitude', 0), getattr(provider, 'longitude', 0), provider.provider_name),
                    
                    # Language Support Field Group
                    "english_proficiency": self.determine_english_proficiency(provider),
                    "proficiency_score": self.calculate_proficiency_score(provider),
                    "english_indicators": self.extract_english_indicators(provider),
                    
                    # Photo Gallery Field Group
                    "photo_urls": self.convert_photo_urls_for_greenshift(getattr(provider, 'photo_urls', '')),
                    
                    # Accessibility & Services Field Group
                    "accessibility_status": self.format_accessibility_status(getattr(provider, 'wheelchair_accessible', False)),
                    "parking_status": self.format_parking_status(getattr(provider, 'parking_available', False)),
                    
                    # Patient Insights Field Group
                    "review_keywords": self.extract_patient_feedback_themes(getattr(provider, 'review_content', '')),
                    "patient_highlights": self.generate_patient_highlights(getattr(provider, 'review_content', '')),
                    
                    # Additional essential fields
                    "provider_website": self.clean_website_url(getattr(provider, 'website', '')),
                    "provider_address": self.clean_address(getattr(provider, 'address', '')),
                    "provider_rating": str(getattr(provider, 'rating', 0)),
                    "provider_reviews": str(getattr(provider, 'total_reviews', 0)),
                    "postal_code": getattr(provider, 'postal_code', ''),
                    "ai_description": getattr(provider, 'ai_description', ''),
                    "provider_city": provider.city,
                },
                "meta": {
                    # Non-ACF meta fields only
                    "status": getattr(provider, 'status', 'Unknown'),
                    "photo_count": str(getattr(provider, 'photo_count', 0)),
                    "photo_references": getattr(provider, 'photo_references', ''),
                    "review_content": getattr(provider, 'review_content', '[]'),
                    "service_categories": json.dumps(getattr(provider, 'service_categories', [])) if hasattr(provider, 'service_categories') else '[]',
                    "google_place_id": getattr(provider, 'google_place_id', ''),
                    "specialties_list": json.dumps(getattr(provider, 'specialties', []) if hasattr(provider, 'specialties') else provider_specialties),
                    "amenities": json.dumps(getattr(provider, 'amenities', [])) if hasattr(provider, 'amenities') else '[]',
                    "business_hours_raw": json.dumps(getattr(provider, 'business_hours', {})) if hasattr(provider, 'business_hours') else '{}',
                    "last_verified": getattr(provider, 'last_verified', ''),
                    "data_source": 'Google Places API',
                    "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "provider_city": provider.city,
                    "provider_address": self.clean_address(provider.address or ""),
                    "provider_phone": provider.phone or "",
                    "provider_website": self.clean_website_url(provider.website or ""),
                    "provider_rating": provider.rating or 0,
                    "total_reviews": provider.total_reviews or 0,
                    "english_proficiency": provider.english_proficiency or "Unknown"
                }
            }
            
            # Handle featured image
            photo_urls = getattr(provider, 'photo_urls', '')
            if photo_urls:
                try:
                    # Parse JSON string to get list of URLs
                    if isinstance(photo_urls, str) and photo_urls.strip():
                        photo_urls_list = json.loads(photo_urls)
                    else:
                        photo_urls_list = photo_urls
                    
                    if photo_urls_list and isinstance(photo_urls_list, list) and len(photo_urls_list) > 0:
                        first_photo_url = photo_urls_list[0]
                        print(f"🖼️  Setting featured image from Photo URLs...")
                        media_id = self.upload_featured_image(first_photo_url, provider.provider_name)
                        if media_id:
                            post_data['featured_media'] = media_id
                            print(f"✅ Featured image set (Media ID: {media_id})")
                        else:
                            print(f"⚠️  Failed to set featured image")
                except json.JSONDecodeError:
                    print(f"⚠️  Could not parse Photo URLs JSON")
                except Exception as e:
                    print(f"⚠️  Error processing Photo URLs: {str(e)}")
            else:
                print(f"⚠️  No photo URLs available for featured image")
            
            # Create the post
            response = requests.post(
                f"{self.wordpress_url}/wp-json/wp/v2/healthcare_provider",
                auth=(self.username, self.application_password),
                json=post_data
            )
            
            if response.status_code == 201:
                post = response.json()
                post_id = post["id"]
                print(f"✅ Created WordPress post: {provider.provider_name} (ID: {post_id})")
                
                # Check if ACF fields were saved
                if 'acf' in post and post['acf']:
                    acf_field_count = len([v for v in post['acf'].values() if v])
                    print(f"✅ ACF fields populated: {acf_field_count} fields")
                else:
                    print(f"⚠️  Warning: ACF fields may not be populated")
                
                return post_id
            else:
                print(f"❌ Failed to create post: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating WordPress post: {str(e)}")
            return None
    
    def generate_provider_content(self, provider):
        """Generate content for a WordPress post based on provider data."""
        # Extract and format all specialties
        specialty_display = "General Practitioner"
        if provider.specialties:
            if isinstance(provider.specialties, list) and provider.specialties:
                # Clean and format specialty names for display
                cleaned_specialties = []
                for specialty in provider.specialties:
                    # Convert common technical terms to readable names
                    specialty_mapping = {
                        "general_practitioner": "General Medicine",
                        "oncologist": "Oncology", 
                        "ent": "ENT (Ear, Nose & Throat)",
                        "Point_of_interest": "General Healthcare",
                        "Health": "General Healthcare",
                        "Establishment": "Medical Facility"
                    }
                    clean_specialty = specialty_mapping.get(specialty.lower(), specialty.title())
                    if clean_specialty not in cleaned_specialties:
                        cleaned_specialties.append(clean_specialty)
                
                specialty_display = ", ".join(cleaned_specialties) if cleaned_specialties else "General Practitioner"
            elif isinstance(provider.specialties, str):
                specialty_display = provider.specialties
        
        content = f"""
        <h2>{provider.provider_name}</h2>
        <p><strong>Location:</strong> {provider.city}, {getattr(provider, 'prefecture', 'Unknown Prefecture')}</p>
        <p><strong>Address:</strong> {self.clean_address(provider.address) or 'Not available'}</p>
        <p><strong>Phone:</strong> {provider.phone or 'Not available'}</p>
        <p><strong>Website:</strong> {self.clean_website_url(provider.website) or 'Not available'}</p>
        <p><strong>Specialties:</strong> {specialty_display}</p>
        <p><strong>English Proficiency:</strong> {provider.english_proficiency or 'Unknown'}</p>
        <p><strong>Business Hours:</strong></p>
        <pre>{self.format_business_hours(getattr(provider, 'business_hours', {}))}</pre>
        <p><strong>Description:</strong> {getattr(provider, 'ai_description', 'Professional healthcare provider offering quality medical services.')}</p>
        <p><strong>Rating:</strong> {provider.rating or 0}/5 ({provider.total_reviews or 0} reviews)</p>
        """
        return content

    def check_duplicate_post(self, provider_name, provider_city):
        """Check for existing WordPress post by name and city"""
        url = f"{self.wordpress_url}/wp-json/wp/v2/healthcare_provider"
        response = requests.get(url, auth=(self.username, self.application_password), params={'per_page': 100})
        if response.status_code != 200:
            print(f"⚠️ Error checking duplicates: {response.status_code} - {response.text}")
            return None
        posts = response.json()
        for post in posts:
            if (post.get('title', {}).get('rendered') == provider_name and 
                post.get('meta', {}).get('provider_city') == provider_city):
                print(f"⚠️ Duplicate detected: {provider_name} in {provider_city} (ID: {post['id']})")
                return post['id']
        return None
    
    def find_or_create_specialty(self, specialty_name):
        """Find or create a specialty term with flexible mapping"""
        print(f"🔍 Looking for specialty: {specialty_name}")
        
        # Mapping from common terms to WordPress specialty terms
        specialty_mapping = {
            "general_practitioner": "General Medicine",
            "general practitioner": "General Medicine", 
            "general medicine": "General Medicine",
            "family medicine": "General Medicine",
            "internal medicine": "General Medicine",
            "pediatrician": "Pediatrics",
            "pediatrics": "Pediatrics",
            "cardiologist": "Cardiology",
            "cardiology": "Cardiology",
            "dermatologist": "Dermatology", 
            "dermatology": "Dermatology",
            "orthopedic_surgeon": "Orthopedics",
            "orthopedic surgeon": "Orthopedics",
            "orthopedics": "Orthopedics",
            "neurologist": "Neurology",
            "neurology": "Neurology",
            "ophthalmologist": "Ophthalmology",
            "ophthalmology": "Ophthalmology",
            "dentist": "Dentistry",
            "dental": "Dentistry",
            "dentistry": "Dentistry",
            "gynecologist": "Gynecology",
            "gynecology": "Gynecology",
            "urologist": "Urology",
            "urology": "Urology",
            "psychiatrist": "Psychiatry",
            "psychiatry": "Psychiatry",
            "oncologist": "Oncology",
            "oncology": "Oncology",
            "ent": "ENT (Ear, Nose & Throat)",
            # Google Places API types mapping
            "point_of_interest": "General Healthcare",
            "health": "General Medicine",
            "establishment": "Medical Facility",
            "doctor": "General Medicine",
            "hospital": "General Medicine",
            "medical_center": "General Medicine"
        }
        
        # Normalize the specialty name
        normalized_specialty = specialty_mapping.get(specialty_name.lower(), specialty_name)
        
        # Search for the specialty
        specialty_terms = self.get_all_wordpress_terms('specialties')
        
        for term in specialty_terms:
            if (term["name"].lower() == normalized_specialty.lower() or 
                term["name"].lower() == specialty_name.lower()):
                print(f"✅ Found specialty: {normalized_specialty} (ID: {term['id']})")
                return term['id']
        
        # Try creating the specialty
        print(f"🆕 Creating specialty: {normalized_specialty}")
        create_data = {"name": normalized_specialty, "slug": normalized_specialty.lower().replace(' ', '-')}
        
        try:
            response = requests.post(
                f"{self.wordpress_url}/wp-json/wp/v2/specialties",
                auth=(self.username, self.application_password),
                json=create_data
            )
            
            if response.status_code == 201:
                new_id = response.json()["id"]
                print(f"✅ Created specialty: {normalized_specialty} (ID: {new_id})")
                return new_id
            else:
                print(f"❌ Failed to create specialty: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error creating specialty: {str(e)}")
        
        print(f"❌ Critical: No valid specialty ID for {specialty_name}")
        return None

    def get_all_wordpress_terms(self, taxonomy):
        """Get ALL terms from WordPress taxonomy with better pagination and search"""
        all_terms = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.wordpress_url}/wp-json/wp/v2/{taxonomy}"
            params = {
                'per_page': per_page, 
                'page': page,
                'hide_empty': False,  # Include terms with no posts
                'orderby': 'name',
                'order': 'asc'
            }
            
            try:
                response = requests.get(url, auth=(self.username, self.application_password), params=params)
                
                if response.status_code == 404:
                    print(f"⚠️ {taxonomy} endpoint not found, trying alternative...")
                    # Try alternative endpoint
                    url = f"{self.wordpress_url}/wp-json/wp/v2/{taxonomy.rstrip('s')}"  # Remove 's' 
                    response = requests.get(url, auth=(self.username, self.application_password), params=params)
                
                if response.status_code != 200:
                    print(f"⚠️ Error fetching {taxonomy} page {page}: {response.status_code} - {response.text}")
                    break
                    
                terms = response.json()
                if not terms:  # No more results
                    break
                    
                all_terms.extend(terms)
                print(f"📄 Fetched page {page}: {len(terms)} {taxonomy} terms")
                
                # Check if there are more pages
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                if page >= total_pages:
                    break
                    
                page += 1
                
            except Exception as e:
                print(f"❌ Error fetching {taxonomy}: {str(e)}")
                break
                
        print(f"📊 Total {taxonomy} fetched: {len(all_terms)}")
        
        # Debug: Print first few location names
        if taxonomy == 'location' and all_terms:
            print(f"🔍 Sample locations: {[term['name'] for term in all_terms[:5]]}")
            
        return all_terms

    def search_wordpress_terms(self, taxonomy, search_term):
        """Search for specific terms in WordPress taxonomy"""
        url = f"{self.wordpress_url}/wp-json/wp/v2/{taxonomy}"
        params = {
            'search': search_term,
            'per_page': 100,
            'hide_empty': False
        }
        
        try:
            response = requests.get(url, auth=(self.username, self.application_password), params=params)
            if response.status_code == 200:
                results = response.json()
                print(f"🔍 Search for '{search_term}' in {taxonomy}: found {len(results)} results")
                return results
            else:
                print(f"⚠️ Search failed for '{search_term}': {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            return []

    def find_or_create_location(self, city_name):
        """Find or create a location term with enhanced search"""
        print(f"🔍 Looking for location: {city_name}")
        
        # Method 1: Search specifically for the city
        search_results = self.search_wordpress_terms('location', city_name)
        for term in search_results:
            if term["name"].lower() == city_name.lower():
                print(f"✅ Found via search: {city_name} (ID: {term['id']})")
                return term['id']
        
        # Method 2: Get all locations and search manually
        location_terms = self.get_all_wordpress_terms('location')
        
        city_lower = city_name.lower().strip()
        
        # Try exact match
        for term in location_terms:
            if term["name"].lower() == city_lower:
                print(f"✅ Found exact match: {city_name} (ID: {term['id']})")
                return term['id']
        
        # Try partial matches
        for term in location_terms:
            term_name_lower = term["name"].lower()
            if (city_lower in term_name_lower or 
                term_name_lower in city_lower or
                city_lower.replace(' ', '') in term_name_lower.replace(' ', '') or
                term_name_lower.replace(' ', '') in city_lower.replace(' ', '')):
                print(f"✅ Found partial match: {term['name']} for {city_name} (ID: {term['id']})")
                return term['id']
        
        # Method 3: Try alternative endpoint formats
        alternative_endpoints = ['location', 'locations', 'cities', 'city']
        for endpoint in alternative_endpoints:
            if endpoint != 'location':  # Already tried above
                print(f"🔄 Trying alternative endpoint: {endpoint}")
                alt_terms = self.get_all_wordpress_terms(endpoint)
                for term in alt_terms:
                    if term["name"].lower() == city_lower:
                        print(f"✅ Found via {endpoint}: {city_name} (ID: {term['id']})")
                        return term['id']
        
        # Method 4: Create new location
        print(f"🆕 Creating new location: {city_name}")
        
        create_data = {"name": city_name, "slug": city_name.lower().replace(' ', '-')}
        
        try:
            response = requests.post(
                f"{self.wordpress_url}/wp-json/wp/v2/location",
                auth=(self.username, self.application_password),
                json=create_data
            )
            
            if response.status_code == 201:
                new_id = response.json()["id"]
                print(f"✅ Created location: {city_name} (ID: {new_id})")
                return new_id
            elif response.status_code == 400:
                error_data = response.json()
                print(f"⚠️ Creation failed: {response.status_code} - {error_data}")
                
                if "term_exists" in response.text or "already exists" in response.text:
                    print(f"🔄 Term exists but not found, forcing refresh...")
                    # Clear any caches and try a direct lookup
                    time.sleep(2)
                    
                    # Try direct ID lookup if we can parse it from error
                    try:
                        # Some WordPress setups return the existing term ID in error
                        if "term_id" in error_data:
                            existing_id = error_data.get("term_id")
                            print(f"✅ Retrieved existing ID from error: {city_name} (ID: {existing_id})")
                            return existing_id
                    except:
                        pass
                    
                    # Last resort: Try fetching all terms again with a longer wait
                    print(f"🔄 Final attempt: re-fetching all locations...")
                    final_terms = self.get_all_wordpress_terms('location')
                    for term in final_terms:
                        if term["name"].lower() == city_lower:
                            print(f"✅ Found on final attempt: {city_name} (ID: {term['id']})")
                            return term['id']
            else:
                print(f"❌ Unexpected creation error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Creation request failed: {str(e)}")
        
        print(f"❌ Complete failure to find/create location: {city_name}")
        return None
    
    def normalize_business_status(self, status):
        """Convert business status to ACF expected values"""
        status_map = {
            'OPERATIONAL': 'Operational',
            'CLOSED_TEMPORARILY': 'Temporarily Closed', 
            'CLOSED_PERMANENTLY': 'Permanently Closed',
            'Operational': 'Operational',
            'Temporarily Closed': 'Temporarily Closed',
            'Permanently Closed': 'Permanently Closed'
        }
        return status_map.get(status, 'Unknown')
    
    def format_english_indicators(self, indicators):
        """Convert English indicators to string format expected by ACF"""
        if isinstance(indicators, list):
            return '\n'.join(indicators) if indicators else ''
        elif isinstance(indicators, str):
            return indicators
        else:
            return ''
    
    def convert_photo_urls_for_greenshift(self, photo_urls_field):
        """Convert photo URLs from JSON format to newline-separated format for Greenshift"""
        if not photo_urls_field:
            return ''
        
        try:
            # Parse JSON string to get list of URLs
            if isinstance(photo_urls_field, str):
                photo_urls_list = json.loads(photo_urls_field)
            else:
                photo_urls_list = photo_urls_field
            
            if photo_urls_list and isinstance(photo_urls_list, list):
                # Convert to newline-separated format
                return '\n'.join(photo_urls_list)
            else:
                return str(photo_urls_field) if photo_urls_field else ''
                
        except json.JSONDecodeError:
            # If it's not JSON, return as-is
            return str(photo_urls_field) if photo_urls_field else ''
        except Exception as e:
            print(f"⚠️  Error converting photo URLs: {str(e)}")
            return str(photo_urls_field) if photo_urls_field else ''
    
    def format_accessibility_status(self, wheelchair_accessible):
        """Format accessibility status with descriptive sentences"""
        if wheelchair_accessible is True:
            return "Location is wheelchair accessible"
        elif wheelchair_accessible is False:
            return "Location is not wheelchair accessible"
        else:
            return "Wheelchair accessibility unknown"

    def format_parking_status(self, parking_available):
        """Format parking status with descriptive sentences"""
        if parking_available is True:
            return "Parking available"
        elif parking_available is False:
            return "No Parking available"
        else:
            return "Parking availability unknown"
    
    def generate_google_maps_embed(self, latitude, longitude, provider_name):
        """Generate Google Maps embed code from coordinates"""
        if not latitude or not longitude or latitude == 0 or longitude == 0:
            return ""
        
        # Use Google Maps embed without API key (using query parameter)
        embed_code = f'''<iframe 
            width="100%" 
            height="300" 
            frameborder="0" 
            style="border:0" 
            src="https://maps.google.com/maps?q={latitude},{longitude}&hl=en&z=15&output=embed" 
            allowfullscreen>
        </iframe>'''
        
        return embed_code

    def extract_patient_feedback_themes(self, review_content):
        """Extract key patient feedback themes from review content"""
        if not review_content:
            return "No patient feedback available"
        
        try:
            # Parse review content JSON
            if isinstance(review_content, str):
                reviews = json.loads(review_content)
            else:
                reviews = review_content
            
            if not reviews or not isinstance(reviews, list):
                return "No patient feedback available"
            
            # Extract common themes from reviews
            positive_themes = []
            service_themes = []
            
            for review in reviews:
                text = review.get('text', '').lower()
                if not text:
                    continue
                
                # Positive themes
                if any(word in text for word in ['friendly', 'kind', 'helpful', 'professional', 'gentle']):
                    positive_themes.append('Staff praised for friendliness and professionalism')
                if any(word in text for word in ['clean', 'modern', 'comfortable', 'nice facilities']):
                    positive_themes.append('Clean and modern facilities')
                if any(word in text for word in ['quick', 'efficient', 'no wait', 'on time']):
                    positive_themes.append('Efficient service and minimal waiting')
                if any(word in text for word in ['english', 'bilingual', 'communication']):
                    positive_themes.append('Good English communication')
                
                # Service themes
                if any(word in text for word in ['treatment', 'care', 'thorough', 'detailed']):
                    service_themes.append('Thorough medical care and treatment')
                if any(word in text for word in ['affordable', 'reasonable price', 'good value']):
                    service_themes.append('Reasonable pricing')
                if any(word in text for word in ['convenient', 'location', 'easy access']):
                    service_themes.append('Convenient location and access')
            
            # Combine unique themes
            all_themes = list(set(positive_themes + service_themes))
            
            if all_themes:
                return "; ".join(all_themes[:5])  # Limit to top 5 themes
            else:
                return "General healthcare services with positive patient feedback"
                
        except Exception as e:
            print(f"Error extracting feedback themes: {str(e)}")
            return "Patient feedback analysis unavailable"

    def generate_patient_highlights(self, review_content):
        """Generate patient experience highlights as ACF repeater field array"""
        if not review_content:
            return []
        
        try:
            # Parse review content JSON
            if isinstance(review_content, str):
                reviews = json.loads(review_content)
            else:
                reviews = review_content
            
            if not reviews or not isinstance(reviews, list):
                return []
            
            highlights = []
            
            # Analyze reviews for common positive highlights
            has_english_support = False
            has_clean_facilities = False
            has_friendly_staff = False
            has_professional_care = False
            has_convenient_location = False
            
            for review in reviews:
                text = review.get('text', '').lower()
                rating = review.get('rating', 0)
                
                # Only consider reviews with 4+ stars for highlights
                if rating >= 4:
                    if any(word in text for word in ['english', 'bilingual', 'speaks english']):
                        has_english_support = True
                    if any(word in text for word in ['clean', 'modern', 'nice facilities']):
                        has_clean_facilities = True
                    if any(word in text for word in ['friendly', 'kind', 'helpful']):
                        has_friendly_staff = True
                    if any(word in text for word in ['professional', 'experienced', 'skilled']):
                        has_professional_care = True
                    if any(word in text for word in ['convenient', 'easy access', 'near station']):
                        has_convenient_location = True
            
            # Create highlights based on findings - ACF repeater format
            if has_english_support:
                highlights.append({
                    "highlight_text": "English-speaking staff available",
                    "highlight_icon": "🗣️"
                })
            
            if has_clean_facilities:
                highlights.append({
                    "highlight_text": "Clean and modern facilities", 
                    "highlight_icon": "✨"
                })
            
            if has_friendly_staff:
                highlights.append({
                    "highlight_text": "Friendly and helpful staff",
                    "highlight_icon": "😊"
                })
            
            if has_professional_care:
                highlights.append({
                    "highlight_text": "Professional medical care",
                    "highlight_icon": "👩‍⚕️"
                })
            
            if has_convenient_location:
                highlights.append({
                    "highlight_text": "Convenient location",
                    "highlight_icon": "📍"
                })
            
            # If no specific highlights found, add generic ones
            if not highlights:
                highlights.append({
                    "highlight_text": "Quality healthcare services",
                    "highlight_icon": "🏥"
                })
            
            return highlights[:4]  # Limit to 4 highlights
            
        except Exception as e:
            print(f"Error generating patient highlights: {str(e)}")
            return [{
                "highlight_text": "Professional healthcare provider",
                "highlight_icon": "🏥"
            }]

    def upload_featured_image(self, image_url, post_title):
        """Upload image from URL as WordPress featured image"""
        try:
            # Download the image
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                return None
            
            # Prepare the file data
            filename = f"{post_title.replace(' ', '_')}_featured.jpg"
            files = {
                'file': (filename, response.content, 'image/jpeg')
            }
            
            # Upload to WordPress
            upload_response = requests.post(
                f"{self.wordpress_url}/wp-json/wp/v2/media",
                auth=(self.username, self.application_password),
                files=files,
                data={'title': f"{post_title} Featured Image"}
            )
            
            if upload_response.status_code == 201:
                media_data = upload_response.json()
                return media_data['id']
            else:
                print(f"⚠️ Failed to upload featured image: {upload_response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️ Error uploading featured image: {str(e)}")
            return None
    
    def determine_english_proficiency(self, provider):
        """Determine English proficiency level from review content and provider data"""
        try:
            # Check if provider has explicit proficiency data
            explicit_proficiency = getattr(provider, 'english_proficiency', 'Unknown')
            if explicit_proficiency and explicit_proficiency != 'Unknown':
                return explicit_proficiency
            
            # Analyze review content for English indicators
            review_content = getattr(provider, 'review_content', '')
            if not review_content:
                return 'Unknown'
            
            # Parse reviews
            if isinstance(review_content, str):
                reviews = json.loads(review_content)
            else:
                reviews = review_content
            
            if not reviews or not isinstance(reviews, list):
                return 'Unknown'
            
            # Collect all review text
            all_text = " ".join([review.get('text', '') for review in reviews if review.get('text')]).lower()
            
            # Strong English indicators
            strong_indicators = [
                "excellent english", "great english", "perfect english", "fluent english",
                "english communication skills", "speaks english well", "english speaking"
            ]
            
            # Good English indicators
            good_indicators = [
                "english", "communicate in english", "english doctor", "english speaking staff"
            ]
            
            # Poor English indicators
            poor_indicators = [
                "no english", "poor english", "limited english", "not good at english",
                "don't speak english", "cannot speak english"
            ]
            
            # Check for strong indicators - map to WordPress values
            for indicator in strong_indicators:
                if indicator in all_text:
                    return "Fluent"
            
            # Check for poor indicators
            for indicator in poor_indicators:
                if indicator in all_text:
                    return "Basic"
            
            # Check for general English mentions
            for indicator in good_indicators:
                if indicator in all_text:
                    return "Conversational"
            
            return "Unknown"
            
        except Exception as e:
            print(f"Error determining English proficiency: {str(e)}")
            return "Unknown"
    
    def calculate_proficiency_score(self, provider):
        """Calculate numeric proficiency score from review analysis"""
        try:
            proficiency_level = self.determine_english_proficiency(provider)
            
            score_mapping = {
                "Fluent": 5,
                "Conversational": 4,
                "Basic": 3,
                "Unknown": 0
            }
            
            return score_mapping.get(proficiency_level, 0)
            
        except Exception as e:
            print(f"Error calculating proficiency score: {str(e)}")
            return 0
    
    def extract_english_indicators(self, provider):
        """Extract English language indicators from review content"""
        try:
            review_content = getattr(provider, 'review_content', '')
            if not review_content:
                return ""
            
            # Parse reviews
            if isinstance(review_content, str):
                reviews = json.loads(review_content)
            else:
                reviews = review_content
            
            if not reviews or not isinstance(reviews, list):
                return ""
            
            # Collect all review text
            all_text = " ".join([review.get('text', '') for review in reviews if review.get('text')])
            
            # Extract English-related sentences
            english_indicators = []
            sentences = all_text.split('. ')
            
            for sentence in sentences:
                if 'english' in sentence.lower():
                    # Clean up the sentence
                    clean_sentence = sentence.strip()
                    if clean_sentence and len(clean_sentence) > 10:
                        english_indicators.append(clean_sentence)
            
            # Return formatted indicators
            if english_indicators:
                return "• " + "\n• ".join(english_indicators[:3])  # Limit to 3 key indicators
            else:
                return ""
            
        except Exception as e:
            print(f"Error extracting English indicators: {str(e)}")
            return ""
    
    def clean_website_url(self, url):
        """Clean website URL by removing query parameters (utm_source, etc.)"""
        if not url:
            return ""
        
        try:
            # Remove everything after the first '?' character
            if '?' in url:
                url = url.split('?')[0]
            
            # Remove trailing slashes
            url = url.rstrip('/')
            
            return url
        except Exception as e:
            print(f"Error cleaning website URL: {str(e)}")
            return url
    
    def clean_address(self, address):
        """Clean address by removing 'Japan' from the end and extra whitespace"""
        if not address:
            return ""
        
        try:
            cleaned_address = address.strip()
            
            # Remove 'Japan' from the end of the address (case-insensitive)
            japan_suffixes = [', Japan', ',Japan', ' Japan']
            for suffix in japan_suffixes:
                if cleaned_address.lower().endswith(suffix.lower()):
                    cleaned_address = cleaned_address[:-len(suffix)]
                    break
            
            # If address ends with just 'Japan' (no comma or space before)
            if cleaned_address.lower().endswith('japan'):
                # Only remove if it's at the very end and preceded by a space or comma
                if len(cleaned_address) > 5 and cleaned_address[-6] in [' ', ',']:
                    cleaned_address = cleaned_address[:-5]
            
            # Clean up extra whitespace and trailing commas
            cleaned_address = cleaned_address.strip(' ,')
            cleaned_address = ' '.join(cleaned_address.split())
            
            return cleaned_address
        except Exception as e:
            print(f"Error cleaning address: {str(e)}")
            return address
    
    def format_wheelchair_accessibility(self, wheelchair_accessible):
        """Format wheelchair accessibility for ACF dropdown field"""
        if wheelchair_accessible is True:
            return "Wheelchair accessible"
        elif wheelchair_accessible is False:
            return "Not wheelchair accessible"
        else:
            return "Wheelchair accessibility unknown"
    
    def format_parking_availability(self, parking_available):
        """Format parking availability for ACF dropdown field"""
        if parking_available is True:
            return "Parking is available"
        elif parking_available is False:
            return "Parking is not available"
        else:
            return "Parking unknown"

    def format_business_hours(self, business_hours):
        """Format business hours for display in ACF field"""
        if not business_hours or not isinstance(business_hours, dict):
            return ""
        
        # If we have display_text from Google Places, use that
        if 'display_text' in business_hours:
            return "\n".join(business_hours['display_text'])
        
        # Otherwise, format from formatted_hours
        if 'formatted_hours' in business_hours:
            formatted_lines = []
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            for day in days_order:
                if day in business_hours['formatted_hours']:
                    hours = business_hours['formatted_hours'][day]
                    if hours.get('open') and hours.get('close'):
                        formatted_lines.append(f"{day}: {hours['open']} - {hours['close']}")
                    else:
                        formatted_lines.append(f"{day}: Closed")
                else:
                    formatted_lines.append(f"{day}: Hours not available")
            
            return "\n".join(formatted_lines)
        
        return "Hours not available"

    def get_day_hours(self, business_hours, day):
        """Get hours for a specific day"""
        if not business_hours or not isinstance(business_hours, dict):
            return "Hours not available"
        
        if 'formatted_hours' in business_hours and day in business_hours['formatted_hours']:
            hours = business_hours['formatted_hours'][day]
            if hours.get('open') and hours.get('close'):
                return f"{hours['open']} - {hours['close']}"
            else:
                return "Closed"
        
        return "Hours not available"

    def get_open_now_status(self, business_hours):
        """Get open now status from Google Places data"""
        if not business_hours or not isinstance(business_hours, dict):
            return "Status unknown"
        
        # Use the open_now status from Google Places if available
        if 'open_now' in business_hours:
            return "Open Now" if business_hours['open_now'] else "Closed"
        
        return "Status unknown"