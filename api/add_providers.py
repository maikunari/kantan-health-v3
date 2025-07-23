"""
Add Providers API Blueprint
Handles adding individual and geographic provider collections
"""

from flask import Blueprint, request, jsonify
import subprocess
import json
import logging
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from postgres_integration import Provider, get_postgres_config

logger = logging.getLogger(__name__)

add_providers_bp = Blueprint('add_providers', __name__)

# Database setup
config = get_postgres_config()
engine = create_engine(
    f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
)
Session = sessionmaker(bind=engine)

def get_recently_added_providers(since_minutes=5):
    """Get providers added in the last N minutes (created_at is stored as date string)"""
    try:
        session = Session()
        # Since created_at is stored as date string (YYYY-MM-DD), get providers from today
        today_str = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"Querying for providers added today: {today_str}")
        
        providers = session.query(Provider).filter(
            Provider.created_at == today_str
        ).order_by(Provider.id.desc()).all()  # Order by ID since created_at doesn't have time
        
        logger.info(f"Found {len(providers)} providers added today")
        
        result = []
        for provider in providers:
            result.append({
                'id': provider.id,
                'provider_name': provider.provider_name,
                'address': provider.address,
                'city': provider.city,
                'ward': provider.district,
                'phone': provider.phone,
                'website': provider.website,
                'specialties': provider.specialties,
                'english_proficiency': provider.english_proficiency,
                'english_proficiency_score': provider.proficiency_score,
                'business_hours': provider.business_hours,
                'ai_description': provider.ai_description,
                'ai_english_experience': provider.english_experience_summary,
                'ai_review_summary': provider.review_summary,
                'seo_title': provider.seo_title,
                'seo_description': provider.seo_meta_description,
                'featured_image_url': provider.selected_featured_image,
                'status': provider.status,
                'wordpress_id': provider.wordpress_post_id,
                'last_synced': getattr(provider, 'last_wordpress_sync', None),
                'created_at': provider.created_at if provider.created_at else None
            })
        
        session.close()
        return result
    except Exception as e:
        logger.error(f"Error getting recently added providers: {str(e)}")
        return []

def run_full_pipeline_for_newly_added_providers(num_providers):
    """Run AI content generation and WordPress sync for newly added providers"""
    try:
        pipeline_results = {
            'ai_content_success': False,
            'wordpress_sync_success': False,
            'ai_output': '',
            'wp_output': '',
            'providers_processed': 0
        }
        
        # Generate AI content for newly added providers (mega batch will process providers without AI content)
        logger.info(f"Running mega batch AI content generation for up to {num_providers} providers...")
        ai_cmd = ['python3', 'run_mega_batch_automation.py', '--limit', str(num_providers)]
        ai_result = subprocess.run(ai_cmd, capture_output=True, text=True, timeout=600)
        
        pipeline_results['ai_content_success'] = ai_result.returncode == 0
        pipeline_results['ai_output'] = ai_result.stdout
        
        if ai_result.returncode != 0:
            logger.warning(f"AI content generation failed: {ai_result.stderr}")
        else:
            logger.info(f"AI content generation completed successfully")
        
        # Sync to WordPress (will sync providers that have content but aren't synced)
        logger.info(f"Running WordPress sync for up to {num_providers} providers...")
        wp_cmd = ['python3', 'wordpress_sync_manager.py', '--sync-all', '--limit', str(num_providers)]
        wp_result = subprocess.run(wp_cmd, capture_output=True, text=True, timeout=600)
        
        pipeline_results['wordpress_sync_success'] = wp_result.returncode == 0
        pipeline_results['wp_output'] = wp_result.stdout
        
        if wp_result.returncode != 0:
            logger.warning(f"WordPress sync failed: {wp_result.stderr}")
        else:
            logger.info(f"WordPress sync completed successfully")
        
        pipeline_results['providers_processed'] = num_providers
        
        return pipeline_results
    except Exception as e:
        logger.error(f"Error running full pipeline: {str(e)}")
        return {
            'ai_content_success': False,
            'wordpress_sync_success': False,
            'error': str(e),
            'providers_processed': 0
        }

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
                # Try to parse JSON output from the script (get the last JSON object)
                stdout_lines = result.stdout.strip().split('\n')
                json_line = None
                for line in reversed(stdout_lines):
                    if line.startswith('{') and line.endswith('}'):
                        json_line = line
                        break
                
                if not json_line:
                    raise json.JSONDecodeError("No JSON found in output", result.stdout, 0)
                
                output_data = json.loads(json_line)
                provider_id = output_data.get('provider_id')
                
                # Run full pipeline if not skipped and not dry run
                pipeline_results = {}
                if provider_id and not data.get('dry_run', False):
                    if not data.get('skip_content_generation', False) or not data.get('skip_wordpress_sync', False):
                        # Run the pipeline for the newly added provider
                        pipeline_results = run_full_pipeline_for_newly_added_providers(1)
                
                # Get recently added providers to return (use longer time window for reliability)
                recent_providers = get_recently_added_providers(10) if not data.get('dry_run', False) else []
                
                return jsonify({
                    'message': 'Provider addition completed successfully',
                    'provider_id': provider_id,
                    'details': output_data,
                    'pipeline_results': pipeline_results,
                    'recent_providers': recent_providers,
                    'providers_added': len(recent_providers),
                    'stdout': result.stdout,
                    'command': ' '.join(cmd)
                }), 200
            except json.JSONDecodeError:
                # Fallback to plain text output
                recent_providers = get_recently_added_providers(2) if not data.get('dry_run', False) else []
                return jsonify({
                    'message': 'Provider addition completed successfully',
                    'recent_providers': recent_providers,
                    'providers_added': len(recent_providers),
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
                # Try to parse JSON output from the script (get the last JSON object)
                stdout_lines = result.stdout.strip().split('\n')
                json_line = None
                for line in reversed(stdout_lines):
                    if line.startswith('{') and line.endswith('}'):
                        json_line = line
                        break
                
                if not json_line:
                    raise json.JSONDecodeError("No JSON found in output", result.stdout, 0)
                
                output_data = json.loads(json_line)
                providers_added = output_data.get('providers_added', 0)
                logger.info(f"Parsed providers_added from script output: {providers_added}")
                logger.info(f"Full script output JSON: {output_data}")
                logger.info(f"Raw stdout length: {len(result.stdout)} chars")
                
                # Get recently added providers to return (use longer time window for reliability)
                recent_providers = get_recently_added_providers(10) if not data.get('dry_run', False) else []
                logger.info(f"Retrieved recent providers: {len(recent_providers)} providers")
                
                # If providers were added and pipeline not skipped, run full pipeline
                pipeline_summary = {}
                if providers_added > 0 and not data.get('dry_run', False):
                    if not data.get('skip_content_generation', False) or not data.get('skip_wordpress_sync', False):
                        # Run the pipeline for all newly added providers at once
                        pipeline_result = run_full_pipeline_for_newly_added_providers(providers_added)
                        
                        pipeline_summary['total_processed'] = providers_added
                        pipeline_summary['ai_success_count'] = providers_added if pipeline_result.get('ai_content_success') else 0
                        pipeline_summary['wp_success_count'] = providers_added if pipeline_result.get('wordpress_sync_success') else 0
                        pipeline_summary['ai_content_success'] = pipeline_result.get('ai_content_success', False)
                        pipeline_summary['wordpress_sync_success'] = pipeline_result.get('wordpress_sync_success', False)
                
                return jsonify({
                    'message': 'Geographic provider search completed successfully',
                    'providers_found': output_data.get('providers_found', 0),
                    'providers_added': providers_added,
                    'details': output_data,
                    'pipeline_summary': pipeline_summary,
                    'recent_providers': recent_providers,
                    'stdout': result.stdout,
                    'command': ' '.join(cmd)
                }), 200
            except json.JSONDecodeError:
                # Fallback to plain text output
                recent_providers = get_recently_added_providers(5) if not data.get('dry_run', False) else []
                return jsonify({
                    'message': 'Geographic provider search completed successfully',
                    'recent_providers': recent_providers,
                    'providers_added': len(recent_providers),
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