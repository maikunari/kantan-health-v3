#!/usr/bin/env python3
"""
Test Script for Claude Mega-Batch Processor
Tests the new mega-batch functionality with a small sample of providers.
"""

import sys
from claude_mega_batch_processor import ClaudeMegaBatchProcessor, run_mega_batch_content_generation, filter_providers_needing_content
from postgres_integration import PostgresIntegration, Provider

def test_mega_batch_processor():
    """Test the mega-batch processor with a small sample"""
    print("🧪 TESTING CLAUDE MEGA-BATCH PROCESSOR")
    print("=" * 50)
    
    try:
        # Initialize
        processor = ClaudeMegaBatchProcessor()
        db = PostgresIntegration()
        
        # Get a small sample of providers that need content
        session = db.Session()
        
        # Get providers without AI descriptions
        sample_providers = session.query(Provider).filter(
            Provider.ai_description.is_(None)
        ).limit(4).all()
        
        if not sample_providers:
            # If no providers without descriptions, get any providers for testing
            sample_providers = session.query(Provider).limit(4).all()
            print("⚠️ No providers without descriptions found, using sample for testing")
        
        session.close()
        
        print(f"📊 Testing with {len(sample_providers)} providers:")
        for i, provider in enumerate(sample_providers, 1):
            print(f"   {i}. {provider.provider_name} ({provider.city})")
        
        print(f"\n🚀 Running mega-batch processing...")
        
        # Test the mega-batch processor
        results = processor.process_providers_mega_batch(sample_providers, batch_size=4)
        
        print(f"\n📊 TEST RESULTS:")
        print(f"   ✅ Updated: {results['updated']}")
        print(f"   ❌ Errors: {results['errors']}")
        print(f"   📈 Success rate: {results['updated']/len(sample_providers)*100:.1f}%")
        
        # Verify the results by checking one provider
        if results['updated'] > 0:
            session = db.Session()
            updated_provider = session.query(Provider).filter(
                Provider.provider_name == sample_providers[0].provider_name
            ).first()
            
            if updated_provider:
                print(f"\n✅ CONTENT VERIFICATION FOR: {updated_provider.provider_name}")
                print(f"📄 Description: {len(updated_provider.ai_description.split()) if updated_provider.ai_description else 0} words")
                print(f"📝 Excerpt: {len(updated_provider.ai_excerpt.split()) if updated_provider.ai_excerpt else 0} words")
                print(f"⭐ Review Summary: {len(updated_provider.review_summary.split()) if updated_provider.review_summary else 0} words")
                print(f"🗣️ English Summary: {len(updated_provider.english_experience_summary.split()) if updated_provider.english_experience_summary else 0} words")
                print(f"📊 Status: {updated_provider.status}")
                
                print(f"\n📄 SAMPLE DESCRIPTION:")
                print(f"{updated_provider.ai_description[:200] if updated_provider.ai_description else 'No description'}...")
            
            session.close()
        
        return results['updated'] > 0
        
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def compare_efficiency():
    """Compare the efficiency of mega-batch vs individual processing"""
    print("\n💰 EFFICIENCY COMPARISON")
    print("=" * 30)
    
    # Sample provider count
    total_providers = 102
    
    print("OLD APPROACH (Individual Files):")
    print(f"   📄 Descriptions: {(total_providers + 2) // 3} API calls (batch_size=3)")
    print(f"   📝 Excerpts: {(total_providers + 2) // 3} API calls (batch_size=3)")
    print(f"   ⭐ Review Summaries: {total_providers} API calls (individual)")
    print(f"   🗣️ English Summaries: {total_providers} API calls (individual)")
    old_total = ((total_providers + 2) // 3) * 2 + total_providers * 2
    print(f"   🔢 TOTAL API CALLS: {old_total}")
    
    print("\nNEW APPROACH (Mega-Batch):")
    batch_size = 4
    new_total = (total_providers + batch_size - 1) // batch_size
    print(f"   🚀 All Content Types: {new_total} API calls (batch_size={batch_size})")
    print(f"   🔢 TOTAL API CALLS: {new_total}")
    
    efficiency_gain = ((old_total - new_total) / old_total) * 100
    print(f"\n📈 EFFICIENCY IMPROVEMENT:")
    print(f"   💾 API Calls Reduced: {old_total - new_total}")
    print(f"   📊 Efficiency Gain: {efficiency_gain:.1f}%")
    print(f"   💰 Cost Reduction: ~{efficiency_gain:.1f}% (assuming same model)")

if __name__ == "__main__":
    # Run tests
    success = test_mega_batch_processor()
    
    # Show efficiency comparison
    compare_efficiency()
    
    if success:
        print(f"\n🎉 MEGA-BATCH PROCESSOR TEST SUCCESSFUL!")
        print(f"Ready to replace individual content generation scripts.")
    else:
        print(f"\n❌ Test failed. Please check the implementation.")
        sys.exit(1) 