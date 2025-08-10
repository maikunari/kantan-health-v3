#!/usr/bin/env python3
"""
Photo URL Management System
Handles photo reference storage and on-demand URL generation
"""

import os
import logging
from typing import List, Optional
from datetime import datetime

from ..core.cache import PersistentCache
from ..core.cost_tracker import CostTracker

logger = logging.getLogger(__name__)


class PhotoURLManager:
    """Manages photo references and generates URLs on demand"""
    
    def __init__(self):
        """Initialize photo manager"""
        self.api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY not found")
        
        self.cache = PersistentCache()
        self.cost_tracker = CostTracker()
        self.photo_base_url = "https://maps.googleapis.com/maps/api/place/photo"
        
        logger.info("✅ Photo URL Manager initialized")
    
    def store_photo_references(self, place_id: str, photo_data: List[dict]) -> List[str]:
        """Store photo references permanently
        
        Args:
            place_id: Google Place ID
            photo_data: List of photo objects from Google Places API
            
        Returns:
            List of photo references
        """
        if not photo_data:
            return []
        
        # Extract references (limit to 4 photos)
        references = []
        for photo in photo_data[:4]:
            ref = photo.get('photo_reference')
            if ref:
                references.append(ref)
        
        # Store permanently in cache
        if references:
            self.cache.set_photo_references(place_id, references)
            logger.info(f"💾 Stored {len(references)} photo references for {place_id}")
        
        return references
    
    def get_photo_urls(self, provider_data: dict, max_photos: int = 4) -> List[str]:
        """Get photo URLs for a provider (generates on demand)
        
        Args:
            provider_data: Provider data with place_id or photo_references
            max_photos: Maximum number of photos to return
            
        Returns:
            List of photo URLs
        """
        # Try to get references from provider data first
        references = provider_data.get('photo_references', [])
        
        # If not in provider data, check cache
        if not references:
            place_id = provider_data.get('google_place_id')
            if place_id:
                references = self.cache.get_photo_references(place_id) or []
        
        if not references:
            logger.warning(f"No photo references found for provider")
            return []
        
        # Generate URLs for requested photos
        urls = []
        for ref in references[:max_photos]:
            url = self._generate_photo_url(ref)
            if url:
                urls.append(url)
        
        return urls
    
    def get_photo_urls_with_caching(self, provider_data: dict, 
                                   max_photos: int = 4,
                                   check_budget: bool = True) -> List[str]:
        """Get photo URLs with URL caching and budget checks
        
        Args:
            provider_data: Provider data
            max_photos: Maximum photos to return
            check_budget: Whether to check cost budget
            
        Returns:
            List of photo URLs
        """
        references = provider_data.get('photo_references', [])
        place_id = provider_data.get('google_place_id')
        
        # Get references from cache if needed
        if not references and place_id:
            references = self.cache.get_photo_references(place_id) or []
        
        if not references:
            return []
        
        urls = []
        
        for ref in references[:max_photos]:
            # Check URL cache first (12-hour TTL)
            cache_key = f"photo_url_{ref[:16]}"  # Use first 16 chars of reference
            cached_url = self.cache.get(cache_key, 'photo_url')
            
            if cached_url:
                urls.append(cached_url)
                logger.debug(f"✅ Using cached photo URL")
                self.cost_tracker.log_request('photos', place_id=place_id, cached=True)
            else:
                # Check budget if requested
                if check_budget:
                    can_proceed, reason = self.cost_tracker.can_make_request('photos')
                    if not can_proceed:
                        logger.warning(f"❌ Skipping photo due to budget: {reason}")
                        continue
                
                # Generate new URL
                url = self._generate_photo_url(ref)
                if url:
                    urls.append(url)
                    # Cache for 12 hours
                    self.cache.set(cache_key, url, 'photo_url', ttl_days=0.5)
                    # Log cost
                    self.cost_tracker.log_request('photos', place_id=place_id)
        
        return urls
    
    def _generate_photo_url(self, photo_reference: str, 
                           max_width: int = 800) -> Optional[str]:
        """Generate a photo URL from reference
        
        Args:
            photo_reference: Google photo reference
            max_width: Maximum width in pixels
            
        Returns:
            Photo URL or None
        """
        if not photo_reference:
            return None
        
        # Build URL with parameters
        params = {
            'photoreference': photo_reference,
            'maxwidth': max_width,
            'key': self.api_key
        }
        
        # Construct URL
        param_string = '&'.join(f"{k}={v}" for k, v in params.items())
        url = f"{self.photo_base_url}?{param_string}"
        
        logger.debug(f"🖼️ Generated photo URL")
        return url
    
    def prefetch_urls_for_sync(self, providers: List[dict], 
                              max_photos_per_provider: int = 4) -> dict:
        """Prefetch photo URLs for a batch of providers (for WordPress sync)
        
        Args:
            providers: List of provider dictionaries
            max_photos_per_provider: Max photos per provider
            
        Returns:
            Dictionary mapping provider IDs to photo URLs
        """
        photo_urls = {}
        
        # Check total budget
        total_photos = len(providers) * max_photos_per_provider
        can_proceed, reason = self.cost_tracker.can_make_request('photos', 
                                                               estimated_count=total_photos)
        
        if not can_proceed:
            logger.warning(f"❌ Cannot prefetch photos: {reason}")
            return photo_urls
        
        for provider in providers:
            provider_id = provider.get('id')
            if not provider_id:
                continue
            
            # Get URLs with caching
            urls = self.get_photo_urls_with_caching(provider, 
                                                   max_photos=max_photos_per_provider,
                                                   check_budget=False)  # Already checked above
            
            if urls:
                photo_urls[provider_id] = urls
        
        logger.info(f"📸 Prefetched photos for {len(photo_urls)} providers")
        return photo_urls
    
    def cleanup_expired_urls(self) -> int:
        """Clean up expired photo URL cache entries
        
        Returns:
            Number of entries cleaned
        """
        return self.cache.cleanup_expired()
    
    def get_photo_stats(self) -> dict:
        """Get photo-related statistics
        
        Returns:
            Dictionary with photo stats
        """
        cache_stats = self.cache.get_cache_stats()
        cost_stats = self.cost_tracker.get_usage_stats(days=7)
        
        # Extract photo-specific costs
        photo_costs = 0
        photo_requests = 0
        
        for item in cost_stats.get('by_type', []):
            if item['type'] == 'photos':
                photo_costs = item['cost']
                photo_requests = item['count']
                break
        
        return {
            'cached_urls': cache_stats.get('by_type', {}).get('photo_url', 0),
            'total_references_stored': cache_stats.get('by_type', {}).get('photo_references', 0),
            'photo_requests_7d': photo_requests,
            'photo_costs_7d': photo_costs,
            'cache_hit_rate': cost_stats.get('cache_rate', 0)
        }