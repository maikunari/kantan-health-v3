#!/usr/bin/env python3
"""
Campaign State Management for Healthcare Provider Collection
Tracks progress, costs, and enables pause/resume for 25-day campaign
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


@dataclass
class CampaignMetrics:
    """Daily and cumulative campaign metrics"""
    # Cumulative totals
    total_providers_found: int = 0
    total_providers_processed: int = 0
    total_providers_published: int = 0
    total_providers_rejected: int = 0
    
    # API costs (in USD)
    google_places_cost: float = 0.0
    claude_api_cost: float = 0.0
    total_cost: float = 0.0
    
    # Quality metrics
    avg_english_proficiency: float = 0.0
    providers_with_english: int = 0
    providers_with_content: int = 0
    
    # Daily metrics
    providers_today: int = 0
    cost_today: float = 0.0
    queries_today: int = 0
    
    # Time tracking
    campaign_start_date: str = ""
    last_update: str = ""
    estimated_completion_date: str = ""
    days_elapsed: int = 0
    days_remaining: int = 0
    
    def update_costs(self, google_searches: int = 0, claude_calls: int = 0):
        """Update cost tracking"""
        # Google Places: $0.032 per search
        google_cost = google_searches * 0.032
        self.google_places_cost += google_cost
        
        # Claude: ~$0.03 per provider (estimate based on token usage)
        claude_cost = claude_calls * 0.03
        self.claude_api_cost += claude_cost
        
        self.total_cost = self.google_places_cost + self.claude_api_cost
        self.cost_today += google_cost + claude_cost
        
        return self.total_cost


@dataclass
class QueryPerformance:
    """Track performance of individual query patterns"""
    query: str
    location: str
    specialty: str
    pattern_type: str
    
    # Results
    providers_found: int = 0
    providers_qualified: int = 0  # Passed English proficiency
    avg_english_score: float = 0.0
    
    # Status
    executed: bool = False
    execution_time: str = ""
    error: Optional[str] = None


@dataclass 
class CampaignState:
    """Complete campaign state for persistence"""
    # Campaign configuration
    campaign_id: str = ""
    target_providers: int = 5000
    daily_target: int = 200
    budget_limit: float = 600.0
    
    # Current state
    status: str = "initialized"  # initialized, running, paused, completed
    current_phase: str = "search"  # search, process, publish
    
    # Query management
    total_queries: int = 0
    completed_queries: int = 0
    current_query_index: int = 0
    query_queue: List[Dict] = field(default_factory=list)
    query_performance: List[QueryPerformance] = field(default_factory=list)
    
    # Progress tracking
    metrics: CampaignMetrics = field(default_factory=CampaignMetrics)
    
    # Checkpoint data
    last_checkpoint: str = ""
    checkpoint_interval: int = 50  # Save every 50 providers
    providers_since_checkpoint: int = 0
    
    # Protected providers (existing)
    protected_provider_ids: List[str] = field(default_factory=list)
    protected_count: int = 464  # Your existing providers
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'campaign_id': self.campaign_id,
            'target_providers': self.target_providers,
            'daily_target': self.daily_target,
            'budget_limit': self.budget_limit,
            'status': self.status,
            'current_phase': self.current_phase,
            'total_queries': self.total_queries,
            'completed_queries': self.completed_queries,
            'current_query_index': self.current_query_index,
            'query_queue': self.query_queue,
            'query_performance': [asdict(q) for q in self.query_performance],
            'metrics': asdict(self.metrics),
            'last_checkpoint': self.last_checkpoint,
            'checkpoint_interval': self.checkpoint_interval,
            'providers_since_checkpoint': self.providers_since_checkpoint,
            'protected_provider_ids': self.protected_provider_ids,
            'protected_count': self.protected_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CampaignState':
        """Create from dictionary (JSON deserialization)"""
        state = cls()
        
        # Simple fields
        for field in ['campaign_id', 'target_providers', 'daily_target', 
                     'budget_limit', 'status', 'current_phase',
                     'total_queries', 'completed_queries', 'current_query_index',
                     'last_checkpoint', 'checkpoint_interval', 
                     'providers_since_checkpoint', 'protected_count']:
            if field in data:
                setattr(state, field, data[field])
        
        # Lists
        state.query_queue = data.get('query_queue', [])
        state.protected_provider_ids = data.get('protected_provider_ids', [])
        
        # Complex objects
        if 'metrics' in data:
            state.metrics = CampaignMetrics(**data['metrics'])
        
        if 'query_performance' in data:
            state.query_performance = [
                QueryPerformance(**perf) for perf in data['query_performance']
            ]
        
        return state


class CampaignStateManager:
    """Manages campaign state persistence and recovery"""
    
    def __init__(self, state_file: str = 'campaign_state.json'):
        """Initialize state manager
        
        Args:
            state_file: Path to state persistence file
        """
        self.state_file = state_file
        self.state: Optional[CampaignState] = None
        self.backup_dir = 'campaign_checkpoints'
        
        # Create backup directory
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Load existing state or create new
        self.load_or_create_state()
    
    def load_or_create_state(self) -> CampaignState:
        """Load existing state or create new campaign"""
        if os.path.exists(self.state_file):
            try:
                self.state = self.load_state()
                logger.info(f"✅ Loaded existing campaign state")
                logger.info(f"   Progress: {self.state.metrics.total_providers_found}/{self.state.target_providers} providers")
                logger.info(f"   Queries: {self.state.completed_queries}/{self.state.total_queries} completed")
                logger.info(f"   Cost: ${self.state.metrics.total_cost:.2f}/${self.state.budget_limit:.2f}")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                self.state = self.create_new_campaign()
        else:
            self.state = self.create_new_campaign()
        
        return self.state
    
    def create_new_campaign(self) -> CampaignState:
        """Create a new campaign state"""
        logger.info("📋 Creating new campaign state")
        
        state = CampaignState(
            campaign_id=f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            target_providers=5000,
            daily_target=200,
            budget_limit=600.0,
            status='initialized'
        )
        
        # Set initial metrics
        state.metrics.campaign_start_date = datetime.now().isoformat()
        state.metrics.last_update = datetime.now().isoformat()
        
        # Calculate estimated completion
        days_needed = state.target_providers / state.daily_target
        state.metrics.estimated_completion_date = (
            datetime.now() + timedelta(days=days_needed)
        ).isoformat()
        
        self.state = state
        self.save_state()
        
        return state
    
    def load_state(self) -> CampaignState:
        """Load state from file"""
        with open(self.state_file, 'r') as f:
            data = json.load(f)
        
        return CampaignState.from_dict(data)
    
    def save_state(self):
        """Save current state to file"""
        if not self.state:
            return
        
        # Update last update time
        self.state.metrics.last_update = datetime.now().isoformat()
        
        # Save main state file
        with open(self.state_file, 'w') as f:
            json.dump(self.state.to_dict(), f, indent=2)
        
        # Check if checkpoint needed
        if self.state.providers_since_checkpoint >= self.state.checkpoint_interval:
            self.create_checkpoint()
            self.state.providers_since_checkpoint = 0
    
    def create_checkpoint(self):
        """Create a backup checkpoint"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        checkpoint_file = os.path.join(
            self.backup_dir, 
            f'checkpoint_{timestamp}.json'
        )
        
        with open(checkpoint_file, 'w') as f:
            json.dump(self.state.to_dict(), f, indent=2)
        
        self.state.last_checkpoint = checkpoint_file
        logger.info(f"💾 Checkpoint saved: {checkpoint_file}")
        
        # Keep only last 10 checkpoints
        self._cleanup_old_checkpoints()
    
    def _cleanup_old_checkpoints(self, keep_count: int = 10):
        """Remove old checkpoint files"""
        checkpoints = sorted([
            f for f in os.listdir(self.backup_dir)
            if f.startswith('checkpoint_')
        ])
        
        if len(checkpoints) > keep_count:
            for old_checkpoint in checkpoints[:-keep_count]:
                os.remove(os.path.join(self.backup_dir, old_checkpoint))
    
    def initialize_query_queue(self, queries: List[Dict]):
        """Initialize the query queue from enhanced search
        
        Args:
            queries: List of query dictionaries from generate_english_focused_queries()
        """
        self.state.query_queue = queries
        self.state.total_queries = len(queries)
        self.state.current_query_index = 0
        self.state.completed_queries = 0
        
        # Initialize performance tracking
        self.state.query_performance = []
        
        logger.info(f"📋 Initialized {len(queries)} queries in campaign queue")
        self.save_state()
    
    def get_next_query(self) -> Optional[Dict]:
        """Get the next query to execute"""
        if self.state.current_query_index < len(self.state.query_queue):
            return self.state.query_queue[self.state.current_query_index]
        return None
    
    def mark_query_completed(self, query: Dict, providers_found: int, 
                            providers_qualified: int, avg_english_score: float):
        """Mark a query as completed and track performance"""
        # Track performance
        perf = QueryPerformance(
            query=query['query'],
            location=query['location'],
            specialty=query['specialty'],
            pattern_type=query['pattern_type'],
            providers_found=providers_found,
            providers_qualified=providers_qualified,
            avg_english_score=avg_english_score,
            executed=True,
            execution_time=datetime.now().isoformat()
        )
        
        self.state.query_performance.append(perf)
        
        # Update counters
        self.state.current_query_index += 1
        self.state.completed_queries += 1
        self.state.metrics.queries_today += 1
        
        # Update cost
        self.state.metrics.update_costs(google_searches=1)
        
        self.save_state()
    
    def update_provider_metrics(self, providers_found: int = 0, 
                               providers_processed: int = 0,
                               providers_published: int = 0,
                               providers_rejected: int = 0,
                               english_scores: List[float] = None):
        """Update provider metrics"""
        metrics = self.state.metrics
        
        metrics.total_providers_found += providers_found
        metrics.total_providers_processed += providers_processed
        metrics.total_providers_published += providers_published
        metrics.total_providers_rejected += providers_rejected
        
        metrics.providers_today += providers_found
        
        # Update English proficiency average
        if english_scores:
            total_scores = (metrics.avg_english_proficiency * 
                          metrics.providers_with_english + sum(english_scores))
            metrics.providers_with_english += len(english_scores)
            metrics.avg_english_proficiency = total_scores / metrics.providers_with_english
        
        # Update checkpoint counter
        self.state.providers_since_checkpoint += providers_found
        
        # Calculate days remaining
        if metrics.providers_today > 0:
            current_rate = metrics.total_providers_found / max(1, metrics.days_elapsed)
            remaining = self.state.target_providers - metrics.total_providers_found
            metrics.days_remaining = int(remaining / max(1, current_rate))
            
            # Update estimated completion
            metrics.estimated_completion_date = (
                datetime.now() + timedelta(days=metrics.days_remaining)
            ).isoformat()
        
        self.save_state()
    
    def get_progress_summary(self) -> Dict:
        """Get current campaign progress summary"""
        metrics = self.state.metrics
        
        return {
            'campaign_id': self.state.campaign_id,
            'status': self.state.status,
            'progress': {
                'providers_found': metrics.total_providers_found,
                'target': self.state.target_providers,
                'percentage': (metrics.total_providers_found / self.state.target_providers * 100),
                'days_elapsed': metrics.days_elapsed,
                'days_remaining': metrics.days_remaining,
                'estimated_completion': metrics.estimated_completion_date
            },
            'queries': {
                'completed': self.state.completed_queries,
                'total': self.state.total_queries,
                'percentage': (self.state.completed_queries / max(1, self.state.total_queries) * 100)
            },
            'costs': {
                'total': metrics.total_cost,
                'budget': self.state.budget_limit,
                'percentage': (metrics.total_cost / self.state.budget_limit * 100),
                'google_places': metrics.google_places_cost,
                'claude_api': metrics.claude_api_cost
            },
            'quality': {
                'avg_english_proficiency': metrics.avg_english_proficiency,
                'providers_with_english': metrics.providers_with_english,
                'providers_with_content': metrics.providers_with_content
            },
            'daily': {
                'providers_today': metrics.providers_today,
                'cost_today': metrics.cost_today,
                'queries_today': metrics.queries_today,
                'daily_target': self.state.daily_target
            }
        }
    
    def pause_campaign(self):
        """Pause the campaign"""
        self.state.status = 'paused'
        logger.info("⏸️ Campaign paused")
        self.save_state()
    
    def resume_campaign(self):
        """Resume the campaign"""
        self.state.status = 'running'
        logger.info("▶️ Campaign resumed")
        self.save_state()
    
    def reset_daily_metrics(self):
        """Reset daily metrics (call at start of each day)"""
        self.state.metrics.providers_today = 0
        self.state.metrics.cost_today = 0
        self.state.metrics.queries_today = 0
        self.state.metrics.days_elapsed += 1
        self.save_state()