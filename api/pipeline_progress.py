"""
Pipeline Progress API Blueprint
Handles real-time pipeline progress tracking and status updates
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
import logging
from datetime import datetime, timedelta
from postgres_integration import Provider, get_postgres_config
from pipeline_tracker import PipelineTracker

logger = logging.getLogger(__name__)

pipeline_progress_bp = Blueprint('pipeline_progress', __name__)

# Database setup
config = get_postgres_config()
engine = create_engine(
    f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
)
Session = sessionmaker(bind=engine)

@pipeline_progress_bp.route('/status/<run_id>', methods=['GET'])
def get_pipeline_status(run_id):
    """Get current status of a pipeline run"""
    try:
        session = Session()
        
        # Query pipeline run details
        run_query = text("""
            SELECT pr.*, 
                   COUNT(DISTINCT ps.provider_id) as total_providers,
                   COUNT(DISTINCT CASE WHEN ps.status = 'success' THEN ps.provider_id END) as completed_providers,
                   COUNT(DISTINCT CASE WHEN ps.status = 'failed' THEN ps.provider_id END) as failed_providers
            FROM pipeline_runs pr
            LEFT JOIN pipeline_steps ps ON pr.id = ps.run_id
            WHERE pr.id = :run_id
            GROUP BY pr.id
        """)
        
        result = session.execute(run_query, {'run_id': run_id}).fetchone()
        
        if not result:
            session.close()
            return jsonify({'error': 'Pipeline run not found'}), 404
        
        # Get current step details
        step_query = text("""
            SELECT step_name, status, COUNT(*) as count
            FROM pipeline_steps
            WHERE run_id = :run_id
            GROUP BY step_name, status
            ORDER BY step_name, status
        """)
        
        step_results = session.execute(step_query, {'run_id': run_id}).fetchall()
        
        # Calculate progress
        total_steps = result.total_providers * 4  # 4 steps per provider
        completed_steps = 0
        
        steps_breakdown = {}
        for step in step_results:
            if step.step_name not in steps_breakdown:
                steps_breakdown[step.step_name] = {'success': 0, 'failed': 0, 'pending': 0}
            steps_breakdown[step.step_name][step.status] = step.count
            if step.status == 'success':
                completed_steps += step.count
        
        progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        # Get recent activity
        activity_query = text("""
            SELECT ps.*, p.provider_name
            FROM pipeline_steps ps
            JOIN providers p ON ps.provider_id = p.id
            WHERE ps.run_id = :run_id
            ORDER BY ps.created_at DESC
            LIMIT 10
        """)
        
        recent_activities = []
        for activity in session.execute(activity_query, {'run_id': run_id}):
            recent_activities.append({
                'provider_name': activity.provider_name,
                'step_name': activity.step_name,
                'status': activity.status,
                'error_message': activity.error_message,
                'created_at': activity.created_at.isoformat() if activity.created_at else None
            })
        
        response = {
            'run_id': result.id,
            'run_type': result.run_type,
            'status': result.status,
            'started_at': result.started_at.isoformat() if result.started_at else None,
            'completed_at': result.completed_at.isoformat() if result.completed_at else None,
            'progress': {
                'percentage': round(progress_percentage, 1),
                'total_providers': result.total_providers,
                'completed_providers': result.completed_providers,
                'failed_providers': result.failed_providers,
                'steps_breakdown': steps_breakdown
            },
            'recent_activity': recent_activities
        }
        
        session.close()
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting pipeline status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_progress_bp.route('/active', methods=['GET'])
def get_active_pipelines():
    """Get all currently active pipeline runs"""
    try:
        session = Session()
        
        # Query active pipeline runs (not completed)
        query = text("""
            SELECT pr.*, 
                   COUNT(DISTINCT ps.provider_id) as total_providers,
                   COUNT(DISTINCT CASE WHEN ps.status = 'success' THEN ps.provider_id END) as completed_providers
            FROM pipeline_runs pr
            LEFT JOIN pipeline_steps ps ON pr.id = ps.run_id
            WHERE pr.status IN ('running', 'pending')
            GROUP BY pr.id
            ORDER BY pr.started_at DESC
        """)
        
        results = session.execute(query).fetchall()
        
        active_runs = []
        for run in results:
            progress = (run.completed_providers / run.total_providers * 100) if run.total_providers > 0 else 0
            active_runs.append({
                'run_id': run.id,
                'run_type': run.run_type,
                'status': run.status,
                'started_at': run.started_at.isoformat() if run.started_at else None,
                'total_providers': run.total_providers,
                'completed_providers': run.completed_providers,
                'progress_percentage': round(progress, 1)
            })
        
        session.close()
        return jsonify({'active_runs': active_runs}), 200
        
    except Exception as e:
        logger.error(f"Error getting active pipelines: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_progress_bp.route('/summary', methods=['GET'])
def get_pipeline_summary():
    """Get summary of recent pipeline runs"""
    try:
        session = Session()
        
        # Get recent runs summary
        summary_query = text("""
            SELECT 
                COUNT(*) as total_runs,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_runs,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_runs,
                COUNT(CASE WHEN status = 'running' THEN 1 END) as active_runs,
                AVG(CASE 
                    WHEN status = 'completed' AND completed_at IS NOT NULL 
                    THEN EXTRACT(EPOCH FROM (completed_at - started_at))/60 
                END) as avg_duration_minutes
            FROM pipeline_runs
            WHERE started_at > NOW() - INTERVAL '7 days'
        """)
        
        summary = session.execute(summary_query).fetchone()
        
        # Get failure statistics
        failure_query = text("""
            SELECT step_name, failure_reason, COUNT(*) as count
            FROM pipeline_failures
            WHERE created_at > NOW() - INTERVAL '7 days' AND resolved = false
            GROUP BY step_name, failure_reason
            ORDER BY count DESC
            LIMIT 10
        """)
        
        top_failures = []
        for failure in session.execute(failure_query):
            top_failures.append({
                'step_name': failure.step_name,
                'failure_reason': failure.failure_reason,
                'count': failure.count
            })
        
        response = {
            'summary': {
                'total_runs': summary.total_runs or 0,
                'completed_runs': summary.completed_runs or 0,
                'failed_runs': summary.failed_runs or 0,
                'active_runs': summary.active_runs or 0,
                'avg_duration_minutes': round(summary.avg_duration_minutes or 0, 1)
            },
            'top_failures': top_failures
        }
        
        session.close()
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting pipeline summary: {str(e)}")
        return jsonify({'error': str(e)}), 500