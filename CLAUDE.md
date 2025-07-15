# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a healthcare directory automation system for international patients in Japan. It uses Google Places API, Claude AI, PostgreSQL, and WordPress to discover, process, and publish healthcare provider data with a focus on English-speaking support.

**Core Technologies:**
- Python 3.8+ with Flask, SQLAlchemy, psycopg2
- PostgreSQL database for provider data
- WordPress REST API with ACF Pro for content management
- Google Places API for provider discovery
- Claude AI (Anthropic) for content generation

## Development Commands

### Main Automation Scripts
```bash
# Complete 6-phase pipeline (collection → AI content → WordPress)
python3 run_automation.py --daily-limit 50

# Premium AI content generation (mega-batch processing)
python3 run_mega_batch_automation.py --all-providers

# Check system status and content completion
python3 run_mega_batch_automation.py --stats-only

# WordPress sync operations
python3 wordpress_sync_manager.py --sync-all --limit 25
```

### Testing Commands
```bash
# Test database connection
python3 utility/tests/test_db_connection.py

# Test WordPress API connection
python3 wordpress_sync_manager.py --test-connection

# Test mega-batch processor
python3 utility/tests/test_mega_batch.py

# Test with small batch (dry run)
python3 run_mega_batch_automation.py --limit 5 --dry-run
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

# Add providers by geographic area
python3 add_geographic_providers.py --city "Tokyo" --wards "Shibuya,Minato" --specialty "ENT" --limit 10
```

## Architecture Overview

### Core Components

1. **Data Collection Pipeline** (`google_places_integration.py`)
   - Advanced search with 150+ query variations
   - Fingerprint-based deduplication system
   - English proficiency filtering (score ≥3 required)

2. **AI Content Generation** (`claude_mega_batch_processor.py`)
   - Mega-batch processing: 4 content types in single API call
   - 90.4% API call reduction vs individual processing
   - Premium quality with 3,000 tokens per provider
   - Intelligent retry logic for 99%+ success rate

3. **WordPress Sync System** (`wordpress_sync_manager.py`, `sync_management_service.py`)
   - Bidirectional sync with change detection (SHA256 hashing)
   - ACF fields-only architecture (35+ mapped fields)
   - Batch processing with error recovery

4. **Database Layer** (`postgres_integration.py`)
   - PostgreSQL with 25+ provider fields
   - Sync tracking tables for WordPress operations
   - Performance-optimized indexing

### Data Flow

```
Google Places → PostgreSQL → AI Content Generation → WordPress Sync
      ↓              ↓                    ↓                ↓
  Deduplication   Provider Table    Mega-batch Process   ACF Fields
  Fingerprinting  Content Storage   4 Content Types     REST API
```

### Key Scripts by Function

**Data Collection:**
- `run_automation.py` - Complete 6-phase pipeline
- `google_places_integration.py` - Google Places API integration
- `add_specific_provider.py` - Individual provider addition
- `add_geographic_providers.py` - Geographic bulk addition

**AI Content:**
- `claude_mega_batch_processor.py` - Primary content generator
- `claude_description_generator.py` - Individual descriptions
- `claude_review_summarizer.py` - Review analysis
- `claude_english_experience_summarizer.py` - Language support analysis

**WordPress Integration:**
- `wordpress_sync_manager.py` - Primary sync management
- `wordpress_update_service.py` - WordPress API operations
- `content_hash_service.py` - Change detection

**Utilities:**
- `provider_fingerprinting.py` - Deduplication system
- `medical_specialty_filter.py` - Specialty validation
- `populate_provider_locations.py` - Location data enhancement

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

## Common Workflows

### Daily Operations
```bash
# 1. Check system status
python3 run_mega_batch_automation.py --stats-only

# 2. Process new content (with preview)
python3 run_mega_batch_automation.py --limit 20 --dry-run
python3 run_mega_batch_automation.py --limit 20

# 3. Sync to WordPress
python3 wordpress_sync_manager.py --sync-all --limit 25
```

### Troubleshooting
```bash
# Test connections
python3 utility/tests/test_db_connection.py
python3 wordpress_sync_manager.py --test-connection

# Check specific provider status
python3 wordpress_sync_manager.py --check-provider "Provider Name"

# Test with minimal batch
python3 run_mega_batch_automation.py --limit 1 --dry-run
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
- Cost savings: 85-90% vs individual processing
- Processing speed: 4x faster with batch operations

### Database Performance
- Use indexed queries for provider lookups
- Batch database operations when possible
- Monitor sync operation performance with timing

### WordPress Sync
- Selective updates based on content hashing
- Batch size optimization for API rate limits
- Error recovery with comprehensive logging