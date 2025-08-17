#!/usr/bin/env python3
"""
Fix Missing Location Data for Providers
Identifies providers with missing city data and attempts to fix them
"""

import os
import sys
import re
import logging
from typing import Optional, Dict, List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.collectors.google_places import GooglePlacesCollector
from sqlalchemy import text
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment
load_dotenv('config/.env')


class LocationFixer:
    """Fix missing location data for providers"""
    
    # Common Tokyo wards and areas
    TOKYO_WARDS = [
        "Chiyoda", "Chuo", "Minato", "Shinjuku", "Bunkyo", "Taito", 
        "Sumida", "Koto", "Shinagawa", "Meguro", "Ota", "Setagaya", 
        "Shibuya", "Nakano", "Suginami", "Toshima", "Kita", "Arakawa", 
        "Itabashi", "Nerima", "Adachi", "Katsushika", "Edogawa"
    ]
    
    # Common Japanese cities
    MAJOR_CITIES = [
        "Tokyo", "Yokohama", "Osaka", "Nagoya", "Sapporo", "Kobe", 
        "Kyoto", "Fukuoka", "Kawasaki", "Saitama", "Sendai", "Hiroshima"
    ]
    
    def __init__(self):
        """Initialize the location fixer"""
        self.db = DatabaseManager()
        self.google_places = GooglePlacesCollector()
        self.fixed_count = 0
        self.failed_count = 0
        
    def get_providers_with_missing_location(self) -> List[Dict]:
        """Get all providers with missing city data"""
        session = self.db.get_session()
        try:
            result = session.execute(text("""
                SELECT id, provider_name, address, district
                FROM providers
                WHERE city IS NULL OR city = ''
                ORDER BY id
            """)).fetchall()
            
            providers = []
            for row in result:
                providers.append({
                    'id': row[0],
                    'provider_name': row[1],
                    'address': row[2],
                    'district': row[3]
                })
            
            return providers
            
        finally:
            session.close()
    
    def extract_city_from_address(self, address: str) -> Optional[str]:
        """Try to extract city from address string"""
        if not address:
            return None
        
        # Check for Tokyo wards
        for ward in self.TOKYO_WARDS:
            if ward in address:
                logger.info(f"  Found Tokyo ward: {ward}")
                return "Tokyo"
        
        # Check for major cities
        for city in self.MAJOR_CITIES:
            if city in address:
                logger.info(f"  Found city: {city}")
                return city
        
        # Check for Japanese patterns (e.g., "東京都" for Tokyo)
        if "東京都" in address or "Tokyo-to" in address:
            return "Tokyo"
        elif "大阪" in address or "Osaka" in address:
            return "Osaka"
        elif "横浜" in address or "Yokohama" in address:
            return "Yokohama"
        elif "京都" in address or "Kyoto" in address:
            return "Kyoto"
        elif "福岡" in address or "Fukuoka" in address:
            return "Fukuoka"
        elif "神戸" in address or "Kobe" in address:
            return "Kobe"
        elif "名古屋" in address or "Nagoya" in address:
            return "Nagoya"
        elif "札幌" in address or "Sapporo" in address:
            return "Sapporo"
        elif "仙台" in address or "Sendai" in address:
            return "Sendai"
        
        return None
    
    def extract_ward_from_address(self, address: str) -> Optional[str]:
        """Try to extract ward from address string"""
        if not address:
            return None
        
        # Check for Tokyo wards
        for ward in self.TOKYO_WARDS:
            if ward in address:
                return ward
        
        # Check for ward patterns with Japanese
        ward_pattern = r'([A-Za-z]+)[-\s]?(ku|区)'
        match = re.search(ward_pattern, address)
        if match:
            return match.group(1)
        
        return None
    
    def fix_from_google_api(self, provider: Dict) -> Optional[Dict]:
        """Use Google Places API to get correct location data"""
        # This would require searching by name/address since we don't have place_id
        # For now, return None as we can't use the API without place_id
        return None
    
    def update_provider_location(self, provider_id: int, city: str, ward: Optional[str] = None) -> bool:
        """Update provider's location in database"""
        session = self.db.get_session()
        try:
            session.execute(text("""
                UPDATE providers
                SET city = :city, ward = :ward
                WHERE id = :provider_id
            """), {
                'provider_id': provider_id,
                'city': city,
                'ward': ward
            })
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"  Error updating database: {str(e)}")
            return False
            
        finally:
            session.close()
    
    def fix_all_missing_locations(self, use_api: bool = False):
        """Fix all providers with missing location data"""
        
        providers = self.get_providers_with_missing_location()
        
        print(f"\n📍 Found {len(providers)} providers with missing location data")
        print("=" * 60)
        
        for i, provider in enumerate(providers, 1):
            print(f"\n[{i}/{len(providers)}] Provider: {provider['provider_name']}")
            print(f"  Address: {provider['address']}")
            
            # First try to extract from address
            city = self.extract_city_from_address(provider['address'])
            ward = self.extract_ward_from_address(provider['address'])
            
            if city:
                print(f"  ✅ Extracted city: {city}" + (f", ward: {ward}" if ward else ""))
                
                if self.update_provider_location(provider['id'], city, ward):
                    self.fixed_count += 1
                    print(f"  ✅ Updated in database")
                else:
                    self.failed_count += 1
                    print(f"  ❌ Failed to update database")
                    
            elif use_api:
                # Try Google API if extraction failed (currently disabled without place_id)
                print(f"  ⚠️ Google API lookup not available without place_id field")
                self.failed_count += 1
            else:
                print(f"  ❌ Could not determine location")
                self.failed_count += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY:")
        print(f"  ✅ Fixed: {self.fixed_count} providers")
        print(f"  ❌ Failed: {self.failed_count} providers")
        print(f"  📍 Total processed: {len(providers)} providers")
        
        if self.failed_count > 0:
            print(f"\n💡 TIP: Run with --use-api flag to use Google Places API for failed providers")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix missing location data for providers')
    parser.add_argument('--use-api', action='store_true', 
                       help='Use Google Places API for providers that cannot be fixed from address')
    parser.add_argument('--limit', type=int, 
                       help='Limit number of providers to process')
    
    args = parser.parse_args()
    
    fixer = LocationFixer()
    
    # If limit specified, only process that many
    if args.limit:
        providers = fixer.get_providers_with_missing_location()[:args.limit]
        print(f"Processing first {args.limit} providers...")
    
    fixer.fix_all_missing_locations(use_api=args.use_api)


if __name__ == "__main__":
    main()