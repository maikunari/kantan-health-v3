#!/usr/bin/env python3
"""
Automation Script for Healthcare Directory
Orchestrates data collection, AI description generation, and WordPress publishing.
"""

import argparse
from google_places_integration import GooglePlacesHealthcareCollector
from ai_description_generator import ClaudeDescriptionGenerator
from wordpress_integration import WordPressIntegration
from flask import Flask, render_template

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

def run_ai_description_generation(providers):
    """Run AI description generation phase."""
    generator = ClaudeDescriptionGenerator()
    for provider in providers:
        if provider.get('status') == 'pending':
            description = generator.generate_description(provider)
            provider['ai_description'] = description
            provider['status'] = 'description_generated'
    return providers

def run_wordpress_publishing():
    """Run WordPress publishing phase."""
    wp = WordPressIntegration()
    results = wp.run_sync()
    if results["errors"] > 0:
        print(f"⚠️ Publishing errors detected, check logs")
    return results

def main():
    parser = argparse.ArgumentParser(description="Run healthcare directory automation")
    parser.add_argument("--daily-limit", type=int, default=25, help="Daily limit for provider collection")
    args = parser.parse_args()

    print("🏥 Healthcare Directory Automation")
    print("=" * 50)

    # Phase 1: Data Collection
    print("🌐 PHASE 1: Data Collection from Google Places API")
    print("=" * 50)
    providers = run_data_collection(daily_limit=args.daily_limit)

    # Phase 2: AI Description Generation
    print("🤖 PHASE 2: AI Description Generation")
    print("=" * 50)
    providers = run_ai_description_generation(providers)

    # Phase 3: WordPress Publishing
    print("🌐 PHASE 3: WordPress Publishing")
    print("=" * 50)
    results = run_wordpress_publishing()

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
    # Uncomment to run Flask server (separate process recommended)
    # app.run(debug=True)