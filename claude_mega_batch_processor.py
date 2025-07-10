#!/usr/bin/env python3
"""
Claude Mega-Batch Content Processor
Generates all AI content types (descriptions, excerpts, review summaries, English summaries) 
in a single API call per batch for maximum efficiency.

Usage:
    processor = ClaudeMegaBatchProcessor()
    results = processor.process_providers_batch(providers, batch_size=4)
    processor.update_database_with_results(providers, results)
"""

import os
import json
import re
import logging
from typing import Dict, List, Any, Optional, NamedTuple
from dotenv import load_dotenv
from anthropic import Anthropic
from postgres_integration import PostgresIntegration, Provider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentResult(NamedTuple):
    """Container for all content types generated for a provider"""
    description: str
    excerpt: str
    review_summary: str
    english_experience_summary: str

class ClaudeMegaBatchProcessor:
    """Generate all AI content types in optimized mega-batches"""
    
    def __init__(self):
        """Initialize Claude API and database connections"""
        # Load environment variables
        config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
        load_dotenv(config_path)
        
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in .env")
        
        # Use latest Sonnet model for all content
        self.claude = Anthropic(api_key=self.anthropic_api_key)
        self.model = "claude-3-5-sonnet-20241022"
        
        # Initialize database
        self.db = PostgresIntegration()
        
        logger.info(f"✅ Claude Mega-Batch Processor initialized with {self.model}")
    
    def process_review_content(self, review_content: str) -> Dict[str, Any]:
        """Extract and process review data for content generation"""
        if not review_content:
            return {
                'reviews': [],
                'avg_rating': 0,
                'total_reviews': 0,
                'positive_themes': [],
                'english_mentions': []
            }
        
        try:
            reviews = json.loads(review_content) if isinstance(review_content, str) else review_content
            
            if not isinstance(reviews, list):
                return {
                    'reviews': reviews,
                    'avg_rating': 0,
                    'total_reviews': 0,
                    'positive_themes': [],
                    'english_mentions': []
                }
            
            # Calculate statistics
            avg_rating = sum(r.get('rating', 0) for r in reviews) / len(reviews) if reviews else 0
            
            # Extract positive themes
            positive_themes = []
            english_mentions = []
            
            for review in reviews:
                text = review.get('text', '').lower()
                if not text:
                    continue
                
                # Positive themes (4+ star reviews)
                if review.get('rating', 0) >= 4:
                    if any(word in text for word in ['professional', 'excellent', 'skilled']):
                        positive_themes.append('professional service')
                    if any(word in text for word in ['clean', 'modern', 'comfortable']):
                        positive_themes.append('clean facilities')
                    if any(word in text for word in ['friendly', 'kind', 'helpful']):
                        positive_themes.append('friendly staff')
                    if any(word in text for word in ['quick', 'efficient', 'no wait']):
                        positive_themes.append('efficient service')
                
                # English language mentions
                if any(word in text for word in ['english', 'bilingual', 'speak english', 'foreign', 'international']):
                    english_mentions.append(review.get('text', ''))
            
            return {
                'reviews': reviews,
                'avg_rating': round(avg_rating, 1),
                'total_reviews': len(reviews),
                'positive_themes': list(set(positive_themes))[:4],
                'english_mentions': english_mentions[:3]
            }
            
        except Exception as e:
            logger.error(f"Error processing review content: {str(e)}")
            return {
                'reviews': [],
                'avg_rating': 0,
                'total_reviews': 0,
                'positive_themes': [],
                'english_mentions': []
            }
    
    def generate_mega_batch_content(self, provider_batch: List[Any], batch_size: int = 4) -> List[ContentResult]:
        """Generate all content types for a batch of providers in a single API call"""
        if not provider_batch:
            return []
        
        logger.info(f"🚀 Generating mega-batch content for {len(provider_batch)} providers")
        
        # Prepare comprehensive provider data
        provider_details = []
        for idx, provider_data in enumerate(provider_batch, 1):
            # Handle both Provider objects and dictionaries
            if hasattr(provider_data, '__dict__'):
                # Provider object from database
                provider_name = getattr(provider_data, 'provider_name', 'Unknown Provider')
                city = getattr(provider_data, 'city', 'Unknown City')
                prefecture = getattr(provider_data, 'prefecture', '')
                district = getattr(provider_data, 'district', '')
                specialties = getattr(provider_data, 'specialties', ['General Medicine'])
                english_proficiency = getattr(provider_data, 'english_proficiency', 'Unknown')
                rating = getattr(provider_data, 'rating', 0)
                total_reviews = getattr(provider_data, 'total_reviews', 0)
                review_content = getattr(provider_data, 'review_content', '')
                wheelchair_accessible = getattr(provider_data, 'wheelchair_accessible', False)
                parking_available = getattr(provider_data, 'parking_available', False)
            else:
                # Dictionary input
                provider_name = provider_data.get('provider_name', 'Unknown Provider')
                city = provider_data.get('city', 'Unknown City')
                prefecture = provider_data.get('prefecture', '')
                district = provider_data.get('district', '')
                specialties = provider_data.get('specialties', ['General Medicine'])
                english_proficiency = provider_data.get('english_proficiency', 'Unknown')
                rating = provider_data.get('rating', 0)
                total_reviews = provider_data.get('total_reviews', 0)
                review_content = provider_data.get('review_content', '')
                wheelchair_accessible = provider_data.get('wheelchair_accessible', False)
                parking_available = provider_data.get('parking_available', False)
            
            # Process review data
            review_insights = self.process_review_content(review_content)
            
            # Format specialties
            if isinstance(specialties, list):
                specialty_text = ', '.join(specialties) if specialties else 'General Medicine'
            else:
                specialty_text = specialties
            
            # Format location
            location_parts = []
            if district:
                location_parts.append(district)
            location_parts.append(city)
            if prefecture and prefecture != city:
                location_parts.append(prefecture)
            location_text = ', '.join(filter(None, location_parts))
            
            # Format review texts for analysis
            review_texts = []
            if review_insights['reviews']:
                for review in review_insights['reviews'][:8]:  # Limit to avoid token overflow
                    text = review.get('text', '').strip()
                    rating_val = review.get('rating', 0)
                    if text and len(text) > 20:
                        review_texts.append(f"Rating {rating_val}/5: {text}")
            
            provider_details.append(f"""
Provider {idx}: {provider_name}
- Location: {location_text}
- Specialties: {specialty_text}
- English Support: {english_proficiency}
- Patient Rating: {rating}/5 stars ({total_reviews} reviews)
- Positive Themes: {', '.join(review_insights['positive_themes']) if review_insights['positive_themes'] else 'Professional healthcare'}
- English Mentions: {len(review_insights['english_mentions'])} reviews mention English support
- Accessibility: {'Wheelchair accessible' if wheelchair_accessible else 'Accessibility not specified'}
- Parking: {'Parking available' if parking_available else 'Parking not specified'}

Patient Reviews Sample:
{chr(10).join(review_texts[:5]) if review_texts else 'Limited review content available'}""")

        # Create comprehensive mega-batch prompt
        mega_prompt = f"""Generate ALL FOUR content types for these {len(provider_batch)} healthcare providers. Each provider needs exactly 4 pieces of content with precise formatting.

{chr(10).join(provider_details)}

CRITICAL: Generate exactly {len(provider_batch)} complete sets of content. For each provider, create ALL FOUR content types in this EXACT format:

PROVIDER [NUMBER]:

DESCRIPTION:
[150-175 word description in exactly 2 paragraphs separated by a blank line. First paragraph: medical services and English support. Second paragraph: patient experience and practical details]

EXCERPT:
[50-75 word concise summary highlighting key strengths and location]

REVIEW_SUMMARY:
[80-100 word narrative paragraph summarizing patient experiences, focusing on what patients consistently praise]

ENGLISH_SUMMARY:
[80-100 word paragraph specifically about English language support and communication experience for international patients]

FORMATTING REQUIREMENTS:
1. DESCRIPTION: Exactly 2 paragraphs, 150-175 words total
2. EXCERPT: Single paragraph, 50-75 words 
3. REVIEW_SUMMARY: Single narrative paragraph, 80-100 words
4. ENGLISH_SUMMARY: Single paragraph about language support, 80-100 words

Content Guidelines:
- Professional, informative tone throughout
- Use specific patient feedback when available
- Mention English proficiency levels accurately
- Include location context (district, city, prefecture)
- Focus on patient experience and medical quality
- Avoid phone numbers or website URLs
- Make each content type distinct but complementary

Example Structure:
PROVIDER 1:

DESCRIPTION:
[First paragraph about medical services and English support...]

[Second paragraph about patient experience and convenience...]

EXCERPT:
[Concise overview highlighting main strengths...]

REVIEW_SUMMARY:
[Narrative about what patients consistently praise...]

ENGLISH_SUMMARY:
[Specific details about English language support and international patient experience...]

Generate content for all {len(provider_batch)} providers following this exact format."""

        try:
            response = self.claude.messages.create(
                model=self.model,
                max_tokens=min(8000, 2000 * len(provider_batch)),  # Stay under 8192 limit while optimizing for quality
                temperature=0.6,
                system="You are a professional healthcare content specialist. Generate comprehensive, accurate content that helps international patients find quality healthcare providers. Focus on clarity, professionalism, and specific patient benefits.",
                messages=[{"role": "user", "content": mega_prompt}]
            )
            
            response_text = response.content[0].text.strip()
            logger.info(f"📝 Raw Claude response received ({len(response_text)} chars)")
            
            # Parse the mega-batch response
            parsed_results = self._parse_mega_batch_response(response_text, len(provider_batch))
            
            # Log results
            for i, result in enumerate(parsed_results):
                provider_name = provider_batch[i].provider_name if hasattr(provider_batch[i], 'provider_name') else provider_batch[i].get('provider_name', f'Provider {i+1}')
                desc_words = len(result.description.split())
                excerpt_words = len(result.excerpt.split())
                review_words = len(result.review_summary.split())
                english_words = len(result.english_experience_summary.split())
                
                logger.info(f"✅ Generated complete content for {provider_name}:")
                logger.info(f"   📄 Description: {desc_words} words")
                logger.info(f"   📝 Excerpt: {excerpt_words} words") 
                logger.info(f"   ⭐ Review Summary: {review_words} words")
                logger.info(f"   🗣️ English Summary: {english_words} words")
            
            return parsed_results
            
        except Exception as e:
            logger.error(f"❌ Error generating mega-batch content: {str(e)}")
            # Return fallback content for all providers
            return [ContentResult(
                description="Professional healthcare provider offering quality medical services. Please contact directly for more information.",
                excerpt="Healthcare provider offering medical services.",
                review_summary="Healthcare provider with patient care services.",
                english_experience_summary="English language support may be available. Please inquire when making appointments."
            )] * len(provider_batch)
    
    def _parse_mega_batch_response(self, response_text: str, expected_count: int) -> List[ContentResult]:
        """Parse the mega-batch response to extract all content types for each provider"""
        results = []
        
        logger.info(f"🔍 Parsing mega-batch response for {expected_count} providers")
        
        # Split by PROVIDER sections
        provider_sections = re.split(r'\bPROVIDER\s+\d+:', response_text)
        
        # Remove empty first section
        if provider_sections and not provider_sections[0].strip():
            provider_sections = provider_sections[1:]
        
        logger.info(f"📊 Found {len(provider_sections)} provider sections")
        
        for i, section in enumerate(provider_sections[:expected_count]):
            try:
                # Extract each content type using regex
                description_match = re.search(r'DESCRIPTION:\s*\n(.*?)(?=EXCERPT:|$)', section, re.DOTALL)
                excerpt_match = re.search(r'EXCERPT:\s*\n(.*?)(?=REVIEW_SUMMARY:|$)', section, re.DOTALL)
                review_match = re.search(r'REVIEW_SUMMARY:\s*\n(.*?)(?=ENGLISH_SUMMARY:|$)', section, re.DOTALL)
                english_match = re.search(r'ENGLISH_SUMMARY:\s*\n(.*?)(?=PROVIDER\s+\d+:|$)', section, re.DOTALL)
                
                # Extract and clean content
                description = description_match.group(1).strip() if description_match else "Professional healthcare provider offering medical services."
                excerpt = excerpt_match.group(1).strip() if excerpt_match else "Healthcare provider offering medical services."
                review_summary = review_match.group(1).strip() if review_match else "Healthcare provider with patient care services."
                english_summary = english_match.group(1).strip() if english_match else "English language support available upon request."
                
                # Clean up any formatting artifacts
                description = re.sub(r'\n\s*\n', '\n\n', description.strip())  # Normalize paragraph breaks
                excerpt = excerpt.replace('\n', ' ').strip()
                review_summary = review_summary.replace('\n', ' ').strip()
                english_summary = english_summary.replace('\n', ' ').strip()
                
                results.append(ContentResult(
                    description=description,
                    excerpt=excerpt,
                    review_summary=review_summary,
                    english_experience_summary=english_summary
                ))
                
                logger.info(f"✅ Parsed content for provider {i+1}")
                
            except Exception as e:
                logger.error(f"❌ Error parsing provider {i+1}: {str(e)}")
                # Add fallback content
                results.append(ContentResult(
                    description="Professional healthcare provider offering quality medical services.",
                    excerpt="Healthcare provider offering medical services.",
                    review_summary="Healthcare provider with patient care services.",
                    english_experience_summary="English language support available upon request."
                ))
        
        # Fill any missing results with fallbacks
        while len(results) < expected_count:
            results.append(ContentResult(
                description="Professional healthcare provider offering quality medical services.",
                excerpt="Healthcare provider offering medical services.",
                review_summary="Healthcare provider with patient care services.",
                english_experience_summary="English language support available upon request."
            ))
            logger.warning(f"Added fallback content for provider {len(results)}")
        
        return results[:expected_count]
    
    def process_providers_mega_batch(self, providers: List[Any], batch_size: int = 4) -> Dict[str, Any]:
        """Process all providers using mega-batch API calls"""
        if not providers:
            logger.warning("No providers to process")
            return {'updated': 0, 'errors': 0, 'total_providers': 0}
        
        logger.info(f"🚀 Starting mega-batch processing for {len(providers)} providers")
        logger.info(f"📦 Using batch size: {batch_size}")
        logger.info(f"💰 Estimated API calls: {(len(providers) + batch_size - 1) // batch_size}")
        
        updated_count = 0
        error_count = 0
        
        # Process in mega-batches
        for i in range(0, len(providers), batch_size):
            batch = providers[i:i + batch_size]
            logger.info(f"📦 Processing batch {i//batch_size + 1}: providers {i+1}-{min(i+batch_size, len(providers))}")
            
            try:
                # Generate all content types in single API call
                batch_results = self.generate_mega_batch_content(batch, batch_size)
                
                # Update database with results
                batch_updated, batch_errors = self._update_database_batch(batch, batch_results)
                updated_count += batch_updated
                error_count += batch_errors
                
                logger.info(f"✅ Batch complete: {batch_updated} updated, {batch_errors} errors")
                
            except Exception as e:
                logger.error(f"❌ Error processing batch {i//batch_size + 1}: {str(e)}")
                error_count += len(batch)
        
        # Final summary
        logger.info(f"🎉 Mega-batch processing complete:")
        logger.info(f"   📊 Total providers: {len(providers)}")
        logger.info(f"   ✅ Successfully updated: {updated_count}")
        logger.info(f"   ❌ Errors: {error_count}")
        logger.info(f"   📈 Success rate: {updated_count/len(providers)*100:.1f}%")
        
        return {
            'updated': updated_count,
            'errors': error_count,
            'total_providers': len(providers)
        }
    
    def _update_database_batch(self, providers: List[Any], results: List[ContentResult]) -> tuple[int, int]:
        """Update database with mega-batch results"""
        updated_count = 0
        error_count = 0
        
        session = self.db.Session()
        
        try:
            for provider, result in zip(providers, results):
                try:
                    # Handle both Provider objects and dictionaries
                    if hasattr(provider, '__dict__'):
                        # Provider object - update directly
                        provider_obj = session.merge(provider)
                    else:
                        # Dictionary - find in database
                        provider_obj = session.query(Provider).filter_by(
                            provider_name=provider.get('provider_name'),
                            city=provider.get('city')
                        ).first()
                        
                        if not provider_obj:
                            logger.error(f"Provider not found in database: {provider.get('provider_name')}")
                            error_count += 1
                            continue
                    
                    # Update all content fields
                    provider_obj.ai_description = result.description
                    provider_obj.ai_excerpt = result.excerpt
                    provider_obj.review_summary = result.review_summary
                    provider_obj.english_experience_summary = result.english_experience_summary
                    provider_obj.status = 'description_generated'
                    
                    updated_count += 1
                    
                    provider_name = provider_obj.provider_name
                    logger.info(f"✅ Updated all content for {provider_name}")
                    
                except Exception as e:
                    logger.error(f"❌ Error updating provider: {str(e)}")
                    error_count += 1
                    session.rollback()
            
            # Commit all updates in batch
            session.commit()
            logger.info(f"💾 Committed {updated_count} provider updates to database")
            
        except Exception as e:
            logger.error(f"❌ Database batch update error: {str(e)}")
            session.rollback()
            error_count += len(providers)
        finally:
            session.close()
        
        return updated_count, error_count


def filter_providers_needing_content(providers: List[Any]) -> List[Any]:
    """Filter providers that need AI-generated content"""
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
        
        # Skip if already has content or is published
        if ai_description and ai_description.strip():
            logger.info(f"⏭️ Skipping {provider_name}: Already has AI content")
            skipped_count += 1
            continue
            
        if wordpress_post_id:
            logger.info(f"⏭️ Skipping {provider_name}: Already published (ID: {wordpress_post_id})")
            skipped_count += 1
            continue
            
        if status in ['published', 'description_generated']:
            logger.info(f"⏭️ Skipping {provider_name}: Status is {status}")
            skipped_count += 1
            continue
        
        # Provider needs content
        filtered_providers.append(provider)
    
    logger.info(f"🔍 Filtering complete: {len(filtered_providers)} need content, {skipped_count} skipped")
    return filtered_providers


def run_mega_batch_content_generation(providers: List[Any] = None, batch_size: int = 4):
    """Main function to run mega-batch content generation for all providers"""
    print("🚀 CLAUDE MEGA-BATCH CONTENT PROCESSOR")
    print("=" * 60)
    
    try:
        processor = ClaudeMegaBatchProcessor()
        
        # Get providers if not provided
        if providers is None:
            session = processor.db.Session()
            providers = session.query(Provider).all()
            session.close()
            logger.info(f"📊 Loaded {len(providers)} providers from database")
        
        # Filter providers that need content
        providers_needing_content = filter_providers_needing_content(providers)
        
        if not providers_needing_content:
            logger.info("✅ All providers already have AI-generated content")
            return {'updated': 0, 'errors': 0, 'total_providers': len(providers)}
        
        # Process using mega-batch
        results = processor.process_providers_mega_batch(providers_needing_content, batch_size)
        
        print(f"\n🎉 MEGA-BATCH PROCESSING COMPLETE!")
        print(f"   📊 Total providers processed: {results['total_providers']}")
        print(f"   ✅ Successfully updated: {results['updated']}")
        print(f"   ❌ Errors: {results['errors']}")
        print(f"   📈 Success rate: {results['updated']/len(providers_needing_content)*100:.1f}%")
        print(f"   💰 API calls made: {(len(providers_needing_content) + batch_size - 1) // batch_size}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error in mega-batch processing: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return {'updated': 0, 'errors': 1, 'total_providers': 0}


if __name__ == "__main__":
    run_mega_batch_content_generation() 