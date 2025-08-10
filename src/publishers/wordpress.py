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
                'type': 'post',
                'categories': self._get_categories(provider),
                'acf': self._prepare_acf_fields(provider, photo_urls)
            }
            
            # Make API request
            response = requests.post(
                f"{self.wp_url}/wp-json/wp/v2/posts",
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
            
            # Make API request
            response = requests.post(
                f"{self.wp_url}/wp-json/wp/v2/posts/{provider.wordpress_post_id}",
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
        
        # Prepare ACF data
        acf_data = {
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
            self.acf_field_mappings['accessibility_info']: accessibility_text
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
                
                # Set as featured image
                update_response = requests.post(
                    f"{self.wp_url}/wp-json/wp/v2/posts/{post_id}",
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