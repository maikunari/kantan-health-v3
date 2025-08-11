#!/usr/bin/env python3
"""
Photo Proxy API Endpoint
Handles on-demand photo fetching with 30-day cache for performance
Compliant with Google Places API Terms of Service
"""

import os
import sys
import hashlib
import requests
import logging
from datetime import datetime, timedelta
from flask import Blueprint, redirect, make_response, jsonify, send_file
from io import BytesIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.cache import PersistentCache
from src.core.cost_tracker import CostTracker
# from src.utils.activity_logger import log_activity
# Temporary: Define no-op log_activity to avoid crashes
def log_activity(*args, **kwargs):
    pass

# Create blueprint
photo_proxy_bp = Blueprint('photo_proxy', __name__)

# Configure logger
logger = logging.getLogger(__name__)

# Initialize services
cache = PersistentCache()
cost_tracker = CostTracker()

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
PHOTO_BASE_URL = "https://maps.googleapis.com/maps/api/place/photo"
CACHE_DAYS = 30  # Google TOS allows 30 days for performance caching
MAX_WIDTH = 800


@photo_proxy_bp.route('/api/photo/<reference>')
def get_photo(reference):
    """
    Proxy endpoint for Google Places photos with 30-day cache
    
    Args:
        reference: Google photo reference
        provider_id (query param): Optional provider ID to help with refresh
        
    Returns:
        Redirects to photo URL or serves cached image
    """
    from flask import request
    provider_id = request.args.get('provider_id', type=int)
    try:
        # Validate reference
        if not reference or len(reference) < 10:
            return jsonify({'error': 'Invalid photo reference'}), 400
        
        # Check cache (30-day TTL for performance)
        cache_key = f"photo_data_{reference[:32]}"  # Use first 32 chars for key
        cached_data = cache.get(cache_key, 'photo_cache')
        
        if cached_data:
            # Serve cached image
            log_activity(
                'photo_proxy',
                'cache_hit',
                {'reference': reference[:16] + '...'},
                'success'
            )
            
            # Create response with cached image data
            response = make_response(cached_data['image_data'])
            response.headers['Content-Type'] = cached_data.get('content_type', 'image/jpeg')
            response.headers['Cache-Control'] = 'public, max-age=86400'  # 1 day browser cache
            
            # Add attribution if required
            if cached_data.get('attribution'):
                response.headers['X-Attribution'] = cached_data['attribution']
            
            return response
        
        # Cache miss - check budget before making API call
        can_proceed, reason = cost_tracker.can_make_request('photos')
        if not can_proceed:
            log_activity(
                'photo_proxy',
                'budget_exceeded',
                {'reference': reference[:16] + '...', 'reason': reason},
                'error'
            )
            return jsonify({'error': 'Photo budget exceeded', 'reason': reason}), 503
        
        # Generate photo URL
        photo_url = f"{PHOTO_BASE_URL}?maxwidth={MAX_WIDTH}&photoreference={reference}&key={GOOGLE_API_KEY}"
        
        # Fetch the image
        response = requests.get(photo_url, timeout=10)
        
        if response.status_code == 200:
            # Cache the image data for 30 days
            cache_data = {
                'image_data': response.content,
                'content_type': response.headers.get('Content-Type', 'image/jpeg'),
                'cached_at': datetime.now().isoformat(),
                'attribution': response.headers.get('X-Attribution', '')
            }
            
            # Store in cache with 30-day TTL
            cache.set(cache_key, cache_data, 'photo_cache', ttl_days=CACHE_DAYS)
            
            # Log the API call
            cost_tracker.log_request('photos', metadata={'reference': reference[:16] + '...'})
            
            log_activity(
                'photo_proxy',
                'photo_fetched',
                {'reference': reference[:16] + '...'},
                'success'
            )
            
            # Return the image
            img_response = make_response(response.content)
            img_response.headers['Content-Type'] = response.headers.get('Content-Type', 'image/jpeg')
            img_response.headers['Cache-Control'] = 'public, max-age=86400'  # 1 day browser cache
            
            if cache_data['attribution']:
                img_response.headers['X-Attribution'] = cache_data['attribution']
            
            return img_response
        
        elif response.status_code == 403:
            # API key issue or quota exceeded
            log_activity(
                'photo_proxy',
                'api_error',
                {'reference': reference[:16] + '...', 'status': 403},
                'error'
            )
            return jsonify({'error': 'API authentication failed'}), 403
        
        elif response.status_code == 400:
            # Photo reference expired - refresh from Google Places
            logger.info(f"Photo reference expired, refreshing from Google Places...")
            
            # Find which provider owns this reference
            from src.core.database import DatabaseManager
            from src.collectors.google_places import GooglePlacesCollector
            from sqlalchemy import text
            import json
            
            db = DatabaseManager()
            session = db.get_session()
            
            try:
                # First try to find by the reference itself
                provider = session.execute(text("""
                    SELECT id, provider_name, google_place_id, photo_references
                    FROM providers
                    WHERE photo_references::text LIKE :ref_pattern
                    LIMIT 1
                """), {'ref_pattern': f'%{reference[:50]}%'}).fetchone()
                
                # If not found, this might be an old reference from WordPress
                # Try using provider_id if provided
                if not provider and provider_id:
                    logger.info(f"Reference not found, trying provider_id {provider_id}")
                    provider = session.execute(text("""
                        SELECT id, provider_name, google_place_id, photo_references
                        FROM providers
                        WHERE id = :provider_id
                        LIMIT 1
                    """), {'provider_id': provider_id}).fetchone()
                
                if not provider:
                    logger.info("Reference not found in database, might be outdated from WordPress")
                    logger.error("Cannot determine provider for expired reference")
                    return jsonify({'error': 'Photo reference expired and provider cannot be determined'}), 404
                
                if provider and provider.google_place_id:
                    logger.info(f"Found provider: {provider.provider_name}, refreshing photos...")
                    
                    # Fetch fresh photo references (force refresh to bypass cache)
                    collector = GooglePlacesCollector()
                    details = collector.get_place_details(provider.google_place_id, force_refresh=True)
                    
                    if not details:
                        logger.error(f"Failed to get place details for {provider.google_place_id}")
                    elif 'photos' not in details:
                        logger.error(f"No photos in place details for {provider.google_place_id}")
                    
                    if details and 'photos' in details:
                        # Extract new references
                        new_photos = details['photos']
                        new_references = [p.get('photo_reference') for p in new_photos if p.get('photo_reference')]
                        
                        if new_references:
                            # Update database with new references (as PostgreSQL text array)
                            session.execute(text("""
                                UPDATE providers 
                                SET photo_references = :references
                                WHERE id = :id
                            """), {
                                'references': new_references,  # Pass as Python list, SQLAlchemy handles conversion
                                'id': provider.id
                            })
                            session.commit()
                            
                            # Use the first new reference to serve the image
                            new_ref = new_references[0]
                            new_url = f"{PHOTO_BASE_URL}?maxwidth={MAX_WIDTH}&photoreference={new_ref}&key={GOOGLE_API_KEY}"
                            
                            # Fetch with new reference
                            new_response = requests.get(new_url, timeout=10)
                            if new_response.status_code == 200:
                                # Cache and return the new image
                                cache_data = {
                                    'image_data': new_response.content,
                                    'content_type': new_response.headers.get('Content-Type', 'image/jpeg'),
                                    'cached_at': datetime.now().isoformat(),
                                    'attribution': new_response.headers.get('X-Attribution', '')
                                }
                                cache.set(
                                    f"photo_data_{new_ref[:32]}",
                                    cache_data,
                                    'photo_cache',
                                    ttl_days=CACHE_DAYS
                                )
                                
                                # Return the image
                                img_response = make_response(new_response.content)
                                img_response.headers['Content-Type'] = new_response.headers.get('Content-Type', 'image/jpeg')
                                img_response.headers['Cache-Control'] = 'public, max-age=86400'
                                return img_response
                
                # If we couldn't refresh, return error
                logger.error(f"Could not refresh expired reference")
                return jsonify({'error': 'Photo reference expired and could not be refreshed'}), 404
                
            except Exception as e:
                logger.error(f"Error refreshing photo reference: {str(e)}")
                return jsonify({'error': 'Failed to refresh photo reference'}), 500
            finally:
                session.close()
        
        else:
            # Other error
            log_activity(
                'photo_proxy',
                'fetch_error',
                {'reference': reference[:16] + '...', 'status': response.status_code},
                'error'
            )
            return jsonify({'error': f'Failed to fetch photo: {response.status_code}'}), response.status_code
            
    except requests.Timeout:
        log_activity(
            'photo_proxy',
            'timeout',
            {'reference': reference[:16] + '...'},
            'error'
        )
        return jsonify({'error': 'Request timeout'}), 504
        
    except Exception as e:
        log_activity(
            'photo_proxy',
            'exception',
            {'reference': reference[:16] + '...', 'error': str(e)},
            'error'
        )
        return jsonify({'error': 'Internal server error'}), 500


@photo_proxy_bp.route('/api/photo/stats')
def photo_stats():
    """Get photo proxy statistics"""
    try:
        # Get cache stats
        cache_stats = cache.get_cache_stats()
        photo_cache_count = cache_stats.get('by_type', {}).get('photo_cache', 0)
        
        # Get cost stats for last 7 days
        cost_stats = cost_tracker.get_usage_stats(days=7)
        
        # Extract photo-specific costs
        photo_costs = 0
        photo_requests = 0
        
        for item in cost_stats.get('by_type', []):
            if item['type'] == 'photos':
                photo_costs = item['cost']
                photo_requests = item['count']
                break
        
        return jsonify({
            'cache': {
                'cached_photos': photo_cache_count,
                'cache_ttl_days': CACHE_DAYS,
                'total_cache_size': cache_stats.get('total_size', 0)
            },
            'usage': {
                'requests_7d': photo_requests,
                'cost_7d': photo_costs,
                'cache_hit_rate': cost_stats.get('cache_rate', 0),
                'daily_limit': cost_tracker.daily_limits.get('photos', 0),
                'monthly_limit': cost_tracker.monthly_limits.get('photos', 0)
            },
            'config': {
                'max_width': MAX_WIDTH,
                'cache_days': CACHE_DAYS
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@photo_proxy_bp.route('/api/photo/clear-cache', methods=['POST'])
def clear_photo_cache():
    """Clear expired photo cache entries (admin endpoint)"""
    try:
        # Clean up expired entries
        expired_count = cache.cleanup_expired()
        
        log_activity(
            'photo_proxy',
            'cache_cleared',
            {'expired_count': expired_count},
            'success'
        )
        
        return jsonify({
            'success': True,
            'expired_removed': expired_count,
            'message': f'Removed {expired_count} expired photo cache entries'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500