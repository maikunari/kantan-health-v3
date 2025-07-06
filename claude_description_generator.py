#!/usr/bin/env python3
"""
Claude Description Generator
Generates AI descriptions for healthcare providers using Claude and stores them in PostgreSQL.
Formats descriptions with HTML (intro, bullet points, user insights, closing) for WordPress.
"""

import anthropic
import json
from typing import Dict, List
import time
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from postgres_integration import PostgresIntegration, Provider

# Load environment variables from config/.env file
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', '.env')
load_dotenv(config_path)

class ClaudeDescriptionGenerator:
    def __init__(self):
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        
        # PostgreSQL setup
        self.engine = create_engine(f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:5432/directory")
        self.Session = sessionmaker(bind=self.engine)
    
    def generate_clinic_description(self, provider_data: Dict) -> str:
        """Generate a personalized clinic description with user insights using Claude"""
        
        # Extract key data points
        name = provider_data.get('provider_name', '')
        city = provider_data.get('city', '')
        rating = provider_data.get('rating', 0)
        total_reviews = provider_data.get('total_reviews', 0)
        english_indicators = provider_data.get('english_indicators', [])
        proficiency_score = provider_data.get('proficiency_score', 0)
        amenities = provider_data.get('amenities', [])
        nearest_station = provider_data.get('nearest_station', 'Not available')
        
        # Parse review keywords and content
        review_keywords = json.loads(provider_data.get('review_keywords', '{}'))
        review_content = json.loads(provider_data.get('review_content', '[]'))
        
        # Get top keywords for context
        top_keywords = list(review_keywords.keys())[:8] if review_keywords else []
        
        # Extract sample review quote
        positive_quote = ""
        for review in review_content[:3]:
            if review.get('rating', 0) >= 4:
                positive_quote = review.get('text', '')[:100]
                break
        
        # Build the prompt
        prompt = f"""Write a compelling, natural-sounding description for {name}, a healthcare provider in {city}, Japan, in 150–200 words. Structure it as:
- An introductory sentence summarizing the provider (name, city, rating).
- 3–4 bullet points highlighting key features (e.g., English support, specialties, amenities, location).
- 3 user insights from reviews (one sentence each, balanced, covering staff, facilities, or accessibility).
- A closing sentence with a practical note about booking or visiting.

Key Information:
- Rating: {rating}/5 stars ({total_reviews} reviews)
- English Support Level: {proficiency_score}/100
- English Indicators: {', '.join(english_indicators) if english_indicators else 'None specified'}
- Popular Keywords: {', '.join(top_keywords)}
- Amenities: {', '.join(amenities) if amenities else 'Standard facilities'}
- Nearest Station: {nearest_station}

Sample Patient Feedback:
- "{positive_quote}" (if available)

Requirements:
- Use a conversational tone, not marketing-heavy.
- Highlight English language support if evidence exists.
- Ensure user insights are balanced (e.g., positive with neutral framing of challenges).
- Avoid superlatives unless backed by data.
- Use plain text with line breaks for structure (intro, features, insights, closing).
- Focus on what makes this clinic unique based on the data provided."""

        try:
            # Call Claude
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=400,
                temperature=0.7,
                messages=[{
                    "role": "user", 
                    "content": prompt
                }]
            )
            
            # Get plain text response
            description = response.content[0].text.strip()
            
            # Basic quality check
            if len(description) < 50:
                fallback = f"{name} is a healthcare provider in {city}, Japan, serving both local and international patients with a {rating}/5 rating."
                return f"<p>{fallback}</p>"
            
            # Format as HTML
            lines = description.split('\n')
            formatted = "<p>" + lines[0] + "</p>\n<ul>\n"
            bullet_count = 0
            insight_count = 0
            for line in lines[1:]:
                if line.strip().startswith('-') and bullet_count < 4 and insight_count == 0:
                    formatted += f"<li>{line.strip()[2:].strip()}</li>\n"
                    bullet_count += 1
                elif line.strip().startswith('-') and bullet_count >= 4 and insight_count < 3:
                    if insight_count == 0:
                        formatted += "</ul>\n<h3>User Insights</h3>\n<ul>\n"
                    formatted += f"<li>{line.strip()[2:].strip()}</li>\n"
                    insight_count += 1
                else:
                    formatted += "</ul>\n<p>" + line.strip() + "</p>"
                    break
            formatted += "</ul>" if insight_count > 0 and insight_count < len(lines[1:]) else ""
            
            return formatted
            
        except Exception as e:
            print(f"Error generating description for {name}: {e}")
            # Fallback description
            fallback = f"{name} is a healthcare provider in {city}, Japan, serving both local and international patients with a {rating}/5 rating."
            return f"<p>{fallback}</p>"
    
    def process_providers_batch(self, limit: int = 10) -> Dict:
        """Process a batch of providers without AI descriptions"""
        
        # Get providers without AI descriptions
        session = self.Session()
        providers = session.query(Provider).filter(Provider.ai_description == '').limit(limit).all()
        session.close()
        
        results = {
            'processed': 0,
            'errors': 0,
            'skipped': 0
        }
        
        for provider in providers:
            provider_data = {
                'provider_name': provider.provider_name,
                'city': provider.city,
                'rating': provider.rating,
                'total_reviews': provider.total_reviews,
                'english_indicators': provider.english_indicators,
                'proficiency_score': provider.proficiency_score,
                'amenities': provider.amenities,
                'review_keywords': provider.review_keywords,
                'review_content': provider.review_content,
                'nearest_station': provider.nearest_station
            }
            provider_name = provider_data.get('provider_name', 'Unknown')
            
            try:
                print(f"🤖 Generating description for: {provider_name}")
                
                # Generate description
                description = self.generate_clinic_description(provider_data)
                
                # Update PostgreSQL record
                session = self.Session()
                provider.ai_description = description
                session.commit()
                session.close()
                
                results['processed'] += 1
                print(f"✅ Updated: {provider_name}")
                
                # Rate limiting for Claude API
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error processing {provider_name}: {e}")
                results['errors'] += 1
                continue
        
        return results
    
    def process_all_providers(self):
        """Process all providers in batches"""
        print("🚀 Starting AI description generation for all providers...")
        
        total_results = {'processed': 0, 'errors': 0, 'skipped': 0}
        batch_size = 10
        
        while True:
            print(f"\n📦 Processing next batch of {batch_size} providers...")
            batch_results = self.process_providers_batch(batch_size)
            
            # Update totals
            for key in total_results:
                total_results[key] += batch_results[key]
            
            print(f"Batch results: {batch_results}")
            
            # If no providers were processed, we're done
            if batch_results['processed'] == 0:
                break
            
            # Brief pause between batches
            time.sleep(5)
        
        print(f"\n🎉 AI Description Generation Complete!")
        print(f"📊 Final Results: {total_results}")
        return total_results

def main():
    """Run the description generator"""
    generator = ClaudeDescriptionGenerator()
    
    # Process all providers
    results = generator.process_all_providers()
    
    print(f"\n✨ Generated {results['processed']} AI descriptions!")
    if results['errors'] > 0:
        print(f"⚠️ {results['errors']} errors encountered")

if __name__ == "__main__":
    main()