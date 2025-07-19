"""
Dashboard API Blueprint
Provides metrics, statistics, and system overview data
"""

from flask import Blueprint, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
import logging
from postgres_integration import get_postgres_config

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

# Database setup
config = get_postgres_config()
engine = create_engine(
    f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
)
Session = sessionmaker(bind=engine)

@dashboard_bp.route('/overview', methods=['GET'])
def get_overview():
    """Get system overview and key metrics"""
    try:
        session = Session()
        
        # Provider counts
        provider_stats = session.execute(text("""
            SELECT 
                COUNT(*) as total_providers,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected,
                COUNT(CASE WHEN wordpress_id IS NOT NULL THEN 1 END) as synced_to_wordpress,
                COUNT(CASE WHEN ai_description IS NOT NULL THEN 1 END) as with_ai_content
            FROM providers
        """)).fetchone()
        
        # Recent activity (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_activity = session.execute(text("""
            SELECT 
                COUNT(CASE WHEN created_at > :yesterday THEN 1 END) as new_providers,
                COUNT(CASE WHEN last_synced > :yesterday THEN 1 END) as recent_syncs
            FROM providers
        """), {'yesterday': yesterday}).fetchone()
        
        # API usage metrics
        api_metrics = session.execute(text("""
            SELECT 
                metric_type,
                SUM(value) as total,
                COUNT(*) as count
            FROM metrics
            WHERE timestamp > :yesterday
            GROUP BY metric_type
        """), {'yesterday': yesterday.isoformat()}).fetchall()
        
        # Content generation progress
        content_progress = session.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN ai_description IS NOT NULL 
                           AND ai_english_experience IS NOT NULL 
                           AND ai_review_summary IS NOT NULL 
                           AND seo_title IS NOT NULL THEN 1 END) as fully_processed
            FROM providers
            WHERE status = 'approved'
        """)).fetchone()
        
        session.close()
        
        return jsonify({
            'providers': {
                'total': provider_stats[0],
                'approved': provider_stats[1],
                'pending': provider_stats[2],
                'rejected': provider_stats[3],
                'synced_to_wordpress': provider_stats[4],
                'with_ai_content': provider_stats[5]
            },
            'recent_activity': {
                'new_providers_24h': recent_activity[0],
                'recent_syncs_24h': recent_activity[1]
            },
            'api_usage': {row[0]: {'total': row[1], 'count': row[2]} 
                         for row in api_metrics},
            'content_generation': {
                'total_approved': content_progress[0],
                'fully_processed': content_progress[1],
                'completion_rate': round(content_progress[1] / content_progress[0] * 100, 2) 
                                  if content_progress[0] > 0 else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching dashboard overview: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/metrics/timeline', methods=['GET'])
def get_metrics_timeline():
    """Get metrics over time for charts"""
    try:
        session = Session()
        
        # Get daily provider additions for last 30 days
        daily_additions = session.execute(text("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count
            FROM providers
            WHERE created_at > CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """)).fetchall()
        
        # Get daily API usage
        daily_api_usage = session.execute(text("""
            SELECT 
                DATE(timestamp) as date,
                metric_type,
                SUM(value) as total
            FROM metrics
            WHERE timestamp > (CURRENT_DATE - INTERVAL '30 days')::text
            GROUP BY DATE(timestamp), metric_type
            ORDER BY date
        """)).fetchall()
        
        # Get sync operations timeline
        sync_timeline = session.execute(text("""
            SELECT 
                DATE(timestamp) as date,
                operation_type,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count
            FROM wordpress_sync_operations
            WHERE timestamp > CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(timestamp), operation_type
            ORDER BY date
        """)).fetchall()
        
        session.close()
        
        # Format timeline data
        provider_timeline = [{'date': row[0].isoformat(), 'count': row[1]} 
                           for row in daily_additions]
        
        api_timeline = {}
        for row in daily_api_usage:
            date = row[0].isoformat()
            if date not in api_timeline:
                api_timeline[date] = {}
            api_timeline[date][row[1]] = row[2]
        
        sync_data = []
        for row in sync_timeline:
            sync_data.append({
                'date': row[0].isoformat(),
                'operation': row[1],
                'total': row[2],
                'success': row[3]
            })
        
        return jsonify({
            'provider_additions': provider_timeline,
            'api_usage': api_timeline,
            'sync_operations': sync_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching metrics timeline: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/metrics/costs', methods=['GET'])
def get_cost_metrics():
    """Get API cost breakdown"""
    try:
        session = Session()
        
        # Get cost metrics from last 30 days
        cost_data = session.execute(text("""
            SELECT 
                metric_type,
                SUM(value) as total_calls,
                SUM((details->>'estimated_cost')::float) as total_cost
            FROM metrics
            WHERE metric_type IN ('google_places_api_calls', 'claude_api_calls')
                AND timestamp > (CURRENT_DATE - INTERVAL '30 days')::text
            GROUP BY metric_type
        """)).fetchall()
        
        # Get daily costs
        daily_costs = session.execute(text("""
            SELECT 
                DATE(timestamp) as date,
                SUM((details->>'estimated_cost')::float) as daily_cost
            FROM metrics
            WHERE details->>'estimated_cost' IS NOT NULL
                AND timestamp > (CURRENT_DATE - INTERVAL '30 days')::text
            GROUP BY DATE(timestamp)
            ORDER BY date
        """)).fetchall()
        
        session.close()
        
        return jsonify({
            'cost_breakdown': {
                row[0]: {
                    'calls': row[1],
                    'cost': round(row[2], 2) if row[2] else 0
                } for row in cost_data
            },
            'daily_costs': [
                {'date': row[0].isoformat(), 'cost': round(row[1], 2)}
                for row in daily_costs
            ],
            'total_cost_30d': sum(row[2] or 0 for row in cost_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching cost metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/system/health', methods=['GET'])
def get_system_health():
    """Check system health and connections"""
    try:
        health_status = {
            'database': 'unknown',
            'google_places_api': 'unknown',
            'claude_api': 'unknown',
            'wordpress_api': 'unknown'
        }
        
        # Check database
        try:
            session = Session()
            session.execute(text("SELECT 1"))
            session.close()
            health_status['database'] = 'healthy'
        except:
            health_status['database'] = 'error'
        
        # Check API keys exist
        if os.getenv('GOOGLE_PLACES_API_KEY'):
            health_status['google_places_api'] = 'configured'
        else:
            health_status['google_places_api'] = 'not_configured'
            
        if os.getenv('ANTHROPIC_API_KEY'):
            health_status['claude_api'] = 'configured'
        else:
            health_status['claude_api'] = 'not_configured'
            
        if os.getenv('WORDPRESS_URL') and os.getenv('WORDPRESS_APPLICATION_PASSWORD'):
            health_status['wordpress_api'] = 'configured'
        else:
            health_status['wordpress_api'] = 'not_configured'
        
        return jsonify({
            'status': 'healthy' if all(v in ['healthy', 'configured'] 
                                     for v in health_status.values()) else 'degraded',
            'components': health_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error checking system health: {str(e)}")
        return jsonify({'error': str(e)}), 500