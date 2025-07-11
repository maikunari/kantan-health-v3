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
from dataclasses import dataclass
from claude_description_generator import ClaudeDescriptionGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContentResult:
    """Result container for all generated content types"""
    description: str
    excerpt: str
    review_summary: str
    english_experience_summary: str
    seo_title: str
    seo_meta_description: str
    selected_featured_image: str  # Claude-selected best photo URL

class ClaudeMegaBatchProcessor:
    """Generate all content types in optimized mega-batches"""
    
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
    
    def generate_mega_batch_content(self, provider_batch: List[Any]) -> List[ContentResult]:
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
            
            # Format location with special handling for Tokyo wards
            location_parts = []
            
            # Tokyo Ward Special Formatting: "Tokyo, Ward" instead of "Ward, Tokyo"
            tokyo_wards = [
                "Adachi", "Arakawa", "Bunkyo", "Chiyoda", "Chuo", "Edogawa",
                "Itabashi", "Katsushika", "Kita", "Koto", "Meguro", "Minato", 
                "Nakano", "Nerima", "Ota", "Setagaya", "Shibuya", "Shinagawa",
                "Shinjuku", "Suginami", "Sumida", "Taito", "Toshima"
            ]
            
            if (city == 'Tokyo' and district and district in tokyo_wards):
                # Tokyo wards: Show city first, then ward
                location_parts.append(city)      # "Tokyo"
                location_parts.append(district)  # "Setagaya"
                # Result: "Tokyo, Setagaya"
            else:
                # Normal formatting: district first (if exists), then city
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
        mega_prompt = f"""Generate ALL SIX content types for these {len(provider_batch)} healthcare providers. Each provider needs exactly 6 pieces of content with precise formatting.

{chr(10).join(provider_details)}

CRITICAL: Generate exactly {len(provider_batch)} complete sets of content. For each provider, create ALL SIX content types in this EXACT format:

PROVIDER [NUMBER]:

DESCRIPTION:
[150-175 word description in exactly 2 paragraphs separated by a blank line. First paragraph: medical services and English support. Second paragraph: patient experience and practical details]

EXCERPT:
[50-75 word concise summary highlighting key strengths and location]

REVIEW_SUMMARY:
[80-100 word narrative paragraph summarizing patient experiences, focusing on what patients consistently praise]

ENGLISH_SUMMARY:
[80-100 word paragraph specifically about English language support and communication experience for international patients]

SEO_TITLE:
[50-60 character SEO title including provider name, specialty, and location for search optimization]

SEO_META_DESCRIPTION:
[150-160 character meta description with call to action, focusing on location + specialty for local SEO]

FORMATTING REQUIREMENTS:
1. DESCRIPTION: Exactly 2 paragraphs, 150-175 words total
2. EXCERPT: Single paragraph, 50-75 words 
3. REVIEW_SUMMARY: Single narrative paragraph, 80-100 words
4. ENGLISH_SUMMARY: Single paragraph about language support, 80-100 words
5. SEO_TITLE: 50-60 characters, includes name + specialty + location
6. SEO_META_DESCRIPTION: 150-160 characters, compelling with call to action

Content Guidelines:
- Professional, informative tone throughout
- Use specific patient feedback when available
- Mention English proficiency levels accurately
- Include location context (district, city, prefecture)
- Focus on patient experience and medical quality
- Avoid phone numbers or website URLs
- Make each content type distinct but complementary
- SEO content should target local search terms

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

SEO_TITLE:
[Internal Medicine Tokyo, Shibuya | Dr. Tanaka Clinic]

SEO_META_DESCRIPTION:
[Expert internal medicine in Tokyo, Shibuya. English-speaking doctors, 4.8/5 rating. Book your consultation today.]

Generate content for all {len(provider_batch)} providers with ALL SIX content types."""

        try:
            response = self.claude.messages.create(
                model=self.model,
                max_tokens=min(8000, 3000 * len(provider_batch)),  # Increased token allocation for comprehensive content
                temperature=0.6,
                system="You are a professional healthcare content specialist. Generate comprehensive, accurate content that helps international patients find quality healthcare providers. Focus on clarity, professionalism, and specific patient benefits.",
                messages=[{"role": "user", "content": mega_prompt}]
            )
            
            response_text = response.content[0].text.strip()
            logger.info(f"📝 Raw Claude response received ({len(response_text)} chars)")
            
            # Parse the mega-batch response
            parsed_results = self._parse_mega_batch_response(response_text, len(provider_batch))
            
            # Process featured image selection for the batch
            logger.info(f"🎨 Starting image selection for {len(provider_batch)} providers")
            final_results = self.process_batch_image_selection(provider_batch, parsed_results)
            
            # Log results with image selection info
            for i, result in enumerate(final_results):
                provider_name = provider_batch[i].provider_name if hasattr(provider_batch[i], 'provider_name') else provider_batch[i].get('provider_name', f'Provider {i+1}')
                desc_words = len(result.description.split())
                excerpt_words = len(result.excerpt.split())
                review_words = len(result.review_summary.split())
                english_words = len(result.english_experience_summary.split())
                seo_title_chars = len(result.seo_title)
                seo_meta_chars = len(result.seo_meta_description)
                has_featured_image = "✅" if result.selected_featured_image else "❌"
                
                logger.info(f"✅ Generated complete content for {provider_name}:")
                logger.info(f"   📄 Description: {desc_words} words")
                logger.info(f"   📄 Excerpt: {excerpt_words} words") 
                logger.info(f"   ⭐ Review Summary: {review_words} words")
                logger.info(f"   🗣️ English Summary: {english_words} words")
                logger.info(f"   🔍 SEO Title: {seo_title_chars} chars")
                logger.info(f"   📝 SEO Meta: {seo_meta_chars} chars")
                logger.info(f"   🖼️ Featured Image: {has_featured_image}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Error generating mega-batch content: {str(e)}")
            # Generate fallback content for providers that couldn't be processed
            fallback_results = []
            for i, provider_data in enumerate(provider_batch):
                provider_name = provider_data.provider_name if hasattr(provider_data, 'provider_name') else provider_data.get('provider_name', f'Provider {i+1}')
                city = provider_data.city if hasattr(provider_data, 'city') else provider_data.get('city', 'Japan')
                specialty = provider_data.specialties[0] if hasattr(provider_data, 'specialties') and provider_data.specialties else provider_data.get('specialties', ['Healthcare'])[0] if provider_data.get('specialties') else 'Healthcare'
                
                # Generate fallback SEO content
                fallback_seo_title = f"{specialty} in {city} | {provider_name}"
                if len(fallback_seo_title) > 60:
                    fallback_seo_title = f"{specialty} | {provider_name}"
                
                fallback_seo_meta = f"{specialty} services in {city}. Professional healthcare provider. Contact {provider_name} for appointments."
                if len(fallback_seo_meta) > 160:
                    fallback_seo_meta = f"{specialty} in {city}. Professional healthcare provider. Contact for appointments."
                
                fallback_results.append(ContentResult(
                    description="Professional healthcare provider offering quality medical services.",
                    excerpt="Healthcare provider offering medical services.",
                    review_summary="Healthcare provider with patient care services.",
                    english_experience_summary="English language support available upon request.",
                    seo_title=fallback_seo_title,
                    seo_meta_description=fallback_seo_meta,
                    selected_featured_image="" # No image for fallback
                ))
                logger.warning(f"Added fallback content for provider {len(fallback_results)}")
            
            return fallback_results
    
    def process_batch_image_selection(self, provider_batch: List[Any], content_results: List[ContentResult]) -> List[ContentResult]:
        """Process image selection for a batch of providers using Claude Vision API"""
        logger.info(f"🎨 Processing featured image selection for {len(provider_batch)} providers")
        
        # Import the description generator for image selection functionality
        from claude_description_generator import ClaudeDescriptionGenerator
        image_selector = ClaudeDescriptionGenerator()
        
        updated_results = []
        
        for provider_data, content_result in zip(provider_batch, content_results):
            try:
                # Convert provider object to dictionary if needed
                if hasattr(provider_data, '__dict__'):
                    provider_dict = {
                        'provider_name': getattr(provider_data, 'provider_name', 'Unknown Provider'),
                        'city': getattr(provider_data, 'city', 'Unknown City'),
                        'prefecture': getattr(provider_data, 'prefecture', ''),
                        'specialties': getattr(provider_data, 'specialties', ['Healthcare']),
                        'photo_urls': getattr(provider_data, 'photo_urls', [])
                    }
                else:
                    provider_dict = provider_data
                
                # Select best featured image using Claude Vision
                selected_image_url = image_selector.select_best_featured_image(provider_dict)
                
                # Update the content result with selected image
                updated_result = ContentResult(
                    description=content_result.description,
                    excerpt=content_result.excerpt,
                    review_summary=content_result.review_summary,
                    english_experience_summary=content_result.english_experience_summary,
                    seo_title=content_result.seo_title,
                    seo_meta_description=content_result.seo_meta_description,
                    selected_featured_image=selected_image_url
                )
                
                updated_results.append(updated_result)
                
                provider_name = provider_dict.get('provider_name', f'Provider {len(updated_results)}')
                logger.info(f"🖼️ Featured image selected for {provider_name}")
                
            except Exception as e:
                logger.error(f"❌ Error selecting image for provider: {str(e)}")
                # Keep original result without selected image
                updated_result = ContentResult(
                    description=content_result.description,
                    excerpt=content_result.excerpt,
                    review_summary=content_result.review_summary,
                    english_experience_summary=content_result.english_experience_summary,
                    seo_title=content_result.seo_title,
                    seo_meta_description=content_result.seo_meta_description,
                    selected_featured_image=""  # Empty if selection failed
                )
                updated_results.append(updated_result)
        
        return updated_results
    
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
                english_match = re.search(r'ENGLISH_SUMMARY:\s*\n(.*?)(?=SEO_TITLE:|$)', section, re.DOTALL)
                seo_title_match = re.search(r'SEO_TITLE:\s*\n(.*?)(?=SEO_META_DESCRIPTION:|$)', section, re.DOTALL)
                seo_meta_description_match = re.search(r'SEO_META_DESCRIPTION:\s*\n(.*?)(?=PROVIDER\s+\d+:|$)', section, re.DOTALL)
                
                # Extract and clean content
                description = description_match.group(1).strip() if description_match else "Professional healthcare provider offering medical services."
                excerpt = excerpt_match.group(1).strip() if excerpt_match else "Healthcare provider offering medical services."
                review_summary = review_match.group(1).strip() if review_match else "Healthcare provider with patient care services."
                english_summary = english_match.group(1).strip() if english_match else "English language support available upon request."
                seo_title = seo_title_match.group(1).strip() if seo_title_match else ""
                seo_meta_description = seo_meta_description_match.group(1).strip() if seo_meta_description_match else ""
                
                # Clean up any formatting artifacts
                description = re.sub(r'\n\s*\n', '\n\n', description.strip())  # Normalize paragraph breaks
                excerpt = excerpt.replace('\n', ' ').strip()
                review_summary = review_summary.replace('\n', ' ').strip()
                english_summary = english_summary.replace('\n', ' ').strip()
                seo_title = seo_title.replace('\n', ' ').strip()
                seo_meta_description = seo_meta_description.replace('\n', ' ').strip()
                
                results.append(ContentResult(
                    description=description,
                    excerpt=excerpt,
                    review_summary=review_summary,
                    english_experience_summary=english_summary,
                    seo_title=seo_title,
                    seo_meta_description=seo_meta_description,
                    selected_featured_image="" # No image for fallback
                ))
                
                logger.info(f"✅ Parsed content for provider {i+1}")
                
            except Exception as e:
                logger.error(f"❌ Error parsing provider {i+1}: {str(e)}")
                # Add fallback content
                results.append(ContentResult(
                    description="Professional healthcare provider offering quality medical services.",
                    excerpt="Healthcare provider offering medical services.",
                    review_summary="Healthcare provider with patient care services.",
                    english_experience_summary="English language support available upon request.",
                    seo_title="",
                    seo_meta_description="",
                    selected_featured_image=""
                ))
        
        # Fill any missing results with fallbacks
        while len(results) < expected_count:
            results.append(ContentResult(
                description="Professional healthcare provider offering quality medical services.",
                excerpt="Healthcare provider offering medical services.",
                review_summary="Healthcare provider with patient care services.",
                english_experience_summary="English language support available upon request.",
                seo_title="",
                seo_meta_description="",
                selected_featured_image=""
            ))
            logger.warning(f"Added fallback content for provider {len(results)}")
        
        return results[:expected_count]
    
    def _is_fallback_content(self, result: ContentResult) -> bool:
        """Check if the content result contains fallback content instead of AI-generated content"""
        fallback_indicators = [
            "Professional healthcare provider offering quality medical services.",
            "Professional healthcare provider offering quality medical services.",
            "Healthcare provider offering medical services.",
            "Healthcare provider with patient care services.",
            "English language support available upon request.",
            "English language support may be available. Please inquire when making appointments."
        ]
        
        # Check if any of the content fields match fallback patterns
        return (result.description in fallback_indicators or
                result.excerpt in fallback_indicators or
                result.review_summary in fallback_indicators or
                result.english_experience_summary in fallback_indicators)
    
    def process_providers_mega_batch(self, providers: List[Any], batch_size: int = 2) -> Dict[str, Any]:
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
                batch_results = self.generate_mega_batch_content(batch)
                
                # Check for fallback content and retry with individual processing if needed
                fallback_count = sum(1 for result in batch_results if self._is_fallback_content(result))
                if fallback_count > 0 and len(batch) > 1:
                    logger.warning(f"⚠️ {fallback_count}/{len(batch)} providers got fallback content, retrying individually...")
                    # Retry failed providers individually
                    retry_results = []
                    for provider in batch:
                        individual_result = self.generate_mega_batch_content([provider])
                        retry_results.extend(individual_result)
                    batch_results = retry_results
                    
                    # Log retry results
                    retry_fallback_count = sum(1 for result in batch_results if self._is_fallback_content(result))
                    logger.info(f"🔄 Retry complete: {len(batch_results) - retry_fallback_count}/{len(batch_results)} providers now have proper content")
                
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
                    provider_obj.seo_title = result.seo_title
                    provider_obj.seo_meta_description = result.seo_meta_description
                    provider_obj.selected_featured_image = result.selected_featured_image
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
    """Filter providers that need AI-generated content (descriptions, SEO, or featured images)"""
    filtered_providers = []
    skipped_count = 0
    
    for provider in providers:
        # Handle both dictionary and Provider object inputs
        if hasattr(provider, '__dict__'):
            # Provider object from database
            provider_name = getattr(provider, 'provider_name', 'Unknown Provider')
            ai_description = getattr(provider, 'ai_description', None)
            seo_title = getattr(provider, 'seo_title', None)
            seo_meta_description = getattr(provider, 'seo_meta_description', None)
            selected_featured_image = getattr(provider, 'selected_featured_image', None)
            wordpress_post_id = getattr(provider, 'wordpress_post_id', None)
            status = getattr(provider, 'status', 'pending')
        else:
            # Dictionary input
            provider_name = provider.get('provider_name', 'Unknown Provider')
            ai_description = provider.get('ai_description', None)
            seo_title = provider.get('seo_title', None)
            seo_meta_description = provider.get('seo_meta_description', None)
            selected_featured_image = provider.get('selected_featured_image', None)
            wordpress_post_id = provider.get('wordpress_post_id', None)
            status = provider.get('status', 'pending')
        
        # Check if provider needs any content type
        needs_basic_content = not (ai_description and ai_description.strip())
        needs_seo_content = not (seo_title and seo_title.strip()) or not (seo_meta_description and seo_meta_description.strip())
        needs_featured_image = not (selected_featured_image and selected_featured_image.strip())
        
        # Skip if already published (unless it needs new content types)
        if wordpress_post_id and not needs_seo_content and not needs_featured_image:
            logger.info(f"⏭️ Skipping {provider_name}: Already published with complete content (ID: {wordpress_post_id})")
            skipped_count += 1
            continue
        
        # Skip if has all content types
        if not needs_basic_content and not needs_seo_content and not needs_featured_image:
            logger.info(f"⏭️ Skipping {provider_name}: Has all content types")
            skipped_count += 1
            continue
        
        # Provider needs some content - log what's needed
        needed_content = []
        if needs_basic_content:
            needed_content.append("basic content")
        if needs_seo_content:
            needed_content.append("SEO content")
        if needs_featured_image:
            needed_content.append("featured image")
        
        logger.info(f"✅ Adding {provider_name}: Needs {', '.join(needed_content)}")
        filtered_providers.append(provider)
    
    logger.info(f"🔍 Filtering complete: {len(filtered_providers)} need content, {skipped_count} skipped")
    return filtered_providers


def run_mega_batch_content_generation(providers: List[Any] = None, batch_size: int = 2):
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