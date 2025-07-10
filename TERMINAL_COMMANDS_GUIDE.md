# Healthcare Directory - Complete Terminal Commands Guide
**Comprehensive Reference for All System Commands and Scripts**

## 📋 Table of Contents

1. [Core Automation Scripts](#core-automation-scripts)
2. [AI Content Generation](#ai-content-generation)
3. [WordPress Sync Operations](#wordpress-sync-operations)
4. [Data Collection & Management](#data-collection--management)
5. [Database Operations](#database-operations)
6. [Testing & Validation](#testing--validation)
7. [Utility Scripts](#utility-scripts)
8. [Quick Reference Tables](#quick-reference-tables)

---

## 🚀 Core Automation Scripts

### `run_automation.py` - Main 6-Phase Pipeline

**Description**: Complete healthcare directory automation including data collection, AI content generation, and WordPress publishing.

#### **Basic Usage**
```bash
# Run complete 6-phase pipeline
python3 run_automation.py

# With custom daily limit
python3 run_automation.py --daily-limit 50
```

#### **All Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--daily-limit` | int | 25 | Daily limit for provider collection |
| `--max-per-query` | int | auto | Maximum results per search query |
| `--cities` | list | Tokyo Yokohama Osaka Fukuoka Kyoto | Cities to search |
| `--query-limit` | int | 200 | Maximum search queries to generate |
| `--batch-size` | int | 5 | Batch size for AI description generation |
| `--skip-collection` | flag | false | Skip data collection phase |
| `--skip-descriptions` | flag | false | Skip AI description generation phase |
| `--skip-experience-summary` | flag | false | Skip English experience summarization |
| `--skip-review-summary` | flag | false | Skip review summarization |
| `--skip-publishing` | flag | false | Skip WordPress publishing phase |

#### **Example Commands**
```bash
# High-volume collection
python3 run_automation.py --daily-limit 100 --max-per-query 3

# Targeted city collection
python3 run_automation.py --daily-limit 50 --cities Tokyo Osaka

# Custom search scope
python3 run_automation.py --daily-limit 75 --query-limit 300

# Skip data collection, only process content
python3 run_automation.py --skip-collection --skip-publishing

# Only content generation phases
python3 run_automation.py --skip-collection --skip-descriptions

# Test with minimal settings
python3 run_automation.py --daily-limit 5 --cities Tokyo --query-limit 50
```

#### **Phase Breakdown**
1. **🌐 Data Collection**: Google Places API with deduplication
2. **🗺️ Location Population**: Missing location data enhancement
3. **🤖 AI Description Generation**: Batch-processed descriptions + excerpts
4. **📝 English Experience Summarization**: Language support analysis
5. **⭐ Review Summarization**: Patient insights analysis
6. **🌐 WordPress Publishing**: Automated content publishing

---

## 🤖 AI Content Generation

### `run_mega_batch_automation.py` - Premium AI Content Processor

**Description**: Mega-batch AI content generation with 90.4% API call reduction and premium quality.

#### **Basic Usage**
```bash
# Process all providers needing content
python3 run_mega_batch_automation.py --all-providers

# Check current system status
python3 run_mega_batch_automation.py --stats-only
```

#### **All Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--batch-size` | int | 4 | Number of providers per batch |
| `--limit` | int | 20 | Limit number of providers to process |
| `--dry-run` | flag | false | Show what would be processed without executing |
| `--all-providers` | flag | false | Process all providers (removes default limits) |
| `--stats-only` | flag | false | Only show provider statistics |

#### **Example Commands**
```bash
# Check system status first
python3 run_mega_batch_automation.py --stats-only

# Test with small batch
python3 run_mega_batch_automation.py --limit 10 --dry-run

# Process all providers with cost preview
python3 run_mega_batch_automation.py --all-providers --dry-run

# Process all providers (production)
python3 run_mega_batch_automation.py --all-providers

# Custom batch processing
python3 run_mega_batch_automation.py --limit 20 --batch-size 3
```

#### **Content Types Generated**
- **📄 AI Descriptions**: 150-175 words, 2-paragraph format
- **📝 AI Excerpts**: 50-75 words, engaging previews
- **⭐ Review Summaries**: 80-100 words, patient insights
- **🗣️ English Experience Summaries**: 80-100 words, language support

### Individual AI Content Scripts

#### `claude_description_generator.py`
```bash
# Generate descriptions and excerpts
python3 claude_description_generator.py

# With custom batch size
python3 claude_description_generator.py --batch-size 3
```

#### `claude_review_summarizer.py`
```bash
# Generate review summaries
python3 claude_review_summarizer.py

# Process specific city
python3 claude_review_summarizer.py --city "Tokyo"
```

#### `claude_english_experience_summarizer.py`
```bash
# Generate English experience summaries
python3 claude_english_experience_summarizer.py

# With custom limit
python3 claude_english_experience_summarizer.py --limit 50
```

---

## 🌐 WordPress Sync Operations

### `wordpress_sync_manager.py` - Complete Sync Management

**Description**: Comprehensive WordPress synchronization with change detection and batch processing.

#### **Connection & Status Commands**
```bash
# Test WordPress API connection
python3 wordpress_sync_manager.py --test-connection

# Show overall sync status
python3 wordpress_sync_manager.py --status

# Check specific provider status
python3 wordpress_sync_manager.py --check-provider "PROVIDER_NAME"

# View sync operation history
python3 wordpress_sync_manager.py --history
```

#### **Individual Provider Sync**
```bash
# Dry-run preview for specific provider
python3 wordpress_sync_manager.py --sync-provider "DENTAL OFFICE OTANI" --dry-run

# Execute sync for specific provider
python3 wordpress_sync_manager.py --sync-provider "DENTAL OFFICE OTANI"

# Force sync even if unchanged
python3 wordpress_sync_manager.py --sync-provider "DENTAL OFFICE OTANI" --force
```

#### **Bulk Sync Operations**
```bash
# Sync all providers needing updates (preview)
python3 wordpress_sync_manager.py --sync-all --dry-run

# Sync all with custom limit
python3 wordpress_sync_manager.py --sync-all --limit 50

# Sync providers by city
python3 wordpress_sync_manager.py --sync-city "Tokyo" --dry-run
python3 wordpress_sync_manager.py --sync-city "Osaka" --limit 15

# Sync providers by specialty
python3 wordpress_sync_manager.py --sync-specialty "Dentistry" --dry-run
python3 wordpress_sync_manager.py --sync-specialty "Internal Medicine" --limit 20
```

#### **All Parameters**
| Parameter | Type | Description |
|-----------|------|-------------|
| `--sync-provider NAME` | string | Sync specific provider by name |
| `--sync-all` | flag | Sync all providers needing updates |
| `--sync-city CITY` | string | Sync providers in specific city |
| `--sync-specialty TYPE` | string | Sync providers with specific specialty |
| `--dry-run` | flag | Preview changes without executing |
| `--limit NUMBER` | int | Limit number of providers to process |
| `--force` | flag | Force update even if unchanged |
| `--status` | flag | Show sync status for all providers |
| `--check-provider NAME` | string | Check sync status for specific provider |
| `--history` | flag | Show sync operation history |
| `--test-connection` | flag | Test WordPress API connection |

### Legacy WordPress Integration
```bash
# Original WordPress publishing script
python3 wordpress_integration.py

# Publish all approved providers
python3 publish_approved.py
```

---

## 📊 Data Collection & Management

### `google_places_integration.py`
```bash
# Direct Google Places collection
python3 google_places_integration.py

# Custom city and limit
python3 google_places_integration.py --cities Tokyo --limit 25
```

### `update_existing_providers.py` - Provider Maintenance
```bash
# Update descriptions for specific city
python3 update_existing_providers.py --descriptions --city "Yokohama" --limit 10

# Update locations (coordinates)
python3 update_existing_providers.py --locations --city "Tokyo" --limit 25

# Update everything
python3 update_existing_providers.py --all --city "Osaka" --limit 15

# Force update even if content exists
python3 update_existing_providers.py --descriptions --force --limit 20

# Clear existing content for regeneration
python3 update_existing_providers.py --clear --city "Yokohama" --limit 10
```

#### **Parameters for `update_existing_providers.py`**
| Parameter | Type | Description |
|-----------|------|-------------|
| `--descriptions` | flag | Update AI descriptions and excerpts |
| `--locations` | flag | Update latitude/longitude coordinates |
| `--clear` | flag | Clear existing descriptions for regeneration |
| `--all` | flag | Update everything (descriptions + locations) |
| `--city CITY` | string | Filter by specific city |
| `--limit NUMBER` | int | Limit number of providers to process |
| `--status STATUS` | string | Filter by status (pending, generated, published) |
| `--force` | flag | Force update even if content exists |
| `--batch-size NUMBER` | int | Batch size for AI generation (default: 5) |

### `populate_provider_locations.py`
```bash
# Add coordinates for providers missing location data
python3 populate_provider_locations.py
```

### `force_update_all.py` - Quick Updates
```bash
# Update all providers (50 limit)
python3 force_update_all.py

# Update specific city
python3 force_update_all.py "Yokohama"

# Update with custom limit
python3 force_update_all.py "Tokyo" 25
```

---

## 🗄️ Database Operations

### Migration Scripts
```bash
# WordPress sync infrastructure
python3 migrate_wordpress_sync_tables.py

# Business hours support
python3 migrate_business_hours.py

# Language proficiency scoring
python3 migrate_proficiency_score.py

# Accessibility features
python3 migrate_accessibility_parking.py

# Provider fingerprinting for deduplication
python3 migrate_add_fingerprints.py

# Fix Tokyo address formatting
python3 migrate_fix_tokyo_addresses.py
```

### Database Testing & Validation
```bash
# Test database connection
python3 tests/test_db_connection.py

# Test ACF data integrity
python3 tests/test_acf_data.py

# Test business hours formatting
python3 tests/test_business_hours.py

# Test WordPress sync functionality
python3 tests/test_wordpress_sync.py

# Test real Google Places API
python3 tests/test_real_places.py
```

### Direct Database Scripts
```bash
# Debug ACF field mapping
python3 debug_acf_fields.py

# PostgreSQL integration testing
python3 postgres_integration.py --validate-schema
```

---

## 🧪 Testing & Validation

### Mega-Batch Testing
```bash
# Test mega-batch processor
python3 test_mega_batch.py

# Test with custom providers
python3 test_mega_batch.py --limit 5
```

### Content Testing
```bash
# Test description generation
python3 claude_description_generator.py --test-mode

# Test review analysis
python3 claude_review_summarizer.py --dry-run

# Test English experience analysis
python3 claude_english_experience_summarizer.py --test
```

### WordPress Testing
```bash
# Test WordPress connection
python3 wordpress_sync_manager.py --test-connection

# Test ACF field mapping
python3 debug_acf_fields.py

# Validate sync operations
python3 tests/test_wordpress_sync.py
```

---

## 🛠️ Utility Scripts

### Cleanup & Maintenance
```bash
# Remove duplicate providers
python3 cleanup_duplicates.py

# Remove providers without photos
python3 cleanup_no_photos.py

# Clean WordPress media library (Google TOS compliance)
python3 cleanup_media_library.py
```

### Analytics & Research
```bash
# Keyword research automation
python3 keyword_research_automation.py

# Review keyword analysis
python3 review_keyword_analyzer.py

# Search tracking and analytics
python3 search_tracking.py

# Medical specialty frequency analysis
python3 medical_specialty_filter.py --analyze
```

### Provider Management
```bash
# Provider fingerprinting
python3 provider_fingerprinting.py

# Content hash service operations
python3 content_hash_service.py

# Sync management service
python3 sync_management_service.py
```

### Review Interface
```bash
# Launch Flask review dashboard
python3 review_app.py

# Access at: http://localhost:5000
```

---

## 📋 Quick Reference Tables

### Most Common Commands

#### Daily Operations
```bash
# Check system status
python3 run_mega_batch_automation.py --stats-only

# Process new content
python3 run_mega_batch_automation.py --limit 20 --dry-run

# Sync to WordPress
python3 wordpress_sync_manager.py --sync-all --limit 25
```

#### Weekly Maintenance
```bash
# Full data collection
python3 run_automation.py --daily-limit 75

# Complete content processing
python3 run_mega_batch_automation.py --all-providers

# WordPress status check
python3 wordpress_sync_manager.py --status
```

### Parameter Quick Reference

#### Core Automation (`run_automation.py`)
- `--daily-limit N` - Provider collection limit
- `--cities Tokyo Osaka` - Target specific cities
- `--skip-collection` - Skip data gathering
- `--skip-descriptions` - Skip AI content
- `--skip-publishing` - Skip WordPress

#### AI Content (`run_mega_batch_automation.py`)
- `--all-providers` - Process everything
- `--limit N` - Process N providers
- `--dry-run` - Preview only
- `--stats-only` - Status check

#### WordPress (`wordpress_sync_manager.py`)
- `--sync-all` - Sync all needing updates
- `--sync-city "Tokyo"` - City-specific sync
- `--sync-provider "Name"` - Individual sync
- `--dry-run` - Preview changes
- `--force` - Force update

### File Extensions & Data Types

#### Configuration Files
- `.env` - Environment variables
- `.json` - Data configuration (cities, specialties)
- `.md` - Documentation
- `.php` - WordPress ACF setup

#### Data Files
- `.pkl` - Cached search results
- `.html` - Template files
- `.py` - All scripts and modules

### Common Workflow Patterns

#### New Installation Setup
```bash
# 1. Install and configure
pip install -r requirements.txt
cp config/.env.example config/.env
# Edit .env with API keys

# 2. Run migrations
python3 migrate_wordpress_sync_tables.py
python3 migrate_business_hours.py
python3 migrate_proficiency_score.py

# 3. Test connections
python3 tests/test_db_connection.py
python3 wordpress_sync_manager.py --test-connection

# 4. Initial data collection
python3 run_automation.py --daily-limit 25
```

#### Production Content Update
```bash
# 1. Check current status
python3 run_mega_batch_automation.py --stats-only

# 2. Preview content generation
python3 run_mega_batch_automation.py --all-providers --dry-run

# 3. Generate content
python3 run_mega_batch_automation.py --all-providers

# 4. Sync to WordPress
python3 wordpress_sync_manager.py --sync-all --limit 50

# 5. Verify results
python3 wordpress_sync_manager.py --status
```

#### Troubleshooting Workflow
```bash
# 1. Test connections
python3 tests/test_db_connection.py
python3 wordpress_sync_manager.py --test-connection

# 2. Check provider status
python3 run_mega_batch_automation.py --stats-only
python3 wordpress_sync_manager.py --status

# 3. Test with small batch
python3 run_mega_batch_automation.py --limit 5 --dry-run

# 4. Check specific provider
python3 wordpress_sync_manager.py --check-provider "PROVIDER_NAME"
```

### Error Recovery Commands

#### Database Issues
```bash
# Validate schema
python3 postgres_integration.py --validate-schema

# Test basic operations
python3 tests/test_db_connection.py

# Reset provider status
# (Use SQL to reset wordpress_status to 'pending')
```

#### WordPress Issues
```bash
# Test connection
python3 wordpress_sync_manager.py --test-connection

# Check sync history
python3 wordpress_sync_manager.py --history

# Force sync specific provider
python3 wordpress_sync_manager.py --sync-provider "NAME" --force
```

#### Content Generation Issues
```bash
# Test with single provider
python3 run_mega_batch_automation.py --limit 1 --dry-run

# Check token limits in code
# Verify ANTHROPIC_API_KEY in .env

# Test individual scripts
python3 claude_description_generator.py --test-mode
```

---

## 📈 Performance & Monitoring

### System Health Checks
```bash
# Complete system status
python3 run_mega_batch_automation.py --stats-only

# WordPress sync health
python3 wordpress_sync_manager.py --status

# Database connectivity
python3 tests/test_db_connection.py

# API connectivity
python3 wordpress_sync_manager.py --test-connection
```

### Cost Estimation
```bash
# Preview mega-batch costs
python3 run_mega_batch_automation.py --all-providers --dry-run

# Check current API usage
# (Monitor via Claude API dashboard)

# Estimate sync operations
python3 wordpress_sync_manager.py --sync-all --dry-run
```

### Performance Monitoring
```bash
# Processing speed tracking
time python3 run_mega_batch_automation.py --limit 10

# WordPress sync performance
time python3 wordpress_sync_manager.py --sync-all --limit 10

# Database query performance
python3 postgres_integration.py --performance-test
```

---

**Last Updated**: July 2025  
**System Version**: v2.0 with Mega-Batch Processing  
**Total Commands**: 100+ comprehensive operations 