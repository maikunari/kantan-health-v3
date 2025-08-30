#!/usr/bin/env python3
"""
Demonstration of Romaji Integration in Content Pipeline
Shows how Japanese provider names are handled throughout the system
"""

import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.romaji_converter import contains_japanese, convert_to_romaji, get_display_name
from src.processors.ai_content import AIContentProcessor
from src.core.database import Provider


def demonstrate_romaji_conversion():
    """Demonstrate romaji conversion for various provider names"""
    print("\n" + "=" * 80)
    print("ROMAJI CONVERSION DEMONSTRATION")
    print("=" * 80)
    
    # Sample provider names from real Japanese healthcare facilities
    sample_names = [
        # Pure Japanese names
        "千葉デンタルクリニック",
        "とようら小児科",
        "聖路加国際病院",
        "新宿駅前医院",
        "渋谷こどもクリニック",
        "鎌倉ハチマンデンタルクリニック",
        
        # Mixed Japanese/English
        "グローバルヘルスケアクリニック Global Healthcare",
        "アフターピル大阪クリニック Afterpill Osaka",
        
        # Already in English
        "Tokyo Medical Center",
        "International Hospital of Japan",
        "Roppongi Hills Clinic"
    ]
    
    print("\nProvider Name Conversions:")
    print("-" * 60)
    
    for name in sample_names:
        if contains_japanese(name):
            romaji = convert_to_romaji(name)
            display = get_display_name(name)
            
            print(f"\nOriginal (Japanese):")
            print(f"  {name}")
            print(f"Romaji Conversion:")
            print(f"  {romaji}")
            print(f"Display Format:")
            print(f"  {display}")
        else:
            print(f"\nOriginal (English):")
            print(f"  {name}")
            print(f"  [No conversion needed - already in English]")


def demonstrate_content_generation():
    """Demonstrate how content is generated with romaji names"""
    print("\n" + "=" * 80)
    print("CONTENT GENERATION WITH ROMAJI")
    print("=" * 80)
    
    # Create a sample provider with Japanese name
    provider = Provider()
    provider.id = 999
    provider.provider_name = "千葉デンタルクリニック"
    provider.city = "Tokyo"
    provider.district = "Shibuya"
    provider.prefecture = "Tokyo"
    provider.specialties = ["Dentistry"]
    provider.rating = 4.5
    provider.total_reviews = 120
    provider.english_proficiency = "High"
    provider.review_content = []
    
    # Initialize processor
    processor = AIContentProcessor()
    
    # Get English name
    english_name = processor._get_english_name(provider)
    
    print(f"\nProvider Details:")
    print(f"  Original Name: {provider.provider_name}")
    print(f"  English Name:  {english_name}")
    print(f"  Location:      {provider.district}, {provider.city}")
    print(f"  Specialty:     {provider.specialties[0]}")
    
    # Generate fallback content (for demonstration)
    content_list = processor._create_fallback_content([provider])
    content = content_list[0]
    
    print(f"\nGenerated Content (using English name):")
    print("-" * 60)
    
    print(f"\nSEO Title:")
    print(f"  {content.seo_title}")
    
    print(f"\nSEO Meta Description:")
    print(f"  {content.seo_meta_description}")
    
    print(f"\nDescription:")
    print(f"  {content.description}")
    
    print(f"\nExcerpt:")
    print(f"  {content.excerpt}")
    
    # Verify no Japanese characters in content
    content_fields = [
        content.description,
        content.excerpt,
        content.seo_title,
        content.seo_meta_description
    ]
    
    has_japanese = any(contains_japanese(field) for field in content_fields)
    
    print(f"\n✅ Verification:")
    print(f"  - English name used: {english_name in content.description}")
    print(f"  - No Japanese characters: {not has_japanese}")


def demonstrate_complete_workflow():
    """Demonstrate the complete workflow from Japanese to English content"""
    print("\n" + "=" * 80)
    print("COMPLETE ROMAJI WORKFLOW")
    print("=" * 80)
    
    print("\n📋 Step-by-step Process:")
    print("-" * 60)
    
    # Step 1: Provider collected from Google
    print("\n1️⃣ Provider collected from Google Places API:")
    print("   Name: 聖路加国際病院")
    print("   Location: Chuo, Tokyo")
    
    # Step 2: Romaji conversion
    original = "聖路加国際病院"
    romaji = convert_to_romaji(original)
    print(f"\n2️⃣ Romaji conversion applied:")
    print(f"   Original: {original}")
    print(f"   Romaji:   {romaji}")
    
    # Step 3: Content generation
    print(f"\n3️⃣ AI content generation uses romaji name:")
    print(f"   All content fields will use: '{romaji}'")
    print(f"   No Japanese characters in generated content")
    
    # Step 4: Database storage
    print(f"\n4️⃣ Database storage:")
    print(f"   provider_name: {original} (original)")
    print(f"   provider_name_romaji: {romaji} (for reference)")
    print(f"   All content fields: Use '{romaji}'")
    
    # Step 5: Website display
    print(f"\n5️⃣ Website display options:")
    print(f"   Option A: {romaji}")
    print(f"   Option B: {romaji} ({original})")
    print(f"   Both formats available for flexibility")


def main():
    """Run all demonstrations"""
    print("\n" + "=" * 80)
    print("🔤 ROMAJI INTEGRATION DEMONSTRATION")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Demo 1: Basic romaji conversion
    demonstrate_romaji_conversion()
    
    # Demo 2: Content generation with romaji
    demonstrate_content_generation()
    
    # Demo 3: Complete workflow
    demonstrate_complete_workflow()
    
    print("\n" + "=" * 80)
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 80)
    
    print("\n🎯 Key Benefits of Romaji Integration:")
    print("  1. Consistent English naming across all content")
    print("  2. Better SEO for English-language searches")
    print("  3. Improved readability for international users")
    print("  4. Maintains original Japanese for reference")
    print("  5. Automatic handling - no manual intervention needed")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()