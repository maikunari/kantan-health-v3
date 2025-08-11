#!/usr/bin/env python3
"""
Unified WordPress Publisher
Handles all WordPress sync operations including create and update
"""

import os
import json
import logging
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
import hashlib

from ..core.database import DatabaseManager, Provider
from .content_hash import ContentHashService

logger = logging.getLogger(__name__)


class WordPressPublisher:
    """Unified WordPress publisher for healthcare providers"""
    
    def __init__(self):
        """Initialize WordPress publisher"""
        # Load configuration
        self.wp_url = os.getenv('WORDPRESS_URL')
        self.wp_username = os.getenv('WORDPRESS_USERNAME')
        self.wp_password = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        
        if not all([self.wp_url, self.wp_username, self.wp_password]):
            raise ValueError("WordPress configuration incomplete. Check environment variables.")
        
        # Remove trailing slash from URL
        self.wp_url = self.wp_url.rstrip('/')
        
        # Initialize services
        self.db = DatabaseManager()
        self.hash_service = ContentHashService()
        
        # ACF field mappings
        self.acf_field_mappings = {
            'provider_name': 'field_669d64327e1be',
            'english_speaker': 'field_669d650b7e1bf',
            'location': 'field_669d74217e1c1',
            'station': 'field_66c7231e83bb1',
            'hours': 'field_669d74837e1c2',
            'phone': 'field_669d74a37e1c3',
            'description': 'field_669d64507e1c0',
            'address': 'field_669d74bb7e1c4',
            'website': 'field_669d74ee7e1c5',
            'google_rating': 'field_66a2a628ce8f5',
            'languages': 'field_66a2b2f1ce8fb',
            'specialties': 'field_66a2b43dee901',
            'place_id': 'field_66a2c0f9ee902',
            'reviews': 'field_66a409eade13a',
            'review_summary': 'field_66c89f8501b9f',
            'english_experience_summary': 'field_66c8a03701ba0',
            'accessibility_info': 'field_66c8a1cf01ba1'
        }
        
        logger.info("✅ WordPress Publisher initialized")
    
    def sync_providers(self, providers: List[Provider], 
                      photo_urls: Dict[int, List[str]] = None) -> Dict[str, Any]:
        """Sync multiple providers to WordPress
        
        Args:
            providers: List of providers to sync
            photo_urls: Pre-fetched photo URLs by provider ID
            
        Returns:
            Sync summary
        """
        summary = {
            'total_providers': len(providers),
            'created': 0,
            'updated': 0,
            'synced': 0,
            'failed': 0,
            'errors': []
        }
        
        for provider in providers:
            try:
                # Get photo URLs for this provider
                provider_photos = photo_urls.get(provider.id, []) if photo_urls else []
                
                # Check if provider has photo references (new system)
                if not provider_photos and hasattr(provider, 'photo_references') and provider.photo_references:
                    # Convert references to proxy URLs
                    api_base = os.getenv('API_BASE_URL', 'http://localhost:5000')
                    provider_photos = [f"{api_base}/api/photo/{ref}" for ref in provider.photo_references[:4]]
                    logger.info(f"📸 Using photo references for {provider.provider_name}: {len(provider_photos)} photos")
                
                # Fallback: If no references, check provider's photo_urls field (old system)
                elif not provider_photos and hasattr(provider, 'photo_urls') and provider.photo_urls:
                    try:
                        import json
                        if isinstance(provider.photo_urls, str):
                            old_urls = json.loads(provider.photo_urls)
                        elif isinstance(provider.photo_urls, list):
                            old_urls = provider.photo_urls
                        else:
                            old_urls = []
                        
                        # Convert old URLs to proxy URLs by extracting references
                        import re
                        api_base = os.getenv('API_BASE_URL', 'http://localhost:5000')
                        provider_photos = []
                        
                        for url in old_urls[:4]:  # Limit to 4 photos
                            match = re.search(r'photoreference=([^&]+)', url)
                            if match:
                                ref = match.group(1)
                                provider_photos.append(f"{api_base}/api/photo/{ref}")
                        
                        if provider_photos:
                            logger.info(f"📸 Converted {len(provider_photos)} URLs to proxy for {provider.provider_name}")
                        
                    except Exception as e:
                        logger.warning(f"Could not parse photo_urls for {provider.provider_name}: {e}")
                        provider_photos = []
                
                if provider.wordpress_post_id:
                    # Update existing post
                    result = self.update_provider(provider, provider_photos)
                    if result.get('success'):
                        summary['updated'] += 1
                        summary['synced'] += 1
                else:
                    # Create new post
                    result = self.create_provider(provider, provider_photos)
                    if result.get('success'):
                        summary['created'] += 1
                        summary['synced'] += 1
                
                if not result.get('success'):
                    summary['failed'] += 1
                    summary['errors'].append(f"{provider.provider_name}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"❌ Sync error for {provider.provider_name}: {str(e)}")
                summary['failed'] += 1
                summary['errors'].append(f"{provider.provider_name}: {str(e)}")
        
        return summary
    
    def create_provider(self, provider: Provider, photo_urls: List[str] = None) -> Dict[str, Any]:
        """Create a new WordPress post for a provider
        
        Args:
            provider: Provider to create
            photo_urls: List of photo URLs
            
        Returns:
            Result dictionary with success status
        """
        logger.info(f"📝 Creating WordPress post for {provider.provider_name}")
        
        try:
            # Prepare post data
            post_data = {
                'title': provider.provider_name,
                'content': self._generate_post_content(provider),
                'status': 'publish',
                'type': 'healthcare_provider',  # Custom post type
                'categories': self._get_categories(provider),
                'acf': self._prepare_acf_fields(provider, photo_urls)
            }
            
            # Make API request to healthcare_provider endpoint
            response = requests.post(
                f"{self.wp_url}/wp-json/wp/v2/healthcare_provider",
                auth=(self.wp_username, self.wp_password),
                json=post_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                result = response.json()
                post_id = result.get('id')
                
                # Update database with WordPress info
                content_hash = self.hash_service.generate_hash(provider)
                self.db.update_wordpress_info(provider.id, post_id, content_hash)
                
                # Set featured image if available
                if provider.selected_featured_image:
                    self._set_featured_image(post_id, provider.selected_featured_image)
                
                logger.info(f"✅ Created WordPress post {post_id} for {provider.provider_name}")
                return {'success': True, 'post_id': post_id}
            else:
                error_msg = f"WordPress API error {response.status_code}: {response.text[:200]}"
                logger.error(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            logger.error(f"❌ Create error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def update_provider(self, provider: Provider, photo_urls: List[str] = None) -> Dict[str, Any]:
        """Update an existing WordPress post
        
        Args:
            provider: Provider to update
            photo_urls: List of photo URLs
            
        Returns:
            Result dictionary with success status
        """
        logger.info(f"🔄 Updating WordPress post {provider.wordpress_post_id} for {provider.provider_name}")
        
        try:
            # Check if update is needed
            if not self.hash_service.needs_update(provider):
                logger.info(f"✅ No update needed for {provider.provider_name}")
                return {'success': True, 'updated': False}
            
            # Get changed fields
            changed_fields = self.hash_service.get_changed_fields(provider)
            logger.info(f"📝 Updating fields: {', '.join(changed_fields)}")
            
            # Prepare update data
            post_data = {
                'title': provider.provider_name,
                'content': self._generate_post_content(provider),
                'categories': self._get_categories(provider),
                'acf': self._prepare_acf_fields(provider, photo_urls)
            }
            
            # Make API request to healthcare_provider endpoint
            response = requests.post(
                f"{self.wp_url}/wp-json/wp/v2/healthcare_provider/{provider.wordpress_post_id}",
                auth=(self.wp_username, self.wp_password),
                json=post_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                # Update content hash
                new_hash = self.hash_service.generate_hash(provider)
                self.db.update_wordpress_info(provider.id, provider.wordpress_post_id, new_hash)
                
                # Update featured image if changed
                if 'selected_featured_image' in changed_fields and provider.selected_featured_image:
                    self._set_featured_image(provider.wordpress_post_id, provider.selected_featured_image)
                
                logger.info(f"✅ Updated WordPress post for {provider.provider_name}")
                return {'success': True, 'updated': True, 'changed_fields': changed_fields}
            else:
                error_msg = f"WordPress API error {response.status_code}: {response.text[:200]}"
                logger.error(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            logger.error(f"❌ Update error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _generate_post_content(self, provider: Provider) -> str:
        """Generate minimal post content (most data goes in ACF fields)
        
        Args:
            provider: Provider data
            
        Returns:
            HTML content for post body
        """
        # Minimal content since ACF handles display
        return f"<!-- Provider: {provider.provider_name} -->"
    
    def _prepare_acf_fields(self, provider: Provider, photo_urls: List[str] = None) -> Dict[str, Any]:
        """Prepare ACF fields for WordPress
        
        Args:
            provider: Provider data
            photo_urls: List of photo URLs
            
        Returns:
            Dictionary of ACF field values
        """
        # Format business hours
        hours_text = ""
        if provider.business_hours:
            if isinstance(provider.business_hours, list):
                hours_text = "\n".join(provider.business_hours)
            elif isinstance(provider.business_hours, str):
                hours_text = provider.business_hours
        
        # Format location
        location_parts = []
        if provider.district:
            location_parts.append(provider.district)
        if provider.city:
            location_parts.append(provider.city)
        if provider.prefecture:
            location_parts.append(provider.prefecture)
        location = ", ".join(location_parts)
        
        # Format specialties
        specialties = ""
        if provider.specialties:
            if isinstance(provider.specialties, list):
                specialties = ", ".join(provider.specialties)
            else:
                specialties = str(provider.specialties)
        
        # Format reviews
        reviews_text = self._format_reviews(provider.review_content)
        
        # Format accessibility
        accessibility_info = []
        if provider.wheelchair_accessible == 'Yes':
            accessibility_info.append("Wheelchair accessible")
        if provider.parking_available == 'Yes':
            accessibility_info.append("Parking available")
        accessibility_text = ", ".join(accessibility_info) if accessibility_info else "Contact for accessibility information"
        
        # Prepare ACF data with ALL fields from the old system
        acf_data = {
            # Basic provider info
            self.acf_field_mappings['provider_name']: provider.provider_name,
            self.acf_field_mappings['english_speaker']: provider.english_proficiency or 'Unknown',
            self.acf_field_mappings['location']: location,
            self.acf_field_mappings['station']: provider.nearest_station or '',
            self.acf_field_mappings['hours']: hours_text,
            self.acf_field_mappings['phone']: provider.phone or '',
            self.acf_field_mappings['description']: provider.ai_description or '',
            self.acf_field_mappings['address']: provider.address or '',
            self.acf_field_mappings['website']: provider.website or '',
            self.acf_field_mappings['google_rating']: str(provider.rating) if provider.rating else '0',
            self.acf_field_mappings['languages']: 'English, Japanese',
            self.acf_field_mappings['specialties']: specialties,
            self.acf_field_mappings['place_id']: provider.google_place_id or '',
            self.acf_field_mappings['reviews']: reviews_text,
            self.acf_field_mappings['review_summary']: provider.review_summary or '',
            self.acf_field_mappings['english_experience_summary']: provider.english_experience_summary or '',
            self.acf_field_mappings['accessibility_info']: accessibility_text,
            
            # Additional ACF fields from old system
            "provider_phone": provider.phone or '',
            "wheelchair_accessible": self._format_wheelchair_accessibility(provider.wheelchair_accessible),
            "parking_available": self._format_parking_availability(provider.parking_available),
            "prefecture": provider.prefecture or '',
            "district": provider.district or '',
            "business_status": self._normalize_business_status(provider.business_status) if hasattr(provider, 'business_status') else 'Operational',
            "postal_code": provider.postal_code if hasattr(provider, 'postal_code') else '',
            
            # Location & Map data
            "latitude": provider.latitude or 0,
            "longitude": provider.longitude or 0,
            "google_maps_embed": self._generate_google_maps_embed(provider),
            "google_map": self._generate_google_map_array(provider),
            
            # Language Support
            "english_proficiency": provider.english_proficiency or 'Unknown',
            "proficiency_score": provider.proficiency_score or 0,
            
            # Photos
            "photo_urls": self._format_photo_urls_for_acf(photo_urls),
            "external_featured_image": photo_urls[0] if photo_urls else provider.selected_featured_image or '',
            "featured_image_source": self._get_featured_image_source(provider, photo_urls),
            "photo_count": len(photo_urls) if photo_urls else 0,
            "image_selection_status": self._get_image_selection_status(provider),
            
            # SEO Fields
            "seo_title": provider.seo_title or provider.provider_name,
            "seo_meta_description": provider.seo_meta_description or provider.ai_excerpt or '',
            
            # Business Hours (individual days)
            "business_hours": self._format_business_hours_for_acf(provider.business_hours) if hasattr(provider, 'business_hours') else '',
            "hours_monday": self._get_day_hours(provider.business_hours, 'Monday') if hasattr(provider, 'business_hours') else '',
            "hours_tuesday": self._get_day_hours(provider.business_hours, 'Tuesday') if hasattr(provider, 'business_hours') else '',
            "hours_wednesday": self._get_day_hours(provider.business_hours, 'Wednesday') if hasattr(provider, 'business_hours') else '',
            "hours_thursday": self._get_day_hours(provider.business_hours, 'Thursday') if hasattr(provider, 'business_hours') else '',
            "hours_friday": self._get_day_hours(provider.business_hours, 'Friday') if hasattr(provider, 'business_hours') else '',
            "hours_saturday": self._get_day_hours(provider.business_hours, 'Saturday') if hasattr(provider, 'business_hours') else '',
            "hours_sunday": self._get_day_hours(provider.business_hours, 'Sunday') if hasattr(provider, 'business_hours') else '',
            "open_now": self._get_open_now_status(provider.business_hours) if hasattr(provider, 'business_hours') else 'Status unknown',
            
            # Accessibility Status Fields
            "accessibility_status": self._format_accessibility_status(provider.wheelchair_accessible),
            "parking_status": self._format_parking_status(provider.parking_available),
            
            # Patient Insights
            "review_keywords": self._extract_patient_feedback_themes(provider.review_content),
            "patient_highlights": self._generate_patient_highlights(provider.review_content),
            "english_indicators": self._extract_english_indicators(provider),
            
            # Content fields
            "ai_description": provider.ai_description or '',
            "ai_excerpt": provider.ai_excerpt or '',
            "provider_city": provider.city or '',
            "provider_rating": str(provider.rating or 0),
            "provider_reviews": str(provider.total_reviews or 0),
            "provider_website": self._clean_website_url(provider.website or ''),
            "provider_address": self._clean_address(provider.address or ''),
        }
        
        return acf_data
    
    def _format_reviews(self, review_content: Any) -> str:
        """Format reviews for ACF field
        
        Args:
            review_content: Review data (JSON string or list)
            
        Returns:
            Formatted review text
        """
        if not review_content:
            return ""
        
        reviews = []
        if isinstance(review_content, str):
            try:
                reviews = json.loads(review_content)
            except:
                return ""
        elif isinstance(review_content, list):
            reviews = review_content
        
        formatted_reviews = []
        for review in reviews[:5]:  # Limit to 5 reviews
            if isinstance(review, dict):
                rating = review.get('rating', 0)
                text = review.get('text', '').strip()
                if text:
                    formatted_reviews.append(f"★{'★' * (rating-1)}{'☆' * (5-rating)} {text}")
        
        return "\n\n".join(formatted_reviews)
    
    def _get_categories(self, provider: Provider) -> List[int]:
        """Get WordPress category IDs for provider
        
        Args:
            provider: Provider data
            
        Returns:
            List of category IDs
        """
        # Default category (you may need to adjust based on your WordPress setup)
        categories = [1]  # Uncategorized
        
        # Add categories based on specialties
        # This would need to be mapped to your actual WordPress category IDs
        specialty_category_map = {
            'Hospital': 2,
            'Clinic': 3,
            'Dentistry': 4,
            'Specialist': 5
        }
        
        if provider.specialties:
            for specialty in provider.specialties:
                if specialty in specialty_category_map:
                    categories.append(specialty_category_map[specialty])
        
        return categories
    
    def _set_featured_image(self, post_id: int, image_url: str) -> bool:
        """Set featured image for a post
        
        Args:
            post_id: WordPress post ID
            image_url: URL of the image
            
        Returns:
            Success status
        """
        try:
            # Download image
            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                return False
            
            # Upload to WordPress Media Library
            files = {
                'file': ('featured.jpg', response.content, 'image/jpeg')
            }
            
            upload_response = requests.post(
                f"{self.wp_url}/wp-json/wp/v2/media",
                auth=(self.wp_username, self.wp_password),
                files=files
            )
            
            if upload_response.status_code == 201:
                media = upload_response.json()
                media_id = media.get('id')
                
                # Set as featured image on healthcare_provider CPT
                update_response = requests.post(
                    f"{self.wp_url}/wp-json/wp/v2/healthcare_provider/{post_id}",
                    auth=(self.wp_username, self.wp_password),
                    json={'featured_media': media_id}
                )
                
                return update_response.status_code == 200
                
        except Exception as e:
            logger.error(f"❌ Featured image error: {str(e)}")
        
        return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Test WordPress API connection
        
        Returns:
            Connection test results
        """
        try:
            response = requests.get(
                f"{self.wp_url}/wp-json/wp/v2/users/me",
                auth=(self.wp_username, self.wp_password),
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'success': True,
                    'message': f"Connected as {user_data.get('name', self.wp_username)}",
                    'user_info': {
                        'name': user_data.get('name'),
                        'email': user_data.get('email'),
                        'roles': user_data.get('roles', [])
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned {response.status_code}: {response.text[:200]}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_google_maps_embed(self, provider: Provider) -> str:
        """Generate Google Maps embed HTML"""
        if not provider.latitude or not provider.longitude:
            return ""
        
        address = provider.address or provider.provider_name
        return f'<iframe src="https://maps.google.com/maps?q={provider.latitude},{provider.longitude}&t=&z=15&ie=UTF8&iwloc=&output=embed" width="100%" height="450" frameborder="0" style="border:0" allowfullscreen></iframe>'
    
    def _generate_google_map_array(self, provider: Provider) -> Dict[str, Any]:
        """Generate Google Map array for ACF Google Map field"""
        if not provider.latitude or not provider.longitude:
            return {}
        
        return {
            "address": provider.address or "",
            "lat": provider.latitude,
            "lng": provider.longitude,
            "zoom": 15,
            "place_id": provider.google_place_id or "",
            "name": provider.provider_name
        }
    
    def _format_photo_urls_for_acf(self, photo_urls: List[str]) -> str:
        """Format photo URLs for ACF gallery field"""
        if not photo_urls:
            return ""
        
        # Return newline-separated URLs for the ACF field
        return "\n".join(photo_urls[:10])  # Limit to 10 photos
    
    def _format_wheelchair_accessibility(self, wheelchair_accessible: str) -> str:
        """Format wheelchair accessibility for ACF dropdown field"""
        if wheelchair_accessible in ['Yes', 'true', 'True', True]:
            return "Wheelchair accessible"
        elif wheelchair_accessible in ['No', 'false', 'False', False]:
            return "Not wheelchair accessible"
        else:
            return "Wheelchair accessibility unknown"
    
    def _format_parking_availability(self, parking_available: str) -> str:
        """Format parking availability for ACF dropdown field"""
        if parking_available in ['Yes', 'true', 'True', True]:
            return "Parking is available"
        elif parking_available in ['No', 'false', 'False', False]:
            return "Parking is not available"
        else:
            return "Parking unknown"
    
    def _get_featured_image_source(self, provider: Provider, photo_urls: List[str]) -> str:
        """Determine the source of the featured image"""
        if provider.selected_featured_image:
            return "Claude AI Selected"
        elif photo_urls and len(photo_urls) > 0:
            return "First Available Photo"
        else:
            return "No Image Available"
    
    def _normalize_business_status(self, status: str) -> str:
        """Normalize business status for ACF field"""
        if status in ['OPERATIONAL', 'operational', 'open']:
            return 'Operational'
        elif status in ['CLOSED_TEMPORARILY', 'closed_temporarily']:
            return 'Temporarily Closed'
        elif status in ['CLOSED_PERMANENTLY', 'closed_permanently']:
            return 'Permanently Closed'
        else:
            return 'Operational'
    
    def _format_business_hours_for_acf(self, business_hours: Any) -> str:
        """Format business hours for ACF field"""
        if not business_hours:
            return ""
        
        # If it's a string (JSON), parse it
        if isinstance(business_hours, str):
            try:
                business_hours = json.loads(business_hours)
            except:
                return ""
        
        # If we have display_text from Google Places, use that
        if isinstance(business_hours, dict) and 'display_text' in business_hours:
            return "\n".join(business_hours['display_text'])
        
        # Format from formatted_hours
        if isinstance(business_hours, dict) and 'formatted_hours' in business_hours:
            formatted_lines = []
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            for day in days_order:
                if day in business_hours['formatted_hours']:
                    hours = business_hours['formatted_hours'][day]
                    if hours.get('status') == 'closed':
                        formatted_lines.append(f"{day}: Closed")
                    elif hours.get('open') and hours.get('close'):
                        formatted_lines.append(f"{day}: {hours['open']} - {hours['close']}")
                    else:
                        formatted_lines.append(f"{day}: Closed")
            
            return "\n".join(formatted_lines)
        
        return ""
    
    def _get_day_hours(self, business_hours: Any, day: str) -> str:
        """Get hours for specific day"""
        if not business_hours:
            return "Hours not available"
        
        # If it's a string (JSON), parse it
        if isinstance(business_hours, str):
            try:
                business_hours = json.loads(business_hours)
            except:
                return "Hours not available"
        
        if isinstance(business_hours, dict) and 'formatted_hours' in business_hours:
            if day in business_hours['formatted_hours']:
                hours = business_hours['formatted_hours'][day]
                if hours.get('status') == 'closed':
                    return "Closed"
                elif hours.get('open') and hours.get('close'):
                    return f"{hours['open']} - {hours['close']}"
                else:
                    return "Closed"
        
        return "Hours not available"
    
    def _get_open_now_status(self, business_hours: Any) -> str:
        """Get open now status from Google Places data"""
        if not business_hours:
            return "Status unknown"
        
        # If it's a string (JSON), parse it
        if isinstance(business_hours, str):
            try:
                business_hours = json.loads(business_hours)
            except:
                return "Status unknown"
        
        if isinstance(business_hours, dict) and 'open_now' in business_hours:
            return "Open Now" if business_hours['open_now'] else "Closed"
        
        return "Status unknown"
    
    def _format_accessibility_status(self, wheelchair_accessible: str) -> str:
        """Format accessibility status for ACF field"""
        return self._format_wheelchair_accessibility(wheelchair_accessible)
    
    def _format_parking_status(self, parking_available: str) -> str:
        """Format parking status for ACF field"""
        return self._format_parking_availability(parking_available)
    
    def _extract_patient_feedback_themes(self, review_content: Any) -> str:
        """Extract patient feedback themes from reviews"""
        if not review_content:
            return ""
        
        # Simple keyword extraction (could be enhanced with NLP)
        themes = []
        
        reviews = []
        if isinstance(review_content, str):
            try:
                reviews = json.loads(review_content)
            except:
                return ""
        elif isinstance(review_content, list):
            reviews = review_content
        
        # Extract common themes
        keywords = {
            'english': 0,
            'friendly': 0,
            'clean': 0,
            'professional': 0,
            'wait': 0,
            'appointment': 0
        }
        
        for review in reviews:
            if isinstance(review, dict) and 'text' in review:
                text = review['text'].lower()
                for keyword in keywords:
                    if keyword in text:
                        keywords[keyword] += 1
        
        # Return top themes
        for keyword, count in sorted(keywords.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                themes.append(f"{keyword} ({count} mentions)")
        
        return ", ".join(themes[:5]) if themes else "No themes extracted"
    
    def _generate_patient_highlights(self, review_content: Any) -> List[Dict[str, str]]:
        """Generate patient highlights from reviews as ACF repeater field array"""
        if not review_content:
            return []
        
        reviews = []
        if isinstance(review_content, str):
            try:
                reviews = json.loads(review_content)
            except:
                return []
        elif isinstance(review_content, list):
            reviews = review_content
        
        if not reviews or not isinstance(reviews, list):
            return []
        
        highlights = []
        
        # Analyze reviews for common positive highlights
        has_english_support = False
        has_clean_facilities = False
        has_friendly_staff = False
        has_professional_care = False
        has_convenient_location = False
        
        for review in reviews:
            if isinstance(review, dict):
                text = review.get('text', '').lower()
                rating = review.get('rating', 0)
                
                # Only consider reviews with 4+ stars for highlights
                if rating >= 4:
                    if any(word in text for word in ['english', 'bilingual', 'speaks english']):
                        has_english_support = True
                    if any(word in text for word in ['clean', 'hygienic', 'spotless']):
                        has_clean_facilities = True
                    if any(word in text for word in ['friendly', 'kind', 'caring', 'welcoming']):
                        has_friendly_staff = True
                    if any(word in text for word in ['professional', 'expert', 'skilled']):
                        has_professional_care = True
                    if any(word in text for word in ['convenient', 'accessible', 'easy to find']):
                        has_convenient_location = True
        
        # Build highlights array for ACF repeater field
        if has_english_support:
            highlights.append({
                'highlight_text': 'English-speaking support available',
                'highlight_icon': 'language'
            })
        
        if has_clean_facilities:
            highlights.append({
                'highlight_text': 'Clean and modern facilities',
                'highlight_icon': 'sparkles'
            })
        
        if has_friendly_staff:
            highlights.append({
                'highlight_text': 'Friendly and caring staff',
                'highlight_icon': 'heart'
            })
        
        if has_professional_care:
            highlights.append({
                'highlight_text': 'Professional medical care',
                'highlight_icon': 'stethoscope'
            })
        
        if has_convenient_location:
            highlights.append({
                'highlight_text': 'Convenient location',
                'highlight_icon': 'location'
            })
        
        # If no specific highlights found but has good reviews, add generic one
        if not highlights and reviews:
            avg_rating = sum(r.get('rating', 0) for r in reviews if isinstance(r, dict)) / len(reviews)
            if avg_rating >= 4.0:
                highlights.append({
                    'highlight_text': 'Highly rated by patients',
                    'highlight_icon': 'star'
                })
        
        return highlights
    
    def _extract_english_indicators(self, provider: Provider) -> str:
        """Extract English language indicators"""
        indicators = []
        
        # Check proficiency score
        if hasattr(provider, 'proficiency_score') and provider.proficiency_score:
            if provider.proficiency_score >= 40:
                indicators.append("High English proficiency score")
            elif provider.proficiency_score >= 20:
                indicators.append("Moderate English proficiency score")
        
        # Check English proficiency field
        if provider.english_proficiency and provider.english_proficiency != 'Unknown':
            indicators.append(f"English: {provider.english_proficiency}")
        
        # Check for English in reviews
        if hasattr(provider, 'english_experience_summary') and provider.english_experience_summary:
            if 'english' in provider.english_experience_summary.lower():
                indicators.append("English support mentioned in reviews")
        
        return ", ".join(indicators) if indicators else "English support status unclear"
    
    def _get_image_selection_status(self, provider: Provider) -> str:
        """Determine the image selection status"""
        if provider.selected_featured_image:
            return "selected"  # AI selected
        elif hasattr(provider, 'photo_urls'):
            photo_urls = provider.photo_urls
            if isinstance(photo_urls, str):
                try:
                    photo_urls = json.loads(photo_urls)
                except:
                    photo_urls = []
            
            if photo_urls and len(photo_urls) > 0:
                return "fallback"  # Using fallback (first photo)
            else:
                return "none"  # No images available
        else:
            return "none"
    
    def _clean_website_url(self, url: str) -> str:
        """Clean website URL by removing query parameters"""
        if not url:
            return ""
        
        try:
            if '?' in url:
                url = url.split('?')[0]
            return url.rstrip('/')
        except Exception:
            return url
    
    def _clean_address(self, address: str) -> str:
        """Clean address by removing Japan suffix"""
        if not address:
            return ""
        
        cleaned = address.strip()
        
        # Remove 'Japan' from end
        japan_suffixes = [', Japan', ',Japan', ' Japan']
        for suffix in japan_suffixes:
            if cleaned.lower().endswith(suffix.lower()):
                cleaned = cleaned[:-len(suffix)]
                break
        
        return cleaned.strip(' ,')