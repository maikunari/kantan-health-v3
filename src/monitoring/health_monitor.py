#!/usr/bin/env python3
"""
System Health Monitoring Integration
Monitors all campaign components for performance and availability
"""

import os
import sys
import time
import psutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import DatabaseManager
from src.publishers.wordpress import WordPressPublisher
from src.collectors.google_places import GooglePlacesCollector
from src.processors.ai_content import AIContentProcessor
from src.campaign.campaign_state import CampaignStateManager

logger = logging.getLogger(__name__)


@dataclass
class HealthMetrics:
    """System health metrics"""
    timestamp: str = ""
    
    # Database Health
    database_status: str = "unknown"
    database_response_time: float = 0.0
    database_connection_count: int = 0
    database_error_message: str = ""
    
    # WordPress Health
    wordpress_status: str = "unknown"
    wordpress_response_time: float = 0.0
    wordpress_last_sync: str = ""
    wordpress_error_message: str = ""
    
    # Google API Health
    google_api_status: str = "unknown"
    google_api_quota_remaining: float = 100.0
    google_api_daily_usage: float = 0.0
    google_api_error_rate: float = 0.0
    
    # Claude API Health
    claude_api_status: str = "unknown"
    claude_api_response_time: float = 0.0
    claude_api_daily_usage: float = 0.0
    claude_api_error_message: str = ""
    
    # System Resources
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    memory_total: float = 0.0
    disk_total: float = 0.0
    
    # Process Health
    process_count: int = 0
    active_connections: int = 0
    avg_processing_time: float = 0.0
    
    # Campaign Health
    campaign_state_healthy: bool = True
    campaign_last_activity: str = ""
    campaign_error_count: int = 0
    
    # Overall Health Score (0-100)
    overall_health_score: float = 100.0
    health_status: str = "healthy"  # healthy, warning, critical


class HealthMonitor:
    """Comprehensive system health monitoring"""
    
    def __init__(self):
        """Initialize health monitor"""
        self.db = DatabaseManager()
        self.wp_publisher = WordPressPublisher()
        self.collector = GooglePlacesCollector()
        self.content_processor = AIContentProcessor()
        self.state_manager = CampaignStateManager()
        
        # Health thresholds
        self.response_time_warning = 5.0  # seconds
        self.response_time_critical = 10.0  # seconds
        self.memory_warning = 80.0  # percentage
        self.memory_critical = 95.0  # percentage
        self.disk_warning = 85.0  # percentage
        self.disk_critical = 95.0  # percentage
        
        logger.info("✅ Health Monitor initialized")
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        health = {
            'status': 'unknown',
            'response_time': 0.0,
            'connection_count': 0,
            'error_message': ''
        }
        
        try:
            start_time = time.time()
            
            # Test database connection
            session = self.db.get_session()
            
            # Simple query to test performance
            from src.core.models import Provider
            from sqlalchemy import func
            
            provider_count = session.query(func.count(Provider.id)).scalar()
            response_time = time.time() - start_time
            
            health['status'] = 'connected'
            health['response_time'] = response_time
            health['connection_count'] = provider_count or 0
            
            session.close()
            
            # Determine health level
            if response_time > self.response_time_critical:
                health['status'] = 'critical'
                health['error_message'] = f'Response time too high: {response_time:.2f}s'
            elif response_time > self.response_time_warning:
                health['status'] = 'warning'
                health['error_message'] = f'Response time elevated: {response_time:.2f}s'
            
        except Exception as e:
            health['status'] = 'error'
            health['error_message'] = str(e)
            logger.error(f"Database health check failed: {e}")
        
        return health
    
    def check_wordpress_health(self) -> Dict[str, Any]:
        """Check WordPress API connectivity and status"""
        health = {
            'status': 'unknown',
            'response_time': 0.0,
            'last_sync': '',
            'error_message': ''
        }
        
        try:
            start_time = time.time()
            
            # Test WordPress connection
            result = self.wp_publisher.test_connection()
            response_time = time.time() - start_time
            
            health['response_time'] = response_time
            
            if result.get('success'):
                health['status'] = 'connected'
                health['last_sync'] = datetime.now().isoformat()
                
                # Check response time
                if response_time > self.response_time_critical:
                    health['status'] = 'critical'
                    health['error_message'] = f'WordPress response time too high: {response_time:.2f}s'
                elif response_time > self.response_time_warning:
                    health['status'] = 'warning'
                    health['error_message'] = f'WordPress response time elevated: {response_time:.2f}s'
            else:
                health['status'] = 'error'
                health['error_message'] = result.get('error', 'WordPress connection failed')
                
        except Exception as e:
            health['status'] = 'error'
            health['error_message'] = str(e)
            logger.error(f"WordPress health check failed: {e}")
        
        return health
    
    def check_google_api_health(self) -> Dict[str, Any]:
        """Check Google Places API status and quota"""
        health = {
            'status': 'unknown',
            'quota_remaining': 100.0,
            'daily_usage': 0.0,
            'error_rate': 0.0
        }
        
        try:
            # Check collector status
            if hasattr(self.collector, 'cost_tracker'):
                cost_tracker = self.collector.cost_tracker
                
                # Get daily usage
                today_cost = cost_tracker.get_daily_costs()
                health['daily_usage'] = today_cost.get('total', 0.0)
                
                # Estimate quota remaining (rough calculation)
                daily_limit_cost = 25.0  # Daily budget limit
                if daily_limit_cost > 0:
                    usage_percent = (health['daily_usage'] / daily_limit_cost) * 100
                    health['quota_remaining'] = max(0, 100 - usage_percent)
                
                health['status'] = 'active'
                
                # Check if approaching limits
                if health['quota_remaining'] < 10:
                    health['status'] = 'critical'
                elif health['quota_remaining'] < 25:
                    health['status'] = 'warning'
            else:
                health['status'] = 'inactive'
                
        except Exception as e:
            health['status'] = 'error'
            logger.error(f"Google API health check failed: {e}")
        
        return health
    
    def check_claude_api_health(self) -> Dict[str, Any]:
        """Check Claude API status and usage"""
        health = {
            'status': 'unknown',
            'response_time': 0.0,
            'daily_usage': 0.0,
            'error_message': ''
        }
        
        try:
            # Check if API key is configured
            if hasattr(self.content_processor, 'api_key') and self.content_processor.api_key:
                health['status'] = 'configured'
                
                # Get usage from campaign state
                state = self.state_manager.state
                health['daily_usage'] = state.metrics.claude_api_cost
                
                # Simple test (could be expensive, so we skip actual API call)
                # Instead, check if processor is properly initialized
                if hasattr(self.content_processor, 'claude'):
                    health['status'] = 'ready'
            else:
                health['status'] = 'not_configured'
                health['error_message'] = 'Claude API key not found'
                
        except Exception as e:
            health['status'] = 'error'
            health['error_message'] = str(e)
            logger.error(f"Claude API health check failed: {e}")
        
        return health
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        resources = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'memory_total': 0.0,
            'disk_usage': 0.0,
            'disk_total': 0.0,
            'process_count': 0
        }
        
        try:
            # CPU usage
            resources['cpu_usage'] = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            resources['memory_usage'] = memory.percent
            resources['memory_total'] = memory.total / (1024**3)  # GB
            
            # Disk usage
            disk = psutil.disk_usage('/')
            resources['disk_usage'] = (disk.used / disk.total) * 100
            resources['disk_total'] = disk.total / (1024**3)  # GB
            
            # Process count
            resources['process_count'] = len(psutil.pids())
            
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
        
        return resources
    
    def check_campaign_health(self) -> Dict[str, Any]:
        """Check campaign state and activity"""
        campaign = {
            'state_healthy': True,
            'last_activity': '',
            'error_count': 0
        }
        
        try:
            state = self.state_manager.state
            
            # Check if campaign state is valid
            if state.total_queries > 0:
                campaign['state_healthy'] = True
                
                # Check last activity
                if hasattr(state, 'last_updated') and state.last_updated:
                    campaign['last_activity'] = state.last_updated
                else:
                    campaign['last_activity'] = datetime.now().isoformat()
                
                # Count any error conditions
                error_count = 0
                if state.metrics.total_providers_found == 0 and state.completed_queries > 10:
                    error_count += 1
                
                if state.metrics.total_cost > 600:  # Over budget
                    error_count += 1
                
                campaign['error_count'] = error_count
            else:
                campaign['state_healthy'] = False
                
        except Exception as e:
            campaign['state_healthy'] = False
            campaign['error_count'] = 1
            logger.error(f"Campaign health check failed: {e}")
        
        return campaign
    
    def calculate_health_score(self, health_data: Dict[str, Any]) -> Tuple[float, str]:
        """Calculate overall health score (0-100)"""
        score = 100.0
        status = "healthy"
        
        # Database health (25% weight)
        db_status = health_data.get('database', {}).get('status', 'unknown')
        if db_status == 'error':
            score -= 25
        elif db_status == 'critical':
            score -= 20
        elif db_status == 'warning':
            score -= 10
        
        # WordPress health (20% weight)
        wp_status = health_data.get('wordpress', {}).get('status', 'unknown')
        if wp_status == 'error':
            score -= 20
        elif wp_status == 'critical':
            score -= 15
        elif wp_status == 'warning':
            score -= 8
        
        # Google API health (20% weight)
        google_status = health_data.get('google_api', {}).get('status', 'unknown')
        quota_remaining = health_data.get('google_api', {}).get('quota_remaining', 100)
        if google_status == 'error':
            score -= 20
        elif quota_remaining < 10:
            score -= 15
        elif quota_remaining < 25:
            score -= 8
        
        # System resources (20% weight)
        resources = health_data.get('system_resources', {})
        memory_usage = resources.get('memory_usage', 0)
        cpu_usage = resources.get('cpu_usage', 0)
        disk_usage = resources.get('disk_usage', 0)
        
        if memory_usage > self.memory_critical or disk_usage > self.disk_critical:
            score -= 20
        elif memory_usage > self.memory_warning or disk_usage > self.disk_warning:
            score -= 10
        
        if cpu_usage > 90:
            score -= 10
        elif cpu_usage > 75:
            score -= 5
        
        # Campaign health (15% weight)
        campaign = health_data.get('campaign', {})
        if not campaign.get('state_healthy', True):
            score -= 15
        elif campaign.get('error_count', 0) > 0:
            score -= 8
        
        # Determine status
        if score >= 90:
            status = "healthy"
        elif score >= 70:
            status = "warning"
        else:
            status = "critical"
        
        return max(0.0, score), status
    
    def generate_health_report(self) -> HealthMetrics:
        """Generate comprehensive health report"""
        logger.info("🏥 Generating system health report...")
        
        # Collect all health metrics
        health_data = {
            'database': self.check_database_health(),
            'wordpress': self.check_wordpress_health(),
            'google_api': self.check_google_api_health(),
            'claude_api': self.check_claude_api_health(),
            'system_resources': self.check_system_resources(),
            'campaign': self.check_campaign_health()
        }
        
        # Calculate overall health
        health_score, health_status = self.calculate_health_score(health_data)
        
        # Create health metrics object
        metrics = HealthMetrics(
            timestamp=datetime.now().isoformat(),
            
            # Database
            database_status=health_data['database']['status'],
            database_response_time=health_data['database']['response_time'],
            database_connection_count=health_data['database']['connection_count'],
            database_error_message=health_data['database']['error_message'],
            
            # WordPress
            wordpress_status=health_data['wordpress']['status'],
            wordpress_response_time=health_data['wordpress']['response_time'],
            wordpress_last_sync=health_data['wordpress']['last_sync'],
            wordpress_error_message=health_data['wordpress']['error_message'],
            
            # Google API
            google_api_status=health_data['google_api']['status'],
            google_api_quota_remaining=health_data['google_api']['quota_remaining'],
            google_api_daily_usage=health_data['google_api']['daily_usage'],
            google_api_error_rate=health_data['google_api']['error_rate'],
            
            # Claude API
            claude_api_status=health_data['claude_api']['status'],
            claude_api_response_time=health_data['claude_api']['response_time'],
            claude_api_daily_usage=health_data['claude_api']['daily_usage'],
            claude_api_error_message=health_data['claude_api']['error_message'],
            
            # System Resources
            cpu_usage=health_data['system_resources']['cpu_usage'],
            memory_usage=health_data['system_resources']['memory_usage'],
            memory_total=health_data['system_resources']['memory_total'],
            disk_usage=health_data['system_resources']['disk_usage'],
            disk_total=health_data['system_resources']['disk_total'],
            process_count=health_data['system_resources']['process_count'],
            
            # Campaign
            campaign_state_healthy=health_data['campaign']['state_healthy'],
            campaign_last_activity=health_data['campaign']['last_activity'],
            campaign_error_count=health_data['campaign']['error_count'],
            
            # Overall
            overall_health_score=health_score,
            health_status=health_status
        )
        
        logger.info(f"✅ Health report generated - Score: {health_score:.1f}/100 ({health_status})")
        return metrics
    
    def format_health_report(self, metrics: HealthMetrics) -> str:
        """Format health metrics into readable report"""
        
        # Status emojis
        status_emojis = {
            'connected': '🟢',
            'active': '🟢', 
            'ready': '🟢',
            'configured': '🟢',
            'healthy': '🟢',
            'warning': '🟡',
            'critical': '🔴',
            'error': '🔴',
            'unknown': '⚪',
            'inactive': '⚪',
            'not_configured': '⚪'
        }
        
        report = f"""
🏥 SYSTEM HEALTH MONITOR
📅 Generated: {datetime.fromisoformat(metrics.timestamp).strftime('%Y-%m-%d %H:%M:%S')}

{'=' * 60}
📊 OVERALL HEALTH SCORE
{'=' * 60}
Score: {metrics.overall_health_score:.1f}/100
Status: {status_emojis.get(metrics.health_status, '⚪')} {metrics.health_status.upper()}

{'=' * 60}
🗄️ DATABASE HEALTH
{'=' * 60}
Status: {status_emojis.get(metrics.database_status, '⚪')} {metrics.database_status}
Response Time: {metrics.database_response_time:.2f}s
Providers Count: {metrics.database_connection_count:,}
{f"Error: {metrics.database_error_message}" if metrics.database_error_message else ""}

{'=' * 60}
🌐 WORDPRESS HEALTH
{'=' * 60}
Status: {status_emojis.get(metrics.wordpress_status, '⚪')} {metrics.wordpress_status}
Response Time: {metrics.wordpress_response_time:.2f}s
Last Sync: {metrics.wordpress_last_sync.split('T')[0] if metrics.wordpress_last_sync else 'Never'}
{f"Error: {metrics.wordpress_error_message}" if metrics.wordpress_error_message else ""}

{'=' * 60}
🔍 GOOGLE PLACES API HEALTH
{'=' * 60}
Status: {status_emojis.get(metrics.google_api_status, '⚪')} {metrics.google_api_status}
Daily Usage: ${metrics.google_api_daily_usage:.2f}
Quota Remaining: {metrics.google_api_quota_remaining:.1f}%
Error Rate: {metrics.google_api_error_rate:.1f}%

{'=' * 60}
🤖 CLAUDE API HEALTH
{'=' * 60}
Status: {status_emojis.get(metrics.claude_api_status, '⚪')} {metrics.claude_api_status}
Response Time: {metrics.claude_api_response_time:.2f}s
Daily Usage: ${metrics.claude_api_daily_usage:.2f}
{f"Error: {metrics.claude_api_error_message}" if metrics.claude_api_error_message else ""}

{'=' * 60}
💻 SYSTEM RESOURCES
{'=' * 60}
CPU Usage: {metrics.cpu_usage:.1f}%
Memory Usage: {metrics.memory_usage:.1f}% ({metrics.memory_total:.1f}GB total)
Disk Usage: {metrics.disk_usage:.1f}% ({metrics.disk_total:.1f}GB total)
Active Processes: {metrics.process_count:,}

{'=' * 60}
📋 CAMPAIGN HEALTH
{'=' * 60}
State Health: {status_emojis.get('healthy' if metrics.campaign_state_healthy else 'error', '⚪')} {'Healthy' if metrics.campaign_state_healthy else 'Unhealthy'}
Last Activity: {metrics.campaign_last_activity.split('T')[0] if metrics.campaign_last_activity else 'Unknown'}
Error Count: {metrics.campaign_error_count}

{'=' * 60}
🔔 HEALTH ALERTS
{'=' * 60}"""

        # Generate alerts based on metrics
        alerts = []
        
        if metrics.database_status in ['error', 'critical']:
            alerts.append(f"🔴 Database: {metrics.database_status} - {metrics.database_error_message}")
        
        if metrics.wordpress_status in ['error', 'critical']:
            alerts.append(f"🔴 WordPress: {metrics.wordpress_status} - {metrics.wordpress_error_message}")
        
        if metrics.google_api_quota_remaining < 10:
            alerts.append(f"🔴 Google API: Low quota remaining ({metrics.google_api_quota_remaining:.1f}%)")
        
        if metrics.memory_usage > self.memory_critical:
            alerts.append(f"🔴 System: Critical memory usage ({metrics.memory_usage:.1f}%)")
        
        if metrics.disk_usage > self.disk_critical:
            alerts.append(f"🔴 System: Critical disk usage ({metrics.disk_usage:.1f}%)")
        
        if not metrics.campaign_state_healthy:
            alerts.append(f"🔴 Campaign: State unhealthy ({metrics.campaign_error_count} errors)")
        
        if alerts:
            for alert in alerts:
                report += f"\n{alert}"
        else:
            report += "\n🟢 No critical alerts"
        
        report += f"""

{'=' * 60}
📈 RECOMMENDATIONS
{'=' * 60}"""
        
        recommendations = []
        
        if metrics.database_response_time > self.response_time_warning:
            recommendations.append("🔧 Optimize database queries or increase resources")
        
        if metrics.memory_usage > self.memory_warning:
            recommendations.append("🔧 Monitor memory usage, consider restarting processes")
        
        if metrics.google_api_quota_remaining < 25:
            recommendations.append("🔧 Monitor Google API usage to avoid quota exhaustion")
        
        if metrics.campaign_error_count > 0:
            recommendations.append("🔧 Review campaign errors and address issues")
        
        if metrics.overall_health_score < 80:
            recommendations.append("🔧 Address system issues to improve overall health")
        
        if recommendations:
            for rec in recommendations:
                report += f"\n{rec}"
        else:
            report += "\n🟢 System operating optimally"
        
        report += f"""

Health Monitor v2.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report
    
    def save_health_report(self, metrics: HealthMetrics) -> str:
        """Save health report to file"""
        # Create monitoring directory if it doesn't exist
        monitoring_dir = Path('monitoring_reports')
        monitoring_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.fromisoformat(metrics.timestamp)
        filename = monitoring_dir / f'health_report_{timestamp.strftime("%Y%m%d_%H%M%S")}.txt'
        
        # Format and save report
        report = self.format_health_report(metrics)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"🏥 Health report saved: {filename}")
        return str(filename)


def main():
    """Run health monitor and generate report"""
    print("\n" + "=" * 60)
    print("🏥 SYSTEM HEALTH MONITOR")
    print("=" * 60)
    
    monitor = HealthMonitor()
    
    # Generate health report
    metrics = monitor.generate_health_report()
    
    # Display report
    report = monitor.format_health_report(metrics)
    print(report)
    
    # Save report
    filename = monitor.save_health_report(metrics)
    print(f"\n💾 Health report saved: {filename}")
    
    # Return health score as exit code (for automation)
    health_score = int(metrics.overall_health_score)
    if health_score >= 90:
        exit_code = 0  # Success
    elif health_score >= 70:
        exit_code = 1  # Warning
    else:
        exit_code = 2  # Critical
    
    print(f"Exit code: {exit_code} (health score: {health_score})")
    return exit_code


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)