#!/usr/bin/env python3
"""
Test content generation for location - SINGLE PARAGRAPH
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dotenv import load_dotenv
import anthropic

load_dotenv('config/.env')

# Initialize Claude
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Single paragraph prompt
prompt = """Generate content for a location taxonomy archive page in WordPress.

Location: Yokohama

Create a single paragraph description that will appear on the archive page when users browse healthcare providers in this location.

GUIDELINES:
- Write in a natural, informative tone for expats in Japan
- Keep it to ONE paragraph (60-80 words)
- Focus on practical information about healthcare in this location
- Don't mention specific provider counts
- No promotional language or calls-to-action
- This needs to be short so the provider listings aren't pushed below the fold

Create:
1. SEO TITLE: (60 chars max, format: "English Healthcare in [Location]")
2. META DESCRIPTION: (155 chars max, for search engines)
3. DESCRIPTION: (ONE paragraph, 60-80 words for the WordPress taxonomy description)

Return in this format:
TITLE: [title]
META: [meta description]
DESCRIPTION: [single paragraph]"""

print("Generating SINGLE PARAGRAPH sample for Yokohama...\n")
print("=" * 60)

response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=500,
    temperature=0.7,
    messages=[{"role": "user", "content": prompt}]
)

content = response.content[0].text
print(content)
print("\n" + "=" * 60)