#!/usr/bin/env python3
"""Test photo fetching directly"""

import os
import requests
from dotenv import load_dotenv
load_dotenv('config/.env')

api_key = os.getenv('GOOGLE_PLACES_API_KEY')

# Test reference (the new one we just got)
reference = "ATKogpfTYaYEoU1HaKVlxAzHgVsjcsn1rc2AMXlllgRctK0iGw"

# Try the exact same URL construction as photo_proxy
PHOTO_BASE_URL = "https://maps.googleapis.com/maps/api/place/photo"
MAX_WIDTH = 800

photo_url = f"{PHOTO_BASE_URL}?maxwidth={MAX_WIDTH}&photoreference={reference}&key={api_key}"

print(f"Testing URL construction...")
print(f"Reference: {reference}")
print(f"URL: {photo_url[:100]}...")

response = requests.get(photo_url, timeout=10)
print(f"Response status: {response.status_code}")
print(f"Response headers Content-Type: {response.headers.get('Content-Type', 'unknown')}")

if response.status_code == 200:
    print(f"Success! Image size: {len(response.content)} bytes")
elif response.status_code == 400:
    print("400 Error - Bad request")
    print(f"Response: {response.text[:200]}")
else:
    print(f"Other error: {response.status_code}")
    print(f"Response: {response.text[:200]}")