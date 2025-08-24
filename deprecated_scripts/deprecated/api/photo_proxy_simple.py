#!/usr/bin/env python3
"""
Simplified Photo Proxy API Endpoint
Handles photo fetching with basic error handling
"""

import os
import sys
import requests
import logging
from datetime import datetime
from flask import Blueprint, make_response, jsonify

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create blueprint
photo_proxy_bp = Blueprint('photo_proxy', __name__)

# Configure logger
logger = logging.getLogger(__name__)

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
PHOTO_BASE_URL = "https://maps.googleapis.com/maps/api/place/photo"
MAX_WIDTH = 800

@photo_proxy_bp.route('/api/photo/<reference>')
def get_photo(reference):
    """
    Proxy endpoint for Google Places photos
    
    Args:
        reference: Google photo reference
        
    Returns:
        Photo or error
    """
    try:
        # Validate reference
        if not reference or len(reference) < 10:
            return jsonify({'error': 'Invalid photo reference'}), 400
        
        if not GOOGLE_API_KEY:
            logger.error("Google API key not configured")
            return jsonify({'error': 'API key not configured'}), 500
        
        # Generate photo URL
        photo_url = f"{PHOTO_BASE_URL}?maxwidth={MAX_WIDTH}&photoreference={reference}&key={GOOGLE_API_KEY}"
        
        # Fetch the image
        response = requests.get(photo_url, timeout=10)
        
        if response.status_code == 200:
            # Return the image
            img_response = make_response(response.content)
            img_response.headers['Content-Type'] = response.headers.get('Content-Type', 'image/jpeg')
            img_response.headers['Cache-Control'] = 'public, max-age=86400'  # 1 day browser cache
            return img_response
        
        elif response.status_code == 400:
            # Photo reference expired
            logger.info(f"Photo reference expired (400 error)")
            
            # For now, just return an error
            # The auto-refresh logic can be added once basic functionality works
            return jsonify({'error': 'Photo reference expired - please refresh provider data'}), 404
        
        elif response.status_code == 403:
            # API key issue or quota exceeded
            logger.error(f"API authentication failed (403)")
            return jsonify({'error': 'API authentication failed'}), 403
        
        else:
            # Other error
            logger.error(f"Failed to fetch photo: {response.status_code}")
            return jsonify({'error': f'Failed to fetch photo: {response.status_code}'}), response.status_code
            
    except requests.Timeout:
        logger.error("Request timeout")
        return jsonify({'error': 'Request timeout'}), 504
        
    except Exception as e:
        logger.error(f"Exception in photo proxy: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500