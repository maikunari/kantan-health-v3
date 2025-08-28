"""
Wrapper for deduplication to provide DuplicateDetector class
"""

from .deduplication import ProviderDeduplicator
from typing import Dict, Tuple, Optional

class DuplicateDetector(ProviderDeduplicator):
    """Class with expected name for duplicate detection"""
    
    def check_duplicate(self, provider_data: Dict) -> Dict:
        """
        Check if provider is a duplicate
        
        Args:
            provider_data: Provider information to check
            
        Returns:
            Dictionary with 'is_duplicate' key and details
        """
        # Generate fingerprints for the provider
        fingerprints = self.generate_fingerprints(provider_data)
        
        # Here we would check against database
        # For now, return not duplicate (would need database integration)
        return {
            'is_duplicate': False,
            'fingerprints': fingerprints,
            'reason': None
        }