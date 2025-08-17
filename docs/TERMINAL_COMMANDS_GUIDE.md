# Healthcare Directory - Complete Terminal Commands Guide
**Comprehensive Reference for All System Commands and Scripts**

## 📋 Table of Contents

1. [Unified Pipeline Commands](#unified-pipeline-commands)
2. [SEO Content Generation](#seo-content-generation)
3. [Data Quality & Maintenance](#data-quality--maintenance)
4. [WordPress Sync Operations](#wordpress-sync-operations)
5. [Provider Management](#provider-management)
6. [Database Operations](#database-operations)
7. [Testing & Validation](#testing--validation)
8. [Cost Optimization](#cost-optimization)
9. [Quick Reference Tables](#quick-reference-tables)

---

## 🚀 Unified Pipeline Commands

### `scripts/run_pipeline.py` - Main Unified Pipeline

**Description**: Single interface for all collection, processing, and publishing operations.

#### **Basic Usage**
```bash
# Check system status
python3 scripts/run_pipeline.py --status-only

# Run full pipeline (collection → AI content → WordPress)
python3 scripts/run_pipeline.py --mode full --limit 50

# Run specific phases
python3 scripts/run_pipeline.py --mode collect --limit 20    # Collection only
python3 scripts/run_pipeline.py --mode process --batch-size 4 # AI processing only
python3 scripts/run_pipeline.py --mode publish --limit 25     # Publishing only
```

#### **All Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--mode` | choice | full | Mode: collect, process, publish, or full |
| `--limit` | int | 10 | Maximum items to process |
| `--batch-size` | int | 2 | Batch size for AI processing |
| `--dry-run` | flag | false | Test without making changes |
| `--status-only` | flag | false | Show system status and exit |
| `--provider-ids` | list | None | Specific provider IDs to process |
| `--city` | string | None | Filter by city |
| `--specialty` | string | None | Filter by specialty |

#### **Example Commands**
```bash
# Daily operations
python3 scripts/run_pipeline.py --mode full --limit 50

# Test with dry run
python3 scripts/run_pipeline.py --mode collect --limit 5 --dry-run

# Process specific providers
python3 scripts/run_pipeline.py --mode process --provider-ids 1,2,3

# Check for gaps and issues
python3 scripts/run_pipeline.py --status-only
```

---

## 🔍 SEO Content Generation

### `analyze_provider_distribution.py` - SEO Priority Analysis

**Description**: Analyzes provider distribution to identify high-value SEO combinations.

```bash
# Analyze current distribution
python3 analyze_provider_distribution.py

# Output includes:
# - Location distribution (excludes unknown cities)
# - Specialty distribution
# - Tier 1 combinations (5+ providers)
# - Tier 2 combinations (1-4 providers)
# - Providers needing location fixes
```

### `scripts/generate_taxonomy_content.py` - SEO Content Generator

**Description**: Generates AI-powered content for taxonomy pages using mega-batch processing.

#### **Basic Usage**
```bash
# Test single page generation
python3 scripts/generate_taxonomy_content.py --mode test

# Generate Tier 1 content (high-value combinations)
python3 scripts/generate_taxonomy_content.py --mode tier1

# Generate Tier 2 content
python3 scripts/generate_taxonomy_content.py --mode tier2 --limit 10

# Generate all priority content
python3 scripts/generate_taxonomy_content.py --mode all
```

#### **Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--mode` | choice | test | Mode: test, tier1, tier2, or all |
| `--limit` | int | None | Limit number of pages to generate |
| `--dry-run` | flag | false | Test without saving to database |

#### **Key Features**
- Removes exact provider counts (uses descriptive terms)
- 70/30 unique/template hybrid approach
- Mega-batch processing (5 items per API call)
- Priority-based generation
- Content saved to `taxonomy_content` table

---

## 🔧 Data Quality & Maintenance

### `utility/fix_missing_locations.py` - Fix Provider Locations

**Description**: Identifies and fixes providers with missing city data.

```bash
# Fix all providers with missing locations
python3 utility/fix_missing_locations.py

# Process limited number
python3 utility/fix_missing_locations.py --limit 10

# Use Google API for unfixable addresses (requires place_id)
python3 utility/fix_missing_locations.py --use-api
```

**Features:**
- Extracts city from address strings
- Recognizes Tokyo wards and major cities
- Updates database with corrected locations
- Reports providers that can't be fixed

### Provider Name Romanization

**Built into `src/collectors/google_places.py`:**
- Automatically romanizes Japanese names for English-proficient providers
- Only applies AFTER providers pass proficiency test (score ≥ 3)
- Handles bilingual names: "日の出薬局 Hinode Pharmacy" → "Hinode Pharmacy"
- Normalizes special characters: "Ōkura" → "Okura"

---

## 💰 Cost Optimization

### Exclusion List System

**Built into collection pipeline:**
- Loads existing providers on startup
- Caches rejected providers for 30 days
- Filters search results BEFORE expensive API calls
- Session-level rejection tracking
- Expected 94% cost reduction

### Check Cost Status
```bash
# View current API costs
python3 scripts/run_pipeline.py --status-only

# Monitor collection efficiency
grep "Filtered out" logs/pipeline_*.log | tail -10
```

---

## 📝 WordPress Sync Operations

### `publish_approved.py` - Publish Content to WordPress

**Description**: Publishes providers with AI-generated content to WordPress.

```bash
# Publish all approved providers
python3 publish_approved.py

# Test with dry run
python3 publish_approved.py --dry-run

# Limit number to publish
python3 publish_approved.py --limit 10

# Publish specific providers
python3 publish_approved.py --provider-ids 1,2,3
```

---

## 👥 Provider Management

### `add_specific_provider.py` - Add Individual Providers

```bash
# Add by name and location
python3 add_specific_provider.py --name "Clinic Name" --location "Tokyo"

# Add by Google Place ID (if known)
python3 add_specific_provider.py --place-id "ChIJN1t_tDeuEmsRUsoyG83frY4"
```

### `add_geographic_providers.py` - Add Providers by Area

```bash
# Add providers from specific area
python3 add_geographic_providers.py --city "Tokyo" --wards "Shibuya,Minato" --specialty "ENT" --limit 10

# Add all specialties from a ward
python3 add_geographic_providers.py --city "Tokyo" --wards "Shinjuku" --limit 20
```

---

## 🗄️ Database Operations

### Migration Scripts

```bash
# Run geographic hierarchy migration
python3 utility/migrate/migrate_geographic_hierarchy.py

# Add collection progress tracking
python3 utility/migrate/migrate_collection_progress.py

# Add proficiency scoring
python3 utility/migrate/migrate_proficiency_score.py

# Add WordPress sync tables
python3 utility/migrate/migrate_wordpress_sync_tables.py
```

### Direct Database Access

```bash
# Connect to database
psql -d directory

# Common queries
# Count providers by city
SELECT city, COUNT(*) FROM providers WHERE city IS NOT NULL GROUP BY city ORDER BY COUNT(*) DESC;

# Find providers with missing data
SELECT id, provider_name FROM providers WHERE city IS NULL OR city = '';

# Check SEO content
SELECT taxonomy_type, location, specialty, priority_tier FROM taxonomy_content ORDER BY created_at DESC LIMIT 10;

# View recent pipeline runs
SELECT run_id, mode, status, providers_processed, created_at 
FROM pipeline_runs 
ORDER BY created_at DESC 
LIMIT 5;
```

---

## ✅ Testing & Validation

### Test Database Connection
```bash
python3 utility/tests/test_db_connection.py
```

### Test WordPress Connection
```bash
python3 wordpress_sync_manager.py --test-connection
```

### Test Pipeline Components
```bash
# Test collection with small limit
python3 scripts/run_pipeline.py --mode collect --limit 1 --dry-run

# Test AI processing
python3 scripts/run_pipeline.py --mode process --limit 1 --dry-run

# Test SEO content generation
python3 scripts/generate_taxonomy_content.py --mode test --dry-run
```

---

## 📊 Quick Reference Tables

### Daily Operations Workflow

| Step | Command | Purpose |
|------|---------|---------|
| 1 | `python3 scripts/run_pipeline.py --status-only` | Check system status |
| 2 | `python3 analyze_provider_distribution.py` | Analyze SEO opportunities |
| 3 | `python3 utility/fix_missing_locations.py` | Fix data quality issues |
| 4 | `python3 scripts/run_pipeline.py --mode full --limit 50` | Run daily collection |
| 5 | `python3 scripts/generate_taxonomy_content.py --mode tier1` | Generate SEO content |

### Cost Control Commands

| Purpose | Command | Expected Result |
|---------|---------|-----------------|
| Check daily costs | `python3 scripts/run_pipeline.py --status-only` | Shows API costs |
| View cache efficiency | `grep "Cache hit" logs/pipeline_*.log \| tail` | Cache hit rate |
| See filtered duplicates | `grep "Filtered out" logs/pipeline_*.log \| tail` | Exclusion count |
| Monitor rejection rate | `grep "Rejected" logs/pipeline_*.log \| wc -l` | Rejection count |

### Troubleshooting Commands

| Issue | Command | Solution |
|-------|---------|----------|
| Providers stuck in pending | `psql -d directory -c "SELECT status, COUNT(*) FROM providers GROUP BY status;"` | Run process mode |
| Missing city data | `python3 utility/fix_missing_locations.py` | Fixes locations |
| Duplicate providers | `python3 find_real_duplicates.py` | Identifies duplicates |
| Failed WordPress sync | `python3 publish_approved.py --dry-run` | Test publishing |

### Environment Variables

Required in `config/.env`:
```bash
GOOGLE_PLACES_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_DB=directory
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APPLICATION_PASSWORD=your_app_password
DISABLE_GOOGLE_PHOTOS=true  # Optional: disable photo API to save costs
```

---

## 🚀 Advanced Operations

### Batch Processing Optimization

```bash
# Process in priority order
# 1. Fix data quality
python3 utility/fix_missing_locations.py

# 2. Generate high-value SEO content
python3 scripts/generate_taxonomy_content.py --mode tier1

# 3. Collect new providers efficiently
python3 scripts/run_pipeline.py --mode collect --limit 100

# 4. Process AI content in batches
python3 scripts/run_pipeline.py --mode process --batch-size 5

# 5. Publish to WordPress
python3 scripts/run_pipeline.py --mode publish --limit 50
```

### Monitor System Health

```bash
# Check all system components
python3 scripts/run_pipeline.py --status-only

# View recent activity
tail -n 100 logs/pipeline_*.log | grep -E "ERROR|WARNING|✅|❌"

# Database health check
psql -d directory -c "SELECT table_name, pg_size_pretty(pg_total_relation_size(table_name::regclass)) as size FROM information_schema.tables WHERE table_schema = 'public' ORDER BY pg_total_relation_size(table_name::regclass) DESC;"
```

### Export Reports

```bash
# Export provider distribution
python3 analyze_provider_distribution.py > reports/distribution_$(date +%Y%m%d).txt

# Export SEO priority data
cat seo_priority_data.json | python3 -m json.tool > reports/seo_priorities_$(date +%Y%m%d).json

# Database backup
pg_dump -d directory > backups/directory_$(date +%Y%m%d).sql
```

---

## 📝 Notes

- **Cost Optimization**: The exclusion list system dramatically reduces API costs by filtering known/rejected providers before making detail calls
- **Data Quality**: Always run `fix_missing_locations.py` before SEO analysis to ensure accurate distribution data
- **SEO Content**: Generated content uses descriptive terms instead of exact numbers to avoid outdated information
- **Romanization**: Only applies to providers that pass English proficiency testing (score ≥ 3)
- **Mega-batching**: Processes 5 SEO content items per API call for 80% cost reduction

**Last Updated**: 2025-01-26