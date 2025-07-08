#!/usr/bin/env python3
"""
Google Places API Integration for Healthcare Directory
Collects comprehensive healthcare provider data including reviews, photos, amenities.
"""

import os
import time
import requests
import json
import pickle
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from postgres_integration import PostgresIntegration, Provider, Metric
from textblob import TextBlob
from langdetect import detect
from anthropic import Anthropic  # Reverted to latest version

class GooglePlacesHealthcareCollector:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
        print(f"Script Location: {__file__}")
        print(f"Config Path: {config_path}")
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                print(f"File Content: [Sensitive data masked]")
            load_dotenv(config_path)
            self.google_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
            self.claude_api_key = os.getenv('CLAUDE_API_KEY')  # Re-added
            print(f"Loaded API Key: [Masked for security]")
        except FileNotFoundError:
            print(f"Error: .env file not found at {config_path}")
        except Exception as e:
            print(f"Error loading .env: {str(e)}")
        self.search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self.details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        self.photo_url = "https://maps.googleapis.com/maps/api/place/photo"
        self.distance_matrix_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        self.engine = create_engine(f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:5432/directory")
        self.Session = sessionmaker(bind=self.engine)
        self.cache_dir = "cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        self.claude = Anthropic(api_key=self.claude_api_key) if self.claude_api_key else None
        # Load cities for translation
        with open("cities.json", "r") as f:
            self.city_translations = {city["translations"]["ja"]: city["translations"]["en"] for prefecture in json.load(f)["prefectures"] for city in prefecture["cities"]}

    def log_api_usage(self, call_type, count, cost_per_call=0.017):
        """Log API usage to metrics table"""
        session = self.Session()
        session.add(Metric(
            metric_type=call_type,
            value=count,
            details={"call_type": call_type, "estimated_cost": count * cost_per_call},
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        session.commit()
        session.close()

    def cache_results(self, query, results):
        """Cache API results to avoid redundant calls"""
        cache_file = os.path.join(self.cache_dir, f"{query.replace(' ', '_')}.pkl")
        with open(cache_file, "wb") as f:
            pickle.dump(results, f)

    def load_cached_results(self, query):
        """Load cached API results"""
        cache_file = os.path.join(self.cache_dir, f"{query.replace(' ', '_')}.pkl")
        if os.path.exists(cache_file):
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        return None

    def generate_search_queries(self, limit=100, initial_cities=["Tokyo", "Yokohama", "Osaka City", "Nagoya"]):
        """Generate dynamic search queries for specified cities and specialties from JSON"""
        with open("cities.json", "r") as f:
            prefectures = json.load(f)["prefectures"]
        
        with open("specialties.json", "r") as f:
            specialties_data = json.load(f)["specialties"]
        
        specialties = specialties_data  # Use the list of strings directly
        
        cities = []
        if initial_cities:
            for prefecture in prefectures:
                for city in prefecture["cities"]:
                    if city["name"] in initial_cities:
                        cities.append(city["name"])
        else:
            cities = [city["name"] for prefecture in prefectures for city in prefecture["cities"]]
        
        base_terms = [
            "English speaking {specialty} {city}",
            "doctor {city}",
            "clinic {city}"
        ]
        queries = []
        for city in cities:
            for term in base_terms:
                if "{specialty}" in term:
                    for specialty in specialties:
                        queries.append(term.format(specialty=specialty, city=city))
                else:
                    queries.append(term.format(city=city))
        return queries[:limit]

    def search_healthcare_providers(self, query, location="Japan", radius=25000):
        """Search for healthcare providers using Google Places API"""
        cached_results = self.load_cached_results(query)
        if cached_results:
            print(f"📥 Loaded cached results for: {query}")
            return cached_results
        params = {
            'query': f"{query} {location}",
            'key': self.google_api_key,
            'type': 'health',
            'radius': radius
        }
        response = requests.get(self.search_url, params=params)
        print(f"API Response for {query}: Status {response.status_code}")
        self.log_api_usage("text_search", 1)
        if response.status_code == 200:
            results = response.json().get('results', [])
            print(f"Parsed Results for {query}: {len(results)} results")
            self.cache_results(query, results)
            return results
        else:
            print(f"❌ Search error: {response.status_code} - {response.text}")
            return []

    def get_place_details(self, place_id):
        """Get comprehensive place details from Google Places API"""
        fields = [
            'place_id', 'name', 'formatted_address', 'address_components',
            'formatted_phone_number', 'international_phone_number', 'website',
            'business_status', 'types', 'price_level', 'rating', 'user_ratings_total',
            'opening_hours', 'geometry', 'plus_code', 'photos', 'reviews',
            'wheelchair_accessible_entrance'
        ]
        params = {
            'place_id': place_id,
            'fields': ','.join(fields),
            'key': self.google_api_key,
            'language': 'en'
        }
        response = requests.get(self.details_url, params=params)
        if response.status_code == 429:
            print(f"⚠️ Rate limit exceeded, backing off for {2 ** 3} seconds")
            time.sleep(8)
            response = requests.get(self.details_url, params=params)
        self.log_api_usage("details", 1)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "OK":
                result = data.get('result', {})
                if not isinstance(result, dict) or not result.get('name'):  # Validate result
                    print(f"⚠️ Invalid result structure for place_id {place_id}: {result}")
                    return {}
                print(f"✅ Got details for: {result.get('name', 'Unknown')}")
                return result
            else:
                print(f"⚠️ API error for place_id {place_id}: {data.get('status', 'Unknown')} - {data.get('error_message', 'No message')}")
                return {}
        else:
            print(f"❌ Details error: {response.status_code} - {response.text}")
            return {}

    def get_nearest_station(self, provider_location):
        """Get the walking time to the closest train station"""
        params = {
            'location': f"{provider_location['lat']},{provider_location['lng']}",
            'radius': 2000,
            'type': 'train_station',
            'key': self.google_api_key
        }
        response = requests.get(self.search_url, params=params)
        self.log_api_usage("station_search", 1)
        if response.status_code != 200:
            print(f"❌ Station search error: {response.status_code}")
            return None
        stations = response.json().get('results', [])
        if not stations:
            print(f"⚠️ No stations found near {provider_location}")
            return None
        destinations = '|'.join([f"{station['geometry']['location']['lat']},{station['geometry']['location']['lng']}" 
                               for station in stations[:5]])
        params = {
            'origins': f"{provider_location['lat']},{provider_location['lng']}",
            'destinations': destinations,
            'mode': 'walking',
            'key': self.google_api_key
        }
        response = requests.get(self.distance_matrix_url, params=params)
        self.log_api_usage("distance_matrix", 1)
        if response.status_code != 200:
            print(f"❌ Distance Matrix error: {response.status_code}")
            return None
        result = response.json()
        if result['status'] != 'OK' or not result['rows']:
            print(f"⚠️ Distance Matrix invalid response: {result.get('status')}")
            return None
        elements = result['rows'][0]['elements']
        min_duration = float('inf')
        nearest_station = None
        for i, element in enumerate(elements):
            if element['status'] == 'OK':
                duration = element['duration']['value']
                if duration < min_duration:
                    min_duration = duration
                    nearest_station = {
                        'name': stations[i]['name'],
                        'time': element['duration']['text'],
                        'distance': element['distance']['text']
                    }
        return nearest_station

    def format_nearest_station(self, nearest_station_info):
        """Format nearest station information for ACF field"""
        if not nearest_station_info or not isinstance(nearest_station_info, dict):
            return ""
        
        station_name = nearest_station_info.get('name', 'Unknown Station')
        walking_time = nearest_station_info.get('time', 'Unknown time')
        distance = nearest_station_info.get('distance', 'Unknown distance')
        
        # Format as: "Station Name (X min walk, Y.Z km)"
        return f"{station_name} ({walking_time} walk, {distance})"

    def search_and_collect_providers(self, search_queries, max_per_query=1, daily_limit=5):
        """Search for providers and collect comprehensive data with a total provider limit"""
        print(f"🔍 Searching {len(search_queries)} queries with max {max_per_query} results per query and daily limit {daily_limit}")
        all_providers = []
        processed_place_ids = set()
        daily_requests = 0
        max_requests = 150  # Cap to ~$2.55 at $0.017/request
        providers_collected = 0

        for i, query in enumerate(search_queries):
            print(f"🔍 Processing query {i+1}/{len(search_queries)}: {query}")
            
            # Search for providers
            search_results = self.search_healthcare_providers(query)
            daily_requests += 1
            
            if not search_results:
                print(f"⚠️ No results for query: {query}")
                continue
            
            # Limit results per query
            limited_results = search_results[:max_per_query]
            print(f"📋 Found {len(search_results)} total, processing {len(limited_results)} providers")
            
            if not limited_results:
                print(f"⚠️ No results to process for {query} due to max_per_query limit")
                continue
            
            for j, provider in enumerate(limited_results, 1):
                if providers_collected >= daily_limit:
                    print(f"⏹️ Daily limit of {daily_limit} providers reached, stopping collection")
                    break
                
                print(f"📊 Processing provider {j}/{len(limited_results)} for {query}: {provider.get('name', 'Unknown')}")
                place_id = provider.get('place_id')
                if not place_id:
                    print(f"⚠️ Provider {j} missing place_id, skipping: {provider.get('name', 'Unknown')}")
                    continue
                
                # Skip if already processed
                if place_id in processed_place_ids:
                    print(f"⏭️ Provider {j} already processed, skipping")
                    continue
                
                # Get detailed information
                detailed_data = self.get_place_details(place_id)
                daily_requests += 1
                
                if not detailed_data:
                    print(f"⚠️ Could not get details for {provider.get('name', 'Unknown')}")
                    continue
                
                # Create comprehensive record
                try:
                    comprehensive_record = self.create_comprehensive_provider_record(detailed_data)
                    all_providers.append(comprehensive_record)
                    processed_place_ids.add(place_id)
                    providers_collected += 1
                    print(f"✅ Successfully processed: {comprehensive_record['provider_name']}")
                except Exception as e:
                    print(f"❌ Error processing {provider.get('name', 'Unknown')}: {str(e)}")
                    continue
                
                # Check daily request limit
                if daily_requests >= max_requests:
                    print(f"⚠️ Daily request limit ({max_requests}) reached, stopping collection")
                    break
            
            if providers_collected >= daily_limit or daily_requests >= max_requests:
                break
        
        print(f"\n📈 Collection Summary:")
        print(f"   Total unique providers collected: {len(all_providers)}")
        print(f"   Processed place IDs: {len(processed_place_ids)}")
        print(f"   Total requests made: {daily_requests}")
        
        if all_providers:
            saved_count = self.save_to_postgres(all_providers)
            print(f"💾 Saved to PostgreSQL: {saved_count} providers")
        else:
            print("⚠️ No providers to save to PostgreSQL")
        
        return all_providers

    def analyze_english_proficiency(self, place_data):
        """Analyze English proficiency with NLP and review volume"""
        english_indicators = []
        proficiency_score = 0
        reviews = place_data.get('reviews', [])
        
        # NLP-based review analysis
        english_mentions = 0
        for review in reviews:
            text = review.get('text', '').lower()
            blob = TextBlob(text)
            if any(word in blob.words for word in ['english', 'bilingual', 'fluent', 'translator', 'international']):
                sentiment = blob.sentiment.polarity
                if 'english speaking' in text or 'speaks english' in text:
                    english_indicators.append('English-speaking staff confirmed')
                    proficiency_score += 20 if sentiment > 0 else 10
                    english_mentions += 1
                elif 'translator' in text or 'translation' in text:
                    english_indicators.append('Translation services available')
                    proficiency_score += 15 if sentiment > 0 else 8
                    english_mentions += 1
                elif 'basic english' in text or 'limited english' in text:
                    english_indicators.append('Basic English support')
                    proficiency_score += 10 if sentiment > 0 else 5
                    english_mentions += 1
        
        # Weight by review volume
        if english_mentions > 5:
            proficiency_score += 10
        elif english_mentions > 0:
            proficiency_score += 5
        
        # Website URL analysis (no scraping)
        website = place_data.get('website', '').lower()
        if '/en/' in website or 'english' in website:
            english_indicators.append('English website indicated')
            proficiency_score += 10
        
        # Name analysis
        name = place_data.get('name', '').lower()
        if any(word in name for word in ['international', 'english', 'foreign', 'expat', 'global']):
            english_indicators.append('International focus in name')
            proficiency_score += 5
        
        # Assign proficiency label and convert to 1-5 scale
        if proficiency_score >= 40:
            proficiency = 'Fluent'
            simple_score = 5
        elif proficiency_score >= 20:
            proficiency = 'Conversational'
            simple_score = 4
        elif proficiency_score >= 10:
            proficiency = 'Basic'
            simple_score = 3
        else:
            proficiency = 'Unknown'
            simple_score = 0
        
        return proficiency, english_indicators, simple_score

    def extract_amenities(self, place_data):
        """Extract all amenities and services from place data"""
        amenities = []
        if place_data.get('wheelchair_accessible_entrance'):
            amenities.append('Wheelchair Accessible')
        return amenities

    def _categorize_services(self, types):
        """Categorize Google Place types into service categories"""
        category_mapping = {
            'doctor': 'General Medicine',
            'hospital': 'General Medicine', 
            'dentist': 'Dental Care',
            'physiotherapist': 'Physical Therapy',
            'pharmacy': 'Pharmacy',
            'health': 'General Medicine',
            'medical_lab': 'Diagnostic Services'
        }
        categories = []
        for place_type in types:
            if place_type in category_mapping:
                category = category_mapping[place_type]
                if category not in categories:
                    categories.append(category)
        if not categories:
            categories = ['General Medicine']
        return categories

    def determine_medical_specialties(self, place_data):
        """Determine medical specialties from place data using comprehensive filtering."""
        # Import the medical specialty filter (lazy import to avoid circular deps)
        try:
            from medical_specialty_filter import MedicalSpecialtyFilter
            specialty_filter = MedicalSpecialtyFilter()
        except ImportError:
            print("⚠️ Medical specialty filter not available, using basic extraction")
            return self._basic_specialty_extraction(place_data)
        
        if not isinstance(place_data, dict):
            return ['general_practitioner']
        
        # Use comprehensive specialty extraction
        provider_data = {
            'provider_name': place_data.get('name', ''),
            'types': place_data.get('types', []),
            'specialties': [],  # No existing specialties
            'ai_description': ''  # No description yet
        }
        
        comprehensive_specialties = specialty_filter.get_comprehensive_specialties(provider_data)
        
        # Ensure we always have at least one specialty
        if not comprehensive_specialties:
            comprehensive_specialties = ['general_practitioner']
        
        print(f"🎯 Extracted {len(comprehensive_specialties)} specialties: {comprehensive_specialties}")
        return comprehensive_specialties
    
    def _basic_specialty_extraction(self, place_data):
        """Fallback basic specialty extraction if filter system unavailable"""
        specialties = []
        
        if not isinstance(place_data, dict):
            return ['general_practitioner']
        
        # Get types from the place data
        types = place_data.get('types', [])
        if not isinstance(types, list):
            return ['general_practitioner']
        
        # Map Google Places types to medical specialties
        specialty_mapping = {
            'dentist': 'dentistry',
            'doctor': 'general_practitioner',
            'hospital': 'general_medicine',
            'pharmacy': 'pharmacy',
            'physiotherapist': 'physical_therapy',
            'veterinary_care': 'veterinary_medicine'
        }
        
        # Check place types
        for place_type in types:
            if place_type in specialty_mapping:
                specialties.append(specialty_mapping[place_type])
        
        # If no specific type found, check name for indicators
        if not specialties:
            name = place_data.get('name', '').lower()
            if any(keyword in name for keyword in ['dental', 'tooth', 'orthodont']):
                specialties.append('dentistry')
            elif any(keyword in name for keyword in ['clinic', 'hospital', 'medical']):
                specialties.append('general_practitioner')
            elif any(keyword in name for keyword in ['pharmacy', 'drug']):
                specialties.append('pharmacy')
        
        # Default to general practitioner if no specific specialty found
        if not specialties:
            specialties.append('general_practitioner')
            
        return specialties
    
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

    def process_reviews(self, reviews):
        """Process and structure review data"""
        processed_reviews = []
        for review in reviews[:5]:
            processed_review = {
                'author': review.get('author_name', 'Anonymous'),
                'rating': review.get('rating', 0),
                'text': review.get('text', '')[:500],
                'date': datetime.fromtimestamp(review.get('time', 0)).strftime('%Y-%m-%d'),
                'helpful': review.get('language', 'en') == 'en'
            }
            processed_reviews.append(processed_review)
        return processed_reviews

    def get_photo_urls(self, photos, max_photos=5):
        """Get photo URLs from Google Places API"""
        photo_urls = []
        for photo in photos[:max_photos]:
            photo_reference = photo.get('photo_reference')
            if photo_reference:
                photo_url = f"{self.photo_url}?maxwidth=800&photoreference={photo_reference}&key={self.google_api_key}"
                photo_urls.append(photo_url)
                self.log_api_usage("photo", 1)
        return photo_urls

    def process_opening_hours(self, place_data):
        """Process opening hours data from Google Places API"""
        opening_hours = place_data.get('opening_hours', {})
        
        if not opening_hours:
            return {}
        
        # Extract weekly opening hours
        weekday_text = opening_hours.get('weekday_text', [])
        periods = opening_hours.get('periods', [])
        
        processed_hours = {
            'weekday_text': weekday_text,
            'periods': periods,
            'open_now': opening_hours.get('open_now', False),
            'formatted_hours': {}
        }
        
        # Format hours for easier display
        days_mapping = {
            0: 'Sunday',
            1: 'Monday', 
            2: 'Tuesday',
            3: 'Wednesday',
            4: 'Thursday',
            5: 'Friday',
            6: 'Saturday'
        }
        
        for period in periods:
            if 'open' in period:
                day = period['open'].get('day', 0)
                day_name = days_mapping.get(day, f'Day {day}')
                open_time = period['open'].get('time', '')
                close_time = period.get('close', {}).get('time', '')
                
                # Format time from 24-hour to 12-hour format
                if open_time and len(open_time) == 4:
                    open_hour = int(open_time[:2])
                    open_min = open_time[2:]
                    open_formatted = f"{open_hour if open_hour <= 12 else open_hour - 12}:{open_min} {'AM' if open_hour < 12 else 'PM'}"
                    if open_hour == 0:
                        open_formatted = f"12:{open_min} AM"
                    elif open_hour == 12:
                        open_formatted = f"12:{open_min} PM"
                else:
                    open_formatted = open_time
                
                if close_time and len(close_time) == 4:
                    close_hour = int(close_time[:2])
                    close_min = close_time[2:]
                    close_formatted = f"{close_hour if close_hour <= 12 else close_hour - 12}:{close_min} {'AM' if close_hour < 12 else 'PM'}"
                    if close_hour == 0:
                        close_formatted = f"12:{close_min} AM"
                    elif close_hour == 12:
                        close_formatted = f"12:{close_min} PM"
                else:
                    close_formatted = close_time
                
                processed_hours['formatted_hours'][day_name] = {
                    'open': open_formatted,
                    'close': close_formatted,
                    'raw_open': open_time,
                    'raw_close': close_time
                }
        
        # Add status indicators
        if weekday_text:
            processed_hours['display_text'] = weekday_text
        
        return processed_hours

    def create_comprehensive_provider_record(self, place_data):
        """Create a comprehensive provider record with all available data, handling invalid data"""
        if not isinstance(place_data, dict):
            print(f"⚠️ Invalid place_data type for {place_data}: {type(place_data)}")
            return {}

        # Use original provider name
        name = place_data.get('name', 'Unknown Provider')

        # Translate city name using predefined list with fallback
        address_components = place_data.get('address_components', [])
        city = next((comp['long_name'] for comp in address_components if 'locality' in comp['types']), '')
        if city:
            try:
                lang = detect(city)
                if lang == 'ja' and city in self.city_translations:
                    translated_city = self.city_translations[city]
                    print(f"ℹ️ Translated city '{city}' to '{translated_city}'")
                    city = translated_city
                elif lang == 'ja' and city not in self.city_translations:
                    print(f"⚠️ Unrecognized Japanese city '{city}', using original")
                    # Fallback to original as per your preference
            except Exception as e:
                print(f"⚠️ City detection error for {city}: {str(e)}")
                city = city  # Fallback to original

        english_proficiency, english_indicators, simple_score = self.analyze_english_proficiency(place_data) if isinstance(place_data, dict) else ("Unknown", [], 0)
        amenities = self.extract_amenities(place_data) if isinstance(place_data, dict) else []
        reviews = self.process_reviews(place_data.get('reviews', [])) if isinstance(place_data, dict) else []
        photos = self.get_photo_urls(place_data.get('photos', [])) if isinstance(place_data, dict) else []
        
        # Get nearest station using Distance Matrix API
        nearest_station_info = None
        if isinstance(place_data, dict) and 'geometry' in place_data:
            provider_location = {
                'lat': place_data.get('geometry', {}).get('location', {}).get('lat', 0),
                'lng': place_data.get('geometry', {}).get('location', {}).get('lng', 0)
            }
            if provider_location['lat'] and provider_location['lng']:
                try:
                    nearest_station_info = self.get_nearest_station(provider_location)
                    if nearest_station_info:
                        print(f"🚃 Found nearest station: {nearest_station_info['name']} ({nearest_station_info['time']})")
                    else:
                        print(f"⚠️ No nearby stations found for {name}")
                except Exception as e:
                    print(f"❌ Error getting nearest station for {name}: {str(e)}")
                    nearest_station_info = None

        prefecture = next((comp['long_name'] for comp in address_components if 'administrative_area_level_1' in comp['types']), '') if isinstance(address_components, list) else ''
        if prefecture:
            try:
                lang = detect(prefecture)
                if lang == 'ja' and prefecture in self.city_translations:
                    translated_prefecture = self.city_translations[prefecture]
                    print(f"ℹ️ Translated prefecture '{prefecture}' to '{translated_prefecture}'")
                    prefecture = translated_prefecture
                elif lang == 'ja' and prefecture not in self.city_translations:
                    print(f"⚠️ Unrecognized Japanese prefecture '{prefecture}', using original")
                    # Fallback to original
            except Exception as e:
                print(f"⚠️ Prefecture detection error for {prefecture}: {str(e)}")
                prefecture = prefecture  # Fallback to original

        postal_code = next((comp['long_name'] for comp in address_components if 'postal_code' in comp['types']), '') if isinstance(address_components, list) else ''

        record = {
            'provider_name': name,
            'address': self.clean_address(place_data.get('formatted_address', '')),
            'city': city,
            'prefecture': prefecture,
            'phone': place_data.get('formatted_phone_number', ''),
            'website': self.clean_website_url(place_data.get('website', '')),
            'specialties': self.determine_medical_specialties(place_data) if isinstance(place_data, dict) else [],
            'english_proficiency': english_proficiency,
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'status': 'pending',
            'rating': place_data.get('rating', 0),
            'total_reviews': place_data.get('user_ratings_total', 0),
            'review_content': json.dumps([{'author': r.get('author', 'Anonymous'), 'rating': r.get('rating', 0), 'text': r.get('text', ''), 'date': r.get('date', '')} for r in reviews], ensure_ascii=False) if reviews else '',
            'latitude': place_data.get('geometry', {}).get('location', {}).get('lat', 0) if isinstance(place_data.get('geometry', {}), dict) else 0,
            'longitude': place_data.get('geometry', {}).get('location', {}).get('lng', 0) if isinstance(place_data.get('geometry', {}), dict) else 0,
            'plus_code': place_data.get('plus_code', {}).get('global_code', ''),
            'postal_code': postal_code,
            'photo_references': json.dumps([p.get('photo_reference') for p in place_data.get('photos', [])], ensure_ascii=False),
            'photo_count': len(place_data.get('photos', [])),
            'photo_urls': json.dumps(photos, ensure_ascii=False),
            'english_indicators': english_indicators,
            'proficiency_score': simple_score,
            'language_evidence': json.dumps(english_indicators, ensure_ascii=False) if english_indicators else '',
            'ai_description': '',
            'google_place_id': place_data.get('place_id', ''),
            'business_status': place_data.get('business_status', 'UNKNOWN'),
            'service_categories': self._categorize_services(place_data.get('types', [])) if isinstance(place_data, dict) else [],
            'wheelchair_accessible': place_data.get('wheelchair_accessible_entrance', False),
            'parking_available': 'parking' in str(place_data.get('types', [])).lower() if isinstance(place_data.get('types', []), list) else False,
            'business_hours': self.process_opening_hours(place_data) if isinstance(place_data, dict) else {},
            'nearest_station': self.format_nearest_station(nearest_station_info) if nearest_station_info else ''
        }
        return record

    def save_to_postgres(self, providers):
        """Save comprehensive provider data to PostgreSQL with advanced fingerprint-based duplicate checking"""
        try:
            from provider_fingerprinting import ProviderFingerprinter
            
            postgres = PostgresIntegration()
            is_connected, message = postgres.test_connection()
            if not is_connected:
                print(f"❌ PostgreSQL connection failed: {message}")
                return 0
            saved_count, error_count, skipped_count = 0, 0, 0
            session = postgres.Session()
            fingerprinter = ProviderFingerprinter()
            
            # Get existing fingerprints to prevent duplicates
            existing_fingerprints = set()
            
            # Get Google Place IDs
            existing_providers = session.query(Provider.google_place_id).filter(Provider.google_place_id.isnot(None)).all()
            for provider in existing_providers:
                if provider.google_place_id:
                    existing_fingerprints.add(provider.google_place_id)
            
            # Get all fingerprint types  
            fingerprint_results = session.query(
                Provider.primary_fingerprint,
                Provider.secondary_fingerprint, 
                Provider.fuzzy_fingerprint
            ).filter(Provider.primary_fingerprint.isnot(None)).all()
            
            for fp_result in fingerprint_results:
                if fp_result.primary_fingerprint:
                    existing_fingerprints.add(fp_result.primary_fingerprint)
                if fp_result.secondary_fingerprint:
                    existing_fingerprints.add(fp_result.secondary_fingerprint)
                if fp_result.fuzzy_fingerprint:
                    existing_fingerprints.add(fp_result.fuzzy_fingerprint)
            
            print(f"📊 Found {len(existing_fingerprints)} existing fingerprints in database")
            
            for provider in providers:
                try:
                    google_place_id = provider.get('google_place_id', '')
                    provider_name = provider.get('provider_name', 'Unknown')
                    
                    # Generate fingerprints for duplicate checking
                    fingerprints = fingerprinter.generate_all_fingerprints(provider)
                    
                    # Check for duplicates using comprehensive fingerprinting
                    is_duplicate, match_type = fingerprinter.check_duplicate(provider, existing_fingerprints)
                    
                    if is_duplicate:
                        print(f"⏭️ Skipping duplicate provider: {provider_name} (matched on: {match_type})")
                        skipped_count += 1
                        continue
                    
                    print(f"🔍 Saving provider: {provider_name} with status {provider.get('status', 'Not set')}")
                    provider_obj = Provider(
                        provider_name=provider_name,
                        address=provider.get('address', ''),
                        city=provider.get('city', ''),
                        prefecture=provider.get('prefecture', ''),
                        phone=provider.get('phone', ''),
                        website=provider.get('website', ''),
                        specialties=provider.get('specialties', []),
                        english_proficiency=provider.get('english_proficiency', 'Unknown'),
                        rating=provider.get('rating', 0),
                        total_reviews=provider.get('total_reviews', 0),
                        review_content=provider.get('review_content', ''),
                        review_keywords=provider.get('review_keywords', []),
                        review_highlights=provider.get('review_highlights', []),
                        photo_urls=provider.get('photo_urls', ''),
                        nearest_station=provider.get('nearest_station', ''),
                        status=provider.get('status', 'pending'),
                        created_at=provider.get('created_at', datetime.now().strftime('%Y-%m-%d')),
                        google_place_id=google_place_id,
                        ai_description=provider.get('ai_description', ''),
                        business_hours=provider.get('business_hours', {}),
                        wheelchair_accessible=provider.get('wheelchair_accessible', False),
                        parking_available=provider.get('parking_available', False),
                        # Add fingerprints for deduplication
                        primary_fingerprint=fingerprints.primary,
                        secondary_fingerprint=fingerprints.secondary if fingerprints.secondary else None,
                        fuzzy_fingerprint=fingerprints.fuzzy
                    )
                    session.add(provider_obj)
                    session.commit()
                    saved_count += 1
                    
                    # Add to existing fingerprints to prevent duplicates within this batch
                    existing_fingerprints.add(fingerprints.primary)
                    if fingerprints.secondary:
                        existing_fingerprints.add(fingerprints.secondary)
                    existing_fingerprints.add(fingerprints.fuzzy)
                    if google_place_id:
                        existing_fingerprints.add(google_place_id)
                    
                    print(f"✅ Saved {provider_name} with status {provider_obj.status}")
                except Exception as e:
                    session.rollback()
                    print(f"⚠️ Error saving {provider_name}: {str(e)}")
                    error_count += 1
            
            session.close()
            
            print(f"📈 Save Summary:")
            print(f"   ✅ Saved: {saved_count}")
            print(f"   ⏭️ Skipped duplicates: {skipped_count}")
            print(f"   ❌ Errors: {error_count}")
            
            return saved_count
        except Exception as e:
            print(f"❌ Error in PostgreSQL integration: {str(e)}")
            return 0

    def main():
        """Main execution function for testing"""
        collector = GooglePlacesHealthcareCollector()
        search_queries = collector.generate_search_queries(limit=100, initial_cities=["Tokyo", "Yokohama", "Osaka City", "Nagoya"])
        print("🏥 Google Places Healthcare Data Collection")
        print("=" * 50)
        print(f"📊 Searching {len(search_queries)} query types")
        print(f"🎯 Target: Comprehensive provider profiles")
        print()
        try:
            providers = collector.search_and_collect_providers(search_queries, max_per_query=1, daily_limit=5)
            print(f"\n📈 Collection Summary:")
            print(f"   Total unique providers collected: {len(providers)}")
            if providers:
                print(f"\n💾 Saving to PostgreSQL...")
                saved_count = collector.save_to_postgres(providers)
                print(f"\n🎉 Collection Complete!")
                print(f"   Providers collected: {len(providers)}")
                print(f"   Successfully saved: {saved_count}")
                print(f"   Success rate: {saved_count/len(providers)*100:.1f}%")
                if providers:
                    sample = providers[0]
                    print(f"\n📋 Sample Provider Data:")
                    print(f"   Name: {sample['provider_name']}")
                    print(f"   English Proficiency: {sample['english_proficiency']}")
                    print(f"   City: {sample['city']}")
                    print(f"   Prefecture: {sample['prefecture']}")
                    print(f"   Status: {sample['status']}")
                    print(f"   Nearest Station: {sample.get('nearest_station', 'Not available')}")
        except Exception as e:
            print(f"❌ Critical error in main execution: {str(e)}")

    if __name__ == "__main__":
        main()