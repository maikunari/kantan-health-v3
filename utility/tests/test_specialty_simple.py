#!/usr/bin/env python3
"""
Test SIMPLE/SHORT content for specialty
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

# Much simpler prompt
prompt = """Generate simple content for a specialty taxonomy archive page.

Specialty: Dentist

GUIDELINES:
- Very simple and short (40-50 words max)
- Just basic information about finding this type of doctor in Japan
- Natural, not SEO-focused
- No complex medical terms or detailed explanations

Create:
1. SEO TITLE: (Simple, like "English-Speaking Dentists in Japan")
2. META DESCRIPTION: (Simple, 100 chars max)
3. DESCRIPTION: (ONE short paragraph, 40-50 words)

Return in this format:
TITLE: [title]
META: [meta description]
DESCRIPTION: [short paragraph]"""

print("Generating SIMPLE/SHORT sample for Dentist...\n")
print("=" * 60)

# Wait to avoid overload
time.sleep(3)

try:
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=300,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )
    
    content = response.content[0].text
    print(content)
except Exception as e:
    print(f"API may be overloaded. Here's an example:")
    print("""TITLE: English-Speaking Dentists in Japan

META: Find dentists in Japan who speak English for cleanings, fillings, and dental care.

DESCRIPTION: Finding an English-speaking dentist in Japan helps ensure clear communication about your dental care. Browse our directory of dentists who can explain procedures in English and understand international dental practices. Services range from routine cleanings to specialized treatments.""")

print("\n" + "=" * 60)