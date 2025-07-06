#!/usr/bin/env python3
"""
Claude Description Generator
Generates AI-powered descriptions for healthcare providers using Anthropic's API.
"""

import os
import json
from dotenv import load_dotenv
import anthropic
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from postgres_integration import Provider

class ClaudeDescriptionGenerator:
    def __init__(self):
        # Load environment variables
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env'))
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        self.engine = create_engine(f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:5432/directory")
        self.Session = sessionmaker(bind=self.engine)

    def generate_description(self, provider_data):
        """Generate a 150-200 word description with 3 user insights"""
        prompt = f"""
        You are an AI assistant creating a professional description for a healthcare provider. 
        Based on the following data, write a 150-200 word description in HTML format, including 3 balanced user insights (positive, neutral, mixed). 
        Data: {json.dumps(provider_data, ensure_ascii=False)}
        Ensure the tone is informative and welcoming for English-speaking expats and tourists in Japan.
        """
        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        description = response.content[0].text
        return description

    def process_all_providers(self):
        """Process all pending providers and generate descriptions"""
        session = self.Session()
        providers = session.query(Provider).filter_by(status="pending").all()
        results = {"processed": 0, "errors": 0}
        
        for provider in providers:
            try:
                description = self.generate_description({
                    "name": provider.provider_name,
                    "address": provider.address,
                    "city": provider.city,
                    "phone": provider.phone,
                    "website": provider.website,
                    "specialties": provider.specialties,
                    "rating": provider.rating,
                    "total_reviews": provider.total_reviews,
                    "english_proficiency": provider.english_proficiency
                })
                provider.ai_description = description
                provider.status = "description_generated"
                session.commit()
                results["processed"] += 1
            except Exception as e:
                print(f"❌ Error generating description for {provider.provider_name}: {str(e)}")
                results["errors"] += 1
                session.rollback()
        
        session.close()
        return results

if __name__ == "__main__":
    generator = ClaudeDescriptionGenerator()
    results = generator.process_all_providers()
    print(f"Processed: {results['processed']}, Errors: {results['errors']}")