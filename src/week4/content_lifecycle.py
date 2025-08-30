"""
Long-term Content Lifecycle Management System

This module provides comprehensive content lifecycle management for ongoing
provider content updates, quality maintenance, and sustainable operations
within maintenance mode constraints.

Created: 2025-08-30
Author: Healthcare Campaign System
Version: 1.0
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from pathlib import Path

# Import existing systems for integration
try:
    from database_manager import DatabaseManager
    from src.week2.romaji_integration import RomajiProcessor
    from src.week3.quality_assurance import QualityAssuranceSystem
    from src.week3.monitoring_dashboard import CampaignDashboard
    from src.week4.maintenance_setup import MaintenanceModeManager, MaintenanceTask, MaintenanceMode
    from campaign_state_manager import CampaignStateManager
except ImportError as e:
    logging.warning(f"Import warning in content_lifecycle: {e}")
    # Create minimal stubs for development
    class DatabaseManager:
        def execute_query(self, query, params=None): return []
    class RomajiProcessor:
        def process_provider_data(self, data): return data
    class QualityAssuranceSystem:
        def assess_provider_quality(self, provider): return {"quality_score": 85.0}
    class CampaignDashboard:
        def get_provider_metrics(self): return {}
    class MaintenanceModeManager:
        pass
    class CampaignStateManager:
        pass

class ContentStatus(Enum):
    """Content lifecycle status"""
    FRESH = "fresh"
    AGING = "aging" 
    STALE = "stale"
    OUTDATED = "outdated"
    RECENTLY_ADDED = "recently_added"
    DELAY_PERIOD_ACTIVE = "delay_period_active"
    READY_FOR_REVIEW = "ready_for_review"
    NEEDS_UPDATE = "needs_update"
    UPDATE_SCHEDULED = "update_scheduled"
    UPDATING = "updating"
    UPDATED = "updated"
    FAILED = "failed"

class UpdatePriority(Enum):
    """Content update priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DEFERRED = "deferred"

class ContentUpdateReason(Enum):
    """Reasons for content updates"""
    AGE_THRESHOLD = "age_threshold"
    QUALITY_DECLINE = "quality_decline"
    DATA_CHANGES = "data_changes"
    PERFORMANCE_ISSUES = "performance_issues"
    ROMAJI_INCONSISTENCY = "romaji_inconsistency"
    WORDPRESS_SYNC_FAILURE = "wordpress_sync_failure"
    MANUAL_REQUEST = "manual_request"

@dataclass
class ContentUpdateDelayConfig:
    """Configuration for content update delays"""
    
    # Base delay periods (in months)
    new_campaign_delay_months: int = 6
    existing_provider_delay_months: int = 12
    quality_issue_delay_months: int = 1  # Shorter delay for quality issues
    
    # Override settings
    quality_issue_override: bool = True
    manual_update_override: bool = True
    critical_priority_override: bool = True
    
    # Quality thresholds for overrides
    critical_quality_threshold: float = 60.0
    quality_issue_threshold: float = 70.0
    
    # Provider age thresholds
    recently_added_threshold_days: int = 30
    delay_evaluation_enabled: bool = True

@dataclass
class ContentMetrics:
    """Content performance and quality metrics"""
    
    provider_id: str
    content_age_days: int
    quality_score: float
    last_updated: datetime
    traffic_score: float = 0.0
    wordpress_sync_status: bool = True
    romaji_consistency: bool = True
    
    # Provider lifecycle tracking
    provider_created_date: Optional[datetime] = None
    provider_age_days: int = 0
    delay_status: ContentStatus = ContentStatus.FRESH
    eligible_for_update_date: Optional[datetime] = None
    delay_override_reason: Optional[str] = None
    
    # Quality indicators
    completeness_score: float = 0.0
    accuracy_score: float = 0.0
    freshness_score: float = 0.0
    
    # Performance metrics
    page_views_30d: int = 0
    search_ranking: float = 0.0
    user_engagement_score: float = 0.0
    
    # Technical metrics
    content_hash: str = ""
    sync_attempts: int = 0
    last_sync_success: Optional[datetime] = None

@dataclass
class ContentUpdatePlan:
    """Comprehensive content update planning"""
    
    provider_id: str
    current_status: ContentStatus
    target_status: ContentStatus
    priority: UpdatePriority
    update_reasons: List[ContentUpdateReason]
    
    scheduled_date: datetime
    estimated_duration_minutes: int = 15
    estimated_cost: float = 2.50
    
    # Update specifications
    sections_to_update: List[str] = field(default_factory=list)
    romaji_processing_required: bool = True
    wordpress_sync_required: bool = True
    quality_validation_required: bool = True
    
    # Dependencies and constraints
    dependencies: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    
    # Results tracking
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success: bool = False
    quality_improvement: float = 0.0
    error_message: Optional[str] = None

@dataclass
class ContentLifecycleReport:
    """Comprehensive content lifecycle reporting"""
    
    report_id: str
    generated_at: datetime
    
    # Overall metrics
    total_providers: int
    content_status_distribution: Dict[ContentStatus, int] = field(default_factory=dict)
    priority_distribution: Dict[UpdatePriority, int] = field(default_factory=dict)
    
    # Update statistics
    updates_completed_30d: int = 0
    updates_failed_30d: int = 0
    average_quality_improvement: float = 0.0
    cost_per_update: float = 0.0
    
    # Quality trends
    quality_score_trend: Dict[str, float] = field(default_factory=dict)
    content_freshness_score: float = 0.0
    romaji_consistency_score: float = 0.0
    
    # Performance metrics
    high_traffic_providers_updated: int = 0
    wordpress_sync_success_rate: float = 0.0
    
    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    budget_utilization: float = 0.0
    projected_next_month: Dict[str, Any] = field(default_factory=dict)

class ContentAgingAnalyzer:
    """Analyze content aging and identify refresh needs with delay configuration"""
    
    def __init__(self, delay_config: Optional[ContentUpdateDelayConfig] = None):
        self.freshness_threshold_days = 30
        self.aging_threshold_days = 90
        self.stale_threshold_days = 180
        self.outdated_threshold_days = 365
        
        # Delay configuration
        self.delay_config = delay_config or ContentUpdateDelayConfig()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def analyze_content_age_with_delay(self, provider_data: Dict[str, Any]) -> ContentStatus:
        """Analyze content age considering delay configuration"""
        try:
            # Get provider creation date and content update date
            provider_created = provider_data.get('provider_created_date') or provider_data.get('created_date')
            last_updated = provider_data.get('last_updated')
            quality_score = provider_data.get('quality_score', 75.0)
            
            current_time = datetime.now()
            
            # Handle date parsing
            if isinstance(provider_created, str):
                provider_created = datetime.fromisoformat(provider_created.replace('Z', '+00:00'))
            if isinstance(last_updated, str):
                last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            
            # Default provider creation to content update date if missing
            if not provider_created:
                provider_created = last_updated or current_time - timedelta(days=365)
            
            provider_age_days = (current_time - provider_created).days
            content_age_days = (current_time - (last_updated or provider_created)).days
            
            # Check if delay evaluation is disabled
            if not self.delay_config.delay_evaluation_enabled:
                return self._analyze_traditional_content_age(content_age_days)
            
            # Check for override conditions first
            override_reason = self._check_delay_overrides(provider_data, quality_score, provider_age_days)
            if override_reason:
                # For override cases, still respect delay-aware status but allow updates
                # Don't fall back to traditional analysis which causes the 'aging' status issue
                delay_status = self._analyze_with_delay_logic(provider_age_days, content_age_days, quality_score)
                
                # If provider would normally be in delay period, but has override, mark as needs update
                if delay_status == ContentStatus.DELAY_PERIOD_ACTIVE:
                    return ContentStatus.NEEDS_UPDATE  # Override allows immediate update
                elif delay_status == ContentStatus.RECENTLY_ADDED:
                    return ContentStatus.NEEDS_UPDATE  # Override allows immediate update
                else:
                    return delay_status  # Use delay-aware status
            
            # Apply delay logic
            return self._analyze_with_delay_logic(provider_age_days, content_age_days, quality_score)
                
        except Exception as e:
            self.logger.error(f"Error analyzing content age with delay: {e}")
            return ContentStatus.OUTDATED
    
    def analyze_content_age(self, provider_data: Dict[str, Any]) -> ContentStatus:
        """Backwards compatibility wrapper - uses delay analysis by default"""
        return self.analyze_content_age_with_delay(provider_data)
    
    def _analyze_traditional_content_age(self, content_age_days: int) -> ContentStatus:
        """Traditional content age analysis without delay considerations"""
        if content_age_days <= self.freshness_threshold_days:
            return ContentStatus.FRESH
        elif content_age_days <= self.aging_threshold_days:
            return ContentStatus.AGING
        elif content_age_days <= self.stale_threshold_days:
            return ContentStatus.STALE
        else:
            return ContentStatus.OUTDATED
    
    def _analyze_with_delay_logic(self, provider_age_days: int, content_age_days: int, quality_score: float) -> ContentStatus:
        """Analyze content age with delay logic applied"""
        # Determine applicable delay period
        if quality_score < self.delay_config.quality_issue_threshold:
            delay_months = self.delay_config.quality_issue_delay_months
        else:
            delay_months = self.delay_config.new_campaign_delay_months
        
        delay_days = delay_months * 30  # Approximate days per month
        
        # Recently added providers (within 30 days)
        if provider_age_days <= self.delay_config.recently_added_threshold_days:
            return ContentStatus.RECENTLY_ADDED
        
        # Providers within delay period
        elif provider_age_days < delay_days:
            return ContentStatus.DELAY_PERIOD_ACTIVE
        
        # Providers past delay period - should be very rare for new campaigns
        else:
            # For providers genuinely past delay period, they are ready for content review
            # But first check content age to determine if updates are actually needed
            if content_age_days <= self.freshness_threshold_days:
                return ContentStatus.FRESH  # Content is fresh, no update needed yet
            else:
                return ContentStatus.READY_FOR_REVIEW  # Content needs review/update
    
    def _check_delay_overrides(self, provider_data: Dict[str, Any], quality_score: float, provider_age_days: int) -> Optional[str]:
        """Check if provider qualifies for delay override"""
        
        # Critical quality issues override
        if (self.delay_config.critical_priority_override and 
            quality_score < self.delay_config.critical_quality_threshold):
            return f"critical_quality_score_{quality_score}"
        
        # Quality issues override (less critical)
        if (self.delay_config.quality_issue_override and 
            quality_score < self.delay_config.quality_issue_threshold):
            return f"quality_issue_score_{quality_score}"
        
        # Manual update request override
        if (self.delay_config.manual_update_override and 
            provider_data.get('manual_update_requested', False)):
            return "manual_update_requested"
        
        # WordPress sync failure override
        if not provider_data.get('wordpress_sync_status', True):
            return "wordpress_sync_failure"
        
        # Romaji consistency issues override
        if not provider_data.get('romaji_consistency', True):
            return "romaji_inconsistency"
        
        return None
    
    def calculate_eligible_update_date(self, provider_created_date: datetime, quality_score: float = 75.0) -> datetime:
        """Calculate when provider becomes eligible for updates"""
        try:
            # Determine applicable delay period
            if quality_score < self.delay_config.quality_issue_threshold:
                delay_months = self.delay_config.quality_issue_delay_months
            else:
                delay_months = self.delay_config.new_campaign_delay_months
            
            # Calculate eligible date (approximate 30 days per month)
            eligible_date = provider_created_date + timedelta(days=delay_months * 30)
            return eligible_date
            
        except Exception as e:
            self.logger.error(f"Error calculating eligible update date: {e}")
            return datetime.now() + timedelta(days=180)  # Default to 6 months
    
    def get_delay_status_summary(self, content_metrics: Dict[str, Any]) -> Dict[str, int]:
        """Get summary of delay status across all providers"""
        status_counts = {}
        
        for provider_data in content_metrics.values():
            status = self.analyze_content_age_with_delay(provider_data)
            status_counts[status.value] = status_counts.get(status.value, 0) + 1
        
        return status_counts
    
    def calculate_freshness_score(self, content_age_days: int) -> float:
        """Calculate content freshness score (0-100)"""
        try:
            if content_age_days <= self.freshness_threshold_days:
                return 100.0
            elif content_age_days <= self.aging_threshold_days:
                # Linear decay from 100 to 70
                return 100 - (content_age_days - self.freshness_threshold_days) * 30 / (self.aging_threshold_days - self.freshness_threshold_days)
            elif content_age_days <= self.stale_threshold_days:
                # Linear decay from 70 to 30
                return 70 - (content_age_days - self.aging_threshold_days) * 40 / (self.stale_threshold_days - self.aging_threshold_days)
            else:
                # Exponential decay below 30
                return max(5.0, 30 * (0.99 ** (content_age_days - self.stale_threshold_days)))
                
        except Exception as e:
            self.logger.error(f"Error calculating freshness score: {e}")
            return 0.0
    
    def identify_content_changes(self, current_data: Dict[str, Any], previous_data: Dict[str, Any]) -> List[str]:
        """Identify specific content changes requiring updates"""
        changes = []
        
        try:
            # Check for data field changes
            key_fields = ['name', 'address', 'phone', 'specialties', 'languages', 'description']
            
            for field in key_fields:
                current_value = current_data.get(field, '')
                previous_value = previous_data.get(field, '')
                
                if current_value != previous_value:
                    changes.append(f"{field}_changed")
            
            # Check for quality score changes
            current_quality = current_data.get('quality_score', 0)
            previous_quality = previous_data.get('quality_score', 0)
            
            if abs(current_quality - previous_quality) > 5.0:
                changes.append("quality_score_change")
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Error identifying content changes: {e}")
            return []

class ContentPrioritizer:
    """Quality-based content update prioritization system"""
    
    def __init__(self, qa_system: QualityAssuranceSystem):
        self.qa_system = qa_system
        
        # Prioritization weights
        self.quality_weight = 0.4
        self.traffic_weight = 0.25
        self.age_weight = 0.20
        self.strategic_weight = 0.15
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def calculate_update_priority_score(self, metrics: ContentMetrics) -> float:
        """Calculate comprehensive priority score for content updates"""
        try:
            # Quality priority (higher score for lower quality)
            quality_priority = max(0, (100 - metrics.quality_score) / 100) * 100
            
            # Traffic priority (higher score for higher traffic)
            traffic_priority = min(metrics.traffic_score, 100)
            
            # Age priority (higher score for older content)
            age_priority = min(metrics.content_age_days / 365 * 100, 100)
            
            # Strategic priority (based on romaji consistency, sync status)
            strategic_priority = 0
            if not metrics.romaji_consistency:
                strategic_priority += 30
            if not metrics.wordpress_sync_status:
                strategic_priority += 40
            strategic_priority = min(strategic_priority, 100)
            
            # Calculate weighted priority score
            priority_score = (
                quality_priority * self.quality_weight +
                traffic_priority * self.traffic_weight +
                age_priority * self.age_weight +
                strategic_priority * self.strategic_weight
            )
            
            return min(priority_score, 100.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating priority score: {e}")
            return 0.0
    
    def assign_priority_level(self, priority_score: float) -> UpdatePriority:
        """Assign priority level based on score"""
        if priority_score >= 80:
            return UpdatePriority.CRITICAL
        elif priority_score >= 60:
            return UpdatePriority.HIGH
        elif priority_score >= 40:
            return UpdatePriority.MEDIUM
        elif priority_score >= 20:
            return UpdatePriority.LOW
        else:
            return UpdatePriority.DEFERRED
    
    def identify_update_reasons(self, metrics: ContentMetrics, priority_score: float) -> List[ContentUpdateReason]:
        """Identify specific reasons for content updates"""
        reasons = []
        
        try:
            # Age-based reasons
            if metrics.content_age_days > 180:
                reasons.append(ContentUpdateReason.AGE_THRESHOLD)
            
            # Quality-based reasons
            if metrics.quality_score < 75:
                reasons.append(ContentUpdateReason.QUALITY_DECLINE)
            
            # Technical reasons
            if not metrics.romaji_consistency:
                reasons.append(ContentUpdateReason.ROMAJI_INCONSISTENCY)
            
            if not metrics.wordpress_sync_status:
                reasons.append(ContentUpdateReason.WORDPRESS_SYNC_FAILURE)
            
            # Performance reasons
            if metrics.traffic_score > 70 and metrics.quality_score < 80:
                reasons.append(ContentUpdateReason.PERFORMANCE_ISSUES)
            
            return reasons
            
        except Exception as e:
            self.logger.error(f"Error identifying update reasons: {e}")
            return [ContentUpdateReason.MANUAL_REQUEST]

class ContentLifecycleManager:
    """Comprehensive content lifecycle management system with delay configuration"""
    
    def __init__(self, maintenance_manager: Optional[MaintenanceModeManager] = None, delay_config: Optional[ContentUpdateDelayConfig] = None):
        # Initialize core systems
        self.db_manager = DatabaseManager()
        self.romaji_processor = RomajiProcessor()
        self.qa_system = QualityAssuranceSystem()
        self.dashboard = CampaignDashboard()
        self.maintenance_manager = maintenance_manager or MaintenanceModeManager()
        
        # Load delay configuration from environment or use provided config
        self.delay_config = delay_config or self._load_delay_config_from_env()
        
        # Initialize analyzers with delay configuration
        self.aging_analyzer = ContentAgingAnalyzer(self.delay_config)
        self.prioritizer = ContentPrioritizer(self.qa_system)
        
        # Configuration
        self.monthly_update_limit = 50
        self.monthly_budget_limit = 500.0
        self.cost_per_update = 2.50
        
        # State management
        self.active_updates: List[ContentUpdatePlan] = []
        self.completed_updates: List[ContentUpdatePlan] = []
        self.failed_updates: List[ContentUpdatePlan] = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Ensure content lifecycle directories exist
        self._setup_content_directories()
    
    def _load_delay_config_from_env(self) -> ContentUpdateDelayConfig:
        """Load delay configuration from environment variables"""
        try:
            import os
            
            config = ContentUpdateDelayConfig(
                new_campaign_delay_months=int(os.getenv('CONTENT_UPDATE_DELAY_MONTHS', '6')),
                existing_provider_delay_months=int(os.getenv('EXISTING_PROVIDER_DELAY_MONTHS', '12')),
                quality_issue_delay_months=int(os.getenv('QUALITY_ISSUE_DELAY_MONTHS', '1')),
                quality_issue_override=os.getenv('QUALITY_ISSUE_OVERRIDE', 'true').lower() == 'true',
                manual_update_override=os.getenv('MANUAL_UPDATE_OVERRIDE', 'true').lower() == 'true',
                critical_priority_override=os.getenv('CRITICAL_PRIORITY_OVERRIDE', 'true').lower() == 'true',
                critical_quality_threshold=float(os.getenv('CRITICAL_QUALITY_THRESHOLD', '60.0')),
                quality_issue_threshold=float(os.getenv('QUALITY_ISSUE_THRESHOLD', '70.0')),
                recently_added_threshold_days=int(os.getenv('RECENTLY_ADDED_THRESHOLD_DAYS', '30')),
                delay_evaluation_enabled=os.getenv('DELAY_EVALUATION_ENABLED', 'true').lower() == 'true'
            )
            
            self.logger.info(f"Loaded delay configuration - Campaign delay: {config.new_campaign_delay_months} months")
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading delay config from environment: {e}")
            return ContentUpdateDelayConfig()  # Use defaults
    
    def update_delay_config(self, new_config: ContentUpdateDelayConfig):
        """Update delay configuration at runtime"""
        try:
            self.delay_config = new_config
            # Reinitialize aging analyzer with new config
            self.aging_analyzer = ContentAgingAnalyzer(self.delay_config)
            self.logger.info(f"Updated delay configuration - Campaign delay: {new_config.new_campaign_delay_months} months")
        except Exception as e:
            self.logger.error(f"Error updating delay configuration: {e}")
    
    def _setup_content_directories(self):
        """Setup required content lifecycle directories"""
        directories = [
            "content_reports",
            "content_updates",
            "content_analytics",
            "content_backups"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def analyze_all_provider_content(self) -> Dict[str, ContentMetrics]:
        """Analyze content metrics for all providers"""
        try:
            self.logger.info("Starting comprehensive provider content analysis...")
            
            # Get all provider data
            providers = self._get_all_providers()
            content_metrics = {}
            
            for provider in providers:
                try:
                    provider_id = provider.get('id', str(provider.get('provider_id', 'unknown')))
                    
                    # Analyze content age and status
                    content_status = self.aging_analyzer.analyze_content_age(provider)
                    content_age = self._calculate_content_age(provider)
                    
                    # Get quality metrics
                    quality_assessment = self.qa_system.assess_provider_quality(provider)
                    quality_score = quality_assessment.get('quality_score', 75.0)
                    
                    # Calculate traffic and performance metrics
                    traffic_metrics = self._get_provider_traffic_metrics(provider_id)
                    
                    # Check romaji consistency
                    romaji_consistent = self._check_romaji_consistency(provider)
                    
                    # Check WordPress sync status
                    wp_sync_status = self._check_wordpress_sync_status(provider_id)
                    
                    # Get provider creation date and calculate delay status
                    provider_created = provider.get('provider_created_date') or provider.get('created_date')
                    if isinstance(provider_created, str):
                        provider_created = datetime.fromisoformat(provider_created.replace('Z', '+00:00'))
                    
                    provider_age_days = (datetime.now() - provider_created).days if provider_created else 365
                    
                    # Analyze delay status
                    delay_status = self.aging_analyzer.analyze_content_age_with_delay(provider)
                    
                    # Calculate eligible update date
                    eligible_date = None
                    delay_override_reason = None
                    if provider_created:
                        eligible_date = self.aging_analyzer.calculate_eligible_update_date(provider_created, quality_score)
                        # Check for overrides
                        delay_override_reason = self.aging_analyzer._check_delay_overrides(provider, quality_score, provider_age_days)
                    
                    # Create content metrics
                    metrics = ContentMetrics(
                        provider_id=provider_id,
                        content_age_days=content_age,
                        quality_score=quality_score,
                        last_updated=provider.get('last_updated', datetime.now()),
                        traffic_score=traffic_metrics.get('traffic_score', 0.0),
                        wordpress_sync_status=wp_sync_status,
                        romaji_consistency=romaji_consistent,
                        # New delay-related fields
                        provider_created_date=provider_created,
                        provider_age_days=provider_age_days,
                        delay_status=delay_status,
                        eligible_for_update_date=eligible_date,
                        delay_override_reason=delay_override_reason,
                        # Quality indicators
                        completeness_score=quality_assessment.get('completeness_score', 80.0),
                        accuracy_score=quality_assessment.get('accuracy_score', 85.0),
                        freshness_score=self.aging_analyzer.calculate_freshness_score(content_age),
                        # Performance metrics
                        page_views_30d=traffic_metrics.get('page_views_30d', 0),
                        search_ranking=traffic_metrics.get('search_ranking', 0.0),
                        user_engagement_score=traffic_metrics.get('engagement_score', 0.0)
                    )
                    
                    content_metrics[provider_id] = metrics
                    
                except Exception as e:
                    self.logger.error(f"Error analyzing provider {provider.get('id', 'unknown')}: {e}")
                    continue
            
            self.logger.info(f"Completed content analysis for {len(content_metrics)} providers")
            return content_metrics
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive content analysis: {e}")
            return {}
    
    def generate_update_plans(self, content_metrics: Dict[str, ContentMetrics], budget_limit: float = None) -> List[ContentUpdatePlan]:
        """Generate prioritized content update plans within budget constraints and delay rules"""
        try:
            if budget_limit is None:
                budget_limit = self.monthly_budget_limit
                
            self.logger.info(f"Generating update plans with budget limit: ${budget_limit} and delay config")
            
            update_plans = []
            total_cost = 0.0
            max_updates = int(budget_limit / self.cost_per_update)
            
            # Filter providers that are eligible for updates based on delay configuration
            eligible_providers = []
            delay_statistics = {
                'total_providers': len(content_metrics),
                'eligible_for_update': 0,
                'in_delay_period': 0,
                'recently_added': 0,
                'override_qualified': 0
            }
            
            for provider_id, metrics in content_metrics.items():
                # Check delay status
                if hasattr(metrics, 'delay_status'):
                    delay_status = metrics.delay_status
                else:
                    # Determine delay status using provider data
                    provider_data = {
                        'provider_created_date': metrics.provider_created_date,
                        'last_updated': metrics.last_updated,
                        'quality_score': metrics.quality_score,
                        'wordpress_sync_status': metrics.wordpress_sync_status,
                        'romaji_consistency': metrics.romaji_consistency,
                        'manual_update_requested': getattr(metrics, 'manual_update_requested', False)
                    }
                    delay_status = self.aging_analyzer.analyze_content_age_with_delay(provider_data)
                
                # Update statistics
                if delay_status == ContentStatus.RECENTLY_ADDED:
                    delay_statistics['recently_added'] += 1
                elif delay_status == ContentStatus.DELAY_PERIOD_ACTIVE:
                    delay_statistics['in_delay_period'] += 1
                elif delay_status in [ContentStatus.READY_FOR_REVIEW, ContentStatus.NEEDS_UPDATE]:
                    delay_statistics['eligible_for_update'] += 1
                    eligible_providers.append((provider_id, metrics))
                elif delay_status in [ContentStatus.AGING, ContentStatus.STALE, ContentStatus.OUTDATED]:
                    # Override case - provider qualifies despite delay
                    delay_statistics['override_qualified'] += 1
                    eligible_providers.append((provider_id, metrics))
            
            self.logger.info(f"Delay filtering results: {delay_statistics}")
            
            # Calculate priority scores only for eligible providers
            provider_priorities = []
            for provider_id, metrics in eligible_providers:
                priority_score = self.prioritizer.calculate_update_priority_score(metrics)
                priority_level = self.prioritizer.assign_priority_level(priority_score)
                update_reasons = self.prioritizer.identify_update_reasons(metrics, priority_score)
                
                provider_priorities.append({
                    'provider_id': provider_id,
                    'metrics': metrics,
                    'priority_score': priority_score,
                    'priority_level': priority_level,
                    'update_reasons': update_reasons
                })
            
            # Sort by priority score (highest first)
            provider_priorities.sort(key=lambda x: x['priority_score'], reverse=True)
            
            # Create update plans within budget
            current_date = datetime.now()
            
            for i, provider_data in enumerate(provider_priorities):
                if len(update_plans) >= max_updates:
                    break
                
                if total_cost + self.cost_per_update > budget_limit:
                    break
                
                # Skip if priority is too low
                if provider_data['priority_level'] == UpdatePriority.DEFERRED:
                    continue
                
                # Create update plan
                plan = ContentUpdatePlan(
                    provider_id=provider_data['provider_id'],
                    current_status=self._determine_content_status(provider_data['metrics']),
                    target_status=ContentStatus.UPDATED,
                    priority=provider_data['priority_level'],
                    update_reasons=provider_data['update_reasons'],
                    scheduled_date=current_date + timedelta(days=i * 2),  # Spread updates over time
                    estimated_cost=self.cost_per_update,
                    sections_to_update=self._identify_sections_to_update(provider_data['update_reasons']),
                    romaji_processing_required=ContentUpdateReason.ROMAJI_INCONSISTENCY in provider_data['update_reasons'],
                    wordpress_sync_required=True,
                    quality_validation_required=True
                )
                
                update_plans.append(plan)
                total_cost += self.cost_per_update
            
            self.logger.info(f"Generated {len(update_plans)} update plans from {len(eligible_providers)} eligible providers")
            self.logger.info(f"Total cost: ${total_cost:.2f}, {delay_statistics['in_delay_period']} providers in delay period")
            return update_plans
            
        except Exception as e:
            self.logger.error(f"Error generating update plans: {e}")
            return []
    
    def execute_content_update(self, update_plan: ContentUpdatePlan) -> ContentUpdatePlan:
        """Execute a single content update plan"""
        try:
            self.logger.info(f"Starting content update for provider {update_plan.provider_id}")
            
            update_plan.started_at = datetime.now()
            update_plan.current_status = ContentStatus.UPDATING
            
            # Get current provider data
            provider_data = self._get_provider_data(update_plan.provider_id)
            if not provider_data:
                raise ValueError(f"Provider {update_plan.provider_id} not found")
            
            # Track quality before update
            pre_update_quality = self.qa_system.assess_provider_quality(provider_data)
            initial_quality_score = pre_update_quality.get('quality_score', 0.0)
            
            # Execute romaji processing if required
            if update_plan.romaji_processing_required:
                self.logger.info(f"Processing romaji for provider {update_plan.provider_id}")
                provider_data = self.romaji_processor.process_provider_data(provider_data)
            
            # Update specific content sections
            updated_data = self._update_content_sections(provider_data, update_plan.sections_to_update)
            
            # Validate quality after update
            if update_plan.quality_validation_required:
                post_update_quality = self.qa_system.assess_provider_quality(updated_data)
                final_quality_score = post_update_quality.get('quality_score', 0.0)
                update_plan.quality_improvement = final_quality_score - initial_quality_score
            
            # Execute WordPress sync if required
            if update_plan.wordpress_sync_required:
                sync_success = self._sync_to_wordpress(updated_data)
                if not sync_success:
                    raise ValueError("WordPress sync failed")
            
            # Save updated data
            self._save_updated_provider_data(updated_data)
            
            # Mark update as successful
            update_plan.completed_at = datetime.now()
            update_plan.success = True
            update_plan.target_status = ContentStatus.UPDATED
            
            self.logger.info(f"Successfully completed content update for provider {update_plan.provider_id}")
            
        except Exception as e:
            update_plan.error_message = str(e)
            update_plan.success = False
            update_plan.completed_at = datetime.now()
            self.logger.error(f"Failed content update for provider {update_plan.provider_id}: {e}")
        
        return update_plan
    
    def generate_lifecycle_report(self) -> ContentLifecycleReport:
        """Generate comprehensive content lifecycle report"""
        try:
            current_time = datetime.now()
            report_id = f"content_lifecycle_{current_time.strftime('%Y%m%d_%H%M%S')}"
            
            # Analyze all content
            content_metrics = self.analyze_all_provider_content()
            
            # Calculate status distribution
            status_distribution = {}
            for metrics in content_metrics.values():
                status = self._determine_content_status(metrics)
                status_distribution[status] = status_distribution.get(status, 0) + 1
            
            # Calculate update statistics
            completed_updates = len([u for u in self.completed_updates if u.completed_at and (current_time - u.completed_at).days <= 30])
            failed_updates = len([u for u in self.failed_updates if u.completed_at and (current_time - u.completed_at).days <= 30])
            
            # Calculate average quality improvement
            quality_improvements = [u.quality_improvement for u in self.completed_updates if u.quality_improvement > 0]
            avg_quality_improvement = sum(quality_improvements) / len(quality_improvements) if quality_improvements else 0.0
            
            # Calculate WordPress sync success rate
            wp_sync_successes = len([m for m in content_metrics.values() if m.wordpress_sync_status])
            wp_sync_rate = (wp_sync_successes / len(content_metrics)) * 100 if content_metrics else 0.0
            
            # Generate recommendations
            recommendations = self._generate_lifecycle_recommendations(content_metrics, status_distribution)
            
            # Create comprehensive report
            report = ContentLifecycleReport(
                report_id=report_id,
                generated_at=current_time,
                total_providers=len(content_metrics),
                content_status_distribution=status_distribution,
                updates_completed_30d=completed_updates,
                updates_failed_30d=failed_updates,
                average_quality_improvement=avg_quality_improvement,
                cost_per_update=self.cost_per_update,
                content_freshness_score=self._calculate_overall_freshness_score(content_metrics),
                romaji_consistency_score=self._calculate_romaji_consistency_score(content_metrics),
                wordpress_sync_success_rate=wp_sync_rate,
                recommended_actions=recommendations,
                budget_utilization=(completed_updates * self.cost_per_update / self.monthly_budget_limit) * 100,
                projected_next_month=self._project_next_month_needs(content_metrics)
            )
            
            # Save report
            self._save_lifecycle_report(report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating lifecycle report: {e}")
            return ContentLifecycleReport(
                report_id="error_report",
                generated_at=datetime.now(),
                total_providers=0
            )
    
    # Helper methods
    def _get_all_providers(self) -> List[Dict[str, Any]]:
        """Get all provider data from database with creation dates"""
        try:
            # Mock implementation - would query actual database
            current_time = datetime.now()
            providers = []
            
            for i in range(1, 474):  # 473 providers as mentioned
                # Simulate providers being added over realistic campaign timeline
                # For a project less than 2 months old, spread providers over ~60 days maximum
                days_ago = min(i * 0.25, 60)  # Spread creation over ~60 days (realistic for 2-month project)
                provider_created = current_time - timedelta(days=days_ago)
                content_updated = provider_created + timedelta(days=2)  # Content updated shortly after creation
                
                provider = {
                    'id': f'provider_{i}',
                    'name': f'Provider {i}',
                    'provider_created_date': provider_created,
                    'created_date': provider_created,  # Alternative field name
                    'last_updated': content_updated,
                    'quality_score': max(75, 90 - (i % 15)),  # Higher baseline quality, fewer issues
                    'romaji_name': f'provider-{i}',
                    'wordpress_sync_status': i % 50 != 0,  # 98% have successful sync (fewer failures)
                    'romaji_consistency': i % 100 != 0,  # 99% have consistent romaji (very few issues)
                    'manual_update_requested': i % 200 == 0  # 0.5% have manual update requests (very rare)
                }
                providers.append(provider)
            
            self.logger.info(f"Generated {len(providers)} mock providers with creation dates")
            return providers
            
        except Exception as e:
            self.logger.error(f"Error getting providers: {e}")
            return []
    
    def _calculate_content_age(self, provider: Dict[str, Any]) -> int:
        """Calculate content age in days"""
        try:
            last_updated = provider.get('last_updated', datetime.now() - timedelta(days=365))
            if isinstance(last_updated, str):
                last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            return (datetime.now() - last_updated).days
        except:
            return 365  # Default to 1 year old if calculation fails
    
    def _get_provider_traffic_metrics(self, provider_id: str) -> Dict[str, Any]:
        """Get traffic and performance metrics for provider"""
        # Mock implementation
        return {
            'traffic_score': 45.0,
            'page_views_30d': 150,
            'search_ranking': 3.2,
            'engagement_score': 65.0
        }
    
    def _check_romaji_consistency(self, provider: Dict[str, Any]) -> bool:
        """Check romaji naming consistency"""
        try:
            # Mock implementation - would check actual romaji consistency
            romaji_name = provider.get('romaji_name', '')
            return bool(romaji_name and '-' in romaji_name)
        except:
            return False
    
    def _check_wordpress_sync_status(self, provider_id: str) -> bool:
        """Check WordPress synchronization status"""
        # Mock implementation - would check actual sync status
        return True  # Assume most are synced
    
    def _determine_content_status(self, metrics: ContentMetrics) -> ContentStatus:
        """Determine current content status from metrics"""
        if metrics.content_age_days <= 30:
            return ContentStatus.FRESH
        elif metrics.content_age_days <= 90:
            return ContentStatus.AGING
        elif metrics.content_age_days <= 180:
            return ContentStatus.STALE
        else:
            return ContentStatus.OUTDATED
    
    def _identify_sections_to_update(self, update_reasons: List[ContentUpdateReason]) -> List[str]:
        """Identify which content sections need updates based on reasons"""
        sections = ['description']  # Always update description
        
        if ContentUpdateReason.DATA_CHANGES in update_reasons:
            sections.extend(['contact_info', 'specialties'])
        if ContentUpdateReason.ROMAJI_INCONSISTENCY in update_reasons:
            sections.extend(['name_romaji', 'address_romaji'])
        if ContentUpdateReason.QUALITY_DECLINE in update_reasons:
            sections.extend(['services', 'experience'])
        
        return list(set(sections))  # Remove duplicates
    
    def _get_provider_data(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get specific provider data"""
        # Mock implementation
        return {
            'id': provider_id,
            'name': f'Provider {provider_id}',
            'description': f'Healthcare provider {provider_id}',
            'quality_score': 75.0
        }
    
    def _update_content_sections(self, provider_data: Dict[str, Any], sections: List[str]) -> Dict[str, Any]:
        """Update specific content sections"""
        # Mock implementation - would perform actual content updates
        updated_data = provider_data.copy()
        updated_data['last_updated'] = datetime.now()
        updated_data['description'] = f"Updated description for {provider_data.get('name', 'provider')}"
        return updated_data
    
    def _sync_to_wordpress(self, provider_data: Dict[str, Any]) -> bool:
        """Synchronize updated content to WordPress"""
        # Mock implementation - would perform actual WordPress sync
        return True
    
    def _save_updated_provider_data(self, provider_data: Dict[str, Any]):
        """Save updated provider data to database"""
        # Mock implementation - would save to actual database
        self.logger.info(f"Saved updated data for provider {provider_data.get('id')}")
    
    def _calculate_overall_freshness_score(self, content_metrics: Dict[str, ContentMetrics]) -> float:
        """Calculate overall content freshness score"""
        if not content_metrics:
            return 0.0
        
        freshness_scores = [m.freshness_score for m in content_metrics.values()]
        return sum(freshness_scores) / len(freshness_scores)
    
    def _calculate_romaji_consistency_score(self, content_metrics: Dict[str, ContentMetrics]) -> float:
        """Calculate overall romaji consistency score"""
        if not content_metrics:
            return 0.0
        
        consistent_count = len([m for m in content_metrics.values() if m.romaji_consistency])
        return (consistent_count / len(content_metrics)) * 100
    
    def _generate_lifecycle_recommendations(self, content_metrics: Dict[str, ContentMetrics], status_distribution: Dict[ContentStatus, int]) -> List[str]:
        """Generate actionable lifecycle recommendations"""
        recommendations = []
        
        total_providers = len(content_metrics)
        if total_providers == 0:
            return recommendations
        
        # Age-based recommendations
        outdated_count = status_distribution.get(ContentStatus.OUTDATED, 0)
        if outdated_count > total_providers * 0.2:
            recommendations.append(f"High priority: {outdated_count} providers have outdated content requiring immediate updates")
        
        # Quality-based recommendations
        low_quality_count = len([m for m in content_metrics.values() if m.quality_score < 70])
        if low_quality_count > 0:
            recommendations.append(f"Focus on {low_quality_count} providers with quality scores below 70")
        
        # Romaji consistency recommendations
        romaji_issues = len([m for m in content_metrics.values() if not m.romaji_consistency])
        if romaji_issues > 0:
            recommendations.append(f"Address romaji inconsistencies in {romaji_issues} provider records")
        
        # WordPress sync recommendations
        sync_failures = len([m for m in content_metrics.values() if not m.wordpress_sync_status])
        if sync_failures > 0:
            recommendations.append(f"Resolve WordPress sync failures for {sync_failures} providers")
        
        return recommendations
    
    def _project_next_month_needs(self, content_metrics: Dict[str, ContentMetrics]) -> Dict[str, Any]:
        """Project content update needs for next month"""
        aging_soon = len([m for m in content_metrics.values() if 20 <= m.content_age_days <= 40])
        high_priority = len([m for m in content_metrics.values() if m.quality_score < 75])
        
        return {
            'providers_aging_soon': aging_soon,
            'high_priority_updates': high_priority,
            'estimated_cost': min(aging_soon + high_priority, self.monthly_update_limit) * self.cost_per_update,
            'budget_required': min((aging_soon + high_priority) * self.cost_per_update, self.monthly_budget_limit)
        }
    
    def _save_lifecycle_report(self, report: ContentLifecycleReport):
        """Save lifecycle report to file"""
        try:
            report_data = {
                'report_id': report.report_id,
                'generated_at': report.generated_at.isoformat(),
                'total_providers': report.total_providers,
                'content_status_distribution': {k.value: v for k, v in report.content_status_distribution.items()},
                'priority_distribution': {k.value: v for k, v in report.priority_distribution.items()},
                'updates_completed_30d': report.updates_completed_30d,
                'updates_failed_30d': report.updates_failed_30d,
                'average_quality_improvement': report.average_quality_improvement,
                'cost_per_update': report.cost_per_update,
                'content_freshness_score': report.content_freshness_score,
                'romaji_consistency_score': report.romaji_consistency_score,
                'wordpress_sync_success_rate': report.wordpress_sync_success_rate,
                'recommended_actions': report.recommended_actions,
                'budget_utilization': report.budget_utilization,
                'projected_next_month': report.projected_next_month
            }
            
            report_filename = f"content_reports/lifecycle_report_{report.report_id}.json"
            with open(report_filename, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            self.logger.info(f"Content lifecycle report saved to {report_filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving lifecycle report: {e}")

# Integration functions
def integrate_with_maintenance_scheduling(lifecycle_manager: ContentLifecycleManager, maintenance_manager: MaintenanceModeManager):
    """Integrate content lifecycle with maintenance scheduling system"""
    try:
        # Create weekly content review task
        content_review_task = MaintenanceTask(
            task_id=f"content_review_{datetime.now().strftime('%Y%m%d')}",
            mode=MaintenanceMode.QUALITY_REVIEW,
            description="Weekly content lifecycle review and update planning",
            scheduled_time=datetime.now() + timedelta(days=2),  # Schedule for Wednesday
            estimated_duration_minutes=90
        )
        
        # Add to maintenance scheduler
        maintenance_manager.scheduler.scheduled_tasks.append(content_review_task)
        
        logging.info("Content lifecycle integrated with maintenance scheduling")
        return True
        
    except Exception as e:
        logging.error(f"Error integrating with maintenance scheduling: {e}")
        return False

def create_test_content_lifecycle_setup(delay_months: int = 6):
    """Create test content lifecycle setup with configurable delay period"""
    try:
        # Create delay configuration for testing
        delay_config = ContentUpdateDelayConfig(
            new_campaign_delay_months=delay_months,
            existing_provider_delay_months=12,
            quality_issue_delay_months=1,
            quality_issue_override=True,
            manual_update_override=True,
            critical_priority_override=True,
            critical_quality_threshold=60.0,
            quality_issue_threshold=70.0,
            recently_added_threshold_days=30,
            delay_evaluation_enabled=True
        )
        
        # Initialize with maintenance integration and delay config
        maintenance_manager = MaintenanceModeManager()
        lifecycle_manager = ContentLifecycleManager(maintenance_manager, delay_config)
        
        # Configure for testing
        lifecycle_manager.monthly_update_limit = 20
        lifecycle_manager.monthly_budget_limit = 200.0
        lifecycle_manager.cost_per_update = 2.00
        
        # Integrate with maintenance scheduling
        integrate_with_maintenance_scheduling(lifecycle_manager, maintenance_manager)
        
        logging.info(f"Created test content lifecycle setup with {delay_months} month delay")
        return lifecycle_manager
        
    except Exception as e:
        logging.error(f"Error creating test content lifecycle setup: {e}")
        return None

def create_aggressive_update_setup():
    """Create content lifecycle setup with aggressive updates (no delays for comparison)"""
    try:
        # Create configuration with delays disabled
        delay_config = ContentUpdateDelayConfig(
            new_campaign_delay_months=0,  # No delay
            existing_provider_delay_months=0,  # No delay
            quality_issue_delay_months=0,  # No delay
            delay_evaluation_enabled=False  # Disable delay evaluation entirely
        )
        
        maintenance_manager = MaintenanceModeManager()
        lifecycle_manager = ContentLifecycleManager(maintenance_manager, delay_config)
        
        # Standard testing configuration
        lifecycle_manager.monthly_update_limit = 50
        lifecycle_manager.monthly_budget_limit = 500.0
        lifecycle_manager.cost_per_update = 2.50
        
        logging.info("Created aggressive update setup with delays disabled")
        return lifecycle_manager
        
    except Exception as e:
        logging.error(f"Error creating aggressive update setup: {e}")
        return None

if __name__ == "__main__":
    # Test content lifecycle management
    print("Testing Content Lifecycle Management...")
    
    try:
        # Create test setup
        lifecycle_manager = create_test_content_lifecycle_setup()
        
        if lifecycle_manager:
            # Test content analysis
            content_metrics = lifecycle_manager.analyze_all_provider_content()
            print(f"✅ Analyzed {len(content_metrics)} providers")
            
            # Test update plan generation
            update_plans = lifecycle_manager.generate_update_plans(content_metrics, budget_limit=100.0)
            print(f"✅ Generated {len(update_plans)} update plans")
            
            # Test lifecycle report generation
            lifecycle_report = lifecycle_manager.generate_lifecycle_report()
            print(f"✅ Generated lifecycle report: {lifecycle_report.report_id}")
            
            print("\n🎉 Content Lifecycle Management System Successfully Initialized!")
            print(f"Total Providers: {lifecycle_report.total_providers}")
            print(f"Content Freshness Score: {lifecycle_report.content_freshness_score:.1f}")
            print(f"Romaji Consistency Score: {lifecycle_report.romaji_consistency_score:.1f}")
            print(f"WordPress Sync Success Rate: {lifecycle_report.wordpress_sync_success_rate:.1f}%")
        else:
            print("❌ Failed to initialize content lifecycle management system")
            
    except Exception as e:
        print(f"❌ Error during content lifecycle test: {e}")