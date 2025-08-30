"""
Debug Content Update Date Logic Issues

This script identifies and fixes the critical date logic error in provider
age calculation and delay period classification.

Created: 2025-08-30
Author: Healthcare Campaign System
Version: 1.0
"""

from datetime import datetime, timedelta
from src.week4.content_lifecycle import create_test_content_lifecycle_setup

def debug_provider_dates():
    print("🔍 DEBUGGING PROVIDER DATE LOGIC ISSUES")
    print("=" * 80)
    
    # Get current date for reference
    current_date = datetime.now()
    print(f"Current Date: {current_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current Date Info: Year={current_date.year}, Month={current_date.month}, Day={current_date.day}")
    
    # Create lifecycle manager
    manager = create_test_content_lifecycle_setup(delay_months=6)
    
    if not manager:
        print("❌ Failed to create lifecycle manager")
        return
    
    print(f"\n📊 DELAY CONFIGURATION:")
    print(f"Campaign Delay: {manager.delay_config.new_campaign_delay_months} months")
    print(f"Delay Days Calculation: {manager.delay_config.new_campaign_delay_months * 30} days")
    print(f"Recently Added Threshold: {manager.delay_config.recently_added_threshold_days} days")
    
    # Get provider data directly
    providers = manager._get_all_providers()
    
    print(f"\n🔍 PROVIDER CREATION DATE ANALYSIS:")
    print(f"Total Providers: {len(providers)}")
    
    # Analyze first few providers in detail
    print(f"\nDetailed Analysis of First 10 Providers:")
    for i, provider in enumerate(providers[:10]):
        provider_id = provider['id']
        created_date = provider.get('provider_created_date')
        last_updated = provider.get('last_updated')
        
        print(f"\nProvider {i+1} ({provider_id}):")
        print(f"  Created Date: {created_date}")
        print(f"  Last Updated: {last_updated}")
        
        if created_date:
            age_days = (current_date - created_date).days
            age_hours = (current_date - created_date).total_seconds() / 3600
            print(f"  Age in Days: {age_days}")
            print(f"  Age in Hours: {age_hours:.1f}")
            
            # Manual delay calculation
            delay_days = 6 * 30  # 6 months * 30 days
            print(f"  Delay Period (days): {delay_days}")
            print(f"  Past Delay Period: {'YES' if age_days >= delay_days else 'NO'}")
            
            # Manual status determination
            if age_days <= 30:
                manual_status = "recently_added"
            elif age_days < delay_days:
                manual_status = "delay_period_active"
            else:
                manual_status = "past_delay_period"
            print(f"  Manual Status: {manual_status}")
    
    # Check the spread of creation dates
    print(f"\n📈 CREATION DATE DISTRIBUTION:")
    creation_dates = []
    for provider in providers:
        created_date = provider.get('provider_created_date')
        if created_date:
            age_days = (current_date - created_date).days
            creation_dates.append(age_days)
    
    if creation_dates:
        min_age = min(creation_dates)
        max_age = max(creation_dates)
        avg_age = sum(creation_dates) / len(creation_dates)
        
        print(f"Oldest Provider: {max_age} days old")
        print(f"Newest Provider: {min_age} days old")
        print(f"Average Age: {avg_age:.1f} days")
        print(f"Expected Range: 0-60 days (for ~2 month project)")
        
        # Check if any providers are older than expected
        very_old_providers = [age for age in creation_dates if age > 90]
        print(f"Providers older than 90 days: {len(very_old_providers)}")
        
        if very_old_providers:
            print(f"⚠️  WARNING: Found {len(very_old_providers)} providers older than expected!")
            print(f"Ages: {sorted(very_old_providers, reverse=True)[:10]}")  # Show top 10
    
    # Now test the actual aging analyzer
    print(f"\n🧪 AGING ANALYZER TESTING:")
    analyzer = manager.aging_analyzer
    
    # Test a few providers through the analyzer
    test_results = {}
    for i, provider in enumerate(providers[:5]):
        provider_id = provider['id']
        status = analyzer.analyze_content_age_with_delay(provider)
        
        created_date = provider.get('provider_created_date')
        age_days = (current_date - created_date).days if created_date else 0
        
        test_results[provider_id] = {
            'age_days': age_days,
            'status': status.value,
            'created_date': created_date.strftime('%Y-%m-%d') if created_date else 'None'
        }
        
        print(f"Provider {provider_id}: {age_days} days old -> Status: {status.value}")
    
    # Get full content analysis
    print(f"\n📊 FULL CONTENT ANALYSIS:")
    content_metrics = manager.analyze_all_provider_content()
    
    status_counts = {}
    age_distribution = {}
    
    for provider_id, metrics in content_metrics.items():
        status = metrics.delay_status.value
        status_counts[status] = status_counts.get(status, 0) + 1
        
        age_days = metrics.provider_age_days
        age_bucket = f"{(age_days // 30) * 30}-{(age_days // 30) * 30 + 29}"
        age_distribution[age_bucket] = age_distribution.get(age_bucket, 0) + 1
    
    print(f"Status Distribution:")
    for status, count in sorted(status_counts.items()):
        percentage = (count / len(content_metrics)) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")
    
    print(f"\nAge Distribution (days):")
    for age_range, count in sorted(age_distribution.items()):
        percentage = (count / len(content_metrics)) * 100
        print(f"  {age_range} days: {count} ({percentage:.1f}%)")
    
    # Identify the problem
    print(f"\n🚨 PROBLEM IDENTIFICATION:")
    ready_for_review = status_counts.get('aging', 0)  # 'aging' status from old system
    past_delay = status_counts.get('ready_for_review', 0)
    
    if ready_for_review > 0 or past_delay > 0:
        print(f"❌ CRITICAL ERROR FOUND:")
        print(f"   {ready_for_review} providers classified as 'aging' (should be in delay period)")
        print(f"   {past_delay} providers classified as 'ready_for_review' (impossible for new project)")
        print(f"   Expected: ALL providers should be 'recently_added' or 'delay_period_active'")
        
        # Check if the issue is in the mock data generation
        print(f"\n🔍 CHECKING MOCK DATA GENERATION:")
        sample_provider = providers[100]  # Check middle provider
        print(f"Sample Provider Creation Logic:")
        print(f"  Provider index: 100")
        print(f"  Days ago calculation: min(100 * 0.5, 90) = {min(100 * 0.5, 90)}")
        print(f"  Created date: {sample_provider['provider_created_date']}")
        print(f"  Age: {(current_date - sample_provider['provider_created_date']).days} days")
        
        if (current_date - sample_provider['provider_created_date']).days > 90:
            print(f"❌ MOCK DATA ERROR: Provider creation spread over {(current_date - sample_provider['provider_created_date']).days} days")
            print(f"   This exceeds realistic project timeline!")
    else:
        print(f"✅ Date logic appears correct - no providers past delay period")
    
    return test_results, status_counts, age_distribution

if __name__ == "__main__":
    debug_results = debug_provider_dates()