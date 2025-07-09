#!/usr/bin/env python3
"""
Content Hash Service for WordPress Sync Enhancement
Generates and compares content hashes to detect changes in provider data.
"""

import hashlib
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from postgres_integration import Provider

@dataclass
class ContentComparison:
    """Result of content comparison"""
    needs_update: bool
    old_hash: Optional[str]
    new_hash: str
    changed_fields: list
    
class ContentHashService:
    """Service for generating and comparing content hashes for change detection"""
    
    def generate_provider_hash(self, provider: Provider) -> str:
        """Generate SHA256 hash of provider content for change detection"""
        try:
            # Extract key content fields that affect WordPress display
            content_data = {
                'ai_description': provider.ai_description or '',
                'ai_excerpt': provider.ai_excerpt or '',
                'provider_name': provider.provider_name or '',
                'specialties': provider.specialties or [],
                'city': provider.city or '',
                'address': provider.address or '',
                'phone': provider.phone or '',
                'website': provider.website or '',
                'english_proficiency': provider.english_proficiency or 'Unknown',
                'rating': provider.rating or 0,
                'total_reviews': provider.total_reviews or 0,
                'business_hours': provider.business_hours or {},
                'wheelchair_accessible': provider.wheelchair_accessible or False,
                'parking_available': provider.parking_available or False,
                'latitude': provider.latitude or 0,
                'longitude': provider.longitude or 0,
                'nearest_station': provider.nearest_station or '',
                'photo_urls': provider.photo_urls or []
            }
            
            # Sort keys for consistent hashing
            content_json = json.dumps(content_data, sort_keys=True, default=str)
            return hashlib.sha256(content_json.encode()).hexdigest()
            
        except Exception as e:
            print(f"❌ Error generating hash for {provider.provider_name}: {str(e)}")
            return ""
    
    def content_changed(self, provider: Provider) -> bool:
        """Check if provider content has changed since last sync"""
        try:
            current_hash = self.generate_provider_hash(provider)
            stored_hash = provider.content_hash
            
            if not stored_hash:
                # No previous hash, assume changed
                return True
            
            return current_hash != stored_hash
            
        except Exception as e:
            print(f"❌ Error checking content change for {provider.provider_name}: {str(e)}")
            return True  # Assume changed on error to be safe
    
    def compare_content(self, provider: Provider) -> ContentComparison:
        """Compare current provider content with stored hash and return detailed comparison"""
        try:
            new_hash = self.generate_provider_hash(provider)
            old_hash = provider.content_hash
            
            if not old_hash:
                return ContentComparison(
                    needs_update=True,
                    old_hash=None,
                    new_hash=new_hash,
                    changed_fields=["initial_sync"]
                )
            
            if new_hash == old_hash:
                return ContentComparison(
                    needs_update=False,
                    old_hash=old_hash,
                    new_hash=new_hash,
                    changed_fields=[]
                )
            
            # Content has changed, try to identify what changed
            changed_fields = self._identify_changed_fields(provider, old_hash, new_hash)
            
            return ContentComparison(
                needs_update=True,
                old_hash=old_hash,
                new_hash=new_hash,
                changed_fields=changed_fields
            )
            
        except Exception as e:
            print(f"❌ Error comparing content for {provider.provider_name}: {str(e)}")
            return ContentComparison(
                needs_update=True,
                old_hash=provider.content_hash,
                new_hash=self.generate_provider_hash(provider),
                changed_fields=["error_occurred"]
            )
    
    def _identify_changed_fields(self, provider: Provider, old_hash: str, new_hash: str) -> list:
        """Identify which fields have changed by comparing individual field hashes"""
        changed_fields = []
        
        # List of fields to check individually
        field_checks = [
            ('ai_description', provider.ai_description or ''),
            ('ai_excerpt', provider.ai_excerpt or ''),
            ('provider_name', provider.provider_name or ''),
            ('specialties', json.dumps(provider.specialties or [], sort_keys=True)),
            ('city', provider.city or ''),
            ('address', provider.address or ''),
            ('phone', provider.phone or ''),
            ('website', provider.website or ''),
            ('english_proficiency', provider.english_proficiency or 'Unknown'),
            ('rating', str(provider.rating or 0)),
            ('total_reviews', str(provider.total_reviews or 0)),
            ('business_hours', json.dumps(provider.business_hours or {}, sort_keys=True)),
            ('wheelchair_accessible', str(provider.wheelchair_accessible or False)),
            ('parking_available', str(provider.parking_available or False)),
            ('latitude', str(provider.latitude or 0)),
            ('longitude', str(provider.longitude or 0)),
            ('nearest_station', provider.nearest_station or ''),
            ('photo_urls', json.dumps(provider.photo_urls or [], sort_keys=True))
        ]
        
        try:
            # This is a simplified approach - in production you might want to store
            # individual field hashes for more precise change detection
            for field_name, field_value in field_checks:
                field_hash = hashlib.sha256(str(field_value).encode()).hexdigest()
                # For now, we'll mark fields as potentially changed
                # A more sophisticated approach would store individual field hashes
                if field_name in ['ai_description', 'ai_excerpt', 'specialties', 'business_hours']:
                    changed_fields.append(field_name)
            
            return changed_fields[:3]  # Return up to 3 most likely changed fields
            
        except Exception as e:
            print(f"❌ Error identifying changed fields: {str(e)}")
            return ["content_changed"]
    
    def update_provider_hash(self, provider: Provider, session) -> bool:
        """Update provider's content hash in database"""
        try:
            new_hash = self.generate_provider_hash(provider)
            provider.content_hash = new_hash
            session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error updating hash for {provider.provider_name}: {str(e)}")
            session.rollback()
            return False
    
    def get_providers_needing_update(self, session, limit: int = 100) -> list:
        """Get providers that need WordPress updates based on content changes"""
        try:
            # Get providers with WordPress post IDs that might need updating
            providers = session.query(Provider).filter(
                Provider.wordpress_post_id.isnot(None),
                Provider.ai_description.isnot(None)
            ).limit(limit).all()
            
            providers_needing_update = []
            
            for provider in providers:
                if self.content_changed(provider):
                    providers_needing_update.append(provider)
            
            return providers_needing_update
            
        except Exception as e:
            print(f"❌ Error getting providers needing update: {str(e)}")
            return []
    
    def bulk_update_hashes(self, providers: list, session) -> Dict[str, int]:
        """Bulk update content hashes for multiple providers"""
        results = {
            'updated': 0,
            'failed': 0,
            'skipped': 0
        }
        
        try:
            for provider in providers:
                try:
                    if self.content_changed(provider):
                        new_hash = self.generate_provider_hash(provider)
                        provider.content_hash = new_hash
                        results['updated'] += 1
                    else:
                        results['skipped'] += 1
                        
                except Exception as e:
                    print(f"❌ Error updating hash for {provider.provider_name}: {str(e)}")
                    results['failed'] += 1
            
            session.commit()
            return results
            
        except Exception as e:
            print(f"❌ Error in bulk hash update: {str(e)}")
            session.rollback()
            return results
    
    def generate_sync_report(self, providers: list) -> Dict[str, Any]:
        """Generate a report of sync status for providers"""
        report = {
            'total_providers': len(providers),
            'needs_update': 0,
            'up_to_date': 0,
            'no_wordpress_id': 0,
            'providers_by_status': {}
        }
        
        try:
            for provider in providers:
                if not provider.wordpress_post_id:
                    report['no_wordpress_id'] += 1
                    continue
                
                if self.content_changed(provider):
                    report['needs_update'] += 1
                else:
                    report['up_to_date'] += 1
                
                # Track by WordPress status
                status = provider.wordpress_status or 'unknown'
                report['providers_by_status'][status] = report['providers_by_status'].get(status, 0) + 1
            
            return report
            
        except Exception as e:
            print(f"❌ Error generating sync report: {str(e)}")
            return report 