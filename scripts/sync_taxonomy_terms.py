#!/usr/bin/env python3
"""
Sync WordPress Taxonomy Terms (Location and Specialty) with SEO Content
Generates SEO content for taxonomy archive pages
Can be run regularly as new terms are added
"""

import os
import sys
import json
import time
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.generate_taxonomy_content_updated import TaxonomyContentGenerator
from src.core.database import DatabaseManager
from sqlalchemy import text
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv('config/.env')


class TaxonomyTermSyncer:
    """Syncs WordPress taxonomy terms with SEO content"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.generator = TaxonomyContentGenerator()
        
        # WordPress credentials
        self.wp_url = os.getenv('WORDPRESS_URL')
        self.wp_user = os.getenv('WORDPRESS_USERNAME')
        self.wp_pass = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        
        if not all([self.wp_url, self.wp_user, self.wp_pass]):
            raise ValueError("WordPress credentials not found in environment")
    
    def fetch_taxonomy_terms(self, taxonomy: str) -> List[Dict]:
        """Fetch all terms for a given taxonomy from WordPress"""
        
        all_terms = []
        endpoint = f"{self.wp_url}/wp-json/wp/v2/{taxonomy}"
        
        logger.info(f"📥 Fetching {taxonomy} terms from WordPress...")
        
        try:
            page = 1
            per_page = 100
            
            while True:
                response = requests.get(
                    endpoint,
                    auth=(self.wp_user, self.wp_pass),
                    params={'per_page': per_page, 'page': page, 'hide_empty': False},
                    timeout=30
                )
                
                if response.status_code == 200:
                    terms = response.json()
                    if not terms:
                        break
                    
                    for term in terms:
                        all_terms.append({
                            'id': term['id'],
                            'name': term['name'],
                            'slug': term['slug'],
                            'description': term.get('description', ''),
                            'count': term.get('count', 0),
                            'taxonomy': taxonomy
                        })
                    
                    page += 1
                else:
                    break
            
            logger.info(f"✅ Found {len(all_terms)} {taxonomy} terms")
            return all_terms
            
        except Exception as e:
            logger.error(f"Error fetching {taxonomy}: {e}")
            return []
    
    def check_existing_term_content(self, terms: List[Dict], taxonomy_type: str) -> tuple:
        """Check which terms already have SEO content"""
        
        session = self.db.get_session()
        try:
            # Get existing term content
            result = session.execute(text("""
                SELECT DISTINCT 
                    CASE 
                        WHEN :type = 'location' THEN location
                        WHEN :type = 'specialty' THEN specialty
                    END as term_name,
                    wp_term_id
                FROM taxonomy_term_content
                WHERE taxonomy_type = :type
            """), {'type': taxonomy_type}).fetchall()
            
            existing = {row[0]: row[1] for row in result if row[0]}
            
            has_content = []
            needs_content = []
            
            for term in terms:
                if term['name'] in existing:
                    has_content.append(term)
                else:
                    needs_content.append(term)
            
            return has_content, needs_content
            
        finally:
            session.close()
    
    def generate_term_content(self, terms: List[Dict], taxonomy_type: str) -> List[Dict]:
        """Generate SEO content for taxonomy terms"""
        
        content_list = []
        
        for term in terms:
            if taxonomy_type == 'location':
                prompt = f"""Generate content for a location taxonomy archive page.

Location: {term['name']}

GUIDELINES:
- Write in a natural, informative tone for expats in Japan
- Keep it to ONE paragraph (60-80 words)
- Focus on practical information about healthcare in this location
- Don't mention specific provider counts
- No promotional language or calls-to-action
- Mention areas, access, and general availability of English support

Create:
1. SEO TITLE: (60 chars max, format: "English Healthcare in [Location]")
2. META DESCRIPTION: (155 chars max)
3. DESCRIPTION: (ONE paragraph, 60-80 words for WordPress taxonomy description)

Return in this format:
TITLE: [title]
META: [meta description]
DESCRIPTION: [single paragraph]"""
            else:  # specialty
                prompt = f"""Generate content for a specialty taxonomy archive page.

Specialty: {term['name']}

GUIDELINES:
- Keep it to ONE paragraph (40-50 words)
- Explain what's unique about this specialty in Japan (different approaches, what to expect)
- State that listed providers have verified English support
- Don't mention specific provider counts
- No promotional language or sales speak
- Factual and informative

Create:
1. SEO TITLE: (Simple, like "English-Speaking {term['name']} in Japan")
2. META DESCRIPTION: (Simple, 100-120 chars max)
3. DESCRIPTION: (ONE paragraph, 40-50 words)

Return in this format:
TITLE: [title]
META: [meta description]
DESCRIPTION: [single paragraph]"""

            try:
                response = self.generator.client.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=2000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                content_text = response.content[0].text
                
                # Parse response - simpler format now
                title = self._extract_section(content_text, "TITLE:", "META:").strip()
                meta_desc = self._extract_section(content_text, "META:", "DESCRIPTION:").strip()
                description = self._extract_section(content_text, "DESCRIPTION:", "END").strip()
                
                if not description:
                    description = content_text.split("DESCRIPTION:")[-1].strip()
                
                content_list.append({
                    'taxonomy_type': taxonomy_type,
                    'term_id': term['id'],
                    'term_name': term['name'],
                    'term_slug': term['slug'],
                    'title': title or f"English Healthcare in {term['name']}" if taxonomy_type == 'location' else f"English-Speaking {term['name']} in Japan",
                    'meta_description': meta_desc or f"Find English-speaking healthcare in {term['name']}" if taxonomy_type == 'location' else f"{term['name']} in Japan with English support",
                    'archive_description': description or "Healthcare providers with verified English language support.",
                    'provider_count': term['count']
                })
                
                logger.info(f"✅ Generated content for {term['name']}")
                
            except Exception as e:
                logger.error(f"Error generating content for {term['name']}: {e}")
                continue
        
        return content_list
    
    def _extract_section(self, text: str, start: str, end: str) -> str:
        """Extract text between markers"""
        if start in text:
            text = text.split(start)[1]
            if end in text:
                text = text.split(end)[0]
        return text.strip()
    
    def save_term_content(self, content_list: List[Dict]):
        """Save taxonomy term content to database"""
        
        session = self.db.get_session()
        try:
            # Create table if needed
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS taxonomy_term_content (
                    id SERIAL PRIMARY KEY,
                    taxonomy_type VARCHAR(20),
                    wp_term_id INTEGER,
                    location VARCHAR(100),
                    specialty VARCHAR(100),
                    term_slug VARCHAR(200),
                    title VARCHAR(200),
                    meta_description TEXT,
                    archive_intro TEXT,
                    archive_description TEXT,
                    provider_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(taxonomy_type, wp_term_id)
                )
            """))
            session.commit()
            
            for content in content_list:
                # Set location or specialty based on type
                location = content['term_name'] if content['taxonomy_type'] == 'location' else None
                specialty = content['term_name'] if content['taxonomy_type'] == 'specialty' else None
                
                session.execute(text("""
                    INSERT INTO taxonomy_term_content
                    (taxonomy_type, wp_term_id, location, specialty, term_slug,
                     title, meta_description, archive_description, provider_count)
                    VALUES
                    (:type, :term_id, :location, :specialty, :slug,
                     :title, :meta, :description, :count)
                    ON CONFLICT (taxonomy_type, wp_term_id) 
                    DO UPDATE SET
                        title = EXCLUDED.title,
                        meta_description = EXCLUDED.meta_description,
                        archive_description = EXCLUDED.archive_description,
                        provider_count = EXCLUDED.provider_count,
                        updated_at = CURRENT_TIMESTAMP
                """), {
                    'type': content['taxonomy_type'],
                    'term_id': content['term_id'],
                    'location': location,
                    'specialty': specialty,
                    'slug': content['term_slug'],
                    'title': content['title'],
                    'meta': content['meta_description'],
                    'description': content['archive_description'],
                    'count': content['provider_count']
                })
            
            session.commit()
            logger.info(f"✅ Saved {len(content_list)} term content items to database")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving content: {e}")
        finally:
            session.close()
    
    def update_wordpress_term(self, term_id: int, content: Dict, taxonomy: str) -> bool:
        """Update WordPress term with SEO content via REST API"""
        
        endpoint = f"{self.wp_url}/wp-json/wp/v2/{taxonomy}/{term_id}"
        
        # WordPress terms have limited fields we can update via REST API
        # Usually just description - SEO fields need custom implementation
        data = {
            'description': content['archive_description'],
            # These would need custom REST fields registered in WordPress
            'meta': {
                'seo_title': content['title'],
                'seo_description': content['meta_description'],
                'archive_intro': content['archive_intro']
            }
        }
        
        try:
            response = requests.post(
                endpoint,
                auth=(self.wp_user, self.wp_pass),
                json=data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Updated term {content['term_name']}")
                return True
            else:
                logger.warning(f"⚠️  Could not update term via REST API (may need custom fields)")
                return False
                
        except Exception as e:
            logger.error(f"Error updating term: {e}")
            return False
    
    def sync_all(self, update_wordpress: bool = False):
        """Main sync process for all taxonomy terms"""
        
        logger.info("=" * 60)
        logger.info("TAXONOMY TERM SEO CONTENT SYNC")
        logger.info("=" * 60)
        
        # Process location taxonomy
        logger.info("\n📍 Processing LOCATION taxonomy...")
        location_terms = self.fetch_taxonomy_terms('location')
        
        if location_terms:
            has_content, needs_content = self.check_existing_term_content(location_terms, 'location')
            logger.info(f"   Already have content: {len(has_content)}")
            logger.info(f"   Need content: {len(needs_content)}")
            
            if needs_content:
                logger.info(f"   Generating content for {len(needs_content)} locations...")
                location_content = self.generate_term_content(needs_content, 'location')
                if location_content:
                    self.save_term_content(location_content)
                    
                    if update_wordpress:
                        for content in location_content:
                            self.update_wordpress_term(content['term_id'], content, 'location')
        
        # Process specialty taxonomy
        logger.info("\n🏥 Processing SPECIALTY taxonomy...")
        specialty_terms = self.fetch_taxonomy_terms('specialties')
        
        if specialty_terms:
            has_content, needs_content = self.check_existing_term_content(specialty_terms, 'specialty')
            logger.info(f"   Already have content: {len(has_content)}")
            logger.info(f"   Need content: {len(needs_content)}")
            
            if needs_content:
                logger.info(f"   Generating content for {len(needs_content)} specialties...")
                specialty_content = self.generate_term_content(needs_content, 'specialty')
                if specialty_content:
                    self.save_term_content(specialty_content)
                    
                    if update_wordpress:
                        for content in specialty_content:
                            self.update_wordpress_term(content['term_id'], content, 'specialties')
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ SYNC COMPLETE")
        logger.info("=" * 60)
        
        # Show how to use the data
        logger.info("\n📋 To use this content in WordPress:")
        logger.info("1. Create a custom plugin to display term meta on archive pages")
        logger.info("2. Or export the content and manually add to term descriptions")
        logger.info("3. Or use a WordPress REST API extension to accept meta fields")
        
        # Generate export if needed
        self.export_for_wordpress()
    
    def export_for_wordpress(self):
        """Export term content for manual WordPress import"""
        
        session = self.db.get_session()
        try:
            result = session.execute(text("""
                SELECT 
                    taxonomy_type,
                    wp_term_id,
                    location,
                    specialty,
                    term_slug,
                    title,
                    meta_description,
                    archive_intro,
                    archive_description
                FROM taxonomy_term_content
                ORDER BY taxonomy_type, location, specialty
            """)).fetchall()
            
            if result:
                with open('taxonomy_term_content_export.json', 'w') as f:
                    export_data = []
                    for row in result:
                        export_data.append({
                            'taxonomy_type': row[0],
                            'term_id': row[1],
                            'location': row[2],
                            'specialty': row[3],
                            'slug': row[4],
                            'seo_title': row[5],
                            'meta_description': row[6],
                            'archive_intro': row[7],
                            'archive_description': row[8]
                        })
                    json.dump(export_data, f, indent=2)
                
                logger.info(f"📁 Exported {len(export_data)} term content items to taxonomy_term_content_export.json")
                
        finally:
            session.close()


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync WordPress taxonomy terms with SEO content')
    parser.add_argument('--update-wp', action='store_true',
                       help='Update WordPress terms via REST API (if supported)')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check status without generating')
    
    args = parser.parse_args()
    
    syncer = TaxonomyTermSyncer()
    
    if args.check_only:
        # Just check status
        logger.info("📊 Checking taxonomy term status...")
        
        location_terms = syncer.fetch_taxonomy_terms('location')
        specialty_terms = syncer.fetch_taxonomy_terms('specialties')
        
        has_loc, needs_loc = syncer.check_existing_term_content(location_terms, 'location')
        has_spec, needs_spec = syncer.check_existing_term_content(specialty_terms, 'specialty')
        
        logger.info("\n📍 LOCATIONS:")
        logger.info(f"   Total: {len(location_terms)}")
        logger.info(f"   Have content: {len(has_loc)}")
        logger.info(f"   Need content: {len(needs_loc)}")
        
        logger.info("\n🏥 SPECIALTIES:")
        logger.info(f"   Total: {len(specialty_terms)}")
        logger.info(f"   Have content: {len(has_spec)}")
        logger.info(f"   Need content: {len(needs_spec)}")
        
        if needs_loc:
            logger.info("\nLocations needing content:")
            for term in needs_loc[:10]:
                logger.info(f"   - {term['name']} ({term['count']} providers)")
        
        if needs_spec:
            logger.info("\nSpecialties needing content:")
            for term in needs_spec[:10]:
                logger.info(f"   - {term['name']} ({term['count']} providers)")
    else:
        # Run full sync
        syncer.sync_all(update_wordpress=args.update_wp)


if __name__ == "__main__":
    main()