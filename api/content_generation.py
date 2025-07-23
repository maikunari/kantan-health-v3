"""
Content Generation API Blueprint
Handles AI content generation requests and monitoring
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import subprocess
import json
import logging
from postgres_integration import Provider, get_postgres_config

logger = logging.getLogger(__name__)

content_bp = Blueprint('content', __name__)

# Database setup
config = get_postgres_config()
engine = create_engine(
    f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
)
Session = sessionmaker(bind=engine)

@content_bp.route('/generate', methods=['POST'])
def generate_content():
    """Trigger AI content generation for providers"""
    try:
        data = request.json
        provider_ids = data.get('provider_ids', [])
        content_types = data.get('content_types', ['all'])
        dry_run = data.get('dry_run', False)
        
        # Note: The mega batch automation script processes providers based on missing content,
        # not by status. The status filter here is for informational purposes only.
        
        # Build command - the script will automatically find providers needing content
        cmd = ['python', 'run_mega_batch_automation.py']
        
        limit = data.get('limit', 10)
        if limit:
            cmd.extend(['--limit', str(limit)])
        
        if dry_run:
            cmd.append('--dry-run')
        
        # Add test mode flag for synchronous execution with immediate feedback
        test_mode = data.get('test_mode', False)
        
        # For user feedback, check what providers would be processed
        session = Session()
        status_filter = data.get('status')
        
        # Count providers that need content (matching the script's logic)
        query = session.query(Provider).filter(
            (Provider.ai_description.is_(None)) |
            (Provider.seo_title.is_(None)) |
            (Provider.seo_meta_description.is_(None)) |
            (Provider.selected_featured_image.is_(None)) |
            (Provider.selected_featured_image == '')
        )
        
        # If user selected a status filter, count how many match that status
        if status_filter:
            providers_with_status = query.filter(Provider.status == status_filter).count()
            total_needing_content = query.count()
            
            if providers_with_status == 0 and total_needing_content > 0:
                session.close()
                return jsonify({
                    'message': f'No {status_filter} providers need content generation. '
                              f'However, {total_needing_content} providers with other statuses need content.',
                    'providers_needing_content': total_needing_content,
                    'status_filter_mismatch': True
                }), 200
        
        session.close()
        
        # Get the directory where the script is located
        import os
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Run in test mode (synchronous) or normal mode (background)
        if test_mode or dry_run:
            # Execute synchronously to get immediate feedback
            logger.info(f"Running content generation in {'test' if test_mode else 'dry-run'} mode: {' '.join(cmd)}")
            
            try:
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True,
                    cwd=script_dir,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode != 0:
                    logger.error(f"Content generation failed: {result.stderr}")
                    return jsonify({
                        'error': f'Content generation failed: {result.stderr}',
                        'stdout': result.stdout,
                        'command': ' '.join(cmd),
                        'working_dir': script_dir
                    }), 500
                
                # Parse output to get results
                output_lines = result.stdout.split('\n')
                providers_processed = 0
                for line in output_lines:
                    if 'Processing batch' in line or 'Updated provider' in line:
                        providers_processed += 1
                
                message = f"Test run complete. Output:\n{result.stdout[-1000:]}"  # Last 1000 chars
                
                return jsonify({
                    'message': message,
                    'success': True,
                    'providers_processed': providers_processed,
                    'full_output': result.stdout,
                    'command': ' '.join(cmd),
                    'test_mode': test_mode
                }), 200
                
            except subprocess.TimeoutExpired:
                return jsonify({'error': 'Content generation timed out after 5 minutes'}), 500
            except Exception as e:
                logger.error(f"Test mode error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        else:
            # Normal background execution
            logger.info(f"Starting content generation with command: {' '.join(cmd)}")
            
            try:
                process = subprocess.Popen(
                    cmd,
                    cwd=script_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Check if process started successfully
                import time
                time.sleep(0.5)  # Wait a bit longer
                
                if process.poll() is not None:
                    # Process ended immediately, probably an error
                    stderr = process.stderr.read().decode('utf-8')
                    stdout = process.stdout.read().decode('utf-8')
                    logger.error(f"Process ended immediately. Stdout: {stdout}, Stderr: {stderr}")
                    return jsonify({
                        'error': f'Process failed to start: {stderr or stdout or "Unknown error"}',
                        'stdout': stdout,
                        'stderr': stderr,
                        'command': ' '.join(cmd),
                        'working_dir': script_dir
                    }), 500
                
                message = f"Started content generation for up to {limit} providers (PID: {process.pid})"
                logger.info(f"Content generation process started with PID: {process.pid}")
                
            except Exception as e:
                logger.error(f"Failed to start subprocess: {str(e)}")
                return jsonify({
                    'error': f'Failed to start content generation: {str(e)}',
                    'command': ' '.join(cmd),
                    'working_dir': script_dir
                }), 500
        
        return jsonify({
            'message': message,
            'limit': limit,
            'dry_run': dry_run
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting content generation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@content_bp.route('/status', methods=['GET'])
def get_content_status():
    """Get content generation status and statistics"""
    try:
        # Run stats-only command
        cmd = ['python', 'run_mega_batch_automation.py', '--stats-only']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return jsonify({'error': 'Failed to get statistics'}), 500
        
        # Parse output
        output_lines = result.stdout.strip().split('\n')
        stats = {}
        
        for line in output_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                stats[key.strip()] = value.strip()
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting content status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@content_bp.route('/preview/<int:provider_id>', methods=['GET'])
def preview_content(provider_id):
    """Preview AI-generated content for a provider"""
    try:
        session = Session()
        provider = session.query(Provider).filter_by(id=provider_id).first()
        
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404
        
        content = {
            'provider_name': provider.provider_name,
            'current_content': {
                'ai_description': provider.ai_description,
                'ai_english_experience': provider.ai_english_experience,
                'ai_review_summary': provider.ai_review_summary,
                'seo_title': provider.seo_title,
                'seo_description': provider.seo_description,
                'seo_focus_keyword': provider.seo_focus_keyword,
                'seo_keywords': provider.seo_keywords
            },
            'source_data': {
                'address': provider.address,
                'city': provider.city,
                'specialties': provider.specialties,
                'english_proficiency': provider.english_proficiency,
                'review_highlights': provider.review_highlights
            }
        }
        
        session.close()
        return jsonify(content), 200
        
    except Exception as e:
        logger.error(f"Error previewing content: {str(e)}")
        return jsonify({'error': str(e)}), 500

@content_bp.route('/regenerate/<int:provider_id>', methods=['POST'])
def regenerate_content(provider_id):
    """Force regeneration of content for a specific provider"""
    try:
        data = request.json
        content_types = data.get('content_types', ['all'])
        
        # Clear existing content to force regeneration
        session = Session()
        provider = session.query(Provider).filter_by(id=provider_id).first()
        
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404
        
        # Clear relevant fields
        if 'all' in content_types or 'description' in content_types:
            provider.ai_description = None
        if 'all' in content_types or 'experience' in content_types:
            provider.ai_english_experience = None
        if 'all' in content_types or 'reviews' in content_types:
            provider.ai_review_summary = None
        if 'all' in content_types or 'seo' in content_types:
            provider.seo_title = None
            provider.seo_description = None
            provider.seo_focus_keyword = None
            provider.seo_keywords = None
        
        session.commit()
        session.close()
        
        # Trigger regeneration
        cmd = [
            'python', 'run_mega_batch_automation.py',
            '--provider-ids', str(provider_id)
        ]
        
        subprocess.Popen(cmd)
        
        return jsonify({
            'message': f'Started content regeneration for provider {provider_id}',
            'content_types': content_types
        }), 200
        
    except Exception as e:
        logger.error(f"Error regenerating content: {str(e)}")
        return jsonify({'error': str(e)}), 500

@content_bp.route('/check-providers', methods=['GET'])
def check_providers_needing_content():
    """Check which providers need content generation"""
    try:
        session = Session()
        
        # Get counts matching the mega batch script's logic
        total_providers = session.query(Provider).count()
        
        # Providers needing any content (matching run_mega_batch_automation.py logic)
        needing_content = session.query(Provider).filter(
            (Provider.ai_description.is_(None)) |
            (Provider.seo_title.is_(None)) |
            (Provider.seo_meta_description.is_(None)) |
            (Provider.selected_featured_image.is_(None)) |
            (Provider.selected_featured_image == '')
        ).all()
        
        # Get sample of providers needing content
        sample_providers = []
        for provider in needing_content[:5]:  # First 5 as sample
            sample_providers.append({
                'id': provider.id,
                'name': provider.provider_name,
                'status': provider.status,
                'has_description': bool(provider.ai_description),
                'has_seo_title': bool(provider.seo_title),
                'has_seo_meta': bool(provider.seo_meta_description),
                'has_featured_image': bool(provider.selected_featured_image)
            })
        
        session.close()
        
        return jsonify({
            'total_providers': total_providers,
            'providers_needing_content': len(needing_content),
            'sample_providers': sample_providers
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking providers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@content_bp.route('/batch-status', methods=['GET'])
def get_batch_status():
    """Get status of current batch processing"""
    try:
        # Check if any Python processes are running mega batch
        cmd = "ps aux | grep 'run_mega_batch_automation.py' | grep -v grep"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        is_running = result.returncode == 0
        
        # Get recent processing stats from database
        session = Session()
        
        # Count providers by content completion (include all statuses)
        stats = session.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN ai_description IS NOT NULL AND ai_description != '' THEN 1 END) as with_description,
                COUNT(CASE WHEN english_experience_summary IS NOT NULL AND english_experience_summary != '' THEN 1 END) as with_experience,
                COUNT(CASE WHEN review_summary IS NOT NULL AND review_summary != '' THEN 1 END) as with_reviews,
                COUNT(CASE WHEN seo_title IS NOT NULL AND seo_title != '' THEN 1 END) as with_seo,
                COUNT(CASE WHEN ai_description IS NOT NULL AND ai_description != ''
                           AND english_experience_summary IS NOT NULL AND english_experience_summary != ''
                           AND review_summary IS NOT NULL AND review_summary != ''
                           AND seo_title IS NOT NULL AND seo_title != '' THEN 1 END) as fully_complete
            FROM providers
        """)).fetchone()
        
        # Get separate counts for approved and pending
        approved_stats = session.execute(text("""
            SELECT COUNT(*) as total
            FROM providers
            WHERE status = 'approved'
        """)).fetchone()
        
        pending_stats = session.execute(text("""
            SELECT COUNT(*) as total
            FROM providers
            WHERE status = 'pending'
        """)).fetchone()
        
        session.close()
        
        return jsonify({
            'batch_running': is_running,
            'content_stats': {
                'total_approved': approved_stats[0] if approved_stats else 0,
                'total_pending': pending_stats[0] if pending_stats else 0,
                'total_providers': stats[0],
                'with_description': stats[1],
                'with_experience': stats[2],
                'with_reviews': stats[3],
                'with_seo': stats[4],
                'fully_complete': stats[5],
                'pending_content': stats[0] - stats[5]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting batch status: {str(e)}")
        return jsonify({'error': str(e)}), 500