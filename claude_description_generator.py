#!/usr/bin/env python3
"""
Enhanced AI Description Generator Module
Generates comprehensive, natural AI-powered descriptions for healthcare providers using Anthropic.
Integrates patient review data, facility information, and accessibility details for informative descriptions.

Usage Examples:

Enhanced Single Provider Generation:
    generator = ClaudeDescriptionGenerator()
    provider_data = {
        'provider_name': 'Tokyo Medical Center',
        'city': 'Tokyo',
        'specialties': ['General Medicine'],
        'english_proficiency': 'Fluent',
        'rating': 4.3,
        'total_reviews': 127,
        'review_content': '[{"author": "John", "rating": 5, "text": "Excellent care..."}]',
        'wheelchair_accessible': True,
        'parking_available': True,
        'website': 'https://example.com',
        'phone': '+81-3-1234-5678'
    }
    description = generator.generate_description(provider_data)

Enhanced Batch Generation (Recommended - integrates review data and patient feedback):
    providers = [comprehensive_provider_data1, provider_data2, provider_data3, ...]
    descriptions = generator.generate_batch_descriptions(providers, batch_size=5)
    
Database Integration with Full Enhancement:
    # Automatically pulls all provider data including reviews for enhanced descriptions
    run_batch_ai_description_generation(provider_list, batch_size=5)
"""

import os
import json
import logging
from dotenv import load_dotenv
from anthropic import Anthropic
from google_places_integration import GooglePlacesHealthcareCollector  # For session access
from postgres_integration import Provider  # Added import

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeDescriptionGenerator:
    def __init__(self):
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config', '.env')
        load_dotenv(config_path)
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.anthropic_api_key:
            logger.error("ANTHROPIC_API_KEY not found in .env")
            raise ValueError("ANTHROPIC_API_KEY not found in .env")
        self.claude = Anthropic(api_key=self.anthropic_api_key)
        logger.info("ClaudeDescriptionGenerator initialized successfully")

    def process_review_content(self, review_content):
        """Process review content to extract meaningful insights."""
        if not review_content:
            return {
                'avg_rating': 0,
                'total_reviews': 0,
                'positive_themes': [],
                'concerns': [],
                'english_mentions': []
            }
        
        try:
            # Parse review content
            if isinstance(review_content, str):
                reviews = json.loads(review_content) if review_content.strip() else []
            else:
                reviews = review_content
            
            if not reviews or not isinstance(reviews, list):
                return {
                    'avg_rating': 0,
                    'total_reviews': 0,
                    'positive_themes': [],
                    'concerns': [],
                    'english_mentions': []
                }
            
            # Calculate statistics
            avg_rating = sum(r.get('rating', 0) for r in reviews) / len(reviews) if reviews else 0
            total_reviews = len(reviews)
            
            # Extract positive feedback (4+ stars)
            positive_reviews = [r.get('text', '') for r in reviews if r.get('rating', 0) >= 4]
            positive_themes = []
            for review in positive_reviews[:3]:  # Limit to 3 most relevant
                if len(review) > 20:  # Skip very short reviews
                    # Extract key phrases (simplified)
                    if 'professional' in review.lower() or 'excellent' in review.lower():
                        positive_themes.append('professional service')
                    if 'clean' in review.lower() or 'modern' in review.lower():
                        positive_themes.append('clean facilities')
                    if 'friendly' in review.lower() or 'kind' in review.lower():
                        positive_themes.append('friendly staff')
                    if 'wait' in review.lower() and ('short' in review.lower() or 'quick' in review.lower()):
                        positive_themes.append('minimal wait times')
            
            # Extract concerns (3 stars or less)
            negative_reviews = [r.get('text', '') for r in reviews if r.get('rating', 0) <= 3]
            concerns = []
            for review in negative_reviews[:2]:  # Limit to 2 concerns
                if len(review) > 20:
                    if 'wait' in review.lower() and ('long' in review.lower() or 'delay' in review.lower()):
                        concerns.append('longer wait times')
                    if 'expensive' in review.lower() or 'cost' in review.lower():
                        concerns.append('higher costs')
                    if 'language' in review.lower() or 'communication' in review.lower():
                        concerns.append('language barriers')
            
            # Extract English language mentions
            english_mentions = []
            for review in reviews:
                text = review.get('text', '').lower()
                if 'english' in text:
                    if 'speak' in text or 'speaking' in text:
                        english_mentions.append('English-speaking staff')
                    elif 'understand' in text:
                        english_mentions.append('English understanding')
                    elif 'translate' in text:
                        english_mentions.append('Translation services')
            
            return {
                'avg_rating': round(avg_rating, 1),
                'total_reviews': total_reviews,
                'positive_themes': list(set(positive_themes))[:3],  # Remove duplicates, limit to 3
                'concerns': list(set(concerns))[:2],  # Remove duplicates, limit to 2
                'english_mentions': list(set(english_mentions))[:2]  # Remove duplicates, limit to 2
            }
            
        except Exception as e:
            logger.error(f"Error processing review content: {str(e)}")
            return {
                'avg_rating': 0,
                'total_reviews': 0,
                'positive_themes': [],
                'concerns': [],
                'english_mentions': []
            }

    def create_enhanced_prompt(self, provider_data):
        """Create an enhanced prompt with review data and detailed information."""
        provider_name = provider_data.get('provider_name', 'Unknown Provider')
        city = provider_data.get('city', 'Unknown City')
        prefecture = provider_data.get('prefecture', '')
        specialties = provider_data.get('specialties', ['General Practitioner'])
        english_proficiency = provider_data.get('english_proficiency', 'Unknown')
        
        # Process additional data
        rating = provider_data.get('rating', 0)
        total_reviews = provider_data.get('total_reviews', 0)
        business_hours = provider_data.get('business_hours', {})
        wheelchair_accessible = provider_data.get('wheelchair_accessible', False)
        parking_available = provider_data.get('parking_available', False)
        website = provider_data.get('website', '')
        phone = provider_data.get('phone', '')
        
        # Process reviews for insights
        review_content = provider_data.get('review_content', '')
        review_insights = self.process_review_content(review_content)
        
        # Format specialties naturally
        if isinstance(specialties, list):
            specialty_text = ', '.join(specialties) if specialties else 'General Practitioner'
        else:
            specialty_text = specialties
        
        # Location context
        location_text = f"{city}"
        if prefecture and prefecture != city:
            location_text += f", {prefecture}"
        
        # Build enhanced prompt
        prompt = f"""
Write a natural, informative description for this healthcare provider. Focus on being specific and helpful to potential patients.

PROVIDER DETAILS:
- Name: {provider_name}
- Location: {location_text}  
- Medical Specialties: {specialty_text}
- English Language Support: {english_proficiency}

PATIENT EXPERIENCE DATA:
- Google Rating: {rating}/5 stars ({total_reviews} reviews)
- Positive Patient Feedback: {', '.join(review_insights['positive_themes']) if review_insights['positive_themes'] else 'Limited feedback available'}
- Patient Concerns: {', '.join(review_insights['concerns']) if review_insights['concerns'] else 'No significant concerns noted'}
- English Language Notes: {', '.join(review_insights['english_mentions']) if review_insights['english_mentions'] else 'English support level varies'}

FACILITY INFORMATION:
- Wheelchair Accessibility: {'Yes' if wheelchair_accessible else 'Not specified'}
- Parking Available: {'Yes' if parking_available else 'Not specified'}
- Contact: {phone if phone else 'Contact via facility'}
- Website: {'Available' if website else 'Not available'}

INSTRUCTIONS:
Write a comprehensive 150-160 word description in TWO paragraphs that flow naturally together:

PARAGRAPH 1 (75-80 words): Focus on core medical services and specialty expertise
- What medical services they provide and their specialty focus
- Their English language capabilities for international patients
- Key professional strengths or unique features that set them apart

PARAGRAPH 2 (75-80 words): Focus on patient experience and practical information  
- Patient experience highlights from reviews (specific feedback when available)
- Practical details (location, accessibility, parking) that help patients decide
- Contact information and convenience factors that matter to patients

Make it sound like a knowledgeable local would describe this provider to a friend. Use specific patient feedback when available, avoid generic phrases. Ensure the two paragraphs flow naturally together with smooth transitions - the second paragraph should build upon the first to create one cohesive story about the provider's complete offering.
"""
        
        return prompt

    def generate_description(self, provider_data):
        """Generate a description for a single provider using Claude with enhanced prompts."""
        provider_name = provider_data.get('provider_name', 'Unknown Provider')
        
        # Use enhanced prompt with review data
        prompt = self.create_enhanced_prompt(provider_data)

        try:
            logger.info(f"Generating enhanced description for {provider_name}")
            response = self.claude.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=450,  # Increased for 150-160 word two-paragraph descriptions
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            description = response.content[0].text.strip()
            logger.info(f"✅ Generated enhanced description for {provider_name}: {description[:50]}...")
            return description
        except Exception as e:
            logger.error(f"⚠️ Error generating description for {provider_name}: {str(e)}")
            return "Professional healthcare provider offering medical services. Please contact the facility directly for more information."

    def generate_batch_descriptions(self, provider_data_list, batch_size=5):
        """Generate descriptions for a batch of providers in a single API call.
        
        Args:
            provider_data_list: List of provider dictionaries
            batch_size: Maximum number of providers to process in one API call
            
        Returns:
            List of descriptions matching the input order
        """
        if not provider_data_list:
            return []

        all_descriptions = []
        
        # Process in chunks to avoid hitting token limits
        for i in range(0, len(provider_data_list), batch_size):
            batch = provider_data_list[i:i + batch_size]
            batch_descriptions = self._generate_batch_chunk(batch)
            all_descriptions.extend(batch_descriptions)
            
        return all_descriptions

    def _generate_batch_chunk(self, provider_batch):
        """Generate enhanced descriptions for a single batch chunk with review data."""
        if not provider_batch:
            return []

        # Build enhanced batch prompt with comprehensive provider data
        provider_details = []
        for idx, provider_data in enumerate(provider_batch, 1):
            provider_name = provider_data.get('provider_name', 'Unknown Provider')
            city = provider_data.get('city', 'Unknown City')
            prefecture = provider_data.get('prefecture', '')
            specialties = provider_data.get('specialties', ['General Practitioner'])
            english_proficiency = provider_data.get('english_proficiency', 'Unknown')
            rating = provider_data.get('rating', 0)
            total_reviews = provider_data.get('total_reviews', 0)
            wheelchair_accessible = provider_data.get('wheelchair_accessible', False)
            
            # Process reviews for insights
            review_insights = self.process_review_content(provider_data.get('review_content', ''))
            
            # Format specialties
            if isinstance(specialties, list):
                specialty_text = ', '.join(specialties) if specialties else 'General Practitioner'
            else:
                specialty_text = specialties
            
            # Location context
            location_text = f"{city}"
            if prefecture and prefecture != city:
                location_text += f", {prefecture}"
            
            provider_details.append(f"""
Provider {idx}: {provider_name}
- Location: {location_text}
- Specialties: {specialty_text}
- English Support: {english_proficiency}
- Patient Rating: {rating}/5 stars ({total_reviews} reviews)
- Positive Feedback: {', '.join(review_insights['positive_themes']) if review_insights['positive_themes'] else 'Limited feedback available'}
- English Language Notes: {', '.join(review_insights['english_mentions']) if review_insights['english_mentions'] else 'Support level varies'}
- Accessibility: {'Wheelchair accessible' if wheelchair_accessible else 'Not specified'}""")

        batch_prompt = f"""
Write comprehensive 150-160 word descriptions for these {len(provider_batch)} healthcare providers. Each description should be formatted in TWO paragraphs that flow naturally together.

{chr(10).join(provider_details)}

INSTRUCTIONS FOR EACH DESCRIPTION:
Format each as TWO paragraphs (150-160 words total):

PARAGRAPH 1 (75-80 words): Core medical services and expertise
- Medical specialty and location
- English language capabilities for international patients
- Key professional strengths or unique features that set them apart

PARAGRAPH 2 (75-80 words): Patient experience and practical information
- Patient experience highlights from reviews (specific feedback when available)
- Practical details (accessibility, parking, location convenience)
- Contact information and convenience factors that matter to patients

Make each description sound like a knowledgeable local recommending the provider. Use specific patient feedback when available, avoid generic phrases. Ensure the two paragraphs flow naturally together with smooth transitions - the second paragraph should build upon the first to create one cohesive story about each provider's complete offering.

Please provide exactly {len(provider_batch)} descriptions, numbered 1-{len(provider_batch)}:

1. [Two-paragraph description for Provider 1]
2. [Two-paragraph description for Provider 2]
3. [Two-paragraph description for Provider 3]
...and so on.
"""

        try:
            logger.info(f"Generating enhanced batch descriptions for {len(provider_batch)} providers")
            response = self.claude.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=550 * len(provider_batch),  # Increased for 150-160 word two-paragraph descriptions
                temperature=0.7,
                messages=[{"role": "user", "content": batch_prompt}]
            )
            
            response_text = response.content[0].text.strip()
            descriptions = self._parse_batch_response(response_text, len(provider_batch))
            
            # Log results
            for provider_data, description in zip(provider_batch, descriptions):
                provider_name = provider_data.get('provider_name', 'Unknown Provider')
                logger.info(f"✅ Generated enhanced description for {provider_name}: {description[:50]}...")
                
            return descriptions
            
        except Exception as e:
            logger.error(f"⚠️ Error generating enhanced batch descriptions: {str(e)}")
            fallback_descriptions = ["Professional healthcare provider offering medical services. Please contact the facility directly for more information."] * len(provider_batch)
            return fallback_descriptions

    def _parse_batch_response(self, response_text, expected_count):
        """Parse the batch response and extract individual descriptions."""
        descriptions = []
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for numbered items (1. 2. 3. etc.)
            if line and len(line) > 3 and line[0].isdigit() and line[1:3] in ['. ', ') ']:
                # Extract description after the number
                description = line[3:].strip()
                if description:
                    descriptions.append(description)
        
        # If parsing fails or we don't get enough descriptions, fill with fallbacks
        while len(descriptions) < expected_count:
            descriptions.append("Professional healthcare provider offering quality medical services.")
            
        # If we got too many, trim to expected count
        return descriptions[:expected_count]

def filter_providers_needing_descriptions(providers):
    """Filter providers to only include those that need AI descriptions generated.
    
    Prevents API costs by excluding providers that already have:
    - AI descriptions generated
    - WordPress post IDs (already published)
    - Status of 'published' or 'description_generated'
    
    Args:
        providers: List of provider dictionaries or Provider objects
        
    Returns:
        List of providers that need descriptions generated
    """
    filtered_providers = []
    skipped_count = 0
    
    for provider in providers:
        # Handle both dictionary and Provider object inputs
        if hasattr(provider, '__dict__'):
            # Provider object from database
            provider_name = getattr(provider, 'provider_name', 'Unknown Provider')
            ai_description = getattr(provider, 'ai_description', None)
            wordpress_post_id = getattr(provider, 'wordpress_post_id', None)
            status = getattr(provider, 'status', 'pending')
        else:
            # Dictionary input
            provider_name = provider.get('provider_name', 'Unknown Provider')
            ai_description = provider.get('ai_description', None)
            wordpress_post_id = provider.get('wordpress_post_id', None)
            status = provider.get('status', 'pending')
        
        # Skip if already has description or is published
        if ai_description and ai_description.strip():
            logger.info(f"⏭️ Skipping {provider_name}: Already has AI description")
            skipped_count += 1
            continue
            
        if wordpress_post_id:
            logger.info(f"⏭️ Skipping {provider_name}: Already published to WordPress (ID: {wordpress_post_id})")
            skipped_count += 1
            continue
            
        if status in ['published', 'description_generated']:
            logger.info(f"⏭️ Skipping {provider_name}: Status is {status}")
            skipped_count += 1
            continue
        
        # Provider needs description
        filtered_providers.append(provider)
    
    logger.info(f"🔍 Filtering complete: {len(filtered_providers)} need descriptions, {skipped_count} skipped")
    return filtered_providers

def run_ai_description_generation(providers):
    """Generate enhanced descriptions for a list of provider dictionaries (single provider mode)."""
    generator = ClaudeDescriptionGenerator()
    collector = GooglePlacesHealthcareCollector()
    session = collector.Session()
    
    for provider in providers:
        # Prepare comprehensive provider data for enhanced descriptions
        if hasattr(provider, '__dict__'):
            # Provider object from database
            provider_data = {
                'provider_name': getattr(provider, 'provider_name', 'Unknown Provider'),
                'city': getattr(provider, 'city', 'Unknown City'),
                'prefecture': getattr(provider, 'prefecture', ''),
                'specialties': getattr(provider, 'specialties', ['General Practitioner']),
                'english_proficiency': getattr(provider, 'english_proficiency', 'Unknown'),
                'rating': getattr(provider, 'rating', 0),
                'total_reviews': getattr(provider, 'total_reviews', 0),
                'review_content': getattr(provider, 'review_content', ''),
                'business_hours': getattr(provider, 'business_hours', {}),
                'wheelchair_accessible': getattr(provider, 'wheelchair_accessible', False),
                'parking_available': getattr(provider, 'parking_available', False),
                'website': getattr(provider, 'website', ''),
                'phone': getattr(provider, 'phone', '')
            }
        else:
            # Dictionary input
            provider_data = {
                'provider_name': provider.get('provider_name', 'Unknown Provider'),
                'city': provider.get('city', 'Unknown City'),
                'prefecture': provider.get('prefecture', ''),
                'specialties': provider.get('specialties', ['General Practitioner']),
                'english_proficiency': provider.get('english_proficiency', 'Unknown'),
                'rating': provider.get('rating', 0),
                'total_reviews': provider.get('total_reviews', 0),
                'review_content': provider.get('review_content', ''),
                'business_hours': provider.get('business_hours', {}),
                'wheelchair_accessible': provider.get('wheelchair_accessible', False),
                'parking_available': provider.get('parking_available', False),
                'website': provider.get('website', ''),
                'phone': provider.get('phone', '')
            }
            
        description = generator.generate_description(provider_data)
        
        # Update the corresponding database record
        db_provider = session.query(Provider).filter_by(provider_name=provider_data['provider_name'], city=provider_data['city']).first()
        if db_provider:
            db_provider.ai_description = description
            db_provider.status = 'description_generated'
            session.commit()
            logger.info(f"✅ Updated {provider_data['provider_name']} with enhanced description and status")
    
    session.close()

def run_batch_ai_description_generation(providers, batch_size=5):
    """Generate descriptions for a list of providers using batch processing for efficiency.
    
    Args:
        providers: List of provider dictionaries or Provider objects
        batch_size: Number of providers to process in each batch (default: 5)
    """
    if not providers:
        logger.info("No providers to process")
        return
    
    # Filter out providers that don't need descriptions (prevents API costs)
    filtered_providers = filter_providers_needing_descriptions(providers)
    
    if not filtered_providers:
        logger.info("✅ All providers already have descriptions or are published")
        return
        
    generator = ClaudeDescriptionGenerator()
    collector = GooglePlacesHealthcareCollector()
    session = collector.Session()
    
    # Prepare comprehensive provider data for enhanced batch processing
    provider_data_list = []
    for provider in filtered_providers:
        # Handle both dictionary and Provider object inputs
        if hasattr(provider, '__dict__'):
            # Provider object from database
            provider_data = {
                'provider_name': getattr(provider, 'provider_name', 'Unknown Provider'),
                'city': getattr(provider, 'city', 'Unknown City'),
                'prefecture': getattr(provider, 'prefecture', ''),
                'specialties': getattr(provider, 'specialties', ['General Practitioner']),
                'english_proficiency': getattr(provider, 'english_proficiency', 'Unknown'),
                'rating': getattr(provider, 'rating', 0),
                'total_reviews': getattr(provider, 'total_reviews', 0),
                'review_content': getattr(provider, 'review_content', ''),
                'business_hours': getattr(provider, 'business_hours', {}),
                'wheelchair_accessible': getattr(provider, 'wheelchair_accessible', False),
                'parking_available': getattr(provider, 'parking_available', False),
                'website': getattr(provider, 'website', ''),
                'phone': getattr(provider, 'phone', '')
            }
        else:
            # Dictionary input
            provider_data = {
                'provider_name': provider.get('provider_name', 'Unknown Provider'),
                'city': provider.get('city', 'Unknown City'),
                'prefecture': provider.get('prefecture', ''),
                'specialties': provider.get('specialties', ['General Practitioner']),
                'english_proficiency': provider.get('english_proficiency', 'Unknown'),
                'rating': provider.get('rating', 0),
                'total_reviews': provider.get('total_reviews', 0),
                'review_content': provider.get('review_content', ''),
                'business_hours': provider.get('business_hours', {}),
                'wheelchair_accessible': provider.get('wheelchair_accessible', False),
                'parking_available': provider.get('parking_available', False),
                'website': provider.get('website', ''),
                'phone': provider.get('phone', '')
            }
        provider_data_list.append(provider_data)
    
    logger.info(f"🚀 Starting batch description generation for {len(provider_data_list)} providers")
    logger.info(f"📦 Using batch size: {batch_size}")
    
    # Generate descriptions in batches
    descriptions = generator.generate_batch_descriptions(provider_data_list, batch_size)
    
    # Update database records with generated descriptions
    successful_updates = 0
    failed_updates = 0
    
    for provider_data, description in zip(provider_data_list, descriptions):
        try:
            # Find the corresponding database record
            db_provider = session.query(Provider).filter_by(
                provider_name=provider_data['provider_name'], 
                city=provider_data['city']
            ).first()
            
            if db_provider:
                db_provider.ai_description = description
                db_provider.status = 'description_generated'
                session.commit()
                successful_updates += 1
                logger.info(f"✅ Updated {provider_data['provider_name']} with batch-generated description")
            else:
                logger.warning(f"⚠️ Provider not found in database: {provider_data['provider_name']} in {provider_data['city']}")
                failed_updates += 1
                
        except Exception as e:
            logger.error(f"❌ Error updating {provider_data['provider_name']}: {str(e)}")
            session.rollback()
            failed_updates += 1
    
    session.close()
    
    # Summary
    logger.info(f"📊 Batch processing complete:")
    logger.info(f"   ✅ Successful updates: {successful_updates}")
    logger.info(f"   ❌ Failed updates: {failed_updates}")
    logger.info(f"   📈 Success rate: {successful_updates/len(provider_data_list)*100:.1f}%")