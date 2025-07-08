#!/usr/bin/env python3
"""
WordPress Healthcare Directory Sync

This script reads provider data from Airtable and automatically creates/updates
WordPress posts with proper categories, tags, SEO optimization, and rich content.
"""

import os
import json
import time
import requests
from datetime import datetime
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables from config/.env file
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', '.env')
load_dotenv(config_path)

class WordPressHealthcareSync:
    def __init__(self):
        # WordPress API credentials  
        self.wp_url = os.getenv('WORDPRESS_URL', 'https://care-compass.jp')
        self.wp_username = os.getenv('WORDPRESS_USERNAME')
        self.wp_password = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        
        # Airtable credentials
        self.airtable_api = Api(os.getenv('AIRTABLE_PERSONAL_ACCESS_TOKEN'))
        self.airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
        self.airtable_table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Providers')
        
        # WordPress REST API endpoint
        self.wp_api_url = f"{self.wp_url}/wp-json/wp/v2"
        
        self.created_categories = {}  # Cache for created categories
        self.created_tags = {}  # Cache for created tags
    
    def get_wp_auth_headers(self):
        """Get WordPress REST API authentication headers"""
        import base64
        credentials = base64.b64encode(f"{self.wp_username}:{self.wp_password}".encode()).decode()
        return {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }
    
    def get_airtable_providers(self):
        """Fetch all provider records from Airtable"""
        try:
            table = self.airtable_api.table(self.airtable_base_id, self.airtable_table_name)
            records = table.all()
            
            print(f"📊 Retrieved {len(records)} providers from Airtable")
            return records
            
        except Exception as e:
            print(f"❌ Error fetching from Airtable: {str(e)}")
            return []
    
    def create_or_get_category(self, category_name):
        """Create WordPress category if it doesn't exist"""
        if category_name in self.created_categories:
            return self.created_categories[category_name]
        
        try:
            # Check if category exists
            response = requests.get(
                f"{self.wp_api_url}/categories",
                headers=self.get_wp_auth_headers(),
                params={'search': category_name}
            )
            
            if response.status_code == 200:
                categories = response.json()
                for cat in categories:
                    if cat['name'].lower() == category_name.lower():
                        self.created_categories[category_name] = cat['id']
                        return cat['id']
            
            # Create new category
            category_data = {
                'name': category_name,
                'slug': category_name.lower().replace(' ', '-').replace('&', 'and')
            }
            
            response = requests.post(
                f"{self.wp_api_url}/categories",
                headers=self.get_wp_auth_headers(),
                json=category_data
            )
            
            if response.status_code == 201:
                category = response.json()
                self.created_categories[category_name] = category['id']
                print(f"✅ Created category: {category_name}")
                return category['id']
            
        except Exception as e:
            print(f"❌ Error creating category {category_name}: {str(e)}")
            return None
    
    def create_or_get_tag(self, tag_name):
        """Create WordPress tag if it doesn't exist"""
        if tag_name in self.created_tags:
            return self.created_tags[tag_name]
        
        try:
            # Check if tag exists
            response = requests.get(
                f"{self.wp_api_url}/tags",
                headers=self.get_wp_auth_headers(),
                params={'search': tag_name}
            )
            
            if response.status_code == 200:
                tags = response.json()
                for tag in tags:
                    if tag['name'].lower() == tag_name.lower():
                        self.created_tags[tag_name] = tag['id']
                        return tag['id']
            
            # Create new tag
            tag_data = {
                'name': tag_name,
                'slug': tag_name.lower().replace(' ', '-').replace('&', 'and')
            }
            
            response = requests.post(
                f"{self.wp_api_url}/tags",
                headers=self.get_wp_auth_headers(),
                json=tag_data
            )
            
            if response.status_code == 201:
                tag = response.json()
                self.created_tags[tag_name] = tag['id']
                print(f"✅ Created tag: {tag_name}")
                return tag['id']
            
        except Exception as e:
            print(f"❌ Error creating tag {tag_name}: {str(e)}")
            return None
    
    def create_or_get_specialty(self, specialty_name):
        """Create or get specialty taxonomy term"""
        try:
            # Check if specialty exists
            response = requests.get(
                f"{self.wp_api_url}/specialties",
                headers=self.get_wp_auth_headers(),
                params={'search': specialty_name}
            )
            
            if response.status_code == 200:
                specialties = response.json()
                for specialty in specialties:
                    if specialty['name'].lower() == specialty_name.lower():
                        return specialty['id']
            
            # Create new specialty
            specialty_data = {
                'name': specialty_name,
                'slug': specialty_name.lower().replace(' ', '-').replace('&', 'and')
            }
            
            response = requests.post(
                f"{self.wp_api_url}/specialties",
                headers=self.get_wp_auth_headers(),
                json=specialty_data
            )
            
            if response.status_code == 201:
                specialty = response.json()
                print(f"✅ Created specialty: {specialty_name}")
                return specialty['id']
            
        except Exception as e:
            print(f"❌ Error creating specialty {specialty_name}: {str(e)}")
            return None
    
    def create_or_get_location(self, location_name):
        """Create or get location taxonomy term"""
        try:
            # Check if location exists
            response = requests.get(
                f"{self.wp_api_url}/location",
                headers=self.get_wp_auth_headers(),
                params={'search': location_name}
            )
            
            if response.status_code == 200:
                locations = response.json()
                for location in locations:
                    if location['name'].lower() == location_name.lower():
                        return location['id']
            
            # Create new location
            location_data = {
                'name': location_name,
                'slug': location_name.lower().replace(' ', '-').replace('&', 'and')
            }
            
            response = requests.post(
                f"{self.wp_api_url}/location",
                headers=self.get_wp_auth_headers(),
                json=location_data
            )
            
            if response.status_code == 201:
                location = response.json()
                print(f"✅ Created location: {location_name}")
                return location['id']
            
        except Exception as e:
            print(f"❌ Error creating location {location_name}: {str(e)}")
            return None
    
    def determine_medical_specialties(self, provider_data):
        """Intelligently determine medical specialties from provider data"""
        fields = provider_data.get('fields', {})
        name = fields.get('Provider Name', '').lower()
        specialties = []
        
        # Analyze provider name for specialty keywords
        specialty_keywords = {
            'Dentistry': ['dental', 'tooth', 'teeth', 'orthodont', 'oral'],
            'Cardiology': ['heart', 'cardio', 'cardiac'],
            'Dermatology': ['skin', 'derma', 'dermatol'],
            'Gynecology': ['women', 'gynec', 'obstet', 'maternity'],
            'Pediatrics': ['child', 'pediatr', 'kids', 'baby', 'infant'],
            'Orthopedics': ['ortho', 'bone', 'joint', 'spine'],
            'Ophthalmology': ['eye', 'vision', 'ophthal', 'optical'],
            'Psychology/Psychiatry': ['psych', 'mental', 'counseling'],
            'Emergency Medicine': ['emergency', 'urgent', 'trauma'],
            'Oncology': ['cancer', 'oncol', 'tumor'],
            'Internal Medicine': ['internal', 'medical center', 'medical university', 'hospital'],
            'General Practice': ['clinic', 'family', 'primary care', 'general practice']
        }
        
        # Check name against specialty keywords
        for specialty, keywords in specialty_keywords.items():
            if any(keyword in name for keyword in keywords):
                specialties.append(specialty)
        
        # Analyze review content for additional clues
        try:
            review_content = json.loads(fields.get('Review Content', '[]'))
            review_text = ' '.join([review.get('text', '').lower() for review in review_content[:5]])
            
            # Look for specialty mentions in reviews
            for specialty, keywords in specialty_keywords.items():
                if specialty not in specialties:  # Don't duplicate
                    if any(keyword in review_text for keyword in keywords):
                        specialties.append(specialty)
                        break  # Only add one from reviews to avoid over-categorization
        except:
            pass
        
        # Default fallback logic
        if not specialties:
            if 'clinic' in name and 'international' in name:
                specialties.append('General Practice')
            elif 'hospital' in name or 'medical center' in name:
                specialties.append('Internal Medicine')
            else:
                specialties.append('General Medicine')
        
        # Remove duplicates and limit to top 2 specialties
        specialties = list(dict.fromkeys(specialties))[:2]
        
        print(f"🎯 Determined specialties for {fields.get('Provider Name', 'Unknown')}: {specialties}")
        return specialties
    
    def upload_featured_image(self, image_url, post_title):
        """Download and upload image as WordPress media"""
        try:
            print(f"🖼️  Downloading featured image from: {image_url[:80]}...")
            
            # Download image
            response = requests.get(image_url, timeout=15)
            if response.status_code != 200:
                print(f"❌ Failed to download image: {response.status_code}")
                return None
            
            # Prepare filename
            filename = f"{post_title.lower().replace(' ', '-').replace('/', '-')}-featured.jpg"
            
            # Upload to WordPress
            files = {
                'file': (filename, response.content, 'image/jpeg')
            }
            
            # Use proper headers format
            auth_headers = self.get_wp_auth_headers()
            headers = {
                'Authorization': auth_headers['Authorization']
            }
            
            upload_response = requests.post(
                f"{self.wp_api_url}/media",
                headers=headers,
                files=files
            )
            
            if upload_response.status_code == 201:
                media = upload_response.json()
                print(f"✅ Uploaded featured image: {filename} (ID: {media['id']})")
                return media['id']
            else:
                print(f"❌ Failed to upload image: {upload_response.status_code}")
                print(f"   Response: {upload_response.text[:200]}")
                return None
            
        except Exception as e:
            print(f"❌ Error uploading image: {str(e)}")
            return None
    
    def generate_provider_content(self, provider_data):
        """Generate rich content for provider post"""
        fields = provider_data.get('fields', {})
        
        # Basic info
        name = fields.get('Provider Name', 'Unknown Provider')
        address = fields.get('Address', '')
        phone = fields.get('Phone Number', '')
        website = fields.get('Website', '')
        rating = fields.get('Rating', 0)
        total_reviews = fields.get('Total Reviews', 0)
        english_proficiency = fields.get('English Proficiency', 'Unknown')
        ai_description = fields.get('AI Description', '')
        
        # Parse JSON fields safely
        amenities = []
        top_keywords = {}
        service_categories = {}
        
        try:
            amenities = json.loads(fields.get('Amenities', '[]'))
        except:
            pass
        
        try:
            top_keywords = json.loads(fields.get('Top Keywords', '{}'))
        except:
            pass
        
        try:
            service_categories = json.loads(fields.get('Service Categories', '{}'))
        except:
            pass
        
        # Generate content with inline CSS
        content = f"""
<div class="provider-profile" style="background: #f9f9f9; padding: 20px; border-radius: 10px; margin: 20px 0;">
    <div class="provider-header" style="border-bottom: 2px solid #e0e0e0; padding-bottom: 15px; margin-bottom: 20px;">
        <h2 style="color: #2c5aa0; margin-top: 0;">{name}</h2>
        <div class="rating" style="margin-top: 10px;">
            <span class="stars" style="font-size: 18px;">{'⭐' * int(rating)}</span>
            <span class="rating-text" style="margin-left: 10px; color: #666;">{rating}/5.0 ({total_reviews} reviews)</span>
        </div>
    </div>
    
    {f'''
    <div class="provider-overview" style="background: #fff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4caf50;">
        <h3 style="color: #2c5aa0; margin-top: 0; margin-bottom: 15px;">🏥 About This Provider</h3>
        <p style="font-size: 16px; line-height: 1.6; color: #333; margin: 0;">{ai_description}</p>
    </div>
    ''' if ai_description else ''}
    
    <div class="provider-details">
        <div class="contact-info">
            <h3 style="color: #2c5aa0; margin-top: 25px; margin-bottom: 10px;">📍 Contact Information</h3>
            <p><strong>Address:</strong> {address}</p>
            {f'<p><strong>Phone:</strong> <a href="tel:{phone}">{phone}</a></p>' if phone else ''}
            {f'<p><strong>Website:</strong> <a href="{website}" target="_blank">Visit Website</a></p>' if website else ''}
        </div>
        
        <div class="english-support">
            <h3 style="color: #2c5aa0; margin-top: 25px; margin-bottom: 10px;">🗣️ Language Support</h3>
            <p><strong>English Proficiency:</strong> <span style="color: #4caf50; font-weight: bold;">{english_proficiency}</span></p>
        </div>
"""

        # Add services from keywords
        if service_categories:
            content += """
        <div class="services-offered">
            <h3 style="color: #2c5aa0; margin-top: 25px; margin-bottom: 10px;">🏥 Services & Specialties</h3>
            <ul style="list-style-type: none; padding-left: 0;">
"""
            for category, services in service_categories.items():
                if services:
                    category_name = category.replace('_', ' ').title()
                    content += f'            <li style="background: #fff; padding: 8px 12px; margin: 5px 0; border-left: 4px solid #2c5aa0;"><strong>{category_name}:</strong> '
                    service_list = [f"{service} ({count} mentions)" for service, count in list(services.items())[:3]]
                    content += ", ".join(service_list) + "</li>"
            
            content += "            </ul>\n        </div>"

        # Add amenities
        if amenities:
            content += """
        <div class="amenities">
            <h3 style="color: #2c5aa0; margin-top: 25px; margin-bottom: 10px;">✨ Amenities & Features</h3>
            <ul style="list-style-type: none; padding-left: 0;">
"""
            for amenity in amenities[:8]:  # Show top 8 amenities
                content += f'                <li style="background: #fff; padding: 8px 12px; margin: 5px 0; border-left: 4px solid #2c5aa0;">{amenity}</li>'
            content += "            </ul>\n        </div>"

        # Add patient feedback highlights
        if top_keywords:
            content += """
        <div class="patient-feedback">
            <h3 style="color: #2c5aa0; margin-top: 25px; margin-bottom: 10px;">💬 What Patients Say</h3>
            <div class="keywords" style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;">
"""
            for keyword, count in list(top_keywords.items())[:6]:
                content += f'                <span style="background: #2c5aa0; color: white; padding: 4px 8px; border-radius: 15px; font-size: 12px;">{keyword.title()} ({count} mentions)</span>'
            content += "            </div>\n        </div>"

        content += """
    </div>
</div>
"""
        
        return content
    
    def generate_seo_title(self, provider_data):
        """Generate SEO-optimized title"""
        fields = provider_data.get('fields', {})
        name = fields.get('Provider Name', 'Healthcare Provider')
        city = fields.get('City', '')
        
        # Get top keywords for SEO
        top_keywords = {}
        try:
            top_keywords = json.loads(fields.get('Top Keywords', '{}'))
        except:
            pass
        
        seo_keywords = list(top_keywords.keys())[:2]  # Top 2 keywords
        
        # Build SEO title
        title_parts = [name]
        
        if seo_keywords:
            if 'english' in seo_keywords:
                title_parts.append('English Speaking')
            if 'kids' in seo_keywords or 'children' in seo_keywords:
                title_parts.append('Family Friendly')
            if 'cleaning' in seo_keywords:
                title_parts.append('Professional Cleaning')
        
        if city:
            title_parts.append(city)
        
        return ' - '.join(title_parts)
    
    def create_wordpress_post(self, provider_data):
        """Create comprehensive WordPress post for provider"""
        fields = provider_data.get('fields', {})
        
        # Generate content
        post_title = self.generate_seo_title(provider_data)
        post_content = self.generate_provider_content(provider_data)
        
        # Set categories
        categories = []
        city = fields.get('City', '')
        if city:
            cat_id = self.create_or_get_category(f"{city} Providers")
            if cat_id:
                categories.append(cat_id)
        
        # Set tags from keywords
        tags = []
        try:
            top_keywords = json.loads(fields.get('Top Keywords', '{}'))
            for keyword in list(top_keywords.keys())[:8]:  # Top 8 keywords as tags
                tag_id = self.create_or_get_tag(keyword.title())
                if tag_id:
                    tags.append(tag_id)
        except:
            pass
        
        # Add service tags
        primary_services = fields.get('Primary Services', '')
        if primary_services:
            service_tags = [s.strip().split('(')[0].strip() for s in primary_services.split(',')]
            for service in service_tags[:5]:
                tag_id = self.create_or_get_tag(service)
                if tag_id and tag_id not in tags:
                    tags.append(tag_id)
        
        # Prepare taxonomy assignments (get IDs, not names)
        specialty_ids = []
        location_ids = []
        
        # Use Airtable Specialties field (now contains proper medical specialties)
        # Fall back to intelligent determination if Specialties field is empty or contains generic terms
        airtable_specialties = fields.get('Specialties', [])
        
        # Check if Airtable has proper medical specialties (not generic Google Places terms)
        generic_terms = {'establishment', 'point_of_interest', 'health', 'hospital', 'doctor'}
        
        if (airtable_specialties and 
            isinstance(airtable_specialties, list) and 
            not any(term in generic_terms for term in airtable_specialties)):
            # Use Airtable specialties if they're proper medical specialties
            specialty_names = airtable_specialties
            print(f"📋 Using Airtable specialties for {fields.get('Provider Name', 'Unknown')}: {specialty_names}")
        else:
            # Fall back to intelligent determination
            specialty_names = self.determine_medical_specialties(provider_data)
        
        for specialty_name in specialty_names:
            if specialty_name:
                specialty_id = self.create_or_get_specialty(specialty_name)
                if specialty_id:
                    specialty_ids.append(specialty_id)
        
        # Get location from City and Prefecture
        location_names = []
        city = fields.get('City', '')
        prefecture = fields.get('Prefecture', '')
        if city:
            location_names.append(city)
        if prefecture and prefecture not in location_names:
            location_names.append(prefecture)
        
        for location_name in location_names:
            if location_name:
                location_id = self.create_or_get_location(location_name)
                if location_id:
                    location_ids.append(location_id)
        
        # Prepare post data with ACF fields
        post_data = {
            'title': post_title,
            'content': post_content,
            'status': 'publish',
            'type': 'healthcare_provider',  # Custom post type
            'categories': categories,
            'tags': tags,
            'specialties': specialty_ids,  # Custom taxonomy (IDs)
            'location': location_ids,     # Custom taxonomy (IDs)
            'acf': {
                # Provider Details Field Group
                'provider_phone': fields.get('Phone Number', ''),
                'wheelchair_accessible': bool(fields.get('Wheelchair Accessible', False)),
                'parking_available': bool(fields.get('Parking Available', False)),
                'business_status': self.normalize_business_status(fields.get('Business Status', 'Unknown')),
                'prefecture': fields.get('Prefecture', ''),
                
                # Location & Navigation Field Group
                'latitude': float(fields.get('Latitude', 0)) if fields.get('Latitude') else None,
                'longitude': float(fields.get('Longitude', 0)) if fields.get('Longitude') else None,
                'nearest_station': fields.get('Nearest Station', ''),
                
                # Language Support Field Group
                'english_proficiency': fields.get('English Proficiency', ''),
                'proficiency_score': int(fields.get('Proficiency Score', 0)) if fields.get('Proficiency Score') else None,
                'english_indicators': self.format_english_indicators(fields.get('English Indicators', [])),
                
                # Photo Gallery Field Group
                'photo_urls': self.convert_photo_urls_for_greenshift(fields.get('Photo URLs', '')),
                
                # Accessibility & Services Field Group
                'accessibility_status': self.format_accessibility_status(fields),
                'parking_status': self.format_parking_status(fields),
                
                # Patient Insights Field Group
                'review_keywords': fields.get('Review Keywords', '{}'),
                
                # Additional fields that should be in ACF
                'provider_website': fields.get('Website', ''),
                'provider_address': fields.get('Address', ''),
                'provider_rating': str(fields.get('Rating', 0)),
                'provider_reviews': str(fields.get('Total Reviews', 0)),
                'postal_code': fields.get('Postal Code', ''),
                'ai_description': fields.get('AI Description', ''),
            },
            'meta': {
                # Non-ACF meta fields only
                'status': fields.get('Status', 'Unknown'),
                'photo_count': str(fields.get('Photo Count', 0)),
                'photo_references': fields.get('Photo References', ''),
                'review_content': fields.get('Review Content', '[]'),
                'service_categories': json.dumps(fields.get('Service Categories', [])),
                'google_place_id': fields.get('Google Place ID', ''),
                'specialties_list': json.dumps(specialty_names),
                'amenities': json.dumps(fields.get('Amenities', [])),
                'last_verified': fields.get('Last Verified', ''),
                'data_source': 'Google Places API',
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        # Handle featured image
        photo_urls = fields.get('Photo URLs', '')
        if photo_urls:
            try:
                # Parse JSON string to get list of URLs
                if isinstance(photo_urls, str):
                    photo_urls_list = json.loads(photo_urls)
                else:
                    photo_urls_list = photo_urls
                
                if photo_urls_list and len(photo_urls_list) > 0:
                    first_photo_url = photo_urls_list[0]
                    print(f"🖼️  Setting featured image from Photo URLs...")
                    media_id = self.upload_featured_image(first_photo_url, fields.get('Provider Name', 'provider'))
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
        
        return post_data

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
                return photo_urls_field
                
        except json.JSONDecodeError:
            # If it's not JSON, return as-is
            return photo_urls_field
        except Exception as e:
            print(f"⚠️  Error converting photo URLs: {str(e)}")
            return photo_urls_field
      
    def sync_providers_to_wordpress(self):
        """Main sync function"""
        print("🚀 Starting WordPress Healthcare Directory Sync")
        print("=" * 60)
        
        # Get providers from Airtable
        providers = self.get_airtable_providers()
        
        if not providers:
            print("❌ No providers found in Airtable")
            return
        
        # Get existing WordPress healthcare provider posts to avoid duplicates
        try:
            response = requests.get(
                f"{self.wp_api_url}/healthcare_provider",
                headers=self.get_wp_auth_headers(),
                params={'per_page': 100}
            )
            existing_posts = response.json() if response.status_code == 200 else []
            existing_titles = {post['title']['rendered'].lower() for post in existing_posts}
        except:
            existing_titles = set()
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        for provider in providers:
            try:
                fields = provider.get('fields', {})
                provider_name = fields.get('Provider Name', 'Unknown')
                
                # Check if post already exists
                seo_title = self.generate_seo_title(provider)
                if seo_title.lower() in existing_titles:
                    print(f"⏭️  Skipping existing provider: {provider_name}")
                    skipped_count += 1
                    continue
                
                print(f"📝 Creating post for: {provider_name}")
                
                # Create WordPress post data
                post_data = self.create_wordpress_post(provider)
                
                # Create healthcare provider post via REST API
                response = requests.post(
                    f"{self.wp_api_url}/healthcare_provider",
                    headers=self.get_wp_auth_headers(),
                    json=post_data
                )
                
                if response.status_code == 201:
                    post = response.json()
                    print(f"✅ Created WordPress post: {seo_title} (ID: {post['id']})")
                    
                    # Check if ACF fields were saved
                    if 'acf' in post and post['acf']:
                        acf_field_count = len([v for v in post['acf'].values() if v])
                        print(f"✅ ACF fields populated: {acf_field_count} fields")
                    else:
                        print(f"⚠️  Warning: ACF fields may not be populated")
                    
                    created_count += 1
                else:
                    print(f"❌ Failed to create post for {provider_name}: {response.status_code}")
                    try:
                        error_details = response.json()
                        print(f"   Error details: {error_details}")
                    except:
                        print(f"   Response text: {response.text[:200]}")
                    error_count += 1
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error processing {provider_name}: {str(e)}")
                error_count += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 WordPress Sync Complete!")
        print(f"   ✅ Created: {created_count} posts")
        print(f"   ⏭️  Skipped: {skipped_count} existing posts")
        print(f"   ❌ Errors: {error_count} failed")
        print(f"   📊 Total processed: {len(providers)} providers")
        
        if created_count > 0:
            print(f"\n🌐 Visit your WordPress site to see the new provider directory!")
            print(f"   URL: {self.wp_url}")

    def format_accessibility_status(self, fields):
        """Format accessibility status with icon"""
        wheelchair = fields.get('Wheelchair Accessible', False)
        if wheelchair:
            return "✅ Wheelchair Accessible"
        else:
            return "❌ Not Wheelchair Accessible"

    def format_parking_status(self, fields):
        """Format parking status with icon"""
        parking = fields.get('Parking Available', False)
        if parking:
            return "✅ Parking Available"
        else:
            return "❌ No Parking Available"

def main():
    """Main execution"""
    try:
        sync = WordPressHealthcareSync()
        sync.sync_providers_to_wordpress()
        
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        print("Please check your WordPress and Airtable credentials.")

if __name__ == "__main__":
    main() 