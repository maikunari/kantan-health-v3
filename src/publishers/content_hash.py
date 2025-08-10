#!/usr/bin/env python3
"""
Content Hash Service
Detects changes in provider content for selective WordPress updates
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional

from ..core.database import Provider

logger = logging.getLogger(__name__)


class ContentHashService:
    """Service for content change detection using SHA256 hashing"""
    
    def __init__(self):
        """Initialize content hash service"""
        self.tracked_fields = [
            'provider_name',
            'address',
            'city',
            'district',
            'prefecture',
            'phone',
            'website',
            'specialties',
            'english_proficiency',
            'rating',
            'total_reviews',
            'business_hours',
            'ai_description',
            'ai_excerpt',
            'review_summary',
            'english_experience_summary',
            'seo_title',
            'seo_meta_description',
            'selected_featured_image',
            'wheelchair_accessible',
            'parking_available',
            'nearest_station'
        ]
        
        logger.info("✅ Content Hash Service initialized")
    
    def generate_hash(self, provider: Provider) -> str:
        """Generate SHA256 hash of provider content
        
        Args:
            provider: Provider object
            
        Returns:
            SHA256 hash string
        """
        # Collect field values
        content_parts = []
        
        for field in self.tracked_fields:
            value = getattr(provider, field, None)
            
            # Normalize value for consistent hashing
            if value is None:
                normalized = ""
            elif isinstance(value, (list, dict)):
                # Convert to sorted JSON for consistent hashing
                normalized = json.dumps(value, sort_keys=True)
            else:
                normalized = str(value)
            
            content_parts.append(f"{field}:{normalized}")
        
        # Join all parts and generate hash
        content_string = "|".join(content_parts)
        hash_value = hashlib.sha256(content_string.encode('utf-8')).hexdigest()
        
        logger.debug(f"Generated hash for {provider.provider_name}: {hash_value[:8]}...")
        return hash_value
    
    def needs_update(self, provider: Provider) -> bool:
        """Check if provider content has changed since last sync
        
        Args:
            provider: Provider object
            
        Returns:
            True if content has changed, False otherwise
        """
        # No WordPress post yet
        if not provider.wordpress_post_id:
            return True
        
        # No previous hash stored
        if not provider.content_hash:
            return True
        
        # Compare current hash with stored hash
        current_hash = self.generate_hash(provider)
        needs_update = current_hash != provider.content_hash
        
        if needs_update:
            logger.info(f"📝 Content changed for {provider.provider_name}")
        else:
            logger.debug(f"✅ No changes for {provider.provider_name}")
        
        return needs_update
    
    def get_changed_fields(self, provider: Provider) -> List[str]:
        """Get list of fields that have changed
        
        Args:
            provider: Provider object
            
        Returns:
            List of changed field names
        """
        if not provider.content_hash:
            return self.tracked_fields
        
        # This is a simplified version - in practice you might want to
        # store individual field hashes for detailed change tracking
        changed_fields = []
        
        # Check each field for changes
        for field in self.tracked_fields:
            current_value = getattr(provider, field, None)
            
            # For this simplified version, we'll mark critical fields
            # In a full implementation, you'd compare with previous values
            if field in ['ai_description', 'review_summary', 'english_experience_summary']:
                if current_value:
                    changed_fields.append(field)
        
        return changed_fields if changed_fields else ['content']
    
    def compare_providers(self, provider1: Provider, provider2: Provider) -> Dict[str, any]:
        """Compare two provider objects
        
        Args:
            provider1: First provider
            provider2: Second provider
            
        Returns:
            Comparison results
        """
        differences = []
        
        for field in self.tracked_fields:
            value1 = getattr(provider1, field, None)
            value2 = getattr(provider2, field, None)
            
            # Normalize for comparison
            if isinstance(value1, (list, dict)):
                value1 = json.dumps(value1, sort_keys=True)
            if isinstance(value2, (list, dict)):
                value2 = json.dumps(value2, sort_keys=True)
            
            if value1 != value2:
                differences.append({
                    'field': field,
                    'old_value': value1,
                    'new_value': value2
                })
        
        return {
            'has_changes': len(differences) > 0,
            'differences': differences,
            'changed_fields': [d['field'] for d in differences]
        }
    
    def batch_check_updates(self, providers: List[Provider]) -> Dict[int, bool]:
        """Check multiple providers for updates
        
        Args:
            providers: List of providers
            
        Returns:
            Dictionary mapping provider ID to update needed status
        """
        results = {}
        
        for provider in providers:
            results[provider.id] = self.needs_update(provider)
        
        needs_update_count = sum(1 for needed in results.values() if needed)
        logger.info(f"📊 Batch check: {needs_update_count}/{len(providers)} providers need updates")
        
        return results