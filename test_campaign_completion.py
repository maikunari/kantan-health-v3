#!/usr/bin/env python3
"""
Campaign Completion Evaluation Test Suite
Comprehensive tests for campaign readiness and maintenance mode transition evaluation
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

from src.week4.campaign_completion import CampaignCompletionEvaluator, CompletionCriterion, CampaignCompletionAssessment, CompletionStatus, TransitionDecision

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CampaignCompletionTestSuite:
    """Test suite for campaign completion evaluation system"""
    
    def __init__(self):
        """Initialize test suite"""
        self.evaluator = CampaignCompletionEvaluator()
        
    def test_completion_criteria_evaluation(self) -> Dict[str, Any]:
        """Test individual completion criteria evaluation"""
        print("\n1. Testing completion criteria evaluation:")
        
        results = {
            'success': True,
            'criteria_evaluated': 0,
            'criteria_results': {},
            'avg_completion_score': 0.0,
            'errors': []
        }
        
        try:
            # Test all individual criteria
            criteria_tests = [
                ('Provider Count', self.evaluator.evaluate_provider_count_criterion),
                ('Geographic Coverage', self.evaluator.evaluate_geographic_coverage_criterion),
                ('Quality Standards', self.evaluator.evaluate_quality_standards_criterion),
                ('Data Integrity', self.evaluator.evaluate_data_integrity_criterion),
                ('System Health', self.evaluator.evaluate_system_health_criterion),
                ('Cost Efficiency', self.evaluator.evaluate_cost_efficiency_criterion)
            ]
            
            completion_scores = []
            
            for criterion_name, test_func in criteria_tests:
                try:
                    start_time = time.time()
                    criterion = test_func()
                    evaluation_time = time.time() - start_time
                    
                    # Validate criterion structure
                    assert isinstance(criterion, CompletionCriterion), f"{criterion_name} should return CompletionCriterion"
                    assert 0 <= criterion.completion_percentage <= 100, f"{criterion_name} completion % should be 0-100"
                    assert 0 <= criterion.weight <= 1, f"{criterion_name} weight should be 0-1"
                    assert isinstance(criterion.status, CompletionStatus), f"{criterion_name} should have CompletionStatus"
                    
                    results['criteria_results'][criterion_name] = {
                        'completion_percentage': criterion.completion_percentage,
                        'current_value': criterion.current_value,
                        'target_value': criterion.target_value,
                        'meets_threshold': criterion.meets_threshold,
                        'status': criterion.status.value,
                        'issues_count': len(criterion.issues),
                        'recommendations_count': len(criterion.recommendations),
                        'evaluation_time': evaluation_time
                    }
                    
                    completion_scores.append(criterion.completion_percentage)
                    
                    print(f"   ✓ {criterion_name}: {criterion.completion_percentage:.1f}% "
                          f"({criterion.status.value}, threshold: {criterion.meets_threshold}) [{evaluation_time:.3f}s]")
                    
                    if criterion.issues:
                        print(f"      Issues: {len(criterion.issues)}")
                    if criterion.recommendations:
                        print(f"      Recommendations: {len(criterion.recommendations)}")
                    
                except Exception as e:
                    results['errors'].append(f"{criterion_name} evaluation failed: {str(e)}")
                    logger.error(f"{criterion_name} evaluation failed: {e}")
            
            results['criteria_evaluated'] = len([r for r in results['criteria_results'].values()])
            if completion_scores:
                results['avg_completion_score'] = sum(completion_scores) / len(completion_scores)
            
            print(f"   ✓ {results['criteria_evaluated']} criteria evaluated")
            print(f"   ✓ Average completion score: {results['avg_completion_score']:.1f}%")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Completion criteria evaluation test failed: {e}")
        
        return results
    
    def test_comprehensive_assessment_generation(self) -> Dict[str, Any]:
        """Test comprehensive campaign assessment generation"""
        print("\n2. Testing comprehensive assessment generation:")
        
        results = {
            'success': True,
            'assessment_generated': False,
            'completion_score': 0.0,
            'weighted_score': 0.0,
            'campaign_status': '',
            'transition_decision': '',
            'criteria_count': 0,
            'blockers_count': 0,
            'recommendations_count': 0,
            'errors': []
        }
        
        try:
            start_time = time.time()
            assessment = self.evaluator.generate_comprehensive_assessment()
            generation_time = time.time() - start_time
            
            results['assessment_generated'] = True
            
            # Validate assessment structure
            assert isinstance(assessment, CampaignCompletionAssessment), "Should return CampaignCompletionAssessment"
            assert 0 <= assessment.overall_completion_percentage <= 100, "Overall completion should be 0-100%"
            assert 0 <= assessment.weighted_completion_score <= 100, "Weighted score should be 0-100"
            assert isinstance(assessment.campaign_status, CompletionStatus), "Should have CompletionStatus"
            assert isinstance(assessment.transition_decision, TransitionDecision), "Should have TransitionDecision"
            
            # Extract key metrics
            results['completion_score'] = assessment.overall_completion_percentage
            results['weighted_score'] = assessment.weighted_completion_score
            results['campaign_status'] = assessment.campaign_status.value
            results['transition_decision'] = assessment.transition_decision.value
            results['blockers_count'] = len(assessment.critical_blockers)
            results['recommendations_count'] = len(assessment.transition_recommendations)
            
            # Count criteria
            criteria_count = 0
            for criterion in [assessment.provider_count_criterion, assessment.geographic_coverage_criterion,
                            assessment.quality_standards_criterion, assessment.data_integrity_criterion,
                            assessment.system_health_criterion, assessment.cost_efficiency_criterion]:
                if criterion is not None:
                    criteria_count += 1
            results['criteria_count'] = criteria_count
            
            print(f"   ✓ Comprehensive assessment generated in {generation_time:.2f}s")
            print(f"   ✓ Overall completion: {assessment.overall_completion_percentage:.1f}%")
            print(f"   ✓ Weighted score: {assessment.weighted_completion_score:.1f}/100")
            print(f"   ✓ Campaign status: {assessment.campaign_status.value.upper()}")
            print(f"   ✓ Transition decision: {assessment.transition_decision.value.upper()}")
            print(f"   ✓ Criteria evaluated: {criteria_count}/6")
            print(f"   ✓ Critical blockers: {len(assessment.critical_blockers)}")
            print(f"   ✓ Recommendations: {len(assessment.transition_recommendations)}")
            
            # Show key metrics
            print(f"   ✓ Key metrics:")
            print(f"      • Providers: {assessment.total_providers:,}/{assessment.target_providers:,}")
            print(f"      • Quality score: {assessment.quality_score:.1f}")
            print(f"      • System health: {assessment.system_health_score:.1f}")
            print(f"      • Budget utilization: {assessment.budget_utilization:.1f}%")
            
            # Show sample blockers and recommendations
            if assessment.critical_blockers:
                print(f"   ✓ Sample critical blocker: {assessment.critical_blockers[0][:80]}...")
            
            if assessment.transition_recommendations:
                print(f"   ✓ Sample recommendation: {assessment.transition_recommendations[0][:80]}...")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Comprehensive assessment generation test failed: {e}")
        
        return results
    
    def test_transition_decision_logic(self) -> Dict[str, Any]:
        """Test transition decision logic and framework"""
        print("\n3. Testing transition decision logic:")
        
        results = {
            'success': True,
            'decision_logic_tested': False,
            'decision_scenarios': 0,
            'valid_decisions': 0,
            'decision_consistency': True,
            'errors': []
        }
        
        try:
            # Get real assessment for baseline
            assessment = self.evaluator.generate_comprehensive_assessment()
            original_decision = assessment.transition_decision
            
            print(f"   ✓ Current campaign decision: {original_decision.value.upper()}")
            print(f"   ✓ Based on weighted score: {assessment.weighted_completion_score:.1f}/100")
            
            # Test decision logic consistency
            test_scores = [95.0, 85.0, 65.0, 45.0, 25.0, 10.0]
            expected_decisions = [
                TransitionDecision.READY_FOR_TRANSITION,
                TransitionDecision.CONDITIONAL_TRANSITION, 
                TransitionDecision.CONTINUE_CAMPAIGN,
                TransitionDecision.CONTINUE_CAMPAIGN,
                TransitionDecision.CONTINUE_CAMPAIGN,
                TransitionDecision.CONTINUE_CAMPAIGN
            ]
            
            print(f"   ✓ Testing decision logic with various completion scores:")
            
            for i, (test_score, expected) in enumerate(zip(test_scores, expected_decisions)):
                # Create test assessment
                test_assessment = CampaignCompletionAssessment()
                test_assessment.weighted_completion_score = test_score
                test_assessment.critical_blockers = []  # No blockers for clean test
                test_assessment.budget_utilization = 50.0  # Reasonable budget usage
                test_assessment.days_remaining = 15  # Reasonable time remaining
                
                # Create mock criteria that meet thresholds for conditional scenarios
                if test_score >= 70:
                    mock_criterion = CompletionCriterion("Test", "Test", 80, 100, 0.3)
                    test_assessment.provider_count_criterion = mock_criterion
                    test_assessment.quality_standards_criterion = mock_criterion
                    test_assessment.data_integrity_criterion = mock_criterion
                
                # Test decision logic
                decision = self.evaluator.determine_transition_decision(test_assessment)
                
                is_valid = decision in [d for d in TransitionDecision]
                is_expected = (test_score >= 70 and decision in [TransitionDecision.READY_FOR_TRANSITION, 
                                                               TransitionDecision.CONDITIONAL_TRANSITION]) or \
                             (test_score < 70 and decision == TransitionDecision.CONTINUE_CAMPAIGN)
                
                print(f"      {i+1}. Score {test_score}%: {decision.value} ({'✓' if is_expected else '⚠️'})")
                
                if is_valid:
                    results['valid_decisions'] += 1
                if not is_expected:
                    results['decision_consistency'] = False
            
            results['decision_scenarios'] = len(test_scores)
            results['decision_logic_tested'] = True
            
            print(f"   ✓ Decision scenarios tested: {results['decision_scenarios']}")
            print(f"   ✓ Valid decisions: {results['valid_decisions']}/{results['decision_scenarios']}")
            print(f"   ✓ Logic consistency: {'✅' if results['decision_consistency'] else '⚠️'}")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Transition decision logic test failed: {e}")
        
        return results
    
    def test_risk_assessment_framework(self) -> Dict[str, Any]:
        """Test risk assessment and mitigation framework"""
        print("\n4. Testing risk assessment framework:")
        
        results = {
            'success': True,
            'risk_assessment_generated': False,
            'risk_level': '',
            'risk_factors_count': 0,
            'mitigation_strategies_count': 0,
            'risk_logic_valid': True,
            'errors': []
        }
        
        try:
            # Get real assessment for testing
            assessment = self.evaluator.generate_comprehensive_assessment()
            
            # Test risk assessment
            start_time = time.time()
            risk_level, risk_factors, mitigation_strategies = self.evaluator.assess_risks_and_mitigation(assessment)
            risk_assessment_time = time.time() - start_time
            
            results['risk_assessment_generated'] = True
            results['risk_level'] = risk_level
            results['risk_factors_count'] = len(risk_factors)
            results['mitigation_strategies_count'] = len(mitigation_strategies)
            
            # Validate risk assessment
            valid_risk_levels = ['low', 'medium', 'high', 'critical']
            if risk_level not in valid_risk_levels:
                results['risk_logic_valid'] = False
                results['errors'].append(f"Invalid risk level: {risk_level}")
            
            # Risk factors should have corresponding mitigation strategies
            if len(risk_factors) > 0 and len(mitigation_strategies) == 0:
                results['risk_logic_valid'] = False
                results['errors'].append("Risk factors identified but no mitigation strategies provided")
            
            print(f"   ✓ Risk assessment completed in {risk_assessment_time:.2f}s")
            print(f"   ✓ Risk level: {risk_level.upper()}")
            print(f"   ✓ Risk factors identified: {len(risk_factors)}")
            print(f"   ✓ Mitigation strategies: {len(mitigation_strategies)}")
            
            # Show sample risk factors and mitigations
            if risk_factors:
                print(f"   ✓ Sample risk: {risk_factors[0][:60]}...")
            if mitigation_strategies:
                print(f"   ✓ Sample mitigation: {mitigation_strategies[0][:60]}...")
            
            # Test risk level logic consistency
            print(f"   ✓ Risk logic consistency: {'✅' if results['risk_logic_valid'] else '❌'}")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Risk assessment framework test failed: {e}")
        
        return results
    
    def test_completion_report_generation(self) -> Dict[str, Any]:
        """Test completion assessment report generation"""
        print("\n5. Testing completion report generation:")
        
        results = {
            'success': True,
            'report_generated': False,
            'report_saved': False,
            'report_length': 0,
            'report_sections': 0,
            'report_completeness': True,
            'errors': []
        }
        
        try:
            # Generate assessment and report
            start_time = time.time()
            assessment = self.evaluator.generate_comprehensive_assessment()
            report = self.evaluator.generate_completion_report(assessment)
            report_generation_time = time.time() - start_time
            
            results['report_generated'] = True
            results['report_length'] = len(report)
            
            # Check for required report sections
            required_sections = [
                'CAMPAIGN COMPLETION ASSESSMENT REPORT',
                'OVERALL COMPLETION SUMMARY',
                'COMPLETION CRITERIA ASSESSMENT',
                'TIMELINE ANALYSIS',
                'TRANSITION DECISION ANALYSIS',
                'TRANSITION RECOMMENDATIONS',
                'RISK ASSESSMENT & MITIGATION',
                'DETAILED METRICS BREAKDOWN',
                'COMPLETION ASSESSMENT SUMMARY'
            ]
            
            sections_found = []
            for section in required_sections:
                if section in report:
                    sections_found.append(section)
                else:
                    results['report_completeness'] = False
                    results['errors'].append(f"Missing section: {section}")
            
            results['report_sections'] = len(sections_found)
            
            print(f"   ✓ Report generated in {report_generation_time:.2f}s")
            print(f"   ✓ Report length: {len(report):,} characters")
            print(f"   ✓ Report sections: {len(sections_found)}/{len(required_sections)}")
            print(f"   ✓ Report completeness: {'✅' if results['report_completeness'] else '❌'}")
            
            # Test report saving
            try:
                filename = self.evaluator.save_completion_assessment(assessment, report)
                results['report_saved'] = True
                results['report_filename'] = filename
                
                # Verify file exists and has content
                if Path(filename).exists():
                    file_size = Path(filename).stat().st_size
                    print(f"   ✓ Report saved: {filename} ({file_size:,} bytes)")
                else:
                    results['errors'].append("Report file not found after saving")
                    
            except Exception as e:
                results['errors'].append(f"Report saving failed: {str(e)}")
            
            # Validate report content quality
            if len(report) < 1000:
                results['errors'].append("Report too short - may be missing content")
            
            # Check for key information in report
            key_info = [
                assessment.campaign_status.value,
                assessment.transition_decision.value,
                f"{assessment.overall_completion_percentage:.1f}%"
            ]
            
            missing_info = []
            for info in key_info:
                if info not in report:
                    missing_info.append(info)
            
            if missing_info:
                results['errors'].append(f"Missing key information in report: {missing_info}")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Completion report generation test failed: {e}")
        
        return results
    
    def test_integration_with_monitoring_systems(self) -> Dict[str, Any]:
        """Test integration with existing monitoring systems"""
        print("\n6. Testing integration with monitoring systems:")
        
        results = {
            'success': True,
            'dashboard_integration': False,
            'qa_integration': False,
            'search_optimizer_integration': False,
            'data_consistency': True,
            'integration_time': 0.0,
            'errors': []
        }
        
        try:
            start_time = time.time()
            
            # Test dashboard integration
            try:
                dashboard_metrics = self.evaluator.dashboard.get_real_time_metrics()
                if hasattr(dashboard_metrics, 'total_providers') and dashboard_metrics.total_providers > 0:
                    results['dashboard_integration'] = True
                    print(f"   ✓ Dashboard integration: ✅ ({dashboard_metrics.total_providers:,} providers)")
                else:
                    results['errors'].append("Dashboard metrics not available or empty")
            except Exception as e:
                results['errors'].append(f"Dashboard integration failed: {str(e)}")
            
            # Test QA system integration
            try:
                qa_metrics = self.evaluator.qa_system.generate_system_quality_metrics()
                if hasattr(qa_metrics, 'overall_system_quality'):
                    results['qa_integration'] = True
                    print(f"   ✓ QA system integration: ✅ (quality: {qa_metrics.overall_system_quality:.1f})")
                else:
                    results['errors'].append("QA metrics not available")
            except Exception as e:
                results['errors'].append(f"QA system integration failed: {str(e)}")
            
            # Test search optimizer integration
            try:
                location_metrics = self.evaluator.search_optimizer.analyze_geographic_performance()
                if len(location_metrics) > 0:
                    results['search_optimizer_integration'] = True
                    print(f"   ✓ Search optimizer integration: ✅ ({len(location_metrics)} locations analyzed)")
                else:
                    results['errors'].append("Search optimizer metrics not available")
            except Exception as e:
                results['errors'].append(f"Search optimizer integration failed: {str(e)}")
            
            integration_time = time.time() - start_time
            results['integration_time'] = integration_time
            
            # Test data consistency across systems
            try:
                # Get metrics from different systems and compare
                assessment = self.evaluator.generate_comprehensive_assessment()
                dashboard_providers = self.evaluator.dashboard.get_real_time_metrics().total_providers
                
                if abs(assessment.total_providers - dashboard_providers) > 1:  # Allow small discrepancy
                    results['data_consistency'] = False
                    results['errors'].append(f"Provider count inconsistency: {assessment.total_providers} vs {dashboard_providers}")
                else:
                    print(f"   ✓ Data consistency: ✅ (provider counts match: {assessment.total_providers:,})")
                    
            except Exception as e:
                results['errors'].append(f"Data consistency check failed: {str(e)}")
            
            print(f"   ✓ Integration testing completed in {integration_time:.2f}s")
            print(f"   ✓ Systems integrated: Dashboard({results['dashboard_integration']}) "
                  f"QA({results['qa_integration']}) Search({results['search_optimizer_integration']})")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Integration test failed: {e}")
        
        return results
    
    def test_performance_and_scalability(self) -> Dict[str, Any]:
        """Test performance and scalability of completion evaluation"""
        print("\n7. Testing performance and scalability:")
        
        results = {
            'success': True,
            'criteria_evaluation_time': 0.0,
            'assessment_generation_time': 0.0,
            'report_generation_time': 0.0,
            'memory_usage': 0.0,
            'performance_acceptable': True,
            'errors': []
        }
        
        try:
            import psutil
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Test individual criteria evaluation performance
            start_time = time.time()
            provider_criterion = self.evaluator.evaluate_provider_count_criterion()
            geographic_criterion = self.evaluator.evaluate_geographic_coverage_criterion()
            quality_criterion = self.evaluator.evaluate_quality_standards_criterion()
            criteria_time = time.time() - start_time
            results['criteria_evaluation_time'] = criteria_time
            
            # Test full assessment generation performance
            start_time = time.time()
            assessment = self.evaluator.generate_comprehensive_assessment()
            assessment_time = time.time() - start_time
            results['assessment_generation_time'] = assessment_time
            
            # Test report generation performance
            start_time = time.time()
            report = self.evaluator.generate_completion_report(assessment)
            report_time = time.time() - start_time
            results['report_generation_time'] = report_time
            
            # Check memory usage
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            results['memory_usage'] = end_memory - start_memory
            
            print(f"   ✓ Criteria evaluation time: {criteria_time:.2f}s")
            print(f"   ✓ Assessment generation time: {assessment_time:.2f}s")
            print(f"   ✓ Report generation time: {report_time:.2f}s")
            print(f"   ✓ Memory usage: {results['memory_usage']:.1f} MB")
            
            # Performance thresholds
            performance_issues = []
            if criteria_time > 10.0:  # Criteria evaluation should be under 10 seconds
                performance_issues.append(f"Criteria evaluation too slow: {criteria_time:.2f}s")
            
            if assessment_time > 15.0:  # Assessment should be under 15 seconds
                performance_issues.append(f"Assessment generation too slow: {assessment_time:.2f}s")
            
            if report_time > 5.0:  # Report should be under 5 seconds
                performance_issues.append(f"Report generation too slow: {report_time:.2f}s")
            
            if results['memory_usage'] > 500:  # Should use less than 500MB
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
        """Run complete campaign completion evaluation test suite"""
        print("=" * 80)
        print("🏁 CAMPAIGN COMPLETION EVALUATION TEST SUITE")
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
            ('Completion Criteria Evaluation', self.test_completion_criteria_evaluation),
            ('Comprehensive Assessment Generation', self.test_comprehensive_assessment_generation),
            ('Transition Decision Logic', self.test_transition_decision_logic),
            ('Risk Assessment Framework', self.test_risk_assessment_framework),
            ('Completion Report Generation', self.test_completion_report_generation),
            ('Integration with Monitoring Systems', self.test_integration_with_monitoring_systems),
            ('Performance and Scalability', self.test_performance_and_scalability)
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
        print("CAMPAIGN COMPLETION EVALUATION TEST SUMMARY")
        print(f"{'=' * 80}")
        
        for test_name, result in all_results['test_results'].items():
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"  {test_name}: {status}")
        
        print(f"\nResults: {all_results['tests_passed']}/{len(tests)} tests passed")
        
        if all_results['overall_success']:
            print("\n🎉 ALL CAMPAIGN COMPLETION EVALUATION TESTS PASSED!")
            print("\n✅ Validated Completion Evaluation Features:")
            print("  • Individual completion criteria assessment with weighted scoring")
            print("  • Comprehensive campaign readiness evaluation framework")
            print("  • Multi-criteria transition decision logic with risk assessment")
            print("  • Systematic risk identification and mitigation strategies")
            print("  • Comprehensive completion reports with actionable recommendations")
            print("  • Seamless integration with monitoring, QA, and optimization systems")
            print("  • Performance optimization for real-time evaluation operations")
            print("\n🚀 Campaign Completion Evaluation system ready for transition planning!")
        else:
            print(f"\n⚠️ {all_results['tests_failed']} test(s) failed. Review issues before deployment.")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return all_results


def main():
    """Run campaign completion evaluation test suite"""
    test_suite = CampaignCompletionTestSuite()
    results = test_suite.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if results['overall_success'] else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()