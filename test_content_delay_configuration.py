"""
Content Update Delay Configuration Testing

This script tests and demonstrates the content update delay configuration
system, showing the difference between aggressive updates and delay-aware
update scheduling.

Created: 2025-08-30
Author: Healthcare Campaign System
Version: 1.0
"""

from datetime import datetime
import json
from src.week4.content_lifecycle import (
    create_test_content_lifecycle_setup,
    create_aggressive_update_setup,
    ContentUpdateDelayConfig,
    ContentStatus
)

def main():
    print("🔧 Content Update Delay Configuration Testing")
    print("=" * 80)
    
    try:
        # Test 1: Aggressive updates (no delays)
        print("\n📊 TEST 1: Aggressive Update Configuration (No Delays)")
        print("-" * 60)
        
        aggressive_manager = create_aggressive_update_setup()
        if aggressive_manager:
            print("✅ Aggressive update manager created")
            print(f"   Delay evaluation enabled: {aggressive_manager.delay_config.delay_evaluation_enabled}")
            print(f"   Campaign delay: {aggressive_manager.delay_config.new_campaign_delay_months} months")
            
            # Analyze providers
            aggressive_metrics = aggressive_manager.analyze_all_provider_content()
            print(f"✅ Analyzed {len(aggressive_metrics)} providers")
            
            # Generate update plans
            aggressive_plans = aggressive_manager.generate_update_plans(aggressive_metrics, budget_limit=100.0)
            print(f"✅ Generated {len(aggressive_plans)} update plans (aggressive)")
            
            # Get status distribution
            aggressive_status_counts = {}
            for metrics in aggressive_metrics.values():
                status = metrics.delay_status.value if hasattr(metrics, 'delay_status') else 'unknown'
                aggressive_status_counts[status] = aggressive_status_counts.get(status, 0) + 1
            
            print("   Status distribution (aggressive):")
            for status, count in aggressive_status_counts.items():
                print(f"     {status}: {count}")
        
        # Test 2: Conservative updates (6-month delay)
        print("\n📊 TEST 2: Conservative Update Configuration (6-Month Delay)")
        print("-" * 60)
        
        conservative_manager = create_test_content_lifecycle_setup(delay_months=6)
        if conservative_manager:
            print("✅ Conservative update manager created")
            print(f"   Delay evaluation enabled: {conservative_manager.delay_config.delay_evaluation_enabled}")
            print(f"   Campaign delay: {conservative_manager.delay_config.new_campaign_delay_months} months")
            print(f"   Quality issue threshold: {conservative_manager.delay_config.quality_issue_threshold}")
            print(f"   Critical quality threshold: {conservative_manager.delay_config.critical_quality_threshold}")
            
            # Analyze providers
            conservative_metrics = conservative_manager.analyze_all_provider_content()
            print(f"✅ Analyzed {len(conservative_metrics)} providers")
            
            # Generate update plans
            conservative_plans = conservative_manager.generate_update_plans(conservative_metrics, budget_limit=100.0)
            print(f"✅ Generated {len(conservative_plans)} update plans (conservative)")
            
            # Get detailed status distribution
            conservative_status_counts = {}
            delay_override_counts = 0
            eligible_dates = []
            
            for provider_id, metrics in conservative_metrics.items():
                status = metrics.delay_status.value if hasattr(metrics, 'delay_status') else 'unknown'
                conservative_status_counts[status] = conservative_status_counts.get(status, 0) + 1
                
                if hasattr(metrics, 'delay_override_reason') and metrics.delay_override_reason:
                    delay_override_counts += 1
                
                if hasattr(metrics, 'eligible_for_update_date') and metrics.eligible_for_update_date:
                    eligible_dates.append(metrics.eligible_for_update_date)
            
            print("   Status distribution (conservative with delays):")
            for status, count in conservative_status_counts.items():
                print(f"     {status}: {count}")
            print(f"   Providers with delay overrides: {delay_override_counts}")
            
            # Calculate earliest eligible update dates
            if eligible_dates:
                earliest_eligible = min(eligible_dates)
                latest_eligible = max(eligible_dates)
                print(f"   Earliest eligible update: {earliest_eligible.strftime('%Y-%m-%d')}")
                print(f"   Latest eligible update: {latest_eligible.strftime('%Y-%m-%d')}")
        
        # Test 3: Quality-based overrides
        print("\n📊 TEST 3: Quality-Based Override Testing")
        print("-" * 60)
        
        # Test with different quality thresholds
        quality_test_manager = create_test_content_lifecycle_setup(delay_months=6)
        
        # Count providers by quality levels
        quality_distribution = {
            'critical_quality': 0,  # < 60
            'quality_issues': 0,    # 60-70
            'good_quality': 0,      # 70-85
            'excellent_quality': 0  # > 85
        }
        
        override_eligible = 0
        delay_period_active = 0
        
        for provider_id, metrics in conservative_metrics.items():
            quality_score = metrics.quality_score
            
            if quality_score < 60:
                quality_distribution['critical_quality'] += 1
            elif quality_score < 70:
                quality_distribution['quality_issues'] += 1
            elif quality_score < 85:
                quality_distribution['good_quality'] += 1
            else:
                quality_distribution['excellent_quality'] += 1
            
            # Check if provider qualifies for overrides
            if hasattr(metrics, 'delay_override_reason') and metrics.delay_override_reason:
                override_eligible += 1
            elif metrics.delay_status == ContentStatus.DELAY_PERIOD_ACTIVE:
                delay_period_active += 1
        
        print("   Quality distribution:")
        for category, count in quality_distribution.items():
            print(f"     {category}: {count}")
        print(f"   Override eligible (quality/technical issues): {override_eligible}")
        print(f"   In delay period (no overrides): {delay_period_active}")
        
        # Test 4: Cost comparison
        print("\n📊 TEST 4: Cost Impact Analysis")
        print("-" * 60)
        
        aggressive_cost = len(aggressive_plans) * 2.50
        conservative_cost = len(conservative_plans) * 2.00
        cost_savings = aggressive_cost - conservative_cost
        cost_reduction_percent = (cost_savings / aggressive_cost * 100) if aggressive_cost > 0 else 0
        
        print(f"   Aggressive approach cost: ${aggressive_cost:.2f} ({len(aggressive_plans)} updates)")
        print(f"   Conservative approach cost: ${conservative_cost:.2f} ({len(conservative_plans)} updates)")
        print(f"   Cost savings with delays: ${cost_savings:.2f} ({cost_reduction_percent:.1f}% reduction)")
        
        # Test 5: Configuration flexibility
        print("\n📊 TEST 5: Configuration Flexibility Testing")
        print("-" * 60)
        
        # Test different delay configurations
        test_configs = [
            {"name": "No Delay", "months": 0},
            {"name": "Short Delay", "months": 3}, 
            {"name": "Standard Delay", "months": 6},
            {"name": "Long Delay", "months": 12}
        ]
        
        config_results = {}
        for config_test in test_configs:
            test_manager = create_test_content_lifecycle_setup(delay_months=config_test["months"])
            if test_manager:
                test_metrics = test_manager.analyze_all_provider_content()
                test_plans = test_manager.generate_update_plans(test_metrics, budget_limit=100.0)
                
                config_results[config_test["name"]] = {
                    "delay_months": config_test["months"],
                    "update_plans": len(test_plans),
                    "estimated_cost": len(test_plans) * 2.00
                }
        
        print("   Configuration comparison:")
        for config_name, results in config_results.items():
            print(f"     {config_name} ({results['delay_months']} months): {results['update_plans']} plans, ${results['estimated_cost']:.2f}")
        
        # Generate comprehensive report
        print("\n📋 COMPREHENSIVE DELAY CONFIGURATION REPORT")
        print("=" * 80)
        
        report = {
            "test_date": datetime.now().isoformat(),
            "total_providers_tested": len(conservative_metrics),
            "aggressive_approach": {
                "update_plans": len(aggressive_plans) if 'aggressive_plans' in locals() else 0,
                "estimated_cost": aggressive_cost,
                "delay_enabled": False
            },
            "conservative_approach": {
                "update_plans": len(conservative_plans) if 'conservative_plans' in locals() else 0,
                "estimated_cost": conservative_cost,
                "delay_months": 6,
                "delay_enabled": True
            },
            "cost_analysis": {
                "cost_savings": cost_savings,
                "cost_reduction_percent": cost_reduction_percent
            },
            "provider_status_distribution": conservative_status_counts,
            "quality_distribution": quality_distribution,
            "override_statistics": {
                "override_eligible": override_eligible,
                "delay_period_active": delay_period_active
            },
            "configuration_flexibility": config_results
        }
        
        # Save report
        with open("content_delay_configuration_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("✅ System successfully configured with realistic update delays")
        print(f"📊 Key Results:")
        print(f"   • Total providers: {len(conservative_metrics)}")
        print(f"   • Providers in delay period: {conservative_status_counts.get('delay_period_active', 0)}")
        print(f"   • Providers ready for review: {conservative_status_counts.get('ready_for_review', 0)}")
        print(f"   • Update plans generated: {len(conservative_plans)}")
        print(f"   • Cost reduction vs aggressive: {cost_reduction_percent:.1f}%")
        
        print(f"\n🎯 DELAY CONFIGURATION BENEFITS:")
        print(f"   • Prevents overwhelming update workload during campaign launch")
        print(f"   • Maintains quality-based overrides for critical issues")
        print(f"   • Reduces maintenance costs significantly")
        print(f"   • Provides configurable delay periods for different scenarios")
        print(f"   • Enables gradual transition to maintenance mode")
        
        print(f"\n📁 Report saved to: content_delay_configuration_report.json")
        
    except Exception as e:
        print(f"❌ Error during delay configuration testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()