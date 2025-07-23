"""
Settings API Blueprint
Handles configuration management for WordPress, Google API, and Claude API
"""

from flask import Blueprint, request, jsonify
import os
import re
import logging
from dotenv import load_dotenv, set_key, unset_key
import requests
from anthropic import Anthropic

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__)

# Path to the .env file
ENV_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', '.env')

@settings_bp.route('/config', methods=['GET'])
def get_configuration():
    """Get current configuration settings (without sensitive data)"""
    try:
        # Load current environment
        load_dotenv(ENV_FILE_PATH)
        
        # Mask sensitive information
        def mask_key(key):
            if not key:
                return ""
            if len(key) <= 8:
                return key[:2] + "*" * (len(key) - 4) + key[-2:] if len(key) > 4 else "*" * len(key)
            return key[:4] + "*" * (len(key) - 8) + key[-4:]
        
        config = {
            'wordpress': {
                'url': os.getenv('WORDPRESS_URL', ''),
                'username': os.getenv('WORDPRESS_USERNAME', ''),
                'password_masked': mask_key(os.getenv('WORDPRESS_APPLICATION_PASSWORD', '')),
                'password_set': bool(os.getenv('WORDPRESS_APPLICATION_PASSWORD'))
            },
            'google_api': {
                'places_api_key_masked': mask_key(os.getenv('GOOGLE_PLACES_API_KEY', '')),
                'places_api_key_set': bool(os.getenv('GOOGLE_PLACES_API_KEY'))
            },
            'claude_api': {
                'api_key_masked': mask_key(os.getenv('ANTHROPIC_API_KEY', '')),
                'api_key_set': bool(os.getenv('ANTHROPIC_API_KEY'))
            },
            'admin': {
                'password_set': bool(os.getenv('ADMIN_PASSWORD')),
                'secret_key_set': bool(os.getenv('SECRET_KEY'))
            }
        }
        
        return jsonify(config), 200
    except Exception as e:
        logger.error(f"Error getting configuration: {str(e)}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/config/wordpress', methods=['PUT'])
def update_wordpress_config():
    """Update WordPress configuration"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('url') or not data.get('username'):
            return jsonify({'error': 'URL and username are required'}), 400
        
        # Validate URL format
        url = data['url'].strip()
        if not url.startswith(('http://', 'https://')):
            return jsonify({'error': 'URL must start with http:// or https://'}), 400
        
        # Update .env file
        set_key(ENV_FILE_PATH, 'WORDPRESS_URL', url)
        set_key(ENV_FILE_PATH, 'WORDPRESS_USERNAME', data['username'].strip())
        
        # Only update password if provided
        if data.get('password') and data['password'].strip():
            set_key(ENV_FILE_PATH, 'WORDPRESS_APPLICATION_PASSWORD', data['password'].strip())
        
        return jsonify({'message': 'WordPress configuration updated successfully'}), 200
    except Exception as e:
        logger.error(f"Error updating WordPress config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/config/google', methods=['PUT'])
def update_google_config():
    """Update Google API configuration"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('places_api_key'):
            return jsonify({'error': 'Google Places API key is required'}), 400
        
        api_key = data['places_api_key'].strip()
        
        # Basic validation - Google API keys typically start with AIza
        if not api_key.startswith('AIza'):
            return jsonify({'error': 'Invalid Google API key format'}), 400
        
        # Update .env file
        set_key(ENV_FILE_PATH, 'GOOGLE_PLACES_API_KEY', api_key)
        
        return jsonify({'message': 'Google API configuration updated successfully'}), 200
    except Exception as e:
        logger.error(f"Error updating Google API config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/config/claude', methods=['PUT'])
def update_claude_config():
    """Update Claude API configuration"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('api_key'):
            return jsonify({'error': 'Claude API key is required'}), 400
        
        api_key = data['api_key'].strip()
        
        # Basic validation - Anthropic API keys start with sk-ant-
        if not api_key.startswith('sk-ant-'):
            return jsonify({'error': 'Invalid Claude API key format'}), 400
        
        # Update .env file
        set_key(ENV_FILE_PATH, 'ANTHROPIC_API_KEY', api_key)
        
        return jsonify({'message': 'Claude API configuration updated successfully'}), 200
    except Exception as e:
        logger.error(f"Error updating Claude API config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/config/admin', methods=['PUT'])
def update_admin_config():
    """Update admin configuration"""
    try:
        data = request.json
        
        # Update password if provided
        if data.get('password'):
            password = data['password'].strip()
            if len(password) < 6:
                return jsonify({'error': 'Password must be at least 6 characters'}), 400
            set_key(ENV_FILE_PATH, 'ADMIN_PASSWORD', password)
        
        # Update secret key if provided
        if data.get('secret_key'):
            secret_key = data['secret_key'].strip()
            if len(secret_key) < 16:
                return jsonify({'error': 'Secret key must be at least 16 characters'}), 400
            set_key(ENV_FILE_PATH, 'SECRET_KEY', secret_key)
        
        return jsonify({'message': 'Admin configuration updated successfully'}), 200
    except Exception as e:
        logger.error(f"Error updating admin config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/test/wordpress', methods=['POST'])
def test_wordpress_connection():
    """Test WordPress API connection"""
    try:
        load_dotenv(ENV_FILE_PATH)
        
        wp_url = os.getenv('WORDPRESS_URL')
        wp_username = os.getenv('WORDPRESS_USERNAME')
        wp_password = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        
        if not all([wp_url, wp_username, wp_password]):
            return jsonify({'error': 'WordPress configuration incomplete'}), 400
        
        # Test connection to WordPress REST API
        test_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/users/me"
        
        response = requests.get(
            test_url,
            auth=(wp_username, wp_password),
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            return jsonify({
                'success': True,
                'message': f'Successfully connected as {user_data.get("name", wp_username)}',
                'user_info': {
                    'name': user_data.get('name'),
                    'email': user_data.get('email'),
                    'roles': user_data.get('roles', [])
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'WordPress API returned {response.status_code}: {response.text[:200]}'
            }), 200
            
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Connection timeout'}), 200
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Unable to connect to WordPress site'}), 200
    except Exception as e:
        logger.error(f"Error testing WordPress connection: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 200

@settings_bp.route('/test/google', methods=['POST'])
def test_google_api():
    """Test Google Places API"""
    try:
        load_dotenv(ENV_FILE_PATH)
        
        api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        if not api_key:
            return jsonify({'error': 'Google API key not configured'}), 400
        
        # Test with a simple place search
        test_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'query': 'hospital Tokyo',
            'key': api_key,
            'type': 'hospital'
        }
        
        response = requests.get(test_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                return jsonify({
                    'success': True,
                    'message': f'API working - found {len(data.get("results", []))} results for test query',
                    'quota_info': {
                        'status': data.get('status'),
                        'results_count': len(data.get('results', []))
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': f'Google API error: {data.get("error_message", data.get("status"))}'
                }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'HTTP {response.status_code}: {response.text[:200]}'
            }), 200
            
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'API request timeout'}), 200
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Unable to connect to Google API'}), 200
    except Exception as e:
        logger.error(f"Error testing Google API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 200

@settings_bp.route('/test/claude', methods=['POST'])
def test_claude_api():
    """Test Claude API connection"""
    try:
        load_dotenv(ENV_FILE_PATH)
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return jsonify({'error': 'Claude API key not configured'}), 400
        
        # Test with a simple API call
        client = Anthropic(api_key=api_key)
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": "Respond with exactly: 'API test successful'"
            }]
        )
        
        if response.content and len(response.content) > 0:
            response_text = response.content[0].text.strip()
            return jsonify({
                'success': True,
                'message': 'Claude API connection successful',
                'test_response': response_text,
                'model': "claude-3-5-sonnet-20241022",
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Received empty response from Claude API'
            }), 200
            
    except Exception as e:
        logger.error(f"Error testing Claude API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 200

@settings_bp.route('/backup', methods=['GET'])
def backup_configuration():
    """Create a backup of current configuration (without sensitive data)"""
    try:
        load_dotenv(ENV_FILE_PATH)
        
        backup_data = {
            'wordpress_url': os.getenv('WORDPRESS_URL', ''),
            'wordpress_username': os.getenv('WORDPRESS_USERNAME', ''),
            'google_api_configured': bool(os.getenv('GOOGLE_PLACES_API_KEY')),
            'claude_api_configured': bool(os.getenv('ANTHROPIC_API_KEY')),
            'admin_configured': bool(os.getenv('ADMIN_PASSWORD')),
            'backup_timestamp': os.path.getmtime(ENV_FILE_PATH) if os.path.exists(ENV_FILE_PATH) else None
        }
        
        return jsonify({
            'message': 'Configuration backup created',
            'backup': backup_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        return jsonify({'error': str(e)}), 500