#!/usr/bin/env python3
"""Test Google Places API on server"""

import os
from dotenv import load_dotenv
load_dotenv('config/.env')

api_key = os.getenv('GOOGLE_PLACES_API_KEY')
print(f'API Key present: {bool(api_key)}')
print(f'API Key length: {len(api_key) if api_key else 0}')

# Test a simple API call
import requests
place_id = 'ChIJBzOd3uiLGGAR7m6txyAFCYw'
url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=photos&key={api_key}'
response = requests.get(url)
print(f'API Response status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    if 'result' in data and 'photos' in data['result']:
        photos = data['result']['photos']
        print(f'Got {len(photos)} photos')
        if photos:
            ref = photos[0].get('photo_reference')
            print(f'First reference length: {len(ref) if ref else 0}')
            print(f'Full reference: {ref}')
            
            # Test if this reference works
            photo_url = f'https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={ref}&key={api_key}'
            photo_response = requests.get(photo_url)
            print(f'Photo fetch status: {photo_response.status_code}')
    else:
        print('No photos in response')
        print(f'Response data: {data}')
else:
    print(f'Error: {response.text[:200]}')