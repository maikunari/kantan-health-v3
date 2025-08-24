#!/usr/bin/env python3
"""
Unified AI Content Generation
Consolidates all AI content generation using mega-batch processing
"""

import os
import re
import logging
from typing import List, Dict, Optional, Any, NamedTuple
from datetime import datetime
from collections import namedtuple

from anthropic import Anthropic
from ..core.database import DatabaseManager, Provider

logger = logging.getLogger(__name__)

# Content result structure
ContentResult = namedtuple('ContentResult', [
    'description',
    'excerpt', 
    'review_summary',
    'english_experience_summary',
    'seo_title',
    'seo_meta_description',
    'selected_featured_image'
])


class AIContentProcessor:
    """Unified AI content processor using mega-batch approach"""
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize AI content processor
        
        Args:
            model: Claude model to use
        """
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.claude = Anthropic(api_key=self.api_key)
        self.model = model
        self.db = DatabaseManager()
        
        logger.info(f"✅ AI Content Processor initialized with {model}")
    
    def process_providers(self, providers: List[Provider], 
                         batch_size: int = 2,
                         max_retries: int = 2) -> Dict[str, Any]:
        """Process providers with mega-batch content generation
        
        Args:
            providers: List of providers to process
            batch_size: Number of providers per API call
            max_retries: Maximum retry attempts
            
        Returns:
            Processing summary
        """
        summary = {
            'total_providers': len(providers),
            'successful': 0,
            'failed': 0,
            'api_calls': 0,
            'errors': []
        }
        
        # Process in batches
        for i in range(0, len(providers), batch_size):
            batch = providers[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(providers) + batch_size - 1) // batch_size
            
            logger.info(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} providers)")
            
            success = False
            
            for attempt in range(max_retries + 1):
                try:
                    # Generate content for batch
                    content_results = self._generate_mega_batch_content(batch)
                    summary['api_calls'] += 1
                    
                    if content_results:
                        # Process image selection
                        content_results = self._process_image_selection(batch, content_results)
                        
                        # Update database
                        updated = self._update_providers_with_content(batch, content_results)
                        summary['successful'] += updated
                        
                        success = True
                        break
                    
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(f"🔄 Retry {attempt + 1}/{max_retries} for batch {batch_num}")
                    else:
                        logger.error(f"❌ Batch {batch_num} failed: {str(e)}")
                        summary['failed'] += len(batch)
                        summary['errors'].append(f"Batch {batch_num}: {str(e)}")
            
            if not success and len(batch) > 1:
                # Try individual processing as fallback
                logger.info(f"🔧 Falling back to individual processing for batch {batch_num}")
                for provider in batch:
                    try:
                        results = self._generate_mega_batch_content([provider])
                        summary['api_calls'] += 1
                        
                        if results:
                            results = self._process_image_selection([provider], results)
                            updated = self._update_providers_with_content([provider], results)
                            summary['successful'] += updated
                        else:
                            summary['failed'] += 1
                            
                    except Exception as e:
                        logger.error(f"❌ Individual processing failed for {provider.provider_name}: {e}")
                        summary['failed'] += 1
        
        logger.info(f"✅ Content generation complete: {summary['successful']}/{summary['total_providers']} successful")
        return summary
    
    def _generate_mega_batch_content(self, providers: List[Provider]) -> List[ContentResult]:
        """Generate all content types for multiple providers in one API call
        
        Args:
            providers: List of providers (max 2-3 recommended)
            
        Returns:
            List of ContentResult for each provider
        """
        if not providers:
            return []
        
        # Build provider details for prompt
        provider_details = []
        
        for idx, provider in enumerate(providers, 1):
            # Extract provider information
            name = provider.provider_name
            city = provider.city or "Unknown City"
            district = provider.district or ""
            prefecture = provider.prefecture or ""
            specialties = provider.specialties or ['Healthcare']
            rating = provider.rating or 0
            reviews = provider.total_reviews or 0
            proficiency = provider.english_proficiency or "Unknown"
            wheelchair = provider.wheelchair_accessible or "Not specified"
            parking = provider.parking_available or "Not specified"
            
            # Format location
            location_parts = [district, city, prefecture]
            location = ', '.join(filter(None, location_parts))
            
            # Process reviews
            review_insights = self._analyze_reviews(provider.review_content)
            
            # Format provider details
            details = f"""
Provider {idx}: {name}
- Location: {location}
- Specialties: {', '.join(specialties) if isinstance(specialties, list) else specialties}
- English Support: {proficiency}
- Patient Rating: {rating}/5 stars ({reviews} reviews)
- Positive Themes: {', '.join(review_insights['positive_themes'][:3]) if review_insights['positive_themes'] else 'Professional healthcare'}
- English Mentions: {len(review_insights['english_mentions'])} reviews mention English support
- Accessibility: {'Wheelchair accessible' if wheelchair == 'Yes' else 'Accessibility not specified'}
- Parking: {'Parking available' if parking == 'Yes' else 'Parking not specified'}

Patient Reviews Sample:
{self._format_review_sample(review_insights['reviews'][:5])}"""
            
            provider_details.append(details)
        
        # Create mega-prompt
        prompt = self._create_mega_prompt(provider_details)
        
        try:
            # Make API call
            response = self.claude.messages.create(
                model=self.model,
                max_tokens=min(8000, 3000 * len(providers)),
                temperature=0.6,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            response_text = response.content[0].text if response.content else ""
            content_results = self._parse_mega_response(response_text, len(providers))
            
            if len(content_results) == len(providers):
                logger.info(f"✅ Generated content for {len(content_results)} providers")
                return content_results
            else:
                logger.warning(f"⚠️ Expected {len(providers)} results, got {len(content_results)}")
                return self._create_fallback_content(providers)
                
        except Exception as e:
            logger.error(f"❌ API error: {str(e)}")
            return self._create_fallback_content(providers)
    
    def _create_mega_prompt(self, provider_details: List[str]) -> str:
        """Create the mega-batch prompt for multiple providers"""
        return f"""Generate ALL SIX content types for these {len(provider_details)} healthcare providers. Each provider needs exactly 6 pieces of content with precise formatting.

{chr(10).join(provider_details)}

CRITICAL: Generate exactly {len(provider_details)} complete sets of content. For each provider, create ALL SIX content types in this EXACT format:

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

Generate content for all {len(provider_details)} providers with ALL SIX content types."""
    
    def _analyze_reviews(self, review_content: Any) -> Dict[str, Any]:
        """Analyze review content for insights"""
        result = {
            'reviews': [],
            'positive_themes': [],
            'english_mentions': [],
            'avg_rating': 0
        }
        
        if not review_content:
            return result
        
        # Handle different review content formats
        reviews = []
        if isinstance(review_content, str):
            try:
                reviews = eval(review_content) if review_content else []
            except:
                return result
        elif isinstance(review_content, list):
            reviews = review_content
        
        if not reviews:
            return result
        
        # Process reviews
        total_rating = 0
        english_keywords = ['english', 'English', '英語', 'foreign', 'international']
        positive_words = ['excellent', 'great', 'good', 'professional', 'friendly', 
                         'helpful', 'clean', 'modern', 'efficient', 'thorough']
        
        themes = set()
        
        for review in reviews[:10]:  # Limit to prevent token overflow
            if isinstance(review, dict):
                text = review.get('text', '')
                rating = review.get('rating', 0)
                
                result['reviews'].append(review)
                total_rating += rating
                
                # Check for English mentions
                if any(keyword in text for keyword in english_keywords):
                    result['english_mentions'].append(text[:200])
                
                # Extract positive themes
                text_lower = text.lower()
                for word in positive_words:
                    if word in text_lower:
                        themes.add(word.capitalize())
        
        result['positive_themes'] = list(themes)[:5]
        result['avg_rating'] = total_rating / len(reviews) if reviews else 0
        
        return result
    
    def _format_review_sample(self, reviews: List[Dict]) -> str:
        """Format review sample for prompt"""
        if not reviews:
            return "Limited review content available"
        
        formatted = []
        for review in reviews[:5]:
            text = review.get('text', '').strip()
            rating = review.get('rating', 0)
            if text and len(text) > 20:
                formatted.append(f"Rating {rating}/5: {text[:150]}...")
        
        return '\n'.join(formatted) if formatted else "Limited review content available"
    
    def _parse_mega_response(self, response_text: str, expected_count: int) -> List[ContentResult]:
        """Parse the mega-batch response to extract content for each provider"""
        results = []
        
        # Split by provider sections
        provider_sections = re.split(r'\bPROVIDER\s+\d+:', response_text)
        
        # Remove empty first section
        if provider_sections and not provider_sections[0].strip():
            provider_sections = provider_sections[1:]
        
        logger.info(f"📊 Found {len(provider_sections)} provider sections")
        
        for section in provider_sections[:expected_count]:
            try:
                # Extract each content type
                content = self._extract_content_from_section(section)
                if content:
                    results.append(content)
            except Exception as e:
                logger.error(f"❌ Error parsing section: {str(e)}")
        
        return results
    
    def _extract_content_from_section(self, section: str) -> Optional[ContentResult]:
        """Extract all content types from a provider section"""
        try:
            # Use regex to extract each content type
            patterns = {
                'description': r'DESCRIPTION:\s*\n(.*?)(?=EXCERPT:|$)',
                'excerpt': r'EXCERPT:\s*\n(.*?)(?=REVIEW_SUMMARY:|$)',
                'review_summary': r'REVIEW_SUMMARY:\s*\n(.*?)(?=ENGLISH_SUMMARY:|$)',
                'english_summary': r'ENGLISH_SUMMARY:\s*\n(.*?)(?=SEO_TITLE:|$)',
                'seo_title': r'SEO_TITLE:\s*\n(.*?)(?=SEO_META_DESCRIPTION:|$)',
                'seo_meta': r'SEO_META_DESCRIPTION:\s*\n(.*?)(?=PROVIDER\s+\d+:|$)'
            }
            
            extracted = {}
            
            for key, pattern in patterns.items():
                match = re.search(pattern, section, re.DOTALL)
                if match:
                    extracted[key] = match.group(1).strip()
            
            # Validate extraction
            if len(extracted) >= 6:
                return ContentResult(
                    description=extracted.get('description', ''),
                    excerpt=extracted.get('excerpt', ''),
                    review_summary=extracted.get('review_summary', ''),
                    english_experience_summary=extracted.get('english_summary', ''),
                    seo_title=extracted.get('seo_title', ''),
                    seo_meta_description=extracted.get('seo_meta', ''),
                    selected_featured_image=""  # Will be added by image selection
                )
        
        except Exception as e:
            logger.error(f"❌ Content extraction error: {str(e)}")
        
        return None
    
    def _create_fallback_content(self, providers: List[Provider]) -> List[ContentResult]:
        """Create fallback content if API fails"""
        results = []
        
        for provider in providers:
            name = provider.provider_name
            city = provider.city or "Japan"
            specialty = provider.specialties[0] if provider.specialties else "Healthcare"
            
            # Create minimal but valid content
            results.append(ContentResult(
                description=f"{name} provides quality healthcare services in {city}. Professional medical care with English language support available.",
                excerpt=f"Healthcare provider in {city} offering medical services.",
                review_summary="Healthcare facility providing medical services to patients.",
                english_experience_summary="English language support is available for international patients.",
                seo_title=f"{specialty} in {city} | {name}"[:60],
                seo_meta_description=f"{specialty} services in {city}. Visit {name} for quality healthcare."[:160],
                selected_featured_image=""
            ))
        
        return results
    
    def _process_image_selection(self, providers: List[Provider], 
                               content_results: List[ContentResult]) -> List[ContentResult]:
        """Select best featured image for each provider
        
        Args:
            providers: List of providers
            content_results: Content results to update
            
        Returns:
            Updated content results with selected images
        """
        updated_results = []
        
        for provider, content in zip(providers, content_results):
            try:
                # Photos are no longer collected
                selected_image = ""
                
                # Update content result
                updated_result = ContentResult(
                    description=content.description,
                    excerpt=content.excerpt,
                    review_summary=content.review_summary,
                    english_experience_summary=content.english_experience_summary,
                    seo_title=content.seo_title,
                    seo_meta_description=content.seo_meta_description,
                    selected_featured_image=selected_image
                )
                
                updated_results.append(updated_result)
                
            except Exception as e:
                logger.error(f"❌ Image selection error: {str(e)}")
                updated_results.append(content)
        
        return updated_results
    
    def _update_providers_with_content(self, providers: List[Provider], 
                                     content_results: List[ContentResult]) -> int:
        """Update database with generated content
        
        Args:
            providers: List of providers
            content_results: Generated content
            
        Returns:
            Number of successfully updated providers
        """
        updated_count = 0
        
        for provider, content in zip(providers, content_results):
            try:
                # Prepare content data
                content_data = {
                    'description': content.description,
                    'excerpt': content.excerpt,
                    'review_summary': content.review_summary,
                    'english_experience_summary': content.english_experience_summary,
                    'seo_title': content.seo_title,
                    'seo_meta_description': content.seo_meta_description,
                    'selected_featured_image': content.selected_featured_image
                }
                
                # Update in database
                if self.db.update_provider_content(provider.id, content_data):
                    updated_count += 1
                    logger.info(f"✅ Updated content for {provider.provider_name}")
                else:
                    logger.error(f"❌ Failed to update {provider.provider_name}")
                    
            except Exception as e:
                logger.error(f"❌ Database update error for {provider.provider_name}: {str(e)}")
        
        return updated_count