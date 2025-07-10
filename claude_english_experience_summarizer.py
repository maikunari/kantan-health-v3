#!/usr/bin/env python3
"""
Claude English Experience Summarizer
Generates AI-powered summaries focused on English language support and communication experiences from patient reviews.
"""

import os
import json
import re
import logging
from typing import Dict, List, Any
from dotenv import load_dotenv
import anthropic
from postgres_integration import PostgresIntegration, Provider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeEnglishExperienceSummarizer:
    """Generate English language experience summaries from patient reviews using Claude AI"""
    
    def __init__(self):
        """Initialize Claude API and database connections"""
        # Load environment variables
        config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
        load_dotenv(config_path)
        
        # Initialize Claude
        claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not claude_api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.claude = anthropic.Anthropic(api_key=claude_api_key)
        
        # Initialize database
        self.db = PostgresIntegration()
        
        logger.info("✅ Claude English Experience Summarizer initialized")
    
    def process_review_content(self, review_content: str) -> Dict[str, Any]:
        """Extract and process review data, filtering for English-related mentions"""
        try:
            if not review_content:
                return {'reviews': [], 'avg_rating': 0, 'total_reviews': 0, 'english_mentions': []}
            
            reviews = json.loads(review_content) if isinstance(review_content, str) else review_content
            
            if not isinstance(reviews, list):
                return {'reviews': [], 'avg_rating': 0, 'total_reviews': 0, 'english_mentions': []}
            
            # Filter for reviews that mention English language support
            english_related_reviews = []
            english_keywords = [
                'english', 'speak english', 'english speaker', 'english speaking', 'bilingual',
                'translator', 'translation', 'interpret', 'language', 'communicate', 'foreign',
                'international', 'expat', 'traveler', 'tourist', 'native english', 'fluent english'
            ]
            
            for review in reviews:
                if not isinstance(review, dict):
                    continue
                    
                text = review.get('text', '').lower()
                rating = review.get('rating', 0)
                
                # Check if review mentions English/language support
                has_english_mention = any(keyword in text for keyword in english_keywords)
                
                if has_english_mention and text and len(text) > 10:
                    english_related_reviews.append({
                        'text': review.get('text', ''),
                        'rating': rating,
                        'author': review.get('author', ''),
                        'date': review.get('date', '')
                    })
            
            if english_related_reviews:
                avg_rating = sum(r['rating'] for r in english_related_reviews if r['rating']) / len(english_related_reviews)
            else:
                avg_rating = 0
            
            return {
                'reviews': english_related_reviews,
                'avg_rating': round(avg_rating, 1),
                'total_reviews': len(english_related_reviews),
                'english_mentions': [r['text'] for r in english_related_reviews]
            }
            
        except Exception as e:
            logger.error(f"Error processing review content: {str(e)}")
            return {'reviews': [], 'avg_rating': 0, 'total_reviews': 0, 'english_mentions': []}
    
    def generate_english_experience_summary(self, provider: Provider) -> str:
        """Generate an 80-100 word summary focused on English language experience"""
        review_data = self.process_review_content(provider.review_content or '')
        english_reviews = review_data['reviews']
        
        if not english_reviews:
            # If no English-specific mentions, create a generic summary based on proficiency
            proficiency = provider.english_proficiency or 'Unknown'
            if proficiency != 'Unknown' and proficiency != 'No English':
                return f"This healthcare provider offers {proficiency.lower()} English language support for international patients. The clinic accommodates English-speaking visitors and provides communication assistance as needed. Staff members work to ensure clear understanding of medical procedures and treatments for foreign patients seeking healthcare services in Japan."
            else:
                return "English language support information not available from patient reviews. International patients may wish to inquire about translation services or English-speaking staff when making appointments."
        
        # Prepare English-focused review texts for Claude
        english_texts = []
        for review in english_reviews:
            text = review.get('text', '').strip()
            rating = review.get('rating', 0)
            if text:
                english_texts.append(f"Rating {rating}/5: {text}")
        
        # Create Claude prompt focused on English language experience
        prompt = f"""Analyze these patient reviews for {provider.provider_name} and write a professional paragraph (80-100 words) that specifically focuses on the English language support and communication experience for international patients.

Provider: {provider.provider_name}
Location: {provider.city}, {provider.prefecture}
English Proficiency Level: {provider.english_proficiency or 'Not specified'}
Reviews mentioning English/language support:

{chr(10).join(english_texts[:8])}

Write a paragraph that:
- Focuses specifically on English language support and communication
- Mentions staff English abilities, translation services, or communication assistance
- Describes the experience for international/English-speaking patients
- Includes any specific details about doctors, nurses, or staff language skills
- Flows as a cohesive paragraph about the English language experience
- Is 80-100 words in professional, informative tone
- Avoids generic healthcare descriptions - focus on language/communication aspects

Example style: "International patients consistently praise [Provider] for its excellent English language support. Reviews highlight that staff members, including doctors and nurses, communicate fluently in English and provide clear explanations of medical procedures. The clinic accommodates foreign visitors with English forms and translation assistance when needed. Patients note the staff's patience in overcoming language barriers and their ability to make international patients feel comfortable and well-informed throughout their healthcare experience."

Focus only on English language and communication aspects from the reviews."""

        try:
            response = self.claude.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                system="You are a healthcare communication specialist focusing on English language support analysis. Create summaries that highlight language and communication experiences for international patients.",
                messages=[{
                    "role": "user", 
                    "content": prompt
                }]
            )
            
            summary = response.content[0].text.strip()
            
            # Clean up the summary
            summary = summary.replace('"', '').replace("'", '')
            if summary.startswith('Summary:') or summary.startswith('summary:'):
                summary = summary.split(':', 1)[1].strip()
            
            # Ensure it's within word count (allow up to 100 words)
            words = summary.split()
            if len(words) > 100:
                # Try to end on a complete sentence within 100 words
                truncated = ' '.join(words[:100])
                # Find the last sentence ending
                last_period = truncated.rfind('.')
                if last_period > len(truncated) * 0.7:  # Only if we're not cutting too much
                    summary = truncated[:last_period + 1]
                else:
                    summary = truncated
            
            logger.info(f"Generated English experience summary for {provider.provider_name}: {len(words)} words")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating Claude summary for {provider.provider_name}: {str(e)}")
            # Fallback to basic summary
            return self._generate_fallback_english_summary(english_reviews, provider)
    
    def _generate_fallback_english_summary(self, reviews: List[Dict], provider: Provider) -> str:
        """Generate a basic fallback English experience summary if Claude fails"""
        if not reviews:
            proficiency = provider.english_proficiency or 'Unknown'
            if proficiency != 'Unknown':
                return f"Provider offers {proficiency.lower()} English language support for international patients."
            else:
                return "English language support information not available from patient reviews."
        
        # Analyze for English-related themes
        english_themes = []
        all_text = ' '.join([r.get('text', '').lower() for r in reviews])
        
        theme_indicators = {
            'staff speak English': ['staff speak english', 'english speaking staff', 'staff could speak english'],
            'fluent communication': ['fluent', 'clear communication', 'communicate well'],
            'translation services': ['translator', 'translation', 'interpret'],
            'helpful for foreigners': ['foreigner', 'international', 'foreign patient', 'expat'],
            'native English speaker': ['native english', 'native speaker'],
            'bilingual support': ['bilingual', 'speak both', 'japanese and english']
        }
        
        for theme, keywords in theme_indicators.items():
            if any(keyword in all_text for keyword in keywords):
                english_themes.append(theme)
        
        if english_themes:
            themes_text = ', '.join(english_themes[:3])
            return f"International patients report positive English language experiences including: {themes_text}. The healthcare provider accommodates English-speaking patients with appropriate communication support."
        else:
            return f"English language support mentioned in patient reviews with {len(reviews)} positive mentions from international patients."
    
    def update_provider_english_summaries(self, providers: List[Provider], batch_size: int = 10) -> Dict[str, int]:
        """Update multiple providers with Claude-generated English experience summaries"""
        
        if not providers:
            logger.warning("No providers to update")
            return {'updated': 0, 'errors': 0, 'skipped': 0}
        
        logger.info(f"🚀 Starting English experience summary generation for {len(providers)} providers")
        
        updated_count = 0
        error_count = 0
        skipped_count = 0
        
        for i, provider in enumerate(providers, 1):
            session = self.db.Session()  # Create new session for each provider
            
            try:
                logger.info(f"📝 Processing {i}/{len(providers)}: {provider.provider_name}")
                
                # Generate English experience summary
                summary = self.generate_english_experience_summary(provider)
                
                # Update provider in database
                provider_in_session = session.merge(provider)  # Merge provider into current session
                provider_in_session.english_experience_summary = summary
                
                # Commit immediately for each provider
                session.commit()
                
                logger.info(f"✅ Updated {provider.provider_name}")
                logger.info(f"   English Summary: {summary}")
                
                updated_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error processing {provider.provider_name}: {str(e)}")
                session.rollback()
                error_count += 1
            finally:
                session.close()
        
        logger.info(f"📊 English experience summary generation complete:")
        logger.info(f"   ✅ Updated: {updated_count}")
        logger.info(f"   ❌ Errors: {error_count}")
        logger.info(f"   ⏭️ Skipped: {skipped_count}")
        
        return {
            'updated': updated_count,
            'errors': error_count,
            'skipped': skipped_count
        }

def main():
    """Main function for testing and running English experience summarization"""
    print("🌐 CLAUDE ENGLISH EXPERIENCE SUMMARIZER")
    print("=" * 60)
    
    try:
        summarizer = ClaudeEnglishExperienceSummarizer()
        
        # Get all providers
        session = summarizer.db.Session()
        all_providers = session.query(Provider).all()
        session.close()
        
        print(f"📊 Found {len(all_providers)} total providers")
        
        if all_providers:
            # Process all providers
            results = summarizer.update_provider_english_summaries(all_providers)
            
            print(f"\n🎉 RESULTS:")
            print(f"   ✅ Successfully updated: {results['updated']}")
            print(f"   ❌ Errors: {results['errors']}")
            print(f"   ⏭️ Skipped: {results['skipped']}")
        else:
            print("❌ No providers found")
            
    except Exception as e:
        logger.error(f"❌ Error in main execution: {str(e)}")
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main() 