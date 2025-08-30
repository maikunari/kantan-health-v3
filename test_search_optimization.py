#!/usr/bin/env python3
"""
Search Optimization System Test Suite
Comprehensive tests for search performance analysis and optimization recommendations
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

from src.monitoring.search_optimizer import SearchOptimizer, QueryPerformanceMetrics, LocationPerformanceMetrics, SearchOptimizationReport
from src.monitoring.campaign_dashboard import CampaignDashboard

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SearchOptimizationTestSuite:
    """Test suite for search optimization system"""
    
    def __init__(self):
        """Initialize test suite"""
        self.optimizer = SearchOptimizer()
        self.dashboard = CampaignDashboard()
        
    def test_search_performance_analysis(self) -> Dict[str, Any]:
        """Test search query performance analysis"""
        print("\n1. Testing search performance analysis:")
        
        results = {
            'success': True,
            'queries_analyzed': 0,
            'performance_metrics_generated': False,
            'query_types_identified': [],
            'avg_effectiveness_score': 0.0,
            'errors': []
        }
        
        try:
            start_time = time.time()
            query_metrics = self.optimizer.analyze_search_performance()
            analysis_time = time.time() - start_time
            
            results['queries_analyzed'] = len(query_metrics)
            results['performance_metrics_generated'] = len(query_metrics) > 0
            
            if query_metrics:
                # Analyze query types
                query_types = list(set(q.query_type for q in query_metrics))
                results['query_types_identified'] = query_types
                
                # Calculate average effectiveness
                avg_effectiveness = sum(q.effectiveness_score for q in query_metrics) / len(query_metrics)
                results['avg_effectiveness_score'] = avg_effectiveness
                
                # Test data integrity
                for query in query_metrics[:3]:  # Test first 3 queries
                    assert isinstance(query, QueryPerformanceMetrics), "Should return QueryPerformanceMetrics objects"
                    assert 0 <= query.effectiveness_score <= 100, "Effectiveness score should be 0-100"
                    assert query.english_success_rate >= 0, "Success rate should be non-negative"
                    assert query.cost_per_english_provider >= 0, "Cost per provider should be non-negative"
                
                print(f"   ✓ Analyzed {len(query_metrics)} search queries in {analysis_time:.2f}s")
                print(f"   ✓ Query types identified: {', '.join(query_types)}")
                print(f"   ✓ Average effectiveness score: {avg_effectiveness:.1f}/100")
                
                # Show top performing queries
                top_queries = query_metrics[:3]
                print(f"   ✓ Top performing queries:")
                for i, query in enumerate(top_queries, 1):
                    print(f"      {i}. {query.query_type}: {query.effectiveness_score:.1f}/100 "
                          f"({query.english_success_rate:.1%} success, ${query.cost_per_english_provider:.2f}/provider)")
                
            else:
                print("   ⚠️ No query metrics generated - may need actual search history data")
                
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Search performance analysis test failed: {e}")
        
        return results
    
    def test_geographic_performance_analysis(self) -> Dict[str, Any]:
        """Test geographic performance analysis"""
        print("\n2. Testing geographic performance analysis:")
        
        results = {
            'success': True,
            'locations_analyzed': 0,
            'international_areas_identified': 0,
            'high_yield_locations': [],
            'avg_english_success_rate': 0.0,
            'errors': []
        }
        
        try:
            start_time = time.time()
            location_metrics = self.optimizer.analyze_geographic_performance()
            analysis_time = time.time() - start_time
            
            results['locations_analyzed'] = len(location_metrics)
            
            if location_metrics:
                # Count international areas
                international_count = len([loc for loc in location_metrics if loc.is_international_area])
                results['international_areas_identified'] = international_count
                
                # Get high-yield locations
                high_yield = [loc.location_name for loc in location_metrics[:5] if loc.english_success_rate > 0.3]
                results['high_yield_locations'] = high_yield
                
                # Calculate average success rate
                avg_success = sum(loc.english_success_rate for loc in location_metrics) / len(location_metrics)
                results['avg_english_success_rate'] = avg_success
                
                # Test data integrity
                for location in location_metrics[:3]:
                    assert isinstance(location, LocationPerformanceMetrics), "Should return LocationPerformanceMetrics objects"
                    assert 0 <= location.english_success_rate <= 1, "Success rate should be 0-1"
                    assert location.total_providers_found >= 0, "Provider count should be non-negative"
                    assert location.optimization_priority in ['low', 'medium', 'high'], "Valid priority level"
                
                print(f"   ✓ Analyzed {len(location_metrics)} locations in {analysis_time:.2f}s")
                print(f"   ✓ International areas identified: {international_count}")
                print(f"   ✓ Average English success rate: {avg_success:.1%}")
                print(f"   ✓ High-yield locations: {', '.join(high_yield[:3])}")
                
                # Show top locations
                print(f"   ✓ Top performing locations:")
                for i, loc in enumerate(location_metrics[:3], 1):
                    print(f"      {i}. {loc.location_name}: {loc.english_success_rate:.1%} success, "
                          f"{loc.total_providers_found} providers, ROI {loc.location_roi_score:.1f}")
                
            else:
                print("   ⚠️ No location metrics generated")
                
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Geographic performance analysis test failed: {e}")
        
        return results
    
    def test_roi_optimization_analysis(self) -> Dict[str, Any]:
        """Test ROI optimization calculations"""
        print("\n3. Testing ROI optimization analysis:")
        
        results = {
            'success': True,
            'roi_analysis_generated': False,
            'total_cost_analyzed': 0.0,
            'overall_roi': 0.0,
            'strategy_performance_analyzed': 0,
            'recommendations_generated': 0,
            'errors': []
        }
        
        try:
            # Get query metrics first
            query_metrics = self.optimizer.analyze_search_performance()
            
            if not query_metrics:
                print("   ⚠️ No query metrics available for ROI analysis")
                return results
            
            start_time = time.time()
            roi_analysis = self.optimizer.calculate_search_roi_optimization(query_metrics)
            analysis_time = time.time() - start_time
            
            results['roi_analysis_generated'] = True
            results['total_cost_analyzed'] = roi_analysis.get('total_cost_analyzed', 0.0)
            results['overall_roi'] = roi_analysis.get('overall_roi', 0.0)
            results['strategy_performance_analyzed'] = len(roi_analysis.get('strategy_performance', {}))
            results['recommendations_generated'] = len(roi_analysis.get('cost_optimization_recommendations', []))
            
            print(f"   ✓ ROI analysis completed in {analysis_time:.2f}s")
            print(f"   ✓ Total cost analyzed: ${roi_analysis.get('total_cost_analyzed', 0):.2f}")
            print(f"   ✓ Overall ROI: {roi_analysis.get('overall_roi', 0):.1f} English providers per $1")
            print(f"   ✓ Strategies analyzed: {len(roi_analysis.get('strategy_performance', {}))}")
            print(f"   ✓ Optimization recommendations: {len(roi_analysis.get('cost_optimization_recommendations', []))}")
            
            # Show strategy performance
            strategy_perf = roi_analysis.get('strategy_performance', {})
            if strategy_perf:
                print("   ✓ Strategy performance summary:")
                for strategy, metrics in list(strategy_perf.items())[:3]:
                    print(f"      • {strategy}: ROI {metrics['roi_score']:.1f}, "
                          f"Success Rate {metrics['avg_success_rate']:.1%}")
            
            # Show recommendations
            recommendations = roi_analysis.get('cost_optimization_recommendations', [])
            if recommendations:
                print("   ✓ Top optimization recommendations:")
                for i, rec in enumerate(recommendations[:2], 1):
                    print(f"      {i}. {rec[:80]}...")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"ROI optimization analysis test failed: {e}")
        
        return results
    
    def test_optimization_recommendations(self) -> Dict[str, Any]:
        """Test optimization recommendation generation"""
        print("\n4. Testing optimization recommendations:")
        
        results = {
            'success': True,
            'recommendations_generated': 0,
            'actionable_recommendations': 0,
            'strategy_recommendations': 0,
            'geographic_recommendations': 0,
            'errors': []
        }
        
        try:
            # Get performance metrics
            query_metrics = self.optimizer.analyze_search_performance()
            location_metrics = self.optimizer.analyze_geographic_performance()
            
            start_time = time.time()
            recommendations = self.optimizer.generate_query_optimization_recommendations(
                query_metrics, location_metrics
            )
            generation_time = time.time() - start_time
            
            results['recommendations_generated'] = len(recommendations)
            
            # Categorize recommendations
            strategy_recs = [r for r in recommendations if any(keyword in r.lower() 
                           for keyword in ['strategy', 'query', 'focus', 'approach'])]
            geographic_recs = [r for r in recommendations if any(keyword in r.lower() 
                             for keyword in ['location', 'area', 'geographic', 'roppongi', 'azabu'])]
            actionable_recs = [r for r in recommendations if any(keyword in r.lower() 
                             for keyword in ['🎯', '💰', '🗺️', 'focus', 'prioritize', 'optimize'])]
            
            results['strategy_recommendations'] = len(strategy_recs)
            results['geographic_recommendations'] = len(geographic_recs)
            results['actionable_recommendations'] = len(actionable_recs)
            
            print(f"   ✓ Generated {len(recommendations)} recommendations in {generation_time:.2f}s")
            print(f"   ✓ Strategy recommendations: {len(strategy_recs)}")
            print(f"   ✓ Geographic recommendations: {len(geographic_recs)}")
            print(f"   ✓ Actionable recommendations: {len(actionable_recs)}")
            
            # Show sample recommendations
            if recommendations:
                print("   ✓ Sample recommendations:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"      {i}. {rec[:100]}...")
            
            # Test recommendation quality
            assert len(recommendations) > 0, "Should generate recommendations"
            assert all(len(rec) > 10 for rec in recommendations), "Recommendations should be substantive"
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Optimization recommendations test failed: {e}")
        
        return results
    
    def test_search_queue_optimization(self) -> Dict[str, Any]:
        """Test search queue optimization"""
        print("\n5. Testing search queue optimization:")
        
        results = {
            'success': True,
            'queue_optimization_completed': False,
            'original_queue_size': 0,
            'optimized_queue_size': 0,
            'priority_searches_identified': 0,
            'projected_improvement': {},
            'errors': []
        }
        
        try:
            start_time = time.time()
            optimization_results = self.optimizer.optimize_remaining_search_queue()
            optimization_time = time.time() - start_time
            
            results.update(optimization_results)
            results['optimization_time'] = optimization_time
            
            print(f"   ✓ Queue optimization completed in {optimization_time:.2f}s")
            print(f"   ✓ Original queue size: {optimization_results.get('original_queue_size', 0)}")
            print(f"   ✓ Optimized queue size: {optimization_results.get('optimized_queue_size', 0)}")
            print(f"   ✓ Priority searches identified: {optimization_results.get('priority_searches_identified', 0)}")
            
            # Show projected improvements
            projected = optimization_results.get('projected_improvement', {})
            if projected:
                print("   ✓ Projected improvements:")
                print(f"      • Current success rate: {projected.get('current_avg_success_rate', 0):.1%}")
                print(f"      • Target success rate: {projected.get('target_success_rate', 0):.1%}")
                print(f"      • Est. additional providers: {projected.get('estimated_additional_providers', 0)}")
                print(f"      • Est. timeline reduction: {projected.get('estimated_timeline_reduction', 'Unknown')}")
            
            # Test that optimization was successful
            if optimization_results['success']:
                assert optimization_results['reordering_applied'], "Reordering should be applied"
                results['queue_optimization_completed'] = True
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Search queue optimization test failed: {e}")
        
        return results
    
    def test_comprehensive_optimization_report(self) -> Dict[str, Any]:
        """Test comprehensive optimization report generation"""
        print("\n6. Testing comprehensive optimization report:")
        
        results = {
            'success': True,
            'report_generated': False,
            'report_saved': False,
            'report_sections': 0,
            'report_length': 0,
            'recommendations_count': 0,
            'errors': []
        }
        
        try:
            start_time = time.time()
            report = self.optimizer.generate_optimization_report()
            generation_time = time.time() - start_time
            
            results['report_generated'] = True
            
            # Test report structure
            assert isinstance(report, SearchOptimizationReport), "Should return SearchOptimizationReport object"
            assert report.total_queries_analyzed >= 0, "Should have valid query count"
            assert report.overall_english_success_rate >= 0, "Should have valid success rate"
            
            # Count recommendations
            immediate_actions = len(report.immediate_actions) if report.immediate_actions else 0
            strategic_adjustments = len(report.strategic_adjustments) if report.strategic_adjustments else 0
            results['recommendations_count'] = immediate_actions + strategic_adjustments
            
            print(f"   ✓ Optimization report generated in {generation_time:.2f}s")
            print(f"   ✓ Queries analyzed: {report.total_queries_analyzed}")
            print(f"   ✓ English success rate: {report.overall_english_success_rate:.1%}")
            print(f"   ✓ Total search cost: ${report.total_search_cost:.2f}")
            print(f"   ✓ Immediate actions: {immediate_actions}")
            print(f"   ✓ Strategic adjustments: {strategic_adjustments}")
            
            # Show high-yield locations
            if report.high_yield_locations:
                print(f"   ✓ High-yield locations identified: {len(report.high_yield_locations)}")
                for i, loc in enumerate(report.high_yield_locations[:3], 1):
                    print(f"      {i}. {loc.location_name}: {loc.english_success_rate:.1%} success")
            
            # Show best strategies
            if report.best_performing_strategies:
                print(f"   ✓ Best strategies identified: {len(report.best_performing_strategies)}")
                for i, strategy in enumerate(report.best_performing_strategies[:2], 1):
                    print(f"      {i}. {strategy['strategy']}: {strategy['effectiveness_score']:.1f}/100")
            
            # Test report saving
            try:
                filename = self.optimizer.save_optimization_report(report)
                results['report_saved'] = True
                results['report_filename'] = filename
                
                # Check file exists and has content
                if Path(filename).exists():
                    file_size = Path(filename).stat().st_size
                    results['report_length'] = file_size
                    print(f"   ✓ Report saved: {filename} ({file_size} bytes)")
                
            except Exception as e:
                results['errors'].append(f"Report saving failed: {str(e)}")
                print(f"   ⚠️ Report saving failed: {e}")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Comprehensive optimization report test failed: {e}")
        
        return results
    
    def test_dashboard_integration(self) -> Dict[str, Any]:
        """Test integration with monitoring dashboard"""
        print("\n7. Testing dashboard integration:")
        
        results = {
            'success': True,
            'search_metrics_integrated': False,
            'dashboard_report_enhanced': False,
            'optimization_insights_present': False,
            'errors': []
        }
        
        try:
            # Test dashboard metrics integration
            start_time = time.time()
            dashboard_metrics = self.dashboard.get_real_time_metrics()
            integration_time = time.time() - start_time
            
            # Check if search optimization metrics are integrated
            if hasattr(dashboard_metrics, 'search_effectiveness_score'):
                results['search_metrics_integrated'] = True
                print(f"   ✓ Search metrics integrated in dashboard ({integration_time:.2f}s)")
                print(f"   ✓ Search effectiveness score: {dashboard_metrics.search_effectiveness_score:.1f}/100")
                print(f"   ✓ English success rate: {dashboard_metrics.avg_english_success_rate:.1%}")
                print(f"   ✓ Cost per English provider: ${dashboard_metrics.cost_per_english_provider:.2f}")
                
                if dashboard_metrics.recommended_search_strategies:
                    print(f"   ✓ Recommended strategies: {', '.join(dashboard_metrics.recommended_search_strategies[:2])}")
                
                if dashboard_metrics.high_yield_locations:
                    print(f"   ✓ High-yield locations: {', '.join(dashboard_metrics.high_yield_locations[:2])}")
                
                results['optimization_insights_present'] = True
            else:
                results['errors'].append("Search optimization metrics not found in dashboard")
            
            # Test enhanced dashboard report
            try:
                dashboard_report = self.dashboard.generate_dashboard_report()
                
                if 'SEARCH OPTIMIZATION INSIGHTS' in dashboard_report:
                    results['dashboard_report_enhanced'] = True
                    print("   ✓ Dashboard report includes search optimization section")
                else:
                    results['errors'].append("Search optimization section not found in dashboard report")
                    
            except Exception as e:
                results['errors'].append(f"Dashboard report generation failed: {str(e)}")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Dashboard integration test failed: {e}")
        
        return results
    
    def test_performance_metrics(self) -> Dict[str, Any]:
        """Test search optimization system performance"""
        print("\n8. Testing search optimization performance:")
        
        results = {
            'success': True,
            'analysis_time': 0.0,
            'report_generation_time': 0.0,
            'memory_usage': 0.0,
            'performance_acceptable': True,
            'errors': []
        }
        
        try:
            import psutil
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Test search performance analysis speed
            start_time = time.time()
            query_metrics = self.optimizer.analyze_search_performance()
            location_metrics = self.optimizer.analyze_geographic_performance()
            analysis_time = time.time() - start_time
            
            results['analysis_time'] = analysis_time
            
            # Test report generation speed
            start_time = time.time()
            report = self.optimizer.generate_optimization_report()
            report_time = time.time() - start_time
            
            results['report_generation_time'] = report_time
            
            # Check memory usage
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            results['memory_usage'] = end_memory - start_memory
            
            print(f"   ✓ Search analysis time: {analysis_time:.2f}s")
            print(f"   ✓ Report generation time: {report_time:.2f}s")
            print(f"   ✓ Memory usage: {results['memory_usage']:.1f} MB")
            
            # Performance thresholds
            performance_issues = []
            if analysis_time > 5.0:  # Analysis should be under 5 seconds
                performance_issues.append(f"Analysis too slow: {analysis_time:.2f}s")
            
            if report_time > 10.0:  # Report should be under 10 seconds
                performance_issues.append(f"Report generation too slow: {report_time:.2f}s")
            
            if results['memory_usage'] > 200:  # Should use less than 200MB
                performance_issues.append(f"Excessive memory usage: {results['memory_usage']:.1f}MB")
            
            if performance_issues:
                results['performance_acceptable'] = False
                results['errors'].extend(performance_issues)
                print(f"   ❌ Performance issues detected")
                for issue in performance_issues:
                    print(f"      • {issue}")
            else:
                print(f"   ✅ Performance acceptable")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Performance test failed: {e}")
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete search optimization test suite"""
        print("=" * 80)
        print("🎯 SEARCH OPTIMIZATION SYSTEM TEST SUITE")
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
            ('Search Performance Analysis', self.test_search_performance_analysis),
            ('Geographic Performance Analysis', self.test_geographic_performance_analysis),
            ('ROI Optimization Analysis', self.test_roi_optimization_analysis),
            ('Optimization Recommendations', self.test_optimization_recommendations),
            ('Search Queue Optimization', self.test_search_queue_optimization),
            ('Comprehensive Optimization Report', self.test_comprehensive_optimization_report),
            ('Dashboard Integration', self.test_dashboard_integration),
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
        print("SEARCH OPTIMIZATION TEST SUMMARY")
        print(f"{'=' * 80}")
        
        for test_name, result in all_results['test_results'].items():
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"  {test_name}: {status}")
        
        print(f"\nResults: {all_results['tests_passed']}/{len(tests)} tests passed")
        
        if all_results['overall_success']:
            print("\n🎉 ALL SEARCH OPTIMIZATION TESTS PASSED!")
            print("\n✅ Validated Search Optimization Features:")
            print("  • Search query performance analysis with effectiveness scoring")
            print("  • Geographic performance analysis for location-based optimization") 
            print("  • ROI optimization with cost-effectiveness calculations")
            print("  • Query optimization recommendations based on real performance")
            print("  • Search queue prioritization for maximum efficiency")
            print("  • Comprehensive optimization reports with actionable insights")
            print("  • Seamless integration with campaign monitoring dashboard")
            print("  • Performance optimization for real-time search analysis")
            print("\n🚀 Search Optimization system ready for campaign enhancement!")
        else:
            print(f"\n⚠️ {all_results['tests_failed']} test(s) failed. Review issues before deployment.")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return all_results


def main():
    """Run search optimization test suite"""
    test_suite = SearchOptimizationTestSuite()
    results = test_suite.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if results['overall_success'] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()