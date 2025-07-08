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

def run_data_collection(daily_limit):
    """Run data collection phase with a daily limit on providers."""
    collector = GooglePlacesHealthcareCollector()
    search_queries = collector.generate_search_queries(limit=100, initial_cities=["Tokyo", "Yokohama", "Osaka City", "Nagoya"])
    max_per_query = max(1, int(daily_limit / len(search_queries)))
    print(f"Running data collection with daily limit {daily_limit}, max_per_query {max_per_query}")
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
    parser.add_argument("--daily-limit", type=int, default=25, help="Daily limit for provider collection")
    args = parser.parse_args()

    print("🏥 Healthcare Directory Automation")
    print("=" * 50)

    # Phase 1: Data Collection
    print("🌐 PHASE 1: Data Collection from Google Places API")
    print("=" * 50)
    providers = run_data_collection(daily_limit=args.daily_limit)

    # Phase 2: AI Description Generation (Batch Processing)
    print("🤖 PHASE 2: AI Description Generation (Batch Processing)")
    print("=" * 50)
    run_batch_ai_description_generation(providers, batch_size=5)

    # Phase 3: WordPress Publishing
    print("🌐 PHASE 3: WordPress Publishing")
    print("=" * 50)
    run_wordpress_publishing()

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