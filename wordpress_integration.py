#!/usr/bin/env python3
"""
WordPress Integration Module
Integrates healthcare provider data from PostgreSQL to WordPress as custom post types with Specialties and Locations taxonomies.
"""

import os
import requests
from dotenv import load_dotenv
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from postgres_integration import Provider

class WordPressIntegration:
    def __init__(self):
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', '.env'))
        self.wordpress_url = os.getenv('WORDPRESS_URL')
        self.username = os.getenv('WORDPRESS_USERNAME')
        self.application_password = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        if not all([self.wordpress_url, self.username, self.application_password]):
            raise ValueError("Missing WordPress credentials in config/.env")
        self.engine = create_engine(f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:5432/directory")
        self.Session = sessionmaker(bind=self.engine)
        # Load specialties.json for flat list
        with open("specialties.json", "r") as f:
            self.specialties = [item.lower() for item in json.load(f)["specialties"]]

    def generate_provider_content(self, provider_data):
        """Generate HTML content for the provider post"""
        name = provider_data.get('provider_name', '')
        ai_description = provider_data.get('ai_description', '')
        content = f"""
        <div class="provider-profile" style="background: #f9f9f9; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <div class="provider-header" style="border-bottom: 2px solid #e0e0e0; padding-bottom: 15px; margin-bottom: 20px;">
                <h2 style="color: #2c5aa0; margin-top: 0;">{name}</h2>
            </div>
            <div class="provider-overview" style="background: #fff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
                {ai_description}
            </div>
            <div class="provider-details" style="margin: 20px 0;">
                <p><strong>Address:</strong> {provider_data.get('address', 'Not provided')}</p>
                <p><strong>City:</strong> {provider_data.get('city', 'Not provided')}</p>
                <p><strong>Phone:</strong> {provider_data.get('phone', 'Not provided')}</p>
                <p><strong>Website:</strong> <a href="{provider_data.get('website', '#')}">{provider_data.get('website', 'Not provided')}</a></p>
                <p><strong>English Proficiency:</strong> {provider_data.get('english_proficiency', 'Unknown')}</p>
            </div>
        </div>
        """
        return content

    def create_wordpress_post(self, provider):
        """Create a new WordPress post for the provider"""
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

        # Assign Specialties taxonomy as flat list with capitalized names
        specialty_ids = []
        response = requests.get(f"{self.wordpress_url}/wp-json/wp/v2/specialties", auth=(self.username, self.application_password))
        if response.status_code != 200:
            print(f"⚠️ Error fetching specialties: {response.status_code} - {response.text}")
            return False
        specialty_terms = response.json()
        for spec in provider.specialties:
            spec_lower = spec.lower()
            if spec_lower not in self.specialties:
                print(f"⚠️ Specialty {spec} not in predefined list, tracking for potential addition")
                # Map to a default valid specialty if not recognized
                mapped_spec = next((s for s in self.specialties if s in spec_lower), "general_practitioner")
                spec_lower = mapped_spec
            spec_id = next((term["id"] for term in specialty_terms if term["name"].lower() == spec_lower), None)
            if not spec_id:
                capitalized_spec = spec_lower.capitalize()  # e.g., "gynecologist" -> "Gynecologist"
                new_spec_response = requests.post(
                    f"{self.wordpress_url}/wp-json/wp/v2/specialties",
                    auth=(self.username, self.application_password),
                    json={"name": capitalized_spec}
                )
                if new_spec_response.status_code == 201:
                    spec_id = new_spec_response.json()["id"]
                elif new_spec_response.status_code == 400 and "term_exists" in new_spec_response.text:
                    response = requests.get(f"{self.wordpress_url}/wp-json/wp/v2/specialties", auth=(self.username, self.application_password))
                    if response.status_code == 200:
                        specialty_terms = response.json()
                        spec_id = next((term["id"] for term in specialty_terms if term["name"].lower() == spec_lower), None)
                    else:
                        print(f"⚠️ Failed to re-fetch specialties after term_exists: {response.text}")
                else:
                    print(f"⚠️ Failed to create specialty {capitalized_spec}: {new_spec_response.text}")
            if spec_id is None:
                print(f"❌ Critical: No valid specialty ID for {spec}")
                continue
            specialty_ids.append(spec_id)
        if specialty_ids:
            post_data['specialties'] = specialty_ids  # Ensure IDs are integers

        # Assign Locations taxonomy with detailed logging and retry
        response = requests.get(f"{self.wordpress_url}/wp-json/wp/v2/location", auth=(self.username, self.application_password))
        if response.status_code != 200:
            print(f"⚠️ Error fetching locations: {response.status_code} - {response.text}")
            return False
        try:
            locations = response.json()
            if not locations:
                print(f"⚠️ No locations returned for API call, city: {provider.city}")
            location_id = next((term["id"] for term in locations if term["name"].lower() == provider.city.lower()), None)
            if not location_id:
                print(f"⚠️ No matching location found for city: {provider.city}, attempting creation")
                new_location_response = requests.post(
                    f"{self.wordpress_url}/wp-json/wp/v2/location",
                    auth=(self.username, self.application_password),
                    json={"name": provider.city}
                )
                if new_location_response.status_code == 201:
                    location_id = new_location_response.json()["id"]
                    print(f"✅ Created new location: {provider.city} (ID: {location_id})")
                elif new_location_response.status_code == 400 and "term_exists" in new_location_response.text:
                    # Retry fetch to ensure ID is captured
                    locations = requests.get(f"{self.wordpress_url}/wp-json/wp/v2/location", auth=(self.username, self.application_password)).json()
                    location_id = next((term["id"] for term in locations if term["name"].lower() == provider.city.lower()), None)
                    if location_id:
                        print(f"✅ Reused existing location: {provider.city} (ID: {location_id})")
                    else:
                        print(f"❌ Critical: Failed to retrieve ID for existing location {provider.city}")
                else:
                    print(f"⚠️ Failed to create location {provider.city}: {new_location_response.text}")
            if location_id:
                post_data['locations'] = [location_id]
            else:
                print(f"❌ Critical: No location_id assigned for city {provider.city} after all attempts")
                return False
        except TypeError as e:
            print(f"⚠️ Invalid response from locations endpoint for city {provider.city}: {str(e)} - {response.text}")
            return False
        except Exception as e:
            print(f"⚠️ Unexpected error in location assignment for {provider.city}: {str(e)}")
            return False

        # Create post
        try:
            response = requests.post(
                f"{self.wordpress_url}/wp-json/wp/v2/healthcare_provider",
                auth=(self.username, self.application_password),
                json=post_data
            )
            if response.status_code == 201:
                print(f"✅ Created WordPress post for {provider.provider_name} (ID: {response.json().get('id')})")
                return True
            else:
                print(f"❌ Failed to create post for {provider.provider_name}: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error for {provider.provider_name}: {str(e)}")
            return False

    def sync_all_providers(self):
        """Sync all providers with status 'description_generated' to WordPress"""
        session = self.Session()
        providers = session.query(Provider).filter_by(status="description_generated").all()
        results = {"published": 0, "errors": 0}

        if not providers:
            print("⚠️ No providers with status 'description_generated' found")
            return results

        print(f"🔍 Found {len(providers)} providers with status 'description_generated'")
        for provider in providers:
            if self.create_wordpress_post(provider):
                provider.status = "published"
                session.commit()
                results["published"] += 1
            else:
                results["errors"] += 1
        session.close()
        return results

    def run_sync(self):
        """Run the synchronization process"""
        results = self.sync_all_providers()
        print(f"✅ WordPress Sync Complete!")
        print(f"   Published: {results['published']}, Errors: {results['errors']}")

if __name__ == "__main__":
    sync = WordPressIntegration()
    sync.run_sync()