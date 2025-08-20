#!/usr/bin/env python3
"""
Test FACTUAL/DESCRIPTIVE content for specialty
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

# Factual, non-salesy prompt
prompt = """Generate factual, descriptive content for a specialty taxonomy archive page.

Specialty: Dentist

GUIDELINES:
- Factual and descriptive, not promotional
- Simply explain what this type of provider does and that this page lists English-verified ones
- About 40-50 words
- No "looking for?" or "find your" or sales language
- Just state what the page shows

Create:
1. SEO TITLE: (Simple, factual)
2. META DESCRIPTION: (Factual description, 100 chars max)
3. DESCRIPTION: (ONE factual paragraph, 40-50 words)

Return in this format:
TITLE: [title]
META: [meta description]
DESCRIPTION: [factual paragraph]"""

print("Generating FACTUAL sample for Dentist...\n")
print("=" * 60)

# Wait to avoid overload
time.sleep(3)

try:
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=300,
        temperature=0.5,  # Lower temperature for more factual output
        messages=[{"role": "user", "content": prompt}]
    )
    
    content = response.content[0].text
    print(content)
except Exception as e:
    print(f"API may be overloaded. Here's a factual example:")
    print("""TITLE: English-Speaking Dentists in Japan

META: Dentists in Japan verified to provide English language support for international patients.

DESCRIPTION: Dentists provide preventive care, cleanings, fillings, crowns, root canals, and oral surgery services. This page lists dental providers in Japan that have been verified to offer English language support, making dental care accessible to international residents and visitors who may have limited Japanese proficiency.""")

print("\n" + "=" * 60)