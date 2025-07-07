#!/usr/bin/env python3
"""
WordPress Integration Module
Handles synchronization of healthcare provider data with a WordPress site via REST API.
"""

import os
import requests
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from postgres_integration import Provider, PostgresIntegration

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
        self.postgres = PostgresIntegration()
        
        # Updated specialties list to match what's being generated
        self.specialties = [
            "general_practitioner", "pediatrician", "cardiologist", "dermatologist",
            "orthopedic_surgeon", "neurologist", "ophthalmologist", "dentist",
            "gynecologist", "urologist", "psychiatrist", "oncologist",
            "general_medicine", "dental_care", "physical_therapy", "pharmacy",
            "diagnostic_services", "internal_medicine", "general_practice"
        ]

    def generate_provider_content(self, provider_data):
        """Generate content for a WordPress post based on provider data."""
        content = f"""
        <h2>{provider_data.get('provider_name', 'Unknown Provider')}</h2>
        <p><strong>Location:</strong> {provider_data.get('city', 'Unknown City')}, {provider_data.get('prefecture', 'Unknown Prefecture')}</p>
        <p><strong>Address:</strong> {provider_data.get('address', 'Not available')}</p>
        <p><strong>Phone:</strong> {provider_data.get('phone', 'Not available')}</p>
        <p><strong>Website:</strong> {provider_data.get('website', 'Not available')}</p>
        <p><strong>Specialties:</strong> {', '.join(provider_data.get('specialties', ['General Practitioner']))}</p>
        <p><strong>English Proficiency:</strong> {provider_data.get('english_proficiency', 'Unknown')}</p>
        <p><strong>Description:</strong> {provider_data.get('ai_description', 'No description available')}</p>
        <p><strong>Rating:</strong> {provider_data.get('rating', 0)}/5 ({provider_data.get('total_reviews', 0)} reviews)</p>
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

    def get_all_wordpress_terms(self, taxonomy):
        """Get ALL terms from WordPress taxonomy with pagination"""
        all_terms = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.wordpress_url}/wp-json/wp/v2/{taxonomy}"
            params = {'per_page': per_page, 'page': page}
            response = requests.get(url, auth=(self.username, self.application_password), params=params)
            
            if response.status_code != 200:
                print(f"⚠️ Error fetching {taxonomy} page {page}: {response.status_code}")
                break
                
            terms = response.json()
            if not terms:  # No more results
                break
                
            all_terms.extend(terms)
            
            # Check if there are more pages
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))
            if page >= total_pages:
                break
                
            page += 1
            
        print(f"📊 Fetched {len(all_terms)} total {taxonomy} terms")
        return all_terms

    def find_or_create_specialty(self, specialty_name):
        """Find or create a specialty term"""
        # Get all specialties
        specialty_terms = self.get_all_wordpress_terms('specialties')
        
        # Normalize the specialty name for comparison
        spec_lower = specialty_name.lower().strip()
        
        # Try to find exact match first
        for term in specialty_terms:
            if term["name"].lower() == spec_lower:
                print(f"✅ Found exact specialty match: {specialty_name} (ID: {term['id']})")
                return term['id']
        
        # Try partial matches
        for term in specialty_terms:
            if spec_lower in term["name"].lower() or term["name"].lower() in spec_lower:
                print(f"✅ Found partial specialty match: {term['name']} for {specialty_name} (ID: {term['id']})")
                return term['id']
        
        # Create new specialty if not found
        capitalized_spec = specialty_name.replace('_', ' ').title()
        print(f"🆕 Creating new specialty: {capitalized_spec}")
        
        response = requests.post(
            f"{self.wordpress_url}/wp-json/wp/v2/specialties",
            auth=(self.username, self.application_password),
            json={"name": capitalized_spec}
        )
        
        if response.status_code == 201:
            new_id = response.json()["id"]
            print(f"✅ Created specialty: {capitalized_spec} (ID: {new_id})")
            return new_id
        elif response.status_code == 400 and "term_exists" in response.text:
            # Try to fetch it again
            specialty_terms = self.get_all_wordpress_terms('specialties')
            for term in specialty_terms:
                if term["name"].lower() == capitalized_spec.lower():
                    print(f"✅ Found existing specialty after creation attempt: {capitalized_spec} (ID: {term['id']})")
                    return term['id']
        
        print(f"❌ Failed to create/find specialty: {specialty_name}")
        return None

    def find_or_create_location(self, city_name):
        """Find or create a location term"""
        # Get all locations
        location_terms = self.get_all_wordpress_terms('location')
        
        city_lower = city_name.lower().strip()
        
        # Try to find exact match
        for term in location_terms:
            if term["name"].lower() == city_lower:
                print(f"✅ Found exact location match: {city_name} (ID: {term['id']})")
                return term['id']
        
        # Try partial matches
        for term in location_terms:
            if city_lower in term["name"].lower() or term["name"].lower() in city_lower:
                print(f"✅ Found partial location match: {term['name']} for {city_name} (ID: {term['id']})")
                return term['id']
        
        # Create new location
        print(f"🆕 Creating new location: {city_name}")
        response = requests.post(
            f"{self.wordpress_url}/wp-json/wp/v2/location",
            auth=(self.username, self.application_password),
            json={"name": city_name}
        )
        
        if response.status_code == 201:
            new_id = response.json()["id"]
            print(f"✅ Created location: {city_name} (ID: {new_id})")
            return new_id
        elif response.status_code == 400 and "term_exists" in response.text:
            # Try to fetch it again
            time.sleep(1)
            location_terms = self.get_all_wordpress_terms('location')
            for term in location_terms:
                if term["name"].lower() == city_name.lower():
                    print(f"✅ Found existing location after creation attempt: {city_name} (ID: {term['id']})")
                    return term['id']
        
        print(f"❌ Failed to create/find location: {city_name}")
        return None

    def create_wordpress_post(self, provider):
        """Create a new WordPress post for the provider or update if duplicate"""
        # Check for duplicate
        duplicate_id = self.check_duplicate_post(provider.provider_name, provider.city)
        if duplicate_id:
            print(f"ℹ️ Updating existing post for {provider.provider_name} (ID: {duplicate_id})")
            # For simplicity, we'll skip updates for now
            return True

        post_data = {
            'title': provider.provider_name,
            'content': self.generate_provider_content(provider.__dict__),
            'status': 'publish',
            'meta': {
                'provider_address': provider.address,
                'provider_city': provider.city,
                'provider_phone': provider.phone,
                'provider_website': provider.website,
                'english_proficiency': provider.english_proficiency,
            }
        }

        # Handle specialties
        specialty_ids = []
        if provider.specialties:
            for spec in provider.specialties:
                spec_id = self.find_or_create_specialty(spec)
                if spec_id:
                    specialty_ids.append(spec_id)
        
        if specialty_ids:
            post_data['specialties'] = specialty_ids
        else:
            # Fallback to general practitioner
            fallback_id = self.find_or_create_specialty("general_practitioner")
            if fallback_id:
                post_data['specialties'] = [fallback_id]

        # Handle location
        location_id = self.find_or_create_location(provider.city)
        if location_id:
            post_data['locations'] = [location_id]
        else:
            print(f"❌ Critical: Could not create/find location for {provider.city}")
            return False

        # Create post
        try:
            response = requests.post(
                f"{self.wordpress_url}/wp-json/wp/v2/healthcare_provider",
                auth=(self.username, self.application_password),
                json=post_data
            )
            if response.status_code == 201:
                post_id = response.json().get('id')
                print(f"✅ Created WordPress post for {provider.provider_name} (ID: {post_id})")
                return True
            else:
                print(f"❌ Failed to create post for {provider.provider_name}: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error for {provider.provider_name}: {str(e)}")
            return False

    def sync_all_providers(self):
        """Synchronize all providers from database to WordPress"""
        session = self.postgres.Session()
        providers = session.query(Provider).filter_by(status='description_generated').all()
        print(f"🔍 Found {len(providers)} providers with status 'description_generated'")
        results = {"success": 0, "errors": 0}
        
        for provider in providers:
            try:
                if self.create_wordpress_post(provider):
                    provider.status = 'published'
                    session.commit()
                    results["success"] += 1
                    print(f"✅ Successfully published {provider.provider_name} to WordPress")
                else:
                    results["errors"] += 1
                    print(f"❌ Failed to publish {provider.provider_name} to WordPress")
            except Exception as e:
                print(f"❌ Exception processing {provider.provider_name}: {str(e)}")
                results["errors"] += 1
                session.rollback()
        
        session.close()
        return results

    def run_sync(self):
        """Execute the full synchronization process"""
        results = self.sync_all_providers()
        print(f"\n📊 WordPress Sync Results:")
        print(f"   Successfully published: {results['success']}")
        print(f"   Errors: {results['errors']}")
        return results

if __name__ == "__main__":
    sync = WordPressIntegration()
    sync.run_sync()