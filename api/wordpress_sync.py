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
import psutil
import time
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict
from postgres_integration import Provider, get_postgres_config

logger = logging.getLogger(__name__)

sync_bp = Blueprint('sync', __name__)

# Database setup
config = get_postgres_config()
engine = create_engine(
    f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
)
Session = sessionmaker(bind=engine)

# Simple in-memory process tracking
active_sync_processes = {}

def cleanup_completed_processes():
    """Clean up completed sync processes"""
    completed_processes = []
    for sync_id, process_info in list(active_sync_processes.items()):
        process = process_info['process']
        if process.poll() is not None:
            # Process has completed
            completed_processes.append(sync_id)
            process_info['status'] = 'COMPLETED' if process.returncode == 0 else 'ERROR'
            if process.returncode != 0:
                stderr = process.stderr.read().decode('utf-8')
                process_info['error'] = stderr
            
    # Remove completed processes after a delay to allow status checks
    for sync_id in completed_processes:
        process_info = active_sync_processes[sync_id]
        # Keep completed processes for 30 seconds for status reporting
        if 'completed_at' not in process_info:
            process_info['completed_at'] = datetime.now().isoformat()
        else:
            completed_time = datetime.fromisoformat(process_info['completed_at'])
            if (datetime.now() - completed_time).seconds > 30:
                del active_sync_processes[sync_id]

def get_sync_running_status():
    """Check if any sync processes are currently running"""
    cleanup_completed_processes()
    running_processes = [p for p in active_sync_processes.values() if p['status'] == 'RUNNING']
    return len(running_processes) > 0, running_processes

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
        
        # Get the correct working directory
        import os
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Run command
        if not dry_run:
            logger.info(f"Starting WordPress sync with command: {' '.join(cmd)}")
            logger.info(f"Working directory: {script_dir}")
            
            process = subprocess.Popen(
                cmd,
                cwd=script_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Track the process
            sync_id = f"sync_{int(time.time())}"
            active_sync_processes[sync_id] = {
                'process': process,
                'started_at': datetime.now().isoformat(),
                'provider_ids': provider_ids,
                'provider_count': len(provider_ids) if provider_ids else 'all',
                'status': 'RUNNING'
            }
            
            # Check if process started successfully
            time.sleep(0.5)
            if process.poll() is not None:
                # Process ended immediately, probably an error
                stderr = process.stderr.read().decode('utf-8')
                stdout = process.stdout.read().decode('utf-8')
                logger.error(f"Sync process ended immediately. Stdout: {stdout}, Stderr: {stderr}")
                active_sync_processes[sync_id]['status'] = 'ERROR'
                return jsonify({'error': f'Sync failed to start: {stderr or stdout}'}), 500
            
            message = f"Started WordPress sync for {len(provider_ids) if provider_ids else 'all'} providers"
        else:
            # For dry run, execute synchronously
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=script_dir)
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
        # Use our new process tracking instead of ps grep
        is_running, running_processes = get_sync_running_status()
        
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
        
        # Get details about running processes
        active_sync_info = []
        for process_info in running_processes:
            active_sync_info.append({
                'started_at': process_info['started_at'],
                'provider_count': process_info['provider_count'],
                'status': process_info['status']
            })

        return jsonify({
            'sync_running': is_running,
            'active_syncs': active_sync_info,
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

def get_wordpress_credentials():
    """Get WordPress credentials from environment"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
    load_dotenv(config_path)
    
    return {
        'url': os.getenv('WORDPRESS_URL', 'https://care-compass.jp'),
        'username': os.getenv('WORDPRESS_USERNAME'),
        'password': os.getenv('WORDPRESS_APPLICATION_PASSWORD')
    }

def get_all_wordpress_posts():
    """Fetch all healthcare provider posts from WordPress"""
    wp_creds = get_wordpress_credentials()
    if not all([wp_creds['url'], wp_creds['username'], wp_creds['password']]):
        raise ValueError("Missing WordPress credentials")
    
    session = requests.Session()
    session.auth = (wp_creds['username'], wp_creds['password'])
    
    all_posts = []
    page = 1
    per_page = 100
    
    while True:
        try:
            response = session.get(
                f"{wp_creds['url']}/wp-json/wp/v2/healthcare_provider",
                params={
                    'per_page': per_page,
                    'page': page,
                    'status': 'any'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                posts = response.json()
                if not posts:
                    break
                all_posts.extend(posts)
                page += 1
            else:
                break
                
        except Exception:
            break
    
    return all_posts

@sync_bp.route('/duplicates/scan', methods=['GET'])
def scan_wordpress_duplicates():
    """Scan for duplicate WordPress posts"""
    try:
        logger.info("Scanning for WordPress duplicates...")
        
        # Get all WordPress posts
        all_posts = get_all_wordpress_posts()
        if not all_posts:
            return jsonify({
                'success': True,
                'duplicates': [],
                'total_posts': 0,
                'message': 'No WordPress posts found'
            }), 200
        
        # Group posts by normalized title
        title_groups = defaultdict(list)
        for post in all_posts:
            title = post['title']['rendered'].strip().lower()
            title_groups[title].append(post)
        
        # Find duplicates
        duplicate_groups = []
        session = Session()
        
        try:
            for title, post_group in title_groups.items():
                if len(post_group) > 1:
                    # Sort by modification date (newest first)
                    sorted_posts = sorted(post_group, key=lambda p: p['modified'], reverse=True)
                    
                    # Analyze each post in the group
                    analyzed_posts = []
                    for post in sorted_posts:
                        # Check database reference
                        db_provider = session.execute(text('''
                            SELECT id, provider_name, status
                            FROM providers 
                            WHERE wordpress_post_id = :wp_id
                        '''), {'wp_id': post['id']}).fetchone()
                        
                        # Extract slug from link or use slug field
                        slug = post.get('slug', '')
                        if not slug and post.get('link'):
                            # Extract slug from URL (last part before trailing slash)
                            slug = post['link'].rstrip('/').split('/')[-1]
                        
                        # Check if slug has numbered suffix (e.g., -2, -3, etc.)
                        has_numbered_suffix = bool(slug and slug.split('-')[-1].isdigit())
                        
                        post_info = {
                            'wp_id': post['id'],
                            'title': post['title']['rendered'],
                            'status': post['status'],
                            'modified': post['modified'],
                            'link': post['link'],
                            'slug': slug,
                            'has_numbered_suffix': has_numbered_suffix,
                            'content_length': len(post['content']['rendered']),
                            'has_featured_image': post.get('featured_media', 0) > 0,
                            'db_provider_id': db_provider.id if db_provider else None,
                            'db_provider_name': db_provider.provider_name if db_provider else None,
                            'db_status': db_provider.status if db_provider else None
                        }
                        analyzed_posts.append(post_info)
                    
                    # Determine recommended actions with updated priority:
                    # 1. Original slug (no numbered suffix) + DB reference + published
                    # 2. Original slug (no numbered suffix) + published
                    # 3. Original slug (no numbered suffix) + DB reference
                    # 4. Original slug (no numbered suffix)
                    # 5. DB reference + published (old logic)
                    # 6. DB reference (old logic)
                    # 7. Newest overall (old logic)
                    
                    keep_post = None
                    
                    # Priority 1: Original slug + DB reference + published
                    for post_info in analyzed_posts:
                        if (not post_info['has_numbered_suffix'] and 
                            post_info['db_provider_id'] and 
                            post_info['status'] == 'publish'):
                            keep_post = post_info
                            break
                    
                    # Priority 2: Original slug + published
                    if not keep_post:
                        for post_info in analyzed_posts:
                            if (not post_info['has_numbered_suffix'] and 
                                post_info['status'] == 'publish'):
                                keep_post = post_info
                                break
                    
                    # Priority 3: Original slug + DB reference
                    if not keep_post:
                        for post_info in analyzed_posts:
                            if (not post_info['has_numbered_suffix'] and 
                                post_info['db_provider_id']):
                                keep_post = post_info
                                break
                    
                    # Priority 4: Original slug (any status)
                    if not keep_post:
                        for post_info in analyzed_posts:
                            if not post_info['has_numbered_suffix']:
                                keep_post = post_info
                                break
                    
                    # Priority 5: DB reference + published (fallback to old logic)
                    if not keep_post:
                        for post_info in analyzed_posts:
                            if post_info['db_provider_id'] and post_info['status'] == 'publish':
                                keep_post = post_info
                                break
                    
                    # Priority 6: DB reference (fallback to old logic)
                    if not keep_post:
                        for post_info in analyzed_posts:
                            if post_info['db_provider_id']:
                                keep_post = post_info
                                break
                    
                    # Priority 7: Newest overall (final fallback)
                    if not keep_post:
                        keep_post = analyzed_posts[0]
                    
                    duplicate_group = {
                        'title': post_group[0]['title']['rendered'],
                        'total_posts': len(analyzed_posts),
                        'posts': analyzed_posts,
                        'recommended_keep': keep_post['wp_id'],
                        'recommended_delete': [p['wp_id'] for p in analyzed_posts if p['wp_id'] != keep_post['wp_id']]
                    }
                    duplicate_groups.append(duplicate_group)
                    
        finally:
            session.close()
        
        return jsonify({
            'success': True,
            'duplicates': duplicate_groups,
            'total_posts': len(all_posts),
            'duplicate_groups': len(duplicate_groups),
            'total_duplicates': sum(len(group['recommended_delete']) for group in duplicate_groups)
        }), 200
        
    except Exception as e:
        logger.error(f"Error scanning for duplicates: {str(e)}")
        return jsonify({'error': str(e)}), 500

@sync_bp.route('/duplicates/cleanup', methods=['POST'])
def cleanup_wordpress_duplicates():
    """Clean up WordPress duplicate posts"""
    try:
        data = request.json or {}
        wp_ids_to_delete = data.get('wp_ids_to_delete', [])
        dry_run = data.get('dry_run', False)
        
        if not wp_ids_to_delete:
            return jsonify({'error': 'No WordPress post IDs provided for deletion'}), 400
        
        wp_creds = get_wordpress_credentials()
        if not all([wp_creds['url'], wp_creds['username'], wp_creds['password']]):
            return jsonify({'error': 'Missing WordPress credentials'}), 500
        
        wp_session = requests.Session()
        wp_session.auth = (wp_creds['username'], wp_creds['password'])
        
        results = []
        session = Session()
        
        try:
            for wp_id in wp_ids_to_delete:
                result = {
                    'wp_id': wp_id,
                    'success': False,
                    'message': '',
                    'db_updated': False
                }
                
                if dry_run:
                    result['success'] = True
                    result['message'] = f'DRY RUN: Would delete post {wp_id}'
                else:
                    try:
                        # Delete from WordPress
                        response = wp_session.delete(
                            f"{wp_creds['url']}/wp-json/wp/v2/healthcare_provider/{wp_id}",
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result['success'] = True
                            result['message'] = f'Successfully deleted WordPress post {wp_id}'
                            
                            # Update database - remove wordpress_post_id reference
                            session.execute(text('''
                                UPDATE providers 
                                SET wordpress_post_id = NULL, wordpress_status = 'deleted'
                                WHERE wordpress_post_id = :wp_id
                            '''), {'wp_id': wp_id})
                            result['db_updated'] = True
                            
                        else:
                            result['message'] = f'Failed to delete post {wp_id}: HTTP {response.status_code}'
                            
                    except Exception as e:
                        result['message'] = f'Error deleting post {wp_id}: {str(e)}'
                
                results.append(result)
            
            if not dry_run:
                session.commit()
                
        except Exception as e:
            if not dry_run:
                session.rollback()
            raise e
        finally:
            session.close()
        
        successful_deletions = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(wp_ids_to_delete),
            'successful_deletions': successful_deletions,
            'failed_deletions': len(wp_ids_to_delete) - successful_deletions,
            'dry_run': dry_run
        }), 200
        
    except Exception as e:
        logger.error(f"Error cleaning up duplicates: {str(e)}")
        return jsonify({'error': str(e)}), 500