#!/usr/bin/env python3
"""
AI Description Generator Module
Generates AI-powered descriptions for healthcare providers using Anthropic.

Usage Examples:

Single Provider Generation:
    generator = ClaudeDescriptionGenerator()
    provider_data = {
        'provider_name': 'Tokyo Medical Center',
        'city': 'Tokyo',
        'specialties': ['General Medicine'],
        'english_proficiency': 'Fluent'
    }
    description = generator.generate_description(provider_data)

Batch Generation (Recommended for multiple providers):
    providers = [provider_data1, provider_data2, provider_data3, ...]
    descriptions = generator.generate_batch_descriptions(providers, batch_size=5)
    
Database Integration:
    # For existing providers in database
    run_batch_ai_description_generation(provider_list, batch_size=5)
"""

import os
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

    def generate_description(self, provider_data):
        """Generate a description for a single provider using Claude."""
        provider_name = provider_data.get('provider_name', 'Unknown Provider')
        city = provider_data.get('city', 'Unknown City')
        specialties = ', '.join(provider_data.get('specialties', ['General Practitioner']))
        english_proficiency = provider_data.get('english_proficiency', 'Unknown')

        prompt = f"""
        Generate a concise and professional description for a healthcare provider.
        Provider Name: {provider_name}
        Location: {city}
        Specialties: {specialties}
        English Proficiency: {english_proficiency}
        The description should be suitable for a directory listing, highlighting the provider's services and language capabilities.
        """

        try:
            logger.info(f"Generating description for {provider_name}")
            response = self.claude.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=200,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            description = response.content[0].text.strip()
            logger.info(f"✅ Generated description for {provider_name}: {description[:50]}...")
            return description
        except Exception as e:
            logger.error(f"⚠️ Error generating description for {provider_name}: {str(e)}")
            return "Description generation failed. Please contact support."

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
        """Generate descriptions for a single batch chunk."""
        if not provider_batch:
            return []

        # Build the batch prompt with all providers
        provider_details = []
        for idx, provider_data in enumerate(provider_batch, 1):
            provider_name = provider_data.get('provider_name', 'Unknown Provider')
            city = provider_data.get('city', 'Unknown City')
            specialties = ', '.join(provider_data.get('specialties', ['General Practitioner']))
            english_proficiency = provider_data.get('english_proficiency', 'Unknown')
            
            provider_details.append(f"""
Provider {idx}:
- Name: {provider_name}
- Location: {city}
- Specialties: {specialties}
- English Proficiency: {english_proficiency}""")

        batch_prompt = f"""
Generate concise and professional descriptions for the following {len(provider_batch)} healthcare providers. Each description should be suitable for a directory listing, highlighting the provider's services and language capabilities.

{chr(10).join(provider_details)}

Please provide exactly {len(provider_batch)} descriptions, numbered 1-{len(provider_batch)}, with each description being 1-2 sentences long and professional in tone. Format your response as:

1. [Description for Provider 1]
2. [Description for Provider 2]
3. [Description for Provider 3]
...and so on.
"""

        try:
            logger.info(f"Generating batch descriptions for {len(provider_batch)} providers")
            response = self.claude.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=250 * len(provider_batch),  # Scale tokens with batch size
                temperature=0.7,
                messages=[{"role": "user", "content": batch_prompt}]
            )
            
            response_text = response.content[0].text.strip()
            descriptions = self._parse_batch_response(response_text, len(provider_batch))
            
            # Log results
            for provider_data, description in zip(provider_batch, descriptions):
                provider_name = provider_data.get('provider_name', 'Unknown Provider')
                logger.info(f"✅ Generated description for {provider_name}: {description[:50]}...")
                
            return descriptions
            
        except Exception as e:
            logger.error(f"⚠️ Error generating batch descriptions: {str(e)}")
            fallback_descriptions = ["Description generation failed. Please contact support."] * len(provider_batch)
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

def run_ai_description_generation(providers):
    """Generate descriptions for a list of provider dictionaries (single provider mode)."""
    generator = ClaudeDescriptionGenerator()
    collector = GooglePlacesHealthcareCollector()
    session = collector.Session()
    
    for provider in providers:
        provider_data = {
            'provider_name': provider.get('provider_name', 'Unknown Provider'),
            'city': provider.get('city', 'Unknown City'),
            'specialties': provider.get('specialties', ['General Practitioner']),
            'english_proficiency': provider.get('english_proficiency', 'Unknown')
        }
        description = generator.generate_description(provider_data)
        
        # Update the corresponding database record
        db_provider = session.query(Provider).filter_by(provider_name=provider_data['provider_name'], city=provider_data['city']).first()
        if db_provider:
            db_provider.ai_description = description
            db_provider.status = 'description_generated'
            session.commit()
            logger.info(f"✅ Updated {provider_data['provider_name']} with description and status")
    
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
        
    generator = ClaudeDescriptionGenerator()
    collector = GooglePlacesHealthcareCollector()
    session = collector.Session()
    
    # Prepare provider data for batch processing
    provider_data_list = []
    for provider in providers:
        provider_data = {
            'provider_name': provider.get('provider_name', 'Unknown Provider'),
            'city': provider.get('city', 'Unknown City'),
            'specialties': provider.get('specialties', ['General Practitioner']),
            'english_proficiency': provider.get('english_proficiency', 'Unknown')
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