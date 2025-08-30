#!/usr/bin/env python3
"""
Automated Daily Reporting System
Generates comprehensive daily reports with optimization recommendations
"""

import os
import sys
import json
import smtplib
from datetime import datetime, timedelta
try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
except ImportError:
    # Fallback for older Python versions or environment issues
    MimeText = None
    MimeMultipart = None
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.monitoring.campaign_dashboard import CampaignDashboard, DashboardMetrics
import logging

logger = logging.getLogger(__name__)


class DailyReporter:
    """Automated daily campaign reporting system"""
    
    def __init__(self):
        """Initialize daily reporter"""
        self.dashboard = CampaignDashboard()
        
        # Email configuration
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.recipients = os.getenv('REPORT_EMAIL_RECIPIENTS', '').split(',')
        self.recipients = [email.strip() for email in self.recipients if email.strip()]
        
        logger.info("✅ Daily Reporter initialized")
    
    def generate_executive_summary(self, metrics: DashboardMetrics) -> str:
        """Generate executive summary for daily report"""
        
        # Determine overall status
        if metrics.campaign_completion_percent >= 20:
            status_emoji = "🟢"
            status_text = "ON TRACK"
        elif metrics.campaign_completion_percent >= 10:
            status_emoji = "🟡"  
            status_text = "NEEDS ATTENTION"
        else:
            status_emoji = "🔴"
            status_text = "BEHIND SCHEDULE"
        
        # Calculate key metrics
        completion_rate = metrics.campaign_completion_percent
        budget_rate = metrics.budget_utilization
        quality_score = metrics.avg_english_proficiency
        
        summary = f"""
📊 EXECUTIVE SUMMARY - {datetime.now().strftime('%Y-%m-%d')}
{'=' * 60}

Campaign Status: {status_emoji} {status_text}

KEY METRICS:
• Progress: {completion_rate:.1f}% complete ({metrics.total_providers:,}/5,000 providers)
• Budget: ${metrics.total_cost:.2f}/${self.dashboard.budget_limit:.2f} ({budget_rate:.1f}% used)
• Quality: {quality_score:.1f}/5.0 average English proficiency
• Daily Rate: {metrics.current_daily_rate:.1f} providers/day (target: {metrics.required_daily_rate})

TODAY'S PERFORMANCE:
• Providers Collected: {metrics.providers_collected_today}
• Daily Target Achievement: {metrics.daily_target_achievement:.1f}%
• Cost Today: ${metrics.cost_today:.2f}
• Systems Status: DB({metrics.database_status}) | WP({metrics.wordpress_status}) | API({metrics.google_api_status})

TIMELINE:
• Estimated Completion: {metrics.estimated_completion_date}
• Days Remaining: {metrics.days_remaining}
• Required Daily Rate: {metrics.required_daily_rate:.1f} providers/day

WEEK 2 ENHANCEMENTS:
• Romaji Conversion: {metrics.romaji_conversion_success:.1f}% success rate
• Master Data Validation: {metrics.location_validation_success:.1f}% locations valid
• Content Quality: English-only content generation active
"""
        return summary
    
    def generate_recommendations(self, metrics: DashboardMetrics) -> List[str]:
        """Generate optimization recommendations based on metrics"""
        recommendations = []
        
        # Progress recommendations
        if metrics.campaign_completion_percent < 20:
            if metrics.current_daily_rate < metrics.required_daily_rate:
                recommendations.append(
                    f"🚀 INCREASE COLLECTION RATE: Current rate ({metrics.current_daily_rate:.1f}/day) "
                    f"is below target ({metrics.required_daily_rate}/day). "
                    f"Consider expanding search criteria or increasing daily limits."
                )
        
        # Budget recommendations  
        if metrics.budget_utilization > 75:
            recommendations.append(
                f"💰 MONITOR BUDGET CLOSELY: {metrics.budget_utilization:.1f}% of budget used. "
                f"At current rate (${metrics.cost_per_provider:.2f}/provider), "
                f"projected total: ${metrics.projected_total_cost:.2f}."
            )
        
        # Quality recommendations
        if metrics.avg_english_proficiency < 3.0:
            recommendations.append(
                f"⭐ IMPROVE QUALITY FILTERS: Average English proficiency is {metrics.avg_english_proficiency:.1f}/5. "
                f"Consider tightening English-focused search criteria or review scoring algorithm."
            )
        
        # Geographic recommendations
        if metrics.cities_covered < 20:
            recommendations.append(
                f"🗺️ EXPAND GEOGRAPHIC COVERAGE: Only {metrics.cities_covered} cities covered. "
                f"Consider adding more locations from the validated master list of 273 locations."
            )
        
        # Specialty recommendations
        if metrics.specialties_covered < 10:
            recommendations.append(
                f"🏥 DIVERSIFY SPECIALTIES: Only {metrics.specialties_covered} specialties covered. "
                f"Consider expanding to more of the 39 canonical specialties in master data."
            )
        
        # Manual review recommendations
        if metrics.providers_needing_manual_review > 100:
            recommendations.append(
                f"👁️ SCHEDULE MANUAL REVIEW: {metrics.providers_needing_manual_review} providers need manual review. "
                f"Allocate time for data quality validation."
            )
        
        # System health recommendations
        if metrics.wordpress_status != "connected":
            recommendations.append(
                f"🔧 FIX WORDPRESS CONNECTION: WordPress API status is {metrics.wordpress_status}. "
                f"Check credentials and API connectivity."
            )
        
        # Performance recommendations
        if metrics.system_memory_usage > 1000:  # Over 1GB
            recommendations.append(
                f"💻 MONITOR SYSTEM RESOURCES: Memory usage at {metrics.system_memory_usage:.0f}MB. "
                f"Consider optimizing batch sizes or restarting processes."
            )
        
        # Success recommendations
        if metrics.romaji_conversion_success < 95:
            recommendations.append(
                f"🔤 OPTIMIZE ROMAJI CONVERSION: {metrics.romaji_conversion_success:.1f}% success rate. "
                f"Review conversion logic for edge cases or special characters."
            )
        
        # Positive reinforcement
        if len(recommendations) == 0:
            recommendations.append(
                f"🎉 CAMPAIGN PERFORMING WELL: All metrics within acceptable ranges. "
                f"Continue current strategy and monitor for any changes."
            )
        
        return recommendations
    
    def generate_detailed_report(self) -> str:
        """Generate comprehensive daily report with analysis"""
        metrics = self.dashboard.get_real_time_metrics()
        
        # Get executive summary
        exec_summary = self.generate_executive_summary(metrics)
        
        # Get optimization recommendations
        recommendations = self.generate_recommendations(metrics)
        
        # Get system alerts
        alerts = self.dashboard.get_alerts()
        
        # Build comprehensive report
        report = exec_summary + "\n"
        
        # Add recommendations section
        report += f"""
{'=' * 60}
💡 OPTIMIZATION RECOMMENDATIONS
{'=' * 60}
"""
        for i, rec in enumerate(recommendations, 1):
            report += f"\n{i}. {rec}\n"
        
        # Add alerts section if any
        if alerts:
            report += f"""
{'=' * 60}
🚨 SYSTEM ALERTS
{'=' * 60}
"""
            for alert in alerts:
                level_emoji = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}
                emoji = level_emoji.get(alert['level'], '⚪')
                report += f"\n{emoji} [{alert['level'].upper()}] {alert['message']}"
                report += f"\n   Action Required: {alert['action']}\n"
        
        # Add detailed metrics (from dashboard)
        detailed_metrics = self.dashboard.generate_dashboard_report()
        
        # Extract the detailed sections (skip the header we already have)
        lines = detailed_metrics.split('\n')
        start_idx = None
        for i, line in enumerate(lines):
            if 'GEOGRAPHIC COVERAGE' in line:
                start_idx = i - 1
                break
        
        if start_idx:
            report += "\n" + "\n".join(lines[start_idx:])
        
        # Add footer
        report += f"""

{'=' * 60}
📧 DAILY REPORT SYSTEM
{'=' * 60}
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Next Report: {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 09:00:00')}
Dashboard Location: src/monitoring/campaign_dashboard.py

For real-time updates, run: python3 src/monitoring/campaign_dashboard.py
For manual report generation, run: python3 src/monitoring/daily_reporter.py

Campaign Monitoring System v2.0
"""
        
        return report
    
    def send_email_report(self, report: str, subject: str = None) -> bool:
        """Send report via email"""
        if not self.recipients or not self.smtp_username or not MimeText:
            logger.warning("📧 Email configuration incomplete or libraries unavailable, skipping email send")
            return False
        
        try:
            # Default subject
            if subject is None:
                today = datetime.now().strftime('%Y-%m-%d')
                subject = f"Healthcare Campaign Daily Report - {today}"
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MimeText(report, 'plain', 'utf-8'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"📧 Daily report emailed to {len(self.recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email report: {e}")
            return False
    
    def run_daily_report(self) -> Dict[str, Any]:
        """Run complete daily reporting process"""
        logger.info("📊 Starting daily report generation...")
        
        results = {
            'success': True,
            'report_generated': False,
            'report_saved': False,
            'email_sent': False,
            'alerts_count': 0,
            'recommendations_count': 0,
            'errors': []
        }
        
        try:
            # Generate comprehensive report
            report = self.generate_detailed_report()
            results['report_generated'] = True
            
            # Save report to file
            filename = self.dashboard.save_daily_report(report)
            results['report_saved'] = True
            results['report_filename'] = filename
            
            # Get metrics for summary
            metrics = self.dashboard.get_real_time_metrics()
            alerts = self.dashboard.get_alerts()
            recommendations = self.generate_recommendations(metrics)
            
            results['alerts_count'] = len(alerts)
            results['recommendations_count'] = len(recommendations)
            
            # Send email if configured
            if os.getenv('SEND_DAILY_REPORTS', '').lower() in ['true', '1', 'yes']:
                email_sent = self.send_email_report(report)
                results['email_sent'] = email_sent
                
                if not email_sent:
                    results['errors'].append("Failed to send email report")
            
            logger.info("✅ Daily report process completed successfully")
            
        except Exception as e:
            logger.error(f"Daily report process failed: {e}")
            results['success'] = False
            results['errors'].append(str(e))
        
        return results


def main():
    """Run daily reporter"""
    print("\n" + "=" * 60)
    print("🏥 HEALTHCARE CAMPAIGN - DAILY REPORTER")
    print("=" * 60)
    
    reporter = DailyReporter()
    
    # Run daily report process
    results = reporter.run_daily_report()
    
    # Display results
    if results['success']:
        print("✅ Daily report process completed successfully")
        
        if results['report_generated']:
            print("📄 Report generated")
        
        if results['report_saved']:
            print(f"💾 Report saved: {results.get('report_filename', 'campaign_reports/')}")
        
        if results['email_sent']:
            print("📧 Email report sent")
        elif os.getenv('SEND_DAILY_REPORTS'):
            print("📧 Email sending failed (check configuration)")
        else:
            print("📧 Email reporting disabled")
        
        print(f"🚨 System alerts: {results['alerts_count']}")
        print(f"💡 Recommendations: {results['recommendations_count']}")
        
    else:
        print("❌ Daily report process failed")
        for error in results['errors']:
            print(f"   Error: {error}")
    
    # Display quick metrics
    try:
        metrics = reporter.dashboard.get_real_time_metrics()
        print("\n📊 QUICK METRICS:")
        print(f"   Progress: {metrics.campaign_completion_percent:.1f}% complete")
        print(f"   Budget: {metrics.budget_utilization:.1f}% used")
        print(f"   Quality: {metrics.avg_english_proficiency:.1f}/5 English proficiency")
        print(f"   Today: {metrics.providers_collected_today} providers collected")
        
    except Exception as e:
        print(f"❌ Could not generate quick metrics: {e}")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()