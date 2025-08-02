#!/usr/bin/env python3
"""
Unified Healthcare Directory Pipeline
Consolidates all automation scripts into a single, streamlined pipeline with:
- Provider discovery and collection
- AI content generation (mega-batch optimized)
- WordPress synchronization
- Comprehensive error tracking and recovery
"""

import argparse
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import core components
from pipeline_tracker import PipelineTracker
from postgres_integration import PostgresIntegration, Provider, get_postgres_config
from google_places_integration import GooglePlacesHealthcareCollector
from claude_mega_batch_processor import ClaudeMegaBatchProcessor
from wordpress_sync_manager import WordPressSyncManager
from populate_provider_locations import populate_missing_locations
from update_existing_providers import update_google_places_data, load_google_api_key
from activity_logger import activity_logger

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedPipeline:
    """Unified pipeline for healthcare directory automation"""
    
    def __init__(self, run_type: str = 'unified_pipeline'):
        self.tracker = PipelineTracker(run_type)
        self.db = PostgresIntegration()
        self.mega_batch_processor = ClaudeMegaBatchProcessor()
        self.wordpress_sync = WordPressSyncManager()
        
    def run(self, 
            mode: str = 'full',
            provider_ids: List[int] = None,
            limit: int = 25,
            cities: List[str] = None,
            skip_collection: bool = False,
            skip_ai_content: bool = False,
            skip_wordpress: bool = False,
            batch_size: int = 2,
            max_retries: int = 2,
            dry_run: bool = False) -> Dict[str, Any]:
        """
        Run the unified pipeline
        
        Args:
            mode: 'full' (all steps), 'content' (AI content only), 'sync' (WordPress only)
            provider_ids: Specific provider IDs to process
            limit: Limit for new provider collection or processing
            cities: Cities to search for new providers
            skip_collection: Skip provider discovery/collection
            skip_ai_content: Skip AI content generation
            skip_wordpress: Skip WordPress sync
            batch_size: Batch size for AI content generation
            max_retries: Maximum retry attempts for failed steps
            dry_run: Preview mode without making changes
        
        Returns:
            Dictionary with pipeline results
        """
        
        start_time = datetime.now()
        results = {
            'run_id': self.tracker.run_id,
            'mode': mode,
            'start_time': start_time.isoformat(),
            'providers_collected': 0,
            'providers_processed': 0,
            'ai_content_generated': 0,
            'wordpress_synced': 0,
            'errors': [],
            'summary': {}
        }
        
        try:
            logger.info(f"🚀 Starting Unified Pipeline - Mode: {mode.upper()}")
            logger.info(f"📋 Run ID: {self.tracker.run_id}")
            
            if dry_run:
                logger.info("🔍 DRY RUN MODE - No changes will be made")
            
            # Step 1: Provider Collection (if not skipped)
            if not skip_collection and mode in ['full']:
                logger.info("\n📡 PHASE 1: Provider Discovery & Collection")
                collection_results = self._run_collection_phase(cities, limit, dry_run)
                results['providers_collected'] = collection_results['collected']
                results['collection_details'] = collection_results
            
            # Step 2: Determine providers to process
            if provider_ids:
                providers_to_process = self._get_providers_by_ids(provider_ids)
                logger.info(f"📋 Processing {len(providers_to_process)} specified providers")
            else:
                providers_to_process = self._get_providers_needing_processing(limit)
                logger.info(f"📋 Found {len(providers_to_process)} providers needing processing")
            
            if not providers_to_process:
                logger.info("✅ No providers need processing")
                results['summary']['status'] = 'completed'
                results['summary']['message'] = 'No providers require processing'
                return results
            
            self.tracker.set_total_providers(len(providers_to_process))
            results['providers_to_process'] = len(providers_to_process)
            
            # Step 3: AI Content Generation (if not skipped)
            if not skip_ai_content and mode in ['full', 'content']:
                logger.info(f"\n🤖 PHASE 2: AI Content Generation (Mega-Batch)")
                content_results = self._run_ai_content_phase(
                    providers_to_process, batch_size, max_retries, dry_run
                )
                results['ai_content_generated'] = content_results['generated']
                results['ai_content_details'] = content_results
            
            # Step 4: WordPress Sync (if not skipped)
            if not skip_wordpress and mode in ['full', 'sync']:
                logger.info(f"\n📝 PHASE 3: WordPress Synchronization")
                sync_results = self._run_wordpress_sync_phase(
                    providers_to_process, max_retries, dry_run
                )
                results['wordpress_synced'] = sync_results['synced']
                results['wordpress_details'] = sync_results
            
            # Complete pipeline tracking
            self.tracker.complete_pipeline()
            
            # Generate summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            results['end_time'] = end_time.isoformat()
            results['duration_seconds'] = duration
            results['summary'] = {
                'status': 'completed',
                'providers_collected': results['providers_collected'],
                'providers_processed': len(providers_to_process),
                'ai_content_generated': results['ai_content_generated'],
                'wordpress_synced': results['wordpress_synced'],
                'total_errors': len(results['errors']),
                'duration_minutes': round(duration / 60, 1)
            }
            
            # Log final summary
            self._log_summary(results)
            
            # Log to activity logger
            activity_logger.log_activity(
                activity_type='pipeline_complete',
                activity_category='pipeline',
                description=f'Unified pipeline completed - {mode} mode',
                details=results['summary'],
                status='success'
            )
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {str(e)}")
            results['errors'].append({
                'phase': 'pipeline',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            results['summary']['status'] = 'failed'
            results['summary']['error'] = str(e)
            
            activity_logger.log_activity(
                activity_type='pipeline_error',
                activity_category='pipeline',
                description=f'Unified pipeline failed - {mode} mode',
                details={'error': str(e)},
                status='error',
                error_message=str(e)
            )
            
            return results
    
    def _run_collection_phase(self, cities: List[str], limit: int, dry_run: bool) -> Dict[str, Any]:
        """Run provider discovery and collection phase"""
        results = {
            'collected': 0,
            'queries_executed': 0,
            'duplicates_skipped': 0,
            'errors': []
        }
        
        if dry_run:
            logger.info("🔍 Dry run - skipping actual collection")
            return results
        
        try:
            # Initialize collector
            collector = GooglePlacesHealthcareCollector(daily_limit=limit)
            
            # Generate search queries
            if not cities:
                cities = ['Tokyo', 'Yokohama', 'Osaka', 'Fukuoka', 'Kyoto']
            
            queries = collector.generate_search_queries(
                cities=cities,
                limit=200  # Query limit
            )
            results['queries_generated'] = len(queries)
            
            # Execute collection
            logger.info(f"🔍 Executing {len(queries)} search queries...")
            collection_summary = collector.collect_providers(
                queries=queries,
                max_per_query=max(1, limit // len(queries))  # Distribute limit across queries
            )
            
            results['collected'] = collection_summary.get('new_providers', 0)
            results['queries_executed'] = collection_summary.get('queries_executed', 0)
            results['duplicates_skipped'] = collection_summary.get('duplicates_skipped', 0)
            
            logger.info(f"✅ Collected {results['collected']} new providers")
            logger.info(f"⏭️ Skipped {results['duplicates_skipped']} duplicates")
            
        except Exception as e:
            logger.error(f"❌ Collection phase error: {str(e)}")
            results['errors'].append(str(e))
        
        return results
    
    def _run_ai_content_phase(self, providers: List[Provider], batch_size: int, 
                             max_retries: int, dry_run: bool) -> Dict[str, Any]:
        """Run AI content generation phase using mega-batch processing"""
        results = {
            'generated': 0,
            'failed': 0,
            'api_calls': 0,
            'errors': []
        }
        
        if dry_run:
            logger.info("🔍 Dry run - skipping actual content generation")
            results['generated'] = len(providers)
            return results
        
        try:
            # Filter providers needing content
            providers_needing_content = [
                p for p in providers
                if not p.ai_description or not p.seo_title or not p.selected_featured_image
            ]
            
            if not providers_needing_content:
                logger.info("✅ All providers already have AI content")
                return results
            
            logger.info(f"📝 Generating content for {len(providers_needing_content)} providers")
            logger.info(f"📦 Batch size: {batch_size}")
            
            # Process in mega-batches
            for i in range(0, len(providers_needing_content), batch_size):
                batch = providers_needing_content[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(providers_needing_content) + batch_size - 1) // batch_size
                
                logger.info(f"📦 Processing batch {batch_num}/{total_batches}")
                
                for attempt in range(max_retries + 1):
                    try:
                        # Generate content for batch
                        content_results = self.mega_batch_processor.generate_mega_batch_content(batch)
                        results['api_calls'] += 1
                        
                        if content_results:
                            # Update database with results
                            success_count = self._update_content_in_database(batch, content_results)
                            results['generated'] += success_count
                            
                            # Log to pipeline tracker
                            for provider in batch[:success_count]:
                                self.tracker.log_step_success(
                                    provider.id, provider.provider_name, 'ai_content'
                                )
                            
                            break  # Success, exit retry loop
                        else:
                            raise Exception("No content generated")
                            
                    except Exception as e:
                        if attempt < max_retries:
                            logger.warning(f"🔄 Retry {attempt + 1}/{max_retries} for batch {batch_num}")
                            time.sleep(2 ** attempt)  # Exponential backoff
                        else:
                            logger.error(f"❌ Batch {batch_num} failed after {max_retries} retries: {str(e)}")
                            results['failed'] += len(batch)
                            results['errors'].append(f"Batch {batch_num}: {str(e)}")
                            
                            # Log failures to tracker
                            for provider in batch:
                                self.tracker.log_failure(
                                    provider.id, provider.provider_name, 'ai_content',
                                    'generation_failed', str(e)
                                )
            
            logger.info(f"✅ Generated content for {results['generated']} providers")
            logger.info(f"💰 Total API calls: {results['api_calls']}")
            
        except Exception as e:
            logger.error(f"❌ AI content phase error: {str(e)}")
            results['errors'].append(str(e))
        
        return results
    
    def _run_wordpress_sync_phase(self, providers: List[Provider], 
                                 max_retries: int, dry_run: bool) -> Dict[str, Any]:
        """Run WordPress synchronization phase"""
        results = {
            'synced': 0,
            'created': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        if dry_run:
            logger.info("🔍 Dry run - skipping actual WordPress sync")
            results['synced'] = len(providers)
            return results
        
        try:
            # Filter providers ready for sync
            providers_to_sync = [
                p for p in providers
                if p.ai_description and p.seo_title and p.status in ['approved', 'description_generated']
            ]
            
            if not providers_to_sync:
                logger.info("ℹ️ No providers ready for WordPress sync")
                return results
            
            logger.info(f"📤 Syncing {len(providers_to_sync)} providers to WordPress")
            
            # Sync each provider
            for provider in providers_to_sync:
                for attempt in range(max_retries + 1):
                    try:
                        if provider.wordpress_post_id:
                            # Update existing post
                            sync_result = self.wordpress_sync.update_single_provider(provider)
                            if sync_result.get('success'):
                                results['updated'] += 1
                                results['synced'] += 1
                        else:
                            # Create new post
                            sync_result = self.wordpress_sync.create_provider_post(provider)
                            if sync_result.get('success'):
                                results['created'] += 1
                                results['synced'] += 1
                        
                        # Log success
                        self.tracker.log_step_success(
                            provider.id, provider.provider_name, 'wordpress_sync'
                        )
                        break  # Success, exit retry loop
                        
                    except Exception as e:
                        if attempt < max_retries:
                            logger.warning(f"🔄 Retry {attempt + 1}/{max_retries} for {provider.provider_name}")
                            time.sleep(2 ** attempt)
                        else:
                            logger.error(f"❌ WordPress sync failed for {provider.provider_name}: {str(e)}")
                            results['failed'] += 1
                            results['errors'].append(f"{provider.provider_name}: {str(e)}")
                            
                            # Log failure
                            self.tracker.log_failure(
                                provider.id, provider.provider_name, 'wordpress_sync',
                                'sync_failed', str(e)
                            )
            
            logger.info(f"✅ WordPress sync complete: {results['created']} created, {results['updated']} updated")
            
        except Exception as e:
            logger.error(f"❌ WordPress sync phase error: {str(e)}")
            results['errors'].append(str(e))
        
        return results
    
    def _get_providers_by_ids(self, provider_ids: List[int]) -> List[Provider]:
        """Get providers by their IDs"""
        session = self.db.Session()
        try:
            providers = session.query(Provider).filter(Provider.id.in_(provider_ids)).all()
            return providers
        finally:
            session.close()
    
    def _get_providers_needing_processing(self, limit: int = None) -> List[Provider]:
        """Get providers that need any processing"""
        session = self.db.Session()
        try:
            query = session.query(Provider).filter(
                # Need AI content (check for None or empty string)
                (Provider.ai_description.is_(None)) |
                (Provider.ai_description == '') |
                (Provider.seo_title.is_(None)) |
                (Provider.seo_title == '') |
                (Provider.selected_featured_image.is_(None)) |
                (Provider.selected_featured_image == '') |
                # Have content but not synced
                ((Provider.ai_description.isnot(None)) & 
                 (Provider.ai_description != '') & 
                 (Provider.wordpress_post_id.is_(None)))
            )
            
            if limit:
                query = query.limit(limit)
            
            providers = query.all()
            return providers
        finally:
            session.close()
    
    def _update_content_in_database(self, providers: List[Provider], 
                                   content_results: List[Any]) -> int:
        """Update database with AI-generated content"""
        session = self.db.Session()
        updated_count = 0
        
        try:
            for provider, result in zip(providers, content_results):
                try:
                    db_provider = session.query(Provider).filter_by(id=provider.id).first()
                    if db_provider:
                        db_provider.ai_description = result.description
                        db_provider.ai_excerpt = result.excerpt
                        db_provider.seo_title = result.seo_title
                        db_provider.seo_meta_description = result.seo_meta_description
                        db_provider.ai_review_summary = result.review_summary
                        db_provider.ai_english_experience = result.english_experience_summary
                        db_provider.selected_featured_image = result.selected_featured_image
                        
                        # Update status if needed
                        if db_provider.status == 'pending':
                            db_provider.status = 'approved'
                        
                        updated_count += 1
                except Exception as e:
                    logger.error(f"Error updating provider {provider.id}: {str(e)}")
                    session.rollback()
            
            session.commit()
            
        except Exception as e:
            logger.error(f"Database update error: {str(e)}")
            session.rollback()
        finally:
            session.close()
        
        return updated_count
    
    def _log_summary(self, results: Dict[str, Any]):
        """Log a summary of the pipeline run"""
        summary = results['summary']
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 UNIFIED PIPELINE COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📋 Run ID: {results['run_id']}")
        logger.info(f"🕐 Duration: {summary['duration_minutes']} minutes")
        logger.info(f"📊 Providers Collected: {summary['providers_collected']}")
        logger.info(f"🔄 Providers Processed: {summary['providers_processed']}")
        logger.info(f"🤖 AI Content Generated: {summary['ai_content_generated']}")
        logger.info(f"📝 WordPress Synced: {summary['wordpress_synced']}")
        
        if summary['total_errors'] > 0:
            logger.warning(f"⚠️ Total Errors: {summary['total_errors']}")
        
        logger.info("=" * 60)

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Unified Healthcare Directory Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline with default settings
  python run_unified_pipeline.py
  
  # Process specific providers
  python run_unified_pipeline.py --provider-ids 123 456 789
  
  # AI content only for all pending providers
  python run_unified_pipeline.py --mode content --limit 50
  
  # WordPress sync only
  python run_unified_pipeline.py --mode sync
  
  # Collect providers from specific cities
  python run_unified_pipeline.py --cities Tokyo Osaka --limit 100
  
  # Dry run to preview
  python run_unified_pipeline.py --dry-run --limit 10
        """
    )
    
    # Mode selection
    parser.add_argument("--mode", choices=['full', 'content', 'sync'], default='full',
                       help="Pipeline mode: full (all steps), content (AI only), sync (WordPress only)")
    
    # Provider selection
    parser.add_argument("--provider-ids", nargs='+', type=int,
                       help="Specific provider IDs to process")
    parser.add_argument("--limit", type=int, default=25,
                       help="Limit for collection or processing (default: 25)")
    
    # Collection options
    parser.add_argument("--cities", nargs='+',
                       help="Cities to search (default: Tokyo, Yokohama, Osaka, Fukuoka, Kyoto)")
    parser.add_argument("--skip-collection", action='store_true',
                       help="Skip provider discovery/collection phase")
    
    # Processing options
    parser.add_argument("--skip-ai-content", action='store_true',
                       help="Skip AI content generation phase")
    parser.add_argument("--skip-wordpress", action='store_true',
                       help="Skip WordPress sync phase")
    parser.add_argument("--batch-size", type=int, default=2,
                       help="Batch size for AI content generation (default: 2)")
    
    # Pipeline options
    parser.add_argument("--max-retries", type=int, default=2,
                       help="Maximum retry attempts for failed operations (default: 2)")
    parser.add_argument("--run-type", default="unified_pipeline",
                       help="Run type for tracking (default: unified_pipeline)")
    parser.add_argument("--dry-run", action='store_true',
                       help="Preview mode - no changes will be made")
    
    args = parser.parse_args()
    
    # Print banner
    print("🏥 UNIFIED HEALTHCARE DIRECTORY PIPELINE")
    print("=" * 60)
    print(f"Mode: {args.mode.upper()}")
    print(f"Limit: {args.limit}")
    if args.dry_run:
        print("🔍 DRY RUN MODE")
    print("=" * 60)
    
    # Initialize and run pipeline
    pipeline = UnifiedPipeline(args.run_type)
    results = pipeline.run(
        mode=args.mode,
        provider_ids=args.provider_ids,
        limit=args.limit,
        cities=args.cities,
        skip_collection=args.skip_collection,
        skip_ai_content=args.skip_ai_content,
        skip_wordpress=args.skip_wordpress,
        batch_size=args.batch_size,
        max_retries=args.max_retries,
        dry_run=args.dry_run
    )
    
    # Exit with appropriate code
    if results['summary'].get('status') == 'completed':
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()