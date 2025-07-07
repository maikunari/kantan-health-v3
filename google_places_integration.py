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
from postgres_integration import PostgresIntegration, Provider
from textblob import TextBlob

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

    def log_api_usage(self, call_type, count, cost_per_call=0.017):
        """Log API usage to metrics table"""
        session = self.Session()
        session.add(Metric(
            metric_type="api_calls",
            value=count,
            details={"call_type": call_type, "estimated_cost": count * cost_per_call}
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

    def generate_search_queries(self, limit=50, initial_cities=["Tokyo", "Yokohama", "Osaka City", "Nagoya"]):
        """Generate dynamic search queries for specified cities and specialties from JSON"""
        with open("cities.json", "r") as f:
            prefectures = json.load(f)["prefectures"]
        
        with open("specialties.json", "r") as f:
            specialties_data = json.load(f)["specialties"]
            specialties = [s["name"] for s in specialties_data]
        
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
            "International clinic {city}",
            "Foreign friendly hospital {city}",
            "Expat clinic {city}",
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

    def search_healthcare_providers(self, query, location="Japan", radius=50000):
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
        self.log_api_usage("details", 1)
        if response.status_code == 200:
            result = response.json().get('result', {})
            if result:
                print(f"✅ Got details for: {result.get('name', 'Unknown')}")
            else:
                print(f"⚠️ Empty result for place_id: {place_id}")
            return result
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

    def search_and_collect_providers(self, search_queries, max_per_query=10):
        """Search for providers and collect comprehensive data"""
        print(f"🔍 Searching {len(search_queries)} queries with max {max_per_query} results per query")
        all_providers = []
        processed_place_ids = set()
        
        for i, query in enumerate(search_queries):
            print(f"🔍 Processing query {i+1}/{len(search_queries)}: {query}")
            
            # Search for providers
            search_results = self.search_healthcare_providers(query)
            
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
                if not detailed_data:
                    print(f"⚠️ Could not get details for {provider.get('name', 'Unknown')}")
                    continue
                
                # Create comprehensive record
                try:
                    comprehensive_record = self.create_comprehensive_provider_record(detailed_data)
                    all_providers.append(comprehensive_record)
                    processed_place_ids.add(place_id)
                    print(f"✅ Successfully processed: {comprehensive_record['provider_name']}")
                except Exception as e:
                    print(f"❌ Error processing {provider.get('name', 'Unknown')}: {str(e)}")
                    continue
                
                # Add small delay to respect API rate limits
                time.sleep(0.1)
        
        print(f"\n📈 Collection Summary:")
        print(f"   Total unique providers collected: {len(all_providers)}")
        print(f"   Processed place IDs: {len(processed_place_ids)}")
        
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
        
        # Assign proficiency label
        if proficiency_score >= 40:
            proficiency = 'Fluent'
        elif proficiency_score >= 20:
            proficiency = 'Conversational'
        elif proficiency_score >= 10:
            proficiency = 'Basic'
        else:
            proficiency = 'Unknown'
        
        return proficiency, english_indicators, proficiency_score

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
        """Intelligently determine medical specialties from provider data"""
        name = place_data.get('name', '').lower()
        specialties = []
        with open("specialties.json", "r") as f:
            specialties_data = json.load(f)["specialties"]
            specialty_keywords = {s["name"]: s["category"] for s in specialties_data}
        for specialty, category in specialty_keywords.items():
            keywords = specialty.lower().split() + [specialty]
            if any(keyword in name for keyword in keywords):
                specialties.append(category)
        try:
            reviews = place_data.get('reviews', [])
            review_text = ' '.join([review.get('text', '').lower() for review in reviews[:5]])
            for specialty, category in specialty_keywords.items():
                if category not in specialties:
                    if any(keyword in review_text for keyword in specialty.lower().split()):
                        specialties.append(category)
                        break
        except:
            pass
        if not specialties:
            if 'clinic' in name and 'international' in name:
                specialties.append('General Practice')
            elif 'hospital' in name or 'medical_center' in name:
                specialties.append('Internal Medicine')
            else:
                specialties.append('General Medicine')
        specialties = list(dict.fromkeys(specialties))[:2]
        return specialties

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
        """Get photo URLs from Google Places photos"""
        photo_urls = []
        for photo in photos[:max_photos]:
            photo_reference = photo.get('photo_reference')
            if photo_reference:
                photo_url = f"{self.photo_url}?maxwidth=800&photoreference={photo_reference}&key={self.google_api_key}"
                photo_urls.append(photo_url)
                self.log_api_usage("photo", 1)
        return photo_urls

    def create_comprehensive_provider_record(self, place_data):
        """Create a comprehensive provider record with all available data"""
        english_proficiency, english_indicators, proficiency_score = self.analyze_english_proficiency(place_data)
        amenities = self.extract_amenities(place_data)
        reviews = self.process_reviews(place_data.get('reviews', []))
        photos = self.get_photo_urls(place_data.get('photos', []))
        
        address_components = place_data.get('address_components', [])
        city = next((comp['long_name'] for comp in address_components if 'locality' in comp['types']), '')
        prefecture = next((comp['long_name'] for comp in address_components if 'administrative_area_level_1' in comp['types']), '')
        postal_code = next((comp['long_name'] for comp in address_components if 'postal_code' in comp['types']), '')
        
        record = {
            'provider_name': place_data.get('name', ''),
            'address': place_data.get('formatted_address', ''),
            'city': city,
            'prefecture': prefecture,
            'phone': place_data.get('formatted_phone_number', ''),
            'website': place_data.get('website', ''),
            'specialties': self.determine_medical_specialties(place_data),
            'english_proficiency': english_proficiency,
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'status': 'pending',
            'rating': place_data.get('rating', 0),
            'total_reviews': place_data.get('user_ratings_total', 0),
            'review_content': json.dumps([{'author': r.get('author', 'Anonymous'), 'rating': r.get('rating', 0), 'text': r.get('text', ''), 'date': r.get('date', '')} for r in reviews], ensure_ascii=False) if reviews else '',
            'latitude': place_data.get('geometry', {}).get('location', {}).get('lat', 0),
            'longitude': place_data.get('geometry', {}).get('location', {}).get('lng', 0),
            'plus_code': place_data.get('plus_code', {}).get('global_code', ''),
            'postal_code': postal_code,
            'photo_references': json.dumps([p.get('photo_reference') for p in place_data.get('photos', [])], ensure_ascii=False),
            'photo_count': len(place_data.get('photos', [])),
            'photo_urls': json.dumps(photos, ensure_ascii=False),
            'english_indicators': english_indicators,
            'proficiency_score': proficiency_score,
            'language_evidence': json.dumps(english_indicators, ensure_ascii=False) if english_indicators else '',
            'ai_description': '',
            'google_place_id': place_data.get('place_id', ''),
            'business_status': place_data.get('business_status', 'UNKNOWN'),
            'service_categories': self._categorize_services(place_data.get('types', [])),
            'wheelchair_accessible': place_data.get('wheelchair_accessible_entrance', False),
            'parking_available': 'parking' in str(place_data.get('types', [])).lower()
        }
        
        location = place_data.get('geometry', {}).get('location', {})
        nearest_station = self.get_nearest_station(location)
        if nearest_station:
            record['nearest_station'] = f"{nearest_station['time']} to {nearest_station['name']}"
        
        return record

    def save_to_postgres(self, providers):
        """Save comprehensive provider data to PostgreSQL"""
        try:
            postgres = PostgresIntegration()
            is_connected, message = postgres.test_connection()
            if not is_connected:
                print(f"❌ PostgreSQL connection failed: {message}")
                return 0
            saved_count, error_count = 0, 0
            session = postgres.Session()
            for provider in providers:
                try:
                    print(f"🔍 Saving provider: {provider['provider_name']} with status {provider.get('status', 'Not set')}")
                    provider_obj = Provider(
                        provider_name=provider.get('provider_name', ''),
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
                        created_at=provider.get('created_at', datetime.now().strftime('%Y-%m-%d'))
                    )
                    session.add(provider_obj)
                    session.commit()
                    saved_count += 1
                    print(f"✅ Saved {provider['provider_name']} with status {provider_obj.status}")
                except Exception as e:
                    session.rollback()
                    print(f"⚠️ Error saving {provider['provider_name']}: {str(e)}")
                    error_count += 1
            session.close()
            if error_count > 0:
                print(f"⚠️ {error_count} providers had errors during save")
            return saved_count
        except Exception as e:
            print(f"❌ Error in PostgreSQL integration: {str(e)}")
            return 0

    def main():
        """Main execution function for testing"""
        collector = GooglePlacesHealthcareCollector()
        search_queries = collector.generate_search_queries(limit=10, initial_cities=["Tokyo", "Yokohama", "Osaka City", "Nagoya"])
        print("🏥 Google Places Healthcare Data Collection")
        print("=" * 50)
        print(f"📊 Searching {len(search_queries)} query types")
        print(f"🎯 Target: Comprehensive provider profiles")
        print()
        try:
            providers = collector.search_and_collect_providers(search_queries, max_per_query=10)
            print(f"\n📈 Collection Summary:")
            print(f"   Total providers found: {len(providers)}")
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