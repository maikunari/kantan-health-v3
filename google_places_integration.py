#!/usr/bin/env python3
'''
Healthcare Directory Automation Runner

This script runs the complete automation pipeline:
1. Collect provider data from Google Places API
2. Store in PostgreSQL with keyword analysis
3. Pause for manual review via Flask dashboard (publishing handled by publish_approved.py)
'''

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from postgres_integration import PostgresIntegration, Metric

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_places_integration import GooglePlacesHealthcareCollector
from claude_description_generator import ClaudeDescriptionGenerator

def run_data_collection(daily_limit=50):
    '''Run Google Places data collection'''
    print("🏥 PHASE 1: Data Collection from Google Places API")
    print("=" * 60)
    
    collector = GooglePlacesHealthcareCollector()
    
    # Generate dynamic search queries for initial 100 listings from 4 cities
    search_queries = collector.generate_search_queries(limit=40, initial_cities=["Tokyo", "Yokohama", "Osaka City", "Nagoya"])
    
    # Collect comprehensive provider data (~25 providers/city for 4 cities = 100)
    providers = collector.search_and_collect_providers(search_queries, max_per_query=int(daily_limit/len(search_queries)))
    
    if providers:
        # Save to PostgreSQL
        saved_count = collector.save_to_postgres(providers)
        
        # Log providers added
        engine = create_engine(f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:5432/directory")
        Session = sessionmaker(bind=engine)
        session = Session()
        session.add(Metric(
            metric_type="providers_added",
            value=saved_count,
            details={"date": datetime.now().strftime("%Y-%m-%d")}
        ))
        session.commit()
        session.close()
        
        print(f"\n✅ Data Collection Complete!")
        print(f"   Providers collected: {len(providers)}")
        print(f"   Successfully saved: {saved_count}")
        
        return saved_count > 0
    else:
        print("❌ No providers collected")
        return False

def run_ai_description_generation():
    '''Generate AI descriptions for providers'''
    print("\n🤖 PHASE 2: AI Description Generation")
    print("=" * 60)
    
    generator = ClaudeDescriptionGenerator()
    results = generator.process_all_providers()
    
    if results['processed'] > 0:
        print(f"\n✅ AI Description Generation Complete!")
        print(f"   Descriptions generated: {results['processed']}")
        if results['errors'] > 0:
            print(f"   Errors encountered: {results['errors']}")
        return True
    else:
        print("⚠️ No new descriptions generated")
        return True

def main():
    '''Main automation runner'''
    print("🚀 Healthcare Directory Automation Pipeline")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Phase 1: Data Collection
        if run_data_collection():
            # Phase 2: AI Description Generation
            run_ai_description_generation()
            
            print("\n🎉 AUTOMATION PAUSED FOR REVIEW!")
            print("   ✅ Data collected from Google Places API")
            print("   ✅ AI descriptions generated")
            print("   ✅ Stored in PostgreSQL, pending review")
            print("\n🌐 Review providers at http://your_droplet_ip/review")
            print("   Publishing will run separately via publish_approved.py")
        else:
            print("❌ Data collection failed. Skipping remaining phases.")
            
    except Exception as e:
        print(f"❌ Automation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--daily-limit", type=int, default=50, help="Daily provider limit")
    args = parser.parse_args()
    run_data_collection(daily_limit=args.daily_limit)
    run_ai_description_generation()