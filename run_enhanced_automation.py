#!/usr/bin/env python3
"""
Enhanced Healthcare Directory Automation with Pipeline Tracking
Complete pipeline with error tracking, retry mechanisms, and failure reporting
"""

import argparse
import time
import logging
from typing import List, Dict, Any
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

class EnhancedHealthcareAutomation:
    def __init__(self, run_type: str = 'automation'):
        self.tracker = PipelineTracker(run_type)
        self.db = PostgresIntegration()
        
    def run_full_pipeline(self, provider_ids: List[int] = None, daily_limit: int = 25, 
                         cities: List[str] = None, max_retries: int = 2):
        """
        Run the complete automation pipeline with error tracking
        
        Args:
            provider_ids: Specific provider IDs to process (if None, get recent providers)
            daily_limit: Limit for new provider collection
            cities: Cities to search for new providers
            max_retries: Number of retry attempts for failed steps
        """
        
        try:
            # Step 1: Determine providers to process
            if provider_ids:
                providers = self._get_providers_by_ids(provider_ids)
                logger.info(f"📋 Processing {len(providers)} specified providers")
            else:
                # Get recently added providers that need processing
                providers = self._get_recent_providers_needing_processing()
                logger.info(f"📋 Found {len(providers)} recent providers needing processing")
            
            if not providers:
                logger.info("✅ No providers need processing")
                return self.tracker.run_id
            
            self.tracker.set_total_providers(len(providers))
            
            # Process each provider through the pipeline
            for provider in providers:
                success = self._process_provider_pipeline(provider, max_retries)
                
                if success:
                    completed_steps = self._get_completed_steps(provider)
                    self.tracker.log_success(provider.id, provider.provider_name, completed_steps)
                else:
                    logger.warning(f"❌ Provider {provider.provider_name} failed pipeline")
            
            # Complete pipeline tracking
            self.tracker.complete_pipeline()
            
            # Generate failure report
            self._generate_failure_report()
            
            return self.tracker.run_id
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {str(e)}")
            activity_logger.log_activity(
                activity_type='pipeline_error',
                activity_category='pipeline',
                description=f'Pipeline {self.tracker.run_id} failed',
                details={'error': str(e)},
                status='error',
                error_message=str(e)
            )
            raise
    
    def _get_providers_by_ids(self, provider_ids: List[int]) -> List[Provider]:
        """Get providers by their IDs"""
        session = self.db.Session()
        try:
            providers = session.query(Provider).filter(Provider.id.in_(provider_ids)).all()
            return providers
        finally:
            session.close()
    
    def _get_recent_providers_needing_processing(self) -> List[Provider]:
        """Get recently added providers that need content generation"""
        session = self.db.Session()
        try:
            # Get providers added today or recently that need AI content
            # Check for both None and empty strings
            providers = session.query(Provider).filter(
                (Provider.ai_description.is_(None)) |
                (Provider.ai_description == '') |
                (Provider.seo_title.is_(None)) |
                (Provider.seo_title == '') |
                (Provider.selected_featured_image.is_(None)) |
                (Provider.selected_featured_image == '')
            ).limit(50).all()  # Reasonable limit for processing
            
            return providers
        finally:
            session.close()
    
    def _process_provider_pipeline(self, provider: Provider, max_retries: int = 2) -> bool:
        """Process a single provider through all pipeline steps"""
        provider_success = True
        
        logger.info(f"🏥 Processing {provider.provider_name}")
        
        # Step 1: Google Places Data Enhancement
        if not self._has_complete_google_data(provider):
            success = self._run_with_retry(
                lambda: self._enhance_google_data(provider),
                'google_data', provider, max_retries
            )
            if not success:
                provider_success = False
        else:
            self.tracker.log_step_success(provider.id, provider.provider_name, 'google_data', 
                                        {'reason': 'already_complete'})
        
        # Step 2: Location Data (Geocoding)
        if not self._has_location_data(provider):
            success = self._run_with_retry(
                lambda: self._populate_location_data(provider),
                'geocoding', provider, max_retries
            )
            if not success:
                provider_success = False
        else:
            self.tracker.log_step_success(provider.id, provider.provider_name, 'geocoding',
                                        {'reason': 'already_complete'})
        
        # Step 3: AI Content Generation (Mega Batch approach for efficiency)
        if not self._has_complete_ai_content(provider):
            success = self._run_with_retry(
                lambda: self._generate_ai_content(provider),
                'ai_content', provider, max_retries
            )
            if not success:
                provider_success = False
        else:
            self.tracker.log_step_success(provider.id, provider.provider_name, 'ai_content',
                                        {'reason': 'already_complete'})
        
        # Step 4: WordPress Sync Preparation (mark as ready)
        if provider_success:
            try:
                self._prepare_for_wordpress_sync(provider)
                self.tracker.log_step_success(provider.id, provider.provider_name, 'wp_preparation')
            except Exception as e:
                self.tracker.log_failure(provider.id, provider.provider_name, 'wp_preparation', 
                                       'preparation_error', str(e))
                provider_success = False
        
        return provider_success
    
    def _run_with_retry(self, func, step_name: str, provider: Provider, max_retries: int) -> bool:
        """Run a function with retry logic"""
        for attempt in range(max_retries + 1):
            try:
                result = func()
                if result:
                    self.tracker.log_step_success(provider.id, provider.provider_name, step_name,
                                                {'attempt': attempt + 1})
                    return True
                else:
                    if attempt < max_retries:
                        logger.warning(f"🔄 Retry {attempt + 1}/{max_retries} for {step_name} on {provider.provider_name}")
                        time.sleep(2 ** attempt)  # Exponential backoff
                    
            except Exception as e:
                error_msg = str(e)
                
                # Detect API limits
                if any(keyword in error_msg.lower() for keyword in ['rate limit', 'quota', 'too many requests']):
                    failure_reason = 'api_limit'
                elif 'timeout' in error_msg.lower():
                    failure_reason = 'timeout'
                elif 'network' in error_msg.lower() or 'connection' in error_msg.lower():
                    failure_reason = 'network_error'
                else:
                    failure_reason = 'processing_error'
                
                if attempt < max_retries and failure_reason != 'api_limit':
                    logger.warning(f"🔄 Retry {attempt + 1}/{max_retries} for {step_name} on {provider.provider_name}: {error_msg}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.tracker.log_failure(provider.id, provider.provider_name, step_name, 
                                           failure_reason, error_msg)
                    return False
        
        # If we get here, all retries failed
        self.tracker.log_failure(provider.id, provider.provider_name, step_name, 
                                'max_retries_exceeded', f'Failed after {max_retries} retries')
        return False
    
    def _enhance_google_data(self, provider: Provider) -> bool:
        """Enhance provider with Google Places data"""
        try:
            # Get Google API key
            api_key = load_google_api_key()
            if not api_key:
                logger.error("Google API key not found")
                return False
            
            # Update Google Places data for the provider
            update_google_places_data([provider], api_key)
            return True
        except Exception as e:
            logger.error(f"Google data enhancement failed: {str(e)}")
            return False
    
    def _populate_location_data(self, provider: Provider) -> bool:
        """Populate location data for provider"""
        try:
            # Check if provider already has location data
            if provider.latitude and provider.longitude:
                return True
            
            # Use the existing location population function
            # Since it processes all providers without coordinates, we'll run it
            # and then check if our provider got updated
            populate_missing_locations()
            
            # Refresh provider data from database to check if location was populated
            session = self.db.Session()
            try:
                updated_provider = session.query(Provider).filter_by(id=provider.id).first()
                if updated_provider and updated_provider.latitude and updated_provider.longitude:
                    # Update our provider object
                    provider.latitude = updated_provider.latitude
                    provider.longitude = updated_provider.longitude
                    return True
                else:
                    return False
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Location population failed: {str(e)}")
            return False
    
    def _generate_ai_content(self, provider: Provider) -> bool:
        """Generate AI content for provider using mega batch processor"""
        try:
            # Use the mega batch processor for single provider
            processor = ClaudeMegaBatchProcessor()
            results = processor.generate_mega_batch_content([provider])
            
            if results and len(results) > 0:
                # Update provider with generated content
                result = results[0]
                session = self.db.Session()
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
                        session.commit()
                        return True
                finally:
                    session.close()
            
            return False
            
        except Exception as e:
            logger.error(f"AI content generation failed: {str(e)}")
            return False
    
    def _prepare_for_wordpress_sync(self, provider: Provider):
        """Prepare provider for WordPress sync"""
        # Mark provider as ready for sync if content is complete
        if self._has_complete_ai_content(provider):
            session = self.db.Session()
            try:
                db_provider = session.query(Provider).filter_by(id=provider.id).first()
                if db_provider and db_provider.status == 'pending':
                    db_provider.status = 'approved'  # Ready for WordPress sync
                    session.commit()
            finally:
                session.close()
    
    def _has_complete_google_data(self, provider: Provider) -> bool:
        """Check if provider has complete Google Places data"""
        return bool(provider.business_hours and provider.rating)
    
    def _has_location_data(self, provider: Provider) -> bool:
        """Check if provider has location data"""
        return bool(provider.latitude and provider.longitude)
    
    def _has_complete_ai_content(self, provider: Provider) -> bool:
        """Check if provider has complete AI content"""
        return bool(
            provider.ai_description and 
            provider.seo_title and 
            provider.selected_featured_image
        )
    
    def _get_completed_steps(self, provider: Provider) -> List[str]:
        """Get list of completed pipeline steps for provider"""
        steps = []
        if self._has_complete_google_data(provider):
            steps.append('google_data')
        if self._has_location_data(provider):
            steps.append('geocoding')
        if self._has_complete_ai_content(provider):
            steps.append('ai_content')
        if provider.status == 'approved':
            steps.append('wp_preparation')
        return steps
    
    def _generate_failure_report(self):
        """Generate and display failure report"""
        failures = self.tracker.get_unresolved_failures()
        
        if not failures:
            logger.info("✅ No unresolved failures!")
            return
        
        logger.info(f"\n📊 PIPELINE FAILURE REPORT ({len(failures)} unresolved failures)")
        logger.info("=" * 60)
        
        # Group failures by step and reason
        failure_groups = {}
        for failure in failures:
            key = f"{failure['step']}_{failure['failure_reason']}"
            if key not in failure_groups:
                failure_groups[key] = []
            failure_groups[key].append(failure)
        
        for group_key, group_failures in failure_groups.items():
            step, reason = group_key.split('_', 1)
            logger.info(f"\n❌ {step.upper()} - {reason.replace('_', ' ').title()}: {len(group_failures)} providers")
            
            for failure in group_failures[:5]:  # Show first 5
                logger.info(f"   • {failure['provider_name']} (ID: {failure['provider_id']})")
            
            if len(group_failures) > 5:
                logger.info(f"   ... and {len(group_failures) - 5} more")
        
        logger.info(f"\n💡 Use the Pipeline Failures page to retry specific steps")
        logger.info(f"🔄 Run with --retry-failures to attempt automatic retry")

def main():
    parser = argparse.ArgumentParser(description="Enhanced Healthcare Directory Automation with Pipeline Tracking")
    parser.add_argument("--provider-ids", nargs='+', type=int, help="Specific provider IDs to process")
    parser.add_argument("--daily-limit", type=int, default=25, help="Daily limit for new provider processing")
    parser.add_argument("--cities", nargs='+', help="Cities to search for new providers")
    parser.add_argument("--max-retries", type=int, default=2, help="Maximum retry attempts for failed steps")
    parser.add_argument("--run-type", default="automation", help="Type of pipeline run for tracking")
    parser.add_argument("--retry-failures", action='store_true', help="Retry unresolved failures")
    
    args = parser.parse_args()
    
    print("🏥 Enhanced Healthcare Directory Automation")
    print("=" * 50)
    
    automation = EnhancedHealthcareAutomation(args.run_type)
    
    if args.retry_failures:
        print("🔄 Retrying unresolved failures...")
        failures = automation.tracker.get_unresolved_failures()
        if failures:
            # Group failures by provider and retry
            provider_failures = {}
            for failure in failures:
                if failure['provider_id'] not in provider_failures:
                    provider_failures[failure['provider_id']] = []
                provider_failures[failure['provider_id']].append(failure)
            
            for provider_id in provider_failures.keys():
                providers = automation._get_providers_by_ids([provider_id])
                if not providers:
                    logger.warning(f"Provider {provider_id} not found for retry")
                    continue
                    
                success = automation._process_provider_pipeline(
                    providers[0], 
                    args.max_retries
                )
                if success:
                    # Mark failures as resolved
                    for failure in provider_failures[provider_id]:
                        automation.tracker.retry_failed_step(failure['id'])
        else:
            print("✅ No unresolved failures to retry")
    else:
        # Run main pipeline
        run_id = automation.run_full_pipeline(
            provider_ids=args.provider_ids,
            daily_limit=args.daily_limit,
            cities=args.cities,
            max_retries=args.max_retries
        )
        
        print(f"\n✅ Pipeline completed with run ID: {run_id}")
        print("📊 Check the Pipeline Failures page for any issues that need attention")

if __name__ == "__main__":
    main()