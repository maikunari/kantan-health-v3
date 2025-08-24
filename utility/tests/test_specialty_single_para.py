#!/usr/bin/env python3
"""
Test content generation for specialty - SINGLE PARAGRAPH
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dotenv import load_dotenv
import anthropic
import time

load_dotenv('config/.env')

# Initialize Claude
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Single paragraph prompt for Dentist specialty
prompt = """Generate content for a specialty taxonomy archive page in WordPress.

Specialty: Dentist

Create a single paragraph description that will appear on the archive page when users browse dentist providers.

GUIDELINES:
- Write in a natural, informative tone for expats in Japan
- Keep it to ONE paragraph (60-80 words)
- Focus on practical information about this specialty in Japan
- Don't mention specific provider counts
- No promotional language or calls-to-action
- This needs to be short so the provider listings aren't pushed below the fold

Create:
1. SEO TITLE: (60 chars max, format: "[Specialty] in Japan" or similar)
2. META DESCRIPTION: (155 chars max, for search engines)
3. DESCRIPTION: (ONE paragraph, 60-80 words for the WordPress taxonomy description)

Return in this format:
TITLE: [title]
META: [meta description]
DESCRIPTION: [single paragraph]"""

print("Generating SINGLE PARAGRAPH sample for Dentist specialty...\n")
print("=" * 60)

# Wait a moment to avoid overload
time.sleep(2)

try:
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=500,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )
    
    content = response.content[0].text
    print(content)
except Exception as e:
    print(f"API Error: {e}")
    print("\nExample output would be:")
    print("""TITLE: English-Speaking Dentists in Japan

META: Find English-speaking dentists across Japan for routine cleanings, fillings, crowns, and emergency dental care. International-standard treatments with clear communication.

DESCRIPTION: Dental care in Japan maintains high technical standards, though treatment approaches may differ from Western practices. Japanese dentists often schedule multiple shorter appointments rather than completing procedures in one visit. English-speaking dentists understand international expectations and can explain treatment plans clearly, helping bridge any cultural differences in dental care philosophy. Most accept Japanese health insurance which covers basic procedures at 70%, while cosmetic treatments like whitening and certain implants require out-of-pocket payment.""")

print("\n" + "=" * 60)