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
        
        if not provider_ids:
            # If no specific IDs, use filters
            limit = data.get('limit', 10)
            status = data.get('status', 'approved')
            
            session = Session()
            query = session.query(Provider).filter(Provider.status == status)
            
            # Only get providers missing AI content
            if 'all' in content_types:
                query = query.filter(
                    (Provider.ai_description.is_(None)) |
                    (Provider.ai_english_experience.is_(None)) |
                    (Provider.ai_review_summary.is_(None)) |
                    (Provider.seo_title.is_(None))
                )
            
            providers = query.limit(limit).all()
            provider_ids = [p.id for p in providers]
            session.close()
        
        if not provider_ids:
            return jsonify({'message': 'No providers found needing content generation'}), 200
        
        # Build command
        cmd = ['python3', 'run_mega_batch_automation.py']
        
        if provider_ids:
            cmd.extend(['--provider-ids', ','.join(map(str, provider_ids))])
        
        if dry_run:
            cmd.append('--dry-run')
        
        # Run in background
        if not dry_run:
            subprocess.Popen(cmd)
            message = f"Started content generation for {len(provider_ids)} providers"
        else:
            # For dry run, execute synchronously to get output
            result = subprocess.run(cmd, capture_output=True, text=True)
            message = result.stdout
        
        return jsonify({
            'message': message,
            'provider_count': len(provider_ids),
            'provider_ids': provider_ids,
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
        cmd = ['python3', 'run_mega_batch_automation.py', '--stats-only']
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
            'python3', 'run_mega_batch_automation.py',
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
        
        # Count providers by content completion
        stats = session.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN ai_description IS NOT NULL THEN 1 END) as with_description,
                COUNT(CASE WHEN english_experience_summary IS NOT NULL THEN 1 END) as with_experience,
                COUNT(CASE WHEN review_summary IS NOT NULL THEN 1 END) as with_reviews,
                COUNT(CASE WHEN seo_title IS NOT NULL THEN 1 END) as with_seo,
                COUNT(CASE WHEN ai_description IS NOT NULL 
                           AND english_experience_summary IS NOT NULL 
                           AND review_summary IS NOT NULL 
                           AND seo_title IS NOT NULL THEN 1 END) as fully_complete
            FROM providers
            WHERE status = 'approved'
        """)).fetchone()
        
        session.close()
        
        return jsonify({
            'batch_running': is_running,
            'content_stats': {
                'total_approved': stats[0],
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