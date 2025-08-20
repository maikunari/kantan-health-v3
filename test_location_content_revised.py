#!/usr/bin/env python3
"""
Test REVISED content generation for a location taxonomy term
Single description field only
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dotenv import load_dotenv
import anthropic

load_dotenv('config/.env')

# Initialize Claude
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Revised prompt for Yokohama location - single description only
prompt = """Generate content for a location taxonomy archive page in WordPress.

Location: Yokohama

Create a single description that will appear on the archive page when users browse healthcare providers in this location.

GUIDELINES:
- Write in a natural, informative tone for expats in Japan
- Keep it relatively short (1-2 paragraphs, around 100-150 words)
- Focus on practical information about healthcare in this location
- Don't mention specific provider counts
- No promotional language or calls-to-action
- This is for the WordPress taxonomy description field

Create:
1. SEO TITLE: (60 chars max, format: "English Healthcare in [Location]")
2. META DESCRIPTION: (155 chars max, for search engines)
3. DESCRIPTION: (1-2 paragraphs for the WordPress taxonomy description field)

Return in this format:
TITLE: [title]
META: [meta description]
DESCRIPTION: [description text]"""

print("Generating REVISED sample content for Yokohama...\n")
print("=" * 60)

response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1000,
    temperature=0.7,
    messages=[{"role": "user", "content": prompt}]
)

content = response.content[0].text
print(content)
print("\n" + "=" * 60)
print("\nThis would be saved as:")
print("1. SEO title and meta (for meta tags)")
print("2. Description (in WordPress taxonomy description field)")
print("3. No separate intro/full description needed")