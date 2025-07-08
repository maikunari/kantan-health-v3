"""
Medical Specialty Filter and Extraction System
Validates and extracts legitimate medical specialties while filtering out garbage terms
"""

import re
import json
from typing import List, Set, Dict
from textblob import TextBlob

class MedicalSpecialtyFilter:
    """Filters and validates medical specialties, removing garbage terms"""
    
    def __init__(self):
        # Comprehensive list of legitimate medical specialties and related terms
        self.valid_medical_specialties = {
            # Primary Medical Specialties
            'allergy', 'allergist', 'allergy immunology',
            'anesthesiology', 'anesthesiologist', 'anesthesia',
            'cardiology', 'cardiologist', 'heart doctor', 'cardiac',
            'dermatology', 'dermatologist', 'skin doctor', 'skin care',
            'emergency medicine', 'emergency doctor', 'emergency care', 'er doctor',
            'endocrinology', 'endocrinologist', 'hormone doctor', 'diabetes',
            'family medicine', 'family doctor', 'family practitioner',
            'gastroenterology', 'gastroenterologist', 'gi doctor', 'digestive',
            'general practitioner', 'general medicine', 'gp', 'internal medicine',
            'geriatrics', 'geriatrician', 'elderly care', 'senior care',
            'gynecology', 'gynecologist', 'womens health', 'obstetrics', 'obgyn',
            'hematology', 'hematologist', 'blood doctor',
            'infectious disease', 'infection specialist',
            'nephrology', 'nephrologist', 'kidney doctor',
            'neurology', 'neurologist', 'brain doctor', 'nervous system',
            'oncology', 'oncologist', 'cancer doctor', 'cancer treatment',
            'ophthalmology', 'ophthalmologist', 'eye doctor', 'vision',
            'orthopedics', 'orthopedic surgeon', 'bone doctor', 'joint doctor',
            'otolaryngology', 'ent', 'ear nose throat', 'ent doctor',
            'pathology', 'pathologist',
            'pediatrics', 'pediatrician', 'childrens doctor', 'kids doctor',
            'psychiatry', 'psychiatrist', 'mental health', 'therapy',
            'pulmonology', 'pulmonologist', 'lung doctor', 'respiratory',
            'radiology', 'radiologist', 'imaging', 'xray',
            'rheumatology', 'rheumatologist', 'arthritis doctor',
            'urology', 'urologist', 'kidney bladder',
            
            # Surgical Specialties
            'surgery', 'surgeon', 'surgical',
            'cardiac surgery', 'heart surgery',
            'neurosurgery', 'brain surgery',
            'orthopedic surgery', 'bone surgery',
            'plastic surgery', 'cosmetic surgery', 'reconstructive surgery',
            'thoracic surgery', 'chest surgery',
            'vascular surgery', 'blood vessel surgery',
            
            # Dental Specialties
            'dentistry', 'dentist', 'dental', 'oral health',
            'orthodontics', 'orthodontist', 'braces',
            'periodontics', 'periodontist', 'gum disease',
            'endodontics', 'endodontist', 'root canal',
            'oral surgery', 'oral surgeon',
            'prosthodontics', 'prosthodontist',
            
            # Alternative Medicine
            'acupuncture', 'acupuncturist',
            'chiropractic', 'chiropractor',
            'naturopathy', 'naturopath',
            'homeopathy', 'homeopath',
            
            # Allied Health
            'physical therapy', 'physiotherapy', 'physiotherapist',
            'occupational therapy', 'occupational therapist',
            'speech therapy', 'speech therapist',
            'nutrition', 'nutritionist', 'dietitian',
            'pharmacy', 'pharmacist',
            'nursing', 'nurse', 'nurse practitioner',
            'midwifery', 'midwife',
            
            # Medical Services (specific procedures/treatments)
            'vaccination', 'immunization',
            'health screening', 'health checkup', 'physical exam',
            'diagnostic imaging', 'ultrasound', 'mri', 'ct scan',
            'laboratory', 'lab services', 'blood test',
            'rehabilitation', 'rehab',
            'pain management', 'pain clinic',
            'sleep medicine', 'sleep study',
            'weight loss', 'bariatric',
            'fertility', 'reproductive health',
            'travel medicine', 'travel clinic',
            'occupational health', 'workplace health',
            'sports medicine', 'sports injury',
            'aesthetic medicine', 'cosmetic treatment',
        }
        
        # Terms that should NEVER be considered medical specialties
        self.garbage_terms = {
            # Generic Google Places types
            'point_of_interest', 'establishment', 'health', 'doctor', 'hospital',
            'clinic', 'medical_center', 'medical', 'care', 'center', 'facility',
            
            # Geographic terms
            'tokyo', 'yokohama', 'osaka', 'nagoya', 'kyoto', 'fukuoka', 'hiroshima',
            'sendai', 'saitama', 'chiba', 'kobe', 'kawasaki', 'city', 'prefecture',
            'district', 'ward', 'area', 'region', 'japan', 'japanese',
            
            # Generic business terms
            'international', 'global', 'premium', 'modern', 'advanced', 'professional',
            'quality', 'best', 'top', 'leading', 'premier', 'excellence', 'comprehensive',
            'specialized', 'expert', 'experienced', 'certified', 'licensed',
            
            # Common words and particles
            'and', 'or', 'the', 'of', 'in', 'at', 'for', 'with', 'by', 'to', 'from',
            'on', 'off', 'up', 'down', 'out', 'over', 'under', 'about', 'into',
            'through', 'during', 'before', 'after', 'above', 'below', 'between',
            
            # Business name fragments  
            'ladies', 'mens', 'women', 'men', 'family', 'general', 'total', 'complete',
            'full', 'whole', 'all', 'every', 'each', 'some', 'many', 'most', 'few',
            
            # Punctuation and symbols
            '|', '-', '_', '&', '+', '/', '\\', '(', ')', '[', ']', '{', '}',
            ':', ';', ',', '.', '?', '!', '@', '#', '$', '%', '^', '*',
            
            # Non-medical services
            'beauty_salon', 'hair_care', 'spa', 'massage', 'fitness', 'gym',
            'restaurant', 'shopping', 'retail', 'finance', 'banking', 'insurance',
            
            # Single letters and short fragments
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            'dr', 'prof', 'mr', 'mrs', 'ms',
            
            # Common provider name fragments
            'clinic', 'hospital', 'center', 'centre', 'institute', 'academy',
            'university', 'college', 'school', 'building', 'tower', 'plaza',
            'medical', 'healthcare', 'health', 'wellness', 'life', 'care'
        }
        
        # Medical specialty groupings for better organization
        self.specialty_groups = {
            'Primary Care': [
                'general_practitioner', 'family_medicine', 'internal_medicine'
            ],
            'Pediatrics': [
                'pediatrics', 'pediatrician', 'childrens_doctor'
            ],
            'Women\'s Health': [
                'gynecology', 'obstetrics', 'womens_health', 'fertility'
            ],
            'Mental Health': [
                'psychiatry', 'psychology', 'mental_health', 'therapy'
            ],
            'Surgical': [
                'surgery', 'orthopedic_surgery', 'plastic_surgery', 'cardiac_surgery'
            ],
            'Dental': [
                'dentistry', 'orthodontics', 'oral_surgery', 'periodontics'
            ],
            'Diagnostic': [
                'radiology', 'pathology', 'laboratory', 'imaging'
            ],
            'Therapeutic': [
                'physical_therapy', 'occupational_therapy', 'rehabilitation'
            ]
        }
    
    def normalize_specialty_term(self, term: str) -> str:
        """Normalize a specialty term for comparison"""
        if not term:
            return ""
        
        # Convert to lowercase and strip whitespace
        normalized = term.lower().strip()
        
        # Remove common prefixes/suffixes
        normalized = re.sub(r'^(dr\.?|prof\.?|doctor)\s+', '', normalized)
        normalized = re.sub(r'\s+(md|phd|do|dds|dvm)$', '', normalized)
        
        # Replace common separators with spaces
        normalized = re.sub(r'[_\-/&+]', ' ', normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Handle common variations
        specialty_normalizations = {
            'gyno': 'gynecology',
            'cardio': 'cardiology',
            'derm': 'dermatology', 
            'neuro': 'neurology',
            'ortho': 'orthopedics',
            'peds': 'pediatrics',
            'psych': 'psychiatry',
            'ent': 'otolaryngology',
            'gp': 'general_practitioner',
            'obgyn': 'gynecology',
            'ob gyn': 'gynecology',
            'eye doctor': 'ophthalmology',
            'heart doctor': 'cardiology',
            'skin doctor': 'dermatology',
            'bone doctor': 'orthopedics',
            'brain doctor': 'neurology',
            'kidney doctor': 'nephrology',
            'lung doctor': 'pulmonology'
        }
        
        return specialty_normalizations.get(normalized, normalized)
    
    def is_valid_medical_specialty(self, term: str) -> bool:
        """Check if a term is a valid medical specialty"""
        if not term or len(term.strip()) < 2:
            return False
        
        normalized = self.normalize_specialty_term(term)
        
        # Check if it's in garbage terms
        if normalized in self.garbage_terms:
            return False
        
        # Check if it's a valid medical specialty
        if normalized in self.valid_medical_specialties:
            return True
        
        # Check for partial matches in valid specialties
        for valid_specialty in self.valid_medical_specialties:
            if normalized in valid_specialty or valid_specialty in normalized:
                # Make sure it's not too generic
                if len(normalized) >= 4:
                    return True
        
        return False
    
    def extract_specialties_from_text(self, text: str) -> List[str]:
        """Extract valid medical specialties from any text"""
        if not text:
            return []
        
        specialties = set()
        
        # Split text into potential terms
        # Handle various separators
        terms = re.split(r'[,;|\n\r\t]+', text.lower())
        
        for term in terms:
            # Clean up the term
            cleaned = re.sub(r'[^\w\s]', ' ', term)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            
            if self.is_valid_medical_specialty(cleaned):
                normalized = self.normalize_specialty_term(cleaned)
                specialties.add(normalized)
            
            # Also check individual words in multi-word terms
            words = cleaned.split()
            for word in words:
                if len(word) > 3 and self.is_valid_medical_specialty(word):
                    normalized = self.normalize_specialty_term(word)
                    specialties.add(normalized)
        
        return list(specialties)
    
    def extract_specialties_from_google_types(self, types: List[str]) -> List[str]:
        """Extract specialties from Google Places types"""
        if not types:
            return []
        
        # Google Places API type mapping
        google_type_mapping = {
            'dentist': 'dentistry',
            'doctor': 'general_practitioner', 
            'hospital': 'general_medicine',
            'pharmacy': 'pharmacy',
            'physiotherapist': 'physical_therapy',
            'veterinary_care': 'veterinary_medicine'
        }
        
        specialties = []
        for place_type in types:
            if place_type in google_type_mapping:
                specialties.append(google_type_mapping[place_type])
            elif self.is_valid_medical_specialty(place_type):
                specialties.append(self.normalize_specialty_term(place_type))
        
        return specialties
    
    def extract_specialties_from_provider_name(self, name: str) -> List[str]:
        """Extract specialties from provider name using medical keywords"""
        if not name:
            return []
        
        specialties = set()
        name_lower = name.lower()
        
        # Look for medical specialty keywords in the name
        medical_keywords = {
            'dental': 'dentistry',
            'tooth': 'dentistry', 
            'orthodont': 'orthodontics',
            'oral': 'oral_surgery',
            'eye': 'ophthalmology',
            'vision': 'ophthalmology',
            'heart': 'cardiology',
            'cardiac': 'cardiology',
            'skin': 'dermatology',
            'beauty': 'cosmetic_surgery',
            'cosmetic': 'cosmetic_surgery',
            'plastic': 'plastic_surgery',
            'bone': 'orthopedics',
            'joint': 'orthopedics',
            'women': 'gynecology',
            'ladies': 'gynecology',
            'pregnancy': 'obstetrics',
            'maternity': 'obstetrics',
            'child': 'pediatrics',
            'kids': 'pediatrics',
            'mental': 'psychiatry',
            'cancer': 'oncology',
            'tumor': 'oncology',
            'kidney': 'nephrology',
            'lung': 'pulmonology',
            'respiratory': 'pulmonology',
            'digestive': 'gastroenterology',
            'stomach': 'gastroenterology',
            'brain': 'neurology',
            'nerve': 'neurology',
            'emergency': 'emergency_medicine',
            'urgent': 'emergency_medicine'
        }
        
        for keyword, specialty in medical_keywords.items():
            if keyword in name_lower:
                specialties.add(specialty)
        
        return list(specialties)
    
    def get_comprehensive_specialties(self, provider_data: Dict) -> List[str]:
        """Get comprehensive specialty list from all available data sources"""
        all_specialties = set()
        
        # Extract from existing specialties field
        existing_specialties = provider_data.get('specialties', [])
        if isinstance(existing_specialties, list):
            for specialty in existing_specialties:
                if self.is_valid_medical_specialty(specialty):
                    all_specialties.add(self.normalize_specialty_term(specialty))
        
        # Extract from Google Places types
        google_types = provider_data.get('types', [])
        if google_types:
            google_specialties = self.extract_specialties_from_google_types(google_types)
            all_specialties.update(google_specialties)
        
        # Extract from provider name
        provider_name = provider_data.get('provider_name', '')
        name_specialties = self.extract_specialties_from_provider_name(provider_name)
        all_specialties.update(name_specialties)
        
        # Extract from any description or review content
        description = provider_data.get('ai_description', '')
        if description:
            desc_specialties = self.extract_specialties_from_text(description)
            all_specialties.update(desc_specialties)
        
        # Default to general practitioner if no specialties found
        if not all_specialties:
            all_specialties.add('general_practitioner')
        
        return sorted(list(all_specialties))
    
    def clean_specialties_file(self, input_file: str, output_file: str) -> Dict:
        """Clean existing specialties file and generate statistics"""
        try:
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            original_specialties = data.get('specialties', [])
            valid_specialties = []
            invalid_specialties = []
            
            for specialty in original_specialties:
                if self.is_valid_medical_specialty(specialty):
                    normalized = self.normalize_specialty_term(specialty)
                    if normalized not in valid_specialties:
                        valid_specialties.append(normalized)
                else:
                    invalid_specialties.append(specialty)
            
            # Add commonly needed specialties that might be missing
            essential_specialties = [
                'general_practitioner', 'family_medicine', 'internal_medicine',
                'pediatrics', 'gynecology', 'obstetrics', 'dermatology',
                'cardiology', 'neurology', 'orthopedics', 'ophthalmology',
                'dentistry', 'psychiatry', 'oncology', 'emergency_medicine',
                'physical_therapy', 'radiology', 'surgery'
            ]
            
            for essential in essential_specialties:
                if essential not in valid_specialties:
                    valid_specialties.append(essential)
            
            cleaned_data = {
                'specialties': sorted(valid_specialties)
            }
            
            with open(output_file, 'w') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            
            return {
                'original_count': len(original_specialties),
                'valid_count': len(valid_specialties),
                'invalid_count': len(invalid_specialties),
                'invalid_terms': invalid_specialties,
                'valid_specialties': valid_specialties
            }
            
        except Exception as e:
            print(f"Error cleaning specialties file: {str(e)}")
            return {}

def test_specialty_filter():
    """Test the medical specialty filter"""
    filter_system = MedicalSpecialtyFilter()
    
    test_cases = [
        # Valid medical specialties
        'cardiology', 'dermatology', 'pediatrics', 'dentistry',
        'general_practitioner', 'emergency_medicine', 'oncology',
        
        # Invalid garbage terms
        'Point_of_interest', 'Establishment', 'Yokohama', 'Luna',
        'Ladies', '|', '-', 'Beauty_salon', 'Hair_care',
        
        # Provider names to test extraction
        'Tokyo Heart Clinic', 'Yokohama Dental Center', 'Kids Pediatric Hospital',
        'Ladies Gynecology Clinic', 'International Eye Center'
    ]
    
    print("🔬 Testing Medical Specialty Filter")
    print("=" * 50)
    
    for term in test_cases:
        is_valid = filter_system.is_valid_medical_specialty(term)
        normalized = filter_system.normalize_specialty_term(term)
        extracted = filter_system.extract_specialties_from_provider_name(term)
        
        print(f"Term: '{term}'")
        print(f"  Valid: {is_valid}")
        print(f"  Normalized: '{normalized}'")
        if extracted:
            print(f"  Extracted: {extracted}")
        print()

if __name__ == "__main__":
    test_specialty_filter() 