#!/usr/bin/env python3
"""
Test script to generate and update a specific taxonomy page
Target: https://kantanhealth.jp/english-gynecology-in-minato/ (post ID: 3833)
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
import anthropic
import traceback

# Load environment
load_dotenv('config/.env')

# Configuration
POST_ID = 3833
TAXONOMY_URL = "https://kantanhealth.jp/english-gynecology-in-minato/"
LOCATION = "Minato, Tokyo"
SPECIALTY = "Gynecology"

def generate_content():
    """Generate content using Claude API"""
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ No ANTHROPIC_API_KEY found")
        return None, None
    
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""Generate content for a healthcare directory page about {SPECIALTY} in {LOCATION}.

Write in a natural, informative tone - like a helpful guide for expats in Japan. Focus on practical information that residents actually need.

Create two sections:

1. BRIEF INTRO (2-3 sentences, simple and direct):
   - First sentence: "Find trusted English-speaking [specialty] in [location] for [type of care]"
   - Second sentence: Mention that listed clinics have verified English support and what they offer (modern equipment, international insurance, etc.)
   - Keep it factual, no marketing fluff

2. FULL DESCRIPTION (use HTML formatting):
   
   Include these elements:
   
   <h2>Finding English-Speaking {SPECIALTY} in {LOCATION}</h2>
   Brief paragraph about the availability and importance
   
   <h2>What to Expect at {SPECIALTY} Clinics in Japan</h2>
   Brief paragraph about the Japanese approach to {SPECIALTY} care and how English-speaking providers accommodate international patients
   
   <ul>
   <li>Specific practical point about {SPECIALTY} services</li>
   <li>Communication support in English</li>
   <li>Another relevant point about {SPECIALTY} care</li>
   </ul>
   
   <h2>Location and Accessibility</h2>
   Paragraph about {LOCATION}'s transportation access, major stations, and convenience for residents
   
   <h2>Insurance and Payment</h2>
   Information about Japanese National Health Insurance acceptance, international insurance, and payment methods

Important: 
- Write naturally and informatively, avoid sales language
- For the brief intro: Start with "Find trusted English-speaking..." and mention that all listed providers have verified English language support
- Focus on practical details residents need to know
- Don't use exact numbers (not "8+ doctors") - use "several" or "multiple" instead
- Avoid words like "cater to", "high-quality", "compassionate" - just state facts
- For Location section: mention actual train lines and stations in {LOCATION}
- For Insurance section: be specific about payment methods typically accepted
- The content should be 70% unique to this location/specialty combo, 30% template
- NO call-to-action at the end (no "browse providers below" etc.)

Return ONLY the content, with sections clearly marked:

BRIEF_INTRO:
[content here]

FULL_DESCRIPTION:
[content here with HTML formatting]"""

    try:
        print("🤖 Generating content with Claude...")
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse the response
        content = response.content[0].text
        
        # Extract sections using simple parsing
        brief_intro = ""
        full_description = ""
        
        if "BRIEF_INTRO:" in content:
            start = content.index("BRIEF_INTRO:") + len("BRIEF_INTRO:")
            end = content.index("FULL_DESCRIPTION:") if "FULL_DESCRIPTION:" in content else len(content)
            brief_intro = content[start:end].strip()
        
        if "FULL_DESCRIPTION:" in content:
            start = content.index("FULL_DESCRIPTION:") + len("FULL_DESCRIPTION:")
            full_description = content[start:].strip()
        
        if brief_intro and full_description:
            print("✅ Content generated successfully")
            print("\n📝 Brief Intro:")
            print(brief_intro)
            print("\n📄 Full Description (first 200 chars):")
            print(full_description[:200] + "...")
            
            return brief_intro, full_description
        else:
            print("❌ Could not parse content sections")
            print("Raw response:", content[:500])
            return None, None
            
    except Exception as e:
        print(f"❌ Error generating content: {e}")
        traceback.print_exc()
        return None, None

def update_wordpress(brief_intro, full_description):
    """Update WordPress post with ACF fields"""
    
    wp_url = os.getenv('WORDPRESS_URL')
    wp_user = os.getenv('WORDPRESS_USERNAME')
    wp_pass = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
    
    if not all([wp_url, wp_user, wp_pass]):
        print("❌ WordPress credentials not found in .env")
        return False
    
    # WordPress REST API endpoint for updating ACF fields
    # Using the correct custom post type: tc_combination
    endpoint = f"{wp_url}/wp-json/wp/v2/tc_combination/{POST_ID}"
    
    # Prepare the data
    data = {
        'acf': {
            'brief_intro': brief_intro,
            'full_description': full_description
        }
    }
    
    print(f"\n🌐 Updating WordPress post {POST_ID}...")
    print(f"   Endpoint: {endpoint}")
    
    try:
        # First, try to GET the post to verify it exists
        response = requests.get(
            endpoint,
            auth=(wp_user, wp_pass),
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Post found, updating ACF fields...")
            
            # Update the post
            response = requests.post(
                endpoint,
                auth=(wp_user, wp_pass),
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print("✅ Successfully updated WordPress post!")
                print(f"   View at: {TAXONOMY_URL}")
                return True
            else:
                print(f"❌ Failed to update: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                
                # Try alternative endpoint format
                print("\n🔄 Trying alternative endpoint...")
                alt_endpoint = f"{wp_url}/wp-json/acf/v3/tc_combination/{POST_ID}"
                
                response = requests.post(
                    alt_endpoint,
                    auth=(wp_user, wp_pass),
                    json={'fields': {
                        'brief_intro': brief_intro,
                        'full_description': full_description
                    }},
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    print("✅ Updated via ACF endpoint!")
                    return True
                else:
                    print(f"❌ Alternative also failed: {response.status_code}")
                    
        else:
            print(f"❌ Could not find post {POST_ID}")
            print(f"   Status: {response.status_code}")
            
            # Check if it's a regular post
            print("\n🔄 Checking if it's a regular post/page...")
            alt_endpoint = f"{wp_url}/wp-json/wp/v2/posts/{POST_ID}"
            response = requests.get(alt_endpoint, auth=(wp_user, wp_pass))
            
            if response.status_code == 200:
                print("✅ Found as regular post, updating...")
                response = requests.post(
                    alt_endpoint,
                    auth=(wp_user, wp_pass),
                    json=data,
                    timeout=10
                )
                if response.status_code == 200:
                    print("✅ Updated successfully!")
                    return True
            else:
                # Try pages endpoint
                print("\n🔄 Checking if it's a page...")
                page_endpoint = f"{wp_url}/wp-json/wp/v2/pages/{POST_ID}"
                response = requests.get(page_endpoint, auth=(wp_user, wp_pass))
                
                if response.status_code == 200:
                    print("✅ Found as page, updating...")
                    response = requests.post(
                        page_endpoint,
                        auth=(wp_user, wp_pass),
                        json=data,
                        timeout=10
                    )
                    if response.status_code == 200:
                        print("✅ Updated successfully!")
                        return True
                    
    except Exception as e:
        print(f"❌ Error updating WordPress: {e}")
        traceback.print_exc()
        
    return False

def main():
    """Main execution"""
    
    print("=" * 60)
    print("TAXONOMY PAGE UPDATE TEST")
    print("=" * 60)
    print(f"Target: {TAXONOMY_URL}")
    print(f"Post ID: {POST_ID}")
    print(f"Location: {LOCATION}")
    print(f"Specialty: {SPECIALTY}")
    print("=" * 60)
    
    # Generate content
    brief_intro, full_description = generate_content()
    
    if not brief_intro or not full_description:
        print("\n❌ Failed to generate content")
        return
    
    # Ask for confirmation
    print("\n" + "=" * 60)
    print("Ready to update WordPress?")
    print("This will overwrite existing content for this page.")
    response = input("Continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    # Update WordPress
    success = update_wordpress(brief_intro, full_description)
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 SUCCESS!")
        print(f"Check the page at: {TAXONOMY_URL}")
        print("If ACF fields don't show, check WordPress admin directly")
    else:
        print("\n" + "=" * 60)
        print("❌ Update failed")
        print("Troubleshooting:")
        print("1. Check if ACF REST API is enabled")
        print("2. Verify the post type name (location_specialty)")
        print("3. Check ACF field names (brief_intro, full_description)")
        print("4. Ensure REST API authentication is working")

if __name__ == "__main__":
    main()