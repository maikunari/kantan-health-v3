# Japan Healthcare Directory Scale-Up Roadmap
**Goal**: Scale from ~500 to 10,000+ providers, then achieve complete national coverage  
**Timeline**: 6 weeks to 10,000 | 1 year to complete coverage  
**Vision**: Become THE definitive source for English-language healthcare information in Japan

---

## Current State Assessment
- **Providers in Database**: ~500
- **API Efficiency**: 90.4% reduction via mega-batch processing
- **Cost Optimization**: 75% reduction via caching
- **Coverage**: Limited to major cities (Tokyo, Osaka, Yokohama, Fukuoka, Kyoto)
- **Collection Limitation**: Only getting 20 results per query (missing pagination)

---

## Phase 1: Collection Engine Upgrade (Week 1)
**Goal**: Fix the collection bottleneck - get 3x more results per query

### 1.1 Add Pagination Support ✅
```python
# File: src/collectors/google_places.py
# Add next_page_token handling to get 60 results instead of 20
```
- [x] Modify `search_providers()` to handle pagination
- [x] Add 2-second delay between page requests (Google requirement)
- [x] Update cost tracking for paginated requests
- [x] Test with single query to verify 60 results (got 38 for "doctor Shinjuku")

### 1.2 Implement Ward-Specific Searches ✅
```python
# Tokyo's 23 Special Wards
TOKYO_WARDS = [
    "Chiyoda", "Chuo", "Minato", "Shinjuku", "Bunkyo",
    "Taito", "Sumida", "Koto", "Shinagawa", "Meguro",
    "Ota", "Setagaya", "Shibuya", "Nakano", "Suginami",
    "Toshima", "Kita", "Arakawa", "Itabashi", "Nerima",
    "Adachi", "Katsushika", "Edogawa"
]
```
- [x] Create ward-based query generator
- [ ] Add ward field to database (pending migration)
- [x] Update deduplication to handle ward-level data

### 1.3 Add Japanese Search Terms ✅
```python
JAPANESE_MEDICAL_TERMS = {
    "dentist": ["歯科", "歯医者", "デンタルクリニック"],
    "clinic": ["クリニック", "診療所", "医院"],
    "hospital": ["病院", "総合病院", "医療センター"],
    "pediatrics": ["小児科", "こども病院"],
    "internal_medicine": ["内科", "内科クリニック"],
    "orthopedics": ["整形外科", "整形外科クリニック"]
}
```
- [x] Implement bilingual search patterns
- [x] Test Japanese queries return different results
- [x] Verify English proficiency filtering still works

### 1.4 Test Collection at Scale ✅
```bash
# Test command for 100 providers across Tokyo wards
python3 test_phase1_complete.py
```
- [x] Collect providers across Tokyo's 23 wards (31 new added)
- [x] Verify deduplication working (274 duplicates caught)
- [x] Check cost tracking accuracy ($5.60 for test)
- [x] Monitor API rate limits (working within limits)

**Success Metrics**: 
- Getting 60 results per query (3x improvement)
- Finding 500+ new providers in Tokyo alone
- API costs remain under $10/day

---

## Phase 2: Geographic Expansion Infrastructure (Week 2-3)
**Goal**: Build infrastructure for nationwide collection

### 2.1 Create Geographic Search Module ✅
```python
# New file: src/collectors/geographic_search.py
class GeographicSearchEngine:
    def generate_grid_searches(self, city_bounds: Dict) -> List[Dict]
    def generate_nearby_searches(self, center: Tuple, radius: int) -> List[Dict]
    def generate_district_searches(self, city: str, districts: List) -> List[Dict]
```
- [x] Implement grid-based search (1km x 1km squares)
- [x] Add Nearby Search API support
- [x] Create search overlap detection
- [x] Build search queue management

### 2.2 Implement Prefecture-City-Ward Hierarchy ✅
```python
# Database migration for geographic hierarchy
- prefecture (string)
- city (string) 
- ward/district (string)
- neighborhood (string)
- postal_code (string)
```
- [x] Create database migration
- [x] Update provider model
- [x] Build location extraction from Google results
- [x] Add geographic filtering to queries

### 2.3 Build Collection Progress Tracker ✅
```python
# New table: collection_progress
- prefecture_id
- city_id
- search_type
- queries_executed
- providers_found
- last_search_date
- coverage_percentage
```
- [x] Create progress tracking table
- [x] Implement coverage calculation
- [x] Add resume capability for interrupted collections
- [x] Build collection statistics dashboard

### 2.4 Expand to Top 10 Cities
Priority cities by population:
1. Tokyo (14M) - 23 wards
2. Yokohama (3.7M) - 18 wards
3. Osaka (2.7M) - 24 wards
4. Nagoya (2.3M) - 16 wards
5. Sapporo (1.9M) - 10 wards
6. Kobe (1.5M) - 9 wards
7. Kyoto (1.4M) - 11 wards
8. Fukuoka (1.5M) - 7 wards
9. Kawasaki (1.5M) - 7 wards
10. Saitama (1.3M) - 10 wards

- [ ] Run collection for each city
- [ ] Target 200 providers per city minimum
- [ ] Track coverage percentage
- [ ] Optimize query patterns based on results

**Success Metrics**:
- 2,000+ providers across top 10 cities
- Geographic search finding 40% more providers
- Collection resumable after interruption

---

## Phase 2.5: SEO Taxonomy Content Generation (Week 3-4)
**Goal**: Generate AI-powered content for all taxonomy pages to dominate local SEO

### 2.5.1 Priority Tier System ⬜
```python
# Content priority based on provider count and search volume
Tier 1: Combinations with 5+ providers (~200 pages)
Tier 2: Combinations with 1-4 providers (~800 pages)
Tier 3: High search volume, no providers (~1,000 pages)
Tier 4: Long-tail coverage (remaining ~10,000 pages)
```
- [ ] Analyze current provider distribution
- [ ] Identify Tier 1 high-value combinations
- [ ] Research search volume for Tier 3 targets
- [ ] Create priority queue for generation

### 2.5.2 Location Taxonomy Content (~500 terms) ⬜
```python
# Generate for each location (city/ward):
- Brief area description and what it's known for
- Transportation and accessibility
- Types of medical services available
- SEO focus: "English doctors in [location]"
```
- [ ] Pull all location terms from WordPress
- [ ] Generate location descriptions with local context
- [ ] Add standard provider availability text
- [ ] Sync to WordPress location taxonomy

### 2.5.3 Specialty Taxonomy Content (~25 terms) ⬜
```python
# Generate for each medical specialty:
- What the specialty covers
- Common conditions treated
- When to see this specialist
- Typical procedures and treatments
```
- [ ] Pull all specialty terms from WordPress
- [ ] Generate educational specialty content
- [ ] Focus on user education and trust
- [ ] Sync to WordPress specialty taxonomy

### 2.5.4 Combination Page Content (THE GOLD 🏆) ⬜
```python
# For each specialty + location combination:
1. Brief Intro (50-75 words):
   "Find trusted English-speaking dentists in Shinjuku..."
   
2. Full Description (400-500 words):
   - Local area context
   - Specialty-specific information
   - Insurance and payment details
   - What to expect at Japanese clinics
   
3. SEO Metadata:
   - Title: "English [Specialty] in [Location] - Trusted Clinics"
   - Meta: 150-160 chars optimized for CTR
```
- [ ] Generate Tier 1 combinations (5+ providers)
- [ ] Generate Tier 2 combinations (1-4 providers)
- [ ] Create content generation script with mega-batching
- [ ] Implement 70/30 unique/template hybrid approach
- [ ] Sync to WordPress ACF fields and Yoast SEO

### 2.5.5 Content Generation Script ⬜
```python
# New file: scripts/generate_taxonomy_content.py
- Mega-batch processing (5-10 combinations per API call)
- Priority-based generation
- Content uniqueness scoring
- WordPress REST API sync
- Progress tracking and resume capability
```
- [ ] Build taxonomy content generator
- [ ] Implement priority algorithm
- [ ] Add mega-batch processing for efficiency
- [ ] Create WordPress sync for ACF and Yoast
- [ ] Add cost tracking and limits

### 2.5.6 Content Strategy ⬜
**Hybrid Approach (70% Unique / 30% Template):**

**Unique Elements (70%):**
- Location-specific details (landmarks, stations)
- Neighborhood character and demographics
- Local hospitals and medical facilities
- Area-specific health concerns

**Template Elements (30%):**
- Insurance acceptance information
- Japanese medical system overview
- Appointment booking process
- Payment methods accepted

**Example Differentiation:**
- "Dentist in Shinjuku": Mentions business district, evening appointments
- "Dentist in Bunkyo": Mentions universities, student-friendly options
- Both share: Japanese dental care approach, insurance basics

### 2.5.7 Implementation Timeline ⬜
- [ ] Week 3 Day 1-2: Build generation script and priority system
- [ ] Week 3 Day 3-4: Generate Tier 1 content (~200 pages)
- [ ] Week 3 Day 5-7: Generate Tier 2 content (~800 pages)
- [ ] Week 4 Day 1-3: Generate Tier 3 content (~1,000 pages)
- [ ] Week 4 Day 4-5: Test and verify WordPress sync
- [ ] Week 4 Day 6-7: Monitor indexing and early rankings

**Success Metrics:**
- ✅ 1,000+ combination pages with optimized content
- ✅ All active provider combinations have landing pages
- ✅ Content uniqueness score > 70%
- ✅ Total cost under $100
- ✅ Pages begin ranking within 30 days

**Cost Breakdown:**
- Location taxonomies: ~$10-15
- Specialty taxonomies: ~$2-3
- Tier 1-2 combinations: ~$40-50
- Tier 3 combinations: ~$25-35
- **Total Phase 2.5**: ~$75-100

**ROI Projection:**
- Organic traffic increase: 200-300% within 3 months
- Conversion rate improvement: 2-3x with targeted content
- Domain authority boost from comprehensive coverage
- Foundation for 100,000+ monthly organic visitors

---

## Phase 3: Scale to 10,000 Providers (Week 4-6)
**Goal**: Systematic collection across all 47 prefectures

### 3.1 Create Scale Collection Script
```python
# New file: scripts/scale_collection.py
- Prefecture-by-prefecture collection
- Automatic progress tracking
- Cost monitoring and limits
- Parallel processing support
```
- [ ] Build prefecture iteration logic
- [ ] Add automatic retry for failures
- [ ] Implement daily/monthly cost limits
- [ ] Create collection report generator

### 3.2 Run Prefecture-Level Collections
Collection targets by region:
- **Kanto** (7 prefectures): 3,000 providers
- **Kansai** (7 prefectures): 2,000 providers  
- **Chubu** (9 prefectures): 1,500 providers
- **Kyushu** (8 prefectures): 1,200 providers
- **Tohoku** (6 prefectures): 800 providers
- **Chugoku** (5 prefectures): 700 providers
- **Shikoku** (4 prefectures): 500 providers
- **Hokkaido** (1 prefecture): 300 providers

- [ ] Week 4: Kanto + Kansai (5,000 providers)
- [ ] Week 5: Chubu + Kyushu (2,700 providers)
- [ ] Week 6: Remaining regions (2,300 providers)

### 3.3 Process Through AI Pipeline
```bash
# Mega-batch processing for all new providers
python3 scripts/run_pipeline.py --mode process --all-providers
```
- [ ] Process in batches of 100
- [ ] Monitor Claude API costs
- [ ] Handle failures with retry logic
- [ ] Generate quality reports

### 3.4 Publish to WordPress
```bash
# Batch publishing with monitoring
python3 scripts/run_pipeline.py --mode publish --batch-size 50
```
- [ ] Publish in batches to avoid timeout
- [ ] Monitor WordPress API limits
- [ ] Update sitemap for SEO
- [ ] Verify all content published correctly

**Success Metrics**:
- 10,000+ providers in database
- All providers have AI-generated content
- 95%+ successfully published to WordPress
- Total cost under $700

---

## Phase 4: Monitoring Dashboard (Week 7)
**Goal**: Build simple CLI dashboard for system overview

### 4.1 Create CLI Dashboard
```
# New file: scripts/dashboard.py
Healthcare Directory Dashboard
===============================================
| Total Providers      | 10,247                |
| With AI Content      | 10,247 (100%)         |
| Published            | 9,735 (95%)           |
| Coverage Score       | 78%                   |
|----------------------|-----------------------|
| Top Cities           | Providers             |
| Tokyo                | 2,341                 |
| Osaka                | 1,287                 |
| Yokohama             | 876                   |
|----------------------|-----------------------|
| API Costs (Month)    | $623.45 / $700        |
| Collection Rate      | 234 providers/day     |
| Processing Rate      | 187 providers/day     |
===============================================
```
- [ ] Build dashboard layout
- [ ] Add real-time statistics
- [ ] Include cost monitoring
- [ ] Add coverage heatmap

### 4.2 Implement Coverage Analysis
- [ ] Calculate coverage by prefecture
- [ ] Identify gaps in specialty coverage
- [ ] Generate collection recommendations
- [ ] Export coverage reports

### 4.3 Add Automated Reporting
- [ ] Daily collection summary email
- [ ] Weekly progress report
- [ ] Monthly cost analysis
- [ ] Coverage gap alerts

**Success Metrics**:
- Dashboard provides instant system overview
- Coverage gaps clearly identified
- Automated alerts for issues

---

## Phase 5: Beyond 10,000 - Complete National Coverage (Months 2-12)
**Goal**: Become THE definitive source for English-language healthcare in Japan

### 5.1 Deep Rural Coverage (Months 2-4)
- [ ] Target all cities with population > 50,000
- [ ] Add rural clinics and hospitals
- [ ] Include emergency services
- [ ] Focus on areas with foreign residents
**Target**: 20,000 providers

### 5.2 Specialty Expansion (Months 5-7)
- [ ] Add 20+ new medical specialties
- [ ] Include alternative medicine (covered by insurance)
- [ ] Add mental health services
- [ ] Include rehabilitation centers
**Target**: 30,000 providers

### 5.3 Enhanced Data Collection (Months 8-10)
- [ ] Add insurance acceptance information
- [ ] Collect staff language capabilities
- [ ] Add accessibility features
- [ ] Include parking/transport info
**Target**: Enhanced data for all providers

### 5.4 Community Features (Months 11-12)
- [ ] Patient review system
- [ ] Doctor verification program
- [ ] Insurance guide integration
- [ ] Appointment booking capability
**Target**: 40,000+ providers with community features

### 5.5 Maintenance & Quality (Ongoing)
**Bi-Annual Provider Review (April & October):**
- [ ] Full validation of all 40,000 providers
- [ ] Check business_status (still operating)
- [ ] Update hours, phone, website
- [ ] Refresh reviews if significant changes
- [ ] Cost: ~$200 per review cycle

**Continuous New Provider Discovery:**
- [ ] Daily automated scans (10 providers/day after Year 1)
- [ ] Focus on high-traffic areas
- [ ] Search for "recently opened" clinics
- [ ] Target: 300 new providers/month ongoing

**Quality Assurance:**
- [ ] Automated dead link checking (weekly)
- [ ] Phone number validation (monthly)
- [ ] Review monitoring for major changes
- [ ] Quarterly manual audit of 100 random providers

---

## Cost Projections

### Phase 1-4: Initial Sprint (Weeks 1-6)
**One-time cost to reach 10,000 providers:**
- Google Places API: ~$400
- Claude AI API: ~$250
- WordPress hosting: ~$50
- **Total**: ~$700 (one-time, not monthly)

### Phase 5: Expansion Phase (Months 2-12)
**Monthly costs while building to 40,000:**
- Google Places API: ~$150/month (adding ~3,000/month)
- Claude AI API: ~$75/month
- WordPress hosting: ~$75/month
- **Total**: ~$200-300/month during expansion
- **Total expansion cost**: ~$2,500 over 10 months

### Maintenance Phase (After reaching 40,000)
**Ongoing monthly costs:**
- New provider discovery: ~$50/month (10/day)
- Bi-annual reviews: ~$35/month (amortized)
- WordPress hosting: ~$75/month
- **Total**: ~$100-150/month ongoing

### Revenue Opportunities (Year 2+)
- Premium listings for providers ($50-200/month per provider)
- Appointment booking commissions (5-10% per booking)
- Insurance company partnerships ($5,000-10,000/month)
- Medical tourism packages ($100-500 per referral)
- Translation service referrals ($20-50 per referral)

---

## Key Success Indicators

### Technical KPIs
- [ ] 10,000 providers by week 6
- [ ] 40,000 providers by month 12
- [ ] 99% data accuracy
- [ ] < 24hr content generation time
- [ ] < $300/month operational cost after initial build

### Business KPIs  
- [ ] #1 Google ranking for "English speaking doctor Japan"
- [ ] 100,000+ monthly users
- [ ] Coverage in all 47 prefectures
- [ ] All cities > 50,000 population covered
- [ ] Provider verification program active

### Quality Metrics
- [ ] 95%+ providers have photos
- [ ] 100% have AI-generated descriptions
- [ ] 80%+ have verified English capability
- [ ] 90%+ have current business hours
- [ ] 85%+ have reviews analyzed

---

## Risk Mitigation

### API Limits & Costs
- Implement aggressive caching
- Use batch processing
- Monitor daily/monthly limits
- Have backup API keys ready

### Data Quality
- Regular deduplication runs
- Automated quality checks
- Provider verification system
- User reporting mechanism

### Technical Debt
- Keep codebase modular
- Document all changes
- Maintain test coverage
- Regular refactoring sprints

---

## Operations & Automation Strategy

### Collection Phases & Targets

#### Phase 1-4: Sprint Mode (Weeks 1-6)
```bash
# AGGRESSIVE COLLECTION - Manual execution with monitoring
python3 scripts/run_pipeline.py --mode collect --limit 240
# Target: 240 providers/day = 10,000 in 6 weeks
# Cost: ~$15-20/day during sprint
```

#### Phase 5: Expansion Mode (Months 2-12)
```bash
# CONTROLLED EXPANSION - Semi-automated
python3 scripts/run_pipeline.py --mode collect --limit 100
# Target: 100 providers/day = 3,000/month
# Cost: ~$10/day during expansion
```

#### Maintenance Mode (After Year 1)
```bash
# DISCOVERY MODE - Fully automated
python3 scripts/discover_new_providers.py --limit 10
# Target: 10 providers/day = 300/month ongoing
# Cost: ~$3-5/day ongoing
```

### Automation Schedule (Cron Jobs)

```bash
# After reaching 10,000 providers, activate automated schedule:

# Daily new provider discovery (2 AM JST)
0 2 * * * /usr/bin/python3 /path/to/scripts/discover_new_providers.py --limit 10 --email-report

# Weekly AI content processing (Sundays 3 AM JST)
0 3 * * 0 /usr/bin/python3 /path/to/scripts/run_pipeline.py --mode process --new-only --email-summary

# Weekly WordPress sync (Sundays 5 AM JST)
0 5 * * 0 /usr/bin/python3 /path/to/scripts/run_pipeline.py --mode publish --batch-size 50

# Bi-annual provider review (April 1 & October 1)
0 0 1 4,10 * /usr/bin/python3 /path/to/scripts/provider_review.py --full-scan --email-report

# Daily status check and alert (9 AM JST)
0 9 * * * /usr/bin/python3 /path/to/scripts/daily_health_check.py
```

### Email Notifications System

#### Daily Report (9 AM JST)
```
Subject: [Healthcare Directory] Daily Report - {date}

=== COLLECTION SUMMARY ===
New providers discovered: 10
Successfully processed: 9
Failed/Rejected: 1
Current total: 10,247

=== COSTS ===
Yesterday's API costs: $4.32
Month-to-date: $87.41
Budget remaining: $212.59

=== ALERTS ===
⚠️ 3 providers need manual review
✓ All systems operational
```

#### Weekly Summary (Monday 9 AM JST)
```
Subject: [Healthcare Directory] Weekly Summary - Week {week_number}

=== WEEK OVERVIEW ===
New providers added: 67
AI content generated: 65
Published to WordPress: 63
Total providers: 10,247

=== PERFORMANCE ===
Collection success rate: 94%
AI processing success: 98%
Publishing success: 100%
English proficiency acceptance: 31%

=== TOP CITIES ===
Tokyo: +12 providers
Osaka: +8 providers
Yokohama: +5 providers

=== ACTION REQUIRED ===
- 5 providers pending manual review
- 2 providers with invalid phone numbers
- Review dashboard: http://localhost:3000
```

#### Alert Notifications (Immediate)
```
Subject: [ALERT] Healthcare Directory - Manual Intervention Required

Issue: API rate limit approaching
Details: 
- Current usage: 95% of daily limit
- Providers processed: 237/250
- Action: Collection paused automatically

Recommended Action:
- Review collection parameters
- Resume tomorrow or increase limits

Dashboard: http://localhost:3000
Logs: /logs/pipeline_20250126_140523.log
```

### Manual vs Automated Tasks

#### Fully Automated
- New provider discovery (after Year 1)
- AI content generation for approved providers
- WordPress publishing of completed content
- Dead link checking
- Phone validation
- Cost tracking and reporting
- Email notifications

#### Semi-Automated (Manual Approval)
- Batch processing > 100 providers
- Major geographic expansions
- Specialty additions
- Content regeneration
- Provider deletion/deactivation

#### Manual Only
- Initial collection phases (Weeks 1-6)
- Quality audits (quarterly)
- Revenue features implementation
- API key rotation
- Cost limit adjustments
- Strategy decisions

### Monitoring & Alerts

```python
# Email alerts triggered for:
ALERT_CONDITIONS = {
    'api_cost_exceeded': 'Daily cost > $10',
    'error_rate_high': 'Error rate > 5%',
    'low_discovery': 'New providers < 5/day',
    'validation_failures': 'Failed validations > 10',
    'manual_review_needed': 'Pending reviews > 10',
    'wordpress_sync_failed': 'Sync failures > 3',
    'cache_size_warning': 'Cache > 1GB',
    'database_connection_lost': 'DB unreachable > 5min'
}
```

---

## Implementation Notes

### Priority Order
1. Fix pagination (immediate 3x improvement)
2. Add Japanese search terms
3. Implement geographic search
4. Scale systematically by prefecture
5. Build monitoring last

### Command Reference
```bash
# Week 1: Test pagination
python3 scripts/run_pipeline.py --mode collect --limit 100

# Week 2-3: Geographic expansion  
python3 add_geographic_providers.py --city Tokyo --wards "all" --limit 500

# Week 4-6: Scale collection
python3 scripts/scale_collection.py --prefecture "all" --target 10000

# Week 7: Monitor progress
python3 scripts/dashboard.py
```

### File Structure Changes
```
src/
├── collectors/
│   ├── google_places.py (UPDATE: add pagination)
│   ├── geographic_search.py (NEW: grid search)
│   └── japanese_search.py (NEW: bilingual terms)
├── scripts/
│   ├── scale_collection.py (NEW: prefecture iteration)
│   └── dashboard.py (NEW: CLI monitoring)
└── migrations/
    └── add_geographic_hierarchy.py (NEW: prefecture/ward)
```

---

## Completion Checklist

### Week 1 Complete When:
- [ ] Getting 60 results per query
- [ ] Japanese searches working
- [ ] 500+ new Tokyo providers added

### Week 3 Complete When:
- [ ] Top 10 cities collected
- [ ] 2,000+ total providers
- [ ] Geographic search operational

### Week 6 Complete When:
- [ ] 10,000+ providers in database
- [ ] All with AI content
- [ ] 95% published to WordPress

### Year 1 Complete When:
- [ ] 40,000+ providers listed
- [ ] All 47 prefectures covered
- [ ] #1 ranking for target keywords
- [ ] THE source for English healthcare in Japan

---

**Last Updated**: January 2025  
**Status**: Ready to implement  
**Next Step**: Start with Phase 1.1 - Add pagination support