# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a healthcare directory automation system for international patients in Japan. It uses Google Places API, Claude AI, PostgreSQL, and WordPress to discover, process, and publish healthcare provider data with a focus on English-speaking support.

**Core Technologies:**
- Python 3.12+ (Homebrew) with SQLAlchemy, psycopg2
- PostgreSQL database for provider data
- WordPress REST API with ACF Pro for content management
- Google Places API for provider discovery (photos disabled)
- Claude AI (Anthropic) for content generation

## Development Commands

### Main Automation Scripts (Unified Pipeline)
```bash
# Complete pipeline (collection → AI content → WordPress)
python3 scripts/run_pipeline.py --mode full --limit 50

# Collection only (discover new providers)
python3 scripts/run_pipeline.py --mode collect --limit 20

# AI content generation only
python3 scripts/run_pipeline.py --mode process --batch-size 4

# WordPress publishing only
python3 scripts/run_pipeline.py --mode publish --limit 25

# Check system status
python3 scripts/run_pipeline.py --status-only
```

### Testing Commands
```bash
# Test database connection
python3 utility/tests/test_db_connection.py

# Test WordPress API connection
python3 wordpress_sync_manager.py --test-connection

# Test unified pipeline (dry run)
python3 scripts/run_pipeline.py --mode full --limit 5 --dry-run
```

### Database Operations
```bash
# Run database migrations
python3 utility/migrate/migrate_wordpress_sync_tables.py
python3 utility/migrate/migrate_business_hours.py
python3 utility/migrate/migrate_proficiency_score.py

# Manual database editing via psql
psql -d directory
```

### Individual Provider Management
```bash
# Add specific provider by name
python3 add_specific_provider.py --name "Clinic Name" --location "Tokyo"

# Add provider by Google Place ID
python3 add_specific_provider.py --place-id "ChIJN1t_tDeuEmsRUsoyG83frY4"

# Add providers by geographic area (RECOMMENDED for city collection)
python3 add_geographic_providers.py --city "Tokyo" --wards "Shibuya,Minato" --specialty "ENT" --limit 10
```

### IMPORTANT: Correct Collection Methods
```bash
# ✅ CORRECT - These scripts properly save to database:
python3 scripts/run_pipeline.py --mode collect --limit 100  # Uses collect_providers()
python3 add_geographic_providers.py --city Tokyo --limit 500  # Uses unified pipeline

# ❌ INCORRECT - Do not use for collection:
python3 scripts/collect_top_cities.py  # BUG: Uses search_providers() which doesn't save to DB
```

**Technical Note**: The `GooglePlacesCollector` class has two key methods:
- `search_providers()` - Only searches and returns raw results (doesn't save to database)
- `collect_providers()` - Searches, gets details, filters by English proficiency, and saves to database

Always use scripts that call `collect_providers()` or use the unified pipeline for proper data collection.

## Architecture Overview

### Core Components (Unified Architecture)

1. **Unified Pipeline** (`src/core/pipeline.py`)
   - Single orchestrator for all operations
   - Modes: collect, process, publish, full
   - Cost tracking and budget enforcement
   - Progress tracking with database persistence

2. **Data Collection** (`src/collectors/`)
   - `google_places.py` - Advanced search with 150+ query variations
   - `deduplication.py` - Fingerprint-based duplicate detection
   - English proficiency filtering (score ≥3 required)

3. **AI Content Generation** (`src/processors/ai_content.py`)
   - Mega-batch processing: 6 content types in single API call
   - 90.4% API call reduction vs individual processing
   - Premium quality with 3,000 tokens per provider
   - Intelligent retry logic for 99%+ success rate

4. **WordPress Publishing** (`src/publishers/`)
   - `wordpress.py` - Unified publisher for create/update operations
   - `content_hash.py` - Change detection (SHA256 hashing)
   - ACF fields-only architecture (35+ mapped fields)
   - Batch processing with error recovery

5. **Core Infrastructure** (`src/core/`)
   - `database.py` - Unified database operations
   - `models.py` - SQLAlchemy models with proper field mapping
   - `cache.py` - Persistent SQLite caching (75% cost reduction)
   - `cost_tracker.py` - API cost tracking with limits



### Data Flow

```
Google Places → PostgreSQL → AI Content Generation → WordPress Sync
      ↓              ↓                    ↓                ↓
  Deduplication   Provider Table    Mega-batch Process   ACF Fields
  Fingerprinting  Content Storage   4 Content Types     REST API
```

### Key Scripts by Function

**Main Pipeline:**
- `scripts/run_pipeline.py` - Unified pipeline runner (replaces all run_*.py scripts)

**User-Facing Scripts:**
- `add_specific_provider.py` - Add individual provider by name or Place ID
- `add_geographic_providers.py` - Add providers by geographic area
- `publish_approved.py` - Publish providers with content to WordPress


**Utilities:**
- `utility/migrate/*.py` - Database migration scripts
- `utility/tests/*.py` - Test scripts

## Environment Configuration

Required environment variables in `config/.env`:
```bash
GOOGLE_PLACES_API_KEY=your_google_places_api_key
ANTHROPIC_API_KEY=your_claude_api_key
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=localhost
POSTGRES_DB=directory
WORDPRESS_URL=https://your-wordpress-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APPLICATION_PASSWORD=your_app_password
```

## Important Implementation Details

### English Proficiency Filtering
The system automatically filters providers based on English proficiency scoring:
- **Score 5**: 'Fluent' (40+ points) ✅ ACCEPTED
- **Score 4**: 'Conversational' (20-39 points) ✅ ACCEPTED  
- **Score 3**: 'Basic' (10-19 points) ✅ ACCEPTED (minimum)
- **Score 0**: 'Unknown' (<10 points) ❌ REJECTED (~70% rejection rate)

### Mega-Batch Processing Optimization
- **Batch size 2**: Optimized for reliability vs speed
- **3,000 tokens per provider**: Premium quality allocation
- **Intelligent retry logic**: Individual fallback for failed batches
- **Zero fallback content**: Enhanced error handling prevents generic content

### WordPress ACF Architecture
- **ACF fields only**: Post content is minimal, all data in ACF fields
- **35+ field mappings**: Complete database-to-WordPress sync
- **Change detection**: SHA256 content hashing for selective updates
- **Taxonomy management**: Auto-resolution of specialty/location terms

## Development Guidelines

### Adding New Features
1. Follow existing patterns in similar scripts
2. Use the PostgreSQL integration layer (`postgres_integration.py`)
3. Implement proper error handling and logging
4. Test with dry-run modes before production use

### Code Conventions
- Use type hints for function parameters and returns
- Follow existing naming conventions (snake_case for functions/variables)
- Include comprehensive error handling with try/catch blocks
- Add logging for debugging and monitoring

### Testing Approach
- Always test with `--dry-run` flags first
- Use small `--limit` values for testing
- Test database connections before running automation
- Verify WordPress API connectivity before sync operations
- ALWAYS CLEAN UP TEST FILES

## Common Workflows

### Daily Operations (Command Line)
```bash
# 1. Check system status
python3 scripts/run_pipeline.py --status-only

# 2. Run full pipeline (collect → process → publish)
python3 scripts/run_pipeline.py --mode full --limit 50

# 3. Or run phases separately:
# Collect new providers
python3 scripts/run_pipeline.py --mode collect --limit 20

# Generate AI content for pending providers
python3 scripts/run_pipeline.py --mode process

# Publish to WordPress
python3 scripts/run_pipeline.py --mode publish --limit 25
```

### Troubleshooting
```bash
# Test connections
python3 utility/tests/test_db_connection.py
python3 wordpress_sync_manager.py --test-connection

# Test with minimal batch
python3 scripts/run_pipeline.py --mode full --limit 1 --dry-run

# Process specific providers
python3 scripts/run_pipeline.py --mode process --provider-ids 1,2,3
```

### Manual Database Editing
```bash
# Connect to database
psql -d directory

# Find provider
SELECT id, provider_name FROM providers WHERE provider_name ILIKE '%search%';

# Edit with psql editor
\e
# Type UPDATE statement, save and exit to execute
```

## Performance Optimization

### API Efficiency
- Mega-batch processing: 90.4% reduction in API calls
- Persistent caching: 75% reduction in Google Places API costs
- Cost tracking: Automatic daily ($10) and monthly ($85) limits
- Processing speed: 4x faster with batch operations

### Caching System
- Place details: 30-day cache (permanent for stable data)
- Search results: 7-day cache
- SQLite-based: No external dependencies

### Database Performance
- Unified database manager with connection pooling
- Proper column mapping
- Indexed queries for provider lookups
- Batch operations for efficiency

### WordPress Sync
- Selective updates based on content hashing
- Batch size optimization for API rate limits
- Error recovery with comprehensive logging
- Separate create/update operations

## Current System State (Updated 2025-01-26)

### Recent Improvements Completed
- ✅ **Unified Pipeline Architecture**: Consolidated 82+ scripts into ~25 core modules with 75% code reduction
- ✅ **Cost Optimization**: Persistent caching reduces API costs by 75% (from $170 to under $85/month)
- ✅ **Single Command Interface**: `scripts/run_pipeline.py` replaces multiple automation scripts
- ✅ **API Endpoint Updates**: All API endpoints now use new unified modules
- ✅ **User Script Updates**: Updated add_specific_provider.py, add_geographic_providers.py, publish_approved.py
- ✅ **SSL/urllib3 Compatibility Fixed**: Migrated to Homebrew Python 3.12 with virtual environment
- ✅ **Photo Collection Removed**: All photo-related functionality has been deprecated
- ✅ **Web Interface Deprecated**: Moved to deprecated/ folder - use command line interface only



### Technical Architecture


### Known Technical Considerations

**Python Environment:**
- Using Homebrew Python 3.12 at `/opt/homebrew/bin/python3`
- Virtual environment at `venv/` with all required dependencies
- SSL compatibility resolved with OpenSSL 3.5.0

**Process Management:**
- Uses `subprocess.Popen` for background task execution
- Implements `psutil` for reliable process monitoring
- In-memory process tracking with automatic cleanup
- Working directory properly set to project root for all subprocess calls

**Database Integration:**
- All operations use existing PostgreSQL integration layer
- Maintains compatibility with existing command-line automation scripts

### Pending Improvements
- 🔄 **Status System Standardization**: Apply unified status terminology to content generation components
- 🔄 **Unified StatusIndicator Component**: Create reusable status display component
- 🔄 **Enhanced Error Handling**: Improve error display and recovery mechanisms

### Recently Fixed Issues

**WordPress Sync Workflow Gap (FIXED):**
- ✅ **Issue**: Providers with `description_generated` status had AI content but no WordPress posts
- ✅ **Solution**: Updated `publish_approved.py` to create initial WordPress posts for providers with content
- ✅ **New Workflow**: Use `python3 publish_approved.py` to publish providers stuck in `description_generated` status
- ✅ **Pipeline Integration**: The unified pipeline now handles both create and update operations seamlessly

### Troubleshooting Notes

**Common Issues:**
1. **Providers Stuck in `description_generated`**: Use `publish_approved.py` to create initial WordPress posts
2. **Sync Not Starting**: Check that the unified pipeline is properly configured
3. **Process Tracking Issues**: Verify psutil is installed (`pip install psutil`)
4. **SSL/Python Issues**: Use Homebrew Python 3.12 environment as documented
5. **Modal Not Loading Providers**: Check API endpoint connectivity and database access

**Debug Commands:**
```bash
# Check system status and gaps
python3 scripts/run_pipeline.py --status-only

# Check providers needing WordPress posts
python3 publish_approved.py --dry-run

# Check pipeline status
python3 scripts/run_pipeline.py --status-only

# Verify process tracking
python3 -c "import psutil; print('psutil OK')"

# Test database connectivity
python3 utility/tests/test_db_connection.py

# View recent pipeline runs
python3 -c "
from src.core.database import DatabaseManager
from sqlalchemy import text

db = DatabaseManager()
session = db.get_session()

print('=== Recent Pipeline Runs ===')
runs = session.execute(text('''
    SELECT run_id, mode, status, providers_processed, created_at 
    FROM pipeline_runs 
    ORDER BY created_at DESC 
    LIMIT 5
''')).fetchall()

for run in runs:
    print(f'{run.created_at}: {run.mode} - {run.status} ({run.providers_processed} providers)')

session.close()
"
```

**Migration Notes:**
1. **Deprecated Scripts**: Old scripts moved to `deprecated_scripts/` folder - do not use
2. **Import Updates**: All scripts now use `src.*` imports instead of direct imports
3. **Command Changes**: Replace old run_*.py commands with `scripts/run_pipeline.py`
4. **Caching**: First run may be slower as cache builds, subsequent runs will be much faster

### Japanese Provider Name Processing (Romaji)

**Unified Processing Script:**
```bash
# Process all Japanese providers (generate romaji + update WordPress)
python3 scripts/process_japanese_providers.py

# Process with limit
python3 scripts/process_japanese_providers.py --limit 50

# Preview changes without applying
python3 scripts/process_japanese_providers.py --dry-run
```

**Romaji Conversion Features:**
- Automatic detection of Japanese text (hiragana, katakana, kanji)
- Medical term translation (not just transliteration):
  - クリニック → Clinic (not Kurinikku)
  - 病院 → Hospital (not Byouin)  
  - 薬局 → Pharmacy (not Yakkyoku)
  - 歯科 → Dental (not Shika)
  - 小児科 → Pediatrics (not Shounika)
- WordPress titles use romaji-only format (no Japanese in parentheses)
- Database column: `provider_name_romaji VARCHAR(500)`
- Utility module: `src/utils/romaji_converter.py`

**Technical Requirements:**
- cutlet>=0.3.0 (for romaji conversion)
- mecab and unidic-lite (for Japanese text processing)
- Installed via: `pip3 install cutlet unidic-lite`