#!/usr/bin/env python3
"""
WordPress Update Service for WordPress Sync Enhancement
Handles updating existing WordPress posts with current database content.
"""

import os
import requests
import time
import json
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging
from dotenv import load_dotenv
from sqlalchemy import text
from postgres_integration import PostgresIntegration, Provider
from content_hash_service import ContentHashService, ContentComparison

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WordPressUpdateService:
    """Service for updating existing WordPress posts with current database content"""
    
    def __init__(self, wp_base_url: str = None, wp_username: str = None, wp_password: str = None):
        """Initialize WordPress update service with credentials"""
        # Load environment variables
        config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
        load_dotenv(config_path)
        
        # Set credentials
        self.wp_base_url = wp_base_url or os.getenv('WORDPRESS_URL', 'https://care-compass.jp')
        self.wp_username = wp_username or os.getenv('WORDPRESS_USERNAME')
        self.wp_password = wp_password or os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        
        if not all([self.wp_base_url, self.wp_username, self.wp_password]):
            raise ValueError("Missing WordPress credentials in environment variables")
        
        # Initialize services
        self.db = PostgresIntegration()
        self.content_hash_service = ContentHashService()
        
        # Configure session
        self.session = requests.Session()
        self.session.auth = (self.wp_username, self.wp_password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Healthcare-Directory-Sync/1.0'
        })
    
    def update_existing_post(self, provider: Provider, dry_run: bool = False) -> Dict[str, Any]:
        """Update a single WordPress post with current database content"""
        
        if not provider.wordpress_post_id:
            raise ValueError(f"Provider {provider.provider_name} has no WordPress post ID")
        
        logger.info(f"🔄 Updating WordPress post for {provider.provider_name} (ID: {provider.wordpress_post_id})")
        
        # Check if content has changed
        content_comparison = self.content_hash_service.compare_content(provider)
        
        if not content_comparison.needs_update:
            logger.info(f"⏭️ No changes detected for {provider.provider_name}")
            return {
                'status': 'no_changes',
                'provider_name': provider.provider_name,
                'post_id': provider.wordpress_post_id,
                'message': 'Content is up to date'
            }
        
        # Generate current content
        post_content = self._generate_post_content(provider)
        acf_fields = self._generate_acf_fields(provider)
        
        # Prepare update payload
        update_data = {
            'content': post_content,
            'title': provider.provider_name,
            'excerpt': provider.ai_excerpt or '',
            'acf': acf_fields,
            'meta': {
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'sync_source': 'WordPress Sync Enhancement',
                'content_hash': content_comparison.new_hash
            }
        }
        
        if dry_run:
            logger.info(f"🧪 DRY RUN: Would update {provider.provider_name}")
            return {
                'status': 'dry_run',
                'provider_name': provider.provider_name,
                'post_id': provider.wordpress_post_id,
                'changes': content_comparison.changed_fields,
                'update_payload': update_data
            }
        
        # Execute WordPress update
        try:
            start_time = time.time()
            
            response = self.session.post(
                f"{self.wp_base_url}/wp-json/wp/v2/healthcare_provider/{provider.wordpress_post_id}",
                json=update_data,
                timeout=30
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully updated {provider.provider_name} in {duration_ms}ms")
                
                # Update local tracking
                session = self.db.Session()
                try:
                    # Refresh provider from database
                    db_provider = session.query(Provider).filter_by(id=provider.id).first()
                    if db_provider:
                        db_provider.last_wordpress_sync = datetime.now()
                        db_provider.content_hash = content_comparison.new_hash
                        db_provider.wordpress_status = 'synced'
                        session.commit()
                        
                        # Log successful sync
                        self._log_sync_operation(
                            provider.id,
                            provider.wordpress_post_id,
                            'update',
                            'success',
                            duration_ms,
                            content_comparison.new_hash
                        )
                finally:
                    session.close()
                
                return {
                    'status': 'success',
                    'provider_name': provider.provider_name,
                    'post_id': provider.wordpress_post_id,
                    'duration_ms': duration_ms,
                    'changes': content_comparison.changed_fields
                }
                
            else:
                error_msg = f"WordPress API error: {response.status_code} - {response.text}"
                logger.error(f"❌ Failed to update {provider.provider_name}: {error_msg}")
                
                # Log failed sync
                self._log_sync_operation(
                    provider.id,
                    provider.wordpress_post_id,
                    'update',
                    'failed',
                    duration_ms,
                    content_comparison.new_hash,
                    error_msg
                )
                
                return {
                    'status': 'failed',
                    'provider_name': provider.provider_name,
                    'post_id': provider.wordpress_post_id,
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            error_msg = "Request timed out"
            logger.error(f"❌ Timeout updating {provider.provider_name}: {error_msg}")
            
            self._log_sync_operation(
                provider.id,
                provider.wordpress_post_id,
                'update',
                'failed',
                30000,
                content_comparison.new_hash,
                error_msg
            )
            
            return {
                'status': 'failed',
                'provider_name': provider.provider_name,
                'post_id': provider.wordpress_post_id,
                'error': error_msg
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Unexpected error updating {provider.provider_name}: {error_msg}")
            
            self._log_sync_operation(
                provider.id,
                provider.wordpress_post_id,
                'update',
                'failed',
                0,
                content_comparison.new_hash,
                error_msg
            )
            
            return {
                'status': 'failed',
                'provider_name': provider.provider_name,
                'post_id': provider.wordpress_post_id,
                'error': error_msg
            }
    
    def bulk_update_posts(self, providers: List[Provider], batch_size: int = 10, dry_run: bool = False) -> Dict[str, Any]:
        """Update multiple WordPress posts in batches with rate limiting"""
        logger.info(f"🔄 Starting bulk update of {len(providers)} providers (batch size: {batch_size})")
        
        results = {
            'total': len(providers),
            'success': 0,
            'failed': 0,
            'no_changes': 0,
            'skipped': 0,
            'details': []
        }
        
        for i in range(0, len(providers), batch_size):
            batch = providers[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"📦 Processing batch {batch_num} ({len(batch)} providers)")
            
            for provider in batch:
                try:
                    result = self.update_existing_post(provider, dry_run=dry_run)
                    results['details'].append(result)
                    
                    if result['status'] == 'success':
                        results['success'] += 1
                    elif result['status'] == 'failed':
                        results['failed'] += 1
                    elif result['status'] == 'no_changes':
                        results['no_changes'] += 1
                    else:
                        results['skipped'] += 1
                        
                except Exception as e:
                    logger.error(f"❌ Error processing {provider.provider_name}: {str(e)}")
                    results['failed'] += 1
                    results['details'].append({
                        'status': 'failed',
                        'provider_name': provider.provider_name,
                        'error': str(e)
                    })
            
            # Rate limiting between batches
            if i + batch_size < len(providers):
                logger.info(f"⏳ Waiting 2 seconds before next batch...")
                time.sleep(2)
        
        # Calculate success rate
        success_rate = (results['success'] / results['total'] * 100) if results['total'] > 0 else 0
        
        logger.info(f"📊 Bulk update complete:")
        logger.info(f"   ✅ Success: {results['success']}")
        logger.info(f"   ❌ Failed: {results['failed']}")
        logger.info(f"   ⏭️ No changes: {results['no_changes']}")
        logger.info(f"   ⏸️ Skipped: {results['skipped']}")
        logger.info(f"   📈 Success rate: {success_rate:.1f}%")
        
        return results
    
    def _generate_post_content(self, provider: Provider) -> str:
        """Generate WordPress post content from provider data"""
        # Get specialty display
        specialties = provider.specialties or []
        if isinstance(specialties, str):
            specialties = [specialties]
        specialty_display = ", ".join(specialties) if specialties else "General Practice"
        
        # Get location display
        location_parts = [part for part in [provider.city, provider.prefecture] if part]
        location_display = ", ".join(location_parts) if location_parts else "Location not specified"
        
        # Format business hours
        business_hours_display = self._format_business_hours_display(provider.business_hours or {})
        
        content = f"""
        <div class="provider-content">
            <h2>{provider.provider_name}</h2>
            
            <div class="provider-details">
                <p><strong>📍 Location:</strong> {location_display}</p>
                <p><strong>📫 Address:</strong> {self._clean_address(provider.address) or 'Not available'}</p>
                <p><strong>📞 Phone:</strong> {provider.phone or 'Not available'}</p>
                <p><strong>🌐 Website:</strong> {self._clean_website_url(provider.website) or 'Not available'}</p>
                <p><strong>🏥 Specialties:</strong> {specialty_display}</p>
                <p><strong>🗣️ English Support:</strong> {provider.english_proficiency or 'Unknown'}</p>
                <p><strong>⭐ Rating:</strong> {provider.rating or 0}/5 ({provider.total_reviews or 0} reviews)</p>
            </div>
            
            <div class="business-hours">
                <h3>🕒 Business Hours</h3>
                <pre>{business_hours_display}</pre>
            </div>
            
            <div class="provider-description">
                <h3>ℹ️ About This Provider</h3>
                <p>{provider.ai_description or 'Professional healthcare provider offering quality medical services.'}</p>
            </div>
            
            <div class="accessibility-info">
                <h3>♿ Accessibility</h3>
                <p><strong>Wheelchair Access:</strong> {self._format_accessibility(provider.wheelchair_accessible)}</p>
                <p><strong>Parking:</strong> {self._format_parking(provider.parking_available)}</p>
            </div>
        </div>
        """
        
        return content.strip()
    
    def _generate_acf_fields(self, provider: Provider) -> Dict[str, Any]:
        """Generate ACF (Advanced Custom Fields) data for WordPress"""
        # This replicates the ACF structure from wordpress_integration.py
        return {
            # Provider Details
            "provider_phone": provider.phone or '',
            "wheelchair_accessible": self._format_wheelchair_accessibility(provider.wheelchair_accessible),
            "parking_available": self._format_parking_availability(provider.parking_available),
            "prefecture": provider.prefecture or '',
            "district": provider.district or '',
            
            # Business Hours
            "business_hours": self._format_business_hours_for_acf(provider.business_hours or {}),
            "hours_monday": self._get_day_hours(provider.business_hours or {}, 'Monday'),
            "hours_tuesday": self._get_day_hours(provider.business_hours or {}, 'Tuesday'),
            "hours_wednesday": self._get_day_hours(provider.business_hours or {}, 'Wednesday'),
            "hours_thursday": self._get_day_hours(provider.business_hours or {}, 'Thursday'),
            "hours_friday": self._get_day_hours(provider.business_hours or {}, 'Friday'),
            "hours_saturday": self._get_day_hours(provider.business_hours or {}, 'Saturday'),
            "hours_sunday": self._get_day_hours(provider.business_hours or {}, 'Sunday'),
            "open_now": self._get_open_now_status(provider.business_hours or {}),
            
            # Location & Navigation
            "latitude": provider.latitude or 0,
            "longitude": provider.longitude or 0,
            "nearest_station": provider.nearest_station or '',
            "google_maps_embed": self._generate_google_maps_embed(provider.latitude, provider.longitude, provider.provider_name, provider.address or ""),
            
            # Language Support
            "english_proficiency": provider.english_proficiency or 'Unknown',
            
            # Photos
            "photo_urls": self._format_photo_urls(provider.photo_urls or []),
            
            # Additional fields
            "provider_website": self._clean_website_url(provider.website or ''),
            "provider_address": self._clean_address(provider.address or ''),
            "provider_rating": str(provider.rating or 0),
            "provider_reviews": str(provider.total_reviews or 0),
            "ai_description": provider.ai_description or '',
            "ai_excerpt": provider.ai_excerpt or '',
            "provider_city": provider.city or '',
        }
    
    def _log_sync_operation(self, provider_id: int, wordpress_post_id: int, sync_type: str, 
                           sync_status: str, duration_ms: int, content_hash: str = None, 
                           error_message: str = None):
        """Log sync operation to database"""
        try:
            session = self.db.Session()
            
            # Insert sync log record
            session.execute(
                text("""
                INSERT INTO wordpress_sync_log 
                (provider_id, wordpress_post_id, sync_type, sync_status, content_hash, 
                 sync_duration_ms, error_message, sync_metadata)
                VALUES (:provider_id, :wordpress_post_id, :sync_type, :sync_status, :content_hash, 
                 :sync_duration_ms, :error_message, :sync_metadata)
                """),
                {
                    'provider_id': provider_id,
                    'wordpress_post_id': wordpress_post_id,
                    'sync_type': sync_type,
                    'sync_status': sync_status,
                    'content_hash': content_hash,
                    'sync_duration_ms': duration_ms,
                    'error_message': error_message,
                    'sync_metadata': json.dumps({'timestamp': datetime.now().isoformat()})
                }
            )
            
            session.commit()
            session.close()
            
        except Exception as e:
            logger.error(f"❌ Error logging sync operation: {str(e)}")
    
    # Helper methods (simplified versions of wordpress_integration.py methods)
    def _format_business_hours_display(self, business_hours: dict) -> str:
        """Format business hours for display"""
        if not business_hours or not isinstance(business_hours, dict):
            return "Hours not available"
        
        # If we have display_text from Google Places, use that
        if 'display_text' in business_hours:
            return "\n".join(business_hours['display_text'])
        
        # Otherwise, format from formatted_hours
        if 'formatted_hours' in business_hours:
            formatted_lines = []
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            for day in days_order:
                if day in business_hours['formatted_hours']:
                    hours = business_hours['formatted_hours'][day]
                    if hours.get('open') and hours.get('close'):
                        formatted_lines.append(f"{day}: {hours['open']} - {hours['close']}")
                    else:
                        formatted_lines.append(f"{day}: Closed")
                else:
                    formatted_lines.append(f"{day}: Hours not available")
            
            return "\n".join(formatted_lines)
        
        return "Hours not available"
    
    def _format_business_hours_for_acf(self, business_hours: dict) -> str:
        """Format business hours for ACF field"""
        if not business_hours or not isinstance(business_hours, dict):
            return ""
        
        # If we have display_text from Google Places, use that
        if 'display_text' in business_hours:
            return "\n".join(business_hours['display_text'])
        
        # Otherwise, format from formatted_hours
        if 'formatted_hours' in business_hours:
            formatted_lines = []
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            for day in days_order:
                if day in business_hours['formatted_hours']:
                    hours = business_hours['formatted_hours'][day]
                    if hours.get('open') and hours.get('close'):
                        formatted_lines.append(f"{day}: {hours['open']} - {hours['close']}")
                    else:
                        formatted_lines.append(f"{day}: Closed")
                else:
                    formatted_lines.append(f"{day}: Hours not available")
            
            return "\n".join(formatted_lines)
        
        return ""
    
    def _get_day_hours(self, business_hours: dict, day: str) -> str:
        """Get hours for specific day"""
        if not business_hours or not isinstance(business_hours, dict):
            return "Hours not available"
        
        if 'formatted_hours' in business_hours and day in business_hours['formatted_hours']:
            hours = business_hours['formatted_hours'][day]
            if hours.get('open') and hours.get('close'):
                return f"{hours['open']} - {hours['close']}"
            else:
                return "Closed"
        
        return "Hours not available"
    
    def _get_open_now_status(self, business_hours: dict) -> str:
        """Get open now status from Google Places data"""
        if not business_hours or not isinstance(business_hours, dict):
            return "Status unknown"
        
        # Use the open_now status from Google Places if available
        if 'open_now' in business_hours:
            return "Open Now" if business_hours['open_now'] else "Closed"
        
        return "Status unknown"
    
    def _format_wheelchair_accessibility(self, accessible) -> str:
        """Format wheelchair accessibility for ACF"""
        if accessible is True or accessible == "true":
            return "Wheelchair accessible"
        elif accessible is False or accessible == "false":
            return "Not wheelchair accessible"
        else:
            return "Wheelchair accessibility unknown"
    
    def _format_parking_availability(self, available) -> str:
        """Format parking availability for ACF"""
        if available is True or available == "true":
            return "Parking is available"
        elif available is False or available == "false":
            return "Parking is not available"
        else:
            return "Parking unknown"
    
    def _format_accessibility(self, accessible) -> str:
        """Format accessibility for display"""
        return self._format_wheelchair_accessibility(accessible)
    
    def _format_parking(self, available) -> str:
        """Format parking for display"""
        return self._format_parking_availability(available)
    
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
    
    def _generate_google_maps_embed(self, latitude: float, longitude: float, provider_name: str, provider_address: str = "") -> str:
        """Generate Google Maps embed code targeting the specific business"""
        if not latitude or not longitude:
            return ""
        
        # Create a search query that targets the specific business
        # This will show the business name and pin like Tokyo Medical University
        if provider_address:
            # Use business name + address for precise targeting
            search_query = f"{provider_name} {provider_address}".replace(" ", "+")
        else:
            # Use business name + coordinates as fallback
            search_query = f"{provider_name} {latitude},{longitude}".replace(" ", "+")
        
        # Use place search rather than raw coordinates for better targeting
        return f'''<iframe 
            width="100%" 
            height="300" 
            frameborder="0" 
            style="border:0" 
            src="https://maps.google.com/maps?q={search_query}&hl=en&z=15&output=embed" 
            allowfullscreen>
        </iframe>'''
    
    def _format_photo_urls(self, photo_urls) -> str:
        """Format photo URLs for ACF - convert to newline-separated format to match WordPress integration"""
        if not photo_urls:
            return ''
        
        try:
            # Parse JSON string to get list of URLs
            if isinstance(photo_urls, str):
                photo_urls_list = json.loads(photo_urls)
            else:
                photo_urls_list = photo_urls
            
            if photo_urls_list and isinstance(photo_urls_list, list):
                # Convert to newline-separated format (same as WordPress integration)
                return '\n'.join(photo_urls_list)
            else:
                return str(photo_urls) if photo_urls else ''
                
        except json.JSONDecodeError:
            # If it's not JSON, return as-is
            return str(photo_urls) if photo_urls else ''
        except Exception as e:
            logger.error(f"❌ Error formatting photo URLs: {str(e)}")
            return str(photo_urls) if photo_urls else '' 