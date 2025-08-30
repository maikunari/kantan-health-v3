#!/usr/bin/env python3
"""
Master Specialty Data Structure for Healthcare Providers
Defines all valid medical specialties - NO dynamic creation allowed
"""

# Primary medical specialties (canonical forms)
PRIMARY_SPECIALTIES = [
    'General Medicine',           # Default for unknown/general practitioners
    'Internal Medicine',         
    'Pediatrics',
    'Obstetrics & Gynecology',
    'Surgery',
    'Orthopedics',
    'Cardiology',
    'Dermatology',
    'Psychiatry',
    'Ophthalmology',
    'ENT',                       # Ear, Nose, Throat
    'Dentistry',                 # All dental services
    'Emergency Medicine',
    'Neurology',
    'Gastroenterology',
    'Endocrinology',
    'Pulmonology',
    'Nephrology',
    'Rheumatology',
    'Urology',
    'Oncology',
    'Hematology',
    'Allergy & Immunology',
    'Infectious Disease',
    'Physical Medicine',
    'Anesthesiology',
    'Radiology',
    'Pathology',
    'Sports Medicine',
    'Plastic Surgery',
    'Vascular Surgery',
    'Neurosurgery',
    'Pediatric Surgery',
    'Pain Management',
    'Geriatrics',
    'Family Medicine',
    'Preventive Medicine',
    'Occupational Medicine',
    'Alternative Medicine'
]

# Duplicate mappings - variations that map to canonical forms
DUPLICATE_MAPPINGS = {
    # General Medicine variations
    'GP': 'General Medicine',
    'General Practice': 'General Medicine',
    'General Practitioner': 'General Medicine',
    'Primary Care': 'General Medicine',
    'PCP': 'General Medicine',
    'Family Doctor': 'Family Medicine',
    'Family Practice': 'Family Medicine',
    
    # Internal Medicine variations
    'Internist': 'Internal Medicine',
    'Internal Med': 'Internal Medicine',
    'IM': 'Internal Medicine',
    
    # Pediatrics variations
    'Pediatrician': 'Pediatrics',
    'Pediatric': 'Pediatrics',
    'Children\'s Doctor': 'Pediatrics',
    'Child Doctor': 'Pediatrics',
    'Kids Doctor': 'Pediatrics',
    
    # OB/GYN variations
    'OBGYN': 'Obstetrics & Gynecology',
    'OB-GYN': 'Obstetrics & Gynecology',
    'OB/GYN': 'Obstetrics & Gynecology',
    'Obstetrics': 'Obstetrics & Gynecology',
    'Gynecology': 'Obstetrics & Gynecology',
    'Gynecologist': 'Obstetrics & Gynecology',
    'Women\'s Health': 'Obstetrics & Gynecology',
    'Maternity': 'Obstetrics & Gynecology',
    
    # Surgery variations
    'Surgeon': 'Surgery',
    'General Surgery': 'Surgery',
    'Surgical': 'Surgery',
    
    # Orthopedics variations
    'Orthopedic': 'Orthopedics',
    'Orthopaedics': 'Orthopedics',
    'Orthopaedic': 'Orthopedics',
    'Orthopedic Surgery': 'Orthopedics',
    'Bone Doctor': 'Orthopedics',
    'Joint Specialist': 'Orthopedics',
    
    # Cardiology variations
    'Cardiologist': 'Cardiology',
    'Heart Doctor': 'Cardiology',
    'Heart Specialist': 'Cardiology',
    'Cardiac': 'Cardiology',
    
    # Dermatology variations
    'Dermatologist': 'Dermatology',
    'Skin Doctor': 'Dermatology',
    'Skin Specialist': 'Dermatology',
    
    # Psychiatry variations
    'Psychiatrist': 'Psychiatry',
    'Mental Health': 'Psychiatry',
    'Psychiatric': 'Psychiatry',
    'Psychology': 'Psychiatry',  # Note: psychologists aren't MDs but grouping for simplicity
    'Psychologist': 'Psychiatry',
    
    # Ophthalmology variations
    'Eye Doctor': 'Ophthalmology',
    'Ophthalmologist': 'Ophthalmology',
    'Eye Specialist': 'Ophthalmology',
    'Optometry': 'Ophthalmology',  # Note: different but grouping for simplicity
    'Optometrist': 'Ophthalmology',
    
    # ENT variations
    'Otolaryngology': 'ENT',
    'Otolaryngologist': 'ENT',
    'Ear Nose Throat': 'ENT',
    'ENT Specialist': 'ENT',
    'Throat Doctor': 'ENT',
    
    # Dentistry variations
    'Dental': 'Dentistry',
    'Dentist': 'Dentistry',
    'Dental Clinic': 'Dentistry',
    'Dental Office': 'Dentistry',
    'Orthodontics': 'Dentistry',
    'Orthodontist': 'Dentistry',
    'Oral Surgery': 'Dentistry',
    'Periodontist': 'Dentistry',
    'Endodontist': 'Dentistry',
    
    # Emergency variations
    'ER': 'Emergency Medicine',
    'Emergency Room': 'Emergency Medicine',
    'Urgent Care': 'Emergency Medicine',
    'Emergency': 'Emergency Medicine',
    'A&E': 'Emergency Medicine',
    
    # Neurology variations
    'Neurologist': 'Neurology',
    'Brain Doctor': 'Neurology',
    'Neurological': 'Neurology',
    
    # Gastroenterology variations
    'GI': 'Gastroenterology',
    'Gastroenterologist': 'Gastroenterology',
    'Digestive': 'Gastroenterology',
    'Stomach Doctor': 'Gastroenterology',
    
    # Other specialties
    'Diabetes': 'Endocrinology',
    'Diabetologist': 'Endocrinology',
    'Hormone': 'Endocrinology',
    'Lung': 'Pulmonology',
    'Lung Doctor': 'Pulmonology',
    'Respiratory': 'Pulmonology',
    'Kidney': 'Nephrology',
    'Kidney Doctor': 'Nephrology',
    'Joint': 'Rheumatology',
    'Arthritis': 'Rheumatology',
    'Urologist': 'Urology',
    'Cancer': 'Oncology',
    'Oncologist': 'Oncology',
    'Blood': 'Hematology',
    'Blood Doctor': 'Hematology',
    'Allergy': 'Allergy & Immunology',
    'Immunology': 'Allergy & Immunology',
    'Rehabilitation': 'Physical Medicine',
    'Physiatry': 'Physical Medicine',
    'Sports Injury': 'Sports Medicine',
    'Cosmetic Surgery': 'Plastic Surgery',
    'Reconstructive Surgery': 'Plastic Surgery',
    'Brain Surgery': 'Neurosurgery',
    'Back Surgery': 'Neurosurgery',
    'Spine': 'Neurosurgery',
    'Pain Clinic': 'Pain Management',
    'Pain Specialist': 'Pain Management',
    'Elderly Care': 'Geriatrics',
    'Senior Care': 'Geriatrics',
    'Preventative': 'Preventive Medicine',
    'Work Medicine': 'Occupational Medicine',
    'Industrial Medicine': 'Occupational Medicine',
    'Holistic': 'Alternative Medicine',
    'Traditional Medicine': 'Alternative Medicine',
    'TCM': 'Alternative Medicine',
    'Acupuncture': 'Alternative Medicine'
}

# Japanese medical terms that might appear (map to English)
JAPANESE_MAPPINGS = {
    '内科': 'Internal Medicine',
    '小児科': 'Pediatrics',
    '産婦人科': 'Obstetrics & Gynecology',
    '外科': 'Surgery',
    '整形外科': 'Orthopedics',
    '心臓内科': 'Cardiology',
    '皮膚科': 'Dermatology',
    '精神科': 'Psychiatry',
    '眼科': 'Ophthalmology',
    '耳鼻咽喉科': 'ENT',
    '歯科': 'Dentistry',
    '救急': 'Emergency Medicine',
    '神経内科': 'Neurology',
    '消化器科': 'Gastroenterology',
    '泌尿器科': 'Urology',
    'クリニック': 'General Medicine',  # Generic "clinic"
    '診療所': 'General Medicine',      # Generic "clinic"
    '医院': 'General Medicine',        # Generic "clinic"
    '病院': 'General Medicine'         # Generic "hospital"
}

# Common search terms for finding English-speaking providers
ENGLISH_SEARCH_TERMS = {
    'General Medicine': [
        'English speaking doctor',
        'International clinic',
        'Foreign friendly doctor',
        'Expat doctor'
    ],
    'Pediatrics': [
        'English speaking pediatrician',
        'International pediatrics',
        'Foreign friendly children doctor'
    ],
    'Obstetrics & Gynecology': [
        'English speaking OBGYN',
        'International women\'s clinic',
        'Foreign friendly maternity'
    ],
    'Dentistry': [
        'English speaking dentist',
        'International dental clinic',
        'Foreign friendly dental'
    ],
    'Emergency Medicine': [
        'English emergency room',
        '24 hour English clinic',
        'International hospital emergency'
    ],
    'Psychiatry': [
        'English speaking psychiatrist',
        'International mental health',
        'English counseling'
    ]
}


class SpecialtyNormalizer:
    """Normalizes and validates medical specialties against master list"""
    
    def __init__(self):
        self.primary_specialties = set(PRIMARY_SPECIALTIES)
        self.duplicate_mappings = DUPLICATE_MAPPINGS.copy()
        self.japanese_mappings = JAPANESE_MAPPINGS.copy()
        
        # Add backward compatibility alias
        self.canonical_specialties = self.primary_specialties
        
        # Default for unknown specialties
        self.default_specialty = 'General Medicine'
    
    def normalize_specialty(self, raw_specialty: str) -> dict:
        """
        Normalize specialty to canonical form
        
        Args:
            raw_specialty: Raw specialty string
            
        Returns:
            Dictionary with normalized specialty and review flag
        """
        if not raw_specialty:
            return {
                'specialty': self.default_specialty,
                'needs_review': True,
                'original_value': raw_specialty,
                'reason': 'empty_specialty'
            }
        
        # Clean and standardize input
        cleaned = raw_specialty.strip()
        
        # Check if it's already a primary specialty
        if cleaned in self.primary_specialties:
            return {
                'specialty': cleaned,
                'needs_review': False
            }
        
        # Check duplicate mappings (case-insensitive)
        for variant, canonical in self.duplicate_mappings.items():
            if cleaned.lower() == variant.lower():
                return {
                    'specialty': canonical,
                    'needs_review': False,
                    'mapped_from': cleaned
                }
        
        # Check Japanese mappings
        if cleaned in self.japanese_mappings:
            return {
                'specialty': self.japanese_mappings[cleaned],
                'needs_review': False,
                'mapped_from_japanese': cleaned
            }
        
        # Try title case
        title_case = cleaned.title()
        if title_case in self.primary_specialties:
            return {
                'specialty': title_case,
                'needs_review': False
            }
        
        # Check if it contains a known specialty
        cleaned_lower = cleaned.lower()
        for specialty in self.primary_specialties:
            if specialty.lower() in cleaned_lower:
                return {
                    'specialty': specialty,
                    'needs_review': True,
                    'original_value': raw_specialty,
                    'reason': 'partial_match'
                }
        
        # Unknown specialty - map to general and flag for review
        return {
            'specialty': self.default_specialty,
            'needs_review': True,
            'original_value': raw_specialty,
            'reason': 'unknown_specialty'
        }
    
    def validate_specialty(self, specialty: str) -> bool:
        """
        Check if specialty is in the primary list
        
        Args:
            specialty: Specialty to validate
            
        Returns:
            True if specialty is valid
        """
        return specialty in self.primary_specialties
    
    def get_search_terms(self, specialty: str) -> list:
        """
        Get English search terms for a specialty
        
        Args:
            specialty: Normalized specialty
            
        Returns:
            List of search terms
        """
        # Use specific terms if available
        if specialty in ENGLISH_SEARCH_TERMS:
            return ENGLISH_SEARCH_TERMS[specialty]
        
        # Generate generic terms
        return [
            f'English speaking {specialty.lower()}',
            f'International {specialty.lower()}',
            f'Foreign friendly {specialty.lower()}'
        ]
    
    def bulk_normalize(self, specialties: list) -> list:
        """
        Normalize multiple specialties at once
        
        Args:
            specialties: List of raw specialties
            
        Returns:
            List of normalized results
        """
        results = []
        for specialty in specialties:
            results.append(self.normalize_specialty(specialty))
        return results
    
    def get_priority_specialties(self) -> list:
        """
        Get specialties most commonly sought by English speakers
        
        Returns:
            List of priority specialties
        """
        return [
            'General Medicine',
            'Pediatrics',
            'Obstetrics & Gynecology',
            'Dentistry',
            'Emergency Medicine',
            'Dermatology',
            'Ophthalmology',
            'ENT',
            'Psychiatry',
            'Orthopedics'
        ]


# Convenience functions
def get_all_valid_specialties() -> set:
    """Get all valid primary specialties as a set"""
    return set(PRIMARY_SPECIALTIES)


def normalize_specialty(raw_specialty: str) -> dict:
    """Normalize a single specialty"""
    normalizer = SpecialtyNormalizer()
    return normalizer.normalize_specialty(raw_specialty)


def get_english_search_terms(specialty: str) -> list:
    """Get English search terms for a specialty"""
    normalizer = SpecialtyNormalizer()
    return normalizer.get_search_terms(specialty)