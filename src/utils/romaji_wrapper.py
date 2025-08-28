"""
Wrapper for romaji converter to provide BusinessNameRomajiConverter class
"""

from .romaji_converter import convert_to_romaji, contains_japanese

class BusinessNameRomajiConverter:
    """Class wrapper for romaji conversion functions"""
    
    def __init__(self):
        """Initialize the converter"""
        pass
    
    def convert_business_name_intelligently(self, text: str) -> str:
        """
        Convert business name from Japanese to romaji intelligently
        
        Args:
            text: Business name in Japanese or mixed text
            
        Returns:
            Romaji version with proper medical term translation
        """
        return convert_to_romaji(text, preserve_non_japanese=True)
    
    def convert(self, text: str) -> str:
        """Alias for convert_business_name_intelligently"""
        return self.convert_business_name_intelligently(text)
    
    def contains_japanese(self, text: str) -> bool:
        """Check if text contains Japanese characters"""
        return contains_japanese(text)