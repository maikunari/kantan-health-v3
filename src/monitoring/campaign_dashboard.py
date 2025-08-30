#!/usr/bin/env python3
"""
Campaign Monitoring Dashboard System
Real-time tracking of healthcare provider collection campaign progress
"""

import os
import sys
import json
import logging
import psutil
import time
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import DatabaseManager
from src.campaign.campaign_state import CampaignStateManager
from src.publishers.wordpress import WordPressPublisher
from src.utils.romaji_converter import contains_japanese

logger = logging.getLogger(__name__)


@dataclass
class DashboardMetrics:
    """Real-time dashboard metrics"""
    # Campaign Progress
    campaign_completion_percent: float = 0.0
    providers_collected_today: int = 0
    providers_processed_today: int = 0
    providers_published_today: int = 0
    daily_target_achievement: float = 0.0  # Percentage of 200/day target
    
    # Cumulative Totals
    total_providers: int = 0
    total_processed: int = 0
    total_published: int = 0
    total_with_content: int = 0
    
    # Quality Metrics
    avg_english_proficiency: float = 0.0
    providers_high_english: int = 0  # Score >= 4
    providers_moderate_english: int = 0  # Score 2-3
    providers_low_english: int = 0  # Score < 2
    romaji_conversion_success: float = 100.0  # Percentage
    
    # Geographic Distribution
    cities_covered: int = 0
    top_cities: List[Dict[str, Any]] = None
    locations_needing_review: int = 0
    
    # Specialty Distribution
    specialties_covered: int = 0
    top_specialties: List[Dict[str, Any]] = None
    specialties_needing_review: int = 0
    
    # Master Data Validation
    location_validation_success: float = 100.0
    specialty_validation_success: float = 100.0
    providers_needing_manual_review: int = 0
    
    # Cost Analysis
    total_cost: float = 0.0
    cost_today: float = 0.0
    google_places_cost: float = 0.0
    claude_api_cost: float = 0.0
    cost_per_provider: float = 0.0
    projected_total_cost: float = 0.0
    budget_utilization: float = 0.0  # Percentage of $600 budget
    
    # Timeline Projections
    estimated_completion_date: str = ""
    days_remaining: int = 0
    current_daily_rate: float = 0.0
    required_daily_rate: float = 200.0
    
    # System Health
    database_status: str = "unknown"
    wordpress_status: str = "unknown"
    google_api_status: str = "unknown"
    system_memory_usage: float = 0.0
    avg_processing_time: float = 0.0
    
    def __post_init__(self):
        if self.top_cities is None:
            self.top_cities = []
        if self.top_specialties is None:
            self.top_specialties = []


class CampaignDashboard:
    """Real-time campaign monitoring dashboard"""
    
    def __init__(self, state_file: str = 'campaign_state.json'):
        """Initialize dashboard with data sources
        
        Args:
            state_file: Path to campaign state file
        """
        self.state_manager = CampaignStateManager(state_file)
        self.db = DatabaseManager()
        self.wp_publisher = WordPressPublisher()
        
        # Dashboard configuration
        self.campaign_target = 5000  # Total providers target
        self.daily_target = 200  # Providers per day target
        self.budget_limit = 600.0  # Total budget in USD
        self.campaign_days = 25  # Expected campaign duration
        
        logger.info("✅ Campaign Dashboard initialized")
    
    def get_real_time_metrics(self) -> DashboardMetrics:
        """Generate real-time dashboard metrics"""
        logger.info("📊 Generating real-time dashboard metrics...")
        
        metrics = DashboardMetrics()
        
        # Get campaign state
        state = self.state_manager.state
        
        try:
            # Campaign Progress Metrics
            metrics.total_providers = state.metrics.total_providers_found
            metrics.total_processed = state.metrics.total_providers_processed
            metrics.total_published = state.metrics.total_providers_published
            metrics.total_with_content = state.metrics.providers_with_content
            
            metrics.campaign_completion_percent = (metrics.total_providers / self.campaign_target) * 100
            
            # Daily metrics from state
            metrics.providers_collected_today = state.metrics.providers_today
            metrics.cost_today = state.metrics.cost_today
            metrics.daily_target_achievement = (metrics.providers_collected_today / self.daily_target) * 100
            
            # Cost Analysis
            metrics.total_cost = state.metrics.total_cost
            metrics.google_places_cost = state.metrics.google_places_cost
            metrics.claude_api_cost = state.metrics.claude_api_cost
            metrics.budget_utilization = (metrics.total_cost / self.budget_limit) * 100
            
            if metrics.total_providers > 0:
                metrics.cost_per_provider = metrics.total_cost / metrics.total_providers
                metrics.projected_total_cost = metrics.cost_per_provider * self.campaign_target
            
            # Quality metrics from state
            metrics.avg_english_proficiency = state.metrics.avg_english_proficiency
            metrics.providers_high_english = state.metrics.providers_with_english
            
            # Timeline projections
            if state.metrics.campaign_start_date:
                start_date = datetime.fromisoformat(state.metrics.campaign_start_date)
                days_elapsed = (datetime.now() - start_date).days + 1
                
                if days_elapsed > 0:
                    metrics.current_daily_rate = metrics.total_providers / days_elapsed
                    
                    if metrics.current_daily_rate > 0:
                        remaining_providers = self.campaign_target - metrics.total_providers
                        estimated_days = remaining_providers / metrics.current_daily_rate
                        completion_date = datetime.now() + timedelta(days=estimated_days)
                        metrics.estimated_completion_date = completion_date.strftime('%Y-%m-%d')
                        metrics.days_remaining = int(estimated_days)
            
            # Get detailed database metrics
            self._update_database_metrics(metrics)
            
            # Get geographic and specialty distribution
            self._update_geographic_metrics(metrics)
            self._update_specialty_metrics(metrics)
            
            # Update system health
            self._update_health_metrics(metrics)
            
            # Master data validation metrics
            self._update_validation_metrics(metrics)
            
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            import traceback
            traceback.print_exc()
        
        logger.info("✅ Dashboard metrics generated")
        return metrics
    
    def _update_database_metrics(self, metrics: DashboardMetrics):
        """Update metrics from database queries"""
        try:
            # Test database connection
            session = self.db.get_session()
            
            # Get English proficiency distribution
            from src.core.models import Provider
            from sqlalchemy import func, and_
            
            # English proficiency distribution
            high_english = session.query(Provider).filter(Provider.proficiency_score >= 4).count()
            moderate_english = session.query(Provider).filter(
                and_(Provider.proficiency_score >= 2, Provider.proficiency_score < 4)
            ).count()
            low_english = session.query(Provider).filter(Provider.proficiency_score < 2).count()
            
            metrics.providers_high_english = high_english
            metrics.providers_moderate_english = moderate_english
            metrics.providers_low_english = low_english
            
            # Romaji conversion success rate
            total_providers = session.query(Provider).count()
            japanese_providers = 0
            romaji_success = 0
            
            if total_providers > 0:
                # Sample providers to check romaji conversion
                providers = session.query(Provider).limit(100).all()
                for provider in providers:
                    if contains_japanese(provider.provider_name):
                        japanese_providers += 1
                        # Check if has romaji or content uses English
                        if (hasattr(provider, 'provider_name_romaji') and provider.provider_name_romaji) or \
                           (provider.ai_description and not contains_japanese(provider.ai_description)):
                            romaji_success += 1
                
                if japanese_providers > 0:
                    metrics.romaji_conversion_success = (romaji_success / japanese_providers) * 100
            
            metrics.database_status = "connected"
            session.close()
            
        except Exception as e:
            logger.error(f"Database metrics error: {e}")
            metrics.database_status = "error"
    
    def _update_geographic_metrics(self, metrics: DashboardMetrics):
        """Update geographic distribution metrics"""
        try:
            session = self.db.get_session()
            from src.core.models import Provider
            from sqlalchemy import func
            
            # City distribution
            city_counts = session.query(
                Provider.city,
                func.count(Provider.id).label('count')
            ).filter(
                Provider.city.isnot(None)
            ).group_by(Provider.city).order_by(
                func.count(Provider.id).desc()
            ).limit(10).all()
            
            metrics.cities_covered = session.query(func.count(func.distinct(Provider.city))).scalar() or 0
            metrics.top_cities = [
                {'name': city, 'count': count} 
                for city, count in city_counts
            ]
            
            # Count providers needing location review
            if hasattr(Provider, 'location_needs_review'):
                metrics.locations_needing_review = session.query(Provider).filter(
                    Provider.location_needs_review == True
                ).count()
            
            session.close()
            
        except Exception as e:
            logger.error(f"Geographic metrics error: {e}")
    
    def _update_specialty_metrics(self, metrics: DashboardMetrics):
        """Update specialty distribution metrics"""
        try:
            session = self.db.get_session()
            from src.core.models import Provider
            from sqlalchemy import func
            
            # Get primary specialty distribution
            if hasattr(Provider, 'primary_specialty'):
                specialty_counts = session.query(
                    Provider.primary_specialty,
                    func.count(Provider.id).label('count')
                ).filter(
                    Provider.primary_specialty.isnot(None)
                ).group_by(Provider.primary_specialty).order_by(
                    func.count(Provider.id).desc()
                ).limit(10).all()
                
                metrics.specialties_covered = session.query(
                    func.count(func.distinct(Provider.primary_specialty))
                ).scalar() or 0
                
                metrics.top_specialties = [
                    {'name': specialty, 'count': count}
                    for specialty, count in specialty_counts
                ]
                
                # Count providers needing specialty review
                if hasattr(Provider, 'specialties_need_review'):
                    metrics.specialties_needing_review = session.query(Provider).filter(
                        Provider.specialties_need_review == True
                    ).count()
            
            session.close()
            
        except Exception as e:
            logger.error(f"Specialty metrics error: {e}")
    
    def _update_validation_metrics(self, metrics: DashboardMetrics):
        """Update master data validation metrics"""
        try:
            session = self.db.get_session()
            from src.core.models import Provider
            
            total_providers = session.query(Provider).count()
            
            if total_providers > 0:
                # Location validation success rate
                if hasattr(Provider, 'location_needs_review'):
                    locations_valid = session.query(Provider).filter(
                        Provider.location_needs_review == False
                    ).count()
                    metrics.location_validation_success = (locations_valid / total_providers) * 100
                
                # Specialty validation success rate
                if hasattr(Provider, 'specialties_need_review'):
                    specialties_valid = session.query(Provider).filter(
                        Provider.specialties_need_review == False
                    ).count()
                    metrics.specialty_validation_success = (specialties_valid / total_providers) * 100
                
                # Providers needing manual review
                if hasattr(Provider, 'needs_manual_review'):
                    metrics.providers_needing_manual_review = session.query(Provider).filter(
                        Provider.needs_manual_review == True
                    ).count()
            
            session.close()
            
        except Exception as e:
            logger.error(f"Validation metrics error: {e}")
    
    def _update_health_metrics(self, metrics: DashboardMetrics):
        """Update system health metrics"""
        try:
            # System memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            metrics.system_memory_usage = memory_info.rss / (1024 * 1024)  # MB
            
            # Test WordPress connection
            wp_test = self.wp_publisher.test_connection()
            metrics.wordpress_status = "connected" if wp_test.get('success') else "error"
            
            # Google API status (based on recent usage)
            state = self.state_manager.state
            if state.metrics.cost_today > 0:
                metrics.google_api_status = "active"
            else:
                metrics.google_api_status = "idle"
            
        except Exception as e:
            logger.error(f"Health metrics error: {e}")
            metrics.wordpress_status = "error"
            metrics.google_api_status = "error"
    
    def generate_dashboard_report(self) -> str:
        """Generate comprehensive dashboard report"""
        metrics = self.get_real_time_metrics()
        
        report = f"""
🏥 HEALTHCARE PROVIDER CAMPAIGN DASHBOARD
📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'=' * 60}
📊 CAMPAIGN PROGRESS
{'=' * 60}
Overall Progress: {metrics.campaign_completion_percent:.1f}% ({metrics.total_providers:,}/{self.campaign_target:,})
Daily Target: {metrics.providers_collected_today}/{self.daily_target} ({metrics.daily_target_achievement:.1f}%)

Providers Status:
  • Total Found: {metrics.total_providers:,}
  • Processed: {metrics.total_processed:,}
  • With Content: {metrics.total_with_content:,}
  • Published: {metrics.total_published:,}

{'=' * 60}
💰 BUDGET & COSTS
{'=' * 60}
Total Cost: ${metrics.total_cost:.2f} / ${self.budget_limit:.2f} ({metrics.budget_utilization:.1f}%)
Cost Today: ${metrics.cost_today:.2f}
Cost per Provider: ${metrics.cost_per_provider:.2f}
Projected Total: ${metrics.projected_total_cost:.2f}

Cost Breakdown:
  • Google Places API: ${metrics.google_places_cost:.2f}
  • Claude API: ${metrics.claude_api_cost:.2f}

{'=' * 60}
🌟 QUALITY METRICS
{'=' * 60}
Average English Proficiency: {metrics.avg_english_proficiency:.1f}/5
English Distribution:
  • High (4-5): {metrics.providers_high_english:,} providers
  • Moderate (2-3): {metrics.providers_moderate_english:,} providers
  • Low (0-1): {metrics.providers_low_english:,} providers

Romaji Conversion Success: {metrics.romaji_conversion_success:.1f}%

{'=' * 60}
🗺️ GEOGRAPHIC COVERAGE
{'=' * 60}
Cities Covered: {metrics.cities_covered}
Locations Needing Review: {metrics.locations_needing_review}

Top Cities:"""

        for city in metrics.top_cities[:5]:
            report += f"\n  • {city['name']}: {city['count']} providers"

        report += f"""

{'=' * 60}
🏥 SPECIALTY DISTRIBUTION
{'=' * 60}
Specialties Covered: {metrics.specialties_covered}
Specialties Needing Review: {metrics.specialties_needing_review}

Top Specialties:"""

        for specialty in metrics.top_specialties[:5]:
            report += f"\n  • {specialty['name']}: {specialty['count']} providers"

        report += f"""

{'=' * 60}
✅ MASTER DATA VALIDATION
{'=' * 60}
Location Validation: {metrics.location_validation_success:.1f}% success rate
Specialty Validation: {metrics.specialty_validation_success:.1f}% success rate
Providers Needing Manual Review: {metrics.providers_needing_manual_review}

{'=' * 60}
⏱️ TIMELINE PROJECTION
{'=' * 60}
Current Daily Rate: {metrics.current_daily_rate:.1f} providers/day
Required Daily Rate: {metrics.required_daily_rate:.1f} providers/day
Estimated Completion: {metrics.estimated_completion_date}
Days Remaining: {metrics.days_remaining}

{'=' * 60}
💻 SYSTEM HEALTH
{'=' * 60}
Database: {metrics.database_status}
WordPress: {metrics.wordpress_status}
Google API: {metrics.google_api_status}
Memory Usage: {metrics.system_memory_usage:.1f} MB

{'=' * 60}
📈 PERFORMANCE SUMMARY
{'=' * 60}"""

        # Performance summary
        if metrics.campaign_completion_percent >= 20:
            status = "🟢 ON TRACK"
        elif metrics.campaign_completion_percent >= 10:
            status = "🟡 NEEDS ATTENTION"
        else:
            status = "🔴 BEHIND SCHEDULE"

        report += f"""
Campaign Status: {status}
Budget Status: {'🟢 WITHIN BUDGET' if metrics.budget_utilization < 80 else '🟡 APPROACHING LIMIT' if metrics.budget_utilization < 100 else '🔴 OVER BUDGET'}
Quality Status: {'🟢 HIGH QUALITY' if metrics.avg_english_proficiency >= 3.5 else '🟡 MODERATE QUALITY' if metrics.avg_english_proficiency >= 2.5 else '🔴 NEEDS IMPROVEMENT'}

{'=' * 60}
✨ WEEK 2 ENHANCEMENTS ACTIVE
{'=' * 60}
🔤 Romaji Integration: {metrics.romaji_conversion_success:.1f}% success
🗺️ Master Data Validation: Active
📝 Enhanced Content Generation: Active
🌐 WordPress Romaji Publishing: Active

Generated by Campaign Monitoring Dashboard v2.0
"""
        
        return report
    
    def save_daily_report(self, report: str = None) -> str:
        """Save daily report to file"""
        if report is None:
            report = self.generate_dashboard_report()
        
        # Create reports directory if it doesn't exist
        reports_dir = Path('campaign_reports')
        reports_dir.mkdir(exist_ok=True)
        
        # Generate filename with date
        today = date.today().strftime('%Y-%m-%d')
        filename = reports_dir / f'campaign_report_{today}.txt'
        
        # Save report
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📄 Daily report saved: {filename}")
        return str(filename)
    
    def send_daily_report(self, report: str = None) -> bool:
        """Send daily report via email if configured"""
        # Check if email reporting is enabled
        if not os.getenv('SEND_DAILY_REPORTS', '').lower() in ['true', '1', 'yes']:
            logger.info("📧 Daily email reports disabled")
            return False
        
        try:
            # This would implement email sending
            # For now, just save the report and log
            filename = self.save_daily_report(report)
            logger.info(f"📧 Daily report ready for email: {filename}")
            
            # TODO: Implement actual email sending with SMTP
            # Would use environment variables for email configuration:
            # - SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD
            # - REPORT_EMAIL_RECIPIENTS
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send daily report: {e}")
            return False
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Generate system alerts based on current metrics"""
        metrics = self.get_real_time_metrics()
        alerts = []
        
        # Budget alerts
        if metrics.budget_utilization > 90:
            alerts.append({
                'level': 'critical',
                'type': 'budget',
                'message': f'Budget utilization at {metrics.budget_utilization:.1f}%',
                'action': 'Review campaign costs and consider adjustments'
            })
        elif metrics.budget_utilization > 75:
            alerts.append({
                'level': 'warning',
                'type': 'budget',
                'message': f'Budget utilization at {metrics.budget_utilization:.1f}%',
                'action': 'Monitor costs closely'
            })
        
        # Progress alerts
        if metrics.campaign_completion_percent < 10 and metrics.days_remaining < 20:
            alerts.append({
                'level': 'critical',
                'type': 'progress',
                'message': f'Campaign only {metrics.campaign_completion_percent:.1f}% complete',
                'action': 'Increase daily collection rate or extend timeline'
            })
        
        # Quality alerts
        if metrics.avg_english_proficiency < 2.5:
            alerts.append({
                'level': 'warning',
                'type': 'quality',
                'message': f'Low average English proficiency: {metrics.avg_english_proficiency:.1f}',
                'action': 'Review English-focused search criteria'
            })
        
        # System health alerts
        if metrics.database_status != "connected":
            alerts.append({
                'level': 'critical',
                'type': 'system',
                'message': 'Database connection issue',
                'action': 'Check database connectivity'
            })
        
        if metrics.wordpress_status != "connected":
            alerts.append({
                'level': 'warning',
                'type': 'system',
                'message': 'WordPress API connection issue',
                'action': 'Check WordPress API credentials'
            })
        
        # Manual review alerts
        if metrics.providers_needing_manual_review > 50:
            alerts.append({
                'level': 'info',
                'type': 'review',
                'message': f'{metrics.providers_needing_manual_review} providers need manual review',
                'action': 'Schedule manual review session'
            })
        
        return alerts


def main():
    """Run dashboard and generate report"""
    dashboard = CampaignDashboard()
    
    # Generate and display report
    report = dashboard.generate_dashboard_report()
    print(report)
    
    # Save daily report
    filename = dashboard.save_daily_report(report)
    print(f"\n📄 Report saved to: {filename}")
    
    # Check for alerts
    alerts = dashboard.get_alerts()
    if alerts:
        print(f"\n🚨 SYSTEM ALERTS ({len(alerts)}):")
        for alert in alerts:
            level_emoji = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}
            emoji = level_emoji.get(alert['level'], '⚪')
            print(f"{emoji} [{alert['level'].upper()}] {alert['type']}: {alert['message']}")
            print(f"   Action: {alert['action']}")
    
    # Send daily report if configured
    dashboard.send_daily_report(report)


if __name__ == "__main__":
    main()