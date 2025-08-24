Please review and optimize my Google Places API integration to reduce costs from $170/month to under $85/month.

CURRENT ISSUES:
- Spending ~$170/month on Google Places API
- Making duplicate API calls for the same place_id
- Photo URLs expiring and being regenerated unnecessarily
- No persistent caching between script runs
- Processing same providers multiple times under different searches

CURRENT COSTS BREAKDOWN:
- Places Details: $65.92 (~3,878 requests @ $0.017 each)
- Places Photos: $47.89 (~6,841 requests @ $0.007 each)
- Atmosphere Data: $11.27 (~2,254 requests @ $0.005 each)
- Contact Data: $6.76 (~2,253 requests @ $0.003 each)

REQUIRED OPTIMIZATIONS:

1. PERSISTENT CACHING SYSTEM
Create a cache that survives between script runs:
- Use SQLite or file-based cache for persistence
- Cache structure: {place_id: {data: {...}, timestamp: ..., expires: ...}}
- Cache place details for 30 days (they rarely change)
- Cache photo_references indefinitely (they don't change)
- Generate photo URLs on-demand with 12-hour cache
- Implement cache warming for popular providers

2. DEDUPLICATION STRATEGY
Prevent processing the same provider multiple times:
- Check PostgreSQL database BEFORE any API call
- Maintain a persistent processed_place_ids file/table
- Track place_ids across ALL search queries (not per query)
- Skip providers updated within last 30 days
- Geographic deduplication: if place_id already found, skip even if different search

3. PHOTO OPTIMIZATION
Reduce photo-related costs:
- Store photo_references, NOT URLs (references don't expire)
- Generate URLs only when needed for sync to WordPress
- Reduce from 5 photos to 4 per provider 
- Cache generated URLs for 12 hours only
- Remove duplicate photo URL generation

4. SEARCH QUERY OPTIMIZATION
Eliminate overlapping searches:
- Implement radius-based deduplication
- If searching "dentist in Shibuya" and "dentist in Harajuku", exclude already-found place_ids
- Track search coverage to avoid overlapping geographic areas
- Reduce search radius from 50000 to 30000 meters (if applicable)

5. API FIELD OPTIMIZATION
Request only necessary fields:
```python
# Current (possibly requesting too much):
fields = ['place_id', 'name', 'formatted_address', 'rating', 'user_ratings_total', 
          'reviews', 'opening_hours', 'website', 'formatted_phone_number', 
          'business_status', 'types', 'photos', 'geometry', 'plus_code', 
          'address_components', 'url', 'vicinity']

# Optimized (only what you actually use):
fields = ['place_id', 'name', 'formatted_address', 'rating', 'user_ratings_total',
          'reviews', 'opening_hours', 'website', 'formatted_phone_number',
          'photos', 'geometry']  # Remove unnecessary fields


class CostTracker:
    COSTS = {
        'place_details': 0.017,
        'atmosphere_data': 0.005,
        'contact_data': 0.003,
        'photos': 0.007
    }
    
    def __init__(self, daily_limit=10, monthly_limit=100):
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        self.load_existing_usage()
    
    def can_make_request(self, request_type):
        # Check if under budget before making request
        pass
    
    def log_request(self, request_type):
        # Log with timestamp and cost
        pass


def need_provider_update(place_id):
    # Check PostgreSQL for existing provider
    existing = db.query("SELECT last_updated FROM providers WHERE place_id = ?", place_id)
    if not existing:
        return True
    
    # Only update if older than 30 days
    last_updated = existing['last_updated']
    if (datetime.now() - last_updated).days > 30:
        return True
    
    return False

def get_provider_details(place_id):
    # First check cache
    cached = cache.get(place_id)
    if cached and not cached.is_expired():
        return cached
    
    # Then check database
    if not need_provider_update(place_id):
        return db.get_provider(place_id)
    
    # Only then make API call
    details = make_api_call(place_id)
    cache.set(place_id, details)
    db.save_provider(details)
    return details