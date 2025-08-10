#!/usr/bin/env python3
"""
Pipeline Tracker for Healthcare Directory Automation
Tracks failures and provides retry mechanisms
"""

import uuid
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from postgres_integration import get_postgres_config, Provider
from activity_logger import activity_logger

logger = logging.getLogger(__name__)

class PipelineFailure:
    def __init__(self, provider_id: int, provider_name: str, step: str, 
                 failure_reason: str, error_details: str = None):
        self.provider_id = provider_id
        self.provider_name = provider_name
        self.step = step
        self.failure_reason = failure_reason
        self.error_details = error_details
        self.retry_count = 0

class PipelineTracker:
    def __init__(self, run_type: str = 'manual'):
        self.run_id = str(uuid.uuid4())
        self.run_type = run_type
        self.total_providers = 0
        self.successful_providers = 0
        self.failed_providers = 0
        self.failures = []
        self.api_limits_hit = {}
        
        # Database setup
        config = get_postgres_config()
        self.engine = create_engine(
            f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
        )
        self.Session = sessionmaker(bind=self.engine)
        
        # Start pipeline run tracking
        self._start_pipeline_run()
    
    def _start_pipeline_run(self):
        """Initialize pipeline run in database"""
        session = self.Session()
        try:
            session.execute(text("""
                INSERT INTO pipeline_runs (id, run_type, status, started_at, metadata)
                VALUES (:run_id, :run_type, 'running', CURRENT_TIMESTAMP, :metadata)
            """), {
                'run_id': self.run_id,
                'run_type': self.run_type,
                'metadata': json.dumps({'started_by': 'automation_system'})
            })
            session.commit()
            logger.info(f"🚀 Started pipeline run {self.run_id}")
        except Exception as e:
            logger.error(f"Failed to start pipeline run: {str(e)}")
            session.rollback()
        finally:
            session.close()
    
    def set_total_providers(self, count: int):
        """Set the total number of providers to process"""
        self.total_providers = count
        
        session = self.Session()
        try:
            session.execute(text("""
                UPDATE pipeline_runs 
                SET total_providers = :count 
                WHERE id = :run_id
            """), {'count': count, 'run_id': self.run_id})
            session.commit()
        except Exception as e:
            logger.error(f"Failed to update provider count: {str(e)}")
        finally:
            session.close()
    
    def log_success(self, provider_id: int, provider_name: str, steps_completed: List[str]):
        """Log successful provider processing"""
        self.successful_providers += 1
        
        # Log activity
        activity_logger.log_activity(
            activity_type='pipeline_success',
            activity_category='pipeline',
            description=f'Successfully processed {provider_name}',
            provider_id=provider_id,
            provider_name=provider_name,
            details={
                'pipeline_run_id': self.run_id,
                'steps_completed': steps_completed
            },
            status='success'
        )
        
        # Mark any existing failures as resolved
        self._resolve_provider_failures(provider_id)
    
    def log_failure(self, provider_id: int, provider_name: str, step: str, 
                   failure_reason: str, error_details: str = None):
        """Log pipeline failure for a provider"""
        failure = PipelineFailure(provider_id, provider_name, step, failure_reason, error_details)
        self.failures.append(failure)
        
        # Track API limits separately
        if failure_reason == 'api_limit':
            self.api_limits_hit[step] = datetime.now()
        
        # Save to database
        session = self.Session()
        try:
            session.execute(text("""
                INSERT INTO pipeline_failures 
                (provider_id, provider_name, pipeline_run_id, step, failure_reason, error_details, created_at)
                VALUES (:provider_id, :provider_name, :run_id, :step, :reason, :details, CURRENT_TIMESTAMP)
            """), {
                'provider_id': provider_id,
                'provider_name': provider_name,
                'run_id': self.run_id,
                'step': step,
                'reason': failure_reason,
                'details': error_details
            })
            session.commit()
            
            logger.warning(f"❌ {provider_name}: Failed at {step} - {failure_reason}")
            
            # Log activity
            activity_logger.log_activity(
                activity_type='pipeline_failure',
                activity_category='pipeline',
                description=f'Failed at {step}: {failure_reason}',
                provider_id=provider_id,
                provider_name=provider_name,
                details={
                    'pipeline_run_id': self.run_id,
                    'step': step,
                    'failure_reason': failure_reason
                },
                status='error',
                error_message=error_details
            )
            
        except Exception as e:
            logger.error(f"Failed to log pipeline failure: {str(e)}")
            session.rollback()
        finally:
            session.close()
    
    def log_step_success(self, provider_id: int, provider_name: str, step: str, details: Dict = None):
        """Log successful completion of a pipeline step"""
        activity_logger.log_activity(
            activity_type=f'pipeline_step_{step}',
            activity_category='pipeline',
            description=f'Completed {step} for {provider_name}',
            provider_id=provider_id,
            provider_name=provider_name,
            details={
                'pipeline_run_id': self.run_id,
                'step': step,
                **(details or {})
            },
            status='success'
        )
    
    def _resolve_provider_failures(self, provider_id: int):
        """Mark all failures for a provider as resolved"""
        session = self.Session()
        try:
            session.execute(text("""
                UPDATE pipeline_failures 
                SET resolved = TRUE, resolved_at = CURRENT_TIMESTAMP 
                WHERE provider_id = :provider_id AND resolved = FALSE
            """), {'provider_id': provider_id})
            session.commit()
        except Exception as e:
            logger.error(f"Failed to resolve provider failures: {str(e)}")
        finally:
            session.close()
    
    def complete_pipeline(self):
        """Mark pipeline as completed and update statistics"""
        self.failed_providers = len(set(f.provider_id for f in self.failures))
        
        session = self.Session()
        try:
            session.execute(text("""
                UPDATE pipeline_runs 
                SET status = 'completed', 
                    completed_at = CURRENT_TIMESTAMP,
                    successful_providers = :successful,
                    failed_providers = :failed
                WHERE id = :run_id
            """), {
                'successful': self.successful_providers,
                'failed': self.failed_providers,
                'run_id': self.run_id
            })
            session.commit()
            
            logger.info(f"✅ Pipeline completed: {self.successful_providers} successful, {self.failed_providers} failed")
            
            # Log summary
            activity_logger.log_activity(
                activity_type='pipeline_completed',
                activity_category='pipeline',
                description=f'Pipeline {self.run_id} completed',
                details={
                    'run_id': self.run_id,
                    'total_providers': self.total_providers,
                    'successful_providers': self.successful_providers,
                    'failed_providers': self.failed_providers,
                    'failure_summary': self._get_failure_summary()
                },
                status='success'
            )
            
        except Exception as e:
            logger.error(f"Failed to complete pipeline: {str(e)}")
        finally:
            session.close()
    
    def _get_failure_summary(self) -> Dict[str, int]:
        """Get summary of failures by step and reason"""
        summary = {}
        for failure in self.failures:
            key = f"{failure.step}_{failure.failure_reason}"
            summary[key] = summary.get(key, 0) + 1
        return summary
    
    def get_unresolved_failures(self) -> List[Dict]:
        """Get all unresolved failures from database"""
        session = self.Session()
        try:
            result = session.execute(text("""
                SELECT pf.*, p.provider_name as current_provider_name
                FROM pipeline_failures pf
                LEFT JOIN providers p ON pf.provider_id = p.id
                WHERE pf.resolved = FALSE
                ORDER BY pf.created_at DESC
            """))
            
            failures = []
            for row in result:
                failures.append({
                    'id': row.id,
                    'provider_id': row.provider_id,
                    'provider_name': row.provider_name,
                    'current_provider_name': row.current_provider_name,
                    'step': row.step,
                    'failure_reason': row.failure_reason,
                    'error_details': row.error_details,
                    'retry_count': row.retry_count,
                    'created_at': row.created_at.isoformat() if row.created_at else None
                })
            
            return failures
            
        except Exception as e:
            logger.error(f"Failed to get unresolved failures: {str(e)}")
            return []
        finally:
            session.close()
    
    def retry_failed_step(self, failure_id: int) -> bool:
        """Retry a specific failed step"""
        session = self.Session()
        try:
            # Get failure details
            result = session.execute(text("""
                SELECT * FROM pipeline_failures WHERE id = :failure_id
            """), {'failure_id': failure_id}).fetchone()
            
            if not result:
                logger.error(f"Failure {failure_id} not found")
                return False
            
            # Increment retry count
            session.execute(text("""
                UPDATE pipeline_failures 
                SET retry_count = retry_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = :failure_id
            """), {'failure_id': failure_id})
            session.commit()
            
            logger.info(f"🔄 Retrying {result.step} for provider {result.provider_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to retry step: {str(e)}")
            return False
        finally:
            session.close()
    
    def get_failure_stats(self) -> Dict[str, Any]:
        """Get statistics about pipeline failures"""
        session = self.Session()
        try:
            result = session.execute(text("""
                SELECT 
                    step,
                    failure_reason,
                    COUNT(*) as count,
                    COUNT(CASE WHEN resolved = TRUE THEN 1 END) as resolved_count
                FROM pipeline_failures
                WHERE created_at > NOW() - INTERVAL '7 days'
                GROUP BY step, failure_reason
                ORDER BY count DESC
            """))
            
            stats = {
                'failure_breakdown': [],
                'total_failures': 0,
                'total_resolved': 0
            }
            
            for row in result:
                stats['failure_breakdown'].append({
                    'step': row.step,
                    'reason': row.failure_reason,
                    'count': row.count,
                    'resolved_count': row.resolved_count
                })
                stats['total_failures'] += row.count
                stats['total_resolved'] += row.resolved_count
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get failure stats: {str(e)}")
            return {'error': str(e)}
        finally:
            session.close()