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
from postgres_integration import get_postgres_config

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
                    duration_ms, error_message, user_id, timestamp
                ) VALUES (
                    :activity_type, :activity_category, :description,
                    :provider_id, :provider_name, :details, :status,
                    :duration_ms, :error_message, :user_id, CURRENT_TIMESTAMP
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
                'user_id': user_id
            })
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to log activity: {str(e)}")
            if session:
                session.rollback()
            return False
        finally:
            if session:
                session.close()
    
    def log_provider_creation(
        self,
        provider_name: str,
        provider_id: int,
        method: str,
        details: Optional[Dict[str, Any]] = None,
        status: str = 'success',
        error_message: Optional[str] = None
    ):
        """Log provider creation activity"""
        description = f"Provider '{provider_name}' created via {method}"
        if status != 'success':
            description = f"Failed to create provider '{provider_name}' via {method}"
        
        self.log_activity(
            activity_type='create',
            activity_category='provider_creation',
            description=description,
            provider_id=provider_id if status == 'success' else None,
            provider_name=provider_name,
            details=details,
            status=status,
            error_message=error_message
        )
    
    def log_content_generation(
        self,
        content_type: str,
        provider_ids: List[int],
        provider_names: List[str],
        batch_size: int,
        status: str = 'success',
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Log content generation activity"""
        if batch_size == 1:
            description = f"Generated {content_type} for {provider_names[0]}"
        else:
            description = f"Batch generated {content_type} for {batch_size} providers"
        
        self.log_activity(
            activity_type=f'generate_{content_type}',
            activity_category='content_generation',
            description=description,
            details={
                'content_type': content_type,
                'provider_ids': provider_ids,
                'provider_names': provider_names,
                'batch_size': batch_size
            },
            status=status,
            duration_ms=duration_ms,
            error_message=error_message
        )
    
    def log_data_quality_update(
        self,
        update_type: str,
        affected_count: int,
        details: Optional[Dict[str, Any]] = None,
        status: str = 'success',
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Log data quality update activity"""
        description = f"Updated {affected_count} providers with {update_type}"
        
        self.log_activity(
            activity_type=f'update_{update_type}',
            activity_category='data_quality',
            description=description,
            details={
                'update_type': update_type,
                'affected_count': affected_count,
                **(details or {})
            },
            status=status,
            duration_ms=duration_ms,
            error_message=error_message
        )
    
    def log_wordpress_sync(
        self,
        sync_type: str,
        provider_ids: List[int],
        provider_names: List[str],
        sync_count: int,
        status: str = 'success',
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log WordPress sync activity"""
        if sync_count == 1:
            description = f"WordPress {sync_type} for {provider_names[0] if provider_names else 'provider'}"
        else:
            description = f"WordPress {sync_type} for {sync_count} providers"
        
        self.log_activity(
            activity_type=f'wordpress_{sync_type}',
            activity_category='wordpress_sync',
            description=description,
            details={
                'sync_type': sync_type,
                'provider_ids': provider_ids,
                'provider_names': provider_names,
                'sync_count': sync_count,
                **(details or {})
            },
            status=status,
            duration_ms=duration_ms,
            error_message=error_message
        )
    
    def log_duplicate_cleanup(
        self,
        action: str,
        duplicate_count: int,
        details: Optional[Dict[str, Any]] = None,
        status: str = 'success',
        error_message: Optional[str] = None
    ):
        """Log WordPress duplicate cleanup activity"""
        if action == 'scan':
            description = f"Scanned for WordPress duplicates, found {duplicate_count} duplicate groups"
        else:
            description = f"Cleaned up {duplicate_count} WordPress duplicates"
        
        self.log_activity(
            activity_type=f'duplicate_{action}',
            activity_category='duplicate_cleanup',
            description=description,
            details={
                'action': action,
                'duplicate_count': duplicate_count,
                **(details or {})
            },
            status=status,
            error_message=error_message
        )
    
    def get_recent_activities(
        self,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get recent activities from the log"""
        session = None
        try:
            session = self.Session()
            
            query = """
                SELECT 
                    id, timestamp, activity_type, activity_category,
                    description, provider_id, provider_name, details,
                    status, duration_ms, error_message
                FROM activity_log
            """
            params = {}
            
            if category:
                query += " WHERE activity_category = :category"
                params['category'] = category
            
            query += " ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
            params['limit'] = limit
            params['offset'] = offset
            
            result = session.execute(text(query), params)
            activities = []
            
            for row in result:
                activity = {
                    'id': row.id,
                    'timestamp': row.timestamp.isoformat() if row.timestamp else None,
                    'activity_type': row.activity_type,
                    'activity_category': row.activity_category,
                    'description': row.description,
                    'provider_id': row.provider_id,
                    'provider_name': row.provider_name,
                    'details': json.loads(row.details) if row.details and isinstance(row.details, str) else row.details,
                    'status': row.status,
                    'duration_ms': row.duration_ms,
                    'error_message': row.error_message
                }
                activities.append(activity)
            
            return activities
            
        except Exception as e:
            logger.error(f"Failed to get recent activities: {str(e)}")
            return []
        finally:
            if session:
                session.close()
    
    def get_activity_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of activities for the past N days"""
        session = None
        try:
            session = self.Session()
            
            result = session.execute(text("""
                SELECT 
                    activity_category,
                    COUNT(*) as count,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) as error_count
                FROM activity_log
                WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '%s days'
                GROUP BY activity_category
            """ % days))
            
            summary = {}
            for row in result:
                summary[row.activity_category] = {
                    'total': row.count,
                    'success': row.success_count,
                    'error': row.error_count,
                    'success_rate': round((row.success_count / row.count * 100), 1) if row.count > 0 else 0
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get activity summary: {str(e)}")
            return {}
        finally:
            if session:
                session.close()
    
    def close(self):
        """Close the database engine"""
        self.engine.dispose()

# Singleton instance
activity_logger = ActivityLogger()