#!/usr/bin/env python3
"""
Activity Logger Service
Centralized logging service for tracking all system operations
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from ..core.database import get_postgres_config

logger = logging.getLogger(__name__)

class ActivityLogger:
    """Service for logging all system activities to the database"""
    
    def __init__(self):
        config = get_postgres_config()
        self.engine = create_engine(
            f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}",
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.Session = sessionmaker(bind=self.engine)
    
    def log_activity(
        self,
        activity_type: str,
        activity_category: str,
        description: str,
        provider_id: Optional[int] = None,
        provider_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: Optional[str] = 'success',
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """Log a single activity to the database"""
        session = None
        try:
            session = self.Session()
            session.execute(text("""
                INSERT INTO activity_log (
                    activity_type, activity_category, description,
                    provider_id, provider_name, details, status,
                    duration_ms, error_message, user_id, created_at
                ) VALUES (
                    :activity_type, :activity_category, :description,
                    :provider_id, :provider_name, :details::jsonb, :status,
                    :duration_ms, :error_message, :user_id, :created_at
                )
            """), {
                'activity_type': activity_type,
                'activity_category': activity_category,
                'description': description,
                'provider_id': provider_id,
                'provider_name': provider_name,
                'details': json.dumps(details) if details else None,
                'status': status,
                'duration_ms': duration_ms,
                'error_message': error_message,
                'user_id': user_id,
                'created_at': datetime.now()
            })
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()
    
    def log_provider_creation(
        self,
        provider_name: str,
        provider_id: Optional[int] = None,
        method: str = 'manual',
        details: Optional[Dict[str, Any]] = None,
        status: str = 'success',
        error_message: Optional[str] = None
    ) -> bool:
        """Log provider creation activity"""
        return self.log_activity(
            activity_type='provider_creation',
            activity_category='data_collection',
            description=f"Added provider: {provider_name}",
            provider_id=provider_id,
            provider_name=provider_name,
            details={
                'method': method,
                **(details or {})
            },
            status=status,
            error_message=error_message
        )
    
    def log_content_generation(
        self,
        provider_name: str,
        provider_id: int,
        content_type: str = 'ai_description',
        batch_size: int = 1,
        processing_time_ms: Optional[int] = None,
        status: str = 'success',
        error_message: Optional[str] = None
    ) -> bool:
        """Log AI content generation activity"""
        return self.log_activity(
            activity_type='content_generation',
            activity_category='ai_processing',
            description=f"Generated {content_type} for {provider_name}",
            provider_id=provider_id,
            provider_name=provider_name,
            details={
                'content_type': content_type,
                'batch_size': batch_size
            },
            status=status,
            duration_ms=processing_time_ms,
            error_message=error_message
        )
    
    def log_wordpress_sync(
        self,
        provider_name: str,
        provider_id: int,
        wordpress_id: Optional[int] = None,
        sync_type: str = 'create',  # create, update, delete
        fields_synced: Optional[List[str]] = None,
        processing_time_ms: Optional[int] = None,
        status: str = 'success',
        error_message: Optional[str] = None
    ) -> bool:
        """Log WordPress synchronization activity"""
        return self.log_activity(
            activity_type='wordpress_sync',
            activity_category='publishing',
            description=f"WordPress {sync_type} for {provider_name}",
            provider_id=provider_id,
            provider_name=provider_name,
            details={
                'wordpress_id': wordpress_id,
                'sync_type': sync_type,
                'fields_synced': fields_synced
            },
            status=status,
            duration_ms=processing_time_ms,
            error_message=error_message
        )
    
    def log_pipeline_run(
        self,
        run_id: str,
        pipeline_mode: str,
        providers_processed: int,
        duration_ms: int,
        details: Optional[Dict[str, Any]] = None,
        status: str = 'success',
        error_message: Optional[str] = None
    ) -> bool:
        """Log pipeline execution activity"""
        return self.log_activity(
            activity_type='pipeline_run',
            activity_category='automation',
            description=f"Pipeline run ({pipeline_mode}): {providers_processed} providers",
            details={
                'run_id': run_id,
                'pipeline_mode': pipeline_mode,
                'providers_processed': providers_processed,
                **(details or {})
            },
            status=status,
            duration_ms=duration_ms,
            error_message=error_message
        )
    
    def get_recent_activities(
        self,
        limit: int = 100,
        activity_type: Optional[str] = None,
        provider_id: Optional[int] = None,
        status: Optional[str] = None,
        hours_ago: int = 24
    ) -> List[Dict[str, Any]]:
        """Retrieve recent activities from the log"""
        session = None
        try:
            session = self.Session()
            
            # Build query with filters
            query = """
                SELECT 
                    id, activity_type, activity_category, description,
                    provider_id, provider_name, details, status,
                    duration_ms, error_message, user_id, created_at
                FROM activity_log
                WHERE created_at >= NOW() - INTERVAL :hours_ago HOUR
            """
            
            params = {'hours_ago': hours_ago}
            
            if activity_type:
                query += " AND activity_type = :activity_type"
                params['activity_type'] = activity_type
            
            if provider_id:
                query += " AND provider_id = :provider_id"
                params['provider_id'] = provider_id
            
            if status:
                query += " AND status = :status"
                params['status'] = status
            
            query += " ORDER BY created_at DESC LIMIT :limit"
            params['limit'] = limit
            
            result = session.execute(text(query), params)
            
            activities = []
            for row in result:
                activities.append({
                    'id': row.id,
                    'activity_type': row.activity_type,
                    'activity_category': row.activity_category,
                    'description': row.description,
                    'provider_id': row.provider_id,
                    'provider_name': row.provider_name,
                    'details': row.details,
                    'status': row.status,
                    'duration_ms': row.duration_ms,
                    'error_message': row.error_message,
                    'user_id': row.user_id,
                    'created_at': row.created_at.isoformat() if row.created_at else None
                })
            
            return activities
            
        except Exception as e:
            logger.error(f"Error retrieving activities: {str(e)}")
            return []
        finally:
            if session:
                session.close()
    
    def get_activity_summary(
        self,
        hours_ago: int = 24
    ) -> Dict[str, Any]:
        """Get summary statistics of recent activities"""
        session = None
        try:
            session = self.Session()
            
            result = session.execute(text("""
                SELECT 
                    activity_type,
                    activity_category,
                    status,
                    COUNT(*) as count,
                    AVG(duration_ms) as avg_duration_ms
                FROM activity_log
                WHERE created_at >= NOW() - INTERVAL :hours_ago HOUR
                GROUP BY activity_type, activity_category, status
                ORDER BY count DESC
            """), {'hours_ago': hours_ago})
            
            summary = {
                'total_activities': 0,
                'by_type': {},
                'by_category': {},
                'by_status': {},
                'recent_errors': []
            }
            
            for row in result:
                summary['total_activities'] += row.count
                
                # By type
                if row.activity_type not in summary['by_type']:
                    summary['by_type'][row.activity_type] = 0
                summary['by_type'][row.activity_type] += row.count
                
                # By category
                if row.activity_category not in summary['by_category']:
                    summary['by_category'][row.activity_category] = 0
                summary['by_category'][row.activity_category] += row.count
                
                # By status
                if row.status not in summary['by_status']:
                    summary['by_status'][row.status] = 0
                summary['by_status'][row.status] += row.count
            
            # Get recent errors
            errors = self.get_recent_activities(
                limit=10,
                status='error',
                hours_ago=hours_ago
            )
            summary['recent_errors'] = errors
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting activity summary: {str(e)}")
            return {
                'total_activities': 0,
                'by_type': {},
                'by_category': {},
                'by_status': {},
                'recent_errors': []
            }
        finally:
            if session:
                session.close()