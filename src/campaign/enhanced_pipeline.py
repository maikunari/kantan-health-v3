#!/usr/bin/env python3
"""
Enhanced Pipeline with Campaign State Management
Wraps existing UnifiedPipeline with state tracking and recovery
"""

import os
import sys
import logging
import time
from typing import List, Dict, Optional
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.pipeline.unified_pipeline import UnifiedPipeline
from src.collectors.google_places import GooglePlacesCollector
from src.processors.ai_content import AIContentProcessor
from src.publishers.wordpress import WordPressPublisher
from src.campaign.campaign_state import CampaignStateManager
from src.data import get_english_priority_locations

logger = logging.getLogger(__name__)


class EnhancedCampaignPipeline:
    """Enhanced pipeline with state management for campaign execution"""
    
    def __init__(self, state_file: str = 'campaign_state.json'):
        """Initialize enhanced pipeline with state management
        
        Args:
            state_file: Path to campaign state file
        """
        # Initialize state manager
        self.state_manager = CampaignStateManager(state_file)
        self.state = self.state_manager.state
        
        # Initialize base pipeline components
        self.pipeline = UnifiedPipeline()
        self.collector = GooglePlacesCollector()
        self.ai_processor = AIContentProcessor()
        self.publisher = WordPressPublisher()
        
        logger.info("✅ Enhanced Campaign Pipeline initialized")
        
        # Display current state
        if self.state.completed_queries > 0:
            logger.info(f"📊 Resuming campaign: {self.state.completed_queries}/{self.state.total_queries} queries completed")
            logger.info(f"   Providers found: {self.state.metrics.total_providers_found}")
            logger.info(f"   Total cost: ${self.state.metrics.total_cost:.2f}")
    
    def initialize_campaign(self, 
                           locations: List[str] = None,
                           specialties: List[str] = None,
                           query_limit: int = 1000):
        """Initialize campaign with English-focused queries
        
        Args:
            locations: List of locations or None for auto-priority
            specialties: List of specialties or None for auto-priority
            query_limit: Maximum queries to generate
        """
        if self.state.total_queries > 0 and self.state.completed_queries > 0:
            logger.info("⚠️ Campaign already in progress, use resume_campaign() instead")
            return
        
        logger.info("🚀 Initializing new campaign with English-focused queries")
        
        # Generate English-focused queries
        queries = self.collector.generate_english_focused_queries(
            locations=locations,
            specialties=specialties,
            limit=query_limit
        )
        
        if not queries:
            logger.error("Failed to generate queries")
            return
        
        # Initialize query queue in state
        self.state_manager.initialize_query_queue(queries)
        
        # Set campaign to running
        self.state.status = 'running'
        self.state_manager.save_state()
        
        logger.info(f"✅ Campaign initialized with {len(queries)} queries")
        
        # Show sample queries
        logger.info("Sample queries:")
        for i, query in enumerate(queries[:5]):
            logger.info(f"  {i+1}. {query['query']} (Priority: {query['priority']})")
    
    def run_with_state_management(self, 
                                 daily_limit: int = 200,
                                 test_mode: bool = False,
                                 test_limit: int = 20):
        """Run pipeline with state management and checkpointing
        
        Args:
            daily_limit: Maximum providers to process per day
            test_mode: If True, only process test_limit providers
            test_limit: Number of providers for test mode
        """
        if self.state.status != 'running':
            logger.info(f"Campaign status: {self.state.status}")
            if self.state.status == 'paused':
                logger.info("Campaign is paused. Use resume_campaign() to continue.")
            return
        
        # Set limits
        max_providers = test_limit if test_mode else daily_limit
        providers_collected = 0
        
        logger.info("=" * 80)
        logger.info(f"STARTING CAMPAIGN BATCH (Limit: {max_providers})")
        logger.info("=" * 80)
        
        # Process queries from queue
        while providers_collected < max_providers:
            # Get next query
            query_data = self.state_manager.get_next_query()
            
            if not query_data:
                logger.info("✅ All queries completed!")
                self.state.status = 'completed'
                self.state_manager.save_state()
                break
            
            logger.info(f"\n📍 Query {self.state.current_query_index + 1}/{self.state.total_queries}")
            logger.info(f"   Search: {query_data['query']}")
            logger.info(f"   Location: {query_data['location']} ({query_data['location_type']})")
            logger.info(f"   Specialty: {query_data['specialty']}")
            
            try:
                # Execute search with existing collector - get basic results first
                results = self.collector.search_providers(
                    query_data['query'],
                    limit=10  # Get up to 10 results per query
                )
                
                if not results:
                    logger.info("   No results found")
                    self.state_manager.mark_query_completed(
                        query_data, 0, 0, 0.0
                    )
                    continue
                
                logger.info(f"   Found {len(results)} potential providers")
                
                # Process results through pipeline phases
                qualified_count = 0
                english_scores = []
                
                for result in results:
                    # Get place_id for detailed fetch
                    place_id = result.get('place_id')
                    if not place_id:
                        continue
                    
                    # Fetch full details including reviews (needed for English proficiency scoring)
                    details = self.collector.get_place_details(place_id)
                    if not details:
                        logger.debug(f"   Could not fetch details for {result.get('name', 'Unknown')}")
                        continue
                    
                    # Create provider record from detailed data (includes validation & deduplication)
                    provider_record = self.collector.create_provider_record(details)
                    
                    if not provider_record:
                        continue
                    
                    # Check English proficiency (now should have actual scores from reviews)
                    proficiency = provider_record.get('proficiency_score', 0)
                    if proficiency >= 3:  # Minimum English score
                        qualified_count += 1
                        english_scores.append(proficiency)
                        
                        # Save to database
                        saved_provider = self.pipeline.db.create_or_update_provider(provider_record)
                        
                        if saved_provider:
                            providers_collected += 1
                            logger.info(f"   ✅ Added: {provider_record.get('provider_name', 'Unknown')}")
                            logger.info(f"      English Score: {proficiency}/5")
                            
                            # Update metrics
                            self.state_manager.update_provider_metrics(
                                providers_found=1,
                                english_scores=[proficiency]
                            )
                
                # Mark query completed with performance metrics
                avg_score = sum(english_scores) / len(english_scores) if english_scores else 0
                self.state_manager.mark_query_completed(
                    query_data,
                    providers_found=len(results),
                    providers_qualified=qualified_count,
                    avg_english_score=avg_score
                )
                
                logger.info(f"   Query complete: {qualified_count}/{len(results)} qualified")
                
                # Check if we've hit the limit
                if providers_collected >= max_providers:
                    logger.info(f"\n✅ Daily limit reached: {providers_collected} providers")
                    break
                
            except Exception as e:
                logger.error(f"   ❌ Query failed: {str(e)}")
                # Still mark as completed to move forward
                self.state_manager.mark_query_completed(query_data, 0, 0, 0.0)
                continue
        
        # Run AI content generation for collected providers
        if providers_collected > 0:
            self._process_content_generation()
        
        # Show progress summary
        self.show_progress_dashboard()
        
        return providers_collected
    
    def _process_content_generation(self):
        """Process AI content generation for providers needing content"""
        logger.info("\n📝 Processing AI content generation...")
        
        # Get providers needing content
        providers_needing_content = self.pipeline.db.get_providers_needing_content(limit=20)
        
        if not providers_needing_content:
            logger.info("   No providers need content generation")
            return
        
        logger.info(f"   Found {len(providers_needing_content)} providers needing content")
        
        processed = 0
        for provider in providers_needing_content:
            try:
                # Generate content
                content = self.ai_processor.generate_provider_content(provider)
                
                if content:
                    # Update provider with content
                    self.pipeline.db.update_provider_content(provider.id, content)
                    processed += 1
                    logger.info(f"   ✅ Generated content for: {provider.provider_name}")
                    
                    # Update cost tracking
                    self.state_manager.state.metrics.update_costs(claude_calls=1)
                    
            except Exception as e:
                logger.error(f"   ❌ Content generation failed: {str(e)}")
        
        if processed > 0:
            self.state_manager.update_provider_metrics(providers_processed=processed)
            logger.info(f"   Completed content for {processed} providers")
    
    def pause_campaign(self):
        """Pause the campaign"""
        self.state_manager.pause_campaign()
    
    def resume_campaign(self):
        """Resume the campaign"""
        self.state_manager.resume_campaign()
        logger.info(f"Resuming from query {self.state.current_query_index}/{self.state.total_queries}")
    
    def show_progress_dashboard(self):
        """Display campaign progress dashboard"""
        summary = self.state_manager.get_progress_summary()
        
        print("\n" + "=" * 80)
        print("CAMPAIGN PROGRESS DASHBOARD")
        print("=" * 80)
        
        # Progress bar
        progress_pct = summary['progress']['percentage']
        bar_length = 40
        filled = int(bar_length * progress_pct / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\n📊 Overall Progress: [{bar}] {progress_pct:.1f}%")
        print(f"   Providers: {summary['progress']['providers_found']}/{summary['progress']['target']}")
        print(f"   Queries: {summary['queries']['completed']}/{summary['queries']['total']} ({summary['queries']['percentage']:.1f}%)")
        
        # Timeline
        print(f"\n📅 Timeline:")
        print(f"   Days elapsed: {summary['progress']['days_elapsed']}")
        print(f"   Days remaining: {summary['progress']['days_remaining']}")
        print(f"   Est. completion: {summary['progress']['estimated_completion'][:10]}")
        
        # Costs
        print(f"\n💰 Costs:")
        print(f"   Total: ${summary['costs']['total']:.2f} / ${summary['costs']['budget']:.2f} ({summary['costs']['percentage']:.1f}%)")
        print(f"   Google Places: ${summary['costs']['google_places']:.2f}")
        print(f"   Claude API: ${summary['costs']['claude_api']:.2f}")
        
        # Quality metrics
        print(f"\n✨ Quality:")
        print(f"   Avg English Score: {summary['quality']['avg_english_proficiency']:.1f}/5")
        print(f"   Providers with English: {summary['quality']['providers_with_english']}")
        
        # Daily metrics
        print(f"\n📈 Today's Performance:")
        print(f"   Providers: {summary['daily']['providers_today']}/{summary['daily']['daily_target']}")
        print(f"   Queries run: {summary['daily']['queries_today']}")
        print(f"   Cost today: ${summary['daily']['cost_today']:.2f}")
        
        print("=" * 80)
    
    def recover_from_checkpoint(self, checkpoint_file: str = None):
        """Recover campaign from checkpoint file
        
        Args:
            checkpoint_file: Path to checkpoint file, or None for latest
        """
        if not checkpoint_file:
            # Find latest checkpoint
            checkpoint_dir = self.state_manager.backup_dir
            checkpoints = sorted([
                f for f in os.listdir(checkpoint_dir)
                if f.startswith('checkpoint_')
            ])
            
            if not checkpoints:
                logger.error("No checkpoint files found")
                return False
            
            checkpoint_file = os.path.join(checkpoint_dir, checkpoints[-1])
        
        logger.info(f"🔄 Recovering from checkpoint: {checkpoint_file}")
        
        try:
            import json
            with open(checkpoint_file, 'r') as f:
                data = json.load(f)
            
            # Restore state
            from src.campaign.campaign_state import CampaignState
            self.state_manager.state = CampaignState.from_dict(data)
            self.state = self.state_manager.state
            
            # Save as current state
            self.state_manager.save_state()
            
            logger.info(f"✅ Recovered campaign state:")
            logger.info(f"   Providers found: {self.state.metrics.total_providers_found}")
            logger.info(f"   Queries completed: {self.state.completed_queries}/{self.state.total_queries}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to recover from checkpoint: {str(e)}")
            return False


def main():
    """Test the enhanced pipeline with state management"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Campaign Pipeline')
    parser.add_argument('--test', action='store_true', help='Run in test mode (20 providers)')
    parser.add_argument('--resume', action='store_true', help='Resume existing campaign')
    parser.add_argument('--pause', action='store_true', help='Pause campaign')
    parser.add_argument('--status', action='store_true', help='Show campaign status')
    parser.add_argument('--recover', action='store_true', help='Recover from checkpoint')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    # Initialize pipeline
    pipeline = EnhancedCampaignPipeline()
    
    if args.status:
        pipeline.show_progress_dashboard()
    elif args.pause:
        pipeline.pause_campaign()
    elif args.resume:
        pipeline.resume_campaign()
        pipeline.run_with_state_management(test_mode=args.test)
    elif args.recover:
        pipeline.recover_from_checkpoint()
    else:
        # Initialize or continue campaign
        if pipeline.state.total_queries == 0:
            # Initialize with priority locations
            pipeline.initialize_campaign(
                locations=None,  # Auto-select priority locations
                specialties=None,  # Auto-select priority specialties
                query_limit=100 if args.test else 1000
            )
        
        # Run campaign
        pipeline.run_with_state_management(
            test_mode=args.test,
            test_limit=20
        )


if __name__ == "__main__":
    main()