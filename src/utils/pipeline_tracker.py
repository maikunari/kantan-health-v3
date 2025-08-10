#!/usr/bin/env python3
"""
Pipeline Execution Tracker
Tracks pipeline runs and individual step progress
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from ..core.database import DatabaseManager
from ..core.models import PipelineRun, PipelineStep

logger = logging.getLogger(__name__)


class PipelineTracker:
    """Track pipeline execution progress"""
    
    def __init__(self):
        """Initialize pipeline tracker"""
        self.db = DatabaseManager()
        self.current_run_id = None
        logger.info("✅ Pipeline Tracker initialized")
    
    def start_run(self, run_id: str, run_type: str, config: Dict = None) -> None:
        """Start tracking a new pipeline run
        
        Args:
            run_id: Unique run identifier
            run_type: Type of run (full, collect, process, etc.)
            config: Configuration for this run
        """
        self.current_run_id = run_id
        
        session = self.db.get_session()
        try:
            run = PipelineRun(
                run_id=run_id,
                run_type=run_type,
                started_at=datetime.utcnow(),
                status='running',
                config=config or {}
            )
            session.add(run)
            session.commit()
            
            logger.info(f"🚀 Started pipeline run {run_id}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error starting run: {str(e)}")
        finally:
            session.close()
    
    def complete_run(self, run_id: str, total_providers: int = 0,
                    successful: int = 0, failed: int = 0) -> None:
        """Mark a pipeline run as complete
        
        Args:
            run_id: Run identifier
            total_providers: Total providers processed
            successful: Successful providers
            failed: Failed providers
        """
        session = self.db.get_session()
        try:
            run = session.query(PipelineRun).filter_by(run_id=run_id).first()
            if run:
                run.completed_at = datetime.utcnow()
                run.status = 'completed'
                run.total_providers = total_providers
                run.successful_providers = successful
                run.failed_providers = failed
                session.commit()
                
                logger.info(f"✅ Completed pipeline run {run_id}")
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error completing run: {str(e)}")
        finally:
            session.close()
    
    def fail_run(self, run_id: str, error: str) -> None:
        """Mark a pipeline run as failed
        
        Args:
            run_id: Run identifier
            error: Error message
        """
        session = self.db.get_session()
        try:
            run = session.query(PipelineRun).filter_by(run_id=run_id).first()
            if run:
                run.completed_at = datetime.utcnow()
                run.status = 'failed'
                run.errors = {'error': error}
                session.commit()
                
                logger.error(f"❌ Failed pipeline run {run_id}: {error}")
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error failing run: {str(e)}")
        finally:
            session.close()
    
    def log_step_start(self, provider_id: int, provider_name: str, 
                      step_name: str) -> None:
        """Log the start of a processing step
        
        Args:
            provider_id: Provider ID
            provider_name: Provider name
            step_name: Step name (collect, ai_content, wordpress_sync)
        """
        if not self.current_run_id:
            return
        
        session = self.db.get_session()
        try:
            step = PipelineStep(
                run_id=self.current_run_id,
                provider_id=provider_id,
                provider_name=provider_name,
                step_name=step_name,
                status='running',
                started_at=datetime.utcnow()
            )
            session.add(step)
            session.commit()
            
            logger.debug(f"▶️ Started {step_name} for {provider_name}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging step start: {str(e)}")
        finally:
            session.close()
    
    def log_step_success(self, provider_id: int, provider_name: str,
                        step_name: str, details: Dict = None) -> None:
        """Log successful completion of a step
        
        Args:
            provider_id: Provider ID
            provider_name: Provider name
            step_name: Step name
            details: Additional details
        """
        if not self.current_run_id:
            return
        
        session = self.db.get_session()
        try:
            step = session.query(PipelineStep).filter_by(
                run_id=self.current_run_id,
                provider_id=provider_id,
                step_name=step_name,
                status='running'
            ).first()
            
            if step:
                step.status = 'success'
                step.completed_at = datetime.utcnow()
                step.details = details or {}
            else:
                # Create new step record if not found
                step = PipelineStep(
                    run_id=self.current_run_id,
                    provider_id=provider_id,
                    provider_name=provider_name,
                    step_name=step_name,
                    status='success',
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    details=details or {}
                )
                session.add(step)
            
            session.commit()
            logger.debug(f"✅ Completed {step_name} for {provider_name}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging step success: {str(e)}")
        finally:
            session.close()
    
    def log_failure(self, provider_id: int, provider_name: str,
                   step_name: str, status: str, error_message: str) -> None:
        """Log a failed step
        
        Args:
            provider_id: Provider ID
            provider_name: Provider name
            step_name: Step name
            status: Failure status
            error_message: Error message
        """
        if not self.current_run_id:
            return
        
        session = self.db.get_session()
        try:
            step = session.query(PipelineStep).filter_by(
                run_id=self.current_run_id,
                provider_id=provider_id,
                step_name=step_name,
                status='running'
            ).first()
            
            if step:
                step.status = status
                step.completed_at = datetime.utcnow()
                step.error_message = error_message
            else:
                step = PipelineStep(
                    run_id=self.current_run_id,
                    provider_id=provider_id,
                    provider_name=provider_name,
                    step_name=step_name,
                    status=status,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error_message=error_message
                )
                session.add(step)
            
            session.commit()
            logger.warning(f"❌ {provider_name}: Failed at {step_name} - {status}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging failure: {str(e)}")
        finally:
            session.close()
    
    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get status of a pipeline run
        
        Args:
            run_id: Run identifier
            
        Returns:
            Run status information
        """
        session = self.db.get_session()
        try:
            run = session.query(PipelineRun).filter_by(run_id=run_id).first()
            
            if not run:
                return {'error': 'Run not found'}
            
            # Get step statistics
            steps = session.query(PipelineStep).filter_by(run_id=run_id).all()
            
            step_stats = {}
            for step in steps:
                step_name = step.step_name
                if step_name not in step_stats:
                    step_stats[step_name] = {
                        'total': 0,
                        'success': 0,
                        'failed': 0,
                        'running': 0
                    }
                
                step_stats[step_name]['total'] += 1
                
                if step.status == 'success':
                    step_stats[step_name]['success'] += 1
                elif step.status == 'running':
                    step_stats[step_name]['running'] += 1
                else:
                    step_stats[step_name]['failed'] += 1
            
            # Calculate progress
            total_steps = len(steps)
            completed_steps = sum(1 for s in steps if s.status != 'running')
            progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0
            
            return {
                'run_id': run.run_id,
                'run_type': run.run_type,
                'status': run.status,
                'started_at': run.started_at.isoformat() if run.started_at else None,
                'completed_at': run.completed_at.isoformat() if run.completed_at else None,
                'progress': round(progress, 1),
                'total_providers': run.total_providers,
                'successful_providers': run.successful_providers,
                'failed_providers': run.failed_providers,
                'step_breakdown': step_stats,
                'config': run.config,
                'errors': run.errors
            }
            
        finally:
            session.close()
    
    def get_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent pipeline runs
        
        Args:
            limit: Maximum number of runs
            
        Returns:
            List of recent runs
        """
        session = self.db.get_session()
        try:
            runs = session.query(PipelineRun).order_by(
                PipelineRun.started_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    'run_id': run.run_id,
                    'run_type': run.run_type,
                    'status': run.status,
                    'started_at': run.started_at.isoformat() if run.started_at else None,
                    'completed_at': run.completed_at.isoformat() if run.completed_at else None,
                    'total_providers': run.total_providers,
                    'successful_providers': run.successful_providers,
                    'failed_providers': run.failed_providers
                }
                for run in runs
            ]
            
        finally:
            session.close()
    
    def get_provider_history(self, provider_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get processing history for a provider
        
        Args:
            provider_id: Provider ID
            limit: Maximum number of records
            
        Returns:
            List of processing history
        """
        session = self.db.get_session()
        try:
            steps = session.query(PipelineStep).filter_by(
                provider_id=provider_id
            ).order_by(
                PipelineStep.started_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    'run_id': step.run_id,
                    'step_name': step.step_name,
                    'status': step.status,
                    'started_at': step.started_at.isoformat() if step.started_at else None,
                    'completed_at': step.completed_at.isoformat() if step.completed_at else None,
                    'error_message': step.error_message,
                    'details': step.details
                }
                for step in steps
            ]
            
        finally:
            session.close()