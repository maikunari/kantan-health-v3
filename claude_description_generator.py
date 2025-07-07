#!/usr/bin/env python3
"""
AI Description Generator Module
Generates AI-powered descriptions for healthcare providers using Anthropic.
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
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
        load_dotenv(config_path)
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.anthropic_api_key:
            logger.error("ANTHROPIC_API_KEY not found in .env")
            raise ValueError("ANTHROPIC_API_KEY not found in .env")
        self.claude = Anthropic(api_key=self.anthropic_api_key)
        logger.info("ClaudeDescriptionGenerator initialized successfully")

    def generate_description(self, provider_data):
        """Generate a description for a provider using Claude."""
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

def run_ai_description_generation(providers):
    """Generate descriptions for a list of provider dictionaries."""
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