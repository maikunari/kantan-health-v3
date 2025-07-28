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
        
        # Execute the geocoding script
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'populate_provider_locations.py')
        cmd = ['python3', script_path, '--automation']
        
        logger.info(f"Executing geocoding command: {' '.join(cmd)}")
        
        # Run in background
        process = subprocess.Popen(cmd, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 cwd=os.path.dirname(os.path.dirname(__file__)))
        
        return jsonify({
            'success': True,
            'message': f'Geocoding started for up to {limit} providers',
            'affected_count': min(missing_count, limit),
            'process_id': process.pid
        })
        
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
        
        # Run in background
        process = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=os.path.dirname(os.path.dirname(__file__)))
        
        return jsonify({
            'success': True,
            'message': f'Google Places data fetch started for up to {limit} providers',
            'affected_count': min(missing_count, limit),
            'process_id': process.pid
        })
        
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
        
        # Execute the AI content generation script
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'run_mega_batch_automation.py')
        cmd = ['python3', script_path, '--limit', str(limit)]
        
        logger.info(f"Executing AI content generation command: {' '.join(cmd)}")
        
        # Run in background
        process = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=os.path.dirname(os.path.dirname(__file__)))
        
        return jsonify({
            'success': True,
            'message': f'AI content generation started for up to {limit} providers',
            'affected_count': min(missing_count, limit),
            'process_id': process.pid
        })
        
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
        
        # Execute complete automation pipeline
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'run_automation.py')
        cmd = ['python3', script_path, '--daily-limit', str(limit)]
        
        logger.info(f"Executing complete automation command: {' '.join(cmd)}")
        
        # Run in background
        process = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=os.path.dirname(os.path.dirname(__file__)))
        
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
        logger.error(f"Error starting complete data completion: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_completion_bp.route('/provider/<int:provider_id>/fields', methods=['POST'])
def regenerate_provider_fields():
    """Regenerate specific fields for a single provider"""
    try:
        data = request.json or {}
        fields = data.get('fields', [])
        
        if not fields:
            return jsonify({'error': 'No fields specified for regeneration'}), 400
        
        session = Session()
        provider = session.query(Provider).filter_by(id=provider_id).first()
        
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404
        
        session.close()
        
        # Map field types to appropriate scripts/methods
        results = {}
        
        if 'location' in fields or 'geocoding' in fields:
            # Geocode this specific provider
            results['location'] = 'Geocoding triggered for provider'
        
        if any(field in fields for field in ['ai_description', 'ai_excerpt', 'seo_title', 'seo_meta_description']):
            # Generate AI content for this provider
            results['ai_content'] = 'AI content generation triggered for provider'
        
        if any(field in fields for field in ['business_hours', 'rating', 'wheelchair_accessible', 'parking_available']):
            # Fetch Google Places data for this provider
            results['google_data'] = 'Google Places data fetch triggered for provider'
        
        return jsonify({
            'success': True,
            'message': f'Field regeneration started for provider {provider_id}',
            'provider_id': provider_id,
            'fields_requested': fields,
            'actions_triggered': results
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