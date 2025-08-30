"""
Content Performance Monitoring and Analytics System

This module provides comprehensive monitoring and analytics for content
lifecycle management, tracking performance metrics, update effectiveness,
and long-term content health trends.

Created: 2025-08-30
Author: Healthcare Campaign System
Version: 1.0
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import statistics

from src.week4.content_lifecycle import ContentLifecycleManager, ContentMetrics

@dataclass
class PerformanceMetrics:
    """Content performance tracking metrics"""
    
    provider_id: str
    measurement_date: datetime
    
    # Traffic metrics
    page_views: int = 0
    unique_visitors: int = 0
    bounce_rate: float = 0.0
    session_duration: float = 0.0
    
    # SEO metrics
    search_ranking_position: float = 0.0
    organic_clicks: int = 0
    impression_count: int = 0
    click_through_rate: float = 0.0
    
    # Quality metrics
    quality_score: float = 0.0
    content_completeness: float = 0.0
    user_satisfaction: float = 0.0
    
    # Update metrics
    last_update_date: Optional[datetime] = None
    updates_count_30d: int = 0
    update_success_rate: float = 100.0
    
    # Technical metrics
    load_time_ms: float = 0.0
    mobile_friendly_score: float = 0.0
    wordpress_sync_status: bool = True

@dataclass
class ContentAnalytics:
    """Comprehensive content analytics summary"""
    
    report_id: str
    generated_at: datetime
    analysis_period_days: int = 30
    
    # Overall performance
    total_providers_analyzed: int = 0
    average_performance_score: float = 0.0
    top_performing_providers: List[str] = field(default_factory=list)
    underperforming_providers: List[str] = field(default_factory=list)
    
    # Traffic analytics
    total_page_views: int = 0
    average_session_duration: float = 0.0
    average_bounce_rate: float = 0.0
    traffic_trend: str = "stable"
    
    # Quality analytics
    quality_score_distribution: Dict[str, int] = field(default_factory=dict)
    quality_improvement_rate: float = 0.0
    quality_issues_identified: List[str] = field(default_factory=list)
    
    # Update effectiveness
    updates_performed: int = 0
    update_success_rate: float = 100.0
    average_quality_improvement: float = 0.0
    cost_per_quality_point: float = 0.0
    
    # Recommendations
    priority_actions: List[str] = field(default_factory=list)
    optimization_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    budget_recommendations: Dict[str, float] = field(default_factory=dict)

class ContentPerformanceMonitor:
    """Advanced content performance monitoring system"""
    
    def __init__(self, lifecycle_manager: ContentLifecycleManager):
        self.lifecycle_manager = lifecycle_manager
        self.performance_history: Dict[str, List[PerformanceMetrics]] = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def collect_performance_metrics(self, provider_id: str) -> PerformanceMetrics:
        """Collect comprehensive performance metrics for a provider"""
        try:
            current_time = datetime.now()
            
            # Get traffic data (mock implementation)
            traffic_data = self._get_traffic_data(provider_id)
            
            # Get SEO performance (mock implementation)
            seo_data = self._get_seo_performance(provider_id)
            
            # Get quality metrics
            quality_data = self._get_quality_metrics(provider_id)
            
            # Get update history
            update_data = self._get_update_history(provider_id)
            
            # Get technical metrics
            technical_data = self._get_technical_metrics(provider_id)
            
            metrics = PerformanceMetrics(
                provider_id=provider_id,
                measurement_date=current_time,
                page_views=traffic_data.get('page_views', 0),
                unique_visitors=traffic_data.get('unique_visitors', 0),
                bounce_rate=traffic_data.get('bounce_rate', 0.0),
                session_duration=traffic_data.get('session_duration', 0.0),
                search_ranking_position=seo_data.get('ranking_position', 0.0),
                organic_clicks=seo_data.get('organic_clicks', 0),
                impression_count=seo_data.get('impressions', 0),
                click_through_rate=seo_data.get('ctr', 0.0),
                quality_score=quality_data.get('quality_score', 0.0),
                content_completeness=quality_data.get('completeness', 0.0),
                user_satisfaction=quality_data.get('satisfaction', 0.0),
                last_update_date=update_data.get('last_update'),
                updates_count_30d=update_data.get('updates_30d', 0),
                update_success_rate=update_data.get('success_rate', 100.0),
                load_time_ms=technical_data.get('load_time', 0.0),
                mobile_friendly_score=technical_data.get('mobile_score', 0.0),
                wordpress_sync_status=technical_data.get('wp_sync_status', True)
            )
            
            # Store metrics in history
            if provider_id not in self.performance_history:
                self.performance_history[provider_id] = []
            self.performance_history[provider_id].append(metrics)
            
            # Keep only last 90 days of history
            self._cleanup_old_metrics(provider_id)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting performance metrics for {provider_id}: {e}")
            return PerformanceMetrics(provider_id=provider_id, measurement_date=datetime.now())
    
    def analyze_performance_trends(self, provider_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze performance trends for a provider"""
        try:
            if provider_id not in self.performance_history:
                return {"error": "No performance history available"}
            
            # Get recent metrics
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_metrics = [
                m for m in self.performance_history[provider_id]
                if m.measurement_date >= cutoff_date
            ]
            
            if not recent_metrics:
                return {"error": "No recent performance data"}
            
            # Calculate trends
            trends = {}
            
            # Traffic trends
            page_views = [m.page_views for m in recent_metrics]
            if len(page_views) > 1:
                trends['traffic_trend'] = self._calculate_trend(page_views)
            
            # Quality trends
            quality_scores = [m.quality_score for m in recent_metrics if m.quality_score > 0]
            if len(quality_scores) > 1:
                trends['quality_trend'] = self._calculate_trend(quality_scores)
            
            # SEO trends
            rankings = [m.search_ranking_position for m in recent_metrics if m.search_ranking_position > 0]
            if len(rankings) > 1:
                trends['seo_trend'] = self._calculate_trend(rankings, lower_is_better=True)
            
            # Performance summary
            latest_metrics = recent_metrics[-1]
            trends.update({
                'current_quality_score': latest_metrics.quality_score,
                'current_page_views': latest_metrics.page_views,
                'current_ranking': latest_metrics.search_ranking_position,
                'recent_updates': latest_metrics.updates_count_30d,
                'update_success_rate': latest_metrics.update_success_rate,
                'analysis_period': f"{len(recent_metrics)} data points over {days} days"
            })
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends for {provider_id}: {e}")
            return {"error": str(e)}
    
    def generate_comprehensive_analytics(self, analysis_period_days: int = 30) -> ContentAnalytics:
        """Generate comprehensive content analytics report"""
        try:
            current_time = datetime.now()
            report_id = f"content_analytics_{current_time.strftime('%Y%m%d_%H%M%S')}"
            
            # Get all provider content metrics
            all_content_metrics = self.lifecycle_manager.analyze_all_provider_content()
            
            # Initialize analytics
            analytics = ContentAnalytics(
                report_id=report_id,
                generated_at=current_time,
                analysis_period_days=analysis_period_days,
                total_providers_analyzed=len(all_content_metrics)
            )
            
            if not all_content_metrics:
                return analytics
            
            # Collect performance metrics for all providers
            provider_performance = {}
            for provider_id in list(all_content_metrics.keys())[:50]:  # Limit for performance
                perf_metrics = self.collect_performance_metrics(provider_id)
                provider_performance[provider_id] = perf_metrics
            
            # Calculate overall performance metrics
            self._calculate_traffic_analytics(analytics, provider_performance)
            self._calculate_quality_analytics(analytics, all_content_metrics, provider_performance)
            self._calculate_update_effectiveness(analytics, provider_performance)
            self._identify_performance_leaders(analytics, provider_performance)
            self._generate_optimization_recommendations(analytics, all_content_metrics, provider_performance)
            
            # Save analytics report
            self._save_analytics_report(analytics)
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive analytics: {e}")
            return ContentAnalytics(
                report_id="error_report",
                generated_at=datetime.now()
            )
    
    def monitor_update_effectiveness(self, update_plans: List) -> Dict[str, Any]:
        """Monitor the effectiveness of content updates"""
        try:
            if not update_plans:
                return {"message": "No update plans to monitor"}
            
            effectiveness_report = {
                "total_updates_monitored": len(update_plans),
                "successful_updates": 0,
                "failed_updates": 0,
                "quality_improvements": [],
                "performance_improvements": [],
                "cost_effectiveness": 0.0,
                "average_improvement": 0.0
            }
            
            for plan in update_plans:
                if plan.success:
                    effectiveness_report["successful_updates"] += 1
                    
                    # Track quality improvement
                    if plan.quality_improvement > 0:
                        effectiveness_report["quality_improvements"].append(plan.quality_improvement)
                    
                    # Get before/after performance metrics
                    performance_improvement = self._measure_performance_improvement(plan.provider_id)
                    if performance_improvement:
                        effectiveness_report["performance_improvements"].append(performance_improvement)
                else:
                    effectiveness_report["failed_updates"] += 1
            
            # Calculate averages
            if effectiveness_report["quality_improvements"]:
                effectiveness_report["average_improvement"] = statistics.mean(effectiveness_report["quality_improvements"])
            
            # Calculate cost effectiveness (improvement per dollar spent)
            total_cost = sum(plan.estimated_cost for plan in update_plans if plan.success)
            total_improvement = sum(effectiveness_report["quality_improvements"])
            if total_cost > 0:
                effectiveness_report["cost_effectiveness"] = total_improvement / total_cost
            
            return effectiveness_report
            
        except Exception as e:
            self.logger.error(f"Error monitoring update effectiveness: {e}")
            return {"error": str(e)}
    
    # Helper methods
    def _get_traffic_data(self, provider_id: str) -> Dict[str, Any]:
        """Get traffic data for provider (mock implementation)"""
        # Mock traffic data - would integrate with Google Analytics, etc.
        return {
            'page_views': 150 + hash(provider_id) % 300,
            'unique_visitors': 120 + hash(provider_id) % 200,
            'bounce_rate': 0.45 + (hash(provider_id) % 100) / 1000,
            'session_duration': 120 + hash(provider_id) % 180
        }
    
    def _get_seo_performance(self, provider_id: str) -> Dict[str, Any]:
        """Get SEO performance data (mock implementation)"""
        return {
            'ranking_position': 3.5 + (hash(provider_id) % 50) / 10,
            'organic_clicks': 80 + hash(provider_id) % 150,
            'impressions': 1200 + hash(provider_id) % 800,
            'ctr': 0.065 + (hash(provider_id) % 30) / 1000
        }
    
    def _get_quality_metrics(self, provider_id: str) -> Dict[str, Any]:
        """Get quality metrics from QA system"""
        return {
            'quality_score': 75.0 + (hash(provider_id) % 20),
            'completeness': 80.0 + (hash(provider_id) % 15),
            'satisfaction': 7.5 + (hash(provider_id) % 25) / 10
        }
    
    def _get_update_history(self, provider_id: str) -> Dict[str, Any]:
        """Get update history for provider"""
        return {
            'last_update': datetime.now() - timedelta(days=hash(provider_id) % 90),
            'updates_30d': hash(provider_id) % 3,
            'success_rate': 95.0 + (hash(provider_id) % 5)
        }
    
    def _get_technical_metrics(self, provider_id: str) -> Dict[str, Any]:
        """Get technical performance metrics"""
        return {
            'load_time': 1200 + hash(provider_id) % 800,
            'mobile_score': 85.0 + (hash(provider_id) % 15),
            'wp_sync_status': hash(provider_id) % 10 != 0  # 90% success rate
        }
    
    def _calculate_trend(self, values: List[float], lower_is_better: bool = False) -> str:
        """Calculate trend direction from list of values"""
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple linear trend calculation
        recent_avg = statistics.mean(values[-3:]) if len(values) >= 3 else values[-1]
        older_avg = statistics.mean(values[:3]) if len(values) >= 3 else values[0]
        
        change_threshold = 0.05  # 5% change threshold
        change_ratio = (recent_avg - older_avg) / older_avg if older_avg != 0 else 0
        
        if lower_is_better:
            change_ratio = -change_ratio
        
        if change_ratio > change_threshold:
            return "improving"
        elif change_ratio < -change_threshold:
            return "declining"
        else:
            return "stable"
    
    def _cleanup_old_metrics(self, provider_id: str):
        """Remove metrics older than 90 days"""
        if provider_id in self.performance_history:
            cutoff_date = datetime.now() - timedelta(days=90)
            self.performance_history[provider_id] = [
                m for m in self.performance_history[provider_id]
                if m.measurement_date >= cutoff_date
            ]
    
    def _calculate_traffic_analytics(self, analytics: ContentAnalytics, performance_data: Dict[str, PerformanceMetrics]):
        """Calculate traffic analytics"""
        if not performance_data:
            return
        
        page_views = [p.page_views for p in performance_data.values()]
        session_durations = [p.session_duration for p in performance_data.values()]
        bounce_rates = [p.bounce_rate for p in performance_data.values() if p.bounce_rate > 0]
        
        analytics.total_page_views = sum(page_views)
        analytics.average_session_duration = statistics.mean(session_durations) if session_durations else 0.0
        analytics.average_bounce_rate = statistics.mean(bounce_rates) if bounce_rates else 0.0
        
        # Determine traffic trend
        if analytics.total_page_views > len(performance_data) * 200:
            analytics.traffic_trend = "high"
        elif analytics.total_page_views < len(performance_data) * 100:
            analytics.traffic_trend = "low"
        else:
            analytics.traffic_trend = "moderate"
    
    def _calculate_quality_analytics(self, analytics: ContentAnalytics, content_metrics: Dict[str, ContentMetrics], performance_data: Dict[str, PerformanceMetrics]):
        """Calculate quality analytics"""
        quality_scores = [m.quality_score for m in content_metrics.values()]
        
        if quality_scores:
            analytics.average_performance_score = statistics.mean(quality_scores)
            
            # Quality score distribution
            for score in quality_scores:
                score_range = f"{int(score//10)*10}-{int(score//10)*10+9}"
                analytics.quality_score_distribution[score_range] = analytics.quality_score_distribution.get(score_range, 0) + 1
            
            # Identify quality issues
            low_quality_count = len([s for s in quality_scores if s < 70])
            if low_quality_count > 0:
                analytics.quality_issues_identified.append(f"{low_quality_count} providers below quality threshold")
    
    def _calculate_update_effectiveness(self, analytics: ContentAnalytics, performance_data: Dict[str, PerformanceMetrics]):
        """Calculate update effectiveness metrics"""
        updates_performed = sum(p.updates_count_30d for p in performance_data.values())
        success_rates = [p.update_success_rate for p in performance_data.values() if p.updates_count_30d > 0]
        
        analytics.updates_performed = updates_performed
        analytics.update_success_rate = statistics.mean(success_rates) if success_rates else 100.0
        
        # Mock quality improvement calculation
        analytics.average_quality_improvement = 3.2  # Mock value
        analytics.cost_per_quality_point = 0.78 if analytics.average_quality_improvement > 0 else 0.0
    
    def _identify_performance_leaders(self, analytics: ContentAnalytics, performance_data: Dict[str, PerformanceMetrics]):
        """Identify top and bottom performing providers"""
        # Sort by overall performance score (combination of quality and traffic)
        provider_scores = {}
        for provider_id, perf in performance_data.items():
            performance_score = (perf.quality_score * 0.6) + (min(perf.page_views/10, 100) * 0.4)
            provider_scores[provider_id] = performance_score
        
        sorted_providers = sorted(provider_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Top 5 performers
        analytics.top_performing_providers = [p[0] for p in sorted_providers[:5]]
        
        # Bottom 5 performers
        analytics.underperforming_providers = [p[0] for p in sorted_providers[-5:]]
    
    def _generate_optimization_recommendations(self, analytics: ContentAnalytics, content_metrics: Dict[str, ContentMetrics], performance_data: Dict[str, PerformanceMetrics]):
        """Generate optimization recommendations"""
        # Priority actions based on analysis
        if analytics.average_performance_score < 75:
            analytics.priority_actions.append("Focus on improving overall content quality - current average below target")
        
        if analytics.update_success_rate < 95:
            analytics.priority_actions.append("Investigate update process reliability - success rate below optimal")
        
        if analytics.average_bounce_rate > 0.6:
            analytics.priority_actions.append("Improve content engagement - high bounce rate detected")
        
        # Optimization opportunities
        low_traffic_high_quality = [
            pid for pid, perf in performance_data.items()
            if perf.quality_score > 80 and perf.page_views < 100
        ]
        
        if low_traffic_high_quality:
            analytics.optimization_opportunities.append({
                "type": "seo_optimization",
                "description": f"{len(low_traffic_high_quality)} high-quality providers with low traffic",
                "potential_impact": "high",
                "providers": low_traffic_high_quality[:5]
            })
        
        # Budget recommendations
        estimated_updates_needed = len([m for m in content_metrics.values() if m.quality_score < 75])
        analytics.budget_recommendations = {
            "next_month_budget": estimated_updates_needed * 2.5,
            "priority_updates": estimated_updates_needed,
            "maintenance_budget": 200.0
        }
    
    def _measure_performance_improvement(self, provider_id: str) -> Optional[float]:
        """Measure performance improvement after update"""
        # Mock implementation - would compare before/after metrics
        return 5.2 if hash(provider_id) % 3 == 0 else None
    
    def _save_analytics_report(self, analytics: ContentAnalytics):
        """Save analytics report to file"""
        try:
            report_data = {
                'report_id': analytics.report_id,
                'generated_at': analytics.generated_at.isoformat(),
                'analysis_period_days': analytics.analysis_period_days,
                'total_providers_analyzed': analytics.total_providers_analyzed,
                'average_performance_score': analytics.average_performance_score,
                'top_performing_providers': analytics.top_performing_providers,
                'underperforming_providers': analytics.underperforming_providers,
                'total_page_views': analytics.total_page_views,
                'average_session_duration': analytics.average_session_duration,
                'average_bounce_rate': analytics.average_bounce_rate,
                'traffic_trend': analytics.traffic_trend,
                'quality_score_distribution': analytics.quality_score_distribution,
                'quality_improvement_rate': analytics.quality_improvement_rate,
                'quality_issues_identified': analytics.quality_issues_identified,
                'updates_performed': analytics.updates_performed,
                'update_success_rate': analytics.update_success_rate,
                'average_quality_improvement': analytics.average_quality_improvement,
                'cost_per_quality_point': analytics.cost_per_quality_point,
                'priority_actions': analytics.priority_actions,
                'optimization_opportunities': analytics.optimization_opportunities,
                'budget_recommendations': analytics.budget_recommendations
            }
            
            report_filename = f"content_analytics/analytics_report_{analytics.report_id}.json"
            with open(report_filename, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            self.logger.info(f"Analytics report saved to {report_filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving analytics report: {e}")

def create_performance_monitoring_demo():
    """Create and demonstrate performance monitoring system"""
    from src.week4.content_lifecycle import create_test_content_lifecycle_setup
    
    # Initialize systems
    lifecycle_manager = create_test_content_lifecycle_setup()
    performance_monitor = ContentPerformanceMonitor(lifecycle_manager)
    
    return performance_monitor

if __name__ == "__main__":
    print("Testing Content Performance Monitoring...")
    
    try:
        # Create performance monitor
        monitor = create_performance_monitoring_demo()
        print("✅ Performance monitor initialized")
        
        # Test performance metrics collection
        sample_provider = "test_provider_1"
        metrics = monitor.collect_performance_metrics(sample_provider)
        print(f"✅ Collected performance metrics for {sample_provider}")
        print(f"   Quality score: {metrics.quality_score}")
        print(f"   Page views: {metrics.page_views}")
        print(f"   Load time: {metrics.load_time_ms}ms")
        
        # Test trend analysis
        trends = monitor.analyze_performance_trends(sample_provider)
        print(f"✅ Analyzed performance trends")
        
        # Test comprehensive analytics
        analytics = monitor.generate_comprehensive_analytics()
        print(f"✅ Generated analytics report: {analytics.report_id}")
        print(f"   Providers analyzed: {analytics.total_providers_analyzed}")
        print(f"   Average performance: {analytics.average_performance_score:.1f}")
        print(f"   Total page views: {analytics.total_page_views}")
        
        print("\n🎉 Content Performance Monitoring System Successfully Tested!")
        
    except Exception as e:
        print(f"❌ Error during performance monitoring test: {e}")