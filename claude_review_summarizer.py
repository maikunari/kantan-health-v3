#!/usr/bin/env python3
"""
Claude Review Summarizer
Generates concise, SEO-optimized review summaries using Claude AI
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from anthropic import Anthropic
from postgres_integration import PostgresIntegration, Provider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeReviewSummarizer:
    def __init__(self):
        """Initialize Claude Review Summarizer"""
        # Load environment variables
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config', '.env')
        load_dotenv(config_path)
        
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in .env")
        
        self.claude = Anthropic(api_key=self.anthropic_api_key)
        self.db = PostgresIntegration()
        
        logger.info("ClaudeReviewSummarizer initialized successfully")
    
    def process_review_content(self, review_content: str) -> Dict[str, Any]:
        """Parse and analyze review content"""
        if not review_content:
            return {'reviews': [], 'avg_rating': 0, 'total_reviews': 0}
        
        try:
            reviews = json.loads(review_content) if isinstance(review_content, str) else review_content or []
            if not isinstance(reviews, list):
                return {'reviews': [], 'avg_rating': 0, 'total_reviews': 0}
            
            # Calculate basic stats
            avg_rating = sum(r.get('rating', 0) for r in reviews) / len(reviews) if reviews else 0
            
            return {
                'reviews': reviews,
                'avg_rating': round(avg_rating, 1),
                'total_reviews': len(reviews)
            }
        except Exception as e:
            logger.error(f"Error processing review content: {str(e)}")
            return {'reviews': [], 'avg_rating': 0, 'total_reviews': 0}
    
    def generate_review_summary(self, provider: Provider) -> str:
        """Generate an 80-100 word narrative paragraph summary of Google reviews"""
        review_data = self.process_review_content(provider.review_content or '')
        reviews = review_data['reviews']
        
        if not reviews:
            return "No patient reviews available for this healthcare provider."
        
        # Prepare review texts for Claude
        review_texts = []
        for review in reviews:
            text = review.get('text', '').strip()
            rating = review.get('rating', 0)
            if text and len(text) > 10:  # Filter out very short reviews
                review_texts.append(f"Rating {rating}/5: {text}")
        
        if not review_texts:
            return "Limited patient feedback available for this healthcare provider."
        
        # Create Claude prompt for narrative paragraph
        prompt = f"""Analyze these patient reviews for {provider.provider_name} and write a professional, well-structured paragraph (80-100 words) that summarizes the overall patient experience. Write it as a cohesive narrative that would fit naturally in a healthcare directory listing.

Provider: {provider.provider_name}
Location: {provider.city}, {provider.prefecture}
Specialty: {', '.join(provider.specialties) if provider.specialties else 'General Medicine'}
Average Rating: {review_data['avg_rating']}/5 ({review_data['total_reviews']} reviews)

Patient Reviews:
{chr(10).join(review_texts[:10])}

Write a paragraph that:
- Starts with what patients consistently praise about this provider
- Mentions facility quality, staff attributes, and care quality
- Includes any English language support if mentioned
- Flows naturally as a single cohesive paragraph
- Is 80-100 words in professional, marketing-friendly tone
- Avoids bullet points or semicolons - write as flowing prose

Example style: "Patients consistently praise [Provider] for its comprehensive approach to healthcare. The clinic's modern facilities and professional staff create a welcoming environment that puts patients at ease. Reviews frequently highlight the thorough medical care and attention to detail, with many noting the staff's exceptional communication skills and willingness to accommodate international patients. The combination of skilled healthcare professionals and patient-centered service has earned strong satisfaction ratings, making it a trusted choice for both routine and specialized medical care in [Location]."""

        try:
            response = self.claude.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                system="You are a healthcare marketing expert specializing in patient review analysis. Create concise, professional summaries that highlight key patient feedback themes for SEO and marketing purposes.",
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
            
            # Ensure it's within word count (allow up to 100 words as intended)
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
            
            logger.info(f"Generated summary for {provider.provider_name}: {len(words)} words")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating Claude summary for {provider.provider_name}: {str(e)}")
            # Fallback to basic summary
            return self._generate_fallback_summary(reviews, provider)
    
    def _generate_fallback_summary(self, reviews: List[Dict], provider: Provider) -> str:
        """Generate a basic fallback summary if Claude fails"""
        themes = []
        
        # Analyze reviews for common themes
        positive_reviews = [r for r in reviews if r.get('rating', 0) >= 4]
        
        theme_keywords = {
            'professional service': ['professional', 'excellent', 'skilled', 'experienced'],
            'clean facilities': ['clean', 'modern', 'nice facilities', 'comfortable'],
            'friendly staff': ['friendly', 'kind', 'helpful', 'welcoming'],
            'English support': ['english', 'bilingual', 'speak english'],
            'thorough care': ['thorough', 'detailed', 'careful', 'comprehensive'],
            'convenient location': ['convenient', 'easy access', 'near station']
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in ' '.join([r.get('text', '').lower() for r in positive_reviews]) 
                   for keyword in keywords):
                themes.append(theme.title())
        
        if themes:
            return '; '.join(themes[:3])  # Limit to 3 themes
        else:
            return f"Healthcare services with {provider.rating:.1f}/5 rating from {len(reviews)} patients"
    
    def update_provider_summaries(self, providers: List[Provider], batch_size: int = 10) -> Dict[str, int]:
        """Update multiple providers with Claude-generated review summaries"""
        
        if not providers:
            logger.warning("No providers to update")
            return {'updated': 0, 'errors': 0, 'skipped': 0}
        
        logger.info(f"🚀 Starting review summary generation for {len(providers)} providers")
        
        updated_count = 0
        error_count = 0
        skipped_count = 0
        
        for i, provider in enumerate(providers, 1):
            session = self.db.Session()  # Create new session for each provider
            
            try:
                logger.info(f"📝 Processing {i}/{len(providers)}: {provider.provider_name}")
                
                # Check if provider has reviews
                review_data = self.process_review_content(provider.review_content or '')
                if not review_data['reviews']:
                    logger.info(f"⏭️ Skipping {provider.provider_name} - no reviews")
                    skipped_count += 1
                    session.close()
                    continue
                
                # Generate summary
                summary = self.generate_review_summary(provider)
                
                # Update provider in database with narrative summary
                provider_in_session = session.merge(provider)  # Merge provider into current session
                provider_in_session.review_summary = summary  # Store narrative paragraph directly as text
                
                # Commit immediately for each provider
                session.commit()
                
                logger.info(f"✅ Updated {provider.provider_name}")
                logger.info(f"   Summary: {summary}")
                
                updated_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error processing {provider.provider_name}: {str(e)}")
                session.rollback()
                error_count += 1
            finally:
                session.close()
        
        logger.info(f"📊 Summary generation complete:")
        logger.info(f"   ✅ Updated: {updated_count}")
        logger.info(f"   ❌ Errors: {error_count}")
        logger.info(f"   ⏭️ Skipped: {skipped_count}")
        
        return {
            'updated': updated_count,
            'errors': error_count,
            'skipped': skipped_count
        }

def main():
    """Main function for testing and running review summarization"""
    print("🤖 CLAUDE REVIEW SUMMARIZER")
    print("=" * 50)
    
    try:
        summarizer = ClaudeReviewSummarizer()
        
        # Get providers with reviews
        session = summarizer.db.Session()
        providers_with_reviews = []
        
        all_providers = session.query(Provider).filter(Provider.total_reviews > 0).all()
        
        for provider in all_providers:
            review_data = summarizer.process_review_content(provider.review_content or '')
            if review_data['reviews']:
                providers_with_reviews.append(provider)
        
        session.close()
        
        print(f"📊 Found {len(providers_with_reviews)} providers with review content")
        
        if providers_with_reviews:
            # Process all providers - narrative paragraphs are working perfectly
            test_limit = None  # Process all providers
            providers_to_process = providers_with_reviews[:test_limit] if test_limit else providers_with_reviews
            
            print(f"🚀 Processing {len(providers_to_process)} providers...")
            
            results = summarizer.update_provider_summaries(providers_to_process)
            
            print(f"\n🎉 RESULTS:")
            print(f"   ✅ Successfully updated: {results['updated']}")
            print(f"   ❌ Errors: {results['errors']}")
            print(f"   ⏭️ Skipped: {results['skipped']}")
        else:
            print("⚠️ No providers with reviews found")
            
    except Exception as e:
        logger.error(f"❌ Error in main execution: {str(e)}")

if __name__ == "__main__":
    main() 