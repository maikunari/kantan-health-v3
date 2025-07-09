# Healthcare Directory Automation

A comprehensive system for automatically collecting, processing, and publishing healthcare provider data for English-speaking patients in Japan.

## Overview

This automation system performs three main phases:
1. **Data Collection**: Searches Google Places API for healthcare providers
2. **AI Description Generation**: Creates natural, informative descriptions using Claude AI
3. **WordPress Publishing**: Publishes provider data to WordPress with proper categorization

## Search Process Explained

### How Search Queries Are Generated

The system generates search queries using:
- **Cities**: Tokyo, Yokohama, Osaka, Fukuoka, Kyoto (default)
- **Specialties**: 7 focused medical specialties from `specialties.json`
- **Search Terms**: 6 different English-friendly search patterns

**Query Formula:**
```
4 specialty-specific terms × 7 specialties × 5 cities = 140 queries
2 generic terms × 5 cities = 10 queries
Total = 150 search queries
```

**Example queries:**
- "English speaking Dentistry Tokyo"
- "International Emergency Medicine Osaka"
- "Foreign friendly Gynecology Fukuoka"
- "doctor Kyoto"

### Why You Get Fewer Results Than Queries

```
150 Search Queries → ~30-50 Unique Providers
```

**Key factors:**

1. **max_per_query Limitation**: Only takes top N results per query
   - `daily_limit < 50`: max_per_query = 1 (top result only)
   - `daily_limit ≥ 50`: max_per_query = 2 (top 2 results)

2. **Deduplication**: Same provider appears in multiple searches
   - "English speaking Dentistry Tokyo" and "International Dentistry Tokyo" 
   - Often return the same top dental clinic
   - System removes duplicates using `google_place_id`

3. **Cache Hits**: Previously searched queries return cached results

4. **Empty Results**: Some specific combinations return 0 providers

5. **Daily Limit**: Collection stops when reaching the daily provider limit

### max_per_query Calculation

| Daily Limit | max_per_query | Theoretical Max Results |
|-------------|---------------|------------------------|
| 5           | 1             | 150                    |
| 30          | 1             | 150                    |
| 50          | 2             | 300                    |
| 100         | 2             | 300                    |

## Command Line Usage

### Basic Usage
```bash
python3 run_automation.py --daily-limit 50
```

### All Available Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--daily-limit` | int | 25 | Daily limit for provider collection |
| `--max-per-query` | int | auto | Maximum results per search query |
| `--cities` | list | Tokyo Yokohama Osaka Fukuoka Kyoto | Cities to search |
| `--query-limit` | int | 200 | Maximum search queries to generate |
| `--batch-size` | int | 5 | Batch size for AI description generation |
| `--skip-collection` | flag | false | Skip data collection phase |
| `--skip-descriptions` | flag | false | Skip AI description generation |
| `--skip-publishing` | flag | false | Skip WordPress publishing |

### Example Commands

**High-volume collection:**
```bash
python3 run_automation.py --daily-limit 100 --max-per-query 3
```

**Specific cities:**
```bash
python3 run_automation.py --daily-limit 50 --cities Tokyo Osaka
```

**Only run descriptions (skip collection):**
```bash
python3 run_automation.py --skip-collection --skip-publishing
```

**Custom batch processing:**
```bash
python3 run_automation.py --daily-limit 75 --batch-size 10
```

**Test configuration:**
```bash
python3 run_automation.py --daily-limit 5 --cities Tokyo --query-limit 50
```

**WordPress sync commands:**
```bash
# Sync all providers needing updates
python3 wordpress_sync_manager.py --sync-all --limit 20

# Sync specific provider
python3 wordpress_sync_manager.py --sync-provider "DENTAL OFFICE OTANI"

# Dry run to preview changes
python3 wordpress_sync_manager.py --sync-all --dry-run --limit 10

# Check sync status
python3 wordpress_sync_manager.py --status
```

## Optimization Strategies

### For Maximum Provider Discovery

1. **Use higher daily limits:**
   ```bash
   python3 run_automation.py --daily-limit 100
   # Gets max_per_query=2, potential for 200+ unique providers
   ```

2. **Force higher max_per_query:**
   ```bash
   python3 run_automation.py --daily-limit 50 --max-per-query 5
   # Takes top 5 results from each query
   ```

3. **Clear cache for fresh results:**
   ```bash
   rm -rf cache/*.pkl
   python3 run_automation.py --daily-limit 50
   ```

### For Targeted Collection

1. **Focus on specific cities:**
   ```bash
   python3 run_automation.py --cities Tokyo Yokohama --daily-limit 30
   ```

2. **Generate more queries:**
   ```bash
   python3 run_automation.py --query-limit 300 --daily-limit 75
   ```

## File Structure

```
healthcare_directory_v2/
├── run_automation.py              # Main automation script
├── google_places_integration.py   # Google Places API integration
├── claude_description_generator.py # AI description generation
├── wordpress_integration.py       # WordPress publishing
├── medical_specialty_filter.py    # Specialty validation/normalization
├── specialties.json               # Current focused specialties (7)
├── specialties-full.json          # Complete specialty list (34)
├── cities.json                     # Japanese cities data
├── cache/                          # Cached Google Places results
└── config/                         # Environment configuration
```

## Configuration Files

### specialties.json (Current Focus)
```json
{
  "specialties": [
    "ENT (Ear, Nose & Throat)",
    "Dentistry", 
    "Emergency Medicine",
    "General Medicine",
    "Pharmacy",
    "Gynecology",
    "Internal Medicine"
  ]
}
```

### Environment Setup
Create `config/.env` with:
```
GOOGLE_PLACES_API_KEY=your_google_places_api_key
ANTHROPIC_API_KEY=your_claude_api_key
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=localhost
WORDPRESS_URL=your_wordpress_site
WORDPRESS_USERNAME=your_wp_username
WORDPRESS_APP_PASSWORD=your_wp_app_password
```

## Cost Estimation

### Google Places API
- Text search: $0.017 per request
- Place details: $0.017 per request
- **Total per provider**: ~$0.034

### Claude AI
- Description generation: ~$0.01 per provider
- Batch processing reduces costs by ~40%

### Example Costs
| Daily Limit | Providers Found | Google API | Claude AI | Total |
|-------------|----------------|------------|-----------|-------|
| 30          | ~20            | $1.36      | $0.20     | $1.56 |
| 50          | ~35            | $2.38      | $0.35     | $2.73 |
| 100         | ~75            | $5.10      | $0.75     | $5.85 |

## Troubleshooting

### Low Results Despite High Daily Limit
- **Cause**: max_per_query too low, lots of duplicates
- **Solution**: Use `--max-per-query 3` or higher

### Cache Issues
- **Cause**: Loading old cached results
- **Solution**: Clear cache with `rm -rf cache/*.pkl`

### Specialty Formatting Issues
- **Cause**: Inconsistent specialty names
- **Solution**: System auto-normalizes to proper format (e.g., "ent" → "ENT (Ear, Nose & Throat)")

### API Rate Limits
- **Cause**: Too many requests too quickly
- **Solution**: Lower daily-limit or use built-in rate limiting

## Updating Existing Providers

When you implement fixes or improvements, you can update existing providers in the database without re-collecting data. The system provides several methods for updating providers with new AI descriptions, location data, and other enhancements.

### Available Update Scripts

| Script | Purpose | Use Case |
|--------|---------|----------|
| `update_existing_providers.py` | Comprehensive updates | Most flexible, full control |
| `force_update_all.py` | Quick updates | Simple, fast updates |
| `populate_provider_locations.py` | Location data only | Google Maps coordinates |

### Comprehensive Update Script (`update_existing_providers.py`)

This is the most powerful script for updating existing providers. It bypasses the normal filtering logic and gives you complete control.

#### Update Enhanced Descriptions & Excerpts

```bash
# Update descriptions for specific city (recommended for testing)
python3 update_existing_providers.py --descriptions --city "Yokohama" --limit 10

# Update descriptions for all providers (use with caution)
python3 update_existing_providers.py --descriptions --limit 50

# Force update even if descriptions already exist
python3 update_existing_providers.py --descriptions --force --limit 20

# Update only published providers
python3 update_existing_providers.py --descriptions --status "published" --limit 15

# Custom batch size for AI generation
python3 update_existing_providers.py --descriptions --batch-size 3 --limit 15
```

#### Update Location Data (Google Maps)

```bash
# Add latitude/longitude for providers missing location data
python3 update_existing_providers.py --locations --limit 20

# Update specific city
python3 update_existing_providers.py --locations --city "Tokyo" --limit 25

# Update all providers in a city
python3 update_existing_providers.py --locations --city "Osaka" --limit 100
```

#### Clear and Regenerate Content

```bash
# Clear existing descriptions to force regeneration
python3 update_existing_providers.py --clear --city "Yokohama" --limit 10

# Then regenerate with enhanced format
python3 update_existing_providers.py --descriptions --city "Yokohama" --limit 10
```

#### Update Everything

```bash
# Update both descriptions and locations
python3 update_existing_providers.py --all --city "Yokohama" --limit 10

# Update everything with custom settings
python3 update_existing_providers.py --all --limit 25 --batch-size 3 --force
```

### Quick Update Script (`force_update_all.py`)

For simple, fast updates without command line arguments:

```bash
# Update all providers (50 limit)
python3 force_update_all.py

# Update specific city
python3 force_update_all.py "Yokohama"

# Update specific city with custom limit
python3 force_update_all.py "Tokyo" 25
```

### Location Population Script (`populate_provider_locations.py`)

Specifically for adding Google Maps coordinates:

```bash
# Add coordinates for providers missing location data
python3 populate_provider_locations.py
```

### Command Line Parameters

#### `update_existing_providers.py` Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `--descriptions` | flag | Update AI descriptions and excerpts |
| `--locations` | flag | Update latitude/longitude for Google Maps |
| `--clear` | flag | Clear existing descriptions for regeneration |
| `--all` | flag | Update everything (descriptions + locations) |
| `--city` | string | Filter by specific city |
| `--limit` | int | Limit number of providers to process |
| `--status` | string | Filter by status (pending, description_generated, published) |
| `--force` | flag | Force update even if content exists |
| `--batch-size` | int | Batch size for AI generation (default: 5) |

### Recommended Update Workflow

When implementing fixes like enhanced descriptions or location data:

#### 1. Test with Small Batch First
```bash
python3 update_existing_providers.py --descriptions --city "Yokohama" --limit 5
```

#### 2. Check Results and Scale Up
```bash
python3 update_existing_providers.py --descriptions --city "Yokohama" --limit 20
```

#### 3. Add Location Data
```bash
python3 update_existing_providers.py --locations --city "Yokohama" --limit 20
```

#### 4. Sync to WordPress
```bash
python3 wordpress_integration.py
```

### Update Strategies

#### For Description Quality Improvements
```bash
# Clear old descriptions and regenerate with latest prompts
python3 update_existing_providers.py --clear --limit 30
python3 update_existing_providers.py --descriptions --limit 30
```

#### For Google Maps Fix
```bash
# Add coordinates to enable maps
python3 update_existing_providers.py --locations --limit 50
```

#### For Complete Refresh
```bash
# Clear and update everything
python3 update_existing_providers.py --clear --limit 20
python3 update_existing_providers.py --all --limit 20
```

### Filtering Logic

The update scripts bypass the normal filtering in `run_automation.py` that prevents updating providers with existing content. This allows you to:

- Update providers that already have AI descriptions
- Force regeneration with improved prompts
- Add missing data like location coordinates
- Update published providers in WordPress

### Cost Considerations

#### Description Updates
- **Claude AI**: ~$0.01 per provider for descriptions + excerpts
- **Batch processing**: Reduces costs by ~40%

#### Location Updates
- **Google Geocoding API**: ~$0.005 per provider
- **Rate limiting**: 200ms delay between requests

#### Example Costs
| Update Type | 20 Providers | 50 Providers | 100 Providers |
|-------------|--------------|--------------|---------------|
| Descriptions | $0.12 | $0.30 | $0.60 |
| Locations | $0.10 | $0.25 | $0.50 |
| Both | $0.22 | $0.55 | $1.10 |

### WordPress Integration

After updating providers, sync changes to WordPress:

```bash
# Sync all providers ready for publishing
python3 wordpress_integration.py

# Check WordPress posts to verify updates
# - Enhanced descriptions appear in ACF wysiwyg field
# - Excerpts sync to both ACF and native WordPress excerpt
# - Google Maps display with latitude/longitude coordinates
```

### Troubleshooting Updates

#### API Key Issues
- **Error**: "❌ Google API key required for location updates"
- **Fix**: Check `config/.env` has `GOOGLE_PLACES_API_KEY=your_key`

#### Rate Limiting
- **Error**: 429 Too Many Requests
- **Fix**: Built-in rate limiting included (200ms delays)

#### Memory Issues
- **Error**: Large batch processing fails
- **Fix**: Reduce `--batch-size` to 3 or lower

#### Mixed Results
- **Issue**: Some providers update, others don't
- **Fix**: Check database constraints and API responses in logs

## Recent Improvements

### Fixed Issues
- ✅ **Phone numbers removed** from AI descriptions
- ✅ **Specialty formatting** standardized to proper display format
- ✅ **Description quality** improved with 140-150 word structured format
- ✅ **Batch processing** implemented for cost efficiency
- ✅ **Location data** added for Google Maps integration
- ✅ **Update scripts** created for existing provider maintenance

### Enhanced Features
- ✅ **Flexible command line options** for different use cases
- ✅ **Smart deduplication** using multiple fingerprinting methods
- ✅ **Comprehensive logging** for debugging and monitoring
- ✅ **Phase skipping** for partial runs
- ✅ **Provider update tools** for maintenance and improvements

---

# WordPress Sync Enhancement System

## Overview

The WordPress Sync Enhancement system provides **bidirectional content synchronization** between the PostgreSQL database and WordPress CMS. This solves the critical gap where the healthcare directory could create new WordPress posts but couldn't update existing ones when database descriptions were enhanced.

### Key Features

- **Bidirectional Sync**: Update existing WordPress posts with current database content
- **Change Detection**: SHA256-based content hashing for precise change identification
- **Selective Operations**: Sync by provider, city, specialty, or status
- **Batch Processing**: Efficient handling of 100+ providers with rate limiting
- **Dry-run Mode**: Preview changes without executing them
- **Comprehensive Logging**: Complete audit trail of all operations
- **Error Recovery**: Robust error handling and retry mechanisms
- **Performance Monitoring**: Detailed statistics and success rate tracking

### Database Schema

The system adds these tables and columns:

**New Table: `wordpress_sync_log`**
- Comprehensive audit trail of all sync operations
- Tracks success/failure rates, duration, and errors
- Links to provider records for complete history

**Enhanced `providers` table:**
- `last_wordpress_sync`: Timestamp of last sync operation
- `content_hash`: SHA256 hash for change detection
- `wordpress_status`: Current sync status (pending, synced, failed)

## WordPress Sync Commands

### Connection Testing

Test WordPress API connectivity:
```bash
python3 wordpress_sync_manager.py --test-connection
```

### Status Checking

View current sync status:
```bash
# Show overall sync status and statistics
python3 wordpress_sync_manager.py --status

# Check specific provider sync status
python3 wordpress_sync_manager.py --check-provider "PROVIDER_NAME"

# View sync operation history
python3 wordpress_sync_manager.py --history
```

### Individual Provider Sync

Sync a specific provider:
```bash
# Dry-run to preview changes
python3 wordpress_sync_manager.py --sync-provider "DENTAL OFFICE OTANI" --dry-run

# Execute the sync
python3 wordpress_sync_manager.py --sync-provider "DENTAL OFFICE OTANI"

# Force sync even if content appears unchanged
python3 wordpress_sync_manager.py --sync-provider "DENTAL OFFICE OTANI" --force
```

### Bulk Sync Operations

Sync multiple providers:
```bash
# Sync all providers needing updates (dry-run)
python3 wordpress_sync_manager.py --sync-all --dry-run

# Sync all with custom limit
python3 wordpress_sync_manager.py --sync-all --limit 20

# Sync providers in specific city
python3 wordpress_sync_manager.py --sync-city "Tokyo" --dry-run
python3 wordpress_sync_manager.py --sync-city "Osaka" --limit 15

# Sync providers by specialty
python3 wordpress_sync_manager.py --sync-specialty "Dentistry" --dry-run
```

### Command Line Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `--sync-provider NAME` | string | Sync specific provider by name |
| `--sync-all` | flag | Sync all providers needing updates |
| `--sync-city CITY` | string | Sync providers in specific city |
| `--sync-specialty TYPE` | string | Sync providers with specific specialty |
| `--dry-run` | flag | Preview changes without executing |
| `--limit NUMBER` | int | Limit number of providers to process |
| `--force` | flag | Force update even if content appears unchanged |
| `--status` | flag | Show sync status for all providers |
| `--check-provider NAME` | string | Check sync status for specific provider |
| `--history` | flag | Show sync operation history |
| `--test-connection` | flag | Test WordPress API connection |

## Usage Examples

### Safe Testing Workflow

Always start with dry-runs to preview changes:

```bash
# 1. Test connection
python3 wordpress_sync_manager.py --test-connection

# 2. Check current status
python3 wordpress_sync_manager.py --status

# 3. Preview what would be updated
python3 wordpress_sync_manager.py --sync-all --dry-run --limit 5

# 4. Execute small batch
python3 wordpress_sync_manager.py --sync-all --limit 5

# 5. Check results
python3 wordpress_sync_manager.py --history
```

### Production Sync Workflow

For production updates:

```bash
# 1. Check system status
python3 wordpress_sync_manager.py --status

# 2. Sync high-priority providers first
python3 wordpress_sync_manager.py --sync-city "Tokyo" --limit 10

# 3. Sync remaining providers in batches
python3 wordpress_sync_manager.py --sync-all --limit 25

# 4. Monitor results
python3 wordpress_sync_manager.py --status
```

### Targeted Updates

For specific maintenance tasks:

```bash
# Update all providers in Osaka
python3 wordpress_sync_manager.py --sync-city "Osaka"

# Update all dental clinics
python3 wordpress_sync_manager.py --sync-specialty "Dentistry" --limit 20

# Force update specific provider
python3 wordpress_sync_manager.py --sync-provider "St. Luke's International Hospital" --force
```

## Troubleshooting

### Common Issues and Solutions

#### 1. ACF Field Validation Errors

**Error:** `acf[wheelchair_accessible] is not one of Wheelchair accessible, Not wheelchair accessible, Wheelchair accessibility unknown`

**Solution:** The system now maps database values to WordPress ACF field values:
- Database `true/false` → WordPress `"Wheelchair accessible"/"Not wheelchair accessible"`
- Database `true/false` → WordPress `"Parking is available"/"Parking is not available"`

#### 2. WordPress API Authentication

**Error:** `403 Forbidden` or authentication failures

**Solution:** Check WordPress credentials in `config/.env`:
```bash
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APPLICATION_PASSWORD=your_app_password
```

#### 3. Rate Limiting

**Error:** `429 Too Many Requests`

**Solution:** The system includes built-in rate limiting:
- 2-second delays between batches
- Batch size of 10 providers (adjustable)
- Automatic retry mechanisms

#### 4. Database Connection Issues

**Error:** `Textual SQL expression should be explicitly declared as text()`

**Solution:** All SQL queries are now properly wrapped with `text()` for SQLAlchemy compatibility.

#### 5. Content Hash Mismatches

**Issue:** Providers show as needing updates when they haven't changed

**Solution:** Clear content hashes to force recalculation:
```sql
UPDATE providers SET content_hash = NULL WHERE id = [provider_id];
```

### Performance Optimization

#### Batch Size Tuning

For large sync operations:
```bash
# Smaller batches for stability
python3 wordpress_sync_manager.py --sync-all --limit 50

# Monitor system resources and adjust accordingly
```

#### Rate Limiting Configuration

The system respects WordPress API limits:
- **Batch size**: 10 providers per batch
- **Delay**: 2 seconds between batches
- **Timeout**: 30 seconds per request

### Error Recovery

#### Failed Sync Recovery

Check sync history to identify failed operations:
```bash
python3 wordpress_sync_manager.py --history
```

Retry specific providers:
```bash
python3 wordpress_sync_manager.py --sync-provider "FAILED_PROVIDER_NAME" --force
```

#### Database Consistency

Verify sync status:
```bash
python3 wordpress_sync_manager.py --status
```

Reset provider sync status if needed:
```sql
UPDATE providers SET wordpress_status = 'pending', content_hash = NULL 
WHERE wordpress_status = 'failed';
```

## Configuration

### Environment Variables

Required in `config/.env`:
```bash
# WordPress API Configuration
WORDPRESS_URL=https://care-compass.jp
WORDPRESS_USERNAME=api_user
WORDPRESS_APPLICATION_PASSWORD=wp_app_password_here

# Database Configuration (shared with main system)
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=localhost
POSTGRES_DB=directory

# Optional: Sync Configuration
WORDPRESS_SYNC_BATCH_SIZE=10
WORDPRESS_SYNC_DELAY=2
```

### WordPress Setup Requirements

Ensure WordPress has:
1. **REST API enabled** (default in modern WordPress)
2. **Application passwords enabled** for API authentication
3. **ACF (Advanced Custom Fields) plugin** with proper field definitions
4. **Custom post type** `healthcare_provider` configured

### Database Migration

The sync system requires database schema updates:
```bash
# Run migration to add sync tables and columns
python3 migrate_wordpress_sync_tables.py
```

This adds:
- `wordpress_sync_log` table for operation tracking
- `last_wordpress_sync`, `content_hash`, `wordpress_status` columns to providers table
- Proper indexes for performance

## System Architecture

### Components

1. **ContentHashService**: SHA256-based change detection
2. **WordPressUpdateService**: WordPress API integration
3. **SyncManagementService**: High-level operation orchestration
4. **WordPressSyncManager**: Command-line interface

### Data Flow

```
Database Content → Content Hash → Change Detection → WordPress API → Sync Logging
```

### Content Mapping

The system maps database fields to WordPress:
- **Post content**: Formatted HTML with provider details
- **ACF fields**: Structured data for all provider attributes
- **Post title**: Provider name
- **Post excerpt**: AI-generated excerpt

### Sync Status Tracking

Each provider has a sync status:
- **pending**: Not yet synced or needs update
- **synced**: Successfully synchronized
- **failed**: Last sync attempt failed

## Best Practices

### Regular Maintenance

1. **Monitor sync status weekly:**
   ```bash
   python3 wordpress_sync_manager.py --status
   ```

2. **Review sync history for errors:**
   ```bash
   python3 wordpress_sync_manager.py --history
   ```

3. **Test connection before bulk operations:**
   ```bash
   python3 wordpress_sync_manager.py --test-connection
   ```

### Safe Operation Guidelines

1. **Always use dry-run first** for bulk operations
2. **Start with small batches** (limit 5-10) for testing
3. **Monitor WordPress site** during sync operations
4. **Keep backups** of WordPress database before major syncs
5. **Check error logs** for any API issues

### Performance Guidelines

1. **Batch size**: Keep at 10 providers for optimal performance
2. **Rate limiting**: Don't modify the 2-second delays
3. **Concurrent operations**: Run only one sync at a time
4. **Peak hours**: Avoid large syncs during high WordPress traffic

## Support

For WordPress Sync Enhancement issues:

1. **Check sync status:** `python3 wordpress_sync_manager.py --status`
2. **Review history:** `python3 wordpress_sync_manager.py --history`
3. **Test connection:** `python3 wordpress_sync_manager.py --test-connection`
4. **Verify configuration:** Check `config/.env` credentials
5. **Check logs:** Review error messages in terminal output
6. **Database verification:** Ensure migration completed successfully

---

## General System Support

For main healthcare directory issues:
1. Check the logs for specific error messages
2. Verify API keys in `config/.env`
3. Test with lower daily limits first
4. Clear cache if getting stale results 