#!/usr/bin/env python3
"""
Enhanced Google Places API Integration
With persistent caching, cost tracking, and deduplication
"""

import os
import time
import json
import logging
import requests
from typing import List, Dict, Optional, Any, Set
from datetime import datetime

from ..core.cache import PersistentCache
from ..core.cost_tracker import CostTracker
from ..core.database import DatabaseManager, Provider
from .deduplication import ProviderDeduplicator
from sqlalchemy import text

logger = logging.getLogger(__name__)


class GooglePlacesCollector:
    """Enhanced Google Places collector with cost optimization"""
    
    # Optimized field selection (only what we need)
    REQUIRED_FIELDS = [
        'place_id', 'name', 'formatted_address', 'rating', 
        'user_ratings_total', 'reviews', 'opening_hours', 
        'website', 'formatted_phone_number', 
        'geometry', 'types', 'business_status'
    ]
    
    # Tokyo's 23 Special Wards for targeted searching
    TOKYO_WARDS = [
        "Chiyoda", "Chuo", "Minato", "Shinjuku", "Bunkyo",
        "Taito", "Sumida", "Koto", "Shinagawa", "Meguro",
        "Ota", "Setagaya", "Shibuya", "Nakano", "Suginami",
        "Toshima", "Kita", "Arakawa", "Itabashi", "Nerima",
        "Adachi", "Katsushika", "Edogawa"
    ]
    
    # Major city wards for other cities
    CITY_WARDS = {
        "Yokohama": ["Naka", "Nishi", "Minami", "Hodogaya", "Isogo", 
                     "Kanagawa", "Tsurumi", "Kohoku", "Aoba", "Tsuzuki"],
        "Osaka": ["Kita", "Chuo", "Nishi", "Naniwa", "Tennoji", 
                  "Yodogawa", "Higashinari", "Abeno", "Sumiyoshi"],
        "Nagoya": ["Naka", "Higashi", "Kita", "Nishi", "Nakamura",
                   "Mizuho", "Atsuta", "Minami", "Midori"],
        "Kyoto": ["Kamigyo", "Nakagyo", "Shimogyo", "Higashiyama", 
                  "Sakyo", "Kita", "Ukyo", "Fushimi"],
        "Kobe": ["Chuo", "Hyogo", "Nada", "Higashinada", "Nagata",
                 "Suma", "Tarumi", "Kita", "Nishi"],
        "Fukuoka": ["Hakata", "Chuo", "Higashi", "Minami", "Nishi",
                    "Jonan", "Sawara"]
    }
    
    # Japanese medical terms for bilingual searching
    JAPANESE_MEDICAL_TERMS = {
        "dentist": ["歯科", "歯医者", "デンタルクリニック", "歯科医院"],
        "clinic": ["クリニック", "診療所", "医院", "内科"],
        "hospital": ["病院", "総合病院", "医療センター", "大学病院"],
        "doctor": ["医師", "医者", "ドクター", "先生"],
        "pediatrics": ["小児科", "こども病院", "小児クリニック"],
        "internal medicine": ["内科", "内科クリニック", "総合内科"],
        "orthopedics": ["整形外科", "整形外科クリニック", "リハビリ"],
        "gynecology": ["産婦人科", "婦人科", "レディースクリニック"],
        "ENT": ["耳鼻咽喉科", "耳鼻科", "ENT"],
        "emergency": ["救急", "救急病院", "急患"]
    }
    
    def __init__(self, daily_limit: int = None):
        """Initialize collector with caching and cost tracking
        
        Args:
            daily_limit: Maximum providers to collect per day
        """
        # API configuration
        self.api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY not found in environment")
        
        # API endpoints
        self.search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self.details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        
        # Initialize components
        self.cache = PersistentCache()
        self.cost_tracker = CostTracker()
        self.db = DatabaseManager()
        self.deduplicator = ProviderDeduplicator()
        
        # FIXED: Add romaji converter integration
        try:
            from ..utils.romaji_wrapper import BusinessNameRomajiConverter
            self.romaji_converter = BusinessNameRomajiConverter()
            logger.info("✅ Romaji converter integrated")
        except ImportError:
            logger.warning("⚠️ Romaji converter not available")
            self.romaji_converter = None
        
        # FIXED: Add rate limiting (2 seconds between API calls)
        self.rate_limit_delay = 2.0  # seconds between API calls
        self.last_api_call = 0
        
        # Configuration
        self.daily_limit = daily_limit
        self.processed_place_ids: Set[str] = set()
        
        # Exclusion tracking for efficiency
        self.excluded_place_ids: Set[str] = set()  # Place IDs to skip
        self.session_rejected_ids: Set[str] = set()  # Rejected in this session
        self._load_exclusion_list()
        
        # Load city translations
        self._load_city_translations()
        
        logger.info(f"✅ Google Places Collector initialized (daily limit: {daily_limit or 'None'})")
    
    def _apply_rate_limit(self):
        """Apply rate limiting between API calls"""
        current_time = time.time()
        time_since_last = current_time - self.last_api_call
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_api_call = time.time()
    
    def _load_exclusion_list(self):
        """Load place IDs to exclude from searches (existing providers and rejected)"""
        try:
            session = self.db.get_session()
            
            # Get all existing provider fingerprints from database
            # Since we don't have place_id, use provider names for now
            existing = session.execute(text("""
                SELECT DISTINCT primary_fingerprint 
                FROM providers 
                WHERE primary_fingerprint IS NOT NULL
            """)).fetchall()
            
            # For now, we'll track by fingerprint instead of place_id
            self.excluded_fingerprints = {row[0] for row in existing}
            self.excluded_place_ids = set()  # Will be populated as we discover place_ids
            
            # Also load recently rejected from cache
            for i in range(1000):  # Check last 1000 rejected entries
                rejected = self.cache.get(f"rejected_place_{i}")
                if rejected and 'place_id' in rejected:
                    self.excluded_place_ids.add(rejected['place_id'])
            
            logger.info(f"📋 Loaded {len(self.excluded_place_ids)} place IDs to exclude")
            
        except Exception as e:
            logger.warning(f"Could not load exclusion list: {e}")
            self.excluded_place_ids = set()
        finally:
            if 'session' in locals():
                session.close()
    
    def extract_romaji_name(self, name: str) -> str:
        """Extract Romaji (English) name from potentially bilingual provider name
        
        Examples:
        - "日の出薬局 Hinode Pharmacy" -> "Hinode Pharmacy"
        - "DUOデンタルクリニック" -> "DUO Dental Clinic"
        - "グローバルヘルスケアクリニック Global Healthcare Clinic" -> "Global Healthcare Clinic"
        - "Ōkura ENT" -> "Okura ENT" (normalize special characters)
        """
        if not name:
            return name
        
        # Check if name contains both Japanese and English
        has_japanese = any(ord(char) > 0x3000 for char in name)
        has_english = any(char.isalpha() and ord(char) < 128 for char in name)
        
        if has_japanese and has_english:
            # Split and find the English part
            # Common patterns: "Japanese English" or "Japanese (English)"
            parts = name.split()
            english_parts = []
            
            for part in parts:
                # Skip pure Japanese parts
                if all(ord(char) > 0x3000 or not char.isalpha() for char in part):
                    continue
                # Keep parts with English letters
                if any(char.isalpha() and ord(char) < 128 for char in part):
                    english_parts.append(part)
            
            if english_parts:
                result = ' '.join(english_parts)
            else:
                # Fallback: take everything after Japanese characters end
                # Find the last Japanese character
                last_japanese_idx = -1
                for i, char in enumerate(name):
                    if ord(char) > 0x3000:
                        last_japanese_idx = i
                
                if last_japanese_idx >= 0 and last_japanese_idx < len(name) - 1:
                    result = name[last_japanese_idx + 1:].strip()
                else:
                    result = name
        else:
            result = name
        
        # Normalize special characters (Ō -> O, etc.)
        replacements = {
            'Ō': 'O', 'ō': 'o', 'Ū': 'U', 'ū': 'u',
            'Ā': 'A', 'ā': 'a', 'Ī': 'I', 'ī': 'i',
            'Ē': 'E', 'ē': 'e'
        }
        for old, new in replacements.items():
            result = result.replace(old, new)
        
        # Clean up any remaining issues
        result = ' '.join(result.split())  # Normalize whitespace
        result = result.strip('()[]（）【】')  # Remove brackets
        
        # If result is empty or too short, return original
        if len(result) < 3:
            return name
        
        return result
    
    def _load_city_translations(self):
        """Load city translations for Japanese place names"""
        try:
            cities_path = os.path.join(os.path.dirname(__file__), '..', '..', 'cities.json')
            with open(cities_path, 'r') as f:
                data = json.load(f)
                self.city_translations = {
                    city["translations"]["ja"]: city["translations"]["en"]
                    for prefecture in data["prefectures"]
                    for city in prefecture["cities"]
                }
        except Exception as e:
            logger.warning(f"Could not load city translations: {e}")
            self.city_translations = {}
    
    def generate_search_queries(self, cities: List[str] = None, 
                              specialties: List[str] = None,
                              wards: List[str] = None,
                              use_ward_specific: bool = True,
                              limit: int = 100) -> List[str]:
        """Generate optimized search queries with ward-level precision
        
        Args:
            cities: List of cities to search
            specialties: List of medical specialties
            wards: Specific wards to search (overrides city wards)
            use_ward_specific: Whether to use ward-specific searches
            limit: Maximum number of queries
            
        Returns:
            List of search queries
        """
        if not cities:
            cities = ["Tokyo", "Yokohama", "Osaka", "Fukuoka", "Kyoto"]
        
        if not specialties:
            # Load from specialties.json if available
            try:
                spec_path = os.path.join(os.path.dirname(__file__), '..', '..', 'specialties.json')
                with open(spec_path, 'r') as f:
                    specialties = json.load(f)["specialties"]
            except:
                specialties = ["doctor", "clinic", "hospital", "dentist"]
        
        queries = []
        
        # If ward-specific searching is enabled
        if use_ward_specific:
            for city in cities:
                # Get wards for this city
                if wards:
                    # Use provided wards
                    city_wards = wards
                elif city == "Tokyo":
                    city_wards = self.TOKYO_WARDS
                elif city in self.CITY_WARDS:
                    city_wards = self.CITY_WARDS[city]
                else:
                    # Fall back to city-level search
                    city_wards = [city]
                
                # Generate ward-specific queries
                for ward in city_wards:
                    for specialty in specialties:
                        # Ward-specific patterns in English
                        ward_patterns = [
                            f"{specialty} {ward}",  # Simple and effective
                            f"{specialty} {ward} {city}",  # With city context
                            f"English {specialty} {ward}",  # English focus
                        ]
                        
                        for pattern in ward_patterns:
                            queries.append(pattern)
                            if len(queries) >= limit:
                                return queries
                        
                        # Also add Japanese term searches for better coverage
                        if specialty.lower() in self.JAPANESE_MEDICAL_TERMS:
                            for jp_term in self.JAPANESE_MEDICAL_TERMS[specialty.lower()][:2]:  # Use top 2 Japanese terms
                                jp_query = f"{jp_term} {ward}"
                                queries.append(jp_query)
                                if len(queries) >= limit:
                                    return queries
        
        # Also add some city-level queries for broader coverage
        for city in cities:
            for specialty in specialties:
                city_patterns = [
                    f"English speaking {specialty} {city}",
                    f"International {specialty} {city}",
                ]
                
                for pattern in city_patterns:
                    queries.append(pattern)
                    if len(queries) >= limit:
                        return queries
        
        return queries[:limit]
    
    def search_providers(self, query: str, limit: int = None, max_results: int = 60) -> List[Dict]:
        """Search for healthcare providers with pagination support
        
        This method now supports pagination to get up to 60 results (3 pages of 20).
        Google Places API returns max 20 results per request, but provides a 
        next_page_token for additional results.
        
        Args:
            query: Search query
            limit: Maximum results to return (backwards compatibility)
            max_results: Maximum results to return (default 60, max 60)
            
        Returns:
            List of provider results (up to 60)
        """
        # Handle backwards compatibility - use limit if provided
        if limit is not None:
            max_results = limit
            
        # Limit max_results to 60 (Google's maximum with pagination)
        max_results = min(max_results, 60)
        
        # Check cache first
        cache_key = f"search_{query}_paginated"
        cached = self.cache.get(cache_key, 'search')
        if cached:
            logger.info(f"✅ Cache hit for search: {query} ({len(cached)} results)")
            self.cost_tracker.log_request('place_search', cached=True)
            return cached[:max_results]
        
        all_results = []
        next_page_token = None
        page_count = 0
        max_pages = 3  # Google allows max 3 pages (60 results total)
        
        while page_count < max_pages:
            # Check budget for each page request
            can_proceed, reason = self.cost_tracker.can_make_request('place_search')
            if not can_proceed:
                logger.warning(f"❌ Budget limit on page {page_count + 1}: {reason}")
                break
            
            # Prepare params for this page
            params = {
                'key': self.api_key,
                'language': 'en',
                'region': 'jp',
                'type': 'doctor|hospital|health|dentist'
            }
            
            # First page uses query, subsequent pages use pagetoken
            if page_count == 0:
                params['query'] = query
            else:
                if not next_page_token:
                    break  # No more pages available
                params['pagetoken'] = next_page_token
            
            try:
                # FIXED: Apply rate limiting
                self._apply_rate_limit()
                
                response = requests.get(self.search_url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                status = data.get('status')
                
                if status not in ['OK', 'ZERO_RESULTS']:
                    logger.error(f"API error on page {page_count + 1}: {status}")
                    if page_count == 0:
                        return []  # First page failed, return empty
                    break  # Subsequent page failed, return what we have
                
                # Add results from this page
                page_results = data.get('results', [])
                all_results.extend(page_results)
                
                # Log cost for this page
                self.cost_tracker.log_request('place_search', search_query=f"{query}_page{page_count + 1}")
                
                logger.info(f"📄 Page {page_count + 1}: Found {len(page_results)} results for: {query}")
                
                # Check if we have enough results
                if len(all_results) >= max_results:
                    break
                
                # Get next page token if available
                next_page_token = data.get('next_page_token')
                if not next_page_token:
                    break  # No more pages
                
                # Google requires a short delay before using next_page_token
                # This is MANDATORY - requests without delay will fail
                if page_count < max_pages - 1 and next_page_token:
                    logger.info("⏳ Waiting 2 seconds before next page (Google requirement)...")
                    time.sleep(2)
                
                page_count += 1
                
            except Exception as e:
                logger.error(f"Search error on page {page_count + 1}: {str(e)}")
                if page_count == 0:
                    return []  # First page failed
                break  # Return what we have from previous pages
        
        # Filter out excluded place IDs BEFORE caching
        filtered_results = []
        excluded_count = 0
        
        for result in all_results:
            place_id = result.get('place_id')
            if place_id and place_id in self.excluded_place_ids:
                excluded_count += 1
                logger.debug(f"⏭️ Skipping known/rejected place: {place_id}")
                continue
            
            # Also check if in session rejected list
            if place_id and place_id in self.session_rejected_ids:
                excluded_count += 1
                logger.debug(f"⏭️ Skipping session-rejected place: {place_id}")
                continue
                
            filtered_results.append(result)
        
        # Cache filtered results for 7 days
        if filtered_results:
            self.cache.set(cache_key, filtered_results, 'search', ttl_days=7)
        
        if excluded_count > 0:
            logger.info(f"🚫 Filtered out {excluded_count} known/rejected places from search results")
        
        logger.info(f"🔍 Total results for '{query}': {len(filtered_results)} usable (from {len(all_results)} total)")
        return filtered_results[:max_results]
    
    def get_place_details(self, place_id: str, force_refresh: bool = False, city: str = None) -> Optional[Dict]:
        """Get detailed place information with caching and deduplication
        
        Args:
            place_id: Google Place ID
            force_refresh: Skip cache and fetch fresh data (for expired references)
            city: City name for city-aware deduplication
            
        Returns:
            Place details or None
        """
        # Skip these checks if force_refresh is True
        if not force_refresh:
            # Check if already processed IN THIS CITY
            if self.cache.is_processed(place_id) and city:
                # Check if we have this provider in THIS specific city
                existing = self.db.get_provider_by_place_id(place_id)
                if existing and existing.city and existing.city.lower() == city.lower():
                    logger.info(f"✅ Already have {place_id} in {city}")
                    return None
                elif existing and existing.city:
                    # Different city - this could be a chain with multiple locations
                    logger.info(f"📍 Found {place_id} in new city: {city} (existing in {existing.city})")
                    # Continue to collect for new city
                else:
                    logger.info(f"✅ Already processed: {place_id}")
                    return None
            elif self.cache.is_processed(place_id):
                logger.info(f"✅ Already processed: {place_id}")
                return None
            
            # Check cache
            cached = self.cache.get(place_id, 'details')
            if cached:
                logger.info(f"✅ Cache hit for details: {place_id}")
                self.cost_tracker.log_request('place_details', place_id=place_id, cached=True)
                return cached
            
            # City-aware database check
            existing = self.db.get_provider_by_place_id(place_id)
            if existing:
                if city and existing.city and existing.city.lower() == city.lower():
                    logger.info(f"✅ Already have {place_id} in {city}")
                    return None
                elif city and existing.city and existing.city.lower() != city.lower():
                    # Different city - allow collection for this new city
                    logger.info(f"📍 Provider {place_id} exists in {existing.city}, collecting for {city}")
                    # Continue to collect
                else:
                    # No city specified - use old behavior
                    logger.info(f"✅ Already in database: {place_id}")
                    return None
        else:
            logger.info(f"🔄 Force refresh requested, skipping cache for: {place_id}")
        
        # Check budget
        can_proceed, reason = self.cost_tracker.can_make_request('place_details')
        if not can_proceed:
            logger.warning(f"❌ Budget limit: {reason}")
            return None
        
        # Make API request with optimized fields
        params = {
            'place_id': place_id,
            'key': self.api_key,
            'language': 'en',
            'fields': ','.join(self.REQUIRED_FIELDS)
        }
        
        try:
            # FIXED: Apply rate limiting
            self._apply_rate_limit()
            
            response = requests.get(self.details_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') != 'OK':
                logger.error(f"API error for {place_id}: {data.get('status')}")
                return None
            
            result = data.get('result', {})
            
            # Photos are no longer collected
            
            # Cache for 30 days
            self.cache.set(place_id, result, 'details', ttl_days=30)
            
            # Log cost (basic + contact data)
            self.cost_tracker.log_request('place_details', place_id=place_id)
            self.cost_tracker.log_request('contact_data', place_id=place_id)
            
            # Mark as processed
            self.cache.mark_processed(place_id)
            
            logger.info(f"📍 Retrieved details for: {result.get('name', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Details error for {place_id}: {str(e)}")
            return None
    
    def create_provider_record(self, place_data: Dict, city: str = None) -> Optional[Dict]:
        """Create a provider record from place data
        
        Args:
            place_data: Google Places API response
            city: City name to override automatic detection
            
        Returns:
            Provider record or None if rejected
        """
        # Basic validation
        if not place_data or not place_data.get('place_id'):
            return None
        
        # Extract place_id first for use in error handling
        place_id = place_data.get('place_id')
        
        # Extract basic information
        record = {
            'google_place_id': place_id,
            'provider_name': place_data.get('name', ''),
            'address': place_data.get('formatted_address', ''),
            'phone': place_data.get('formatted_phone_number', ''),
            'website': place_data.get('website', ''),
            'rating': place_data.get('rating', 0),
            'total_reviews': place_data.get('user_ratings_total', 0)
        }
        
        # Extract location data
        if 'geometry' in place_data:
            location = place_data['geometry'].get('location', {})
            record['latitude'] = location.get('lat')
            record['longitude'] = location.get('lng')
        
        # Parse address components
        self._parse_address_components(place_data, record)
        
        # Override city if provided (for grid search)
        if city:
            record['city'] = city
        
        # Extract business hours
        if 'opening_hours' in place_data:
            record['business_hours'] = place_data['opening_hours'].get('weekday_text', [])
        
        # Extract medical specialties from types
        types = place_data.get('types', [])
        specialties = self._extract_specialties(types)
        record['specialties'] = specialties
        
        # Process reviews for English proficiency
        reviews = place_data.get('reviews', [])
        proficiency_data = self._analyze_english_proficiency(reviews)
        record.update(proficiency_data)
        
        # Check English proficiency threshold
        if record['proficiency_score'] < 3:  # Minimum score of 3
            logger.info(f"❌ Rejected {record['provider_name']}: Low English proficiency ({record['proficiency_score']})")
            
            # Add to session rejected list and cache
            self.session_rejected_ids.add(place_id)
            self.cache.set(f"rejected_{place_id}", {
                'place_id': place_id,
                'reason': 'low_english_proficiency',
                'score': record['proficiency_score'],
                'name': record['provider_name'],
                'timestamp': datetime.now().isoformat()
            }, cache_type='rejected', ttl_days=30)
            
            return None
        
        # Photos are no longer collected or required
        
        # Provider passed all checks - clean the name if needed
        original_name = record['provider_name']
        cleaned_name = self.extract_romaji_name(original_name)
        
        if cleaned_name != original_name:
            logger.info(f"🔤 Romanized name: '{original_name}' -> '{cleaned_name}'")
            record['provider_name'] = cleaned_name
            # Keep original for reference
            record['original_name'] = original_name
        
        # Generate fingerprints for deduplication
        fingerprints = self.deduplicator.generate_fingerprints(record)
        record.update(fingerprints)
        
        # Check for duplicates
        existing = self.db.check_fingerprints(
            fingerprints['primary_fingerprint'],
            fingerprints['secondary_fingerprint'],
            fingerprints['fuzzy_fingerprint']
        )
        
        if existing:
            logger.info(f"🔁 Duplicate found: {record['provider_name']} = {existing.provider_name}")
            return None
        
        # Set initial status
        record['status'] = 'pending'
        record['created_at'] = datetime.now().isoformat()
        
        return record
    
    def _parse_address_components(self, place_data: Dict, record: Dict):
        """Parse address components to extract city, prefecture, district"""
        components = place_data.get('address_components', [])
        
        for component in components:
            types = component.get('types', [])
            
            if 'locality' in types:
                # City
                city_ja = component.get('long_name', '')
                record['city'] = self.city_translations.get(city_ja, city_ja)
            
            elif 'administrative_area_level_1' in types:
                # Prefecture
                record['prefecture'] = component.get('long_name', '')
            
            elif 'sublocality_level_1' in types or 'ward' in types:
                # Ward/District
                record['district'] = component.get('long_name', '')
    
    def _extract_specialties(self, types: List[str]) -> List[str]:
        """Extract medical specialties from Google Place types"""
        medical_type_mapping = {
            'doctor': 'General Medicine',
            'hospital': 'Hospital',
            'dentist': 'Dentistry',
            'physiotherapist': 'Physical Therapy',
            'health': 'Healthcare'
        }
        
        specialties = []
        for place_type in types:
            if place_type in medical_type_mapping:
                specialties.append(medical_type_mapping[place_type])
        
        return specialties or ['Healthcare']
    
    def _analyze_english_proficiency(self, reviews: List[Dict]) -> Dict:
        """Analyze reviews for English language proficiency indicators"""
        english_keywords = [
            'english', 'English', 'ENGLISH', '英語', 'えいご',
            'foreign', 'Foreign', 'international', 'International',
            'interpreter', 'translation', 'bilingual'
        ]
        
        proficiency_score = 0
        review_content = []
        english_mentions = []
        
        for review in reviews:
            text = review.get('text', '')
            review_content.append({
                'text': text,
                'rating': review.get('rating', 0),
                'time': review.get('time', 0)
            })
            
            # Check for English keywords
            for keyword in english_keywords:
                if keyword in text:
                    proficiency_score += 10
                    english_mentions.append(text[:200])
                    break
        
        # Additional scoring based on review patterns
        if len(english_mentions) >= 3:
            proficiency_score += 20
        elif len(english_mentions) >= 2:
            proficiency_score += 10
        
        # Convert to 0-5 scale
        proficiency_level = min(5, proficiency_score // 10)
        
        return {
            'review_content': review_content,
            'proficiency_score': proficiency_level,
            'english_proficiency': self._get_proficiency_label(proficiency_level)
        }
    
    def _get_proficiency_label(self, score: int) -> str:
        """Convert proficiency score to label"""
        labels = {
            0: 'Unknown',
            1: 'Limited',
            2: 'Basic',
            3: 'Conversational',
            4: 'Professional',
            5: 'Fluent'
        }
        return labels.get(score, 'Unknown')
    
    def collect_providers(self, queries: List[str] = None, max_per_query: int = 60, city: str = None) -> Dict[str, Any]:
        """Main collection method with all optimizations
        
        Args:
            queries: List of search queries
            max_per_query: Maximum results per query
            city: City name to set for all collected providers
            
        Returns:
            Collection summary
        """
        summary = {
            'queries_executed': 0,
            'providers_found': 0,
            'providers_collected': 0,
            'duplicates_skipped': 0,
            'rejected_proficiency': 0,
            'api_calls': 0,
            'cache_hits': 0,
            'estimated_cost': 0.0
        }
        
        collected_providers = []
        
        for query in queries:
            # Check daily limit
            if self.daily_limit and summary['providers_collected'] >= self.daily_limit:
                logger.info(f"📊 Daily limit reached: {self.daily_limit}")
                break
            
            # Search providers
            results = self.search_providers(query, max_results=max_per_query)
            summary['queries_executed'] += 1
            summary['providers_found'] += len(results)
            
            for result in results:
                place_id = result.get('place_id')
                if not place_id:
                    continue
                
                # Get details with city-aware deduplication
                details = self.get_place_details(place_id, city=city)
                if not details:
                    summary['duplicates_skipped'] += 1
                    continue
                
                # Create provider record
                record = self.create_provider_record(details, city=city)
                if not record:
                    if details.get('proficiency_score', 0) < 3:
                        summary['rejected_proficiency'] += 1
                    continue
                
                # Save to database
                provider = self.db.create_or_update_provider(record)
                collected_providers.append(provider)
                summary['providers_collected'] += 1
                
                # Check limit
                if self.daily_limit and summary['providers_collected'] >= self.daily_limit:
                    break
        
        # Get final stats
        stats = self.cost_tracker.get_usage_stats(days=1)
        summary['api_calls'] = stats['total_requests']
        summary['cache_hits'] = stats['cache_hits']
        summary['estimated_cost'] = stats['current_day_cost']
        
        logger.info(f"✅ Collection complete: {summary['providers_collected']} providers collected")
        # logger.info(f"💰 Today's cost: ${summary['estimated_cost']:.2f}")  # Cost logging commented out
        
        return summary