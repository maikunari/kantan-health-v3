#!/usr/bin/env python3
"""
Test content generation for a specialty taxonomy term
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dotenv import load_dotenv
import anthropic

load_dotenv('config/.env')

# Initialize Claude
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Test prompt for Dentist specialty
prompt = """Generate SEO content for a specialty taxonomy archive page.

Specialty: Dentist
Provider Count: 16 providers

Create content that will appear on the archive page when users browse this specialty.

GUIDELINES:
- Write in a natural, informative tone for expats in Japan
- Focus on practical information
- Don't mention specific provider counts
- No promotional language or calls-to-action
- Include information about what to expect

Create:
1. SEO TITLE: (60 chars max, format: "[Specialty] Doctors in Japan")
2. META DESCRIPTION: (155 chars max)
3. ARCHIVE INTRO: (2-3 sentences for the top of the archive page)
4. ARCHIVE DESCRIPTION: (2-3 paragraphs with practical information about this medical specialty)

Return in this format:
TITLE: [title]
META: [meta description]
INTRO: [intro text]
DESCRIPTION: [full description]"""

print("Generating sample content for Dentist specialty...\n")
print("=" * 60)

response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=2000,
    temperature=0.7,
    messages=[{"role": "user", "content": prompt}]
)

content = response.content[0].text
print(content)
print("\n" + "=" * 60)
print("\nThis content would be:")
print("1. Saved to database")
print("2. Displayed on the /specialty/dentist/ archive page")
print("3. Used for SEO meta tags on that page")