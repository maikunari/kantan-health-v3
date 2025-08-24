#!/usr/bin/env python3
"""
Unified Pipeline Orchestrator
Main entry point for all healthcare directory operations
"""

import os
import uuid
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

from .database import DatabaseManager, Provider
from .cache import PersistentCache
from .cost_tracker import CostTracker
from ..collectors.google_places import GooglePlacesCollector
from ..processors.ai_content import AIContentProcessor
from ..publishers.wordpress import WordPressPublisher
from ..utils.pipeline_tracker import PipelineTracker

logger = logging.getLogger(__name__)


class PipelineMode(Enum):
    """Pipeline execution modes"""
    COLLECT = "collect"          # Only collect from Google Places
    PROCESS = "process"          # Only generate AI content
    PUBLISH = "publish"          # Only sync to WordPress
    COLLECT_PROCESS = "collect_process"  # Collect + Process
    PROCESS_PUBLISH = "process_publish"  # Process + Publish
    FULL = "full"               # Complete pipeline


class UnifiedPipeline:
    """Main pipeline orchestrator for healthcare directory"""
    
    def __init__(self):
        """Initialize pipeline components"""
        self.db = DatabaseManager()
        self.cache = PersistentCache()
        self.cost_tracker = CostTracker()
        self.collector = GooglePlacesCollector()
        self.processor = AIContentProcessor()
        self.publisher = WordPressPublisher()
        self.tracker = PipelineTracker()
        
        logger.info("✅ Unified Pipeline initialized")
    
    def run(self, mode: PipelineMode = PipelineMode.FULL, **options) -> Dict[str, Any]:
        """Execute pipeline with specified mode and options
        
        Args:
            mode: Pipeline execution mode
            **options: Configuration options including:
                - limit: Maximum providers to process
                - provider_ids: Specific provider IDs to process
                - cities: Cities for collection
                - specialties: Medical specialties for collection
                - batch_size: AI content batch size
                - dry_run: Preview mode without changes
                
        Returns:
            Execution summary
        """
        # Generate run ID
        run_id = str(uuid.uuid4())
        self.tracker.start_run(run_id, mode.value)
        
        logger.info(f"🚀 Starting Unified Pipeline")
        logger.info(f"📋 Run ID: {run_id}")
        logger.info(f"🔧 Mode: {mode.value}")
        
        start_time = datetime.now()
        results = {
            'run_id': run_id,
            'mode': mode.value,
            'started_at': start_time.isoformat(),
            'phases': {},
            'totals': {
                'collected': 0,
                'processed': 0,
                'published': 0,
                'failed': 0
            },
            'costs': {
                'api_calls': 0,
                'estimated_cost': 0.0
            }
        }
        
        try:
            # Execute based on mode
            if mode in [PipelineMode.COLLECT, PipelineMode.COLLECT_PROCESS, PipelineMode.FULL]:
                collection_results = self._run_collection_phase(**options)
                results['phases']['collection'] = collection_results
                results['totals']['collected'] = collection_results.get('providers_collected', 0)
            
            if mode in [PipelineMode.PROCESS, PipelineMode.COLLECT_PROCESS, 
                       PipelineMode.PROCESS_PUBLISH, PipelineMode.FULL]:
                process_results = self._run_processing_phase(**options)
                results['phases']['processing'] = process_results
                results['totals']['processed'] = process_results.get('successful', 0)
            
            if mode in [PipelineMode.PUBLISH, PipelineMode.PROCESS_PUBLISH, PipelineMode.FULL]:
                publish_results = self._run_publishing_phase(**options)
                results['phases']['publishing'] = publish_results
                results['totals']['published'] = publish_results.get('synced', 0)
            
            # Calculate final metrics
            duration = (datetime.now() - start_time).total_seconds()
            results['completed_at'] = datetime.now().isoformat()
            results['duration_seconds'] = duration
            
            # Get cost summary
            cost_stats = self.cost_tracker.get_usage_stats(days=1)
            results['costs']['api_calls'] = cost_stats['total_requests']
            results['costs']['estimated_cost'] = cost_stats['current_day_cost']
            results['costs']['cache_hits'] = cost_stats['cache_hits']
            results['costs']['cache_rate'] = cost_stats['cache_rate']
            
            # Complete tracking
            self.tracker.complete_run(
                run_id,
                total_providers=results['totals']['collected'] + results['totals']['processed'],
                successful=results['totals']['processed'] + results['totals']['published'],
                failed=results['totals']['failed']
            )
            
            self._print_summary(results)
            
        except Exception as e:
            logger.error(f"❌ Pipeline error: {str(e)}")
            results['error'] = str(e)
            results['status'] = 'failed'
            self.tracker.fail_run(run_id, str(e))
            raise
        
        return results
    
    def _run_collection_phase(self, **options) -> Dict[str, Any]:
        """Run data collection phase
        
        Args:
            **options: Collection options
            
        Returns:
            Collection results
        """
        logger.info("\n📡 PHASE 1: Provider Discovery & Collection")
        logger.info("=" * 50)
        
        results = {
            'started_at': datetime.now().isoformat(),
            'providers_collected': 0,
            'queries_executed': 0,
            'duplicates_skipped': 0,
            'rejected_proficiency': 0,
        }
        
        try:
            # Get collection parameters
            limit = options.get('limit', 10)
            cities = options.get('cities', ['Tokyo', 'Osaka', 'Yokohama'])
            specialties = options.get('specialties')
            
            # Check for specific provider IDs
            provider_ids = options.get('provider_ids', [])
            if provider_ids:
                logger.info(f"📋 Processing {len(provider_ids)} specific providers")
                # Skip collection for specific providers
                return results
            
            # Generate search queries
            queries = self.collector.generate_search_queries(
                cities=cities,
                specialties=specialties,
                limit=100
            )
            
            logger.info(f"🔍 Generated {len(queries)} search queries")
            logger.info(f"🏙️ Cities: {', '.join(cities)}")
            logger.info(f"💊 Limit: {limit} providers")
            
            # Execute collection
            collection_summary = self.collector.collect_providers(
                queries=queries,
                max_per_query=max(1, limit // len(queries))
            )
            
            # Update results
            results.update(collection_summary)
            results['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"✅ Collected {results['providers_collected']} new providers")
            logger.info(f"⏭️ Skipped {results['duplicates_skipped']} duplicates")
            logger.info(f"❌ Rejected {results['rejected_proficiency']} for low English proficiency")
            
        except Exception as e:
            logger.error(f"❌ Collection error: {str(e)}")
            results['error'] = str(e)
            results['status'] = 'failed'
        
        return results
    
    def _run_processing_phase(self, **options) -> Dict[str, Any]:
        """Run AI content processing phase
        
        Args:
            **options: Processing options
            
        Returns:
            Processing results
        """
        logger.info("\n🤖 PHASE 2: AI Content Generation")
        logger.info("=" * 50)
        
        results = {
            'started_at': datetime.now().isoformat(),
            'total_providers': 0,
            'successful': 0,
            'failed': 0,
            'api_calls': 0
        }
        
        try:
            # Get providers to process
            provider_ids = options.get('provider_ids', [])
            limit = options.get('limit', 50)
            batch_size = options.get('batch_size', 2)
            
            if provider_ids:
                # Process specific providers
                providers = []
                for pid in provider_ids:
                    provider = self.db.get_provider_by_id(pid)
                    if provider:
                        providers.append(provider)
            else:
                # Get providers needing content
                providers = self.db.get_providers_needing_content(limit=limit)
            
            results['total_providers'] = len(providers)
            
            if not providers:
                logger.info("✅ No providers need content generation")
                return results
            
            logger.info(f"📝 Processing {len(providers)} providers")
            logger.info(f"📦 Batch size: {batch_size}")
            
            # Process with AI
            if not options.get('dry_run'):
                process_summary = self.processor.process_providers(
                    providers,
                    batch_size=batch_size
                )
                
                results.update(process_summary)
                
                # Log each provider to tracker
                for provider in providers[:results['successful']]:
                    self.tracker.log_step_success(
                        provider.id, provider.provider_name, 'ai_content'
                    )
            else:
                logger.info("🔍 DRY RUN - Skipping actual content generation")
                results['successful'] = len(providers)
            
            results['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"✅ Generated content for {results['successful']} providers")
            logger.info(f"📊 API calls made: {results['api_calls']}")
            
        except Exception as e:
            logger.error(f"❌ Processing error: {str(e)}")
            results['error'] = str(e)
            results['status'] = 'failed'
        
        return results
    
    def _run_publishing_phase(self, **options) -> Dict[str, Any]:
        """Run WordPress publishing phase
        
        Args:
            **options: Publishing options
            
        Returns:
            Publishing results
        """
        logger.info("\n📝 PHASE 3: WordPress Publishing")
        logger.info("=" * 50)
        
        results = {
            'started_at': datetime.now().isoformat(),
            'total_providers': 0,
            'created': 0,
            'updated': 0,
            'synced': 0,
            'failed': 0
        }
        
        try:
            # Get providers to publish
            provider_ids = options.get('provider_ids', [])
            limit = options.get('limit', 25)
            
            if provider_ids:
                # Publish specific providers
                providers = []
                for pid in provider_ids:
                    provider = self.db.get_provider_by_id(pid)
                    if provider:
                        providers.append(provider)
            else:
                # Get providers needing WordPress sync
                providers_to_create = self.db.get_providers_needing_wordpress(limit=limit//2)
                providers_to_update = self.db.get_providers_needing_update(limit=limit//2)
                providers = providers_to_create + providers_to_update
            
            results['total_providers'] = len(providers)
            
            if not providers:
                logger.info("✅ No providers need WordPress sync")
                return results
            
            logger.info(f"📤 Syncing {len(providers)} providers to WordPress")
            
            # Photo URLs no longer needed
            photo_urls = {}
            
            # Sync to WordPress
            if not options.get('dry_run'):
                sync_summary = self.publisher.sync_providers(
                    providers,
                    photo_urls=photo_urls
                )
                
                results.update(sync_summary)
                
                # Log each provider to tracker
                for provider in providers[:results['synced']]:
                    self.tracker.log_step_success(
                        provider.id, provider.provider_name, 'wordpress_sync'
                    )
            else:
                logger.info("🔍 DRY RUN - Skipping actual WordPress sync")
                results['synced'] = len(providers)
            
            results['completed_at'] = datetime.now().isoformat()
            
            logger.info(f"✅ WordPress sync complete: {results['created']} created, {results['updated']} updated")
            
        except Exception as e:
            logger.error(f"❌ Publishing error: {str(e)}")
            results['error'] = str(e)
            results['status'] = 'failed'
        
        return results
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print execution summary"""
        logger.info("\n" + "=" * 60)
        logger.info("🎉 PIPELINE EXECUTION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📋 Run ID: {results['run_id']}")
        logger.info(f"🕐 Duration: {results.get('duration_seconds', 0):.1f} seconds")
        logger.info(f"📊 Providers Collected: {results['totals']['collected']}")
        logger.info(f"🤖 Providers Processed: {results['totals']['processed']}")
        logger.info(f"📝 Providers Published: {results['totals']['published']}")
        logger.info(f"💰 API Calls: {results['costs']['api_calls']}")
        logger.info(f"💵 Estimated Cost: ${results['costs']['estimated_cost']:.2f}")
        logger.info(f"✅ Cache Hit Rate: {results['costs']['cache_rate']:.1f}%")
        logger.info("=" * 60)
    
    def get_status(self, run_id: str = None) -> Dict[str, Any]:
        """Get pipeline status
        
        Args:
            run_id: Specific run ID or None for current
            
        Returns:
            Status information
        """
        if run_id:
            return self.tracker.get_run_status(run_id)
        
        # Get overall system status
        return {
            'database': self.db.get_stats(),
            'cache': self.cache.get_cache_stats(),
            'costs': self.cost_tracker.get_usage_stats(days=1),
            'recent_runs': self.tracker.get_recent_runs(limit=5)
        }
    
    def cleanup(self):
        """Perform cleanup operations"""
        logger.info("🧹 Running cleanup operations...")
        
        # Clean expired cache entries
        expired = self.cache.cleanup_expired()
        logger.info(f"🗑️ Removed {expired} expired cache entries")
        
        # Photo cleanup no longer needed
        photo_expired = 0
        
        return {
            'cache_entries_removed': expired,
            'cache_entries_removed': expired
        }