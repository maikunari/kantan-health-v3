"""
Romaji converter for Japanese provider names
Converts Japanese text (hiragana, katakana, kanji) to readable romaji
"""

import re
import logging

logger = logging.getLogger(__name__)

# Try to import cutlet, fall back gracefully if not available
try:
    from cutlet import Cutlet
    CUTLET_AVAILABLE = True
except ImportError:
    CUTLET_AVAILABLE = False
    logger.warning("Cutlet library not available. Install with: pip install cutlet")


# Dictionary of common medical terms that should be translated, not transliterated
MEDICAL_TERM_TRANSLATIONS = {
    # Katakana medical terms
    'デンタルクリニック': 'Dental Clinic',
    'クリニック': 'Clinic',
    'ホスピタル': 'Hospital',
    'メディカル': 'Medical',
    'センター': 'Center',
    'ファーマシー': 'Pharmacy',
    'デンタル': 'Dental',
    'アイクリニック': 'Eye Clinic',
    'ペインクリニック': 'Pain Clinic',
    'レディースクリニック': 'Ladies Clinic',
    'ウィメンズクリニック': 'Women\'s Clinic',
    'こどもクリニック': 'Children\'s Clinic',
    'キッズクリニック': 'Kids Clinic',
    'デンタルオフィス': 'Dental Office',
    'メディカルセンター': 'Medical Center',
    'ヘルスケア': 'Healthcare',
    'スキンクリニック': 'Skin Clinic',
    
    # Kanji medical terms
    '歯科医院': 'Dental Clinic',
    '歯科': 'Dental',
    '医院': 'Clinic',
    '病院': 'Hospital',
    '薬局': 'Pharmacy',
    '診療所': 'Clinic',
    '整形外科': 'Orthopedic Surgery',
    '内科': 'Internal Medicine',
    '小児科': 'Pediatrics',
    '外科': 'Surgery',
    '皮膚科': 'Dermatology',
    '耳鼻咽喉科': 'ENT Clinic',
    '眼科': 'Ophthalmology',
    '産婦人科': 'Obstetrics and Gynecology',
    '精神科': 'Psychiatry',
    '歯科医': 'Dentist',
    '耳鼻科': 'ENT',
    
    # Common location terms
    '駅前': 'Station',
    '駅東口': 'Station East Exit',
    '駅西口': 'Station West Exit',
    '駅南口': 'Station South Exit',
    '駅北口': 'Station North Exit',
    '東口': 'East Exit',
    '西口': 'West Exit',
    '南口': 'South Exit',
    '北口': 'North Exit',
}


def contains_japanese(text: str) -> bool:
    """
    Check if text contains Japanese characters (hiragana, katakana, or kanji)
    
    Args:
        text: Text to check
        
    Returns:
        True if text contains Japanese characters
    """
    if not text:
        return False
    
    # Unicode ranges for Japanese characters
    # Hiragana: \u3040-\u309f
    # Katakana: \u30a0-\u30ff
    # Kanji: \u4e00-\u9faf
    # Katakana extensions: \u31f0-\u31ff
    # CJK unified ideographs: \u3400-\u4dbf
    japanese_pattern = r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf\u31f0-\u31ff\u3400-\u4dbf]'
    
    return bool(re.search(japanese_pattern, text))


def convert_to_romaji(text: str, preserve_non_japanese: bool = True) -> str:
    """
    Convert Japanese text to romaji with proper medical term translation
    
    Args:
        text: Text to convert
        preserve_non_japanese: If True, preserve non-Japanese text as-is
        
    Returns:
        Romaji version of the text with medical terms properly translated
    """
    if not text:
        return text
    
    if not CUTLET_AVAILABLE:
        logger.warning("Cannot convert to romaji - cutlet not installed")
        return text
    
    try:
        # First, replace known medical terms with English equivalents
        processed_text = text
        replacements = []
        
        # Sort terms by length (longest first) to avoid partial replacements
        sorted_terms = sorted(MEDICAL_TERM_TRANSLATIONS.items(), 
                            key=lambda x: len(x[0]), reverse=True)
        
        for japanese_term, english_term in sorted_terms:
            if japanese_term in processed_text:
                # Store the replacement for later
                placeholder = f"__TERM_{len(replacements)}__"
                processed_text = processed_text.replace(japanese_term, placeholder)
                replacements.append(english_term)
        
        # Now convert the remaining Japanese text to romaji
        if contains_japanese(processed_text):
            # Initialize Cutlet with hepburn romanization
            katsu = Cutlet()
            katsu.use_foreign_spelling = True
            
            if preserve_non_japanese and not contains_only_japanese(processed_text):
                # Mixed text - need to handle carefully
                romaji = convert_mixed_text(processed_text, katsu)
            else:
                # Pure Japanese text
                romaji = katsu.romaji(processed_text)
                romaji = title_case_romaji(romaji)
        else:
            romaji = processed_text
        
        # Replace placeholders with English terms
        for i, english_term in enumerate(replacements):
            placeholder = f"__TERM_{i}__"
            # Add space before the term if needed
            if romaji.find(placeholder) > 0 and not romaji[romaji.find(placeholder)-1].isspace():
                romaji = romaji.replace(placeholder, ' ' + english_term)
            else:
                romaji = romaji.replace(placeholder, english_term)
        
        # Clean up spacing and capitalize properly
        romaji = re.sub(r'\s+', ' ', romaji).strip()
        
        # Fix common spacing issues
        romaji = re.sub(r'([a-z])([A-Z])', r'\1 \2', romaji)  # Add space between camelCase
        
        return romaji
            
    except Exception as e:
        logger.error(f"Error converting to romaji: {e}")
        return text


def contains_only_japanese(text: str) -> bool:
    """
    Check if text contains ONLY Japanese characters (and spaces/punctuation)
    
    Args:
        text: Text to check
        
    Returns:
        True if text contains only Japanese characters
    """
    if not text:
        return False
    
    # Remove spaces and common punctuation
    cleaned = re.sub(r'[\s\-・（）()「」『』、。！？]', '', text)
    
    # Check if all remaining characters are Japanese
    japanese_pattern = r'^[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf\u31f0-\u31ff\u3400-\u4dbf]+$'
    
    return bool(re.match(japanese_pattern, cleaned))


def convert_mixed_text(text: str, katsu=None) -> str:
    """
    Convert mixed Japanese/English text, preserving English parts
    
    Args:
        text: Mixed text to convert
        katsu: Cutlet instance (created if not provided)
        
    Returns:
        Text with Japanese parts converted to romaji
    """
    if not CUTLET_AVAILABLE:
        return text
    
    if katsu is None:
        katsu = Cutlet()
        katsu.use_foreign_spelling = True
    
    # Split text into Japanese and non-Japanese segments
    japanese_pattern = r'([\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf\u31f0-\u31ff\u3400-\u4dbf]+)'
    
    segments = re.split(japanese_pattern, text)
    result = []
    
    for segment in segments:
        if not segment:
            continue
        
        if re.match(japanese_pattern, segment):
            # Japanese segment - convert to romaji
            try:
                romaji = katsu.romaji(segment)
                # Capitalize if it looks like a proper noun (at start or after space)
                if result and result[-1].endswith(' '):
                    romaji = title_case_romaji(romaji)
                result.append(romaji)
            except Exception as e:
                logger.warning(f"Failed to convert segment '{segment}': {e}")
                result.append(segment)
        else:
            # Non-Japanese segment - keep as-is
            result.append(segment)
    
    return ''.join(result)


def title_case_romaji(romaji: str) -> str:
    """
    Convert romaji to title case for proper names
    
    Args:
        romaji: Romaji text
        
    Returns:
        Title-cased romaji
    """
    # Split on spaces and capitalize first letter of each word
    words = romaji.split()
    
    # Don't capitalize particles and common words
    no_capitalize = {'no', 'to', 'wa', 'ga', 'wo', 'ni', 'de', 'he', 'kara', 'made', 'ya'}
    
    result = []
    for i, word in enumerate(words):
        # Always capitalize first word, otherwise check if it's a particle
        if i == 0 or word.lower() not in no_capitalize:
            result.append(word.capitalize())
        else:
            result.append(word.lower())
    
    return ' '.join(result)


def get_display_name(provider_name: str, provider_name_romaji: str = None) -> str:
    """
    Get display name for provider, with romaji if Japanese
    
    Args:
        provider_name: Original provider name
        provider_name_romaji: Pre-computed romaji version (optional)
        
    Returns:
        Display name with format "Romaji - Original" for Japanese names
    """
    if not provider_name:
        return ""
    
    # Check if name contains Japanese
    if contains_japanese(provider_name):
        # Use provided romaji or generate it
        if not provider_name_romaji:
            provider_name_romaji = convert_to_romaji(provider_name)
        
        # If romaji conversion succeeded and is different from original
        if provider_name_romaji and provider_name_romaji != provider_name:
            return f"{provider_name_romaji} ({provider_name})"
    
    # Return original name if no Japanese or conversion failed
    return provider_name


def generate_romaji_for_provider(provider) -> str:
    """
    Generate romaji for a provider object
    
    Args:
        provider: Provider object with provider_name attribute
        
    Returns:
        Romaji version of provider name, or None if not needed
    """
    if not hasattr(provider, 'provider_name'):
        return None
    
    if contains_japanese(provider.provider_name):
        return convert_to_romaji(provider.provider_name)
    
    return None


# Test function for development
def test_romaji_conversion():
    """Test romaji conversion with sample names"""
    test_names = [
        "千葉デンタルクリニック",
        "とようら小児科",
        "グローバルヘルスケアクリニック Global Healthcare Clinic",
        "Tokyo Medical Center",
        "聖路加国際病院",
        "アフターピル大阪クリニック Afterpill Osaka Clinic",
        "新宿駅東口医院",
        "鎌倉ハチマンデンタルクリニック",
        "日の出薬局",
        "高尾歯科医院",
        "渋谷駅前耳鼻咽喉科",
        "平和医院",
        "千賀デンタルクリニック 新宿駅東口医院"
    ]
    
    print("Testing Romaji Conversion:")
    print("-" * 60)
    
    for name in test_names:
        has_japanese = contains_japanese(name)
        romaji = convert_to_romaji(name) if has_japanese else None
        display = get_display_name(name)
        
        print(f"Original: {name}")
        print(f"  Has Japanese: {has_japanese}")
        if romaji:
            print(f"  Romaji: {romaji}")
        print(f"  Display: {display}")
        print()


if __name__ == "__main__":
    test_romaji_conversion()