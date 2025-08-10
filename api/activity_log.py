"""
Activity Log API Blueprint
Provides endpoints for retrieving system activity logs
"""

from flask import Blueprint, request, jsonify
import logging
import os
import sys

# Add src to path for new modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

# Import from new unified modules
from src.utils.activity_logger import ActivityLogger

# Create activity logger instance
activity_logger = ActivityLogger()

logger = logging.getLogger(__name__)

activity_log_bp = Blueprint('activity_log', __name__)

@activity_log_bp.route('/activities', methods=['GET'])
def get_activities():
    """Get recent activities with optional filtering"""
    try:
        category = request.args.get('category')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        activities = activity_logger.get_recent_activities(
            category=category,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            'activities': activities,
            'count': len(activities),
            'limit': limit,
            'offset': offset,
            'category': category
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching activities: {str(e)}")
        return jsonify({'error': str(e)}), 500

@activity_log_bp.route('/activities/summary', methods=['GET'])
def get_activity_summary():
    """Get activity summary for the past N days"""
    try:
        days = int(request.args.get('days', 7))
        summary = activity_logger.get_activity_summary(days=days)
        
        return jsonify({
            'summary': summary,
            'days': days
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching activity summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@activity_log_bp.route('/activities/categories', methods=['GET'])
def get_activity_categories():
    """Get list of activity categories with descriptions"""
    categories = {
        'provider_creation': {
            'name': 'Provider Creation',
            'description': 'New healthcare providers added to the system',
            'icon': 'plus-circle'
        },
        'content_generation': {
            'name': 'Content Generation',
            'description': 'AI-generated content for providers',
            'icon': 'file-text'
        },
        'data_quality': {
            'name': 'Data Quality Updates',
            'description': 'Geocoding, Google Places data, and other quality improvements',
            'icon': 'database'
        },
        'wordpress_sync': {
            'name': 'WordPress Sync',
            'description': 'Provider data synchronized to WordPress',
            'icon': 'sync'
        },
        'duplicate_cleanup': {
            'name': 'Duplicate Cleanup',
            'description': 'WordPress duplicate post management',
            'icon': 'delete'
        },
        'settings_update': {
            'name': 'Settings Update',
            'description': 'Configuration and settings changes',
            'icon': 'setting'
        },
        'authentication': {
            'name': 'Authentication',
            'description': 'User login and logout events',
            'icon': 'user'
        }
    }
    
    return jsonify({'categories': categories}), 200