#!/usr/bin/env python3
"""
Unified Pipeline Runner
Main command-line interface for the healthcare directory automation system

This script replaces the multiple run_*.py scripts with a single unified interface:
- run_automation.py
- run_enhanced_automation.py  
- run_mega_batch_automation.py
- run_unified_pipeline.py
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.pipeline import UnifiedPipeline, PipelineMode
from src.core.database import DatabaseManager
from src.core.cost_tracker import CostTracker


def setup_logging(verbose: bool = False):
    """Configure logging for the pipeline"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/pipeline_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Suppress noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    return log_file


def print_summary(results: Dict[str, Any]):
    """Print execution summary"""
    print("\n" + "="*60)
    print("PIPELINE EXECUTION SUMMARY")
    print("="*60)
    
    # Overall status
    print(f"\nStatus: {results.get('status', 'completed')}")
    print(f"Duration: {results.get('duration_seconds', 0):.1f} seconds")
    
    # Collection summary
    if 'collection' in results:
        coll = results['collection']
        print(f"\n📍 Collection Phase:")
        print(f"  - Total queries: {coll.get('total_queries', 0)}")
        print(f"  - New providers: {coll.get('new_providers', 0)}")
        print(f"  - Duplicates skipped: {coll.get('duplicates_skipped', 0)}")
        if 'cost_summary' in coll:
            cost = coll['cost_summary']
            print(f"  - Total cost: ${cost.get('total_cost', 0):.2f}")
    
    # Processing summary
    if 'processing' in results:
        proc = results['processing']
        print(f"\n🤖 AI Processing Phase:")
        print(f"  - Providers processed: {proc.get('providers_processed', 0)}")
        print(f"  - Successful: {proc.get('successful', 0)}")
        print(f"  - Failed: {proc.get('failed', 0)}")
        if proc.get('batch_stats'):
            batch = proc['batch_stats']
            print(f"  - Batches: {batch.get('total_batches', 0)}")
            print(f"  - API efficiency: {batch.get('api_efficiency', 0):.1f}%")
    
    # Publishing summary
    if 'publishing' in results:
        pub = results['publishing']
        print(f"\n📤 WordPress Publishing Phase:")
        print(f"  - Total synced: {pub.get('synced', 0)}")
        print(f"  - Created: {pub.get('created', 0)}")
        print(f"  - Updated: {pub.get('updated', 0)}")
        print(f"  - Failed: {pub.get('failed', 0)}")
    
    # Errors
    if results.get('errors'):
        print(f"\n❌ Errors encountered:")
        for error in results['errors'][:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(results['errors']) > 5:
            print(f"  ... and {len(results['errors']) - 5} more errors")
    
    print("\n" + "="*60 + "\n")


def check_system_status():
    """Check system status before running"""
    print("🔍 Checking system status...")
    
    # Check database connection
    try:
        db = DatabaseManager()
        session = db.get_session()
        
        # Get provider stats
        from sqlalchemy import text
        stats = session.execute(text('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN ai_description IS NOT NULL THEN 1 ELSE 0 END) as has_content,
                SUM(CASE WHEN wordpress_post_id IS NOT NULL THEN 1 ELSE 0 END) as has_wordpress
            FROM providers
        ''')).fetchone()
        
        session.close()
        
        print(f"  ✅ Database connected")
        print(f"  📊 Total providers: {stats.total}")
        print(f"  ⏳ Pending: {stats.pending}")
        print(f"  📝 With AI content: {stats.has_content}")
        print(f"  🌐 Published to WordPress: {stats.has_wordpress}")
        
    except Exception as e:
        print(f"  ❌ Database error: {str(e)}")
        return False
    
    # Check API costs
    try:
        tracker = CostTracker()
        daily_usage = tracker.get_daily_usage()
        monthly_usage = tracker.get_monthly_usage()
        
        print(f"  💰 Daily API cost: ${daily_usage:.2f} / ${tracker.DAILY_LIMIT:.2f}")
        print(f"  💰 Monthly API cost: ${monthly_usage:.2f} / ${tracker.MONTHLY_LIMIT:.2f}")
        
    except Exception as e:
        print(f"  ⚠️  Cost tracking unavailable: {str(e)}")
    
    print()
    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Unified Healthcare Directory Pipeline Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline with defaults
  python scripts/run_pipeline.py --mode full
  
  # Collect only, with specific limit
  python scripts/run_pipeline.py --mode collect --limit 20
  
  # Collect providers in specific Tokyo wards
  python scripts/run_pipeline.py --mode collect --cities Tokyo --wards Shibuya Minato --limit 50
  
  # Use grid search for comprehensive coverage (2km grid)
  python scripts/run_pipeline.py --mode collect --use-grid --cities Tokyo --grid-size 2000 --limit 100
  
  # Collect dentists in Osaka
  python scripts/run_pipeline.py --mode collect --cities Osaka --specialties Dentistry --limit 30
  
  # Process AI content for pending providers
  python scripts/run_pipeline.py --mode process --batch-size 4
  
  # Publish to WordPress with dry run
  python scripts/run_pipeline.py --mode publish --dry-run
  
  # Check system status only
  python scripts/run_pipeline.py --status-only
        """
    )
    
    # Mode selection
    parser.add_argument(
        '--mode',
        type=str,
        choices=['full', 'collect', 'process', 'publish'],
        default='full',
        help='Pipeline mode to run (default: full)'
    )
    
    # Common options
    parser.add_argument('--limit', type=int, help='Limit number of providers to process')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without making changes')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--status-only', action='store_true', help='Check system status and exit')
    
    # Collection options
    parser.add_argument('--queries-per-type', type=int, default=2, help='Max queries per search type (default: 2)')
    parser.add_argument('--results-per-query', type=int, default=20, help='Max results per query (default: 20)')
    parser.add_argument('--skip-photos', action='store_true', help='Skip photo URL generation to save costs')
    parser.add_argument('--cities', type=str, nargs='+', help='Cities to search (e.g., Tokyo Osaka Kyoto)')
    parser.add_argument('--wards', type=str, nargs='+', help='Specific wards to search (e.g., Shibuya Minato Shinjuku)')
    parser.add_argument('--specialties', type=str, nargs='+', help='Medical specialties to search (e.g., Dentistry "Internal Medicine")')
    parser.add_argument('--use-ward-specific', action='store_true', default=True, help='Use ward-specific searches (default: True)')
    
    # Grid search options
    parser.add_argument('--use-grid', action='store_true', help='Use grid-based geographic search for comprehensive coverage')
    parser.add_argument('--grid-size', type=int, help='Grid size in meters (default: 2000 for city, 500 for ward)')
    parser.add_argument('--search-method', type=str, choices=['grid', 'standard'], default='standard',
                        help='Search method to use (default: standard)')
    
    # Processing options
    parser.add_argument('--batch-size', type=int, default=2, help='AI batch size (default: 2)')
    parser.add_argument('--provider-ids', type=int, nargs='+', help='Process specific provider IDs')
    parser.add_argument('--regenerate', action='store_true', help='Regenerate content for providers that already have it')
    
    # Publishing options
    parser.add_argument('--force-update', action='store_true', help='Force update even if content hasn\'t changed')
    parser.add_argument('--create-only', action='store_true', help='Only create new posts, skip updates')
    parser.add_argument('--update-only', action='store_true', help='Only update existing posts, skip creates')
    
    args = parser.parse_args()
    
    # Setup logging
    log_file = setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info(f"🚀 Starting Unified Pipeline Runner")
    logger.info(f"📝 Log file: {log_file}")
    
    # Check status only
    if args.status_only:
        check_system_status()
        return 0
    
    # Check system before running
    if not check_system_status():
        logger.error("System check failed")
        return 1
    
    # Prepare pipeline options
    options = {
        'limit': args.limit,
        'dry_run': args.dry_run,
        'queries_per_type': args.queries_per_type,
        'results_per_query': args.results_per_query,
        'skip_photos': args.skip_photos,
        'batch_size': args.batch_size,
        'provider_ids': args.provider_ids,
        'regenerate': args.regenerate,
        'force_update': args.force_update,
        'create_only': args.create_only,
        'update_only': args.update_only,
        'cities': args.cities,
        'wards': args.wards,
        'specialties': args.specialties,
        'use_ward_specific': args.use_ward_specific,
        'use_grid': args.use_grid or args.search_method == 'grid',
        'grid_size': args.grid_size
    }
    
    # Remove None values
    options = {k: v for k, v in options.items() if v is not None}
    
    # Map mode string to enum
    mode_map = {
        'full': PipelineMode.FULL,
        'collect': PipelineMode.COLLECT,
        'process': PipelineMode.PROCESS,
        'publish': PipelineMode.PUBLISH
    }
    mode = mode_map[args.mode]
    
    # Run pipeline
    try:
        pipeline = UnifiedPipeline()
        results = pipeline.run(mode=mode, **options)
        
        # Print summary
        print_summary(results)
        
        # Check for errors
        if results.get('status') == 'failed':
            logger.error("Pipeline failed")
            return 1
        
        logger.info("✅ Pipeline completed successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.warning("⚠️  Pipeline interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"❌ Pipeline error: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())