"""
WordPress Sync API Blueprint
Handles WordPress synchronization operations and monitoring
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import subprocess
import json
import logging
from datetime import datetime
from postgres_integration import Provider, get_postgres_config

logger = logging.getLogger(__name__)

sync_bp = Blueprint('sync', __name__)

# Database setup
config = get_postgres_config()
engine = create_engine(
    f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
)
Session = sessionmaker(bind=engine)

@sync_bp.route('/sync', methods=['POST'])
def sync_providers():
    """Trigger WordPress sync for providers"""
    try:
        data = request.json
        provider_ids = data.get('provider_ids', [])
        sync_all = data.get('sync_all', False)
        limit = data.get('limit', 25)
        force = data.get('force', False)
        dry_run = data.get('dry_run', False)
        
        # Build command
        cmd = ['python', 'wordpress_sync_manager.py']
        
        if sync_all:
            cmd.append('--sync-all')
        elif provider_ids:
            cmd.extend(['--provider-ids', ','.join(map(str, provider_ids))])
        else:
            # Default to syncing providers that need it
            session = Session()
            providers = session.query(Provider).filter(
                Provider.status == 'approved',
                Provider.wordpress_post_id.is_(None),
                Provider.ai_description.isnot(None)
            ).limit(limit).all()
            provider_ids = [p.id for p in providers]
            session.close()
            
            if provider_ids:
                cmd.extend(['--provider-ids', ','.join(map(str, provider_ids))])
        
        if limit:
            cmd.extend(['--limit', str(limit)])
        
        if force:
            cmd.append('--force')
        
        if dry_run:
            cmd.append('--dry-run')
        
        # Run command
        if not dry_run:
            subprocess.Popen(cmd)
            message = f"Started WordPress sync for {len(provider_ids) if provider_ids else 'all'} providers"
        else:
            # For dry run, execute synchronously
            result = subprocess.run(cmd, capture_output=True, text=True)
            message = result.stdout
        
        return jsonify({
            'message': message,
            'provider_count': len(provider_ids) if provider_ids else 'all',
            'dry_run': dry_run
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting sync: {str(e)}")
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/status', methods=['GET'])
def get_sync_status():
    """Get WordPress sync status and statistics"""
    try:
        session = Session()
        
        # Overall sync stats
        sync_stats = session.execute(text("""
            SELECT 
                COUNT(*) as total_providers,
                COUNT(wordpress_post_id) as synced_providers,
                COUNT(CASE WHEN status = 'approved' AND wordpress_post_id IS NULL THEN 1 END) as pending_sync,
                COUNT(CASE WHEN last_wordpress_sync > CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as synced_24h
            FROM providers
        """)).fetchone()
        
        # Recent sync operations
        recent_syncs = session.execute(text("""
            SELECT 
                sync_type,
                sync_status,
                COUNT(*) as count,
                MAX(sync_timestamp) as last_operation
            FROM wordpress_sync_log
            WHERE sync_timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
            GROUP BY sync_type, sync_status
            ORDER BY last_operation DESC
        """)).fetchall()
        
        # Sync errors
        recent_errors = session.execute(text("""
            SELECT 
                provider_id,
                error_message,
                sync_timestamp
            FROM wordpress_sync_log
            WHERE sync_status = 'error'
                AND sync_timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
            ORDER BY sync_timestamp DESC
            LIMIT 10
        """)).fetchall()
        
        session.close()
        
        return jsonify({
            'sync_overview': {
                'total_providers': sync_stats[0],
                'synced_providers': sync_stats[1],
                'pending_sync': sync_stats[2],
                'synced_last_24h': sync_stats[3],
                'sync_percentage': round(sync_stats[1] / sync_stats[0] * 100, 2) if sync_stats[0] > 0 else 0
            },
            'recent_operations': [
                {
                    'operation': row[0],
                    'status': row[1],
                    'count': row[2],
                    'last_operation': row[3].isoformat() if row[3] else None
                }
                for row in recent_syncs
            ],
            'recent_errors': [
                {
                    'provider_id': row[0],
                    'error': row[1],
                    'timestamp': row[2].isoformat() if row[2] else None
                }
                for row in recent_errors
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/check/<int:provider_id>', methods=['GET'])
def check_provider_sync(provider_id):
    """Check sync status for a specific provider"""
    try:
        session = Session()
        
        # Get provider info
        provider = session.query(Provider).filter_by(id=provider_id).first()
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404
        
        # Get sync history
        sync_history = session.execute(text("""
            SELECT 
                sync_type,
                sync_status,
                wordpress_post_id,
                content_hash,
                error_message,
                sync_timestamp
            FROM wordpress_sync_log
            WHERE provider_id = :provider_id
            ORDER BY sync_timestamp DESC
            LIMIT 10
        """), {'provider_id': provider_id}).fetchall()
        
        session.close()
        
        return jsonify({
            'provider': {
                'id': provider.id,
                'name': provider.provider_name,
                'status': provider.status,
                'wordpress_id': provider.wordpress_post_id,
                'last_synced': provider.last_wordpress_sync.isoformat() if provider.last_wordpress_sync else None
            },
            'sync_history': [
                {
                    'operation': row[0],
                    'status': row[1],
                    'wordpress_id': row[2],
                    'content_hash': row[3],
                    'error': row[4],
                    'timestamp': row[5].isoformat() if row[5] else None
                }
                for row in sync_history
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking provider sync: {str(e)}")
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/test-connection', methods=['GET'])
def test_wordpress_connection():
    """Test WordPress API connection"""
    try:
        cmd = ['python', 'wordpress_sync_manager.py', '--test-connection']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                'status': 'connected',
                'message': 'WordPress API connection successful',
                'output': result.stdout
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'WordPress API connection failed',
                'error': result.stderr
            }), 500
            
    except Exception as e:
        logger.error(f"Error testing WordPress connection: {str(e)}")
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/force-update/<int:provider_id>', methods=['POST'])
def force_update_provider(provider_id):
    """Force update a specific provider in WordPress"""
    try:
        cmd = [
            'python', 'wordpress_sync_manager.py',
            '--provider-ids', str(provider_id),
            '--force'
        ]
        
        subprocess.Popen(cmd)
        
        return jsonify({
            'message': f'Started force update for provider {provider_id}'
        }), 200
        
    except Exception as e:
        logger.error(f"Error forcing update: {str(e)}")
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/batch-status', methods=['GET'])
def get_batch_sync_status():
    """Get status of current batch sync operations"""
    try:
        # Check if sync process is running
        cmd = "ps aux | grep 'wordpress_sync_manager.py' | grep -v grep"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        is_running = result.returncode == 0
        
        # Get sync queue size
        session = Session()
        queue_stats = session.execute(text("""
            SELECT 
                COUNT(*) as total_approved,
                COUNT(CASE WHEN wordpress_post_id IS NULL THEN 1 END) as not_synced,
                COUNT(CASE WHEN wordpress_post_id IS NOT NULL 
                           AND last_wordpress_sync < CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) as needs_update
            FROM providers
            WHERE status = 'approved'
                AND ai_description IS NOT NULL
        """)).fetchone()
        
        session.close()
        
        return jsonify({
            'sync_running': is_running,
            'queue_stats': {
                'total_eligible': queue_stats[0],
                'not_synced': queue_stats[1],
                'needs_update': queue_stats[2],
                'total_pending': queue_stats[1] + queue_stats[2]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting batch sync status: {str(e)}")
        return jsonify({'error': str(e)}), 500