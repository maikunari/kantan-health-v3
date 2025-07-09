#!/usr/bin/env python3
"""
Force update all providers by bypassing filtering logic
Quick and simple approach to update existing providers
"""

from claude_description_generator import run_batch_ai_description_generation
from google_places_integration import GooglePlacesHealthcareCollector
from postgres_integration import Provider

def force_update_all_providers(city=None, limit=50):
    """Force update all providers regardless of existing content"""
    
    collector = GooglePlacesHealthcareCollector()
    session = collector.Session()
    
    # Get providers to update
    query = session.query(Provider)
    
    if city:
        query = query.filter(Provider.city == city)
    
    providers = query.limit(limit).all()
    
    print(f"🔄 FORCE UPDATING {len(providers)} PROVIDERS")
    print("=" * 50)
    
    if not providers:
        print("No providers found")
        session.close()
        return
    
    # Temporarily clear descriptions to force regeneration
    for provider in providers:
        provider.ai_description = None
        provider.ai_excerpt = None
        provider.status = 'pending'
    
    session.commit()
    print(f"✅ Cleared descriptions for {len(providers)} providers")
    
    session.close()
    
    # Now run batch generation (this will bypass the filtering)
    run_batch_ai_description_generation(providers, batch_size=3)
    
    print("🎉 Force update completed!")

if __name__ == "__main__":
    import sys
    
    # Parse simple arguments
    city = None
    limit = 50
    
    if len(sys.argv) > 1:
        city = sys.argv[1]
    if len(sys.argv) > 2:
        limit = int(sys.argv[2])
    
    force_update_all_providers(city, limit) 