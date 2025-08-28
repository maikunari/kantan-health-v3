"""
Master data structures for healthcare provider campaign
"""

from .master_locations import (
    MAJOR_CITIES,
    TOKYO_SPECIAL_WARDS,
    INTERNATIONAL_DISTRICTS,
    PREFECTURES,
    LocationValidator,
    get_all_valid_locations,
    get_english_priority_locations
)

from .master_specialties import (
    PRIMARY_SPECIALTIES,
    DUPLICATE_MAPPINGS,
    SpecialtyNormalizer,
    get_all_valid_specialties,
    normalize_specialty,
    get_english_search_terms
)

__all__ = [
    # Locations
    'MAJOR_CITIES',
    'TOKYO_SPECIAL_WARDS',
    'INTERNATIONAL_DISTRICTS',
    'PREFECTURES',
    'LocationValidator',
    'get_all_valid_locations',
    'get_english_priority_locations',
    
    # Specialties
    'PRIMARY_SPECIALTIES',
    'DUPLICATE_MAPPINGS',
    'SpecialtyNormalizer',
    'get_all_valid_specialties',
    'normalize_specialty',
    'get_english_search_terms'
]