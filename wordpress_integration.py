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
            
            # Find or create location(s) - enhanced for Tokyo wards
            location_ids = []
            
            # Always create/find the main city location
            location_id = self.find_or_create_location(provider.city)
            if not location_id:
                print(f"❌ Failed to create/find location for {provider.city}")
                return None
            location_ids.append(location_id)
            
            # Tokyo Ward Enhancement: For Tokyo's 23 wards, also add ward as location term
            tokyo_wards = [
                "Adachi", "Arakawa", "Bunkyo", "Chiyoda", "Chuo", "Edogawa",
                "Itabashi", "Katsushika", "Kita", "Koto", "Meguro", "Minato", 
                "Nakano", "Nerima", "Ota", "Setagaya", "Shibuya", "Shinagawa",
                "Shinjuku", "Suginami", "Sumida", "Taito", "Toshima"
            ]
            
            ward_name = getattr(provider, 'district', '')
            if (provider.city == 'Tokyo' and ward_name in tokyo_wards):
                print(f"🏢 Tokyo ward detected: Adding {ward_name} as additional location term")
                ward_location_id = self.find_or_create_tokyo_ward_location(ward_name)
                if ward_location_id:
                    location_ids.append(ward_location_id)
                    print(f"✅ Added ward location: {ward_name} (ID: {ward_location_id})")
                else:
                    print(f"⚠️ Failed to create/find ward location: {ward_name}")
            
            print(f"📍 Final location assignment: {len(location_ids)} location terms")
            
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
            
            # Prepare post data with comprehensive ACF fields - ACF Only Approach
            post_data = {
                "title": provider.provider_name,
                "content": self.generate_minimal_provider_content(provider),  # Minimal placeholder content
                "excerpt": getattr(provider, 'ai_excerpt', ''),  # Add excerpt for WordPress preview
                "status": "publish",
                "type": "healthcare_provider",
                "location": location_ids,
                "specialties": specialty_ids,
                "acf": {
                    # Provider Details Field Group
                    "provider_phone": getattr(provider, 'phone', ''),
                    "wheelchair_accessible": self.format_wheelchair_accessibility(getattr(provider, 'wheelchair_accessible', False)),
                    "parking_available": self.format_parking_availability(getattr(provider, 'parking_available', False)),
                    "business_status": self.normalize_business_status(getattr(provider, 'business_status', 'Unknown')),
                    "prefecture": getattr(provider, 'prefecture', ''),
                    "district": getattr(provider, 'district', ''),  # Ward/district within city
                    
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
                    "latitude": getattr(provider, 'latitude', 0),
                    "longitude": getattr(provider, 'longitude', 0),
                    "nearest_station": getattr(provider, 'nearest_station', ''),
                    "google_maps_embed": self.generate_google_maps_embed(getattr(provider, 'latitude', 0), getattr(provider, 'longitude', 0), provider.provider_name, self.clean_address(getattr(provider, 'address', ''))),
                    
                    # Language Support Field Group
                    "english_proficiency": getattr(provider, 'english_proficiency', 'Unknown'),
                    "proficiency_score": getattr(provider, 'proficiency_score', 0),
                    "english_indicators": self.extract_english_indicators(provider),
                    
                    # Photo Gallery Field Group
                    "photo_urls": self.convert_photo_urls_for_greenshift(getattr(provider, 'photo_urls', '')),
                    "external_featured_image": self.get_primary_photo_url(provider),
                    "featured_image_source": self.get_featured_image_source(provider),
                    "photo_count": self.get_photo_count(provider),
                    "image_selection_status": self.get_image_selection_status(provider),
                    
                    # Accessibility & Services Field Group
                    "accessibility_status": self.format_accessibility_status(getattr(provider, 'wheelchair_accessible', False)),
                    "parking_status": self.format_parking_status(getattr(provider, 'parking_available', False)),
                    
                    # Patient Insights Field Group
                    "review_keywords": self.extract_patient_feedback_themes(getattr(provider, 'review_content', '')),
                    "review_summary": getattr(provider, 'review_summary', ''),
            "english_experience_summary": getattr(provider, 'english_experience_summary', ''),
                    "patient_highlights": self.generate_patient_highlights(getattr(provider, 'review_content', '')),
                    
                    # Additional essential fields
                    "provider_website": self.clean_website_url(getattr(provider, 'website', '')),
                    "provider_address": self.clean_address(getattr(provider, 'address', '')),
                    "provider_rating": str(getattr(provider, 'rating', 0)),
                    "provider_reviews": str(getattr(provider, 'total_reviews', 0)),
                    "postal_code": getattr(provider, 'postal_code', ''),
                    "ai_description": getattr(provider, 'ai_description', ''),
                    "ai_excerpt": getattr(provider, 'ai_excerpt', ''),  # Add excerpt to ACF fields as well
                    "provider_city": provider.city,
                    
                    # SEO Content Field Group
                    "seo_title": getattr(provider, 'seo_title', ''),
                    "seo_meta_description": getattr(provider, 'seo_meta_description', ''),
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
                    "data_display_method": "acf_fields_only",  # Track ACF-only architecture
                    "provider_city": provider.city,
                    "provider_district": getattr(provider, 'district', ''),
                    "provider_address": self.clean_address(provider.address or ""),
                    "provider_phone": provider.phone or "",
                    "provider_website": self.clean_website_url(provider.website or ""),
                    "provider_rating": provider.rating or 0,
                    "total_reviews": provider.total_reviews or 0,
                    "english_proficiency": provider.english_proficiency or "Unknown",
                    
                    # External Featured Image - TOS Compliant
                    "external_featured_image": self.get_primary_photo_url(provider),
                    
                    # SEO meta fields for Yoast/RankMath compatibility
                    "_yoast_wpseo_title": getattr(provider, 'seo_title', ''),
                    "_yoast_wpseo_metadesc": getattr(provider, 'seo_meta_description', ''),
                    "_rank_math_title": getattr(provider, 'seo_title', ''),
                    "_rank_math_description": getattr(provider, 'seo_meta_description', ''),
                }
            }
            
            # NOTE: We do NOT upload photos to media library (Google API TOS compliance)
            # Photos are linked directly via ACF photo_urls field
            print(f"📸 Using direct Google Places photo URLs (TOS compliant)")
            
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
    
    def generate_minimal_provider_content(self, provider):
        """Generate minimal WordPress post content - ACF fields handle all data display"""
        return f"""
        <!-- Provider data is displayed via ACF fields -->
        <div class="provider-acf-content">
            <p><em>This provider's information is displayed using ACF fields. 
            If you're seeing this message, please check your theme's ACF field display configuration.</em></p>
        </div>
        """
    
    def generate_provider_content(self, provider):
        """DEPRECATED: Generate content for a WordPress post based on provider data.
        
        This method is deprecated in favor of ACF-only data display.
        Use generate_minimal_provider_content() instead.
        """
        print("⚠️  generate_provider_content is deprecated. Using ACF fields only for data display.")
        return self.generate_minimal_provider_content(provider)

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
        
        # Search for the specialty with multiple methods
        print(f"📄 Searching for specialty: {normalized_specialty}")
        
        # Method 1: Direct search API call
        search_results = self.search_wordpress_terms('specialties', normalized_specialty)
        for term in search_results:
            if (term["name"].lower() == normalized_specialty.lower() or 
                term["name"].lower() == specialty_name.lower()):
                print(f"✅ Found via search API: {normalized_specialty} (ID: {term['id']})")
                return term['id']
        
        # Method 2: Get all terms and search manually
        specialty_terms = self.get_all_wordpress_terms('specialties')
        print(f"📊 Total specialties fetched: {len(specialty_terms)}")
        
        # Try exact matches first
        for term in specialty_terms:
            if (term["name"].lower() == normalized_specialty.lower() or 
                term["name"].lower() == specialty_name.lower()):
                print(f"✅ Found exact match: {normalized_specialty} (ID: {term['id']})")
                return term['id']
        
        # Try partial matches and common variations
        for term in specialty_terms:
            term_name_lower = term["name"].lower().strip()
            normalized_lower = normalized_specialty.lower().strip()
            specialty_lower = specialty_name.lower().strip()
            
            # Check if terms are similar (accounting for punctuation, spacing differences)
            if (term_name_lower.replace('&', 'and').replace('(', '').replace(')', '').replace(',', '').replace(' ', '') == 
                normalized_lower.replace('&', 'and').replace('(', '').replace(')', '').replace(',', '').replace(' ', '') or
                term_name_lower.replace('&', 'and').replace('(', '').replace(')', '').replace(',', '').replace(' ', '') == 
                specialty_lower.replace('&', 'and').replace('(', '').replace(')', '').replace(',', '').replace(' ', '')):
                print(f"✅ Found similar match: {term['name']} for {normalized_specialty} (ID: {term['id']})")
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
            elif response.status_code == 400:
                # Handle "term_exists" error - extract existing term ID
                try:
                    error_data = response.json()
                    print(f"⚠️ Creation failed: {response.status_code} - {error_data}")
                    
                    if "term_exists" in response.text or "already exists" in response.text:
                        print(f"🔄 Term exists but not found in search, extracting ID from error...")
                        
                        # Extract term_id from various possible error response formats
                        existing_id = None
                        
                        # Method 1: Check data.term_id
                        if isinstance(error_data, dict) and "data" in error_data:
                            data = error_data["data"]
                            if isinstance(data, dict) and "term_id" in data:
                                existing_id = data["term_id"]
                        
                        # Method 2: Check additional_data array
                        if not existing_id and isinstance(error_data, dict) and "additional_data" in error_data:
                            additional_data = error_data["additional_data"]
                            if isinstance(additional_data, list) and len(additional_data) > 0:
                                existing_id = additional_data[0]
                        
                        # Method 3: Check top-level term_id
                        if not existing_id and isinstance(error_data, dict) and "term_id" in error_data:
                            existing_id = error_data["term_id"]
                        
                        if existing_id:
                            print(f"✅ Retrieved existing specialty ID from error: {normalized_specialty} (ID: {existing_id})")
                            return existing_id
                        else:
                            print(f"⚠️ Could not extract term_id from error response")
                            
                    # Final attempt: force refresh and search again
                    print(f"🔄 Final attempt: re-fetching all specialties...")
                    time.sleep(1)
                    final_terms = self.get_all_wordpress_terms('specialties')
                    for term in final_terms:
                        if (term["name"].lower() == normalized_specialty.lower() or 
                            term["name"].lower() == specialty_name.lower()):
                            print(f"✅ Found on final attempt: {normalized_specialty} (ID: {term['id']})")
                            return term['id']
                            
                except Exception as parse_error:
                    print(f"❌ Error parsing term_exists response: {str(parse_error)}")
                    print(f"Raw response: {response.text}")
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
    
    def find_or_create_tokyo_ward_location(self, ward_name):
        """Find or create Tokyo ward location with normalized naming (no 'City' suffix)"""
        print(f"🏢 Looking for Tokyo ward location: {ward_name}")
        
        # Tokyo ward names should never have "City" suffix
        clean_ward_name = ward_name
        ward_with_city = f"{ward_name} City"
        
        # Method 1: Try to find clean ward name first (preferred)
        search_results = self.search_wordpress_terms('location', clean_ward_name)
        for term in search_results:
            if term["name"].lower() == clean_ward_name.lower():
                print(f"✅ Found clean ward name: {clean_ward_name} (ID: {term['id']})")
                return term['id']
        
        # Method 2: Check if ward exists with "City" suffix (legacy inconsistent naming)
        search_results_city = self.search_wordpress_terms('location', ward_with_city)
        for term in search_results_city:
            if term["name"].lower() == ward_with_city.lower():
                print(f"⚠️ Found ward with 'City' suffix (inconsistent): {ward_with_city} (ID: {term['id']})")
                print(f"   NOTE: This should be renamed to '{clean_ward_name}' for consistency")
                return term['id']
        
        # Method 3: Get all location terms and search manually
        location_terms = self.get_all_wordpress_terms('location')
        
        # Try exact match for clean name
        for term in location_terms:
            if term["name"].lower() == clean_ward_name.lower():
                print(f"✅ Found clean ward name (manual search): {clean_ward_name} (ID: {term['id']})")
                return term['id']
        
        # Try exact match for ward with "City" suffix
        for term in location_terms:
            if term["name"].lower() == ward_with_city.lower():
                print(f"⚠️ Found ward with 'City' suffix (manual search): {ward_with_city} (ID: {term['id']})")
                print(f"   NOTE: This should be renamed to '{clean_ward_name}' for consistency")
                return term['id']
        
        # Method 4: Create new ward location with clean name (no "City" suffix)
        print(f"🆕 Creating Tokyo ward location: {clean_ward_name} (normalized, no 'City' suffix)")
        
        create_data = {"name": clean_ward_name, "slug": clean_ward_name.lower().replace(' ', '-')}
        
        try:
            response = requests.post(
                f"{self.wordpress_url}/wp-json/wp/v2/location",
                auth=(self.username, self.application_password),
                json=create_data
            )
            
            if response.status_code == 201:
                new_id = response.json()["id"]
                print(f"✅ Created normalized ward location: {clean_ward_name} (ID: {new_id})")
                return new_id
            elif response.status_code == 400:
                error_data = response.json()
                print(f"⚠️ Creation failed: {response.status_code} - {error_data}")
                
                if "term_exists" in response.text or "already exists" in response.text:
                    print(f"🔄 Term exists but not found, forcing refresh...")
                    time.sleep(2)
                    
                    # Try to get existing term ID from error response
                    try:
                        if "term_id" in error_data:
                            existing_id = error_data.get("term_id")
                            print(f"✅ Retrieved existing ward ID from error: {clean_ward_name} (ID: {existing_id})")
                            return existing_id
                    except:
                        pass
                    
                    # Final attempt: re-fetch all terms
                    print(f"🔄 Final attempt: re-fetching all locations for {clean_ward_name}...")
                    final_terms = self.get_all_wordpress_terms('location')
                    for term in final_terms:
                        if term["name"].lower() == clean_ward_name.lower():
                            print(f"✅ Found on final attempt: {clean_ward_name} (ID: {term['id']})")
                            return term['id']
            else:
                print(f"❌ Unexpected creation error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Creation request failed: {str(e)}")
        
        print(f"❌ Complete failure to find/create Tokyo ward location: {clean_ward_name}")
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
        if wheelchair_accessible is True or wheelchair_accessible == 'True' or wheelchair_accessible == True:
            return "Location is wheelchair accessible"
        elif wheelchair_accessible is False or wheelchair_accessible == 'False' or wheelchair_accessible == False:
            return "Location is not wheelchair accessible"
        else:
            return "Wheelchair accessibility unknown"

    def format_parking_status(self, parking_available):
        """Format parking status with descriptive sentences"""
        if parking_available is True or parking_available == 'True' or parking_available == True:
            return "Parking available"
        elif parking_available is False or parking_available == 'False' or parking_available == False:
            return "No Parking available"
        else:
            return "Parking availability unknown"
    
    def generate_google_maps_embed(self, latitude, longitude, provider_name, provider_address=""):
        """Generate Google Maps embed code targeting the specific business"""
        if not latitude or not longitude or latitude == 0 or longitude == 0:
            return ""
        
        # Create a search query that targets the specific business
        # This will show the business name and pin like Tokyo Medical University
        if provider_address:
            # Use business name + address for precise targeting
            search_query = f"{provider_name} {provider_address}".replace(" ", "+")
        else:
            # Use business name + coordinates as fallback
            search_query = f"{provider_name} {latitude},{longitude}".replace(" ", "+")
        
        # Use place search rather than raw coordinates for better targeting
        embed_code = f'''<iframe 
            width="100%" 
            height="300" 
            frameborder="0" 
            style="border:0" 
            src="https://maps.google.com/maps?q={search_query}&hl=en&z=15&output=embed" 
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

    # NOTE: upload_featured_image method removed for Google API TOS compliance
    # We link directly to Google Places photo URLs instead of downloading/storing them
    

    

    
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

    def get_primary_photo_url(self, provider) -> str:
        """Get the primary photo URL for external featured image - prioritizes Claude-selected image"""
        try:
            # First priority: Claude-selected featured image
            selected_featured_image = getattr(provider, 'selected_featured_image', '')
            if selected_featured_image and selected_featured_image.strip():
                return selected_featured_image.strip()
            
            # Fallback: Use first photo from photo_urls if no selection available
            photo_urls = getattr(provider, 'photo_urls', [])
            if not photo_urls:
                return ""
            
            # Parse photo URLs if they're in JSON string format
            if isinstance(photo_urls, str):
                photo_urls = json.loads(photo_urls)
            
            if photo_urls and isinstance(photo_urls, list) and len(photo_urls) > 0:
                # Return the first photo URL as fallback
                return photo_urls[0]
            else:
                return ""
                
        except json.JSONDecodeError:
            print(f"⚠️ Error parsing photo URLs for {getattr(provider, 'provider_name', 'Unknown Provider')}")
            return ""
        except Exception as e:
            print(f"⚠️ Error getting primary photo URL: {str(e)}")
            return ""

    def get_featured_image_source(self, provider) -> str:
        """Determine the source of the featured image"""
        try:
            selected_featured_image = getattr(provider, 'selected_featured_image', '')
            photo_urls = getattr(provider, 'photo_urls', [])
            
            # Parse photo URLs if needed
            if isinstance(photo_urls, str):
                photo_urls = json.loads(photo_urls) if photo_urls else []
            
            if selected_featured_image and selected_featured_image.strip():
                return "Claude AI Selected"
            elif photo_urls and len(photo_urls) > 0:
                return "First Available Photo"
            else:
                return "No Image Available"
                
        except Exception as e:
            print(f"⚠️ Error determining image source: {str(e)}")
            return "No Image Available"

    def get_photo_count(self, provider) -> int:
        """Get the number of available photos"""
        try:
            photo_urls = getattr(provider, 'photo_urls', [])
            
            # Parse photo URLs if needed
            if isinstance(photo_urls, str):
                photo_urls = json.loads(photo_urls) if photo_urls else []
            
            if isinstance(photo_urls, list):
                return len(photo_urls)
            else:
                return 0
                
        except Exception as e:
            print(f"⚠️ Error counting photos: {str(e)}")
            return 0

    def get_image_selection_status(self, provider) -> str:
        """Determine the image selection status"""
        try:
            selected_featured_image = getattr(provider, 'selected_featured_image', '')
            photo_urls = getattr(provider, 'photo_urls', [])
            
            # Parse photo URLs if needed
            if isinstance(photo_urls, str):
                photo_urls = json.loads(photo_urls) if photo_urls else []
            
            if selected_featured_image and selected_featured_image.strip():
                return "selected"  # AI selected
            elif photo_urls and len(photo_urls) > 0:
                return "fallback"  # Using fallback (first photo)
            elif not photo_urls or len(photo_urls) == 0:
                return "none"  # No images available
            else:
                return "pending"  # Pending selection
                
        except Exception as e:
            print(f"⚠️ Error determining selection status: {str(e)}")
            return "none"

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
        if wheelchair_accessible is True or wheelchair_accessible == 'True' or wheelchair_accessible == True:
            return "Wheelchair accessible"
        elif wheelchair_accessible is False or wheelchair_accessible == 'False' or wheelchair_accessible == False:
            return "Not wheelchair accessible"
        else:
            return "Wheelchair accessibility unknown"
    
    def format_parking_availability(self, parking_available):
        """Format parking availability for ACF dropdown field"""
        if parking_available is True or parking_available == 'True' or parking_available == True:
            return "Parking is available"
        elif parking_available is False or parking_available == 'False' or parking_available == False:
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
                    
                    # Check if explicitly marked as closed
                    if hours.get('status') == 'closed':
                        formatted_lines.append(f"{day}: Closed")
                    # Check if has open/close times
                    elif hours.get('open') and hours.get('close'):
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
            
            # Check if explicitly marked as closed
            if hours.get('status') == 'closed':
                return "Closed"
            
            # Check if has open/close times
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

    def sync_provider_to_wordpress(self, provider) -> int:
        """Sync a provider to WordPress and return the post ID"""
        try:
            provider_data = self.prepare_provider_data(provider)
            
            # Check if post already exists
            if hasattr(provider, 'wordpress_post_id') and provider.wordpress_post_id:
                # Update existing post
                post_id = self.update_wordpress_post(provider.wordpress_post_id, provider_data)
                if post_id:
                    print(f"✅ Updated WordPress post {post_id} for {provider_data['title']}")
                    return post_id
                else:
                    print(f"⚠️ Failed to update post {provider.wordpress_post_id}, creating new one")
            
            # Create new post
            post_id = self.create_wordpress_post(provider_data)
            if post_id:
                print(f"✅ Created WordPress post {post_id} for {provider_data['title']}")
                return post_id
            else:
                print(f"❌ Failed to create WordPress post for {provider_data['title']}")
                return None
                
        except Exception as e:
            print(f"❌ Error syncing provider to WordPress: {str(e)}")
            return None

    def delete_post(self, post_id: int) -> dict:
        """Delete a WordPress post by ID"""
        try:
            if not post_id:
                return {'deleted': False, 'error': 'No post ID provided'}
            
            delete_url = f"{self.wordpress_url}/wp-json/wp/v2/healthcare_provider/{post_id}?force=true"
            
            response = requests.delete(
                delete_url,
                auth=(self.username, self.application_password),
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {'deleted': True, 'data': result}
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return {'deleted': False, 'error': error_msg}
                
        except requests.exceptions.RequestException as e:
            return {'deleted': False, 'error': f"Network error: {str(e)}"}
        except Exception as e:
            return {'deleted': False, 'error': f"Unexpected error: {str(e)}"}

    def update_post_acf_fields(self, post_id: int, acf_fields: dict) -> bool:
        """Update ACF fields for a specific WordPress post"""
        try:
            if not post_id:
                print(f"❌ No post ID provided")
                return False
            
            update_data = {
                'acf': acf_fields
            }
            
            response = requests.post(
                f"{self.wordpress_url}/wp-json/wp/v2/healthcare_provider/{post_id}",
                auth=(self.username, self.application_password),
                json=update_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"❌ Failed to update ACF fields for post {post_id}: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error updating ACF fields for post {post_id}: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error updating ACF fields for post {post_id}: {str(e)}")
            return False

    def test_connection(self):
        """Test WordPress connection"""
        try:
            response = requests.get(
                f"{self.wordpress_url}/wp-json/wp/v2/types/healthcare_provider",
                auth=(self.username, self.application_password),
                timeout=10
            )
            return response.status_code == 200
        except:
            return False