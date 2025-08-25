"""
Enhanced specialty detection using multiple data sources including reviews
Improves accuracy of provider classification and reduces "General Medicine" misclassification
"""

import re
import logging
from typing import List, Dict, Optional, Any
from collections import Counter

logger = logging.getLogger(__name__)


class SpecialtyDetector:
    """Multi-source specialty detection for healthcare providers"""
    
    # Review keywords that indicate specific specialties
    REVIEW_SPECIALTY_PATTERNS = {
        'Dentistry': [
            'dentist', 'teeth', 'dental', 'cavity', 'root canal', 
            'filling', 'crown', 'orthodont', 'tooth', 'gum', 'oral',
            '歯科', '歯医者', '虫歯', '歯周病'
        ],
        'Women\'s Health': [
            'gynecologist', 'obgyn', 'ob-gyn', 'pregnancy', 'birth control', 
            'prenatal', 'afterpill', 'after-pill', 'women\'s clinic', 'maternity',
            'obstetrics', 'gynecology', 'midwife', 'abortion', 'pill',
            '産婦人科', '婦人科', '妊娠', 'レディース', 'ウィメンズ'
        ],
        'Pediatrics': [
            'pediatrician', 'child', 'kids', 'baby', 'vaccination', 
            'infant', 'pediatric', 'children', 'newborn', 'toddler',
            '小児科', 'こども', '子供', '赤ちゃん'
        ],
        'Dermatology': [
            'dermatologist', 'skin', 'acne', 'rash', 'eczema', 
            'psoriasis', 'mole', 'dermatology', 'cosmetic', 'laser',
            '皮膚科', 'ニキビ', 'アトピー', '美容皮膚科'
        ],
        'Orthopedics': [
            'orthopedic', 'bone', 'fracture', 'joint', 'knee', 
            'shoulder', 'sports injury', 'spine', 'back pain', 'arthritis',
            '整形外科', '骨折', '関節', 'リハビリ'
        ],
        'Mental Health': [
            'psychiatrist', 'therapy', 'counseling', 'depression', 
            'anxiety', 'mental health', 'psychologist', 'psychiatric',
            '精神科', '心療内科', 'メンタル', 'カウンセリング'
        ],
        'Cardiology': [
            'cardiologist', 'heart', 'blood pressure', 'cholesterol', 
            'cardiac', 'cardiovascular', 'ecg', 'ekg', 'hypertension',
            '循環器', '心臓', '血圧', '不整脈'
        ],
        'ENT': [
            'ent specialist', 'ear', 'hearing', 'throat', 'sinus', 
            'tonsils', 'otolaryngology', 'nose', 'allergy', 'hearing loss',
            '耳鼻咽喉科', '耳鼻科', '花粉症', 'アレルギー'
        ],
        'Emergency': [
            'emergency', 'urgent care', 'er', 'accident', 'trauma',
            'emergency room', '24 hour', '24/7', 'walk-in',
            '救急', '急患', '夜間診療', '休日診療'
        ],
        'Ophthalmology': [
            'eye doctor', 'optometrist', 'vision', 'glasses', 'cataract',
            'ophthalmologist', 'contact lens', 'glaucoma', 'lasik', 'retina',
            '眼科', '視力', 'コンタクト', '白内障'
        ],
        'Internal Medicine': [
            'internal medicine', 'internist', 'general checkup', 
            'health screening', 'physical exam', 'diabetes', 'hypertension',
            '内科', '総合診療', '健康診断', '生活習慣病'
        ],
        'Gastroenterology': [
            'gastro', 'stomach', 'digestive', 'colonoscopy', 'endoscopy',
            'gastroenterologist', 'ibs', 'gerd', 'liver', 'intestine',
            '消化器', '胃腸科', '内視鏡', '胃カメラ'
        ],
        'Urology': [
            'urologist', 'urology', 'prostate', 'kidney', 'bladder',
            'urinary', 'kidney stone', 'uti', 'incontinence',
            '泌尿器科', '前立腺', '腎臓', '膀胱'
        ],
        'Plastic Surgery': [
            'plastic surgery', 'cosmetic', 'aesthetic', 'botox', 'filler',
            'reconstruction', 'breast augmentation', 'liposuction',
            '形成外科', '美容外科', '美容整形'
        ],
        'Neurology': [
            'neurologist', 'neurology', 'headache', 'migraine', 'epilepsy',
            'stroke', 'parkinson', 'alzheimer', 'brain', 'nerve',
            '神経内科', '脳神経', '頭痛', 'てんかん'
        ]
    }
    
    # Provider name keywords that strongly indicate specialty
    NAME_SPECIALTY_PATTERNS = {
        'Dentistry': [
            'dental', 'dentist', 'teeth', 'oral', '歯科', 'デンタル'
        ],
        'Women\'s Health': [
            'women', 'womens', 'woman', 'ladies', 'maternity', 'obstetrics',
            'gynecology', 'obgyn', 'afterpill', 'レディース', 'ウィメンズ',
            '産婦人科', '婦人科'
        ],
        'Pediatrics': [
            'pediatric', 'children', 'kids', 'child', 'baby',
            '小児科', 'こども', 'キッズ'
        ],
        'Dermatology': [
            'dermatology', 'skin', 'cosmetic', 'aesthetic',
            '皮膚科', 'スキン', '美容'
        ],
        'Mental Health': [
            'mental', 'psychiatric', 'psychology', 'counseling',
            '精神科', '心療内科', 'メンタル'
        ],
        'ENT': [
            'ent', 'ear nose throat', 'otolaryngology',
            '耳鼻咽喉科', '耳鼻科'
        ],
        'Ophthalmology': [
            'eye', 'vision', 'optical', 'ophthalmology',
            '眼科', 'アイクリニック'
        ],
        'Cardiology': [
            'heart', 'cardiac', 'cardiovascular',
            '循環器', '心臓'
        ],
        'Orthopedics': [
            'orthopedic', 'sports medicine', 'spine',
            '整形外科', 'スポーツ'
        ],
        'Pharmacy': [
            'pharmacy', 'drug', 'chemist', 'prescription',
            '薬局', 'ファーマシー', 'ドラッグ'
        ]
    }
    
    # Google Places types to specialty mapping
    GOOGLE_TYPE_MAPPING = {
        'dentist': 'Dentistry',
        'pharmacy': 'Pharmacy',
        'hospital': 'Hospital',
        'doctor': 'General Medicine',
        'health': 'Healthcare',
        'physiotherapist': 'Physical Therapy'
    }
    
    def __init__(self):
        """Initialize the specialty detector"""
        self.logger = logging.getLogger(__name__)
    
    def extract_from_reviews(self, reviews: List[Dict[str, Any]]) -> List[str]:
        """Extract specialty hints from patient reviews
        
        Args:
            reviews: List of review dictionaries
            
        Returns:
            List of detected specialties
        """
        if not reviews:
            return []
        
        # Combine all review text
        review_text = ''
        for review in reviews:
            if isinstance(review, dict):
                review_text += ' ' + review.get('text', '').lower()
            elif isinstance(review, str):
                review_text += ' ' + review.lower()
        
        detected_specialties = []
        
        # Check each specialty pattern
        for specialty, keywords in self.REVIEW_SPECIALTY_PATTERNS.items():
            keyword_count = sum(1 for keyword in keywords if keyword.lower() in review_text)
            if keyword_count >= 2:  # Require at least 2 keyword matches for confidence
                detected_specialties.append(specialty)
                self.logger.debug(f"Detected {specialty} from reviews (matched {keyword_count} keywords)")
        
        return detected_specialties
    
    def extract_from_name(self, provider_name: str) -> List[str]:
        """Extract specialty from provider name
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            List of detected specialties
        """
        if not provider_name:
            return []
        
        name_lower = provider_name.lower()
        detected_specialties = []
        
        # Check name patterns
        for specialty, keywords in self.NAME_SPECIALTY_PATTERNS.items():
            if any(keyword.lower() in name_lower for keyword in keywords):
                detected_specialties.append(specialty)
                self.logger.debug(f"Detected {specialty} from name: {provider_name}")
        
        return detected_specialties
    
    def extract_from_google_types(self, google_types: List[str]) -> List[str]:
        """Map Google Places types to specialties
        
        Args:
            google_types: List of Google Places types
            
        Returns:
            List of detected specialties
        """
        if not google_types:
            return []
        
        detected_specialties = []
        
        for gtype in google_types:
            if gtype in self.GOOGLE_TYPE_MAPPING:
                specialty = self.GOOGLE_TYPE_MAPPING[gtype]
                detected_specialties.append(specialty)
                self.logger.debug(f"Mapped Google type {gtype} to {specialty}")
        
        return detected_specialties
    
    def extract_from_description(self, description: str) -> List[str]:
        """Extract specialty from provider description
        
        Args:
            description: Provider description text
            
        Returns:
            List of detected specialties
        """
        if not description:
            return []
        
        description_lower = description.lower()
        detected_specialties = []
        
        # Check review patterns in description too
        for specialty, keywords in self.REVIEW_SPECIALTY_PATTERNS.items():
            keyword_count = sum(1 for keyword in keywords if keyword.lower() in description_lower)
            if keyword_count >= 3:  # Require more matches in description
                detected_specialties.append(specialty)
                self.logger.debug(f"Detected {specialty} from description (matched {keyword_count} keywords)")
        
        return detected_specialties
    
    def determine_specialty(self, 
                          provider_name: str = None,
                          reviews: List[Dict] = None,
                          google_types: List[str] = None,
                          description: str = None,
                          existing_specialties: List[str] = None) -> str:
        """Determine the best specialty from all available sources
        
        Args:
            provider_name: Provider name
            reviews: List of reviews
            google_types: Google Places types
            description: Provider description
            existing_specialties: Already detected specialties
            
        Returns:
            Best specialty match or 'General Medicine' as fallback
        """
        all_specialties = []
        
        # Priority 1: Existing AI-extracted specialties
        if existing_specialties:
            # Filter out generic ones
            filtered = [s for s in existing_specialties 
                       if s not in ['General Medicine', 'Healthcare', 'general_practitioner', 'general_medicine']]
            if filtered:
                all_specialties.extend(filtered)
        
        # Priority 2: Provider name (very reliable)
        name_specialties = self.extract_from_name(provider_name)
        if name_specialties:
            all_specialties.extend(name_specialties * 2)  # Weight name matches higher
        
        # Priority 3: Reviews (patient experiences)
        review_specialties = self.extract_from_reviews(reviews)
        if review_specialties:
            all_specialties.extend(review_specialties)
        
        # Priority 4: Google types
        type_specialties = self.extract_from_google_types(google_types)
        if type_specialties:
            all_specialties.extend(type_specialties)
        
        # Priority 5: Description
        desc_specialties = self.extract_from_description(description)
        if desc_specialties:
            all_specialties.extend(desc_specialties)
        
        # Count frequencies and return most common
        if all_specialties:
            specialty_counts = Counter(all_specialties)
            best_specialty = specialty_counts.most_common(1)[0][0]
            
            self.logger.info(f"Determined specialty: {best_specialty} "
                           f"(from {len(all_specialties)} detections)")
            return best_specialty
        
        # Only use General Medicine if nothing else found
        self.logger.debug("No specific specialty detected, defaulting to General Medicine")
        return 'General Medicine'
    
    def clean_specialty_list(self, specialties: List[str]) -> List[str]:
        """Clean and deduplicate specialty list
        
        Args:
            specialties: List of specialties
            
        Returns:
            Cleaned list with specific specialties prioritized
        """
        if not specialties:
            return ['General Medicine']
        
        # Remove generic terms if we have specific ones
        generic_terms = {'General Medicine', 'Healthcare', 'Hospital', 
                        'general_practitioner', 'general_medicine'}
        
        specific = [s for s in specialties if s not in generic_terms]
        
        if specific:
            # Return specific specialties only
            return list(dict.fromkeys(specific))  # Remove duplicates while preserving order
        
        # If only generic terms, return them cleaned
        return list(dict.fromkeys(specialties))


def test_detector():
    """Test the specialty detector with sample data"""
    detector = SpecialtyDetector()
    
    # Test cases
    test_cases = [
        {
            'name': 'Afterpill Osaka Clinic',
            'reviews': [{'text': 'Great women\'s health clinic for birth control'}],
            'expected': 'Women\'s Health'
        },
        {
            'name': 'Tokyo Dental Care',
            'reviews': [{'text': 'Excellent dentist, fixed my cavity'}],
            'expected': 'Dentistry'
        },
        {
            'name': 'Shibuya Children\'s Hospital',
            'reviews': [{'text': 'Best pediatrician for my baby'}],
            'expected': 'Pediatrics'
        }
    ]
    
    for case in test_cases:
        result = detector.determine_specialty(
            provider_name=case['name'],
            reviews=case['reviews']
        )
        print(f"Test: {case['name']}")
        print(f"  Expected: {case['expected']}")
        print(f"  Got: {result}")
        print(f"  ✅ Pass" if result == case['expected'] else f"  ❌ Fail")
        print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_detector()