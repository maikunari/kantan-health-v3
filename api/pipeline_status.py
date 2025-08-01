"""
Pipeline Status API Blueprint
Handles pipeline failure tracking, retry mechanisms, and status reporting
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import subprocess
import json
import logging
import os
from datetime import datetime, timedelta
from postgres_integration import Provider, get_postgres_config
from pipeline_tracker import PipelineTracker
from activity_logger import activity_logger

logger = logging.getLogger(__name__)

pipeline_bp = Blueprint('pipeline', __name__)

# Database setup
config = get_postgres_config()
engine = create_engine(
    f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
)
Session = sessionmaker(bind=engine)

@pipeline_bp.route('/failures', methods=['GET'])
def get_pipeline_failures():
    """Get all unresolved pipeline failures"""
    try:
        session = Session()
        
        # Get query parameters
        step = request.args.get('step')
        failure_reason = request.args.get('failure_reason')
        limit = int(request.args.get('limit', 100))
        
        # Build query
        query = """
            SELECT pf.*, p.provider_name as current_provider_name,
                   p.status as current_status,
                   p.ai_description IS NOT NULL as has_ai_description,
                   p.seo_title IS NOT NULL as has_seo_title,
                   p.latitude IS NOT NULL as has_location
            FROM pipeline_failures pf
            LEFT JOIN providers p ON pf.provider_id = p.id
            WHERE pf.resolved = FALSE
        """
        params = {}
        
        if step:
            query += " AND pf.step = :step"
            params['step'] = step
        
        if failure_reason:
            query += " AND pf.failure_reason = :failure_reason"
            params['failure_reason'] = failure_reason
        
        query += " ORDER BY pf.created_at DESC LIMIT :limit"
        params['limit'] = limit
        
        result = session.execute(text(query), params)
        
        failures = []
        for row in result:
            failures.append({
                'id': row.id,
                'provider_id': row.provider_id,
                'provider_name': row.provider_name,
                'current_provider_name': row.current_provider_name,
                'current_status': row.current_status,
                'step': row.step,
                'failure_reason': row.failure_reason,
                'error_details': row.error_details,
                'retry_count': row.retry_count,
                'created_at': row.created_at.isoformat() if row.created_at else None,
                'has_ai_description': bool(row.has_ai_description),
                'has_seo_title': bool(row.has_seo_title),
                'has_location': bool(row.has_location)
            })
        
        session.close()
        
        return jsonify({
            'success': True,
            'failures': failures,
            'total': len(failures)
        })
        
    except Exception as e:
        logger.error(f"Error getting pipeline failures: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/failures/summary', methods=['GET'])
def get_failure_summary():
    """Get summary statistics of pipeline failures"""
    try:
        session = Session()
        
        # Get failure breakdown by step and reason
        result = session.execute(text("""
            SELECT 
                step,
                failure_reason,
                COUNT(*) as count,
                COUNT(CASE WHEN resolved = TRUE THEN 1 END) as resolved_count,
                MAX(created_at) as latest_failure
            FROM pipeline_failures
            WHERE created_at > NOW() - INTERVAL '7 days'
            GROUP BY step, failure_reason
            ORDER BY count DESC
        """))
        
        breakdown = []
        total_failures = 0
        total_resolved = 0
        
        for row in result:
            breakdown.append({
                'step': row.step,
                'failure_reason': row.failure_reason,
                'count': row.count,
                'resolved_count': row.resolved_count,
                'unresolved_count': row.count - row.resolved_count,
                'latest_failure': row.latest_failure.isoformat() if row.latest_failure else None
            })
            total_failures += row.count
            total_resolved += row.resolved_count
        
        # Get pipeline run statistics
        run_stats = session.execute(text("""
            SELECT 
                run_type,
                COUNT(*) as total_runs,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_runs,
                AVG(successful_providers) as avg_successful,
                AVG(failed_providers) as avg_failed
            FROM pipeline_runs
            WHERE started_at > NOW() - INTERVAL '7 days'
            GROUP BY run_type
            ORDER BY total_runs DESC
        """)).fetchall()
        
        run_statistics = []
        for row in run_stats:
            run_statistics.append({
                'run_type': row.run_type,
                'total_runs': row.total_runs,
                'completed_runs': row.completed_runs,
                'success_rate': round((row.completed_runs / row.total_runs * 100), 1) if row.total_runs > 0 else 0,
                'avg_successful': round(float(row.avg_successful or 0), 1),
                'avg_failed': round(float(row.avg_failed or 0), 1)
            })
        
        session.close()
        
        return jsonify({
            'success': True,
            'summary': {
                'total_failures_7d': total_failures,
                'total_resolved_7d': total_resolved,
                'total_unresolved_7d': total_failures - total_resolved,
                'resolution_rate': round((total_resolved / total_failures * 100), 1) if total_failures > 0 else 100
            },
            'failure_breakdown': breakdown,
            'run_statistics': run_statistics
        })
        
    except Exception as e:
        logger.error(f"Error getting failure summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/failures/<int:failure_id>/retry', methods=['POST'])
def retry_single_failure(failure_id):
    """Retry a specific pipeline failure"""
    try:
        session = Session()
        
        # Get failure details
        failure = session.execute(text("""
            SELECT pf.*, p.provider_name as current_provider_name
            FROM pipeline_failures pf
            LEFT JOIN providers p ON pf.provider_id = p.id
            WHERE pf.id = :failure_id AND pf.resolved = FALSE
        """), {'failure_id': failure_id}).fetchone()
        
        if not failure:
            return jsonify({'error': 'Failure not found or already resolved'}), 404
        
        session.close()
        
        # Increment retry count
        session = Session()
        session.execute(text("""
            UPDATE pipeline_failures 
            SET retry_count = retry_count + 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = :failure_id
        """), {'failure_id': failure_id})
        session.commit()
        session.close()
        
        # Execute retry using the enhanced automation script
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'run_enhanced_automation.py')
        cmd = [
            'python3', script_path,
            '--provider-ids', str(failure.provider_id),
            '--run-type', 'retry',
            '--max-retries', '1'
        ]
        
        logger.info(f"Retrying failure {failure_id}: {' '.join(cmd)}")
        
        # Run in background
        process = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=os.path.dirname(os.path.dirname(__file__)))
        
        # Log the retry activity
        activity_logger.log_activity(
            activity_type='retry_pipeline_failure',
            activity_category='pipeline',
            description=f'Retrying {failure.step} for {failure.current_provider_name or failure.provider_name}',
            provider_id=failure.provider_id,
            provider_name=failure.current_provider_name or failure.provider_name,
            details={
                'failure_id': failure_id,
                'step': failure.step,
                'failure_reason': failure.failure_reason,
                'retry_count': failure.retry_count + 1
            },
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': f'Retry initiated for {failure.step} step',
            'failure_id': failure_id,
            'provider_id': failure.provider_id,
            'process_id': process.pid
        })
        
    except Exception as e:
        logger.error(f"Error retrying failure {failure_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/failures/bulk-retry', methods=['POST'])
def bulk_retry_failures():
    """Retry multiple failures of the same type"""
    try:
        data = request.json or {}
        step = data.get('step')
        failure_reason = data.get('failure_reason')
        failure_ids = data.get('failure_ids', [])
        limit = data.get('limit', 10)
        
        if not any([step, failure_reason, failure_ids]):
            return jsonify({'error': 'Must provide step, failure_reason, or failure_ids'}), 400
        
        session = Session()
        
        # Build query to get failures to retry
        if failure_ids:
            query = """
                SELECT DISTINCT pf.provider_id, p.provider_name
                FROM pipeline_failures pf
                LEFT JOIN providers p ON pf.provider_id = p.id
                WHERE pf.id = ANY(:failure_ids) AND pf.resolved = FALSE
            """
            result = session.execute(text(query), {'failure_ids': failure_ids})
        else:
            query = """
                SELECT DISTINCT pf.provider_id, p.provider_name
                FROM pipeline_failures pf
                LEFT JOIN providers p ON pf.provider_id = p.id
                WHERE pf.resolved = FALSE
            """
            params = {}
            
            if step:
                query += " AND pf.step = :step"
                params['step'] = step
            
            if failure_reason:
                query += " AND pf.failure_reason = :failure_reason"
                params['failure_reason'] = failure_reason
            
            query += " LIMIT :limit"
            params['limit'] = limit
            
            result = session.execute(text(query), params)
        
        providers_to_retry = result.fetchall()
        session.close()
        
        if not providers_to_retry:
            return jsonify({'error': 'No matching failures found'}), 404
        
        # Update retry counts
        if failure_ids:
            session = Session()
            session.execute(text("""
                UPDATE pipeline_failures 
                SET retry_count = retry_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ANY(:failure_ids)
            """), {'failure_ids': failure_ids})
            session.commit()
            session.close()
        
        # Execute bulk retry
        provider_ids = [str(p.provider_id) for p in providers_to_retry]
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'run_enhanced_automation.py')
        cmd = [
            'python3', script_path,
            '--provider-ids'] + provider_ids + [
            '--run-type', 'bulk_retry',
            '--max-retries', '1'
        ]
        
        logger.info(f"Bulk retry for {len(provider_ids)} providers: {' '.join(cmd)}")
        
        # Run in background
        process = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=os.path.dirname(os.path.dirname(__file__)))
        
        # Log the bulk retry activity
        activity_logger.log_activity(
            activity_type='bulk_retry_pipeline_failures',
            activity_category='pipeline',
            description=f'Bulk retry initiated for {len(provider_ids)} providers',
            details={
                'provider_count': len(provider_ids),
                'step': step,
                'failure_reason': failure_reason,
                'provider_ids': provider_ids
            },
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': f'Bulk retry initiated for {len(provider_ids)} providers',
            'provider_count': len(provider_ids),
            'process_id': process.pid
        })
        
    except Exception as e:
        logger.error(f"Error in bulk retry: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/runs', methods=['GET'])
def get_pipeline_runs():
    """Get recent pipeline runs"""
    try:
        session = Session()
        
        limit = int(request.args.get('limit', 20))
        
        result = session.execute(text("""
            SELECT *
            FROM pipeline_runs
            ORDER BY started_at DESC
            LIMIT :limit
        """), {'limit': limit})
        
        runs = []
        for row in result:
            runs.append({
                'id': row.id,
                'run_type': row.run_type,
                'total_providers': row.total_providers,
                'successful_providers': row.successful_providers,
                'failed_providers': row.failed_providers,
                'status': row.status,
                'started_at': row.started_at.isoformat() if row.started_at else None,
                'completed_at': row.completed_at.isoformat() if row.completed_at else None,
                'metadata': row.metadata
            })
        
        session.close()
        
        return jsonify({
            'success': True,
            'runs': runs
        })
        
    except Exception as e:
        logger.error(f"Error getting pipeline runs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/providers/missing-fields', methods=['GET'])
def get_providers_missing_fields():
    """Get providers with missing required fields"""
    try:
        session = Session()
        
        limit = int(request.args.get('limit', 50))
        
        # Get providers with missing essential fields
        result = session.execute(text("""
            SELECT 
                id,
                provider_name,
                status,
                ai_description IS NULL as missing_ai_description,
                seo_title IS NULL as missing_seo_title,
                selected_featured_image IS NULL OR selected_featured_image = '' as missing_featured_image,
                latitude IS NULL as missing_latitude,
                business_hours IS NULL as missing_business_hours,
                rating IS NULL as missing_rating,
                created_at
            FROM providers
            WHERE (
                ai_description IS NULL OR
                seo_title IS NULL OR
                selected_featured_image IS NULL OR
                selected_featured_image = '' OR
                latitude IS NULL OR
                business_hours IS NULL OR
                rating IS NULL
            )
            ORDER BY created_at DESC
            LIMIT :limit
        """), {'limit': limit})
        
        providers = []
        for row in result:
            missing_fields = []
            if row.missing_ai_description:
                missing_fields.append('ai_description')
            if row.missing_seo_title:
                missing_fields.append('seo_title')
            if row.missing_featured_image:
                missing_fields.append('featured_image')
            if row.missing_latitude:
                missing_fields.append('location')
            if row.missing_business_hours:
                missing_fields.append('business_hours')
            if row.missing_rating:
                missing_fields.append('rating')
            
            providers.append({
                'id': row.id,
                'provider_name': row.provider_name,
                'status': row.status,
                'missing_fields': missing_fields,
                'missing_count': len(missing_fields),
                'created_at': row.created_at.isoformat() if row.created_at else None
            })
        
        session.close()
        
        return jsonify({
            'success': True,
            'providers': providers,
            'total': len(providers)
        })
        
    except Exception as e:
        logger.error(f"Error getting providers with missing fields: {str(e)}")
        return jsonify({'error': str(e)}), 500