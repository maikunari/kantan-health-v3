"""
Data Completion API Blueprint
Handles bulk data completion operations including geocoding, Google Places data, and AI content generation
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import subprocess
import logging
import time
from postgres_integration import Provider, get_postgres_config
from activity_logger import activity_logger

logger = logging.getLogger(__name__)

data_completion_bp = Blueprint('data_completion', __name__)

# Database setup
config = get_postgres_config()
engine = create_engine(
    f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
)
Session = sessionmaker(bind=engine)

@data_completion_bp.route('/geocode', methods=['POST'])
def geocode_missing_locations():
    """Trigger geocoding for providers missing latitude/longitude"""
    try:
        data = request.json or {}
        limit = data.get('limit', 50)
        dry_run = data.get('dry_run', False)
        
        session = Session()
        
        # Count providers missing location data
        missing_count = session.execute(text("""
            SELECT COUNT(*) FROM providers 
            WHERE latitude IS NULL OR longitude IS NULL
        """)).scalar()
        
        if missing_count == 0:
            return jsonify({
                'success': True,
                'message': 'No providers missing location data',
                'affected_count': 0
            })
        
        session.close()
        
        if dry_run:
            return jsonify({
                'success': True,
                'message': f'Dry run: Would geocode {min(missing_count, limit)} providers',
                'affected_count': min(missing_count, limit),
                'dry_run': True
            })
        
        # Execute the geocoding script (remove --automation flag that doesn't exist)
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'populate_provider_locations.py')
        cmd = ['python3', script_path]
        
        logger.info(f"Executing geocoding command: {' '.join(cmd)}")
        
        # Run in background with proper error handling
        try:
            process = subprocess.Popen(cmd, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     cwd=os.path.dirname(os.path.dirname(__file__)))
            
            # Wait a moment to check if process starts successfully
            time.sleep(0.5)
            poll_result = process.poll()
            
            if poll_result is not None:
                # Process already exited, capture error
                stdout, stderr = process.communicate()
                error_msg = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                logger.error(f"Geocoding script failed immediately: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': f'Geocoding script failed: {error_msg[:200]}...' if len(error_msg) > 200 else error_msg
                }), 500
            
            return jsonify({
                'success': True,
                'message': f'Geocoding started for up to {limit} providers',
                'affected_count': min(missing_count, limit),
                'process_id': process.pid
            })
            
        except Exception as e:
            logger.error(f"Failed to start geocoding process: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to start geocoding: {str(e)}'
            }), 500
        
    except Exception as e:
        logger.error(f"Error starting geocoding: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_completion_bp.route('/google-places', methods=['POST'])
def fetch_google_places_data():
    """Fetch missing Google Places data (hours, ratings, reviews, accessibility)"""
    try:
        data = request.json or {}
        limit = data.get('limit', 50)
        dry_run = data.get('dry_run', False)
        
        session = Session()
        
        # Count providers missing Google Places data
        missing_count = session.execute(text("""
            SELECT COUNT(*) FROM providers 
            WHERE business_hours IS NULL 
            OR rating IS NULL 
            OR wheelchair_accessible IS NULL
            OR parking_available IS NULL
        """)).scalar()
        
        if missing_count == 0:
            return jsonify({
                'success': True,
                'message': 'No providers missing Google Places data',
                'affected_count': 0
            })
        
        session.close()
        
        if dry_run:
            return jsonify({
                'success': True,
                'message': f'Dry run: Would fetch Google data for {min(missing_count, limit)} providers',
                'affected_count': min(missing_count, limit),
                'dry_run': True
            })
        
        # Execute the Google Places update script
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'update_existing_providers.py')
        cmd = ['python3', script_path, '--google-data', '--limit', str(limit)]
        
        logger.info(f"Executing Google Places command: {' '.join(cmd)}")
        
        # Run in background with proper error handling
        try:
            process = subprocess.Popen(cmd,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     cwd=os.path.dirname(os.path.dirname(__file__)))
            
            # Wait a moment to check if process starts successfully
            time.sleep(0.5)
            poll_result = process.poll()
            
            if poll_result is not None:
                # Process already exited, capture error
                stdout, stderr = process.communicate()
                error_msg = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                logger.error(f"Google Places script failed immediately: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': f'Google Places script failed: {error_msg[:200]}...' if len(error_msg) > 200 else error_msg
                }), 500
            
            return jsonify({
                'success': True,
                'message': f'Google Places data fetch started for up to {limit} providers',
                'affected_count': min(missing_count, limit),
                'process_id': process.pid
            })
            
        except Exception as e:
            logger.error(f"Failed to start Google Places process: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to start Google Places fetch: {str(e)}'
            }), 500
        
    except Exception as e:
        logger.error(f"Error starting Google Places data fetch: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_completion_bp.route('/ai-content', methods=['POST'])
def generate_ai_content():
    """Generate missing AI content using mega-batch processing"""
    try:
        data = request.json or {}
        limit = data.get('limit', 50)
        dry_run = data.get('dry_run', False)
        
        session = Session()
        
        # Count providers missing AI content
        missing_count = session.execute(text("""
            SELECT COUNT(*) FROM providers 
            WHERE ai_description IS NULL 
            OR ai_excerpt IS NULL 
            OR seo_title IS NULL 
            OR seo_meta_description IS NULL
        """)).scalar()
        
        if missing_count == 0:
            return jsonify({
                'success': True,
                'message': 'No providers missing AI content',
                'affected_count': 0
            })
        
        session.close()
        
        if dry_run:
            return jsonify({
                'success': True,
                'message': f'Dry run: Would generate AI content for {min(missing_count, limit)} providers',
                'affected_count': min(missing_count, limit),
                'dry_run': True
            })
        
        # For now, disable mega-batch due to proxies error and use fallback message
        logger.warning("AI content generation temporarily disabled due to configuration issues")
        return jsonify({
            'success': False,
            'error': 'AI content generation is temporarily disabled due to configuration issues with the Anthropic client. Please use the command line tools directly or contact support.',
            'affected_count': 0,
            'troubleshooting': {
                'command_line_alternative': f'python3 run_mega_batch_automation.py --limit {limit}',
                'error_details': 'Anthropic client initialization fails with proxies parameter error'
            }
        }), 503
        
    except Exception as e:
        logger.error(f"Error starting AI content generation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_completion_bp.route('/complete-all', methods=['POST'])
def complete_all_missing_data():
    """Execute complete data completion workflow in sequence"""
    try:
        data = request.json or {}
        limit = data.get('limit', 25)  # Smaller default for complete workflow
        dry_run = data.get('dry_run', False)
        
        if dry_run:
            return jsonify({
                'success': True,
                'message': f'Dry run: Would complete all missing data for up to {limit} providers',
                'workflow': [
                    'Fetch Google Places data',
                    'Geocode missing locations', 
                    'Generate AI content',
                    'Update WordPress (optional)'
                ],
                'dry_run': True
            })
        
        # Execute complete automation pipeline (remove --dry-run that's not supported)
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'run_automation.py')
        cmd = ['python3', script_path, '--daily-limit', str(limit)]
        
        logger.info(f"Executing complete automation command: {' '.join(cmd)}")
        
        # Run in background with proper error handling
        try:
            process = subprocess.Popen(cmd,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     cwd=os.path.dirname(os.path.dirname(__file__)))
            
            # Wait a moment to check if process starts successfully
            time.sleep(0.5)
            poll_result = process.poll()
            
            if poll_result is not None:
                # Process already exited, capture error
                stdout, stderr = process.communicate()
                error_msg = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                logger.error(f"Complete automation script failed immediately: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': f'Complete automation failed: {error_msg[:200]}...' if len(error_msg) > 200 else error_msg
                }), 500
            
            return jsonify({
                'success': True,
                'message': f'Complete data completion workflow started for up to {limit} providers',
                'process_id': process.pid,
                'workflow': [
                    'Phase 1: Google Places data collection',
                    'Phase 2: Location geocoding',
                    'Phase 3: AI content generation',
                    'Phase 4: Data validation',
                    'Phase 5: WordPress sync preparation',
                    'Phase 6: Status updates'
                ]
            })
            
        except Exception as e:
            logger.error(f"Failed to start complete automation process: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to start complete automation: {str(e)}'
            }), 500
        
    except Exception as e:
        logger.error(f"Error starting complete data completion: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_completion_bp.route('/provider/<int:provider_id>/fields', methods=['POST'])
def regenerate_provider_fields(provider_id):
    """Regenerate specific fields for a single provider"""
    try:
        data = request.json or {}
        fields = data.get('fields', [])
        
        logger.info(f"Received regeneration request for provider {provider_id} with fields: {fields}")
        
        if not fields:
            return jsonify({'error': 'No fields specified for regeneration'}), 400
        
        session = Session()
        provider = session.query(Provider).filter_by(id=provider_id).first()
        
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404
        
        provider_name = provider.provider_name
        session.close()
        
        # Map field types to appropriate scripts/methods
        results = {}
        processes = []
        
        # Check which fields need regeneration - match frontend field keys
        location_fields = ['latitude,longitude', 'coordinates', 'nearest_station']
        google_fields = ['business_hours', 'rating', 'google_rating', 'total_reviews', 'review_count', 'wheelchair_accessible', 'parking_available']
        ai_fields = ['ai_description', 'ai_excerpt', 'seo_title', 'seo_description', 'seo_meta_description', 'ai_english_experience', 'ai_review_summary', 'english_proficiency', 'english_experience_summary', 'review_summary']
        
        # Determine which scripts to run based on requested fields
        needs_location = any(field in fields for field in location_fields)
        needs_google = any(field in fields for field in google_fields)
        needs_ai = any(field in fields for field in ai_fields)
        
        logger.info(f"Field analysis - Location: {needs_location}, Google: {needs_google}, AI: {needs_ai}")
        logger.info(f"Location fields to check: {location_fields}")
        logger.info(f"Google fields to check: {google_fields}")
        logger.info(f"AI fields to check: {ai_fields}")
        
        # Execute geocoding if needed
        if needs_location:
            # For now, return a message that location updates need to be run manually
            logger.info(f"Location update requested for provider {provider_id}")
            results['location'] = f'Location update requested for {provider_name}. Please run: python3 populate_provider_locations.py'
            
            # Future: implement direct geocoding here when populate_provider_locations.py supports single provider
        
        # Execute Google Places data fetch if needed
        if needs_google:
            script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'update_single_provider.py')
            cmd = ['python3', script_path, '--provider-id', str(provider_id)]
            
            logger.info(f"Executing Google Places update for provider {provider_id}: {' '.join(cmd)}")
            
            try:
                process = subprocess.Popen(cmd,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         cwd=os.path.dirname(os.path.dirname(__file__)))
                processes.append(('google', process))
                results['google_data'] = f'Google Places data fetch started for {provider_name}'
            except Exception as e:
                logger.error(f"Failed to start Google Places fetch: {str(e)}")
                results['google_data'] = f'Failed to start Google Places fetch: {str(e)}'
        
        # Execute AI content generation if needed
        if needs_ai:
            # For AI content, we'll use a simpler approach due to mega-batch complexity
            script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generate_provider_content.py')
            cmd = ['python3', script_path, '--provider-id', str(provider_id)]
            
            logger.info(f"Executing AI content generation for provider {provider_id}: {' '.join(cmd)}")
            
            try:
                process = subprocess.Popen(cmd,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         cwd=os.path.dirname(os.path.dirname(__file__)))
                processes.append(('ai', process))
                results['ai_content'] = f'AI content generation started for {provider_name}'
            except Exception as e:
                logger.error(f"Failed to start AI content generation: {str(e)}")
                results['ai_content'] = f'Failed to start AI content generation: {str(e)}'
        
        # Log the activity
        activity_logger.log_activity(
            activity_type='regenerate_provider_fields',
            activity_category='data_quality',
            description=f'Regenerating {len(fields)} fields for {provider_name}',
            provider_id=provider_id,
            provider_name=provider_name,
            details={
                'fields_requested': fields,
                'actions_triggered': list(results.keys())
            },
            status='success' if results else 'error'
        )
        
        if not results:
            return jsonify({
                'success': False,
                'message': 'No matching regeneration actions found for the selected fields',
                'fields_requested': fields
            }), 400
        
        return jsonify({
            'success': True,
            'message': f'Field regeneration started for {provider_name}',
            'provider_id': provider_id,
            'fields_requested': fields,
            'actions_triggered': results,
            'process_count': len(processes)
        })
        
    except Exception as e:
        logger.error(f"Error regenerating provider fields: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_completion_bp.route('/status/<int:process_id>', methods=['GET'])
def get_completion_status(process_id):
    """Get status of a data completion process"""
    try:
        import psutil
        
        try:
            process = psutil.Process(process_id)
            if process.is_running():
                return jsonify({
                    'status': 'running',
                    'process_id': process_id,
                    'process_name': process.name(),
                    'cpu_percent': process.cpu_percent(),
                    'memory_info': process.memory_info()._asdict()
                })
            else:
                return jsonify({
                    'status': 'completed',
                    'process_id': process_id,
                    'exit_code': process.poll()
                })
        except psutil.NoSuchProcess:
            return jsonify({
                'status': 'completed',
                'process_id': process_id,
                'message': 'Process completed or not found'
            })
        
    except Exception as e:
        logger.error(f"Error checking process status: {str(e)}")
        return jsonify({'error': str(e)}), 500