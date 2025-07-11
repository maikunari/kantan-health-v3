# PRD: WordPress Sync Enhancement - Bidirectional Content Management

## Document Info
- **Version**: 1.1
- **Date**: 2024-07-09 (Updated: 2024-12-19)
- **Author**: System Architecture Team
- **Status**: Approved

## 🆕 Architecture Update: ACF Fields Only (v1.1)

### Enhancement Summary
**Date**: December 19, 2024  
**Impact**: Major architectural simplification

The system has been updated to use **ACF fields exclusively** for all provider data display, eliminating WordPress post content duplication.

### Changes Made
- **WordPress Post Content**: Now minimal placeholder text only
- **Data Display**: 100% via ACF fields (35+ mapped fields)
- **Sync Payload**: Reduced size due to eliminated HTML content duplication
- **Performance**: Faster sync operations with streamlined data flow
- **Maintainability**: Single source of truth for provider data

### Technical Implementation
```python
# Before: Dual content approach
update_data = {
    'content': self._generate_post_content(provider),  # Full HTML content
    'acf': self._generate_acf_fields(provider)         # Duplicate data
}

# After: ACF-only approach  
update_data = {
    'content': self._generate_minimal_post_content(provider),  # Minimal placeholder
    'acf': self._generate_acf_fields(provider)                 # Primary data source
}
```

### Benefits Achieved
- **Eliminated Redundancy**: No more duplicate data in post content and ACF fields
- **Faster Sync**: Reduced payload size improves WordPress API performance
- **Theme Flexibility**: Complete control over data presentation via ACF fields
- **Single Source**: All provider data managed through structured ACF fields

---

## Executive Summary

The current healthcare directory system has a critical gap: it can create new WordPress posts from database content but cannot update existing posts when database descriptions are enhanced. This PRD outlines the implementation of a production-ready bidirectional sync system that maintains content consistency between PostgreSQL and WordPress.

## Problem Statement

### Current Issues
1. **One-way Publishing**: System only creates new WordPress posts (`wordpress_post_id.is_(None)`)
2. **Content Drift**: Database descriptions get updated but WordPress remains stale
3. **No Update Mechanism**: No way to sync improved descriptions to existing WordPress posts
4. **Manual Intervention Required**: Requires resetting WordPress IDs to force re-publishing

### Business Impact
- **User Experience**: Visitors see outdated, lower-quality descriptions
- **SEO Impact**: Stale content reduces search visibility
- **Operational Overhead**: Manual sync processes are error-prone and time-consuming
- **Data Integrity**: Inconsistent content across systems

## Requirements

### Functional Requirements

#### FR-1: WordPress Post Update
- **Description**: Update existing WordPress posts with current database descriptions
- **Acceptance Criteria**: 
  - System can identify posts that need updating
  - Updates preserve WordPress metadata (publish date, categories, etc.)
  - Supports both individual and bulk updates
  - Handles WordPress API rate limits gracefully

#### FR-2: Content Comparison
- **Description**: Compare database vs WordPress content to detect changes
- **Acceptance Criteria**:
  - Detect when database descriptions are newer than WordPress
  - Compare both description content and metadata
  - Track last sync timestamps
  - Identify content differences for logging

#### FR-3: Selective Sync Operations
- **Description**: Support targeted sync operations for specific providers
- **Acceptance Criteria**:
  - Update single provider by name/ID
  - Update providers by city/specialty
  - Update providers by status or date range
  - Dry-run mode for previewing changes

#### FR-4: Sync Status Tracking
- **Description**: Track sync status and history for audit purposes
- **Acceptance Criteria**:
  - Log all sync operations with timestamps
  - Track success/failure rates
  - Store sync metadata in database
  - Provide sync status reporting

### Non-Functional Requirements

#### NFR-1: Performance
- **Bulk Operations**: Handle 100+ providers efficiently
- **Rate Limiting**: Respect WordPress API limits (avoid 429 errors)
- **Timeout Handling**: Graceful degradation for slow responses
- **Memory Usage**: Process large batches without memory issues

#### NFR-2: Reliability
- **Error Handling**: Comprehensive error recovery mechanisms
- **Transaction Safety**: Atomic operations where possible
- **Rollback Capability**: Ability to revert changes if needed
- **Monitoring**: Detailed logging and alerting

#### NFR-3: Security
- **Authentication**: Secure WordPress API authentication
- **Authorization**: Role-based access to sync operations
- **Data Validation**: Sanitize content before WordPress publishing
- **Audit Trail**: Complete history of all sync operations

## Technical Architecture

### Database Schema Enhancements

#### New Table: `wordpress_sync_log`
```sql
CREATE TABLE wordpress_sync_log (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES providers(id),
    wordpress_post_id INTEGER,
    sync_type VARCHAR(50), -- 'create', 'update', 'delete'
    sync_status VARCHAR(20), -- 'success', 'failed', 'pending'
    content_hash VARCHAR(64), -- SHA256 of synced content
    sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    sync_duration_ms INTEGER
);
```

#### Provider Table Enhancements
```sql
ALTER TABLE providers ADD COLUMN last_wordpress_sync TIMESTAMP;
ALTER TABLE providers ADD COLUMN content_hash VARCHAR(64);
```

### API Design

#### 1. WordPress Update Service
```python
class WordPressUpdateService:
    def update_existing_post(self, provider_id: int, force: bool = False)
    def bulk_update_posts(self, filter_criteria: dict, batch_size: int = 10)
    def compare_content(self, provider_id: int) -> ContentComparison
    def sync_provider(self, provider_id: int, dry_run: bool = False)
```

#### 2. Content Comparison Service
```python
class ContentComparisonService:
    def generate_content_hash(self, content: str) -> str
    def needs_update(self, provider_id: int) -> bool
    def get_content_diff(self, provider_id: int) -> ContentDiff
```

#### 3. Sync Management Service
```python
class SyncManagementService:
    def plan_sync_operation(self, criteria: dict) -> SyncPlan
    def execute_sync_plan(self, plan: SyncPlan) -> SyncResult
    def get_sync_status(self, operation_id: str) -> SyncStatus
```

## Implementation Steps

### Phase 1: Foundation 

#### Step 1.1: Database Schema Updates
```sql
-- Create sync logging table
CREATE TABLE wordpress_sync_log (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES providers(id),
    wordpress_post_id INTEGER,
    sync_type VARCHAR(50),
    sync_status VARCHAR(20),
    content_hash VARCHAR(64),
    sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    sync_duration_ms INTEGER,
    metadata JSONB
);

-- Add tracking columns to providers
ALTER TABLE providers ADD COLUMN last_wordpress_sync TIMESTAMP;
ALTER TABLE providers ADD COLUMN content_hash VARCHAR(64);
ALTER TABLE providers ADD COLUMN wordpress_status VARCHAR(20) DEFAULT 'pending';

-- Create indexes for performance
CREATE INDEX idx_sync_log_provider ON wordpress_sync_log(provider_id);
CREATE INDEX idx_sync_log_timestamp ON wordpress_sync_log(sync_timestamp);
CREATE INDEX idx_providers_sync_status ON providers(wordpress_status);
```

#### Step 1.2: Content Hashing System
```python
# File: content_hash_service.py
import hashlib
import json
from typing import Dict, Any

class ContentHashService:
    """Service for generating and comparing content hashes"""
    
    def generate_provider_hash(self, provider: Provider) -> str:
        """Generate SHA256 hash of provider content for change detection"""
        content_data = {
            'ai_description': provider.ai_description or '',
            'ai_excerpt': provider.ai_excerpt or '',
            'provider_name': provider.provider_name,
            'specialties': provider.specialties,
            'city': provider.city,
            'english_proficiency': provider.english_proficiency,
            'rating': provider.rating,
            'total_reviews': provider.total_reviews
        }
        
        # Sort keys for consistent hashing
        content_json = json.dumps(content_data, sort_keys=True)
        return hashlib.sha256(content_json.encode()).hexdigest()
    
    def content_changed(self, provider: Provider) -> bool:
        """Check if provider content has changed since last sync"""
        current_hash = self.generate_provider_hash(provider)
        return current_hash != provider.content_hash
```

### Phase 2: WordPress Update Service 

#### Step 2.1: WordPress Post Update Service
```python
# File: wordpress_update_service.py
import requests
import time
from typing import Optional, Dict, List
from datetime import datetime
import logging

class WordPressUpdateService:
    """Service for updating existing WordPress posts"""
    
    def __init__(self, wp_base_url: str, wp_username: str, wp_password: str):
        self.wp_base_url = wp_base_url
        self.auth = (wp_username, wp_password)
        self.session = requests.Session()
        self.session.auth = self.auth
        
    def update_existing_post(self, provider: Provider, dry_run: bool = False) -> Dict:
        """Update a single WordPress post with current database content"""
        
        if not provider.wordpress_post_id:
            raise ValueError(f"Provider {provider.provider_name} has no WordPress post ID")
        
        # Generate ACF fields - primary data source (ACF-only approach)
        acf_fields = self._generate_acf_fields(provider)
        
        # Prepare update payload - ACF fields only approach
        update_data = {
            'content': self._generate_minimal_post_content(provider),  # Minimal placeholder
            'title': provider.provider_name,
            'excerpt': provider.ai_excerpt or '',
            'acf': acf_fields,  # Primary data source
            'meta': {
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_display_method': 'acf_fields_only'
            }
        }
        
        if dry_run:
            return {
                'status': 'dry_run',
                'post_id': provider.wordpress_post_id,
                'changes': update_data
            }
        
        # Execute WordPress update
        try:
            start_time = time.time()
            
            response = self.session.post(
                f"{self.wp_base_url}/wp-json/wp/v2/posts/{provider.wordpress_post_id}",
                json=update_data,
                timeout=30
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                # Update local tracking
                provider.last_wordpress_sync = datetime.now()
                provider.content_hash = ContentHashService().generate_provider_hash(provider)
                provider.wordpress_status = 'synced'
                
                # Log success
                self._log_sync_operation(
                    provider.id,
                    provider.wordpress_post_id,
                    'update',
                    'success',
                    duration_ms
                )
                
                return {
                    'status': 'success',
                    'post_id': provider.wordpress_post_id,
                    'duration_ms': duration_ms
                }
            else:
                error_msg = f"WordPress API error: {response.status_code} - {response.text}"
                self._log_sync_operation(
                    provider.id,
                    provider.wordpress_post_id,
                    'update',
                    'failed',
                    duration_ms,
                    error_msg
                )
                
                return {
                    'status': 'failed',
                    'error': error_msg,
                    'post_id': provider.wordpress_post_id
                }
                
        except Exception as e:
            self._log_sync_operation(
                provider.id,
                provider.wordpress_post_id,
                'update',
                'failed',
                0,
                str(e)
            )
            
            return {
                'status': 'failed',
                'error': str(e),
                'post_id': provider.wordpress_post_id
            }
    
    def bulk_update_posts(self, providers: List[Provider], batch_size: int = 10) -> Dict:
        """Update multiple WordPress posts in batches"""
        results = {
            'total': len(providers),
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        for i in range(0, len(providers), batch_size):
            batch = providers[i:i + batch_size]
            
            logging.info(f"Processing batch {i//batch_size + 1} ({len(batch)} providers)")
            
            for provider in batch:
                result = self.update_existing_post(provider)
                results['details'].append(result)
                
                if result['status'] == 'success':
                    results['success'] += 1
                elif result['status'] == 'failed':
                    results['failed'] += 1
                else:
                    results['skipped'] += 1
            
            # Rate limiting between batches
            if i + batch_size < len(providers):
                time.sleep(2)  # 2 second delay between batches
        
        return results
```

### Phase 3: Command Line Interface 

#### Step 3.1: Enhanced Update Script
```python
# File: wordpress_sync_manager.py
import argparse
import sys
from typing import List, Optional
from wordpress_update_service import WordPressUpdateService
from content_hash_service import ContentHashService

class WordPressSyncManager:
    """Command-line interface for WordPress sync operations"""
    
    def __init__(self):
        self.db = GooglePlacesHealthcareCollector()
        self.wp_service = WordPressUpdateService(
            wp_base_url=os.getenv('WORDPRESS_BASE_URL'),
            wp_username=os.getenv('WORDPRESS_USERNAME'),
            wp_password=os.getenv('WORDPRESS_PASSWORD')
        )
        
    def sync_provider_by_name(self, provider_name: str, dry_run: bool = False):
        """Sync specific provider by name"""
        session = self.db.Session()
        
        provider = session.query(Provider).filter(
            Provider.provider_name.ilike(f'%{provider_name}%')
        ).first()
        
        if not provider:
            print(f"❌ Provider '{provider_name}' not found")
            return
        
        if not provider.wordpress_post_id:
            print(f"❌ Provider '{provider_name}' has no WordPress post ID")
            return
        
        print(f"🔄 Syncing {provider.provider_name} (WordPress ID: {provider.wordpress_post_id})")
        
        result = self.wp_service.update_existing_post(provider, dry_run=dry_run)
        
        if result['status'] == 'success':
            print(f"✅ Successfully synced {provider.provider_name} in {result['duration_ms']}ms")
        elif result['status'] == 'dry_run':
            print(f"🧪 DRY RUN: Would update {provider.provider_name}")
            print(f"   Changes: {result['changes'].keys()}")
        else:
            print(f"❌ Failed to sync {provider.provider_name}: {result['error']}")
        
        session.close()
    
    def sync_providers_needing_update(self, limit: int = 50, dry_run: bool = False):
        """Sync all providers that need updating"""
        session = self.db.Session()
        
        # Find providers with WordPress posts that need updating
        providers = session.query(Provider).filter(
            Provider.wordpress_post_id.isnot(None),
            Provider.ai_description.isnot(None)
        ).limit(limit).all()
        
        # Filter to only those that need updating
        hash_service = ContentHashService()
        providers_to_update = []
        
        for provider in providers:
            if hash_service.content_changed(provider):
                providers_to_update.append(provider)
        
        if not providers_to_update:
            print("✅ All WordPress posts are up to date")
            return
        
        print(f"🔄 Found {len(providers_to_update)} providers needing WordPress updates")
        
        if dry_run:
            print("🧪 DRY RUN MODE - No changes will be made")
            for provider in providers_to_update:
                print(f"   - {provider.provider_name} (WordPress ID: {provider.wordpress_post_id})")
            return
        
        # Execute bulk update
        results = self.wp_service.bulk_update_posts(providers_to_update)
        
        print(f"\n📊 SYNC RESULTS:")
        print(f"   ✅ Success: {results['success']}")
        print(f"   ❌ Failed: {results['failed']}")
        print(f"   ⏭️ Skipped: {results['skipped']}")
        print(f"   📈 Success Rate: {(results['success']/results['total']*100):.1f}%")
        
        session.close()

def main():
    parser = argparse.ArgumentParser(description="WordPress Sync Manager")
    
    # Sync operations
    parser.add_argument("--sync-provider", type=str, help="Sync specific provider by name")
    parser.add_argument("--sync-all", action='store_true', help="Sync all providers needing updates")
    parser.add_argument("--sync-city", type=str, help="Sync providers in specific city")
    
    # Options
    parser.add_argument("--dry-run", action='store_true', help="Show what would be updated without making changes")
    parser.add_argument("--limit", type=int, default=50, help="Limit number of providers to process")
    parser.add_argument("--force", action='store_true', help="Force update even if content appears unchanged")
    
    # Status operations
    parser.add_argument("--status", action='store_true', help="Show sync status for all providers")
    parser.add_argument("--check-provider", type=str, help="Check sync status for specific provider")
    
    args = parser.parse_args()
    
    if not any([args.sync_provider, args.sync_all, args.sync_city, args.status, args.check_provider]):
        print("❌ Please specify an operation. Use --help for options.")
        sys.exit(1)
    
    manager = WordPressSyncManager()
    
    if args.sync_provider:
        manager.sync_provider_by_name(args.sync_provider, dry_run=args.dry_run)
    elif args.sync_all:
        manager.sync_providers_needing_update(limit=args.limit, dry_run=args.dry_run)
    elif args.sync_city:
        manager.sync_providers_by_city(args.sync_city, dry_run=args.dry_run)
    elif args.status:
        manager.show_sync_status()
    elif args.check_provider:
        manager.check_provider_status(args.check_provider)

if __name__ == "__main__":
    main()
```

### Phase 4: Testing Strategy

#### Unit Tests
```python
# File: test_wordpress_sync.py
import pytest
from unittest.mock import Mock, patch
from wordpress_update_service import WordPressUpdateService
from content_hash_service import ContentHashService

class TestWordPressUpdateService:
    
    def test_update_existing_post_success(self):
        """Test successful post update"""
        # Test implementation
        pass
    
    def test_update_existing_post_api_error(self):
        """Test handling of WordPress API errors"""
        # Test implementation
        pass
    
    def test_bulk_update_with_rate_limiting(self):
        """Test bulk updates respect rate limits"""
        # Test implementation
        pass

class TestContentHashService:
    
    def test_generate_provider_hash(self):
        """Test content hash generation"""
        # Test implementation
        pass
    
    def test_content_changed_detection(self):
        """Test change detection"""
        # Test implementation
        pass
```

#### Integration Tests
```python
# File: test_wordpress_integration.py
import pytest
from wordpress_sync_manager import WordPressSyncManager

class TestWordPressSyncIntegration:
    
    @pytest.fixture
    def sync_manager(self):
        return WordPressSyncManager()
    
    def test_full_sync_workflow(self, sync_manager):
        """Test complete sync workflow"""
        # Test implementation
        pass
```

### Phase 5: Production Deployment

#### Step 5.1: Environment Configuration
```bash
# Environment variables for production
WORDPRESS_BASE_URL=https://your-site.com
WORDPRESS_USERNAME=api_user
WORDPRESS_PASSWORD=app_password
WORDPRESS_SYNC_BATCH_SIZE=10
WORDPRESS_SYNC_DELAY=2
```

#### Step 5.2: Usage Examples
```bash
# Sync specific provider
python3 wordpress_sync_manager.py --sync-provider "DENTAL OFFICE OTANI" --dry-run

# Sync all providers needing updates
python3 wordpress_sync_manager.py --sync-all --limit 20

# Check what needs updating without making changes
python3 wordpress_sync_manager.py --sync-all --dry-run

# Force sync all providers in a city
python3 wordpress_sync_manager.py --sync-city "Osaka" --force

# Show sync status
python3 wordpress_sync_manager.py --status
```

## Risk Assessment

### Technical Risks

#### High Risk
- **WordPress API Rate Limits**: Could cause sync failures
  - **Mitigation**: Implement exponential backoff and batch processing
- **Content Corruption**: Malformed updates could break WordPress posts
  - **Mitigation**: Content validation and rollback mechanisms

#### Medium Risk
- **Database Consistency**: Sync failures could leave inconsistent state
  - **Mitigation**: Transaction management and sync logging
- **Performance Impact**: Large sync operations could slow system
  - **Mitigation**: Background processing and progress monitoring

#### Low Risk
- **Authentication Issues**: WordPress credentials could expire
  - **Mitigation**: Credential validation and monitoring

### Operational Risks

#### High Risk
- **Data Loss**: Incorrect updates could overwrite content
  - **Mitigation**: Backup before sync operations
- **Downtime**: Sync failures could affect WordPress availability
  - **Mitigation**: Graceful error handling and monitoring

## Success Metrics

### Performance Metrics
- **Sync Success Rate**: > 95% successful updates
- **Sync Speed**: < 5 seconds per provider update
- **Error Recovery**: < 1% unrecoverable errors

### Quality Metrics
- **Content Consistency**: 100% database-WordPress content match
- **User Experience**: Updated descriptions visible within 24 hours
- **System Reliability**: 99.9% uptime during sync operations

## Maintenance Plan

### Daily Operations
- Monitor sync logs for errors
- Check content consistency reports
- Validate WordPress API connectivity

### Weekly Operations
- Review sync performance metrics
- Update content hashes for changed providers
- Audit sync operation logs

### Monthly Operations
- Full system sync validation
- Performance optimization review
- Security credential rotation

## Conclusion

This PRD provides a comprehensive plan for implementing production-ready WordPress sync functionality. The phased approach ensures systematic development while maintaining system stability. The solution addresses the core problem of content drift between database and WordPress while providing robust error handling and monitoring capabilities.

The implementation will enable:
- Seamless updates of existing WordPress posts
- Automated detection of content changes
- Comprehensive sync status tracking
- Production-ready error handling and logging

This foundation will support the ongoing operation of the healthcare directory system with consistent, up-to-date content across all platforms. 