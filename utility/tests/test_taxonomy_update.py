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
    
    prompt = f"""Generate SEO-optimized content for a healthcare directory taxonomy page.

Location: {LOCATION}
Specialty: {SPECIALTY}
URL: {TAXONOMY_URL}

Create two sections:

1. BRIEF INTRO (2-3 sentences, 50-75 words):
   - Welcoming, professional tone
   - Mention the specialty and location
   - Emphasize English-speaking support
   - Use "verified providers" or "multiple providers" (not exact numbers)

2. FULL DESCRIPTION (3-4 paragraphs, 200-300 words):
   - Overview of {SPECIALTY} services available in {LOCATION}
   - Importance of English-speaking healthcare for international residents
   - What patients can expect from providers in this area
   - Why {LOCATION} is a good location for medical care
   - Call-to-action to browse providers

Important: Do NOT use specific numbers like "8+ doctors". Instead use terms like:
- "Multiple verified providers"
- "Several English-speaking specialists"
- "A selection of qualified practitioners"
- "Various clinics and hospitals"

Format your response as JSON:
{{
    "brief_intro": "...",
    "full_description": "..."
}}"""

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
        
        # Try to extract JSON
        if '{' in content and '}' in content:
            start = content.index('{')
            end = content.rindex('}') + 1
            json_str = content[start:end]
            data = json.loads(json_str)
            
            print("✅ Content generated successfully")
            print("\n📝 Brief Intro:")
            print(data['brief_intro'])
            print("\n📄 Full Description (first 200 chars):")
            print(data['full_description'][:200] + "...")
            
            return data['brief_intro'], data['full_description']
        else:
            print("❌ Could not parse JSON from response")
            return None, None
            
    except Exception as e:
        print(f"❌ Error generating content: {e}")
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
    endpoint = f"{wp_url}/wp-json/wp/v2/location_specialty/{POST_ID}"
    
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
                alt_endpoint = f"{wp_url}/wp-json/acf/v3/location_specialty/{POST_ID}"
                
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
                    
    except Exception as e:
        print(f"❌ Error updating WordPress: {e}")
        
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