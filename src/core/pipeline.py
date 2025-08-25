#!/usr/bin/env python3
"""
Unified Pipeline Orchestrator
Main entry point for all healthcare directory operations
"""

# import os  # Not currently used
import uuid
import logging
from typing import List, Dict, Any  # Optional removed - not used
from datetime import datetime
from enum import Enum

from .database import DatabaseManager  # Provider removed - not used
from .cache import PersistentCache
from .cost_tracker import CostTracker
from ..collectors.google_places import GooglePlacesCollector
from ..collectors.geographic_search import GeographicSearchEngine
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
        self.geo_engine = None  # Initialized on demand
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
            wards = options.get('wards')
            specialties = options.get('specialties')
            use_ward_specific = options.get('use_ward_specific', True)
            use_grid = options.get('use_grid', False)
            grid_size = options.get('grid_size')
            
            # Smart grid size defaults
            if grid_size is None:
                if wards:
                    grid_size = 500  # 500m for ward-specific searches
                else:
                    grid_size = 2000  # 2km for city-wide searches
            
            # Check for specific provider IDs
            provider_ids = options.get('provider_ids', [])
            if provider_ids:
                logger.info(f"📋 Processing {len(provider_ids)} specific providers")
                # Skip collection for specific providers
                return results
            
            # Use grid search if enabled
            if use_grid:
                logger.info(f"🗺️ Using GRID SEARCH with {grid_size}m grid size")
                
                # Initialize geographic engine if needed
                if self.geo_engine is None:
                    self.geo_engine = GeographicSearchEngine(grid_size_meters=grid_size)
                
                # Generate grids for each city
                all_grids = []
                for city in cities:
                    grids = self.geo_engine.generate_grid_searches(city, specialties)
                    all_grids.extend(grids)
                    logger.info(f"📍 Generated {len(grids)} grids for {city}")
                
                # Filter grids by ward if specified
                if wards:
                    filtered_grids = [g for g in all_grids if g.ward in wards]
                    logger.info(f"🏘️ Filtered to {len(filtered_grids)} grids in wards: {', '.join(wards)}")
                    all_grids = filtered_grids
                
                # Process grids with progress tracking
                total_collected = 0
                for grid_idx, grid in enumerate(all_grids, 1):
                    if total_collected >= limit:
                        logger.info(f"✅ Reached collection limit of {limit} providers")
                        break
                    
                    # Progress message
                    location = f"{grid.ward} ward" if grid.ward else grid.city
                    logger.info(f"\n📍 Processing grid {grid_idx}/{len(all_grids)} for {location}")
                    
                    # ADAPTIVE SEARCH: Test grid with basic terms first
                    basic_terms = ['doctor', 'clinic', 'hospital', 'dentist', 'pharmacy']
                    test_queries = []
                    
                    # First, test if this grid has ANY providers
                    for term in basic_terms:
                        if grid.ward:
                            query = f"{term} {grid.ward} {grid.city}"
                        else:
                            query = f"{term} near {grid.center_lat},{grid.center_lng}"
                        test_queries.append(query)
                    
                    # Test with basic queries first (in actual collection, not dry run)
                    grid_has_providers = False
                    if not options.get('dry_run'):
                        # Quick test to see if area has providers
                        test_summary = self.collector.collect_providers(
                            queries=test_queries,
                            max_per_query=1,  # Just test for existence
                            city=grid.city,
                            ward=grid.ward
                        )
                        grid_has_providers = test_summary.get('providers_collected', 0) > 0
                        
                        if not grid_has_providers:
                            logger.info(f"   ⏭️ Skipping empty grid - no providers found in basic search")
                            continue
                    
                    # If grid has providers (or dry run), use comprehensive terms
                    grid_queries = []
                    if not specialties:
                        # Use comprehensive medical terms for better coverage
                        specialties = self._get_comprehensive_medical_terms()
                    
                    # Skip basic terms if we already tested them
                    if not options.get('dry_run') and grid_has_providers:
                        # Filter out already-tested basic terms
                        specialties = [s for s in specialties if s not in basic_terms]
                    
                    for specialty in specialties:
                        if grid.ward:
                            query = f"{specialty} {grid.ward} {grid.city}"
                        else:
                            query = f"{specialty} near {grid.center_lat},{grid.center_lng}"
                        grid_queries.append(query)
                    
                    # Calculate remaining slots
                    remaining = limit - total_collected
                    
                    # Check if dry run
                    if options.get('dry_run'):
                        # Estimate what would happen without making API calls
                        estimated_providers = len(grid_queries) * 15  # Average 15 providers per query
                        estimated_cost = len(grid_queries) * 0.035  # $0.035 per query
                        
                        logger.info(f"   🔍 DRY RUN: Would search {len(grid_queries)} queries")
                        # logger.info(f"   📊 Estimated: ~{estimated_providers} providers, ${estimated_cost:.2f} cost")  # Cost logging commented out
                        
                        # Update dry-run totals (but don't actually collect)
                        results['queries_executed'] += len(grid_queries)
                        # Don't increment providers_collected in dry run - no actual collection
                        total_collected += min(estimated_providers, remaining)  # Just for loop control
                    else:
                        # Actually collect providers (if grid has any)
                        if grid_queries:  # Only if we have queries to run
                            grid_summary = self.collector.collect_providers(
                                queries=grid_queries,
                                max_per_query=min(10, remaining // len(grid_queries) if grid_queries else 1),
                                city=grid.city  # Pass city for proper field population
                            )
                            
                            # Track grid in geographic engine
                            self.geo_engine.track_search({"grid_id": grid.grid_id}, grid_summary['providers_collected'])
                            
                            # Update totals (include test results if any)
                            if grid_has_providers and 'test_summary' in locals():
                                # Add providers from initial test
                                total_collected += test_summary.get('providers_collected', 0)
                                results['providers_collected'] += test_summary.get('providers_collected', 0)
                            
                            total_collected += grid_summary['providers_collected']
                            results['providers_collected'] += grid_summary['providers_collected']
                            results['duplicates_skipped'] += grid_summary['duplicates_skipped']
                            results['rejected_proficiency'] += grid_summary['rejected_proficiency']
                            results['queries_executed'] += grid_summary['queries_executed']
                
                # Store estimated totals for dry run
                if options.get('dry_run'):
                    results['estimated_providers'] = total_collected
                    results['estimated_cost'] = results['queries_executed'] * 0.035
                
                collection_summary = results
            else:
                # Standard search (non-grid)
                logger.info(f"🔍 Using STANDARD SEARCH")
                
                # Generate search queries
                queries = self.collector.generate_search_queries(
                    cities=cities,
                    specialties=specialties,
                    wards=wards,
                    use_ward_specific=use_ward_specific,
                    limit=100
                )
                
                logger.info(f"🔍 Generated {len(queries)} search queries")
                logger.info(f"🏙️ Cities: {', '.join(cities)}")
                if wards:
                    logger.info(f"🏘️ Wards: {', '.join(wards)}")
                if specialties:
                    logger.info(f"🏥 Specialties: {', '.join(specialties)}")
                logger.info(f"💊 Limit: {limit} providers")
                
                # Check if dry run
                if options.get('dry_run'):
                    # Estimate what would happen without making API calls
                    estimated_providers = len(queries) * 20  # Average 20 providers per query
                    estimated_cost = len(queries) * 0.035  # $0.035 per query
                    
                    logger.info(f"🔍 DRY RUN MODE - No API calls will be made")
                    logger.info(f"   Would execute {len(queries)} search queries")
                    logger.info(f"   Estimated providers: ~{min(estimated_providers, limit)}")
                    # logger.info(f"   Estimated cost: ${estimated_cost:.2f}")  # Cost logging commented out
                    
                    # Mock results for dry run
                    collection_summary = {
                        'providers_collected': 0,  # No actual collection in dry run
                        'queries_executed': len(queries),
                        'duplicates_skipped': 0,
                        'rejected_proficiency': 0,
                        'estimated_providers': min(estimated_providers, limit),
                        'estimated_cost': estimated_cost,
                        'dry_run': True
                    }
                else:
                    # Execute actual collection
                    collection_summary = self.collector.collect_providers(
                        queries=queries,
                        max_per_query=max(1, limit // len(queries) if queries else 1)
                    )
            
            # Update results
            results.update(collection_summary)
            results['completed_at'] = datetime.now().isoformat()
            
            if options.get('dry_run'):
                logger.info(f"🔍 DRY RUN COMPLETE")
                logger.info(f"   Estimated providers: {results.get('estimated_providers', 0)}")
                # logger.info(f"   Estimated cost: ${results.get('estimated_cost', 0):.2f}")  # Cost logging commented out
                logger.info(f"   No database changes made")
            else:
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
            
            # Sync to WordPress
            if not options.get('dry_run'):
                sync_summary = self.publisher.sync_providers(
                    providers
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
    
    def _get_comprehensive_medical_terms(self) -> List[str]:
        """Get comprehensive list of medical search terms for better coverage"""
        return [
            # Basic terms (essential)
            'doctor', 'clinic', 'hospital', 'dentist', 'pharmacy',
            
            # Specialists
            'cardiologist', 'dermatologist', 'psychiatrist', 'psychologist',
            'orthopedic', 'pediatrician', 'gynecologist', 'ophthalmologist',
            'ENT specialist', 'neurologist', 'urologist', 'oncologist',
            'endocrinologist', 'gastroenterologist', 'rheumatologist',
            
            # Specialty clinics
            'fertility clinic', 'dialysis center', 'rehabilitation center',
            'mental health clinic', 'pain clinic', 'sleep clinic',
            'sports medicine', 'travel clinic', 'vaccination center',
            
            # Alternative medicine
            'acupuncture', 'chiropractor', 'physiotherapy', 'osteopath',
            'traditional medicine', 'holistic clinic',
            
            # Japanese medical terms (for better coverage)
            '医院', '病院', 'クリニック', '診療所',
            '整形外科', '皮膚科', '耳鼻咽喉科', '眼科',
            '内科', '外科', '小児科', '産婦人科',
            '心療内科', '精神科', '歯科'
        ]
    
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
        # logger.info(f"💰 API Calls: {results['costs']['api_calls']}")  # Cost logging commented out
        # logger.info(f"💵 Estimated Cost: ${results['costs']['estimated_cost']:.2f}")  # Cost logging commented out
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
        
        # Photo cleanup no longer needed (removed)
        # photo_expired = 0  # Not used
        
        return {
            'cache_entries_removed': expired
        }