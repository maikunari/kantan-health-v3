#!/usr/bin/env python3
"""
Mega-Batch Content Generation Automation
Replaces the existing individual content generation scripts with efficient mega-batch processing.

This script:
1. Finds providers needing AI content
2. Generates all content types (descriptions, excerpts, review summaries, English summaries) in mega-batches
3. Updates the database efficiently
4. Provides comprehensive reporting

Usage:
    python3 run_mega_batch_automation.py --batch-size 4 --dry-run
    python3 run_mega_batch_automation.py --all-providers
    python3 run_mega_batch_automation.py --limit 20
"""

import argparse
import sys
import time
from typing import List, Dict, Any
from claude_mega_batch_processor import ClaudeMegaBatchProcessor, filter_providers_needing_content
from postgres_integration import PostgresIntegration, Provider

def get_providers_needing_content(db: PostgresIntegration, limit: int = None) -> List[Provider]:
    """Get providers that need AI-generated content"""
    session = db.Session()
    
    try:
        query = session.query(Provider).filter(
            Provider.ai_description.is_(None),
            Provider.status != 'published'
        )
        
        if limit:
            query = query.limit(limit)
            
        providers = query.all()
        
        print(f"📊 Found {len(providers)} providers needing AI content")
        
        if limit and len(providers) == limit:
            total_needing = session.query(Provider).filter(
                Provider.ai_description.is_(None),
                Provider.status != 'published'
            ).count()
            print(f"   (Limited to {limit} providers, {total_needing} total need content)")
        
        return providers
        
    finally:
        session.close()

def show_provider_stats(db: PostgresIntegration):
    """Show comprehensive provider statistics"""
    session = db.Session()
    
    try:
        total_providers = session.query(Provider).count()
        
        # Content statistics
        has_description = session.query(Provider).filter(Provider.ai_description.isnot(None)).count()
        has_excerpt = session.query(Provider).filter(Provider.ai_excerpt.isnot(None)).count()
        has_review_summary = session.query(Provider).filter(Provider.review_summary.isnot(None)).count()
        has_english_summary = session.query(Provider).filter(Provider.english_experience_summary.isnot(None)).count()
        
        # Status statistics
        pending = session.query(Provider).filter(Provider.status == 'pending').count()
        generated = session.query(Provider).filter(Provider.status == 'description_generated').count()
        published = session.query(Provider).filter(Provider.status == 'published').count()
        
        # Providers with all content types
        complete_content = session.query(Provider).filter(
            Provider.ai_description.isnot(None),
            Provider.ai_excerpt.isnot(None),
            Provider.review_summary.isnot(None),
            Provider.english_experience_summary.isnot(None)
        ).count()
        
        print("📊 PROVIDER CONTENT STATISTICS")
        print("=" * 40)
        print(f"   📋 Total Providers: {total_providers}")
        print(f"   📄 Has Descriptions: {has_description}")
        print(f"   📝 Has Excerpts: {has_excerpt}")
        print(f"   ⭐ Has Review Summaries: {has_review_summary}")
        print(f"   🗣️ Has English Summaries: {has_english_summary}")
        print(f"   ✅ Complete Content: {complete_content}")
        print()
        print(f"📈 STATUS DISTRIBUTION")
        print(f"   ⏳ Pending: {pending}")
        print(f"   🤖 Generated: {generated}")
        print(f"   📄 Published: {published}")
        
        completion_rate = (complete_content / total_providers) * 100 if total_providers > 0 else 0
        print(f"\n📊 Content Completion: {completion_rate:.1f}%")
        
    finally:
        session.close()

def estimate_api_costs(providers_count: int, batch_size: int):
    """Estimate API costs for the mega-batch processing"""
    api_calls = (providers_count + batch_size - 1) // batch_size
    
    # Updated estimates for claude-3-5-sonnet-20241022 with premium token allocation
    # Input tokens: ~2500 per provider (comprehensive prompts with full context)
    # Output tokens: ~1200 per provider (all content types with premium quality)
    input_tokens_per_call = 2500 * batch_size
    output_tokens_per_call = 1200 * batch_size
    
    total_input_tokens = input_tokens_per_call * api_calls
    total_output_tokens = output_tokens_per_call * api_calls
    
    # Pricing estimates (as of late 2024)
    input_cost_per_million = 3.00  # $3 per million input tokens
    output_cost_per_million = 15.00  # $15 per million output tokens
    
    input_cost = (total_input_tokens / 1_000_000) * input_cost_per_million
    output_cost = (total_output_tokens / 1_000_000) * output_cost_per_million
    total_cost = input_cost + output_cost
    
    print("💰 ESTIMATED API COSTS")
    print("=" * 25)
    print(f"   📞 API Calls: {api_calls}")
    print(f"   📊 Batch Size: {batch_size}")
    print(f"   📝 Input Tokens: {total_input_tokens:,}")
    print(f"   💬 Output Tokens: {total_output_tokens:,}")
    print(f"   💵 Input Cost: ${input_cost:.2f}")
    print(f"   💵 Output Cost: ${output_cost:.2f}")
    print(f"   🔢 TOTAL COST: ${total_cost:.2f}")
    
    return total_cost

def run_mega_batch_automation(batch_size: int = 2, limit: int = None, dry_run: bool = False):
    """Run the complete mega-batch content generation automation"""
    
    print("🚀 MEGA-BATCH CONTENT GENERATION AUTOMATION")
    print("=" * 60)
    
    try:
        # Initialize
        db = PostgresIntegration()
        processor = ClaudeMegaBatchProcessor()
        
        # Show current statistics
        show_provider_stats(db)
        
        # Get providers needing content
        providers = get_providers_needing_content(db, limit)
        
        if not providers:
            print("✅ All providers already have complete AI content!")
            return {'updated': 0, 'errors': 0, 'total_providers': 0}
        
        # Filter providers (additional validation)
        filtered_providers = filter_providers_needing_content(providers)
        
        if not filtered_providers:
            print("✅ All selected providers already have content after filtering!")
            return {'updated': 0, 'errors': 0, 'total_providers': 0}
        
        print(f"\n🎯 PROCESSING PLAN")
        print(f"   📋 Providers to process: {len(filtered_providers)}")
        print(f"   📦 Batch size: {batch_size}")
        print(f"   📞 API calls needed: {(len(filtered_providers) + batch_size - 1) // batch_size}")
        
        # Estimate costs
        estimated_cost = estimate_api_costs(len(filtered_providers), batch_size)
        
        if dry_run:
            print(f"\n🧪 DRY RUN MODE - No actual processing will occur")
            print(f"   Would process {len(filtered_providers)} providers")
            print(f"   Estimated cost: ${estimated_cost:.2f}")
            return {'updated': 0, 'errors': 0, 'total_providers': len(filtered_providers)}
        
        # Confirm before proceeding
        if estimated_cost > 10.00:  # Warning for costs over $10
            print(f"\n⚠️ WARNING: Estimated cost is ${estimated_cost:.2f}")
            response = input("Continue? (y/N): ")
            if response.lower() != 'y':
                print("❌ Cancelled by user")
                return {'updated': 0, 'errors': 0, 'total_providers': 0}
        
        # Show sample providers
        print(f"\n📋 SAMPLE PROVIDERS TO PROCESS:")
        for i, provider in enumerate(filtered_providers[:5], 1):
            print(f"   {i}. {provider.provider_name} ({provider.city})")
        if len(filtered_providers) > 5:
            print(f"   ... and {len(filtered_providers) - 5} more")
        
        # Start processing
        print(f"\n🚀 Starting mega-batch processing...")
        start_time = time.time()
        
        results = processor.process_providers_mega_batch(filtered_providers, batch_size)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Final statistics
        print(f"\n🎉 PROCESSING COMPLETE!")
        print(f"   ⏱️ Processing time: {processing_time:.1f} seconds")
        print(f"   📊 Total providers: {results['total_providers']}")
        print(f"   ✅ Successfully updated: {results['updated']}")
        print(f"   ❌ Errors: {results['errors']}")
        print(f"   📈 Success rate: {results['updated']/len(filtered_providers)*100:.1f}%")
        
        if results['updated'] > 0:
            providers_per_second = results['updated'] / processing_time
            print(f"   🚄 Processing speed: {providers_per_second:.1f} providers/second")
            
            # Show updated statistics
            print(f"\n📊 UPDATED STATISTICS:")
            show_provider_stats(db)
        
        return results
        
    except Exception as e:
        print(f"❌ Error in mega-batch automation: {str(e)}")
        return {'updated': 0, 'errors': 1, 'total_providers': 0}

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description='Mega-Batch Content Generation Automation')
    
    parser.add_argument('--batch-size', type=int, default=2,
                        help='Number of providers per batch (default: 2, optimized for reliability)')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of providers to process (for testing)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be processed without actually doing it')
    parser.add_argument('--all-providers', action='store_true',
                        help='Process all providers that need content (removes any default limits)')
    parser.add_argument('--stats-only', action='store_true',
                        help='Only show provider statistics, do not process')
    
    args = parser.parse_args()
    
    if args.stats_only:
        db = PostgresIntegration()
        show_provider_stats(db)
        return
    
    # Determine processing limit
    limit = None
    if not args.all_providers and args.limit is None:
        limit = 20  # Default safety limit
        print(f"ℹ️ Using default limit of {limit} providers. Use --all-providers to process all.")
    elif args.limit:
        limit = args.limit
    
    # Run the automation
    results = run_mega_batch_automation(
        batch_size=args.batch_size,
        limit=limit,
        dry_run=args.dry_run
    )
    
    # Exit with appropriate code
    if results['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main() 