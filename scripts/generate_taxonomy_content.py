#!/usr/bin/env python3
"""
SEO Taxonomy Content Generator
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
    brief_intro: str  # 50-75 words
    full_description: str  # 400-500 words
    location: Optional[str] = None
    specialty: Optional[str] = None
    ward: Optional[str] = None
    provider_count: int = 0
    priority_tier: int = 3


class TaxonomyContentGenerator:
    """
    Generates SEO-optimized content for taxonomy pages using Claude AI.
    Implements mega-batch processing and 70/30 unique/template hybrid approach.
    """
    
    # Template elements (30% of content)
    TEMPLATE_SECTIONS = {
        "insurance": """
Japanese health insurance typically covers 70% of medical costs at participating clinics. 
International insurance is also widely accepted. Payment methods include cash, credit cards, 
and some clinics accept digital payments. Always confirm insurance acceptance when booking.
        """,
        
        "appointment": """
Appointments can usually be made by phone, online, or walk-in depending on the clinic. 
Many facilities offer same-day appointments for urgent care. English-speaking staff can 
assist with booking and paperwork. Online booking systems are increasingly available.
        """,
        
        "medical_system": """
Japan's healthcare system is known for high quality and efficiency. Clinics typically 
operate on a first-come, first-served basis with appointment options. Prescriptions are 
filled at separate pharmacies. Regular health checks are encouraged and affordable.
        """
    }
    
    # Location-specific keywords for uniqueness
    LOCATION_KEYWORDS = {
        "Shinjuku": ["business district", "Takashimaya Times Square", "evening hours", "JR Shinjuku Station"],
        "Shibuya": ["youth culture", "Shibuya Crossing", "trendy clinics", "tech-savvy services"],
        "Minato": ["expat-friendly", "international community", "embassies", "Roppongi Hills"],
        "Ginza": ["luxury services", "high-end facilities", "shopping district", "premium care"],
        "Ueno": ["museums", "Ueno Park", "traditional", "accessible location"],
        "Asakusa": ["tourist area", "Sensoji Temple", "traditional medicine", "visitor-friendly"],
        "Yokohama": ["port city", "Chinatown", "international", "Minato Mirai"],
        "Osaka": ["Kansai region", "friendly atmosphere", "Dotonbori", "merchant city"],
    }
    
    def __init__(self):
        """Initialize the content generator"""
        self.db = DatabaseManager()
        self.cost_tracker = CostTracker()
        
        # Initialize Claude client
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = anthropic.Client(api_key=api_key)
        self.content_cache = {}
        self.generated_count = 0
        
        logger.info("✅ Taxonomy Content Generator initialized")
    
    def load_priority_data(self) -> Dict:
        """Load the priority data from the analysis"""
        try:
            with open('seo_priority_data.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Priority data file not found, using defaults")
            return {"tier1": [], "tier2": [], "locations": {}, "specialties": {}}
    
    def generate_location_content(self, location: str, ward: Optional[str] = None) -> TaxonomyContent:
        """
        Generate content for a location taxonomy page.
        
        Args:
            location: City name
            ward: Optional ward/district name
            
        Returns:
            TaxonomyContent object with generated content
        """
        full_location = f"{ward}, {location}" if ward else location
        
        # Get location-specific keywords
        keywords = self.LOCATION_KEYWORDS.get(ward or location, [])
        keyword_text = ", ".join(keywords) if keywords else "convenient location"
        
        # Count providers in this location
        session = self.db.get_session()
        try:
            if ward:
                count = session.execute(text("""
                    SELECT COUNT(*) FROM providers 
                    WHERE city = :city AND ward = :ward
                """), {"city": location, "ward": ward}).scalar()
            else:
                count = session.execute(text("""
                    SELECT COUNT(*) FROM providers 
                    WHERE city = :city
                """), {"city": location}).scalar()
        finally:
            session.close()
        
        # Create prompt for location content
        prompt = f"""
Generate SEO-optimized content for a healthcare directory location page.

Location: {full_location}
Provider Count: {count}
Local Features: {keyword_text}

Required sections:
1. Meta Title (60 chars max): "English Doctors & Clinics in {full_location} - Find Healthcare"
2. Meta Description (155 chars): Brief, compelling description for search results
3. Brief Intro (50-75 words): Welcoming introduction mentioning the area
4. Full Description (400-500 words) covering:
   - What {full_location} is known for (use local features: {keyword_text})
   - Types of medical facilities available
   - Why international residents choose this area
   - Transportation and accessibility
   - General atmosphere and patient experience
   
Make the content unique by incorporating specific local landmarks and characteristics.
Focus on helping English-speaking residents and visitors find healthcare.
Use a professional, informative, yet friendly tone.

Format the response as JSON with keys: title, meta_description, brief_intro, full_description
"""
        
        # Generate content with Claude
        content = self._generate_with_claude(prompt)
        
        return TaxonomyContent(
            taxonomy_type="location",
            title=content.get("title", f"Healthcare in {full_location}"),
            meta_description=content.get("meta_description", f"Find English-speaking doctors in {full_location}"),
            brief_intro=content.get("brief_intro", ""),
            full_description=content.get("full_description", "") + "\n\n" + self.TEMPLATE_SECTIONS["medical_system"],
            location=location,
            ward=ward,
            provider_count=count
        )
    
    def generate_specialty_content(self, specialty: str) -> TaxonomyContent:
        """
        Generate content for a specialty taxonomy page.
        
        Args:
            specialty: Medical specialty name
            
        Returns:
            TaxonomyContent object with generated content
        """
        # Count providers with this specialty
        session = self.db.get_session()
        try:
            count = session.execute(text("""
                SELECT COUNT(*) FROM providers 
                WHERE specialties::text LIKE :specialty
            """), {"specialty": f"%{specialty}%"}).scalar()
        finally:
            session.close()
        
        # Create prompt for specialty content
        prompt = f"""
Generate SEO-optimized content for a medical specialty page.

Specialty: {specialty}
Provider Count: {count} English-speaking providers

Required sections:
1. Meta Title (60 chars max): "English-Speaking {specialty} in Japan - Find Specialists"
2. Meta Description (155 chars): Brief, compelling description for search results
3. Brief Intro (50-75 words): What this specialty covers
4. Full Description (400-500 words) covering:
   - What {specialty} specialists treat
   - Common conditions and symptoms
   - When to see a {specialty} specialist
   - Typical procedures and treatments
   - What to expect during appointments
   - How to prepare for your visit
   
Make the content educational and trustworthy.
Focus on helping patients understand when and why to seek this type of care.
Use a professional, informative tone that builds confidence.

Format the response as JSON with keys: title, meta_description, brief_intro, full_description
"""
        
        # Generate content with Claude
        content = self._generate_with_claude(prompt)
        
        return TaxonomyContent(
            taxonomy_type="specialty",
            title=content.get("title", f"{specialty} Specialists"),
            meta_description=content.get("meta_description", f"Find English-speaking {specialty} specialists"),
            brief_intro=content.get("brief_intro", ""),
            full_description=content.get("full_description", "") + "\n\n" + self.TEMPLATE_SECTIONS["insurance"],
            specialty=specialty,
            provider_count=count
        )
    
    def generate_combination_content(self, location: str, specialty: str, 
                                    ward: Optional[str] = None, 
                                    provider_count: int = 0) -> TaxonomyContent:
        """
        Generate content for a combination (specialty + location) page.
        This is the SEO GOLD - most valuable for organic traffic.
        
        Args:
            location: City name
            specialty: Medical specialty
            ward: Optional ward/district name
            provider_count: Number of providers
            
        Returns:
            TaxonomyContent object with generated content
        """
        full_location = f"{ward}, {location}" if ward else location
        
        # Get location-specific keywords
        keywords = self.LOCATION_KEYWORDS.get(ward or location, [])
        keyword_text = ", ".join(keywords[:2]) if keywords else "this area"
        
        # Determine priority tier
        if provider_count >= 5:
            priority_tier = 1
        elif provider_count >= 1:
            priority_tier = 2
        else:
            priority_tier = 3
        
        # Create prompt for combination content
        prompt = f"""
Generate SEO-optimized content for a combination page targeting a specific medical specialty in a specific location.
This is a HIGH-PRIORITY page for organic search traffic.

Specialty: {specialty}
Location: {full_location}
Provider Count: {provider_count} verified providers
Local Context: {keyword_text}
Priority: Tier {priority_tier}

Required sections:
1. Meta Title (60 chars max): "{specialty} in {full_location} - {provider_count}+ English Doctors"
2. Meta Description (155 chars): Compelling description mentioning both specialty and location
3. Brief Intro (50-75 words): Welcome message combining specialty expertise and local convenience
4. Full Description (400-500 words) with these sections:
   
   Opening paragraph: Seeking {specialty} care in {full_location}
   
   Local Context paragraph: Why {full_location} is convenient for {specialty} care
   - Mention: {keyword_text}
   - Transportation options
   - Nearby facilities
   
   Specialty Information paragraph: What our {specialty} providers offer
   - Common treatments
   - English support level
   - Modern equipment and techniques
   
   Patient Experience paragraph: What to expect
   - Appointment process
   - Language support
   - Insurance and payment
   
   Closing paragraph: Call to action to browse providers

Make the content highly specific to both the location AND specialty.
Use local landmarks and area characteristics naturally.
Optimize for search intent: "English {specialty} in {full_location}"
Professional yet approachable tone that builds trust.

Format the response as JSON with keys: title, meta_description, brief_intro, full_description
"""
        
        # Generate content with Claude
        content = self._generate_with_claude(prompt)
        
        # Add appropriate template section based on context
        template_addition = self.TEMPLATE_SECTIONS["appointment"] if provider_count > 0 else self.TEMPLATE_SECTIONS["medical_system"]
        
        return TaxonomyContent(
            taxonomy_type="combination",
            title=content.get("title", f"{specialty} in {full_location}"),
            meta_description=content.get("meta_description", f"Find {specialty} in {full_location}"),
            brief_intro=content.get("brief_intro", ""),
            full_description=content.get("full_description", "") + "\n\n" + template_addition,
            location=location,
            specialty=specialty,
            ward=ward,
            provider_count=provider_count,
            priority_tier=priority_tier
        )
    
    def _generate_with_claude(self, prompt: str) -> Dict:
        """
        Generate content using Claude API.
        
        Args:
            prompt: The prompt to send to Claude
            
        Returns:
            Dictionary with generated content
        """
        try:
            # Track API call cost (estimate based on tokens)
            estimated_cost = 0.01  # Haiku model cost estimate
            
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse response
            content_text = response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
            
            # Try to parse as JSON
            try:
                import re
                # Extract JSON from response if wrapped in other text
                json_match = re.search(r'\{.*\}', content_text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    
                    # Handle nested structure if full_description is a dict
                    full_desc = parsed.get("full_description", "")
                    if isinstance(full_desc, dict):
                        # Combine all paragraphs
                        full_desc = "\n\n".join([
                            str(full_desc.get("opening_paragraph", "")),
                            str(full_desc.get("local_context_paragraph", "")),
                            str(full_desc.get("specialty_information_paragraph", "")),
                            str(full_desc.get("patient_experience_paragraph", "")),
                            str(full_desc.get("closing_paragraph", ""))
                        ])
                    
                    # Ensure all values are strings
                    return {
                        "title": str(parsed.get("title", "Healthcare Directory")),
                        "meta_description": str(parsed.get("meta_description", "Find healthcare providers")),
                        "brief_intro": str(parsed.get("brief_intro", "Welcome to our directory")),
                        "full_description": str(full_desc)
                    }
                else:
                    # Fallback: create structured content from text
                    lines = content_text.strip().split('\n')
                    return {
                        "title": lines[0] if lines else "Healthcare Directory",
                        "meta_description": lines[1] if len(lines) > 1 else "Find healthcare providers",
                        "brief_intro": ' '.join(lines[2:5]) if len(lines) > 2 else "Welcome to our directory",
                        "full_description": '\n'.join(lines[5:]) if len(lines) > 5 else content_text
                    }
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"JSON parsing failed: {str(e)}")
                # If JSON parsing fails, structure the content manually
                return {
                    "title": "Healthcare Directory",
                    "meta_description": "Find English-speaking healthcare providers",
                    "brief_intro": str(content_text)[:200] if content_text else "Welcome",
                    "full_description": str(content_text) if content_text else "Browse our directory"
                }
                
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            # Return fallback content
            return {
                "title": "Healthcare Directory",
                "meta_description": "Find English-speaking healthcare providers in Japan",
                "brief_intro": "Find quality healthcare providers in your area.",
                "full_description": "Browse our directory of English-speaking healthcare providers."
            }
    
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
        
        # Create a mega prompt for multiple items
        mega_prompt = """
Generate SEO-optimized content for multiple taxonomy pages in one response.
Create unique, high-quality content for each page.

PAGES TO GENERATE:
"""
        
        for i, item in enumerate(items[:batch_size], 1):
            content_type, location, specialty, ward, count = item
            
            if content_type == "combination":
                full_location = f"{ward}, {location}" if ward else location
                mega_prompt += f"""

PAGE {i}: {specialty} in {full_location}
Type: Combination Page (HIGH PRIORITY)
Providers: {count}
Target Keywords: "English {specialty} in {full_location}"
"""
            elif content_type == "location":
                full_location = f"{ward}, {location}" if ward else location
                mega_prompt += f"""

PAGE {i}: Healthcare in {full_location}
Type: Location Page
Providers: {count}
Target Keywords: "English doctors in {full_location}"
"""
            else:  # specialty
                mega_prompt += f"""

PAGE {i}: {specialty} Specialists
Type: Specialty Page  
Providers: {count}
Target Keywords: "English {specialty} Japan"
"""
        
        mega_prompt += """

For EACH page, provide:
1. title (60 chars max)
2. meta_description (155 chars max)
3. brief_intro (50-75 words)
4. full_description (400-500 words)

Format as JSON array with each page as an object.
Make each page unique with specific local details and medical information.
Maintain SEO best practices and natural keyword usage.
"""
        
        # Generate all content in one API call
        try:
            logger.info(f"🚀 Generating mega-batch of {len(items[:batch_size])} content pieces...")
            
            # Track cost estimate for mega batch
            estimated_cost = 0.05  # Higher cost for mega batch
            
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4096,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": mega_prompt
                }]
            )
            
            content_text = response.content[0].text
            
            # Parse the response
            try:
                # Try to extract JSON array
                import re
                json_match = re.search(r'\[.*\]', content_text, re.DOTALL)
                if json_match:
                    content_array = json.loads(json_match.group())
                else:
                    # Fallback to individual parsing
                    content_array = [{}] * len(items[:batch_size])
            except:
                content_array = [{}] * len(items[:batch_size])
            
            # Create TaxonomyContent objects
            results = []
            for i, item in enumerate(items[:batch_size]):
                content_type, location, specialty, ward, count = item
                
                content_data = content_array[i] if i < len(content_array) else {}
                
                # Add template sections
                if content_type == "combination":
                    template = self.TEMPLATE_SECTIONS["appointment"]
                elif content_type == "location":
                    template = self.TEMPLATE_SECTIONS["medical_system"]
                else:
                    template = self.TEMPLATE_SECTIONS["insurance"]
                
                results.append(TaxonomyContent(
                    taxonomy_type=content_type,
                    title=content_data.get("title", f"Healthcare Directory"),
                    meta_description=content_data.get("meta_description", "Find healthcare"),
                    brief_intro=content_data.get("brief_intro", ""),
                    full_description=content_data.get("full_description", "") + "\n\n" + template,
                    location=location,
                    specialty=specialty,
                    ward=ward,
                    provider_count=count,
                    priority_tier=1 if count >= 5 else 2 if count >= 1 else 3
                ))
            
            self.generated_count += len(results)
            logger.info(f"✅ Generated {len(results)} content pieces (Total: {self.generated_count})")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in mega-batch generation: {str(e)}")
            # Fall back to individual generation
            return [self._generate_individual(item) for item in items[:batch_size]]
    
    def _generate_individual(self, item: Tuple) -> TaxonomyContent:
        """Generate content for a single item"""
        content_type, location, specialty, ward, count = item
        
        if content_type == "combination":
            return self.generate_combination_content(location, specialty, ward, count)
        elif content_type == "location":
            return self.generate_location_content(location, ward)
        else:
            return self.generate_specialty_content(specialty)
    
    def save_content(self, content_list: List[TaxonomyContent]):
        """
        Save generated content to database for WordPress sync.
        
        Args:
            content_list: List of TaxonomyContent objects to save
        """
        session = self.db.get_session()
        try:
            # Create taxonomy_content table if it doesn't exist
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS taxonomy_content (
                    id SERIAL PRIMARY KEY,
                    taxonomy_type VARCHAR(20),
                    location VARCHAR(100),
                    specialty VARCHAR(100),
                    ward VARCHAR(100),
                    title VARCHAR(255),
                    meta_description TEXT,
                    brief_intro TEXT,
                    full_description TEXT,
                    provider_count INTEGER,
                    priority_tier INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced_to_wordpress BOOLEAN DEFAULT FALSE,
                    wordpress_id INTEGER
                )
            """))
            
            # Insert content
            for content in content_list:
                session.execute(text("""
                    INSERT INTO taxonomy_content 
                    (taxonomy_type, location, specialty, ward, title, meta_description, 
                     brief_intro, full_description, provider_count, priority_tier)
                    VALUES 
                    (:type, :location, :specialty, :ward, :title, :meta_desc, 
                     :brief, :full, :count, :tier)
                """), {
                    "type": content.taxonomy_type,
                    "location": content.location,
                    "specialty": content.specialty,
                    "ward": content.ward,
                    "title": content.title,
                    "meta_desc": content.meta_description,
                    "brief": content.brief_intro,
                    "full": content.full_description,
                    "count": content.provider_count,
                    "tier": content.priority_tier
                })
            
            session.commit()
            logger.info(f"💾 Saved {len(content_list)} content pieces to database")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving content: {str(e)}")
        finally:
            session.close()
    
    def generate_all_priority_content(self):
        """
        Generate all priority content based on the analysis.
        Process in priority order: Tier 1, Tier 2, then additional high-value pages.
        """
        logger.info("🚀 Starting priority content generation...")
        
        # Load priority data
        priority_data = self.load_priority_data()
        
        # Prepare items for generation
        all_items = []
        
        # Add Tier 1 combinations (5+ providers)
        for city, ward, specialty, count in priority_data.get("tier1", []):
            all_items.append(("combination", city, specialty, ward, count))
        
        # Add Tier 2 combinations (1-4 providers) 
        for city, ward, count in priority_data.get("tier2", []):
            # Generate for common specialties
            for specialty in ["General Medicine", "Dentistry", "Pediatrics"]:
                all_items.append(("combination", city, specialty, ward, count))
        
        # Add high-value location pages
        for location, count in priority_data.get("locations", {}).items():
            if count >= 5:
                all_items.append(("location", location, None, None, count))
        
        # Add specialty pages
        for specialty, count in priority_data.get("specialties", {}).items():
            if count >= 10:
                all_items.append(("specialty", None, specialty, None, count))
        
        logger.info(f"📊 Total items to generate: {len(all_items)}")
        logger.info(f"   - Tier 1 combinations: {len(priority_data.get('tier1', []))}")
        logger.info(f"   - Tier 2 combinations: {len(priority_data.get('tier2', [])) * 3}")
        logger.info(f"   - Location pages: {len([l for l, c in priority_data.get('locations', {}).items() if c >= 5])}")
        logger.info(f"   - Specialty pages: {len([s for s, c in priority_data.get('specialties', {}).items() if c >= 10])}")
        
        # Process in batches
        batch_size = 5
        all_content = []
        
        for i in range(0, len(all_items), batch_size):
            batch = all_items[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(all_items)-1)//batch_size + 1}...")
            
            # Generate content
            content_batch = self.generate_mega_batch(batch, batch_size)
            all_content.extend(content_batch)
            
            # Save batch
            self.save_content(content_batch)
            
            # Rate limiting
            if i + batch_size < len(all_items):
                time.sleep(2)
        
        # Summary
        logger.info("=" * 60)
        logger.info("✅ CONTENT GENERATION COMPLETE")
        logger.info(f"   Total pages generated: {len(all_content)}")
        logger.info(f"   Tier 1 pages: {len([c for c in all_content if c.priority_tier == 1])}")
        logger.info(f"   Tier 2 pages: {len([c for c in all_content if c.priority_tier == 2])}")
        logger.info(f"   Estimated API cost: ${self.generated_count * 0.01:.2f}")
        logger.info("=" * 60)
        
        return all_content


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate SEO taxonomy content')
    parser.add_argument('--mode', choices=['test', 'tier1', 'tier2', 'all'], 
                       default='test', help='Generation mode')
    parser.add_argument('--limit', type=int, help='Limit number of pages to generate')
    parser.add_argument('--dry-run', action='store_true', help='Test without saving')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = TaxonomyContentGenerator()
    
    if args.mode == 'test':
        # Test with a single page
        logger.info("🧪 Running test generation...")
        
        content = generator.generate_combination_content(
            location="Tokyo",
            specialty="Dentistry", 
            ward="Shinjuku",
            provider_count=8
        )
        
        print("\n" + "=" * 60)
        print("GENERATED CONTENT SAMPLE")
        print("=" * 60)
        print(f"Title: {content.title}")
        print(f"Meta: {content.meta_description}")
        print(f"\nBrief Intro:\n{content.brief_intro}")
        print(f"\nFull Description (first 500 chars):\n{content.full_description[:500]}...")
        print("=" * 60)
        
        if not args.dry_run:
            generator.save_content([content])
    
    elif args.mode == 'tier1':
        # Generate Tier 1 content only
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
        # Generate Tier 2 content
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
        # Generate all priority content
        logger.info("🌟 Generating ALL priority content...")
        
        if not args.dry_run:
            all_content = generator.generate_all_priority_content()
        else:
            logger.info("Dry run - would generate all priority content")


if __name__ == "__main__":
    main()