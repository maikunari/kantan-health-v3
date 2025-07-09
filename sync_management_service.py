#!/usr/bin/env python3
"""
Sync Management Service for WordPress Sync Enhancement
Orchestrates sync operations and provides high-level sync management functionality.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from postgres_integration import PostgresIntegration, Provider
from content_hash_service import ContentHashService, ContentComparison
from wordpress_update_service import WordPressUpdateService
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyncOperation(Enum):
    """Types of sync operations"""
    UPDATE_SINGLE = "update_single"
    UPDATE_BULK = "update_bulk"
    UPDATE_BY_CITY = "update_by_city"
    UPDATE_BY_SPECIALTY = "update_by_specialty"
    UPDATE_BY_STATUS = "update_by_status"
    UPDATE_ALL_STALE = "update_all_stale"

class SyncStatus(Enum):
    """Sync operation statuses"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class SyncPlan:
    """Plan for a sync operation"""
    operation_id: str
    operation_type: SyncOperation
    target_providers: List[Provider]
    estimated_duration: int  # in seconds
    batch_size: int = 10
    dry_run: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    filters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.provider_count = len(self.target_providers)

@dataclass
class SyncResult:
    """Result of a sync operation"""
    operation_id: str
    status: SyncStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    providers_processed: int = 0
    providers_updated: int = 0
    providers_failed: int = 0
    providers_no_changes: int = 0
    errors: List[str] = field(default_factory=list)
    details: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def duration(self) -> Optional[int]:
        """Calculate operation duration in seconds"""
        if self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.providers_processed == 0:
            return 0.0
        return (self.providers_updated / self.providers_processed) * 100

class SyncManagementService:
    """Service for managing WordPress sync operations"""
    
    def __init__(self):
        """Initialize sync management service"""
        self.db = PostgresIntegration()
        self.content_hash_service = ContentHashService()
        self.wordpress_service = WordPressUpdateService()
        self.active_operations: Dict[str, SyncResult] = {}
    
    def plan_sync_operation(self, operation_type: SyncOperation, 
                          filters: Dict[str, Any] = None, 
                          batch_size: int = 10,
                          dry_run: bool = False) -> SyncPlan:
        """Plan a sync operation based on specified criteria"""
        
        filters = filters or {}
        operation_id = f"{operation_type.value}_{int(time.time())}"
        
        logger.info(f"🎯 Planning sync operation: {operation_type.value}")
        
        # Get target providers based on operation type
        target_providers = self._get_target_providers(operation_type, filters)
        
        if not target_providers:
            logger.warning(f"⚠️ No providers found for operation: {operation_type.value}")
            return SyncPlan(
                operation_id=operation_id,
                operation_type=operation_type,
                target_providers=[],
                estimated_duration=0,
                batch_size=batch_size,
                dry_run=dry_run,
                filters=filters
            )
        
        # Estimate duration (assuming ~2 seconds per provider + batch delays)
        estimated_duration = len(target_providers) * 2
        estimated_duration += (len(target_providers) // batch_size) * 2  # Batch delays
        
        plan = SyncPlan(
            operation_id=operation_id,
            operation_type=operation_type,
            target_providers=target_providers,
            estimated_duration=estimated_duration,
            batch_size=batch_size,
            dry_run=dry_run,
            filters=filters
        )
        
        logger.info(f"📋 Sync plan created:")
        logger.info(f"   🆔 Operation ID: {operation_id}")
        logger.info(f"   📊 Target providers: {len(target_providers)}")
        logger.info(f"   ⏱️ Estimated duration: {estimated_duration} seconds")
        logger.info(f"   🧪 Dry run: {dry_run}")
        
        return plan
    
    def execute_sync_plan(self, plan: SyncPlan) -> SyncResult:
        """Execute a sync plan and return results"""
        
        logger.info(f"🚀 Executing sync plan: {plan.operation_id}")
        
        # Initialize result tracking
        result = SyncResult(
            operation_id=plan.operation_id,
            status=SyncStatus.RUNNING,
            started_at=datetime.now()
        )
        
        # Track active operation
        self.active_operations[plan.operation_id] = result
        
        try:
            # Execute the sync operation
            if plan.operation_type == SyncOperation.UPDATE_SINGLE:
                sync_results = self._execute_single_update(plan)
            else:
                sync_results = self._execute_bulk_update(plan)
            
            # Process results
            result.providers_processed = sync_results.get('total', 0)
            result.providers_updated = sync_results.get('success', 0)
            result.providers_failed = sync_results.get('failed', 0)
            result.providers_no_changes = sync_results.get('no_changes', 0)
            result.details = sync_results.get('details', [])
            
            # Determine final status
            if result.providers_failed == 0:
                result.status = SyncStatus.SUCCESS
            elif result.providers_updated > 0:
                result.status = SyncStatus.SUCCESS  # Partial success
            else:
                result.status = SyncStatus.FAILED
            
            result.completed_at = datetime.now()
            
            logger.info(f"✅ Sync operation completed: {plan.operation_id}")
            logger.info(f"   📊 Processed: {result.providers_processed}")
            logger.info(f"   ✅ Updated: {result.providers_updated}")
            logger.info(f"   ❌ Failed: {result.providers_failed}")
            logger.info(f"   ⏭️ No changes: {result.providers_no_changes}")
            logger.info(f"   📈 Success rate: {result.success_rate:.1f}%")
            logger.info(f"   ⏱️ Duration: {result.duration} seconds")
            
        except Exception as e:
            logger.error(f"❌ Sync operation failed: {plan.operation_id}: {str(e)}")
            result.status = SyncStatus.FAILED
            result.errors.append(str(e))
            result.completed_at = datetime.now()
        
        finally:
            # Clean up active operation tracking
            if plan.operation_id in self.active_operations:
                del self.active_operations[plan.operation_id]
        
        return result
    
    def get_sync_status(self, operation_id: str) -> Optional[SyncResult]:
        """Get status of a sync operation"""
        return self.active_operations.get(operation_id)
    
    def cancel_sync_operation(self, operation_id: str) -> bool:
        """Cancel a running sync operation"""
        if operation_id in self.active_operations:
            self.active_operations[operation_id].status = SyncStatus.CANCELLED
            logger.info(f"❌ Cancelled sync operation: {operation_id}")
            return True
        return False
    
    def get_sync_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for sync operations"""
        session = self.db.Session()
        
        try:
            # Get all providers with WordPress posts
            providers = session.query(Provider).filter(
                Provider.wordpress_post_id.isnot(None),
                Provider.ai_description.isnot(None)
            ).all()
            
            # Analyze sync needs
            needs_update = []
            recently_synced = []
            never_synced = []
            stale_content = []
            
            for provider in providers:
                # Check if content changed
                if self.content_hash_service.content_changed(provider):
                    needs_update.append(provider)
                
                # Check last sync time
                if provider.last_wordpress_sync:
                    last_sync = provider.last_wordpress_sync
                    if isinstance(last_sync, str):
                        last_sync = datetime.fromisoformat(last_sync)
                    
                    if last_sync > datetime.now() - timedelta(hours=24):
                        recently_synced.append(provider)
                    elif last_sync < datetime.now() - timedelta(days=7):
                        stale_content.append(provider)
                else:
                    never_synced.append(provider)
            
            recommendations = {
                'total_providers': len(providers),
                'needs_update': len(needs_update),
                'recently_synced': len(recently_synced),
                'never_synced': len(never_synced),
                'stale_content': len(stale_content),
                'recommendations': []
            }
            
            # Generate recommendations
            if needs_update:
                recommendations['recommendations'].append({
                    'priority': 'high',
                    'action': 'update_stale_content',
                    'description': f'{len(needs_update)} providers have updated content that needs syncing',
                    'operation_type': SyncOperation.UPDATE_ALL_STALE.value
                })
            
            if never_synced:
                recommendations['recommendations'].append({
                    'priority': 'medium',
                    'action': 'initial_sync',
                    'description': f'{len(never_synced)} providers have never been synced',
                    'operation_type': SyncOperation.UPDATE_BULK.value
                })
            
            if stale_content:
                recommendations['recommendations'].append({
                    'priority': 'low',
                    'action': 'refresh_stale',
                    'description': f'{len(stale_content)} providers have stale content (>7 days)',
                    'operation_type': SyncOperation.UPDATE_ALL_STALE.value
                })
            
            return recommendations
            
        finally:
            session.close()
    
    def get_sync_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get sync operation history from database"""
        session = self.db.Session()
        
        try:
            # Query sync log
            history = session.execute(
                text("""
                SELECT 
                    wsl.sync_timestamp,
                    wsl.sync_type,
                    wsl.sync_status,
                    wsl.sync_duration_ms,
                    wsl.error_message,
                    p.provider_name,
                    p.city,
                    wsl.wordpress_post_id
                FROM wordpress_sync_log wsl
                JOIN providers p ON wsl.provider_id = p.id
                ORDER BY wsl.sync_timestamp DESC
                LIMIT :limit
                """),
                {"limit": limit}
            ).fetchall()
            
            return [
                {
                    'timestamp': row[0],
                    'type': row[1],
                    'status': row[2],
                    'duration_ms': row[3],
                    'error': row[4],
                    'provider_name': row[5],
                    'city': row[6],
                    'wordpress_post_id': row[7]
                }
                for row in history
            ]
            
        finally:
            session.close()
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """Get comprehensive sync statistics"""
        session = self.db.Session()
        
        try:
            # Provider statistics
            total_providers = session.query(Provider).count()
            with_wordpress_id = session.query(Provider).filter(
                Provider.wordpress_post_id.isnot(None)
            ).count()
            
            # Sync statistics
            sync_stats = session.execute(
                text("""
                SELECT 
                    sync_status,
                    COUNT(*) as count,
                    AVG(sync_duration_ms) as avg_duration
                FROM wordpress_sync_log
                WHERE sync_timestamp > NOW() - INTERVAL '30 days'
                GROUP BY sync_status
                """)
            ).fetchall()
            
            # Recent activity
            recent_syncs = session.execute(
                text("""
                SELECT COUNT(*) as count
                FROM wordpress_sync_log
                WHERE sync_timestamp > NOW() - INTERVAL '24 hours'
                """)
            ).scalar()
            
            # Content freshness
            needs_update = len(self.content_hash_service.get_providers_needing_update(session))
            
            return {
                'providers': {
                    'total': total_providers,
                    'with_wordpress_id': with_wordpress_id,
                    'sync_coverage': (with_wordpress_id / total_providers * 100) if total_providers > 0 else 0
                },
                'sync_performance': {
                    stat[0]: {
                        'count': stat[1],
                        'avg_duration_ms': int(stat[2]) if stat[2] else 0
                    }
                    for stat in sync_stats
                },
                'recent_activity': {
                    'syncs_last_24h': recent_syncs,
                    'needs_update': needs_update
                }
            }
            
        finally:
            session.close()
    
    def _get_target_providers(self, operation_type: SyncOperation, filters: Dict[str, Any]) -> List[Provider]:
        """Get target providers for sync operation"""
        session = self.db.Session()
        
        try:
            # Base query - providers with WordPress posts
            query = session.query(Provider).filter(
                Provider.wordpress_post_id.isnot(None),
                Provider.ai_description.isnot(None)
            )
            
            # Apply filters based on operation type
            if operation_type == SyncOperation.UPDATE_SINGLE:
                if 'provider_name' in filters:
                    query = query.filter(Provider.provider_name.ilike(f"%{filters['provider_name']}%"))
                elif 'provider_id' in filters:
                    query = query.filter(Provider.id == filters['provider_id'])
                    
            elif operation_type == SyncOperation.UPDATE_BY_CITY:
                if 'city' in filters:
                    query = query.filter(Provider.city == filters['city'])
                    
            elif operation_type == SyncOperation.UPDATE_BY_SPECIALTY:
                if 'specialty' in filters:
                    # Handle JSON field search
                    query = query.filter(Provider.specialties.op('?')(filters['specialty']))
                    
            elif operation_type == SyncOperation.UPDATE_BY_STATUS:
                if 'status' in filters:
                    query = query.filter(Provider.status == filters['status'])
                    
            elif operation_type == SyncOperation.UPDATE_ALL_STALE:
                # Get providers that need updating based on content changes
                all_providers = query.all()
                return [p for p in all_providers if self.content_hash_service.content_changed(p)]
            
            # Apply limit if specified
            if 'limit' in filters:
                query = query.limit(filters['limit'])
            
            return query.all()
            
        finally:
            session.close()
    
    def _execute_single_update(self, plan: SyncPlan) -> Dict[str, Any]:
        """Execute single provider update"""
        if not plan.target_providers:
            return {'total': 0, 'success': 0, 'failed': 0, 'no_changes': 0, 'details': []}
        
        provider = plan.target_providers[0]
        result = self.wordpress_service.update_existing_post(provider, dry_run=plan.dry_run)
        
        return {
            'total': 1,
            'success': 1 if result['status'] == 'success' else 0,
            'failed': 1 if result['status'] == 'failed' else 0,
            'no_changes': 1 if result['status'] == 'no_changes' else 0,
            'details': [result]
        }
    
    def _execute_bulk_update(self, plan: SyncPlan) -> Dict[str, Any]:
        """Execute bulk provider update"""
        return self.wordpress_service.bulk_update_posts(
            plan.target_providers,
            batch_size=plan.batch_size,
            dry_run=plan.dry_run
        ) 