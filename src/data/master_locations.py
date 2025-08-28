#!/usr/bin/env python3
"""
Master Location Data Structure for Japan Healthcare Providers
Defines all valid locations for the campaign - NO dynamic creation allowed
"""

# Major cities in Japan (population order)
MAJOR_CITIES = [
    'Tokyo',
    'Yokohama',
    'Osaka',
    'Nagoya',
    'Sapporo',
    'Kobe',
    'Kyoto',
    'Fukuoka',
    'Kawasaki',
    'Saitama',
    'Hiroshima',
    'Sendai',
    'Kitakyushu',
    'Chiba',
    'Sakai',
    'Niigata',
    'Hamamatsu',
    'Kumamoto',
    'Sagamihara',
    'Okayama',
    'Shizuoka',
    'Kagoshima',
    'Funabashi',
    'Hachioji',
    'Matsuyama',
    'Utsunomiya',
    'Matsudo',
    'Nishinomiya'
]

# Tokyo Special Wards (23区) - High priority for English services
TOKYO_SPECIAL_WARDS = [
    'Chiyoda',      # Imperial Palace, government offices
    'Chuo',         # Ginza, Tokyo Station
    'Minato',       # Roppongi, international business
    'Shinjuku',     # Major hub, entertainment
    'Bunkyo',       # Universities, residential
    'Taito',        # Asakusa, Ueno
    'Sumida',       # Skytree area
    'Koto',         # Waterfront development
    'Shinagawa',    # Business, transport hub
    'Meguro',       # Upscale residential
    'Ota',          # Haneda Airport area
    'Setagaya',     # Large residential
    'Shibuya',      # Youth culture, business
    'Nakano',       # Residential, subculture
    'Suginami',     # Residential
    'Toshima',      # Ikebukuro area
    'Kita',         # Northern residential
    'Arakawa',      # Traditional area
    'Itabashi',     # Northwestern residential
    'Nerima',       # Northwestern residential
    'Adachi',       # Northeastern residential
    'Katsushika',   # Traditional eastern
    'Edogawa'       # Eastern residential
]

# International districts with high English-speaking populations
INTERNATIONAL_DISTRICTS = {
    'Tokyo': [
        'Roppongi',      # Embassy area, international nightlife
        'Azabu',         # Embassy area, expat residential
        'Hiroo',         # International schools, expat families
        'Akasaka',       # Business district, embassies
        'Ginza',         # Luxury shopping, international visitors
        'Marunouchi',    # International business district
        'Ebisu',         # International dining, expat friendly
        'Daikanyama',    # Upscale, international boutiques
        'Omotesando',    # Fashion district, international brands
        'Aoyama',        # Fashion and business
        'Meguro',        # Expat residential
        'Shirokane',     # Luxury residential, "Platinum Street"
        'Azabujuban',    # International supermarkets, restaurants
        'Yoyogi',        # Near Meiji Shrine, international area
        'Harajuku'       # Tourist area, youth culture
    ],
    'Yokohama': [
        'Minato Mirai',  # Modern waterfront, international
        'Motomachi',     # Historical foreign settlement
        'Yamate',        # Foreign cemetery, international schools
        'Kannai',        # Business district
        'Bashamichi'     # Historical international trade area
    ],
    'Osaka': [
        'Kita',          # Umeda area, business district
        'Namba',         # Entertainment, shopping
        'Umeda',         # Major transport hub
        'Shinsaibashi',  # Shopping district
        'Kitahama',      # Financial district
        'Honmachi',      # Business district
        'Tennoji',       # Cultural area
        'Nakanoshima'    # Museums, international hotels
    ],
    'Kyoto': [
        'Gion',          # Traditional, tourist area
        'Kawaramachi',   # Shopping, dining
        'Kyoto Station', # Transport hub
        'Arashiyama',    # Tourist area
        'Higashiyama'    # Traditional tourist area
    ],
    'Kobe': [
        'Sannomiya',     # Central business district
        'Kitano',        # Foreign residences (Ijinkan)
        'Harborland',    # Waterfront development
        'Motomachi'      # Chinatown area
    ],
    'Fukuoka': [
        'Tenjin',        # Central business district
        'Hakata',        # Station area, business
        'Nakasu',        # Entertainment district
        'Momochihama',   # Waterfront development
        'Daimyo'         # Trendy area, international restaurants
    ],
    'Nagoya': [
        'Sakae',         # Central business district
        'Meieki',        # Station area
        'Fushimi',       # Business district
        'Osu'            # Shopping district
    ]
}

# Prefectures (for broader searches)
PREFECTURES = [
    'Tokyo',
    'Kanagawa',      # Yokohama, Kawasaki
    'Osaka',
    'Aichi',         # Nagoya
    'Hokkaido',      # Sapporo
    'Hyogo',         # Kobe
    'Kyoto',
    'Fukuoka',
    'Saitama',
    'Chiba',
    'Hiroshima',
    'Miyagi',        # Sendai
    'Shizuoka',
    'Niigata',
    'Kumamoto',
    'Okayama',
    'Kagoshima',
    'Okinawa',       # US military presence
    'Gunma',
    'Tochigi',
    'Ibaraki',
    'Gifu',
    'Nagano',
    'Mie',
    'Shiga',
    'Nara',
    'Wakayama'
]

# Additional areas with significant foreign populations
EXPAT_COMMUNITIES = {
    'US_Military_Bases': [
        'Yokosuka',      # US Navy
        'Yokota',        # US Air Force
        'Zama',          # US Army
        'Sasebo',        # US Navy
        'Misawa',        # US Air Force
        'Iwakuni',       # US Marine Corps
        'Okinawa'        # Multiple bases
    ],
    'International_Schools': [
        'Chofu',         # American School in Japan
        'Yokohama',      # Multiple international schools
        'Kobe',          # Canadian Academy
        'Nagoya',        # International School
        'Kyoto',         # International School
        'Sendai',        # International School
        'Hiroshima',     # International School
        'Fukuoka',       # International School
    ]
}


class LocationValidator:
    """Validates and normalizes location names against master list"""
    
    def __init__(self):
        # Compile all valid locations
        self.valid_cities = set(MAJOR_CITIES)
        self.valid_wards = set(TOKYO_SPECIAL_WARDS)
        self.valid_prefectures = set(PREFECTURES)
        
        # Compile all districts
        self.valid_districts = set()
        for districts in INTERNATIONAL_DISTRICTS.values():
            self.valid_districts.update(districts)
        
        # All valid locations combined
        self.all_valid_locations = (
            self.valid_cities | 
            self.valid_wards | 
            self.valid_prefectures | 
            self.valid_districts
        )
        
        # Create normalization mappings
        self._create_normalization_map()
    
    def _create_normalization_map(self):
        """Create mappings for common variations"""
        self.normalization_map = {
            # Common variations
            'Tokyo Metropolis': 'Tokyo',
            'Tokyo-to': 'Tokyo',
            'Osaka City': 'Osaka',
            'Osaka-shi': 'Osaka',
            'Kyoto City': 'Kyoto',
            'Kyoto-shi': 'Kyoto',
            'Yokohama City': 'Yokohama',
            'Yokohama-shi': 'Yokohama',
            
            # Ward variations
            'Shibuya-ku': 'Shibuya',
            'Shinjuku-ku': 'Shinjuku',
            'Minato-ku': 'Minato',
            'Chiyoda-ku': 'Chiyoda',
            'Chuo-ku': 'Chuo',
            
            # Alternative spellings
            'Roppongi Hills': 'Roppongi',
            'Ginza District': 'Ginza',
            'Harajuku Area': 'Harajuku'
        }
    
    def validate_location(self, location: str) -> bool:
        """
        Check if location is in the master list
        
        Args:
            location: Location name to validate
            
        Returns:
            True if location is valid
        """
        # Normalize the location
        normalized = self.normalize_location(location)
        return normalized in self.all_valid_locations
    
    def normalize_location(self, location: str) -> str:
        """
        Normalize location name to standard form
        
        Args:
            location: Raw location name
            
        Returns:
            Normalized location name
        """
        if not location:
            return ''
        
        # Strip whitespace and normalize case
        location = location.strip()
        
        # Check normalization map first
        if location in self.normalization_map:
            return self.normalization_map[location]
        
        # Check if it's already valid
        if location in self.all_valid_locations:
            return location
        
        # Try title case
        title_case = location.title()
        if title_case in self.all_valid_locations:
            return title_case
        
        # Return original if no match (will fail validation)
        return location
    
    def get_location_type(self, location: str) -> str:
        """
        Determine the type of location
        
        Args:
            location: Normalized location name
            
        Returns:
            Location type: 'city', 'ward', 'prefecture', 'district', or 'unknown'
        """
        if location in self.valid_cities:
            return 'city'
        elif location in self.valid_wards:
            return 'ward'
        elif location in self.valid_prefectures:
            return 'prefecture'
        elif location in self.valid_districts:
            return 'district'
        else:
            return 'unknown'
    
    def get_priority_locations(self, limit: int = 20) -> list:
        """
        Get highest priority locations for English services
        
        Args:
            limit: Maximum number of locations to return
            
        Returns:
            List of priority locations
        """
        priority_locations = []
        
        # Priority 1: Tokyo international districts
        if 'Tokyo' in INTERNATIONAL_DISTRICTS:
            priority_locations.extend(INTERNATIONAL_DISTRICTS['Tokyo'][:5])
        
        # Priority 2: Major Tokyo wards
        priority_locations.extend(['Shibuya', 'Shinjuku', 'Minato', 'Roppongi'])
        
        # Priority 3: Other major cities with international districts
        for city in ['Yokohama', 'Osaka', 'Kyoto', 'Kobe']:
            if city in INTERNATIONAL_DISTRICTS and INTERNATIONAL_DISTRICTS[city]:
                priority_locations.append(INTERNATIONAL_DISTRICTS[city][0])
        
        # Priority 4: US military base areas
        if 'US_Military_Bases' in EXPAT_COMMUNITIES:
            priority_locations.extend(EXPAT_COMMUNITIES['US_Military_Bases'][:3])
        
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for loc in priority_locations:
            if loc not in seen and len(result) < limit:
                seen.add(loc)
                result.append(loc)
        
        return result


# Convenience function
def get_all_valid_locations() -> set:
    """Get all valid locations as a set"""
    validator = LocationValidator()
    return validator.all_valid_locations


def get_english_priority_locations(limit: int = 20) -> list:
    """Get locations with highest English-speaking populations"""
    validator = LocationValidator()
    return validator.get_priority_locations(limit)