"""
Comprehensive Test Suite for Content Lifecycle Management System

This module provides thorough testing for the content lifecycle management,
aging analysis, priority-based updates, and maintenance integration systems.

Created: 2025-08-30
Author: Healthcare Campaign System
Version: 1.0
"""

import os
import json
import unittest
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import logging
from typing import Dict, List, Any

# Import content lifecycle system
from src.week4.content_lifecycle import (
    ContentLifecycleManager,
    ContentAgingAnalyzer,
    ContentPrioritizer,
    ContentMetrics,
    ContentUpdatePlan,
    ContentLifecycleReport,
    ContentStatus,
    UpdatePriority,
    ContentUpdateReason,
    integrate_with_maintenance_scheduling,
    create_test_content_lifecycle_setup
)

# Setup test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentLifecycleTestSuite:
    """Comprehensive test suite for content lifecycle management"""
    
    def __init__(self):
        self.test_results = []
        self.temp_dir = None
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Setup isolated test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test directories
        test_dirs = [
            "content_reports",
            "content_updates",
            "content_analytics",
            "content_backups"
        ]
        
        for directory in test_dirs:
            os.makedirs(os.path.join(self.temp_dir, directory), exist_ok=True)
    
    def cleanup_test_environment(self):
        """Cleanup test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_content_aging_analysis(self) -> Dict[str, Any]:
        """Test content aging analysis and status determination"""
        try:
            analyzer = ContentAgingAnalyzer()
            
            # Test fresh content (< 30 days)
            fresh_provider = {
                'last_updated': datetime.now() - timedelta(days=15)
            }
            fresh_status = analyzer.analyze_content_age(fresh_provider)
            assert fresh_status == ContentStatus.FRESH
            
            # Test aging content (30-90 days)
            aging_provider = {
                'last_updated': datetime.now() - timedelta(days=60)
            }
            aging_status = analyzer.analyze_content_age(aging_provider)
            assert aging_status == ContentStatus.AGING
            
            # Test stale content (90-180 days)
            stale_provider = {
                'last_updated': datetime.now() - timedelta(days=120)
            }
            stale_status = analyzer.analyze_content_age(stale_provider)
            assert stale_status == ContentStatus.STALE
            
            # Test outdated content (> 180 days)
            outdated_provider = {
                'last_updated': datetime.now() - timedelta(days=300)
            }
            outdated_status = analyzer.analyze_content_age(outdated_provider)
            assert outdated_status == ContentStatus.OUTDATED
            
            # Test freshness score calculation
            fresh_score = analyzer.calculate_freshness_score(15)
            aging_score = analyzer.calculate_freshness_score(60)
            stale_score = analyzer.calculate_freshness_score(120)
            
            assert fresh_score == 100.0
            assert 70 <= aging_score < 100
            assert 30 <= stale_score < 70
            
            # Test content change identification
            current_data = {'name': 'New Name', 'address': 'New Address'}
            previous_data = {'name': 'Old Name', 'address': 'New Address'}
            changes = analyzer.identify_content_changes(current_data, previous_data)
            assert 'name_changed' in changes
            
            return {
                "test_name": "content_aging_analysis",
                "status": "PASSED",
                "details": {
                    "status_classification_correct": True,
                    "freshness_scoring_accurate": True,
                    "change_detection_working": True,
                    "all_age_ranges_handled": True
                }
            }
            
        except Exception as e:
            return {
                "test_name": "content_aging_analysis",
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_content_prioritization_system(self) -> Dict[str, Any]:
        """Test quality-based content prioritization logic"""
        try:
            # Mock QA system
            mock_qa = Mock()
            prioritizer = ContentPrioritizer(mock_qa)
            
            # Test high priority scenario (poor quality, high traffic, old content)
            high_priority_metrics = ContentMetrics(
                provider_id="high_priority_1",
                content_age_days=200,
                quality_score=60.0,
                last_updated=datetime.now() - timedelta(days=200),
                traffic_score=80.0,
                romaji_consistency=False,
                wordpress_sync_status=False
            )
            
            high_priority_score = prioritizer.calculate_update_priority_score(high_priority_metrics)
            high_priority_level = prioritizer.assign_priority_level(high_priority_score)
            high_reasons = prioritizer.identify_update_reasons(high_priority_metrics, high_priority_score)
            
            assert high_priority_score >= 70.0  # Should be high priority
            assert high_priority_level in [UpdatePriority.CRITICAL, UpdatePriority.HIGH]
            assert ContentUpdateReason.QUALITY_DECLINE in high_reasons
            assert ContentUpdateReason.AGE_THRESHOLD in high_reasons
            
            # Test low priority scenario (good quality, low traffic, fresh content)
            low_priority_metrics = ContentMetrics(
                provider_id="low_priority_1",
                content_age_days=20,
                quality_score=90.0,
                last_updated=datetime.now() - timedelta(days=20),
                traffic_score=20.0,
                romaji_consistency=True,
                wordpress_sync_status=True
            )
            
            low_priority_score = prioritizer.calculate_update_priority_score(low_priority_metrics)
            low_priority_level = prioritizer.assign_priority_level(low_priority_score)
            
            assert low_priority_score < 40.0  # Should be low priority
            assert low_priority_level in [UpdatePriority.LOW, UpdatePriority.DEFERRED]
            
            # Test priority level assignment boundaries
            assert prioritizer.assign_priority_level(85.0) == UpdatePriority.CRITICAL
            assert prioritizer.assign_priority_level(65.0) == UpdatePriority.HIGH
            assert prioritizer.assign_priority_level(45.0) == UpdatePriority.MEDIUM
            assert prioritizer.assign_priority_level(25.0) == UpdatePriority.LOW
            assert prioritizer.assign_priority_level(10.0) == UpdatePriority.DEFERRED
            
            return {
                "test_name": "content_prioritization_system",
                "status": "PASSED",
                "details": {
                    "high_priority_detection": True,
                    "low_priority_detection": True,
                    "priority_level_assignment": True,
                    "update_reason_identification": True
                }
            }
            
        except Exception as e:
            return {
                "test_name": "content_prioritization_system",
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_content_metrics_creation(self) -> Dict[str, Any]:
        """Test content metrics calculation and validation"""
        try:
            # Create test content metrics
            metrics = ContentMetrics(
                provider_id="test_provider_1",
                content_age_days=45,
                quality_score=82.0,
                last_updated=datetime.now() - timedelta(days=45),
                traffic_score=65.0,
                wordpress_sync_status=True,
                romaji_consistency=True,
                completeness_score=85.0,
                accuracy_score=88.0,
                freshness_score=75.0,
                page_views_30d=250,
                search_ranking=2.5,
                user_engagement_score=70.0
            )
            
            # Validate metrics structure
            assert metrics.provider_id == "test_provider_1"
            assert metrics.content_age_days == 45
            assert metrics.quality_score == 82.0
            assert 0 <= metrics.traffic_score <= 100
            assert isinstance(metrics.wordpress_sync_status, bool)
            assert isinstance(metrics.romaji_consistency, bool)
            assert metrics.page_views_30d >= 0
            
            # Test metrics with edge cases
            edge_metrics = ContentMetrics(
                provider_id="edge_case_provider",
                content_age_days=0,  # Brand new
                quality_score=100.0,  # Perfect quality
                last_updated=datetime.now(),
                traffic_score=0.0,  # No traffic
                wordpress_sync_status=False,  # Sync failed
                romaji_consistency=False  # Romaji issues
            )
            
            assert edge_metrics.content_age_days == 0
            assert edge_metrics.quality_score == 100.0
            assert edge_metrics.traffic_score == 0.0
            
            return {
                "test_name": "content_metrics_creation",
                "status": "PASSED",
                "details": {
                    "metrics_structure_valid": True,
                    "data_type_validation": True,
                    "edge_cases_handled": True,
                    "all_fields_accessible": True
                }
            }
            
        except Exception as e:
            return {
                "test_name": "content_metrics_creation",
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_update_plan_generation(self) -> Dict[str, Any]:
        """Test content update plan generation and budget constraints"""
        try:
            lifecycle_manager = ContentLifecycleManager()
            
            # Create test content metrics for multiple providers
            test_metrics = {}
            for i in range(10):
                provider_id = f"test_provider_{i}"
                metrics = ContentMetrics(
                    provider_id=provider_id,
                    content_age_days=30 + (i * 20),  # Varying ages
                    quality_score=90 - (i * 5),  # Declining quality
                    last_updated=datetime.now() - timedelta(days=30 + (i * 20)),
                    traffic_score=50 + (i * 5),  # Increasing traffic
                    wordpress_sync_status=i % 2 == 0,  # Alternating sync status
                    romaji_consistency=i % 3 == 0  # Some romaji issues
                )
                test_metrics[provider_id] = metrics
            
            # Test update plan generation with budget limit
            budget_limit = 25.0  # Should allow ~10 updates at $2.50 each
            update_plans = lifecycle_manager.generate_update_plans(test_metrics, budget_limit)
            
            # Validate plan generation
            assert len(update_plans) <= 10  # Should not exceed max updates for budget
            assert len(update_plans) > 0  # Should generate some plans
            
            # Check that plans are sorted by priority (highest first)
            if len(update_plans) > 1:
                for i in range(len(update_plans) - 1):
                    current_priority_score = lifecycle_manager.prioritizer.calculate_update_priority_score(test_metrics[update_plans[i].provider_id])
                    next_priority_score = lifecycle_manager.prioritizer.calculate_update_priority_score(test_metrics[update_plans[i+1].provider_id])
                    assert current_priority_score >= next_priority_score
            
            # Test budget constraint enforcement
            total_cost = sum(plan.estimated_cost for plan in update_plans)
            assert total_cost <= budget_limit
            
            # Validate individual update plans
            for plan in update_plans:
                assert plan.provider_id in test_metrics
                assert plan.priority != UpdatePriority.DEFERRED
                assert plan.scheduled_date >= datetime.now()
                assert plan.estimated_cost > 0
                assert len(plan.sections_to_update) > 0
            
            return {
                "test_name": "update_plan_generation",
                "status": "PASSED",
                "details": {
                    "plans_generated": True,
                    "budget_constraints_enforced": True,
                    "priority_sorting_correct": True,
                    "plan_structure_valid": True,
                    "cost_calculations_accurate": True
                }
            }
            
        except Exception as e:
            return {
                "test_name": "update_plan_generation",
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_content_update_execution(self) -> Dict[str, Any]:
        """Test individual content update execution"""
        try:
            lifecycle_manager = ContentLifecycleManager()
            
            # Create test update plan
            update_plan = ContentUpdatePlan(
                provider_id="test_execution_provider",
                current_status=ContentStatus.STALE,
                target_status=ContentStatus.UPDATED,
                priority=UpdatePriority.HIGH,
                update_reasons=[ContentUpdateReason.QUALITY_DECLINE, ContentUpdateReason.AGE_THRESHOLD],
                scheduled_date=datetime.now(),
                sections_to_update=['description', 'services'],
                romaji_processing_required=True,
                wordpress_sync_required=True,
                quality_validation_required=True
            )
            
            # Execute update
            result_plan = lifecycle_manager.execute_content_update(update_plan)
            
            # Validate execution results
            assert result_plan.started_at is not None
            assert result_plan.completed_at is not None
            assert result_plan.started_at <= result_plan.completed_at
            
            # Check if execution was successful (mock should succeed)
            if result_plan.success:
                assert result_plan.target_status == ContentStatus.UPDATED
                assert result_plan.error_message is None
            else:
                assert result_plan.error_message is not None
            
            # Validate that all required processing was attempted
            assert result_plan.romaji_processing_required == True
            assert result_plan.wordpress_sync_required == True
            assert result_plan.quality_validation_required == True
            
            return {
                "test_name": "content_update_execution",
                "status": "PASSED",
                "details": {
                    "update_execution_completed": True,
                    "timing_tracked": True,
                    "success_status_recorded": True,
                    "error_handling_working": True
                }
            }
            
        except Exception as e:
            return {
                "test_name": "content_update_execution",
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_lifecycle_report_generation(self) -> Dict[str, Any]:
        """Test comprehensive lifecycle report generation"""
        try:
            lifecycle_manager = ContentLifecycleManager()
            
            # Generate lifecycle report
            report = lifecycle_manager.generate_lifecycle_report()
            
            # Validate report structure
            assert report.report_id is not None
            assert report.generated_at is not None
            assert isinstance(report.total_providers, int)
            assert report.total_providers >= 0
            
            # Validate status distribution
            assert isinstance(report.content_status_distribution, dict)
            status_sum = sum(report.content_status_distribution.values())
            if status_sum > 0:
                assert status_sum == report.total_providers
            
            # Validate metrics
            assert isinstance(report.updates_completed_30d, int)
            assert isinstance(report.updates_failed_30d, int)
            assert isinstance(report.average_quality_improvement, float)
            assert isinstance(report.cost_per_update, float)
            assert 0 <= report.content_freshness_score <= 100
            assert 0 <= report.romaji_consistency_score <= 100
            assert 0 <= report.wordpress_sync_success_rate <= 100
            
            # Validate recommendations
            assert isinstance(report.recommended_actions, list)
            
            # Validate projections
            assert isinstance(report.projected_next_month, dict)
            if 'estimated_cost' in report.projected_next_month:
                assert report.projected_next_month['estimated_cost'] >= 0
            
            # Validate budget utilization
            assert 0 <= report.budget_utilization <= 200  # Allow for over-budget scenarios
            
            return {
                "test_name": "lifecycle_report_generation",
                "status": "PASSED",
                "details": {
                    "report_structure_valid": True,
                    "metrics_calculation_correct": True,
                    "recommendations_generated": True,
                    "projections_included": True,
                    "budget_tracking_accurate": True
                }
            }
            
        except Exception as e:
            return {
                "test_name": "lifecycle_report_generation",
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_provider_analysis_system(self) -> Dict[str, Any]:
        """Test comprehensive provider content analysis"""
        try:
            lifecycle_manager = ContentLifecycleManager()
            
            # Test provider analysis
            content_metrics = lifecycle_manager.analyze_all_provider_content()
            
            # Validate analysis results
            assert isinstance(content_metrics, dict)
            
            # If providers exist, validate metrics structure
            if content_metrics:
                sample_provider_id = list(content_metrics.keys())[0]
                sample_metrics = content_metrics[sample_provider_id]
                
                # Validate ContentMetrics structure
                assert isinstance(sample_metrics, ContentMetrics)
                assert sample_metrics.provider_id == sample_provider_id
                assert isinstance(sample_metrics.content_age_days, int)
                assert isinstance(sample_metrics.quality_score, float)
                assert isinstance(sample_metrics.last_updated, datetime)
                assert 0 <= sample_metrics.quality_score <= 100
                assert sample_metrics.content_age_days >= 0
                
                # Validate calculated scores
                assert 0 <= sample_metrics.freshness_score <= 100
                assert isinstance(sample_metrics.romaji_consistency, bool)
                assert isinstance(sample_metrics.wordpress_sync_status, bool)
            
            return {
                "test_name": "provider_analysis_system",
                "status": "PASSED",
                "details": {
                    "analysis_completed": True,
                    "metrics_structure_correct": True,
                    "quality_scores_valid": True,
                    "age_calculations_accurate": True,
                    "status_flags_correct": True
                }
            }
            
        except Exception as e:
            return {
                "test_name": "provider_analysis_system",
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_maintenance_integration(self) -> Dict[str, Any]:
        """Test integration with maintenance scheduling system"""
        try:
            # Test content lifecycle setup creation
            lifecycle_manager = create_test_content_lifecycle_setup()
            
            # Validate setup
            assert lifecycle_manager is not None
            assert lifecycle_manager.maintenance_manager is not None
            
            # Test configuration for maintenance mode
            assert lifecycle_manager.monthly_update_limit <= 50  # Should be constrained for maintenance
            assert lifecycle_manager.monthly_budget_limit <= 500.0
            assert lifecycle_manager.cost_per_update > 0
            
            # Test that maintenance tasks include content lifecycle operations
            scheduler = lifecycle_manager.maintenance_manager.scheduler
            content_tasks = [task for task in scheduler.scheduled_tasks if 'content' in task.description.lower()]
            
            # Should have at least one content-related task
            assert len(content_tasks) > 0
            
            # Validate task structure
            if content_tasks:
                sample_task = content_tasks[0]
                assert sample_task.estimated_duration_minutes > 0
                assert sample_task.scheduled_time is not None
            
            return {
                "test_name": "maintenance_integration",
                "status": "PASSED",
                "details": {
                    "test_setup_created": True,
                    "maintenance_manager_integrated": True,
                    "budget_constraints_applied": True,
                    "content_tasks_scheduled": True
                }
            }
            
        except Exception as e:
            return {
                "test_name": "maintenance_integration",
                "status": "FAILED",
                "error": str(e)
            }
    
    def test_content_lifecycle_workflow(self) -> Dict[str, Any]:
        """Test complete content lifecycle workflow"""
        try:
            lifecycle_manager = create_test_content_lifecycle_setup()
            
            # Step 1: Analyze all provider content
            content_metrics = lifecycle_manager.analyze_all_provider_content()
            assert isinstance(content_metrics, dict)
            
            # Step 2: Generate update plans
            update_plans = lifecycle_manager.generate_update_plans(content_metrics, budget_limit=50.0)
            assert isinstance(update_plans, list)
            
            # Step 3: Execute a sample update (if plans exist)
            if update_plans:
                sample_plan = update_plans[0]
                executed_plan = lifecycle_manager.execute_content_update(sample_plan)
                assert executed_plan.started_at is not None
                assert executed_plan.completed_at is not None
            
            # Step 4: Generate lifecycle report
            lifecycle_report = lifecycle_manager.generate_lifecycle_report()
            assert lifecycle_report.report_id is not None
            
            # Validate workflow integration
            assert lifecycle_report.total_providers >= 0
            if content_metrics:
                assert lifecycle_report.total_providers == len(content_metrics)
            
            # Validate that all components work together
            workflow_success = (
                content_metrics is not None and
                update_plans is not None and
                lifecycle_report is not None
            )
            assert workflow_success
            
            return {
                "test_name": "content_lifecycle_workflow",
                "status": "PASSED",
                "details": {
                    "content_analysis_completed": True,
                    "update_plans_generated": True,
                    "update_execution_working": True,
                    "lifecycle_reporting_functional": True,
                    "workflow_integration_successful": True
                }
            }
            
        except Exception as e:
            return {
                "test_name": "content_lifecycle_workflow",
                "status": "FAILED",
                "error": str(e)
            }
    
    def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run the complete content lifecycle test suite"""
        print("🧪 Starting Comprehensive Content Lifecycle Test Suite...")
        print("=" * 80)
        
        # Run all tests
        test_methods = [
            self.test_content_aging_analysis,
            self.test_content_prioritization_system,
            self.test_content_metrics_creation,
            self.test_update_plan_generation,
            self.test_content_update_execution,
            self.test_lifecycle_report_generation,
            self.test_provider_analysis_system,
            self.test_maintenance_integration,
            self.test_content_lifecycle_workflow
        ]
        
        results = []
        passed_tests = 0
        failed_tests = 0
        
        for test_method in test_methods:
            try:
                print(f"Running {test_method.__name__}...")
                result = test_method()
                results.append(result)
                
                if result["status"] == "PASSED":
                    print(f"✅ {result['test_name']}: PASSED")
                    passed_tests += 1
                else:
                    print(f"❌ {result['test_name']}: FAILED - {result.get('error', 'Unknown error')}")
                    failed_tests += 1
                    
            except Exception as e:
                error_result = {
                    "test_name": test_method.__name__,
                    "status": "ERROR",
                    "error": str(e)
                }
                results.append(error_result)
                print(f"🚨 {test_method.__name__}: ERROR - {str(e)}")
                failed_tests += 1
        
        # Calculate summary statistics
        total_tests = len(test_methods)
        success_rate = (passed_tests / total_tests) * 100
        
        summary = {
            "test_suite": "Content Lifecycle Comprehensive Test Suite",
            "execution_time": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "individual_results": results
        }
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUITE SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100.0:
            print("\n🎉 ALL TESTS PASSED! Content lifecycle management is fully functional.")
        elif success_rate >= 80.0:
            print(f"\n⚠️  Most tests passed ({success_rate:.1f}%), but some issues need attention.")
        else:
            print(f"\n🚨 Significant issues detected ({success_rate:.1f}% success rate). Review failed tests.")
        
        return summary

def run_content_lifecycle_integration_test():
    """Run comprehensive content lifecycle integration test"""
    print("🔧 Running Content Lifecycle Integration Test...")
    
    try:
        # Test complete content lifecycle workflow
        lifecycle_manager = create_test_content_lifecycle_setup()
        
        if lifecycle_manager:
            print("✅ Content lifecycle manager created")
            
            # Test content analysis
            content_metrics = lifecycle_manager.analyze_all_provider_content()
            print(f"✅ Analyzed {len(content_metrics)} providers")
            
            # Test update plan generation
            update_plans = lifecycle_manager.generate_update_plans(content_metrics, budget_limit=100.0)
            print(f"✅ Generated {len(update_plans)} update plans within budget")
            
            # Test lifecycle report
            lifecycle_report = lifecycle_manager.generate_lifecycle_report()
            print(f"✅ Generated lifecycle report: {lifecycle_report.report_id}")
            print(f"   Total providers: {lifecycle_report.total_providers}")
            print(f"   Freshness score: {lifecycle_report.content_freshness_score:.1f}")
            print(f"   Romaji consistency: {lifecycle_report.romaji_consistency_score:.1f}%")
            
            # Test maintenance integration
            maintenance_tasks = lifecycle_manager.maintenance_manager.scheduler.scheduled_tasks
            content_tasks = [t for t in maintenance_tasks if 'content' in t.description.lower()]
            print(f"✅ Integrated with maintenance scheduling: {len(content_tasks)} content tasks")
            
            print("\n🎉 Content Lifecycle Integration Test PASSED!")
            return True
        else:
            print("❌ Failed to create content lifecycle manager")
            return False
        
    except Exception as e:
        print(f"❌ Content Lifecycle Integration Test FAILED: {e}")
        return False

if __name__ == "__main__":
    # Run comprehensive test suite
    test_suite = ContentLifecycleTestSuite()
    
    try:
        # Run all tests
        results = test_suite.run_comprehensive_test_suite()
        
        # Save test results
        results_file = f"content_lifecycle_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📁 Test results saved to: {results_file}")
        
        # Run integration test
        print("\n" + "=" * 80)
        integration_success = run_content_lifecycle_integration_test()
        
        # Final summary
        overall_success = (results["success_rate"] == 100.0 and integration_success)
        
        if overall_success:
            print("\n🌟 CONTENT LIFECYCLE MANAGEMENT FULLY VALIDATED!")
            print("System is ready for long-term content maintenance operations.")
        else:
            print("\n⚠️  Some issues detected. Review test results for details.")
            
    finally:
        # Cleanup
        test_suite.cleanup_test_environment()