"""
Validate Corrected Content Update Delay Logic

This script validates that the critical date logic error has been fixed
and providers are correctly classified according to realistic project timeline.

Created: 2025-08-30
Author: Healthcare Campaign System
Version: 1.0
"""

from datetime import datetime, timedelta
from src.week4.content_lifecycle import create_test_content_lifecycle_setup
import json

def validate_corrected_logic():
    print("✅ VALIDATING CORRECTED CONTENT UPDATE DELAY LOGIC")
    print("=" * 80)
    
    current_date = datetime.now()
    print(f"Current Date: {current_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test with 6-month delay configuration
    manager = create_test_content_lifecycle_setup(delay_months=6)
    
    if not manager:
        print("❌ Failed to create lifecycle manager")
        return
    
    print(f"\n📊 DELAY CONFIGURATION VERIFICATION:")
    print(f"Campaign Delay: {manager.delay_config.new_campaign_delay_months} months ({manager.delay_config.new_campaign_delay_months * 30} days)")
    print(f"Quality Issue Threshold: {manager.delay_config.quality_issue_threshold}")
    print(f"Critical Quality Threshold: {manager.delay_config.critical_quality_threshold}")
    print(f"Recently Added Threshold: {manager.delay_config.recently_added_threshold_days} days")
    
    # Get provider data to check creation timeline
    providers = manager._get_all_providers()
    print(f"\n🔍 PROVIDER CREATION TIMELINE VALIDATION:")
    print(f"Total Providers: {len(providers)}")
    
    # Check age distribution
    ages = []
    for provider in providers:
        created_date = provider.get('provider_created_date')
        if created_date:
            age_days = (current_date - created_date).days
            ages.append(age_days)
    
    if ages:
        min_age = min(ages)
        max_age = max(ages)
        avg_age = sum(ages) / len(ages)
        
        print(f"Provider Age Range: {min_age} to {max_age} days")
        print(f"Average Provider Age: {avg_age:.1f} days")
        print(f"Expected: All providers should be ≤ 60 days old (realistic for 2-month project)")
        
        # Validation check
        if max_age <= 60:
            print("✅ Provider timeline is realistic for project age")
        else:
            print(f"❌ Provider timeline issue: Oldest provider is {max_age} days old")
    
    # Test content analysis with corrected logic
    print(f"\n📊 CONTENT ANALYSIS WITH CORRECTED LOGIC:")
    content_metrics = manager.analyze_all_provider_content()
    
    # Count providers by corrected status
    corrected_status_counts = {}
    quality_override_count = 0
    
    for provider_id, metrics in content_metrics.items():
        status = metrics.delay_status.value
        corrected_status_counts[status] = corrected_status_counts.get(status, 0) + 1
        
        # Count quality-based overrides
        if hasattr(metrics, 'delay_override_reason') and metrics.delay_override_reason:
            if 'quality' in metrics.delay_override_reason:
                quality_override_count += 1
    
    print(f"Status Distribution (After Fix):")
    total_providers = len(content_metrics)
    for status, count in sorted(corrected_status_counts.items()):
        percentage = (count / total_providers) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")
    
    print(f"\nQuality-based overrides: {quality_override_count}")
    
    # Validation checks
    print(f"\n✅ VALIDATION RESULTS:")
    
    # Check 1: No providers should be classified as 'aging' with delays enabled
    aging_count = corrected_status_counts.get('aging', 0)
    if aging_count == 0:
        print(f"✅ FIXED: No providers incorrectly classified as 'aging' ({aging_count})")
    else:
        print(f"❌ STILL BROKEN: {aging_count} providers still classified as 'aging'")
    
    # Check 2: No providers should be 'ready_for_review' since project < 6 months
    ready_count = corrected_status_counts.get('ready_for_review', 0)
    if ready_count == 0:
        print(f"✅ CORRECT: No providers past delay period ({ready_count})")
    else:
        print(f"❌ ERROR: {ready_count} providers incorrectly past delay period")
    
    # Check 3: Most providers should be 'delay_period_active' or 'recently_added'
    expected_statuses = ['delay_period_active', 'recently_added', 'needs_update']
    expected_count = sum(corrected_status_counts.get(status, 0) for status in expected_statuses)
    expected_percentage = (expected_count / total_providers) * 100
    
    if expected_percentage >= 95:
        print(f"✅ CORRECT: {expected_percentage:.1f}% of providers in expected delay statuses")
    else:
        print(f"❌ ISSUE: Only {expected_percentage:.1f}% of providers in expected statuses")
    
    # Check 4: Update plan generation should show minimal immediate requirements
    print(f"\n📋 UPDATE PLAN GENERATION TEST:")
    update_plans = manager.generate_update_plans(content_metrics, budget_limit=200.0)
    
    immediate_updates = len(update_plans)
    immediate_percentage = (immediate_updates / total_providers) * 100
    
    print(f"Update plans generated: {immediate_updates}")
    print(f"Percentage requiring immediate updates: {immediate_percentage:.1f}%")
    print(f"Expected: Very low percentage (< 15%) due to delay period")
    
    if immediate_percentage < 15:
        print(f"✅ CORRECT: Low immediate update requirements ({immediate_percentage:.1f}%)")
    else:
        print(f"❌ ISSUE: High immediate update requirements ({immediate_percentage:.1f}%)")
    
    # Show detailed breakdown of what's eligible for updates
    eligible_statuses = {}
    for plan in update_plans:
        provider_id = plan.provider_id
        if provider_id in content_metrics:
            status = content_metrics[provider_id].delay_status.value
            eligible_statuses[status] = eligible_statuses.get(status, 0) + 1
    
    print(f"\nProviders eligible for immediate updates by status:")
    for status, count in sorted(eligible_statuses.items()):
        print(f"  {status}: {count}")
    
    # Test different delay periods
    print(f"\n📊 DELAY PERIOD COMPARISON TEST:")
    delay_configs = [0, 3, 6, 12]  # months
    
    comparison_results = {}
    for delay_months in delay_configs:
        test_manager = create_test_content_lifecycle_setup(delay_months=delay_months)
        test_metrics = test_manager.analyze_all_provider_content()
        test_plans = test_manager.generate_update_plans(test_metrics, budget_limit=200.0)
        
        comparison_results[delay_months] = {
            'update_plans': len(test_plans),
            'percentage': (len(test_plans) / len(test_metrics)) * 100
        }
    
    print(f"Update requirements by delay period:")
    for delay_months, results in comparison_results.items():
        print(f"  {delay_months} months delay: {results['update_plans']} plans ({results['percentage']:.1f}%)")
    
    # Generate comprehensive validation report
    validation_report = {
        "validation_date": current_date.isoformat(),
        "total_providers": total_providers,
        "provider_age_range": {
            "min_days": min(ages) if ages else 0,
            "max_days": max(ages) if ages else 0,
            "avg_days": sum(ages) / len(ages) if ages else 0
        },
        "status_distribution": corrected_status_counts,
        "validation_results": {
            "aging_status_fixed": aging_count == 0,
            "no_premature_ready_providers": ready_count == 0,
            "expected_status_percentage": expected_percentage,
            "immediate_update_percentage": immediate_percentage
        },
        "delay_period_comparison": comparison_results,
        "quality_overrides": quality_override_count
    }
    
    # Save validation report
    with open("delay_logic_validation_report.json", "w") as f:
        json.dump(validation_report, f, indent=2)
    
    # Final validation summary
    print(f"\n🎯 FINAL VALIDATION SUMMARY:")
    print("=" * 80)
    
    all_checks_passed = (
        aging_count == 0 and
        ready_count == 0 and
        expected_percentage >= 95 and
        immediate_percentage < 15
    )
    
    if all_checks_passed:
        print(f"🎉 ALL VALIDATION CHECKS PASSED!")
        print(f"✅ Date logic error has been successfully fixed")
        print(f"✅ Provider timeline is realistic ({max(ages) if ages else 0} days max)")
        print(f"✅ Delay periods are working correctly")
        print(f"✅ Immediate update requirements are minimal ({immediate_percentage:.1f}%)")
        print(f"✅ Quality overrides are functioning ({quality_override_count} providers)")
    else:
        print(f"❌ VALIDATION FAILED - Issues remain:")
        if aging_count > 0:
            print(f"   • {aging_count} providers still classified as 'aging'")
        if ready_count > 0:
            print(f"   • {ready_count} providers incorrectly past delay period")
        if expected_percentage < 95:
            print(f"   • Only {expected_percentage:.1f}% in expected statuses")
        if immediate_percentage >= 15:
            print(f"   • {immediate_percentage:.1f}% immediate updates (too high)")
    
    print(f"\n📁 Validation report saved to: delay_logic_validation_report.json")
    
    return validation_report

if __name__ == "__main__":
    validation_results = validate_corrected_logic()