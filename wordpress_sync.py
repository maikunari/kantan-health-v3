#!/usr/bin/env python3
"""
WordPress Healthcare Sync
Syncs provider data from PostgreSQL to WordPress as custom post types.
"""

import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables from config/.env file
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', '.env')
load_dotenv(config_path)

class WordPressHealthcareSync:
    def __init__(self):
        self.wordpress_url = os.getenv('WORDPRESS_URL')
        self.username = os.getenv('WORDPRESS_USERNAME')
        self.application_password = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        if not all([self.wordpress_url, self.username, self.application_password]):
            raise ValueError("Missing WordPress credentials in config/.env")

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
                <p><strong>English Proficiency:</strong> {provider_data.get('english_proficiency', 'Unknown')}</p>
            </div>
        </div>
        """
        return content

    def create_wordpress_post(self, provider_data):
        """Create a new WordPress post for the provider"""
        post_data = {
            'title': provider_data.get('provider_name', 'Unnamed Provider'),
            'content': self.generate_provider_content(provider_data),
            'status': 'publish',
            'categories': [1],  # Default category (e.g., Uncategorized)
            'meta': {
                'provider_address': provider_data.get('address', ''),
                'provider_city': provider_data.get('city', ''),
                'provider_phone': provider_data.get('phone', ''),
                'english_proficiency': provider_data.get('english_proficiency', 'Unknown'),
            }
        }
        # Load specialties from JSON for Healthcare Category
        with open("specialties.json", "r") as f:
            specialties_data = json.load(f)["specialties"]
        specialty_categories = {s["name"]: s["category"] for s in specialties_data}
        specialty = provider_data.get('specialties', ['General Medicine'])[0]
        category_name = next((cat for name, cat in specialty_categories.items() if name in specialty.lower()), "General Medicine")
        response = requests.get(f"{self.wordpress_url}/wp-json/wp/v2/healthcare_category", auth=(self.username, self.application_password))
        categories = response.json()
        category_id = next((cat["id"] for cat in categories if cat["name"].lower() == category_name.lower()), None)
        if not category_id:
            new_category = requests.post(
                f"{self.wordpress_url}/wp-json/wp/v2/healthcare_category",
                auth=(self.username, self.application_password),
                json={"name": category_name}
            ).json()["id"]
            category_id = new_category
        post_data['healthcare_category'] = [category_id]

        # Assign Specialties taxonomy (assuming it's a custom taxonomy)
        specialties_list = provider_data.get('specialties', [])
        response = requests.get(f"{self.wordpress_url}/wp-json/wp/v2/specialties", auth=(self.username, self.application_password))
        specialty_terms = response.json()
        specialty_ids = []
        for spec in specialties_list:
            spec_id = next((term["id"] for term in specialty_terms if term["name"].lower() == spec.lower()), None)
            if not spec_id:
                new_spec = requests.post(
                    f"{self.wordpress_url}/wp-json/wp/v2/specialties",
                    auth=(self.username, self.application_password),
                    json={"name": spec}
                ).json()["id"]
                spec_id = new_spec
            specialty_ids.append(spec_id)
        if specialty_ids:
            post_data['specialties'] = specialty_ids

        # Assign Locations taxonomy (assuming it's a custom taxonomy)
        city = provider_data.get('city', '')
        response = requests.get(f"{self.wordpress_url}/wp-json/wp/v2/locations", auth=(self.username, self.application_password))
        location_terms = response.json()
        location_id = next((term["id"] for term in location_terms if term["name"].lower() == city.lower()), None)
        if not location_id:
            new_location = requests.post(
                f"{self.wordpress_url}/wp-json/wp/v2/locations",
                auth=(self.username, self.application_password),
                json={"name": city}
            ).json()["id"]
            location_id = new_location
        if location_id:
            post_data['locations'] = [location_id]

        # Use WordPress REST API to create post
        response = requests.post(
            f"{self.wordpress_url}/wp-json/wp/v2/healthcare_provider",
            auth=(self.username, self.application_password),
            json=post_data
        )
        if response.status_code == 201:
            print(f"✅ Created WordPress post for {provider_data.get('provider_name', '')}")
        else:
            print(f"❌ Failed to create post: {response.text}")