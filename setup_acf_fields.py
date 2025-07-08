#!/usr/bin/env python3
"""
ACF Field Setup Script for WordPress Healthcare Directory
Automatically configures all required ACF fields via REST API
"""

import os
import requests
import json
from dotenv import load_dotenv

class ACFFieldSetup:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
        load_dotenv(config_path)
        self.wordpress_url = os.getenv('WORDPRESS_URL', 'https://care-compass.jp')
        self.username = os.getenv('WORDPRESS_USERNAME')
        self.application_password = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        
        if not all([self.wordpress_url, self.username, self.application_password]):
            raise ValueError("Missing WordPress credentials in .env")
        
        self.auth = (self.username, self.application_password)
        self.headers = {'Content-Type': 'application/json'}

    def create_field_group(self, field_group_data):
        """Create a field group via ACF REST API"""
        url = f"{self.wordpress_url}/wp-json/acf/v3/field-groups"
        
        response = requests.post(url, auth=self.auth, json=field_group_data, headers=self.headers)
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Created field group: {field_group_data['title']} (ID: {result.get('id')})")
            return result.get('id')
        else:
            print(f"❌ Failed to create field group: {field_group_data['title']}")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    def get_existing_field_groups(self):
        """Get existing field groups to avoid duplicates"""
        url = f"{self.wordpress_url}/wp-json/acf/v3/field-groups"
        
        response = requests.get(url, auth=self.auth)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get existing field groups")
            return []

    def setup_provider_details_group(self):
        """Setup Provider Details field group"""
        field_group = {
            "title": "Provider Details",
            "fields": [
                {
                    "label": "Provider Phone",
                    "name": "provider_phone",
                    "type": "text",
                    "instructions": "Healthcare provider phone number",
                    "required": 0,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Wheelchair Accessible",
                    "name": "wheelchair_accessible",
                    "type": "select",
                    "instructions": "Wheelchair accessibility status",
                    "required": 0,
                    "choices": {
                        "accessible": "Wheelchair Accessible",
                        "not_accessible": "Not Wheelchair Accessible",
                        "unknown": "Accessibility Unknown"
                    },
                    "default_value": "unknown",
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Parking Available",
                    "name": "parking_available", 
                    "type": "select",
                    "instructions": "Parking availability status",
                    "required": 0,
                    "choices": {
                        "available": "Parking Available",
                        "not_available": "Parking Not Available", 
                        "unknown": "Parking Unknown"
                    },
                    "default_value": "unknown",
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Business Status",
                    "name": "business_status",
                    "type": "text",
                    "instructions": "Current business operating status",
                    "required": 0,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Prefecture",
                    "name": "prefecture",
                    "type": "text",
                    "instructions": "Prefecture/State location",
                    "required": 0,
                    "wrapper": {"width": "50"}
                }
            ],
            "location": [
                [
                    {
                        "param": "post_type",
                        "operator": "==",
                        "value": "healthcare_provider"
                    }
                ]
            ],
            "menu_order": 1,
            "position": "normal",
            "style": "default",
            "label_placement": "top",
            "instruction_placement": "label"
        }
        
        return self.create_field_group(field_group)

    def setup_business_hours_group(self):
        """Setup Business Hours field group"""
        field_group = {
            "title": "Business Hours",
            "fields": [
                {
                    "label": "Complete Business Hours",
                    "name": "business_hours",
                    "type": "textarea",
                    "instructions": "Complete formatted business hours for all days",
                    "required": 0,
                    "rows": 8,
                    "wrapper": {"width": "100"}
                },
                {
                    "label": "Monday Hours",
                    "name": "hours_monday",
                    "type": "text",
                    "instructions": "Monday operating hours",
                    "required": 0,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Tuesday Hours", 
                    "name": "hours_tuesday",
                    "type": "text",
                    "instructions": "Tuesday operating hours",
                    "required": 0,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Wednesday Hours",
                    "name": "hours_wednesday", 
                    "type": "text",
                    "instructions": "Wednesday operating hours",
                    "required": 0,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Thursday Hours",
                    "name": "hours_thursday",
                    "type": "text", 
                    "instructions": "Thursday operating hours",
                    "required": 0,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Friday Hours",
                    "name": "hours_friday",
                    "type": "text",
                    "instructions": "Friday operating hours", 
                    "required": 0,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Saturday Hours",
                    "name": "hours_saturday",
                    "type": "text",
                    "instructions": "Saturday operating hours",
                    "required": 0,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Sunday Hours",
                    "name": "hours_sunday",
                    "type": "text",
                    "instructions": "Sunday operating hours",
                    "required": 0,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Open Now Status",
                    "name": "open_now",
                    "type": "select",
                    "instructions": "Current open/closed status",
                    "required": 0,
                    "choices": {
                        "Open Now": "Currently Open",
                        "Closed": "Currently Closed",
                        "Status unknown": "Status Unknown"
                    },
                    "default_value": "Status unknown",
                    "wrapper": {"width": "50"}
                }
            ],
            "location": [
                [
                    {
                        "param": "post_type",
                        "operator": "==", 
                        "value": "healthcare_provider"
                    }
                ]
            ],
            "menu_order": 2,
            "position": "normal",
            "style": "default",
            "label_placement": "top",
            "instruction_placement": "label"
        }
        
        return self.create_field_group(field_group)

    def setup_location_navigation_group(self):
        """Setup Location & Navigation field group"""
        field_group = {
            "title": "Location & Navigation",
            "fields": [
                {
                    "label": "Latitude",
                    "name": "latitude",
                    "type": "number",
                    "instructions": "GPS latitude coordinate",
                    "required": 0,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Longitude",
                    "name": "longitude", 
                    "type": "number",
                    "instructions": "GPS longitude coordinate",
                    "required": 0,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Nearest Station",
                    "name": "nearest_station",
                    "type": "text",
                    "instructions": "Nearest train/subway station", 
                    "required": 0,
                    "wrapper": {"width": "100"}
                },
                {
                    "label": "Google Maps Embed",
                    "name": "google_maps_embed",
                    "type": "textarea",
                    "instructions": "Google Maps embed code or URL",
                    "required": 0,
                    "rows": 4,
                    "wrapper": {"width": "100"}
                }
            ],
            "location": [
                [
                    {
                        "param": "post_type",
                        "operator": "==",
                        "value": "healthcare_provider"
                    }
                ]
            ],
            "menu_order": 3,
            "position": "normal", 
            "style": "default",
            "label_placement": "top",
            "instruction_placement": "label"
        }
        
        return self.create_field_group(field_group)

    def setup_language_support_group(self):
        """Setup Language Support field group"""
        field_group = {
            "title": "Language Support",
            "fields": [
                {
                    "label": "English Proficiency",
                    "name": "english_proficiency",
                    "type": "select",
                    "instructions": "English language proficiency level",
                    "required": 0,
                    "choices": {
                        "Fluent": "Fluent English",
                        "Conversational": "Conversational English", 
                        "Basic": "Basic English",
                        "Unknown": "English Level Unknown"
                    },
                    "default_value": "Unknown",
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Proficiency Score",
                    "name": "proficiency_score",
                    "type": "number",
                    "instructions": "Numeric proficiency score (0-5)",
                    "required": 0,
                    "min": 0,
                    "max": 5,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "English Indicators",
                    "name": "english_indicators", 
                    "type": "textarea",
                    "instructions": "Evidence of English language support from reviews",
                    "required": 0,
                    "rows": 4,
                    "wrapper": {"width": "100"}
                }
            ],
            "location": [
                [
                    {
                        "param": "post_type",
                        "operator": "==",
                        "value": "healthcare_provider"
                    }
                ]
            ],
            "menu_order": 4,
            "position": "normal",
            "style": "default", 
            "label_placement": "top",
            "instruction_placement": "label"
        }
        
        return self.create_field_group(field_group)

    def setup_additional_fields_group(self):
        """Setup Additional Essential Fields group"""
        field_group = {
            "title": "Additional Provider Information",
            "fields": [
                {
                    "label": "Provider Website",
                    "name": "provider_website",
                    "type": "url",
                    "instructions": "Official website URL",
                    "required": 0,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Provider Address",
                    "name": "provider_address",
                    "type": "textarea",
                    "instructions": "Complete address",
                    "required": 0,
                    "rows": 3,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Provider Rating",
                    "name": "provider_rating", 
                    "type": "text",
                    "instructions": "Google Reviews rating",
                    "required": 0,
                    "wrapper": {"width": "33"}
                },
                {
                    "label": "Total Reviews",
                    "name": "provider_reviews",
                    "type": "text",
                    "instructions": "Number of Google Reviews",
                    "required": 0,
                    "wrapper": {"width": "33"}
                },
                {
                    "label": "Postal Code",
                    "name": "postal_code",
                    "type": "text",
                    "instructions": "Postal/ZIP code",
                    "required": 0,
                    "wrapper": {"width": "34"}
                },
                {
                    "label": "AI Description",
                    "name": "ai_description",
                    "type": "textarea",
                    "instructions": "AI-generated provider description",
                    "required": 0,
                    "rows": 5,
                    "wrapper": {"width": "100"}
                },
                {
                    "label": "Provider City",
                    "name": "provider_city",
                    "type": "text", 
                    "instructions": "City location",
                    "required": 0,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Photo URLs",
                    "name": "photo_urls",
                    "type": "textarea",
                    "instructions": "Photo URLs from Google Places",
                    "required": 0,
                    "rows": 4,
                    "wrapper": {"width": "100"}
                }
            ],
            "location": [
                [
                    {
                        "param": "post_type",
                        "operator": "==",
                        "value": "healthcare_provider"
                    }
                ]
            ],
            "menu_order": 5,
            "position": "normal",
            "style": "default",
            "label_placement": "top", 
            "instruction_placement": "label"
        }
        
        return self.create_field_group(field_group)

    def setup_accessibility_services_group(self):
        """Setup Accessibility & Services field group (duplicate fields for compatibility)"""
        field_group = {
            "title": "Accessibility & Services",
            "fields": [
                {
                    "label": "Accessibility Status",
                    "name": "accessibility_status",
                    "type": "text",
                    "instructions": "Detailed accessibility status description",
                    "required": 0,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Parking Status", 
                    "name": "parking_status",
                    "type": "text",
                    "instructions": "Detailed parking status description",
                    "required": 0,
                    "wrapper": {"width": "50"}
                }
            ],
            "location": [
                [
                    {
                        "param": "post_type",
                        "operator": "==",
                        "value": "healthcare_provider"
                    }
                ]
            ],
            "menu_order": 6,
            "position": "normal",
            "style": "default",
            "label_placement": "top",
            "instruction_placement": "label"
        }
        
        return self.create_field_group(field_group)

    def setup_patient_insights_group(self):
        """Setup Patient Insights field group"""
        field_group = {
            "title": "Patient Insights",
            "fields": [
                {
                    "label": "Review Keywords",
                    "name": "review_keywords",
                    "type": "textarea",
                    "instructions": "Key themes from patient reviews",
                    "required": 0,
                    "rows": 4,
                    "wrapper": {"width": "50"}
                },
                {
                    "label": "Patient Highlights",
                    "name": "patient_highlights",
                    "type": "textarea", 
                    "instructions": "Highlighted positive patient feedback",
                    "required": 0,
                    "rows": 4,
                    "wrapper": {"width": "50"}
                }
            ],
            "location": [
                [
                    {
                        "param": "post_type",
                        "operator": "==",
                        "value": "healthcare_provider"
                    }
                ]
            ],
            "menu_order": 7,
            "position": "normal",
            "style": "default",
            "label_placement": "top",
            "instruction_placement": "label"
        }
        
        return self.create_field_group(field_group)

    def setup_all_field_groups(self):
        """Setup all required field groups"""
        print("🚀 Setting up ACF Field Groups for Healthcare Directory")
        print("=" * 60)
        
        # Check existing field groups
        existing_groups = self.get_existing_field_groups()
        existing_titles = [group.get('title', '') for group in existing_groups]
        
        field_groups = [
            ("Provider Details", self.setup_provider_details_group),
            ("Business Hours", self.setup_business_hours_group),
            ("Location & Navigation", self.setup_location_navigation_group),
            ("Language Support", self.setup_language_support_group),
            ("Additional Provider Information", self.setup_additional_fields_group),
            ("Accessibility & Services", self.setup_accessibility_services_group),
            ("Patient Insights", self.setup_patient_insights_group)
        ]
        
        created_count = 0
        skipped_count = 0
        
        for title, setup_function in field_groups:
            if title in existing_titles:
                print(f"⏭️ Skipping existing field group: {title}")
                skipped_count += 1
            else:
                result = setup_function()
                if result:
                    created_count += 1
                
        print(f"\n📊 Setup Summary:")
        print(f"   ✅ Created: {created_count} field groups")
        print(f"   ⏭️ Skipped: {skipped_count} existing field groups")
        
        if created_count > 0:
            print(f"\n🎉 ACF field groups setup completed successfully!")
            print("   Your WordPress site is now ready for healthcare provider data!")
        else:
            print(f"\n✅ All field groups already exist - no changes needed")

def main():
    """Main execution function"""
    try:
        acf_setup = ACFFieldSetup()
        acf_setup.setup_all_field_groups()
    except Exception as e:
        print(f"❌ Error setting up ACF fields: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1) 