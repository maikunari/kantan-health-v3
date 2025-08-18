#!/usr/bin/env python3
"""
SEO Taxonomy Content Generator - UPDATED VERSION
Generates AI-powered content for location, specialty, and combination taxonomy pages
Uses mega-batch processing for efficiency and implements 70/30 unique/template hybrid approach
"""

import os
import sys
import json
import time
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import DatabaseManager
from src.processors.ai_content import AIContentProcessor
from src.core.cost_tracker import CostTracker
from sqlalchemy import text
import anthropic

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class TaxonomyContent:
    """Represents content for a taxonomy page"""
    taxonomy_type: str  # 'location', 'specialty', or 'combination'
    title: str
    meta_description: str
    brief_intro: str
    full_description: str
    location: str
    specialty: Optional[str] = None
    ward: Optional[str] = None
    provider_count: int = 0
    priority_tier: int = 0


class TaxonomyContentGenerator:
    """
    Generates SEO-optimized content for taxonomy pages using Claude AI.
    Implements mega-batch processing and 70/30 unique/template hybrid approach.
    """
    
    # Template elements (30% of content) - Updated to be more natural
    TEMPLATE_SECTIONS = {
        "insurance": """
<h2>Insurance and Payment</h2>
<p>Healthcare providers in this area accept various insurance plans, including Japanese National Health Insurance and many international insurance policies. Having comprehensive health insurance ensures you can access quality care whenever needed, from routine checkups to specialized treatments. Multiple payment options are available for your convenience, including credit cards and digital payments. The clinic staff can help verify your insurance coverage and explain your benefits when you book your appointment.</p>
        """,
        
        "appointment": """
<h2>Booking Your Appointment</h2>
<p>Appointments can be made by phone, online, or walk-in depending on the clinic. Many facilities offer same-day appointments for urgent care. English-speaking staff are available to assist with booking and paperwork. Online booking systems are becoming more common, making it easier for international patients to schedule visits.</p>
        """,
        
        "accessibility": """
<h2>Getting There</h2>
<p>Most clinics are located within walking distance of major train stations. Building signage often includes English, and reception staff can provide directions by phone. Consider saving the clinic's address in Japanese on your phone for taxi drivers who may not speak English.</p>
        """
    }
    
    def __init__(self):
        """Initialize the content generator"""
        self.db = DatabaseManager()
        self.cost_tracker = CostTracker()
        
        # Initialize Claude client
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        
        self.generated_count = 0
        self.total_cost = 0.0
        
        logger.info("✅ Taxonomy content generator initialized")
    
    def generate_mega_batch(self, items: List[Tuple], batch_size: int = 5) -> List[TaxonomyContent]:
        """
        Generate multiple content pieces in a single API call for efficiency.
        
        Args:
            items: List of tuples (type, location, specialty, ward, count)
            batch_size: Number of items to process in one API call
            
        Returns:
            List of TaxonomyContent objects
        """
        if not items:
            return []
        
        # Create a refined mega prompt
        mega_prompt = """Generate content for multiple healthcare directory taxonomy pages.
Write in a natural, informative tone - like a helpful guide for expats in Japan.
Focus on practical information that residents actually need.

IMPORTANT GUIDELINES:
- Brief intro: Start with "Find trusted English-speaking [specialty] in [location]..."
- Mention that all listed providers have verified English language support
- Use HTML formatting for full descriptions with <h2> headers
- Include practical details about train access and what to expect
- Avoid sales language and marketing fluff
- NEVER use exact numbers like "8+", "12+" etc. Use "multiple", "several", or "various" instead
- Do NOT mention specific provider counts anywhere
- NO call-to-action at the end (no "browse providers below")
- Content should be 70% unique to each location/specialty, 30% can be template

INSURANCE SECTION GUIDELINES:
- Keep the Insurance and Payment section general and positive
- Mention that providers accept "various insurance plans including Japanese National Health Insurance and international insurance"
- Say "multiple payment options are available" and "staff can help verify coverage"
- DO NOT mention: specific costs, upfront payments, reimbursement processes, additional fees, or any complications
- Make insurance sound valuable and accessible, not complicated

PAGES TO GENERATE:
"""
        
        for i, item in enumerate(items[:batch_size], 1):
            content_type, location, specialty, ward, count = item
            
            if content_type == "combination":
                full_location = f"{ward}, {location}" if ward else location
                mega_prompt += f"""

PAGE {i}: {specialty} in {full_location}
Create content including:
- Brief intro (2-3 sentences)
- Full description with these H2 sections:
  * Finding English-Speaking {specialty} in {full_location}
  * What to Expect at {specialty} Clinics in Japan
  * Location and Accessibility (mention actual train lines/stations)
  * Insurance and Payment
"""
            elif content_type == "location":
                full_location = f"{ward}, {location}" if ward else location
                mega_prompt += f"""

PAGE {i}: Healthcare in {full_location}
Create content for a location overview page
"""
            else:  # specialty
                mega_prompt += f"""

PAGE {i}: {specialty} Specialists in Japan
Create content for a specialty overview page
"""
        
        mega_prompt += """

For EACH page, provide content in this format:

PAGE [number]:
TITLE: [Simple format: "English [Specialty] in [Location]" - keep it under 60 chars]
META: [meta description, 155 chars max]
BRIEF_INTRO:
[2-3 sentences starting with "Find trusted English-speaking..."]

FULL_DESCRIPTION:
[HTML formatted content with H2 headers as specified]

---

Make each page unique with specific local details and practical information.
"""
        
        # Generate all content in one API call
        try:
            logger.info(f"🚀 Generating mega-batch of {len(items[:batch_size])} content pieces...")
            
            response = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",  # Claude 3.7 Sonnet for best quality
                max_tokens=8000,  # Increased for comprehensive SEO content
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": mega_prompt
                }]
            )
            
            content_text = response.content[0].text
            
            # Parse the response for each page
            results = []
            pages = content_text.split("PAGE ")
            
            for i, item in enumerate(items[:batch_size]):
                content_type, location, specialty, ward, count = item
                
                # Find the corresponding page content
                page_content = ""
                for page in pages:
                    if page.startswith(f"{i+1}:"):
                        page_content = page
                        break
                
                # Extract content sections
                title = self._extract_section(page_content, "TITLE:", "META:")
                meta_desc = self._extract_section(page_content, "META:", "BRIEF_INTRO:")
                brief_intro = self._extract_section(page_content, "BRIEF_INTRO:", "FULL_DESCRIPTION:")
                full_desc = self._extract_section(page_content, "FULL_DESCRIPTION:", "---")
                
                # Create TaxonomyContent object
                if content_type == "combination":
                    priority_tier = 1 if count >= 5 else 2
                else:
                    priority_tier = 3
                
                results.append(TaxonomyContent(
                    taxonomy_type=content_type,
                    title=title or f"English {specialty} in {location}" if specialty else f"Healthcare in {location}",
                    meta_description=meta_desc or f"Find English-speaking {specialty} in {location}" if specialty else f"English healthcare in {location}",
                    brief_intro=brief_intro or f"Find trusted English-speaking {specialty} in {location}." if specialty else f"Find healthcare in {location}.",
                    full_description=full_desc or "<p>Quality healthcare services available.</p>",
                    location=location,
                    specialty=specialty,
                    ward=ward,
                    provider_count=count,
                    priority_tier=priority_tier
                ))
            
            self.generated_count += len(results)
            logger.info(f"✅ Generated {len(results)} content pieces (Total: {self.generated_count})")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in mega-batch generation: {str(e)}")
            # Fall back to individual generation
            return [self._generate_individual(item) for item in items[:batch_size]]
    
    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> str:
        """Extract a section of text between markers"""
        if start_marker in text:
            start = text.index(start_marker) + len(start_marker)
            if end_marker in text[start:]:
                end = text.index(end_marker, start)
                return text[start:end].strip()
            else:
                return text[start:].strip()
        return ""
    
    def _generate_individual(self, item: Tuple) -> TaxonomyContent:
        """Generate content for a single item with refined prompt"""
        content_type, location, specialty, ward, count = item
        
        full_location = f"{ward}, {location}" if ward else location
        
        if content_type == "combination":
            prompt = f"""Generate content for a healthcare directory page about {specialty} in {full_location}.

Write in a natural, informative tone. Focus on practical information.

Create:
1. BRIEF INTRO: Start with "Find trusted English-speaking {specialty} in {full_location}..." (2-3 sentences)
2. FULL DESCRIPTION with HTML formatting:
   <h2>Finding English-Speaking {specialty} in {full_location}</h2>
   <h2>What to Expect at {specialty} Clinics in Japan</h2>
   <h2>Location and Accessibility</h2>
   <h2>Insurance and Payment</h2>

Return sections marked as:
TITLE:
META:
BRIEF_INTRO:
FULL_DESCRIPTION:"""
        else:
            prompt = f"Generate content for {content_type} page: {location or specialty}"
        
        try:
            response = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",  # Claude 3.7 Sonnet
                max_tokens=4000,  # Increased for richer individual content
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content_text = response.content[0].text
            
            return TaxonomyContent(
                taxonomy_type=content_type,
                title=self._extract_section(content_text, "TITLE:", "META:") or f"Healthcare in {full_location}",
                meta_description=self._extract_section(content_text, "META:", "BRIEF_INTRO:") or f"Find healthcare in {full_location}",
                brief_intro=self._extract_section(content_text, "BRIEF_INTRO:", "FULL_DESCRIPTION:"),
                full_description=self._extract_section(content_text, "FULL_DESCRIPTION:", "END") or content_text,
                location=location,
                specialty=specialty,
                ward=ward,
                provider_count=count,
                priority_tier=1 if count >= 5 else 2
            )
        except Exception as e:
            logger.error(f"Error generating individual content: {e}")
            return TaxonomyContent(
                taxonomy_type=content_type,
                title=f"Healthcare in {full_location}",
                meta_description=f"Find healthcare in {full_location}",
                brief_intro=f"Find healthcare providers in {full_location}.",
                full_description="<p>Healthcare services available.</p>",
                location=location,
                specialty=specialty,
                ward=ward,
                provider_count=count,
                priority_tier=2
            )
    
    def save_content(self, content_list: List[TaxonomyContent]):
        """Save generated content to database"""
        session = self.db.get_session()
        try:
            # Create table if needed
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS taxonomy_content (
                    id SERIAL PRIMARY KEY,
                    taxonomy_type VARCHAR(20),
                    location VARCHAR(100),
                    specialty VARCHAR(100),
                    ward VARCHAR(100),
                    title VARCHAR(200),
                    meta_description TEXT,
                    brief_intro TEXT,
                    full_description TEXT,
                    provider_count INTEGER,
                    priority_tier INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            session.commit()
            
            # Insert content
            for content in content_list:
                session.execute(text("""
                    INSERT INTO taxonomy_content 
                    (taxonomy_type, location, specialty, ward, title, meta_description, 
                     brief_intro, full_description, provider_count, priority_tier)
                    VALUES 
                    (:type, :location, :specialty, :ward, :title, :meta, 
                     :brief, :full, :count, :tier)
                    ON CONFLICT DO NOTHING
                """), {
                    'type': content.taxonomy_type,
                    'location': content.location,
                    'specialty': content.specialty,
                    'ward': content.ward,
                    'title': content.title,
                    'meta': content.meta_description,
                    'brief': content.brief_intro,
                    'full': content.full_description,
                    'count': content.provider_count,
                    'tier': content.priority_tier
                })
            
            session.commit()
            logger.info(f"✅ Saved {len(content_list)} content pieces to database")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving content: {e}")
        finally:
            session.close()
    
    def load_priority_data(self) -> Dict:
        """Load SEO priority data"""
        try:
            with open('seo_priority_data.json', 'r') as f:
                return json.load(f)
        except:
            logger.warning("Could not load priority data")
            return {"tier1": [], "tier2": []}
    
    def generate_all_priority_content(self, batch_size: int = 5) -> List[TaxonomyContent]:
        """Generate all priority content"""
        priority_data = self.load_priority_data()
        
        # Prepare all items
        all_items = []
        
        # Tier 1 combinations
        for city, ward, specialty, count in priority_data.get("tier1", []):
            all_items.append(("combination", city, specialty, ward, count))
        
        # Tier 2 combinations
        for city, ward, count in priority_data.get("tier2", [])[:20]:
            for specialty in ["General Medicine", "Dentistry"]:
                all_items.append(("combination", city, specialty, ward, count))
        
        logger.info(f"📊 Generating content for {len(all_items)} priority pages...")
        
        # Process in batches
        all_content = []
        for i in range(0, len(all_items), batch_size):
            batch = all_items[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(all_items)-1)//batch_size + 1}...")
            
            content_batch = self.generate_mega_batch(batch, batch_size)
            all_content.extend(content_batch)
            
            self.save_content(content_batch)
            
            if i + batch_size < len(all_items):
                time.sleep(2)
        
        logger.info("=" * 60)
        logger.info("✅ CONTENT GENERATION COMPLETE")
        logger.info(f"   Total pages generated: {len(all_content)}")
        logger.info(f"   Tier 1 pages: {len([c for c in all_content if c.priority_tier == 1])}")
        logger.info(f"   Tier 2 pages: {len([c for c in all_content if c.priority_tier == 2])}")
        logger.info("=" * 60)
        
        return all_content


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate SEO taxonomy content')
    parser.add_argument('--mode', choices=['test', 'tier1', 'tier2', 'all'], 
                       default='test', help='Generation mode')
    parser.add_argument('--limit', type=int, help='Limit number of pages')
    parser.add_argument('--dry-run', action='store_true', help='Test without saving')
    
    args = parser.parse_args()
    
    generator = TaxonomyContentGenerator()
    
    if args.mode == 'test':
        logger.info("🧪 Test mode - generating single content piece...")
        
        test_item = ("combination", "Tokyo", "Gynecology", "Minato", 8)
        content = generator._generate_individual(test_item)
        
        print("\n" + "=" * 60)
        print("GENERATED CONTENT:")
        print("=" * 60)
        print(f"Title: {content.title}")
        print(f"Meta: {content.meta_description}")
        print(f"\nBrief Intro:\n{content.brief_intro}")
        print(f"\nFull Description (first 500 chars):\n{content.full_description[:500]}...")
        
        if not args.dry_run:
            generator.save_content([content])
    
    elif args.mode == 'tier1':
        logger.info("🏆 Generating Tier 1 content (5+ providers)...")
        
        priority_data = generator.load_priority_data()
        tier1_items = []
        
        for city, ward, specialty, count in priority_data.get("tier1", [])[:args.limit] if args.limit else priority_data.get("tier1", []):
            tier1_items.append(("combination", city, specialty, ward, count))
        
        all_content = []
        for i in range(0, len(tier1_items), 5):
            batch = tier1_items[i:i+5]
            content_batch = generator.generate_mega_batch(batch, 5)
            all_content.extend(content_batch)
            
            if not args.dry_run:
                generator.save_content(content_batch)
            
            time.sleep(2)
        
        logger.info(f"✅ Generated {len(all_content)} Tier 1 pages")
    
    elif args.mode == 'tier2':
        logger.info("📈 Generating Tier 2 content (1-4 providers)...")
        
        priority_data = generator.load_priority_data()
        tier2_items = []
        
        for city, ward, count in priority_data.get("tier2", [])[:args.limit] if args.limit else priority_data.get("tier2", []):
            for specialty in ["General Medicine", "Dentistry"]:
                tier2_items.append(("combination", city, specialty, ward, count))
        
        all_content = []
        for i in range(0, len(tier2_items), 5):
            batch = tier2_items[i:i+5]
            content_batch = generator.generate_mega_batch(batch, 5)
            all_content.extend(content_batch)
            
            if not args.dry_run:
                generator.save_content(content_batch)
            
            time.sleep(2)
        
        logger.info(f"✅ Generated {len(all_content)} Tier 2 pages")
    
    else:  # all
        logger.info("🌟 Generating ALL priority content...")
        
        if not args.dry_run:
            all_content = generator.generate_all_priority_content()
        else:
            logger.info("Dry run - would generate all priority content")


if __name__ == "__main__":
    main()