"""
Debug Delay Classification Logic Step by Step

This script traces through the exact logic causing providers to be
misclassified with delay periods.
"""

from datetime import datetime, timedelta
from src.week4.content_lifecycle import create_test_content_lifecycle_setup

def debug_classification_logic():
    print("🔍 DEBUGGING DELAY CLASSIFICATION STEP BY STEP")
    print("=" * 80)
    
    # Create manager
    manager = create_test_content_lifecycle_setup(delay_months=6)
    current_time = datetime.now()
    
    print(f"Current Time: {current_time}")
    print(f"Delay Config: {manager.delay_config.new_campaign_delay_months} months = {manager.delay_config.new_campaign_delay_months * 30} days")
    
    # Get a few sample providers and trace through the logic
    providers = manager._get_all_providers()
    
    print(f"\nTesting 5 sample providers through classification logic:")
    
    test_indices = [1, 50, 100, 200, 400]  # Sample providers at different ages
    
    for i in test_indices:
        if i < len(providers):
            provider = providers[i-1]  # Adjust for 0-based indexing
            provider_id = provider['id']
            
            print(f"\n--- PROVIDER {provider_id} (index {i}) ---")
            
            # Step 1: Extract dates
            created_date = provider.get('provider_created_date')
            last_updated = provider.get('last_updated')
            quality_score = provider.get('quality_score', 75.0)
            
            print(f"Created: {created_date}")
            print(f"Updated: {last_updated}")
            print(f"Quality: {quality_score}")
            
            # Step 2: Calculate ages
            provider_age_days = (current_time - created_date).days if created_date else 0
            content_age_days = (current_time - last_updated).days if last_updated else 0
            
            print(f"Provider age: {provider_age_days} days")
            print(f"Content age: {content_age_days} days")
            
            # Step 3: Manual delay logic check
            delay_days = 6 * 30  # 180 days
            recently_added_threshold = 30
            
            print(f"Delay period: {delay_days} days")
            print(f"Recently added threshold: {recently_added_threshold} days")
            
            # Step 4: Manual status determination
            if provider_age_days <= recently_added_threshold:
                manual_status = "recently_added"
            elif provider_age_days < delay_days:
                manual_status = "delay_period_active"
            else:
                manual_status = "past_delay_period (SHOULD NOT HAPPEN)"
            
            print(f"Expected manual status: {manual_status}")
            
            # Step 5: Check for overrides
            override_checks = {
                'quality_critical': quality_score < 60.0,
                'quality_issue': quality_score < 70.0,
                'wp_sync': not provider.get('wordpress_sync_status', True),
                'romaji': not provider.get('romaji_consistency', True),
                'manual': provider.get('manual_update_requested', False)
            }
            
            has_override = any(override_checks.values())
            print(f"Override checks: {override_checks}")
            print(f"Has override: {has_override}")
            
            # Step 6: Run through actual analyzer
            actual_status = manager.aging_analyzer.analyze_content_age_with_delay(provider)
            print(f"ACTUAL analyzer result: {actual_status.value}")
            
            # Step 7: Check if there's a mismatch
            if has_override:
                expected_result = "needs_update"
            else:
                expected_result = manual_status
                
            if actual_status.value != expected_result and actual_status.value not in ['needs_update', manual_status]:
                print(f"❌ MISMATCH: Expected {expected_result}, got {actual_status.value}")
            else:
                print(f"✅ MATCH: Status is correct")
    
    # Now test the full analysis
    print(f"\n📊 FULL ANALYSIS COMPARISON:")
    content_metrics = manager.analyze_all_provider_content()
    
    # Manual classification count
    manual_counts = {
        'recently_added': 0,
        'delay_period_active': 0,
        'past_delay_period': 0,
        'has_override': 0
    }
    
    for provider in providers:
        created_date = provider.get('provider_created_date')
        quality_score = provider.get('quality_score', 75.0)
        
        if created_date:
            provider_age_days = (current_time - created_date).days
            
            # Check overrides
            has_override = (
                quality_score < 70.0 or
                not provider.get('wordpress_sync_status', True) or
                not provider.get('romaji_consistency', True) or
                provider.get('manual_update_requested', False)
            )
            
            if has_override:
                manual_counts['has_override'] += 1
            elif provider_age_days <= 30:
                manual_counts['recently_added'] += 1
            elif provider_age_days < 180:
                manual_counts['delay_period_active'] += 1
            else:
                manual_counts['past_delay_period'] += 1
    
    # Actual classification count
    actual_counts = {}
    for metrics in content_metrics.values():
        status = metrics.delay_status.value
        actual_counts[status] = actual_counts.get(status, 0) + 1
    
    print(f"Manual classification counts:")
    for status, count in manual_counts.items():
        print(f"  {status}: {count}")
    
    print(f"\nActual analyzer counts:")
    for status, count in sorted(actual_counts.items()):
        print(f"  {status}: {count}")
    
    # Identify the discrepancy
    expected_delay_active = manual_counts['delay_period_active']
    actual_delay_active = actual_counts.get('delay_period_active', 0)
    
    print(f"\n🚨 DISCREPANCY ANALYSIS:")
    print(f"Expected delay_period_active: {expected_delay_active}")
    print(f"Actual delay_period_active: {actual_delay_active}")
    print(f"Difference: {expected_delay_active - actual_delay_active}")
    
    # Check what's causing providers to be misclassified
    unexpected_ready = actual_counts.get('ready_for_review', 0)
    if unexpected_ready > 0:
        print(f"❌ Found {unexpected_ready} providers incorrectly classified as 'ready_for_review'")
        print("   This should be impossible with current project timeline")

if __name__ == "__main__":
    debug_classification_logic()