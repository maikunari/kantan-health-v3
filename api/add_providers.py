"""
Add Providers API Blueprint
Handles adding individual and geographic provider collections
"""

from flask import Blueprint, request, jsonify
import subprocess
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

add_providers_bp = Blueprint('add_providers', __name__)

@add_providers_bp.route('/add-specific', methods=['POST'])
def add_specific_provider():
    """Add a specific healthcare provider"""
    try:
        data = request.json
        
        # Build command for add_specific_provider.py
        cmd = ['python3', 'add_specific_provider.py']
        
        # Add parameters based on request
        if data.get('place_id'):
            cmd.extend(['--place-id', data['place_id']])
        elif data.get('name'):
            cmd.extend(['--name', data['name']])
            if data.get('location'):
                cmd.extend(['--location', data['location']])
        else:
            return jsonify({'error': 'Either place_id or name is required'}), 400
        
        # Optional parameters
        if data.get('specialty'):
            cmd.extend(['--specialty', data['specialty']])
        
        # Pipeline control flags
        if data.get('skip_content_generation', False):
            cmd.append('--skip-content-generation')
        
        if data.get('skip_wordpress_sync', False):
            cmd.append('--skip-wordpress-sync')
        
        if data.get('dry_run', False):
            cmd.append('--dry-run')
        
        # Add JSON output flag for structured response
        cmd.append('--json-output')
        
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        # Execute the command
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            try:
                # Try to parse JSON output from the script
                output_data = json.loads(result.stdout)
                return jsonify({
                    'message': 'Provider addition completed successfully',
                    'provider_id': output_data.get('provider_id'),
                    'details': output_data,
                    'stdout': result.stdout,
                    'command': ' '.join(cmd)
                }), 200
            except json.JSONDecodeError:
                # Fallback to plain text output
                return jsonify({
                    'message': 'Provider addition completed successfully',
                    'stdout': result.stdout,
                    'command': ' '.join(cmd)
                }), 200
        else:
            logger.error(f"Command failed with return code {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")
            return jsonify({
                'error': f'Provider addition failed: {result.stderr or result.stdout}',
                'command': ' '.join(cmd),
                'return_code': result.returncode
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Provider addition timed out (5 minutes)'}), 500
    except Exception as e:
        logger.error(f"Error in add_specific_provider: {str(e)}")
        return jsonify({'error': str(e)}), 500

@add_providers_bp.route('/add-geographic', methods=['POST'])
def add_geographic_providers():
    """Add providers by geographic area"""
    try:
        data = request.json
        
        # Build command for add_geographic_providers.py
        cmd = ['python3', 'add_geographic_providers.py']
        
        # Geographic parameters
        if data.get('city'):
            if isinstance(data['city'], list):
                cmd.extend(['--cities', ','.join(data['city'])])
            else:
                cmd.extend(['--city', data['city']])
        
        if data.get('wards'):
            if isinstance(data['wards'], list):
                cmd.extend(['--wards', ','.join(data['wards'])])
            else:
                cmd.extend(['--wards', data['wards']])
        
        # Limit parameter
        if data.get('limit'):
            cmd.extend(['--limit', str(data['limit'])])
        
        # Optional specialty filter
        if data.get('specialty'):
            cmd.extend(['--specialty', data['specialty']])
        
        # Pipeline control flags
        if data.get('skip_content_generation', False):
            cmd.append('--skip-content-generation')
        
        if data.get('skip_wordpress_sync', False):
            cmd.append('--skip-wordpress-sync')
        
        if data.get('dry_run', False):
            cmd.append('--dry-run')
        
        # Add JSON output flag for structured response
        cmd.append('--json-output')
        
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        # Execute the command
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=600  # 10 minute timeout for geographic searches
        )
        
        if result.returncode == 0:
            try:
                # Try to parse JSON output from the script
                output_data = json.loads(result.stdout)
                return jsonify({
                    'message': 'Geographic provider search completed successfully',
                    'providers_found': output_data.get('providers_found', 0),
                    'providers_added': output_data.get('providers_added', 0),
                    'details': output_data,
                    'stdout': result.stdout,
                    'command': ' '.join(cmd)
                }), 200
            except json.JSONDecodeError:
                # Fallback to plain text output
                return jsonify({
                    'message': 'Geographic provider search completed successfully',
                    'stdout': result.stdout,
                    'command': ' '.join(cmd)
                }), 200
        else:
            logger.error(f"Command failed with return code {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")
            return jsonify({
                'error': f'Geographic provider search failed: {result.stderr or result.stdout}',
                'command': ' '.join(cmd),
                'return_code': result.returncode
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Geographic provider search timed out (10 minutes)'}), 500
    except Exception as e:
        logger.error(f"Error in add_geographic_providers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@add_providers_bp.route('/validate-place-id', methods=['POST'])
def validate_place_id():
    """Validate a Google Place ID without adding the provider"""
    try:
        data = request.json
        place_id = data.get('place_id')
        
        if not place_id:
            return jsonify({'error': 'place_id is required'}), 400
        
        # Use the specific provider script with dry-run to validate
        cmd = [
            'python3', 'add_specific_provider.py',
            '--place-id', place_id,
            '--dry-run',
            '--json-output'
        ]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=60  # 1 minute timeout for validation
        )
        
        if result.returncode == 0:
            try:
                output_data = json.loads(result.stdout)
                return jsonify({
                    'valid': True,
                    'provider_info': output_data,
                    'message': 'Place ID is valid'
                }), 200
            except json.JSONDecodeError:
                return jsonify({
                    'valid': True,
                    'message': 'Place ID appears valid',
                    'stdout': result.stdout
                }), 200
        else:
            return jsonify({
                'valid': False,
                'message': f'Place ID validation failed: {result.stderr or result.stdout}'
            }), 200  # Return 200 but with valid: false
            
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Place ID validation timed out'}), 500
    except Exception as e:
        logger.error(f"Error in validate_place_id: {str(e)}")
        return jsonify({'error': str(e)}), 500

@add_providers_bp.route('/search-preview', methods=['POST'])
def search_preview():
    """Preview what providers would be found by a search without adding them"""
    try:
        data = request.json
        
        if data.get('place_id'):
            # Use specific provider script for place ID preview
            cmd = [
                'python3', 'add_specific_provider.py',
                '--place-id', data['place_id'],
                '--dry-run',
                '--json-output'
            ]
        elif data.get('name'):
            # Use specific provider script for name search preview
            cmd = [
                'python3', 'add_specific_provider.py',
                '--name', data['name'],
                '--dry-run',
                '--json-output'
            ]
            if data.get('location'):
                cmd.extend(['--location', data['location']])
        elif data.get('city'):
            # Use geographic script for area preview
            cmd = [
                'python3', 'add_geographic_providers.py',
                '--dry-run',
                '--json-output'
            ]
            if isinstance(data['city'], list):
                cmd.extend(['--cities', ','.join(data['city'])])
            else:
                cmd.extend(['--city', data['city']])
            
            if data.get('limit'):
                cmd.extend(['--limit', str(data['limit'])])
        else:
            return jsonify({'error': 'Either place_id, name, or city is required'}), 400
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=120  # 2 minute timeout for preview
        )
        
        if result.returncode == 0:
            try:
                output_data = json.loads(result.stdout)
                return jsonify({
                    'preview': output_data,
                    'message': 'Search preview completed'
                }), 200
            except json.JSONDecodeError:
                return jsonify({
                    'preview': {'stdout': result.stdout},
                    'message': 'Search preview completed'
                }), 200
        else:
            return jsonify({
                'error': f'Search preview failed: {result.stderr or result.stdout}'
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Search preview timed out'}), 500
    except Exception as e:
        logger.error(f"Error in search_preview: {str(e)}")
        return jsonify({'error': str(e)}), 500