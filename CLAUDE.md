# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a healthcare directory automation system for international patients in Japan. It uses Google Places API, Claude AI, PostgreSQL, and WordPress to discover, process, and publish healthcare provider data with a focus on English-speaking support.

**Core Technologies:**
- Python 3.12+ (Homebrew) with Flask, SQLAlchemy, psycopg2, psutil
- React 18+ with TypeScript and Ant Design UI components
- PostgreSQL database for provider data
- WordPress REST API with ACF Pro for content management
- Google Places API for provider discovery
- Claude AI (Anthropic) for content generation

## Development Commands

### Web Application
```bash
# Start the Flask + React web interface
./start_app.sh

# Access the web interface at http://localhost:3000
# API server runs on http://localhost:5000
```

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

5. **Web Interface** (`frontend/` + `api/`)
   - React TypeScript frontend with Ant Design components
   - Flask REST API with Blueprint architecture
   - Real-time status monitoring and process tracking
   - Provider selection modal with filtering capabilities
   - Comprehensive settings management interface

### Data Flow

```
Google Places → PostgreSQL → AI Content Generation → WordPress Sync
      ↓              ↓                    ↓                ↓
  Deduplication   Provider Table    Mega-batch Process   ACF Fields
  Fingerprinting  Content Storage   4 Content Types     REST API
                     ↕                    ↕                ↕
              Web Interface ←→ Flask API ←→ Real-time Status
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

**Web Interface:**
- `api/content_generation.py` - Content generation API endpoints
- `api/wordpress_sync.py` - WordPress sync API with process tracking
- `api/settings.py` - Configuration management API
- `frontend/src/components/ContentGeneration/` - Content generation UI
- `frontend/src/components/Sync/` - WordPress sync UI with provider selection modal
- `frontend/src/components/Settings/` - Settings management interface

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

### Daily Operations (Web Interface)
```bash
# 1. Start the web application
./start_app.sh

# 2. Access web interface at http://localhost:3000
# - Use Content Generation page for AI content processing
# - Use WordPress Sync page with provider selection modal
# - Configure API keys in Settings page
```

### Daily Operations (Command Line)
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

## Current System State (Updated 2025-01-24)

### Recent Improvements Completed
- ✅ **SSL/urllib3 Compatibility Fixed**: Migrated to Homebrew Python 3.12 with virtual environment
- ✅ **Web Interface Implementation**: Full React + TypeScript frontend with Flask API backend
- ✅ **Settings Management**: Comprehensive configuration interface for all API keys with security features
- ✅ **Provider Selection Modal**: Advanced filtering and multi-select capabilities for WordPress sync
- ✅ **Process Tracking System**: Real-time monitoring of sync operations with psutil integration
- ✅ **Enhanced UI Components**: Removed redundant notifications, improved Recent Activity sections
- ✅ **WordPress Sync Fixes**: Fixed provider selection modal sync functionality with proper process tracking

### Current Web Interface Features

**Content Generation Page (`/content-generation`):**
- Real-time batch status monitoring with auto-refresh
- Comprehensive progress tracking with completion rates
- Enhanced Recent Activity section with verbose processing details
- Quick action buttons for common batch sizes
- Support for dry-run testing and content type selection

**WordPress Sync Page (`/sync`):**
- Provider selection modal with advanced filtering (status, city, content status, search)
- Multi-select capabilities with visual feedback
- Real-time sync status monitoring
- Batch operation tracking with process management
- Recent operations and error logging display

**Settings Page (`/settings`):**
- Secure API key management with masked display
- Real-time connection testing for WordPress, Google API, and Claude API
- Collapsible sections for organized configuration
- Password visibility toggles and validation feedback

### Technical Architecture

**Backend API Structure:**
- `api/content_generation.py` - Manages AI content generation with subprocess tracking
- `api/wordpress_sync.py` - Handles WordPress sync with process monitoring via psutil
- `api/settings.py` - Provides secure configuration management with connection testing
- Unified error handling and logging across all endpoints

**Frontend Component Structure:**
- `frontend/src/components/ContentGeneration/ContentGeneration.tsx` - Main content UI
- `frontend/src/components/Sync/WordPressSync.tsx` - Sync interface with provider modal
- `frontend/src/components/Settings/Settings.tsx` - Configuration management interface
- Real-time status polling and responsive design with Ant Design components

### Status Terminology System
The application uses standardized status terminology across all components:
- **IDLE**: No operations running
- **STARTING**: Process initialization phase
- **RUNNING**: Active processing in progress
- **COMPLETING**: Process finishing up
- **COMPLETED**: Operation finished successfully
- **ERROR**: Operation failed with error details

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
- Real-time status queries for web interface responsiveness

### Pending Improvements
- 🔄 **Status System Standardization**: Apply unified status terminology to content generation components
- 🔄 **Unified StatusIndicator Component**: Create reusable status display component
- 🔄 **Enhanced Error Handling**: Improve error display and recovery mechanisms

### Outstanding Issues

**WordPress Sync Workflow Gap:**
- ❗ **Critical Issue**: 25 providers with `description_generated` status have AI content but no WordPress posts
- **Root Cause**: Current sync system only updates existing WordPress posts (providers with `wordpress_post_id`)
- **Missing Step**: Initial WordPress post creation for new providers with generated content
- **Impact**: Providers get stuck in `description_generated` status instead of progressing to `published`

**Affected Providers (Sample):**
- ID 388: Tokyo Midtown Dental Clinic
- ID 394: Tokyo Midtown Clinic  
- ID 396: Caps Clinic Hikarigaoka
- ID 398: Bashamichi Sakura Clinic
- (21 more providers with similar status)

**Status Workflow Issues:**
- Providers transition: `pending` → `description_generated` → **STUCK**
- Expected flow: `pending` → `description_generated` → `published` (with WordPress post)
- Missing automation: Initial WordPress post creation step

### Troubleshooting Notes

**Common Issues:**
1. **Providers Stuck in `description_generated`**: Use `publish_approved.py` to create initial WordPress posts
2. **Sync Not Starting**: Ensure Flask server is running and check browser console for API errors
3. **Process Tracking Issues**: Verify psutil is installed (`pip install psutil`)
4. **SSL/Python Issues**: Use Homebrew Python 3.12 environment as documented
5. **Modal Not Loading Providers**: Check API endpoint connectivity and database access

**Debug Commands:**
```bash
# Check WordPress sync status and gaps
python3 -c "
from postgres_integration import get_postgres_config, Provider
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

config = get_postgres_config()
engine = create_engine(f'postgresql://{config[\"user\"]}:{config[\"password\"]}@{config[\"host\"]}:5432/{config[\"database\"]}')
Session = sessionmaker(bind=engine)
session = Session()

print('=== WordPress Sync Gap Analysis ===')
unsynced = session.execute(text('''
    SELECT COUNT(*) as count, status 
    FROM providers 
    WHERE ai_description IS NOT NULL AND wordpress_post_id IS NULL
    GROUP BY status
''')).fetchall()

for row in unsynced:
    print(f'{row[1]}: {row[0]} providers with content but no WordPress post')

session.close()
"

# Check Flask server status
curl http://localhost:5000/api/content/batch-status

# Verify process tracking
python3 -c "import psutil; print('psutil OK')"

# Test database connectivity
python3 utility/tests/test_db_connection.py

# Create WordPress posts for description_generated providers
python3 publish_approved.py
```

**Immediate Fixes Needed:**
1. **Update Status Workflow**: Modify content generation to set status to `approved` instead of `description_generated`
2. **Automated Post Creation**: Integrate `publish_approved.py` functionality into web interface
3. **Sync System Enhancement**: Add support for creating new WordPress posts, not just updating existing ones