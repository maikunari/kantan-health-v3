#!/usr/bin/env python3
"""
Automation Script for Healthcare Directory
Orchestrates data collection, AI description generation, and WordPress publishing.
"""

import argparse
from google_places_integration import GooglePlacesHealthcareCollector
from wordpress_integration import WordPressIntegration
from flask import Flask, render_template
from claude_description_generator import run_batch_ai_description_generation  # Updated to use batch processing

app = Flask(__name__)
duplicates_detected = []

def run_data_collection(daily_limit, max_per_query=None, cities=None, query_limit=200):
    """Run data collection phase with configurable parameters."""
    collector = GooglePlacesHealthcareCollector()
    
    # Use default cities if not provided
    if cities is None:
        cities = ["Tokyo", "Yokohama", "Osaka", "Fukuoka", "Kyoto"]
    
    search_queries = collector.generate_search_queries(limit=query_limit, initial_cities=cities)
    
    # Calculate max_per_query if not explicitly provided
    if max_per_query is None:
        max_per_query = max(1, int(daily_limit / len(search_queries)))
        # For focused strategy, allow more results per query
        if daily_limit >= 50:
            max_per_query = max(2, max_per_query)
    
    print(f"Running data collection with daily limit {daily_limit}, max_per_query {max_per_query}")
    print(f"Generated {len(search_queries)} search queries for cities: {cities}")
    providers = collector.search_and_collect_providers(search_queries, max_per_query=max_per_query, daily_limit=daily_limit)
    return providers

def run_wordpress_publishing():
    """Run WordPress publishing phase."""
    wp = WordPressIntegration()
    results = wp.run_sync()
    if results["errors"] > 0:
        print(f"⚠️ Publishing errors detected, check logs")
    return results

def main():
    """Main function to parse arguments and run phases."""
    parser = argparse.ArgumentParser(description="Automate healthcare directory data collection and description generation.")
    parser.add_argument("--daily-limit", type=int, default=25, help="Daily limit for provider collection (default: 25)")
    parser.add_argument("--max-per-query", type=int, default=None, help="Maximum results per search query (auto-calculated if not specified)")
    parser.add_argument("--cities", nargs='+', default=None, help="Cities to search (default: Tokyo Yokohama Osaka Fukuoka Kyoto)")
    parser.add_argument("--query-limit", type=int, default=200, help="Maximum number of search queries to generate (default: 200)")
    parser.add_argument("--batch-size", type=int, default=5, help="Batch size for AI description generation (default: 5)")
    parser.add_argument("--skip-collection", action='store_true', help="Skip data collection phase")
    parser.add_argument("--skip-descriptions", action='store_true', help="Skip AI description generation phase")
    parser.add_argument("--skip-publishing", action='store_true', help="Skip WordPress publishing phase")
    args = parser.parse_args()

    print("🏥 Healthcare Directory Automation")
    print("=" * 50)
    print(f"📊 Configuration:")
    print(f"   Daily limit: {args.daily_limit}")
    print(f"   Max per query: {args.max_per_query or 'Auto-calculated'}")
    print(f"   Cities: {args.cities or ['Tokyo', 'Yokohama', 'Osaka', 'Fukuoka', 'Kyoto']}")
    print(f"   Query limit: {args.query_limit}")
    print(f"   Batch size: {args.batch_size}")
    print()

    # Phase 1: Data Collection
    if not args.skip_collection:
        print("🌐 PHASE 1: Data Collection from Google Places API")
        print("=" * 50)
        providers = run_data_collection(
            daily_limit=args.daily_limit,
            max_per_query=args.max_per_query,
            cities=args.cities,
            query_limit=args.query_limit
        )
    else:
        print("⏭️ Skipping data collection phase")
        providers = []

    # Phase 2: Location Population (if needed)
    if not args.skip_collection:
        print("🗺️ PHASE 2: Location Population")
        print("=" * 50)
        from populate_provider_locations import populate_missing_locations
        populate_missing_locations()
    else:
        print("⏭️ Skipping location population phase")

    # Phase 3: AI Description Generation (Batch Processing)
    if not args.skip_descriptions:
        print("🤖 PHASE 3: AI Description Generation (Batch Processing)")
        print("=" * 50)
        run_batch_ai_description_generation(providers, batch_size=args.batch_size)
    else:
        print("⏭️ Skipping AI description generation phase")

    # Phase 4: WordPress Publishing
    if not args.skip_publishing:
        print("🌐 PHASE 4: WordPress Publishing")
        print("=" * 50)
        run_wordpress_publishing()
    else:
        print("⏭️ Skipping WordPress publishing phase")

    # Flask alert for duplicates (simplified)
    if duplicates_detected:
        print(f"🚨 Duplicate Alerts: {len(duplicates_detected)} duplicates detected")
        with app.app_context():
            # Assuming a template 'alert.html' exists
            with open('templates/alert.html', 'w') as f:
                f.write(render_template('alert.html', duplicates=duplicates_detected))
            print("🚨 Duplicate alerts saved to templates/alert.html")

# Flask route for alert display (run separately or integrate)
@app.route('/alerts')
def show_alerts():
    return render_template('alert.html', duplicates=duplicates_detected)

if __name__ == "__main__":
    main()