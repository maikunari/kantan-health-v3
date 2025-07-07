#!/usr/bin/env python3
"""
Automation Script for Healthcare Directory
Manages data collection and AI description generation phases.
"""

import argparse
from google_places_integration import GooglePlacesHealthcareCollector
from claude_description_generator import ClaudeDescriptionGenerator

def run_data_collection(daily_limit):
    """Run data collection phase with a daily limit on providers."""
    collector = GooglePlacesHealthcareCollector()
    search_queries = collector.generate_search_queries(limit=10, initial_cities=["Tokyo", "Yokohama", "Osaka City", "Nagoya"])
    max_per_query = max(1, int(daily_limit / len(search_queries)))  # Ensure at least 1 result per query
    print(f"Running data collection with daily limit {daily_limit}, max_per_query {max_per_query}")
    providers = collector.search_and_collect_providers(search_queries, max_per_query=max_per_query)
    return providers

def run_ai_description_generation():
    """Run AI description generation phase."""
    generator = ClaudeDescriptionGenerator()
    results = generator.process_all_providers()
    if results["processed"] > 0 or results["errors"] > 0:
        print(f"✅ AI Description Generation Complete!")
        print(f"   Processed: {results['processed']}, Errors: {results['errors']}")
    else:
        print("⚠️ No new descriptions generated")

def main():
    """Main function to parse arguments and run phases."""
    parser = argparse.ArgumentParser(description="Automate healthcare directory data collection and description generation.")
    parser.add_argument("--daily-limit", type=int, default=25, help="Daily limit for provider collection")
    args = parser.parse_args()

    print("🏥 PHASE 1: Data Collection from Google Places API")
    print("=" * 50)
    providers = run_data_collection(daily_limit=args.daily_limit)
    if not providers:
        print("❌ No providers collected")
    else:
        print(f"✅ {len(providers)} providers collected")

    print("\n🤖 PHASE 2: AI Description Generation")
    print("=" * 50)
    run_ai_description_generation()

if __name__ == "__main__":
    main()