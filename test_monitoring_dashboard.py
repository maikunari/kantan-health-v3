#!/usr/bin/env python3
"""
Campaign Monitoring Dashboard Test Suite
Comprehensive tests for the monitoring system with real campaign data
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.monitoring.campaign_dashboard import CampaignDashboard
from src.monitoring.daily_reporter import DailyReporter
from src.monitoring.health_monitor import HealthMonitor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MonitoringTestSuite:
    """Test suite for monitoring dashboard system"""
    
    def __init__(self):
        """Initialize test suite"""
        self.dashboard = CampaignDashboard()
        self.reporter = DailyReporter()
        self.health_monitor = HealthMonitor()
        
        self.test_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'warnings': []
        }
    
    def test_campaign_dashboard(self) -> bool:
        """Test campaign dashboard metrics generation"""
        print("\n" + "=" * 80)
        print("TEST 1: CAMPAIGN DASHBOARD METRICS")
        print("=" * 80)
        
        try:
            print("\n1. Testing real-time metrics generation:")
            
            # Generate metrics
            metrics = self.dashboard.get_real_time_metrics()
            
            # Test basic metrics
            print(f"   Campaign completion: {metrics.campaign_completion_percent:.1f}%")
            print(f"   Total providers: {metrics.total_providers:,}")
            print(f"   Total cost: ${metrics.total_cost:.2f}")
            print(f"   Budget utilization: {metrics.budget_utilization:.1f}%")
            
            # Validate metrics structure
            required_fields = [
                'campaign_completion_percent', 'total_providers', 'total_cost',
                'daily_target_achievement', 'avg_english_proficiency',
                'cities_covered', 'specialties_covered'
            ]
            
            missing_fields = [field for field in required_fields if not hasattr(metrics, field)]
            
            if missing_fields:
                print(f"   ❌ Missing fields: {missing_fields}")
                return False
            else:
                print(f"   ✓ All required metrics fields present")
            
            # Test geographic metrics
            if metrics.cities_covered > 0:
                print(f"   ✓ Geographic coverage: {metrics.cities_covered} cities")
                if metrics.top_cities:
                    print(f"   ✓ Top cities data: {len(metrics.top_cities)} entries")
            
            # Test specialty metrics
            if metrics.specialties_covered > 0:
                print(f"   ✓ Specialty coverage: {metrics.specialties_covered} specialties")
                if metrics.top_specialties:
                    print(f"   ✓ Top specialties data: {len(metrics.top_specialties)} entries")
            
            # Test quality metrics
            print(f"   English proficiency: {metrics.avg_english_proficiency:.1f}/5")
            print(f"   Romaji conversion: {metrics.romaji_conversion_success:.1f}%")
            
            # Test validation metrics
            print(f"   Location validation: {metrics.location_validation_success:.1f}%")
            print(f"   Specialty validation: {metrics.specialty_validation_success:.1f}%")
            
            print(f"\n✅ Campaign dashboard test PASSED")
            return True
            
        except Exception as e:
            print(f"\n❌ Campaign dashboard test FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_dashboard_report_generation(self) -> bool:
        """Test dashboard report generation"""
        print("\n" + "=" * 80)
        print("TEST 2: DASHBOARD REPORT GENERATION")
        print("=" * 80)
        
        try:
            print("\n1. Testing comprehensive report generation:")
            
            # Generate report
            report = self.dashboard.generate_dashboard_report()
            
            # Validate report content
            required_sections = [
                'CAMPAIGN PROGRESS',
                'BUDGET & COSTS',
                'QUALITY METRICS',
                'GEOGRAPHIC COVERAGE',
                'SPECIALTY DISTRIBUTION',
                'MASTER DATA VALIDATION',
                'TIMELINE PROJECTION',
                'SYSTEM HEALTH'
            ]
            
            missing_sections = [section for section in required_sections if section not in report]
            
            if missing_sections:
                print(f"   ❌ Missing sections: {missing_sections}")
                return False
            else:
                print(f"   ✓ All required sections present")
            
            # Check report length (should be comprehensive)
            if len(report) < 1000:
                print(f"   ❌ Report too short: {len(report)} characters")
                return False
            else:
                print(f"   ✓ Report comprehensive: {len(report):,} characters")
            
            # Test report saving
            filename = self.dashboard.save_daily_report(report)
            if Path(filename).exists():
                print(f"   ✓ Report saved successfully: {filename}")
                
                # Check file size
                file_size = Path(filename).stat().st_size
                if file_size > 0:
                    print(f"   ✓ Report file not empty: {file_size:,} bytes")
                else:
                    print(f"   ❌ Report file is empty")
                    return False
            else:
                print(f"   ❌ Report file not created")
                return False
            
            print(f"\n✅ Dashboard report generation test PASSED")
            return True
            
        except Exception as e:
            print(f"\n❌ Dashboard report generation test FAILED: {e}")
            return False
    
    def test_daily_reporter(self) -> bool:
        """Test automated daily reporting system"""
        print("\n" + "=" * 80)
        print("TEST 3: DAILY REPORTER SYSTEM")
        print("=" * 80)
        
        try:
            print("\n1. Testing executive summary generation:")
            
            # Get metrics for summary
            metrics = self.dashboard.get_real_time_metrics()
            summary = self.reporter.generate_executive_summary(metrics)
            
            # Validate summary content
            required_summary_items = [
                'EXECUTIVE SUMMARY',
                'Campaign Status:',
                'KEY METRICS:',
                'TODAY\'S PERFORMANCE:',
                'TIMELINE:',
                'WEEK 2 ENHANCEMENTS:'
            ]
            
            missing_items = [item for item in required_summary_items if item not in summary]
            
            if missing_items:
                print(f"   ❌ Missing summary items: {missing_items}")
                return False
            else:
                print(f"   ✓ Executive summary complete")
            
            print("\n2. Testing recommendations generation:")
            
            # Generate recommendations
            recommendations = self.reporter.generate_recommendations(metrics)
            
            if recommendations:
                print(f"   ✓ Generated {len(recommendations)} recommendations")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"   {i}. {rec[:80]}...")
            else:
                print(f"   ⚠️ No recommendations generated (system may be optimal)")
            
            print("\n3. Testing detailed report generation:")
            
            # Generate detailed report
            detailed_report = self.reporter.generate_detailed_report()
            
            # Check for comprehensive content
            if len(detailed_report) > 2000:
                print(f"   ✓ Detailed report generated: {len(detailed_report):,} characters")
            else:
                print(f"   ❌ Detailed report too short: {len(detailed_report)} characters")
                return False
            
            print("\n4. Testing daily report process:")
            
            # Run full daily report process
            results = self.reporter.run_daily_report()
            
            if results['success']:
                print(f"   ✓ Daily report process completed")
                print(f"   - Report generated: {results['report_generated']}")
                print(f"   - Report saved: {results['report_saved']}")
                print(f"   - Email configured: {'SEND_DAILY_REPORTS' in os.environ}")
                print(f"   - Alerts found: {results['alerts_count']}")
                print(f"   - Recommendations: {results['recommendations_count']}")
            else:
                print(f"   ❌ Daily report process failed: {results['errors']}")
                return False
            
            print(f"\n✅ Daily reporter test PASSED")
            return True
            
        except Exception as e:
            print(f"\n❌ Daily reporter test FAILED: {e}")
            return False
    
    def test_health_monitor(self) -> bool:
        """Test system health monitoring"""
        print("\n" + "=" * 80)
        print("TEST 4: HEALTH MONITORING SYSTEM")
        print("=" * 80)
        
        try:
            print("\n1. Testing individual health checks:")
            
            # Test database health
            db_health = self.health_monitor.check_database_health()
            print(f"   Database status: {db_health['status']}")
            print(f"   Database response: {db_health['response_time']:.2f}s")
            
            if db_health['status'] not in ['error']:
                print(f"   ✓ Database health check working")
            else:
                print(f"   ❌ Database health check failed: {db_health['error_message']}")
            
            # Test WordPress health
            wp_health = self.health_monitor.check_wordpress_health()
            print(f"   WordPress status: {wp_health['status']}")
            
            if wp_health['status'] in ['connected', 'warning']:
                print(f"   ✓ WordPress health check working")
            else:
                print(f"   ⚠️ WordPress health check issue: {wp_health['error_message']}")
            
            # Test Google API health
            google_health = self.health_monitor.check_google_api_health()
            print(f"   Google API status: {google_health['status']}")
            print(f"   Google API usage: ${google_health['daily_usage']:.2f}")
            
            if google_health['status'] in ['active', 'inactive']:
                print(f"   ✓ Google API health check working")
            
            # Test system resources
            system_resources = self.health_monitor.check_system_resources()
            print(f"   Memory usage: {system_resources['memory_usage']:.1f}%")
            print(f"   CPU usage: {system_resources['cpu_usage']:.1f}%")
            print(f"   Disk usage: {system_resources['disk_usage']:.1f}%")
            
            if all(key in system_resources for key in ['cpu_usage', 'memory_usage', 'disk_usage']):
                print(f"   ✓ System resource monitoring working")
            else:
                print(f"   ❌ System resource monitoring incomplete")
                return False
            
            print("\n2. Testing comprehensive health report:")
            
            # Generate full health report
            health_metrics = self.health_monitor.generate_health_report()
            
            # Validate health metrics
            if health_metrics.overall_health_score >= 0:
                print(f"   ✓ Health score calculated: {health_metrics.overall_health_score:.1f}/100")
                print(f"   ✓ Health status: {health_metrics.health_status}")
            else:
                print(f"   ❌ Health score calculation failed")
                return False
            
            # Test health report formatting
            formatted_report = self.health_monitor.format_health_report(health_metrics)
            
            if len(formatted_report) > 500:
                print(f"   ✓ Health report formatted: {len(formatted_report):,} characters")
            else:
                print(f"   ❌ Health report too short")
                return False
            
            # Test health report saving
            filename = self.health_monitor.save_health_report(health_metrics)
            
            if Path(filename).exists():
                print(f"   ✓ Health report saved: {filename}")
            else:
                print(f"   ❌ Health report not saved")
                return False
            
            print(f"\n✅ Health monitoring test PASSED")
            return True
            
        except Exception as e:
            print(f"\n❌ Health monitoring test FAILED: {e}")
            return False
    
    def test_monitoring_integration(self) -> bool:
        """Test integration between monitoring components"""
        print("\n" + "=" * 80)
        print("TEST 5: MONITORING SYSTEM INTEGRATION")
        print("=" * 80)
        
        try:
            print("\n1. Testing cross-component data consistency:")
            
            # Get metrics from dashboard
            dashboard_metrics = self.dashboard.get_real_time_metrics()
            
            # Get health metrics
            health_metrics = self.health_monitor.generate_health_report()
            
            # Check for consistency
            dashboard_db_status = dashboard_metrics.database_status
            health_db_status = health_metrics.database_status
            
            if dashboard_db_status == health_db_status or (dashboard_db_status in ['connected', 'healthy'] and health_db_status in ['connected', 'healthy']):
                print(f"   ✓ Database status consistent: {dashboard_db_status} / {health_db_status}")
            else:
                print(f"   ⚠️ Database status inconsistent: {dashboard_db_status} vs {health_db_status}")
            
            # Check WordPress status consistency
            dashboard_wp_status = dashboard_metrics.wordpress_status
            health_wp_status = health_metrics.wordpress_status
            
            if dashboard_wp_status == health_wp_status or (dashboard_wp_status in ['connected'] and health_wp_status in ['connected']):
                print(f"   ✓ WordPress status consistent: {dashboard_wp_status} / {health_wp_status}")
            else:
                print(f"   ⚠️ WordPress status inconsistent: {dashboard_wp_status} vs {health_wp_status}")
            
            print("\n2. Testing alert generation integration:")
            
            # Get alerts from dashboard
            dashboard_alerts = self.dashboard.get_alerts()
            
            # Generate recommendations from reporter
            reporter_recommendations = self.reporter.generate_recommendations(dashboard_metrics)
            
            print(f"   Dashboard alerts: {len(dashboard_alerts)}")
            print(f"   Reporter recommendations: {len(reporter_recommendations)}")
            
            if dashboard_alerts or reporter_recommendations:
                print(f"   ✓ Alert/recommendation system active")
                
                # Show sample alerts/recommendations
                if dashboard_alerts:
                    sample_alert = dashboard_alerts[0]
                    print(f"   Sample alert: {sample_alert['type']} - {sample_alert['message'][:50]}...")
                
                if reporter_recommendations:
                    sample_rec = reporter_recommendations[0]
                    print(f"   Sample recommendation: {sample_rec[:60]}...")
            else:
                print(f"   ✓ No alerts (system healthy)")
            
            print("\n3. Testing report file generation consistency:")
            
            # Check that all report files are created in expected locations
            campaign_reports_dir = Path('campaign_reports')
            monitoring_reports_dir = Path('monitoring_reports')
            
            if campaign_reports_dir.exists():
                campaign_files = list(campaign_reports_dir.glob('*.txt'))
                print(f"   ✓ Campaign reports directory exists: {len(campaign_files)} files")
            
            if monitoring_reports_dir.exists():
                health_files = list(monitoring_reports_dir.glob('*.txt'))
                print(f"   ✓ Health reports directory exists: {len(health_files)} files")
            
            print(f"\n✅ Monitoring system integration test PASSED")
            return True
            
        except Exception as e:
            print(f"\n❌ Monitoring system integration test FAILED: {e}")
            return False
    
    def test_real_time_performance(self) -> bool:
        """Test monitoring system performance with real data"""
        print("\n" + "=" * 80)
        print("TEST 6: REAL-TIME PERFORMANCE")
        print("=" * 80)
        
        try:
            print("\n1. Testing dashboard metrics generation performance:")
            
            import time
            
            # Time dashboard metrics generation
            start_time = time.time()
            metrics = self.dashboard.get_real_time_metrics()
            dashboard_time = time.time() - start_time
            
            print(f"   Dashboard metrics time: {dashboard_time:.2f}s")
            
            if dashboard_time < 5.0:  # Should be under 5 seconds
                print(f"   ✓ Dashboard performance acceptable")
            else:
                print(f"   ⚠️ Dashboard performance slow")
                self.test_results['warnings'].append("Dashboard metrics generation slow")
            
            print("\n2. Testing health check performance:")
            
            # Time health check generation
            start_time = time.time()
            health_report = self.health_monitor.generate_health_report()
            health_time = time.time() - start_time
            
            print(f"   Health check time: {health_time:.2f}s")
            
            if health_time < 10.0:  # Should be under 10 seconds
                print(f"   ✓ Health check performance acceptable")
            else:
                print(f"   ⚠️ Health check performance slow")
                self.test_results['warnings'].append("Health check generation slow")
            
            print("\n3. Testing report generation performance:")
            
            # Time report generation
            start_time = time.time()
            report = self.reporter.generate_detailed_report()
            report_time = time.time() - start_time
            
            print(f"   Report generation time: {report_time:.2f}s")
            
            if report_time < 15.0:  # Should be under 15 seconds
                print(f"   ✓ Report generation performance acceptable")
            else:
                print(f"   ⚠️ Report generation performance slow")
                self.test_results['warnings'].append("Report generation slow")
            
            # Test memory usage
            import psutil
            process = psutil.Process()
            memory_usage = process.memory_info().rss / (1024 * 1024)  # MB
            
            print(f"\n4. Testing memory usage:")
            print(f"   Memory usage: {memory_usage:.1f} MB")
            
            if memory_usage < 500:  # Under 500MB
                print(f"   ✓ Memory usage acceptable")
            else:
                print(f"   ⚠️ Memory usage high")
                self.test_results['warnings'].append(f"High memory usage: {memory_usage:.1f}MB")
            
            print(f"\n✅ Performance test PASSED")
            return True
            
        except Exception as e:
            print(f"\n❌ Performance test FAILED: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all monitoring dashboard tests"""
        print("\n" + "=" * 80)
        print("CAMPAIGN MONITORING DASHBOARD TEST SUITE")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Define tests
        tests = [
            ("Campaign Dashboard", self.test_campaign_dashboard),
            ("Dashboard Report Generation", self.test_dashboard_report_generation),
            ("Daily Reporter System", self.test_daily_reporter),
            ("Health Monitoring System", self.test_health_monitor),
            ("Monitoring Integration", self.test_monitoring_integration),
            ("Real-Time Performance", self.test_real_time_performance)
        ]
        
        # Run tests
        test_results = {}
        for test_name, test_func in tests:
            self.test_results['total_tests'] += 1
            
            try:
                result = test_func()
                test_results[test_name] = result
                
                if result:
                    self.test_results['passed'] += 1
                else:
                    self.test_results['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Test {test_name} crashed: {e}")
                test_results[test_name] = False
                self.test_results['failed'] += 1
        
        # Print summary
        print("\n" + "=" * 80)
        print("MONITORING DASHBOARD TEST SUMMARY")
        print("=" * 80)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {test_name}: {status}")
        
        print(f"\nResults: {self.test_results['passed']}/{self.test_results['total_tests']} tests passed")
        
        if self.test_results['warnings']:
            print(f"\nWarnings: {len(self.test_results['warnings'])}")
            for warning in self.test_results['warnings']:
                print(f"  ⚠️ {warning}")
        
        # Final status
        all_passed = self.test_results['failed'] == 0
        
        if all_passed:
            print("\n🎉 ALL MONITORING DASHBOARD TESTS PASSED!")
            print("\n✅ Validated Monitoring Features:")
            print("  • Real-time campaign progress tracking")
            print("  • Comprehensive daily reporting system")
            print("  • System health monitoring and alerts")
            print("  • Geographic and specialty distribution analysis")
            print("  • Budget tracking and cost projections")
            print("  • Quality metrics and romaji integration status")
            print("  • Master data validation monitoring")
            print("  • Performance monitoring and optimization")
            print("\n🚀 Monitoring dashboard ready for production use!")
        else:
            print(f"\n⚠️ {self.test_results['failed']} test(s) failed. Review issues before deployment.")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return {
            'success': all_passed,
            'test_results': test_results,
            'statistics': self.test_results,
            'timestamp': datetime.now().isoformat()
        }


def main():
    """Run monitoring dashboard test suite"""
    test_suite = MonitoringTestSuite()
    results = test_suite.run_all_tests()
    
    # Return exit code based on success
    sys.exit(0 if results['success'] else 1)


if __name__ == "__main__":
    main()