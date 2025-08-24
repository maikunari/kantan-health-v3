# Google Places Photo API - Caching & Performance Challenge

## Overview
We're building a healthcare provider directory that will scale to 10,000+ providers. Each provider has ~5 photos from Google Places API that must be displayed on their WordPress page. We need images to load instantly when users first visit a page, but we're facing challenges with Google's API requirements and browser behavior.

## Current Architecture

### System Components
1. **WordPress Frontend**: Displays provider pages with photos
2. **Photo Proxy API** (`/api/photo/<reference>`): Our proxy server that:
   - Receives photo requests from WordPress
   - Checks local cache (30-day TTL per Google TOS)
   - Fetches from Google Places API if cache miss
   - Returns image to browser
3. **PostgreSQL Database**: Stores photo references for each provider
4. **Cache Layer**: SQLite-based persistent cache with 30-day expiration

### Google Places API Constraints
- **Terms of Service**: Can cache photos for maximum 30 days
- **Photo References**: Expire periodically (unpredictable timing)
- **API Cost**: $0.007 per photo fetch
- **Response Time**: 1-2 seconds per photo from Google

## The Problem

### Current Behavior
1. User visits provider page for first time
2. Browser requests 5 images from our proxy
3. Proxy has cache miss (cold cache)
4. Proxy fetches from Google (1-2 seconds each)
5. **Browser times out or shows broken images before proxy responds**
6. User must refresh page to see images (now cached)

### Scale Concerns
- Adding **hundreds of providers daily**
- Target: **10,000+ total providers**
- **50,000+ total photos** to manage
- Cost projection: $350/month if blindly refreshing all photos

## Potential Solutions

### Option 1: Pre-warm Cache on Publish
- **How**: When publishing provider to WordPress, immediately fetch all photos
- **Pros**: First visitor always gets cached images
- **Cons**: Cache expires in 30 days; unvisited pages waste API calls

### Option 2: Scheduled Cache Warming
- **How**: Cron job refreshes all photos every 25-28 days
- **Pros**: Cache always warm
- **Cons**: Very expensive at scale ($350/month for 10,000 providers)

### Option 3: Smart Popularity-Based Caching
- **How**: Track page views, only refresh popular providers
- **Pros**: Cost-efficient, scales well
- **Cons**: Still has cold-start problem for new/unpopular content

### Option 4: Streaming Proxy Response
- **How**: Return HTTP 200 immediately, stream image data as it arrives
- **Pros**: True on-demand, no pre-warming needed
- **Cons**: Complex implementation, browser compatibility concerns

### Option 5: JavaScript Retry Mechanism
- **How**: Client-side JS detects failed images and retries after delay
- **Pros**: Works with current architecture
- **Cons**: Still shows broken images initially, requires JavaScript

### Option 6: Placeholder with Async Loading
- **How**: Return placeholder immediately, JavaScript swaps in real image
- **Pros**: Page never looks broken
- **Cons**: Requires JavaScript, more complex frontend

## Technical Constraints

### Browser Behavior
- HTML `<img>` tags have implicit timeout expectations
- Browsers may cache failed image requests
- `loading="lazy"` attribute delays load but doesn't help with timeouts

### Performance Requirements
- **Must Have**: Images must appear on first page load (no broken images)
- **Scalability**: Solution must work efficiently for 10,000+ providers
- **Cost**: Need to minimize Google API costs
- **Compliance**: Must respect Google's 30-day cache limit

## Current Code Structure

### Photo Request Flow
```
WordPress (img src) → Nginx → Flask API → Photo Proxy Handler → 
  ↓ (cache check)
  → If hit: Return cached image (fast)
  → If miss: Fetch from Google → Cache → Return (slow, times out)
```

### Key Files
- `api/photo_proxy.py` - Proxy endpoint implementation
- `src/collectors/google_places.py` - Google API integration
- `blocks/provider-featured-image.php` - WordPress image display

## Questions for Consideration

1. **Is there a way to make the Google fetch fast enough that browsers won't timeout?**
2. **Should we accept that some API cost is necessary for good UX?**
3. **Can we leverage CDN or edge caching in addition to our approach?**
4. **Is there a hybrid approach that gives instant loading AND cost efficiency?**
5. **Would a different architecture (e.g., background job queue) help?**

## Ideal Solution Criteria

The perfect solution would:
- Load images instantly on first visit (no broken images ever)
- Scale efficiently to 10,000+ providers
- Minimize Google API costs
- Require minimal infrastructure changes
- Work without JavaScript (progressive enhancement)
- Comply with Google's Terms of Service

## Budget Considerations

At 10,000 providers with 5 photos each:
- Full refresh every 30 days: $350/month
- Smart refresh (20% popular): ~$70/month
- On-demand only: Variable, but likely $30-50/month

## Next Steps

We need to decide on an approach that balances:
1. User experience (instant loading)
2. Cost efficiency (API calls)
3. Technical complexity (implementation/maintenance)
4. Scalability (works at 10,000+ providers)

Your input and alternative solutions are welcome!