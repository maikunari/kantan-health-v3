#!/bin/bash

# Script to update the main taxonomy generator with our refined prompt

cat > update_taxonomy_prompt.py << 'EOF'
#!/usr/bin/env python3
"""
Update the main taxonomy content generator with refined prompt
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Read the current file
with open('scripts/generate_taxonomy_content.py', 'r') as f:
    content = f.read()

# Find and replace the content generation prompt
old_prompt_start = '''def generate_content_batch(self, combinations: List[Dict]) -> List[Dict]:
        """Generate content for multiple combinations in a single API call"""
        
        # Build the batch prompt
        batch_prompt = """You are creating SEO-optimized content for healthcare directory taxonomy pages.
Generate content for the following location-specialty combinations.

For each combination, create:
1. A brief introduction (2-3 sentences, 50-75 words)
2. A full description (3-4 paragraphs, 200-300 words)'''

new_prompt_start = '''def generate_content_batch(self, combinations: List[Dict]) -> List[Dict]:
        """Generate content for multiple combinations in a single API call"""
        
        # Build the batch prompt
        batch_prompt = """You are creating content for healthcare directory taxonomy pages.
Generate content for the following location-specialty combinations.

For each combination, create:
1. A brief introduction (2-3 sentences, simple and direct)
2. A full description with HTML formatting (200-300 words)'''

# Replace the prompt section
if old_prompt_start in content:
    content = content.replace(old_prompt_start, new_prompt_start)
    print("✓ Updated batch prompt introduction")

# Find and replace the individual item prompt
old_item_prompt = '''The content should:
- Be unique and specific to each location-specialty combination
- Include information about English-speaking healthcare services
- Mention international patient support
- Be SEO-friendly and natural-sounding
- Use "Multiple verified providers" or "Several English-speaking specialists" instead of exact numbers'''

new_item_prompt = '''The content should:
- Start brief intro with "Find trusted English-speaking [specialty] in [location]..."
- Mention that all listed providers have verified English language support
- Be natural and informative, avoiding sales language
- Include these H2 sections in full description:
  * Finding English-Speaking [Specialty] in [Location]
  * What to Expect at [Specialty] Clinics in Japan
  * Location and Accessibility (with actual train lines/stations)
  * Insurance and Payment (specific payment methods accepted)
- Use "multiple" or "several" instead of exact numbers
- NO call-to-action at the end (no "browse providers below")
- Focus on practical information residents actually need'''

if old_item_prompt in content:
    content = content.replace(old_item_prompt, new_item_prompt)
    print("✓ Updated content guidelines")

# Write the updated file
with open('scripts/generate_taxonomy_content.py', 'w') as f:
    f.write(content)

print("✅ Successfully updated generate_taxonomy_content.py with refined prompt")
EOF

python3 update_taxonomy_prompt.py

# Also update the test generation prompt for single items
echo "
Updating single item generation method..."

python3 -c "
import re

with open('scripts/generate_taxonomy_content.py', 'r') as f:
    content = f.read()

# Update the test mode prompt as well
content = re.sub(
    r'brief_intro.*?Emphasize.*?providers\.\"',
    'brief_intro: Start with \"Find trusted English-speaking...\" and mention verified English support. Keep it factual.',
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'full_description.*?the area\.\"',
    'full_description: Include H2 sections for Finding providers, What to Expect, Location/Accessibility, and Insurance/Payment. Focus on practical details.',
    content,
    flags=re.DOTALL
)

with open('scripts/generate_taxonomy_content.py', 'w') as f:
    f.write(content)

print('✅ Updated test mode generation')
"

echo "
✅ Script created! Now run:
1. ./update_taxonomy_generator.sh (locally)
2. Copy to server: scp scripts/generate_taxonomy_content.py deploy@206.189.156.138:/opt/healthcare-directory/scripts/
3. Test on server: python3 scripts/generate_taxonomy_content.py --mode test --dry-run
"