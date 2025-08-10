#!/usr/bin/env python3
"""
Provider Fingerprinting System
Creates unique, reliable identifiers for healthcare providers to prevent duplicates
even when Google Place IDs are missing or inconsistent.

This system generates multiple types of fingerprints:
1. Primary fingerprint: name + normalized address
2. Secondary fingerprint: name + phone number  
3. Fuzzy fingerprint: for catching minor variations

Usage:
    fingerprinter = ProviderFingerprinter()
    fingerprint = fingerprinter.generate_primary_fingerprint(provider_data)
    is_duplicate = fingerprinter.check_duplicate(provider_data, existing_fingerprints)
"""

import re
import hashlib
import unicodedata
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ProviderFingerprints:
    """Container for all fingerprint types for a provider"""
    primary: str           # name + normalized address
    secondary: str         # name + phone  
    fuzzy: str            # fuzzy matching fingerprint
    google_place_id: Optional[str] = None

class ProviderFingerprinter:
    """Generates reliable fingerprints for healthcare provider deduplication"""
    
    def __init__(self):
        # Common variations and synonyms for healthcare names
        self.name_normalizations = {
            # Common suffixes
            'clinic': 'clinic',
            'クリニック': 'clinic', 
            'hospital': 'hospital',
            '病院': 'hospital',
            'center': 'center',
            'centre': 'center',
            'センター': 'center',
            # Common prefixes/titles
            'dr.': 'dr',
            'doctor': 'dr',
            'prof.': 'prof',
            'professor': 'prof',
            # Common separators
            ' - ': ' ',
            ' – ': ' ',
            ' | ': ' ',
            '/': ' ',
            '・': ' ',
            # Common abbreviations
            'int\'l': 'international',
            'intl': 'international',
            'med': 'medical',
            'hosp': 'hospital',
        }
        
        # Address normalizations  
        self.address_normalizations = {
            # Japanese address components
            '丁目': 'chome',
            '番地': 'banchi', 
            '号': 'go',
            '市': 'shi',
            '区': 'ku',
            '町': 'machi',
            '村': 'mura',
            # English variations
            'street': 'st',
            'avenue': 'ave',
            'boulevard': 'blvd',
            'building': 'bldg',
            'apartment': 'apt',
            'floor': 'fl',
            # Remove common noise
            'japan': '',
            '日本': '',
            'tokyo': '',
            '東京': '',
            'yokohama': '',
            '横浜': '',
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for consistent fingerprinting"""
        if not text:
            return ""
            
        # Convert to lowercase and strip
        text = text.lower().strip()
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKC', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common punctuation that varies
        text = re.sub(r'[.,;:!?()"\'\[\]{}]', '', text)
        
        # Apply text normalizations
        for original, replacement in self.name_normalizations.items():
            text = text.replace(original, replacement)
            
        return text.strip()
    
    def normalize_address(self, address: str) -> str:
        """Normalize address for consistent fingerprinting"""
        if not address:
            return ""
            
        address = self.normalize_text(address)
        
        # Apply address-specific normalizations
        for original, replacement in self.address_normalizations.items():
            address = address.replace(original, replacement)
        
        # Extract and normalize key components
        # Remove building/floor details that often vary
        address = re.sub(r'\b\d+f\b|\b\d+fl\b|\bfloor\s*\d+\b', '', address)
        address = re.sub(r'\bapt\s*\d+\b|\bunit\s*\d+\b', '', address)
        
        # Normalize spacing
        address = re.sub(r'\s+', ' ', address).strip()
        
        return address
    
    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number for consistent fingerprinting"""
        if not phone:
            return ""
            
        # Extract only digits
        phone = re.sub(r'[^\d]', '', phone)
        
        # Remove country codes for consistency
        if phone.startswith('81') and len(phone) > 10:  # Japan country code
            phone = phone[2:]
        elif phone.startswith('1') and len(phone) == 11:  # US country code
            phone = phone[1:]
            
        return phone
    
    def generate_primary_fingerprint(self, provider_data: Dict) -> str:
        """Generate primary fingerprint: normalized name + address"""
        name = self.normalize_text(provider_data.get('provider_name', ''))
        address = self.normalize_address(provider_data.get('address', ''))
        city = self.normalize_text(provider_data.get('city', ''))
        
        # Combine components
        fingerprint_text = f"{name}|{address}|{city}"
        
        # Generate hash
        return hashlib.md5(fingerprint_text.encode('utf-8')).hexdigest()
    
    def generate_secondary_fingerprint(self, provider_data: Dict) -> str:
        """Generate secondary fingerprint: normalized name + phone"""
        name = self.normalize_text(provider_data.get('provider_name', ''))
        phone = self.normalize_phone(provider_data.get('phone', ''))
        city = self.normalize_text(provider_data.get('city', ''))
        
        if not phone:
            return ""  # Can't generate without phone
            
        fingerprint_text = f"{name}|{phone}|{city}"
        return hashlib.md5(fingerprint_text.encode('utf-8')).hexdigest()
    
    def generate_fuzzy_fingerprint(self, provider_data: Dict) -> str:
        """Generate fuzzy fingerprint for catching variations"""
        name = provider_data.get('provider_name', '')
        
        # Extract key words from name (skip common words)
        words = self.normalize_text(name).split()
        significant_words = []
        
        skip_words = {
            'clinic', 'hospital', 'center', 'medical', 'dr', 'prof', 
            'the', 'and', 'of', 'in', 'at', 'for', 'with'
        }
        
        for word in words:
            if len(word) > 2 and word not in skip_words:
                significant_words.append(word)
        
        # Sort words to handle reordering
        significant_words.sort()
        
        city = self.normalize_text(provider_data.get('city', ''))
        fingerprint_text = f"{''.join(significant_words)}|{city}"
        
        return hashlib.md5(fingerprint_text.encode('utf-8')).hexdigest()
    
    def generate_all_fingerprints(self, provider_data: Dict) -> ProviderFingerprints:
        """Generate all fingerprint types for a provider"""
        return ProviderFingerprints(
            primary=self.generate_primary_fingerprint(provider_data),
            secondary=self.generate_secondary_fingerprint(provider_data),
            fuzzy=self.generate_fuzzy_fingerprint(provider_data),
            google_place_id=provider_data.get('google_place_id')
        )
    
    def check_duplicate(self, provider_data: Dict, existing_fingerprints: Set[str]) -> Tuple[bool, str]:
        """Check if provider is duplicate against existing fingerprints
        
        Returns:
            (is_duplicate, matching_fingerprint_type)
        """
        fingerprints = self.generate_all_fingerprints(provider_data)
        
        # Check Google Place ID first (most reliable)
        if fingerprints.google_place_id and fingerprints.google_place_id in existing_fingerprints:
            return True, "google_place_id"
        
        # Check primary fingerprint
        if fingerprints.primary in existing_fingerprints:
            return True, "primary"
            
        # Check secondary fingerprint (if available)
        if fingerprints.secondary and fingerprints.secondary in existing_fingerprints:
            return True, "secondary"
            
        # Check fuzzy fingerprint (more permissive)
        if fingerprints.fuzzy in existing_fingerprints:
            return True, "fuzzy"
        
        return False, "none"
    
    def debug_fingerprints(self, provider_data: Dict) -> Dict:
        """Generate debug information about fingerprints"""
        fingerprints = self.generate_all_fingerprints(provider_data)
        
        return {
            'provider_name': provider_data.get('provider_name'),
            'normalized_name': self.normalize_text(provider_data.get('provider_name', '')),
            'normalized_address': self.normalize_address(provider_data.get('address', '')),
            'normalized_phone': self.normalize_phone(provider_data.get('phone', '')),
            'fingerprints': {
                'primary': fingerprints.primary,
                'secondary': fingerprints.secondary,
                'fuzzy': fingerprints.fuzzy,
                'google_place_id': fingerprints.google_place_id
            }
        }

# Utility functions for integration
def generate_provider_fingerprints(provider_data: Dict) -> ProviderFingerprints:
    """Convenience function to generate fingerprints"""
    fingerprinter = ProviderFingerprinter()
    return fingerprinter.generate_all_fingerprints(provider_data)

def is_duplicate_provider(provider_data: Dict, existing_fingerprints: Set[str]) -> bool:
    """Convenience function to check for duplicates"""
    fingerprinter = ProviderFingerprinter()
    is_dup, _ = fingerprinter.check_duplicate(provider_data, existing_fingerprints)
    return is_dup

if __name__ == "__main__":
    # Test the fingerprinting system
    fingerprinter = ProviderFingerprinter()
    
    # Test cases
    test_providers = [
        {
            'provider_name': 'Yokohama International Clinic',
            'address': '1-2-3 Minato Mirai, Nishi-ku, Yokohama',
            'city': 'Yokohama',
            'phone': '+81-45-123-4567'
        },
        {
            'provider_name': 'yokohama international clinic',  # Case variation
            'address': '1-2-3 Minato Mirai Nishi-ku Yokohama',  # Punctuation variation
            'city': 'Yokohama',
            'phone': '045-123-4567'  # Phone format variation
        },
        {
            'provider_name': 'Yu Skin Clinic - Yokohama',
            'address': '4-5-6 Kohoku New Town, Yokohama',
            'city': 'Yokohama',
            'phone': '+81-45-987-6543'
        }
    ]
    
    print("🔍 PROVIDER FINGERPRINTING TEST")
    print("=" * 60)
    
    for i, provider in enumerate(test_providers, 1):
        print(f"\n📋 Provider {i}: {provider['provider_name']}")
        debug_info = fingerprinter.debug_fingerprints(provider)
        
        print(f"   Normalized name: {debug_info['normalized_name']}")
        print(f"   Normalized address: {debug_info['normalized_address']}")
        print(f"   Primary fingerprint: {debug_info['fingerprints']['primary']}")
        print(f"   Secondary fingerprint: {debug_info['fingerprints']['secondary']}")
        print(f"   Fuzzy fingerprint: {debug_info['fingerprints']['fuzzy']}")
    
    # Test duplicate detection
    print(f"\n🔍 Testing duplicate detection:")
    fp1 = fingerprinter.generate_all_fingerprints(test_providers[0])
    is_dup, match_type = fingerprinter.check_duplicate(
        test_providers[1], 
        {fp1.primary, fp1.secondary, fp1.fuzzy}
    )
    print(f"Provider 1 vs 2: {'DUPLICATE' if is_dup else 'UNIQUE'} (matched on: {match_type})") 