#!/usr/bin/env python3
"""
Fix remaining providers without taxonomies
Based on screenshots showing providers published on 08/24 and 08/25 without taxonomies
"""

import sys
import os
import logging
import time
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.publishers.wordpress import WordPressPublisher
from sqlalchemy import text
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_providers_without_taxonomies(db):
    """Find providers that likely don't have taxonomies based on name patterns from screenshots"""
    
    # Names from the screenshots that are missing taxonomies
    provider_names_missing_tax = [
        'Shinjuku Higashiguchi Clinic',
        'Shinjuku Ekimae Buratoshikashinjukueki Dental Clinic',
        '千葉デンタルクリニック 新宿駅東口医院',  # Chiba Dental Clinic
        'Kim Clinic',
        'Aiiku Hospital',
        'Yanagawa Clinic',
        'Shirokanesanko Clinic',
        'とようら小児科',  # Toyoura Pediatrics
        'Tokyo Tower View Clinic Azabujuban',
        'Nakamura Azabujuban Clinic',
        'Flow East Clinic',
        'Ito Hospital',
        'Minato Medical Clinics',
        'Well – Being Dental Clinic',
        'Well - Being Dental Clinic',  # Try with regular hyphen
        'Well-Being Dental Clinic',  # Try without spaces
        'Akasaka Hiro Dental',
        'Clinic for Shinbashi',
        'Le Coquelicot Health and Beauty Clinic',
        # Also check these based on the screenshot pattern
        '千葉デンタル',  # Partial match for Chiba Dental
        'Chiba Dental'  # English version
    ]
    
    session = db.get_session()
    
    try:
        # Query for these specific providers
        providers = []
        
        for name in provider_names_missing_tax:
            # Try exact match first
            query = """
                SELECT id, provider_name, city, district, specialties, 
                       wordpress_post_id, content_hash
                FROM providers 
                WHERE wordpress_post_id IS NOT NULL
                AND (provider_name = :name OR provider_name ILIKE :pattern)
                LIMIT 1
            """
            
            result = session.execute(text(query), {
                'name': name,
                'pattern': f'%{name}%'
            }).first()
            
            if result:
                class ProviderData:
                    def __init__(self, row):
                        self.id = row[0]
                        self.provider_name = row[1]
                        self.city = row[2]
                        self.district = row[3]
                        self.specialties = row[4]
                        self.wordpress_post_id = row[5]
                        self.content_hash = row[6]
                        # Parse provider type from name
                        name_lower = row[1].lower()
                        if 'hospital' in name_lower:
                            self.provider_type = 'hospital'
                        elif 'clinic' in name_lower:
                            self.provider_type = 'clinic'
                        elif 'dental' in name_lower or 'dentist' in name_lower:
                            self.provider_type = 'dentist'
                        elif 'pharmacy' in name_lower:
                            self.provider_type = 'pharmacy'
                        else:
                            self.provider_type = None
                
                providers.append(ProviderData(result))
                logger.info(f"Found: {result.provider_name} (Post ID: {result.wordpress_post_id})")
            else:
                logger.warning(f"Not found in database: {name}")
        
        # Skip the recent query since we found most of them already
        # The providers from the screenshots have been identified
        
        return providers
        
    finally:
        session.close()


def update_provider_taxonomies(publisher: WordPressPublisher, provider) -> bool:
    """Update taxonomies for a single provider"""
    
    try:
        # Get taxonomy term IDs
        taxonomies = publisher._get_taxonomies(provider)
        
        if not taxonomies:
            logger.warning(f"   No taxonomies could be determined for {provider.provider_name}")
            # Try to at least set basic taxonomies based on name
            taxonomies = {}
            
            # Set location if we have city
            if provider.city:
                # Force creating basic location taxonomy
                taxonomies['location'] = []
                city_term = publisher._get_or_create_term(provider.city, 'location')
                if city_term:
                    taxonomies['location'].append(city_term)
            
            # Set specialty based on provider type or name
            taxonomies['specialties'] = []
            name_lower = provider.provider_name.lower()
            
            if 'dental' in name_lower or 'dentist' in name_lower:
                term = publisher._get_or_create_term('Dentistry', 'specialties')
                if term:
                    taxonomies['specialties'].append(term)
            elif 'hospital' in name_lower:
                term = publisher._get_or_create_term('Hospital', 'specialties')
                if term:
                    taxonomies['specialties'].append(term)
            elif 'clinic' in name_lower:
                term = publisher._get_or_create_term('Clinic', 'specialties')
                if term:
                    taxonomies['specialties'].append(term)
            else:
                # Default to General Medicine
                term = publisher._get_or_create_term('General Medicine', 'specialties')
                if term:
                    taxonomies['specialties'].append(term)
        
        if not taxonomies:
            logger.error(f"   Could not create any taxonomies for {provider.provider_name}")
            return False
        
        logger.info(f"   Taxonomies to set: {taxonomies}")
        
        # Make API request to update taxonomies
        response = requests.post(
            f"{publisher.wp_url}/wp-json/wp/v2/healthcare_provider/{provider.wordpress_post_id}",
            auth=(publisher.wp_username, publisher.wp_password),
            json=taxonomies,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Updated {provider.provider_name}")
            if 'location' in taxonomies and taxonomies['location']:
                logger.info(f"   Location set: {provider.city}, {provider.district}")
            if 'specialties' in taxonomies and taxonomies['specialties']:
                logger.info(f"   Specialties set: {provider.specialties or 'Based on name'}")
            return True
        elif response.status_code == 404:
            logger.warning(f"⚠️  Post {provider.wordpress_post_id} not found for {provider.provider_name}")
            return False
        else:
            logger.error(f"❌ Failed {provider.provider_name}: {response.status_code}")
            logger.error(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


def main():
    """Main execution"""
    
    # Initialize services
    db = DatabaseManager()
    publisher = WordPressPublisher()
    
    logger.info("="*60)
    logger.info("🔧 FIXING REMAINING PROVIDERS WITHOUT TAXONOMIES")
    logger.info("="*60)
    
    # Find providers without taxonomies
    providers = find_providers_without_taxonomies(db)
    
    if not providers:
        logger.info("No providers found that need taxonomy updates")
        return 0
    
    logger.info(f"\nFound {len(providers)} providers to check/update")
    logger.info("-"*60)
    
    # Update each provider
    success_count = 0
    failed_count = 0
    
    for i, provider in enumerate(providers, 1):
        logger.info(f"\n[{i}/{len(providers)}] {provider.provider_name} (Post {provider.wordpress_post_id})")
        
        success = update_provider_taxonomies(publisher, provider)
        
        if success:
            success_count += 1
        else:
            failed_count += 1
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.3)
    
    # Final summary
    logger.info("\n" + "="*60)
    logger.info("✅ TAXONOMY UPDATE COMPLETE")
    logger.info(f"   Total processed: {len(providers)}")
    logger.info(f"   Successfully updated: {success_count}")
    if failed_count > 0:
        logger.info(f"   Failed/Not found: {failed_count}")
    logger.info("="*60)
    
    # Show WordPress admin URL
    if success_count > 0:
        logger.info("\n📌 Check results in WordPress:")
        logger.info("   https://kantanhealth.jp/wp-admin/edit.php?post_type=healthcare_provider")
        logger.info("   All providers should now have Location and Specialties values")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())