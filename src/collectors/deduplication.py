#!/usr/bin/env python3
"""
Provider Deduplication System
Uses fingerprinting to detect duplicate providers
"""

import hashlib
import re
import unicodedata
from typing import Dict, Optional
import logging

# For compatibility - import the wrapper class
try:
    from .duplicate_detector import DuplicateDetector
except ImportError:
    pass

logger = logging.getLogger(__name__)


class ProviderDeduplicator:
    """Fingerprint-based deduplication for healthcare providers"""
    
    def __init__(self):
        """Initialize the deduplicator"""
        logger.info("✅ Provider deduplicator initialized")
    
    def generate_fingerprints(self, provider_data: Dict) -> Dict[str, str]:
        """Generate multiple fingerprints for duplicate detection
        
        Args:
            provider_data: Provider information dictionary
            
        Returns:
            Dictionary with fingerprint values
        """
        # Extract key fields
        name = provider_data.get('provider_name', '')
        address = provider_data.get('address', '')
        phone = provider_data.get('phone', '')
        city = provider_data.get('city', '')
        
        # Generate fingerprints
        primary = self._generate_primary_fingerprint(name, address, city)
        secondary = self._generate_secondary_fingerprint(name, phone, city)
        fuzzy = self._generate_fuzzy_fingerprint(name, city)
        
        return {
            'primary_fingerprint': primary,
            'secondary_fingerprint': secondary,
            'fuzzy_fingerprint': fuzzy
        }
    
    def _generate_primary_fingerprint(self, name: str, address: str, city: str) -> str:
        """Generate primary fingerprint from name + address + city
        
        Args:
            name: Provider name
            address: Provider address
            city: City name
            
        Returns:
            MD5 hash fingerprint
        """
        # Normalize components
        norm_name = self._normalize_text(name)
        norm_address = self._normalize_address(address)
        norm_city = self._normalize_text(city)
        
        # Combine and hash
        combined = f"{norm_name}|{norm_address}|{norm_city}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def _generate_secondary_fingerprint(self, name: str, phone: str, city: str) -> str:
        """Generate secondary fingerprint from name + phone + city
        
        Args:
            name: Provider name
            phone: Phone number
            city: City name
            
        Returns:
            MD5 hash fingerprint
        """
        # Normalize components
        norm_name = self._normalize_text(name)
        norm_phone = self._normalize_phone(phone)
        norm_city = self._normalize_text(city)
        
        # Combine and hash
        combined = f"{norm_name}|{norm_phone}|{norm_city}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def _generate_fuzzy_fingerprint(self, name: str, city: str) -> str:
        """Generate fuzzy fingerprint for approximate matching
        
        Args:
            name: Provider name
            city: City name
            
        Returns:
            MD5 hash fingerprint
        """
        # Extract key words from name
        keywords = self._extract_keywords(name)
        norm_city = self._normalize_text(city)
        
        # Combine and hash
        combined = f"{keywords}|{norm_city}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent comparison
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove unicode accents
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Remove special characters
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _normalize_address(self, address: str) -> str:
        """Normalize address for comparison
        
        Args:
            address: Address string
            
        Returns:
            Normalized address
        """
        if not address:
            return ""
        
        # Basic normalization
        address = self._normalize_text(address)
        
        # Remove common variations
        replacements = {
            'street': 'st',
            'avenue': 'ave',
            'road': 'rd',
            'building': 'bldg',
            'floor': 'fl',
            'japan': '',
            'tokyo': '',
            'ku': ''
        }
        
        for old, new in replacements.items():
            address = address.replace(old, new)
        
        # Extract just numbers and key words
        parts = address.split()
        key_parts = []
        
        for part in parts:
            # Keep numbers
            if any(c.isdigit() for c in part):
                key_parts.append(part)
            # Keep short words (likely important)
            elif len(part) <= 3:
                key_parts.append(part)
        
        return ' '.join(key_parts)
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number
        
        Args:
            phone: Phone number string
            
        Returns:
            Normalized phone number
        """
        if not phone:
            return ""
        
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Remove country code if present
        if digits.startswith('81'):
            digits = digits[2:]
        elif digits.startswith('+81'):
            digits = digits[3:]
        
        # Remove leading 0 if present
        if digits.startswith('0'):
            digits = digits[1:]
        
        return digits
    
    def _extract_keywords(self, name: str) -> str:
        """Extract keywords from provider name
        
        Args:
            name: Provider name
            
        Returns:
            Space-separated keywords
        """
        if not name:
            return ""
        
        # Normalize first
        name = self._normalize_text(name)
        
        # Remove common medical terms
        stop_words = {
            'clinic', 'hospital', 'medical', 'center', 'centre',
            'healthcare', 'health', 'care', 'international',
            'クリニック', 'クリニツク', '病院', '医院', '診療所',
            'the', 'a', 'an', 'and', 'or', 'of', 'in'
        }
        
        # Split and filter
        words = name.split()
        keywords = []
        
        for word in words:
            if word not in stop_words and len(word) > 2:
                keywords.append(word)
        
        # Sort for consistency
        keywords.sort()
        
        return ' '.join(keywords[:3])  # Limit to 3 most significant words
    
    def calculate_similarity(self, provider1: Dict, provider2: Dict) -> float:
        """Calculate similarity score between two providers
        
        Args:
            provider1: First provider data
            provider2: Second provider data
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        score = 0.0
        
        # Compare fingerprints
        fp1 = self.generate_fingerprints(provider1)
        fp2 = self.generate_fingerprints(provider2)
        
        # Exact match on primary fingerprint
        if fp1['primary_fingerprint'] == fp2['primary_fingerprint']:
            return 1.0
        
        # Exact match on secondary fingerprint
        if fp1['secondary_fingerprint'] == fp2['secondary_fingerprint']:
            score += 0.8
        
        # Fuzzy match
        if fp1['fuzzy_fingerprint'] == fp2['fuzzy_fingerprint']:
            score += 0.5
        
        # Additional checks
        if provider1.get('phone') and provider1.get('phone') == provider2.get('phone'):
            score += 0.3
        
        # Cap at 1.0
        return min(1.0, score)