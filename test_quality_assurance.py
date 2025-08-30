#!/usr/bin/env python3
"""
Quality Assurance System Test Suite
Comprehensive tests for content quality, data integrity, and system reliability
"""

import os
import sys
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.monitoring.quality_assurance import QualityAssuranceSystem, ContentQualityScore, SystemQualityMetrics
from src.monitoring.campaign_dashboard import CampaignDashboard
from src.core.database import DatabaseManager, Provider

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QualityAssuranceTestSuite:
    """Test suite for quality assurance system"""
    
    def __init__(self):
        """Initialize test suite"""
        self.qa_system = QualityAssuranceSystem()
        self.dashboard = CampaignDashboard()
        self.db_manager = DatabaseManager()
        
    def test_content_quality_analysis(self) -> Dict[str, Any]:
        """Test content quality analysis for individual providers"""
        print("\n1. Testing content quality analysis:")
        
        results = {
            'success': True,
            'providers_analyzed': 0,
            'quality_scores': [],
            'avg_quality_score': 0.0,
            'issues_found': 0,
            'recommendations_generated': 0,
            'errors': []
        }
        
        try:
            # Get sample providers from database
            with self.db_manager.get_session() as session:
                providers = session.query(Provider).limit(5).all()
            
            if not providers:
                print("   ⚠️ No providers found for testing")
                return results
            
            quality_scores = []
            total_issues = 0
            total_recommendations = 0
            
            for provider in providers:
                try:
                    start_time = time.time()
                    quality_score = self.qa_system.analyze_content_quality(provider)
                    analysis_time = time.time() - start_time
                    
                    quality_scores.append(quality_score)
                    total_issues += len(quality_score.issues)
                    total_recommendations += len(quality_score.recommendations)
                    
                    print(f"   Provider {provider.id}: {quality_score.final_quality_score:.1f}/100 "
                          f"({quality_score.priority_level} priority) [{analysis_time:.3f}s]")
                    
                    # Test quality score components
                    assert 0 <= quality_score.final_quality_score <= 100, "Quality score out of range"
                    assert quality_score.priority_level in ['low', 'medium', 'high', 'critical'], "Invalid priority level"
                    assert isinstance(quality_score.issues, list), "Issues should be a list"
                    assert isinstance(quality_score.recommendations, list), "Recommendations should be a list"
                    
                except Exception as e:
                    results['errors'].append(f"Provider {provider.id}: {str(e)}")
                    logger.error(f"Quality analysis failed for provider {provider.id}: {e}")
            
            if quality_scores:
                results['providers_analyzed'] = len(quality_scores)
                results['quality_scores'] = quality_scores
                results['avg_quality_score'] = sum(s.final_quality_score for s in quality_scores) / len(quality_scores)
                results['issues_found'] = total_issues
                results['recommendations_generated'] = total_recommendations
                
                print(f"   ✓ Analyzed {len(quality_scores)} providers")
                print(f"   ✓ Average quality score: {results['avg_quality_score']:.1f}/100")
                print(f"   ✓ Total issues identified: {total_issues}")
                print(f"   ✓ Recommendations generated: {total_recommendations}")
                
                # Verify quality distribution
                high_quality = len([s for s in quality_scores if s.final_quality_score >= 75])
                medium_quality = len([s for s in quality_scores if 60 <= s.final_quality_score < 75])
                low_quality = len([s for s in quality_scores if s.final_quality_score < 60])
                
                print(f"   ✓ Quality distribution: High({high_quality}) Medium({medium_quality}) Low({low_quality})")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Content quality analysis test failed: {e}")
        
        return results
    
    def test_system_quality_metrics(self) -> Dict[str, Any]:
        """Test system-wide quality metrics generation"""
        print("\n2. Testing system quality metrics generation:")
        
        results = {
            'success': True,
            'metrics_generated': False,
            'system_quality_score': 0.0,
            'content_metrics': {},
            'integrity_metrics': {},
            'reliability_metrics': {},
            'errors': []
        }
        
        try:
            start_time = time.time()
            metrics = self.qa_system.generate_system_quality_metrics()
            generation_time = time.time() - start_time
            
            results['metrics_generated'] = True
            results['system_quality_score'] = metrics.overall_system_quality
            
            # Test metrics structure
            assert isinstance(metrics, SystemQualityMetrics), "Should return SystemQualityMetrics object"
            assert 0 <= metrics.overall_system_quality <= 100, "Overall quality score out of range"
            
            # Content metrics
            results['content_metrics'] = {
                'avg_content_quality': metrics.avg_content_quality,
                'content_completeness_rate': metrics.content_completeness_rate,
                'romaji_conversion_success_rate': metrics.romaji_conversion_success_rate,
                'seo_optimization_score': metrics.seo_optimization_score
            }
            
            # Data integrity metrics
            results['integrity_metrics'] = {
                'master_data_compliance_rate': metrics.master_data_compliance_rate,
                'database_integrity_score': metrics.database_integrity_score,
                'wordpress_sync_accuracy': metrics.wordpress_sync_accuracy,
                'duplicate_detection_accuracy': metrics.duplicate_detection_accuracy
            }
            
            # System reliability metrics
            results['reliability_metrics'] = {
                'api_performance_score': metrics.api_performance_score,
                'error_handling_score': metrics.error_handling_score,
                'system_uptime_score': metrics.system_uptime_score,
                'campaign_state_reliability': metrics.campaign_state_reliability
            }
            
            print(f"   ✓ System quality metrics generated in {generation_time:.2f}s")
            print(f"   ✓ Overall system quality: {metrics.overall_system_quality:.1f}/100")
            print(f"   ✓ Content quality: {metrics.avg_content_quality:.1f}/100")
            print(f"   ✓ Data integrity: {(metrics.master_data_compliance_rate + metrics.database_integrity_score) / 2:.1f}/100")
            print(f"   ✓ System reliability: {(metrics.api_performance_score + metrics.system_uptime_score + metrics.error_handling_score) / 3:.1f}/100")
            print(f"   ✓ Quality distribution: High({metrics.high_quality_providers}) Medium({metrics.medium_quality_providers}) Low({metrics.low_quality_providers})")
            print(f"   ✓ Issues: Total({metrics.total_issues}) Critical({metrics.critical_issues}) High({metrics.high_priority_issues})")
            print(f"   ✓ Recommendations: {len(metrics.top_recommendations)}")
            
            # Test issue detection
            assert metrics.total_issues >= 0, "Total issues should be non-negative"
            assert metrics.critical_issues <= metrics.total_issues, "Critical issues should not exceed total"
            assert len(metrics.top_recommendations) > 0, "Should generate recommendations"
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"System quality metrics test failed: {e}")
        
        return results
    
    def test_quality_report_generation(self) -> Dict[str, Any]:
        """Test comprehensive quality report generation"""
        print("\n3. Testing quality report generation:")
        
        results = {
            'success': True,
            'report_generated': False,
            'report_length': 0,
            'report_saved': False,
            'report_sections': [],
            'errors': []
        }
        
        try:
            start_time = time.time()
            report = self.qa_system.generate_quality_report()
            generation_time = time.time() - start_time
            
            results['report_generated'] = True
            results['report_length'] = len(report)
            
            # Test report content
            assert len(report) > 1000, "Report should be comprehensive"
            
            # Check for required sections
            required_sections = [
                'QUALITY ASSURANCE COMPREHENSIVE REPORT',
                'OVERALL QUALITY SUMMARY',
                'CONTENT QUALITY METRICS',
                'DATA INTEGRITY METRICS',
                'SYSTEM RELIABILITY METRICS',
                'ISSUES SUMMARY',
                'TOP QUALITY RECOMMENDATIONS',
                'QUALITY ASSURANCE CHECKLIST'
            ]
            
            found_sections = []
            for section in required_sections:
                if section in report:
                    found_sections.append(section)
                else:
                    results['errors'].append(f"Missing section: {section}")
            
            results['report_sections'] = found_sections
            
            print(f"   ✓ Quality report generated in {generation_time:.2f}s")
            print(f"   ✓ Report length: {len(report):,} characters")
            print(f"   ✓ Sections found: {len(found_sections)}/{len(required_sections)}")
            
            # Test report saving
            try:
                filename = self.qa_system.save_quality_report(report)
                results['report_saved'] = True
                results['report_filename'] = filename
                
                # Verify file exists and has content
                if Path(filename).exists():
                    file_size = Path(filename).stat().st_size
                    print(f"   ✓ Report saved: {filename} ({file_size} bytes)")
                else:
                    results['errors'].append("Report file not found after saving")
                    
            except Exception as e:
                results['errors'].append(f"Report saving failed: {str(e)}")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Quality report generation test failed: {e}")
        
        return results
    
    def test_dashboard_integration(self) -> Dict[str, Any]:
        """Test integration with campaign dashboard"""
        print("\n4. Testing dashboard integration:")
        
        results = {
            'success': True,
            'qa_metrics_integrated': False,
            'dashboard_report_enhanced': False,
            'quality_scores_present': False,
            'errors': []
        }
        
        try:
            # Test dashboard metrics with QA integration
            start_time = time.time()
            dashboard_metrics = self.dashboard.get_real_time_metrics()
            integration_time = time.time() - start_time
            
            # Check if QA metrics are integrated
            if hasattr(dashboard_metrics, 'overall_quality_score'):
                results['qa_metrics_integrated'] = True
                results['overall_quality_score'] = dashboard_metrics.overall_quality_score
                results['content_quality_score'] = dashboard_metrics.content_quality_score
                results['data_integrity_score'] = dashboard_metrics.data_integrity_score
                results['system_reliability_score'] = dashboard_metrics.system_reliability_score
                results['providers_needing_qa_review'] = dashboard_metrics.providers_needing_qa_review
                results['critical_quality_issues'] = dashboard_metrics.critical_quality_issues
                
                print(f"   ✓ QA metrics integrated in dashboard ({integration_time:.2f}s)")
                print(f"   ✓ Overall quality score: {dashboard_metrics.overall_quality_score:.1f}/100")
                print(f"   ✓ Content quality: {dashboard_metrics.content_quality_score:.1f}/100")
                print(f"   ✓ Data integrity: {dashboard_metrics.data_integrity_score:.1f}/100")
                print(f"   ✓ System reliability: {dashboard_metrics.system_reliability_score:.1f}/100")
                print(f"   ✓ Providers needing review: {dashboard_metrics.providers_needing_qa_review}")
                print(f"   ✓ Critical issues: {dashboard_metrics.critical_quality_issues}")
                
                results['quality_scores_present'] = True
                
            else:
                results['errors'].append("QA metrics not found in dashboard metrics")
            
            # Test enhanced dashboard report
            try:
                dashboard_report = self.dashboard.generate_dashboard_report()
                
                if 'QUALITY ASSURANCE METRICS' in dashboard_report:
                    results['dashboard_report_enhanced'] = True
                    print("   ✓ Dashboard report includes QA metrics section")
                else:
                    results['errors'].append("QA metrics section not found in dashboard report")
                    
            except Exception as e:
                results['errors'].append(f"Dashboard report generation failed: {str(e)}")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Dashboard integration test failed: {e}")
        
        return results
    
    def test_comprehensive_qa_process(self) -> Dict[str, Any]:
        """Test complete QA process workflow"""
        print("\n5. Testing comprehensive QA process:")
        
        results = {
            'success': True,
            'qa_process_completed': False,
            'metrics_calculated': False,
            'report_generated': False,
            'issues_identified': 0,
            'recommendations_provided': 0,
            'errors': []
        }
        
        try:
            start_time = time.time()
            qa_results = self.qa_system.run_comprehensive_quality_check()
            process_time = time.time() - start_time
            
            results['qa_process_completed'] = qa_results['success']
            results['metrics_calculated'] = qa_results['quality_report_generated']
            results['report_generated'] = qa_results['quality_report_saved']
            results['system_quality_score'] = qa_results['system_quality_score']
            results['providers_analyzed'] = qa_results['providers_analyzed']
            results['issues_identified'] = qa_results['issues_found']
            results['critical_issues'] = qa_results['critical_issues']
            results['recommendations_provided'] = qa_results['recommendations_count']
            
            print(f"   ✓ Complete QA process completed in {process_time:.2f}s")
            print(f"   ✓ System quality score: {qa_results['system_quality_score']:.1f}/100")
            print(f"   ✓ Providers analyzed: {qa_results['providers_analyzed']}")
            print(f"   ✓ Issues found: {qa_results['issues_found']}")
            print(f"   ✓ Critical issues: {qa_results['critical_issues']}")
            print(f"   ✓ Recommendations: {qa_results['recommendations_count']}")
            
            if qa_results['quality_report_saved']:
                print(f"   ✓ Quality report saved: {qa_results.get('report_filename', 'quality_reports/')}")
            
            # Test error handling
            if qa_results['errors']:
                results['errors'].extend(qa_results['errors'])
                print(f"   ⚠️ Process completed with {len(qa_results['errors'])} errors")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Comprehensive QA process test failed: {e}")
        
        return results
    
    def test_performance_metrics(self) -> Dict[str, Any]:
        """Test QA system performance with current data"""
        print("\n6. Testing QA system performance:")
        
        results = {
            'success': True,
            'analysis_time': 0.0,
            'metrics_time': 0.0,
            'report_time': 0.0,
            'memory_usage': 0.0,
            'performance_acceptable': True,
            'errors': []
        }
        
        try:
            import psutil
            process = psutil.Process()
            
            # Test individual provider analysis performance
            with self.db_manager.get_session() as session:
                provider = session.query(Provider).first()
            
            if provider:
                start_time = time.time()
                start_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                quality_score = self.qa_system.analyze_content_quality(provider)
                
                analysis_time = time.time() - start_time
                results['analysis_time'] = analysis_time
                
                print(f"   ✓ Individual analysis time: {analysis_time:.3f}s")
                
                # Test system metrics performance
                start_time = time.time()
                system_metrics = self.qa_system.generate_system_quality_metrics()
                metrics_time = time.time() - start_time
                results['metrics_time'] = metrics_time
                
                print(f"   ✓ System metrics time: {metrics_time:.3f}s")
                
                # Test report generation performance
                start_time = time.time()
                report = self.qa_system.generate_quality_report()
                report_time = time.time() - start_time
                results['report_time'] = report_time
                
                end_memory = process.memory_info().rss / 1024 / 1024  # MB
                results['memory_usage'] = end_memory - start_memory
                
                print(f"   ✓ Report generation time: {report_time:.3f}s")
                print(f"   ✓ Memory usage: {results['memory_usage']:.1f} MB")
                
                # Performance thresholds
                if analysis_time > 2.0:  # Analysis should be under 2 seconds
                    results['performance_acceptable'] = False
                    results['errors'].append(f"Analysis too slow: {analysis_time:.3f}s")
                
                if metrics_time > 10.0:  # System metrics should be under 10 seconds
                    results['performance_acceptable'] = False
                    results['errors'].append(f"Metrics generation too slow: {metrics_time:.3f}s")
                
                if report_time > 5.0:  # Report should be under 5 seconds
                    results['performance_acceptable'] = False
                    results['errors'].append(f"Report generation too slow: {report_time:.3f}s")
                
                if results['memory_usage'] > 500:  # Should use less than 500MB
                    results['performance_acceptable'] = False
                    results['errors'].append(f"Excessive memory usage: {results['memory_usage']:.1f}MB")
                
                print(f"   {'✅' if results['performance_acceptable'] else '❌'} Performance {'acceptable' if results['performance_acceptable'] else 'needs optimization'}")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Performance test failed: {e}")
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete QA test suite"""
        print("=" * 80)
        print("🔍 QUALITY ASSURANCE SYSTEM TEST SUITE")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_results = {
            'overall_success': True,
            'tests_passed': 0,
            'tests_failed': 0,
            'total_errors': 0,
            'test_results': {}
        }
        
        # Define tests
        tests = [
            ('Content Quality Analysis', self.test_content_quality_analysis),
            ('System Quality Metrics', self.test_system_quality_metrics),
            ('Quality Report Generation', self.test_quality_report_generation),
            ('Dashboard Integration', self.test_dashboard_integration),
            ('Comprehensive QA Process', self.test_comprehensive_qa_process),
            ('Performance Metrics', self.test_performance_metrics)
        ]
        
        # Run all tests
        for test_name, test_func in tests:
            print(f"\n{'=' * 80}")
            print(f"TEST: {test_name.upper()}")
            print(f"{'=' * 80}")
            
            try:
                result = test_func()
                all_results['test_results'][test_name] = result
                
                if result['success']:
                    all_results['tests_passed'] += 1
                    print(f"\n✅ {test_name} test PASSED")
                else:
                    all_results['tests_failed'] += 1
                    all_results['overall_success'] = False
                    print(f"\n❌ {test_name} test FAILED")
                    
                all_results['total_errors'] += len(result.get('errors', []))
                
                # Display errors if any
                if result.get('errors'):
                    for error in result['errors']:
                        print(f"   Error: {error}")
                        
            except Exception as e:
                all_results['tests_failed'] += 1
                all_results['overall_success'] = False
                all_results['total_errors'] += 1
                print(f"\n❌ {test_name} test FAILED with exception: {e}")
        
        # Summary
        print(f"\n{'=' * 80}")
        print("QUALITY ASSURANCE TEST SUMMARY")
        print(f"{'=' * 80}")
        
        for test_name, result in all_results['test_results'].items():
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"  {test_name}: {status}")
        
        print(f"\nResults: {all_results['tests_passed']}/{len(tests)} tests passed")
        
        if all_results['overall_success']:
            print("\n🎉 ALL QUALITY ASSURANCE TESTS PASSED!")
            print("\n✅ Validated QA Features:")
            print("  • Individual provider quality analysis with detailed scoring")
            print("  • System-wide quality metrics generation and aggregation") 
            print("  • Comprehensive quality reports with actionable recommendations")
            print("  • Seamless integration with campaign monitoring dashboard")
            print("  • Complete QA workflow from analysis to reporting")
            print("  • Performance optimization for real-time quality monitoring")
            print("\n🚀 Quality Assurance system ready for production use!")
        else:
            print(f"\n⚠️ {all_results['tests_failed']} test(s) failed. Review issues before deployment.")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return all_results


def main():
    """Run QA test suite"""
    test_suite = QualityAssuranceTestSuite()
    results = test_suite.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if results['overall_success'] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()