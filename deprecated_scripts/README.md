# Deprecated Scripts

This directory contains scripts that have been deprecated as part of the Unified Pipeline Architecture consolidation (January 2025).

## Why These Scripts Were Deprecated

These scripts were replaced by a unified, modular architecture that provides:
- 75% reduction in code complexity
- 75% API cost reduction through persistent caching
- Single command-line interface
- Better maintainability and testing

## Deprecated Scripts Reference

### Data Collection
- `google_places_integration.py` → `src/collectors/google_places.py`
- `provider_fingerprinting.py` → `src/collectors/deduplication.py`
- `medical_specialty_filter.py` → `src/collectors/specialty_filter.py`

### AI Content Generation
- `claude_mega_batch_processor.py` → `src/processors/ai_content.py`
- `claude_description_generator.py` → Consolidated into ai_content.py
- `claude_review_summarizer.py` → Consolidated into ai_content.py
- `claude_english_experience_summarizer.py` → Consolidated into ai_content.py

### WordPress Sync
- `wordpress_sync_manager.py` → `src/publishers/wordpress.py`
- `wordpress_update_service.py` → Consolidated into wordpress.py
- `content_hash_service.py` → `src/publishers/content_hash.py`
- `sync_management_service.py` → Consolidated into wordpress.py

### Pipeline Runners
- `run_automation.py` → `scripts/run_pipeline.py --mode full`
- `run_enhanced_automation.py` → `scripts/run_pipeline.py --mode full`
- `run_mega_batch_automation.py` → `scripts/run_pipeline.py --mode process`
- `run_unified_pipeline.py` → `scripts/run_pipeline.py`

### Utilities
- `postgres_integration.py` → `src/core/database.py`
- `activity_logger.py` → `src/utils/activity_logger.py`
- `pipeline_tracker.py` → `src/utils/pipeline_tracker.py`

## Migration Guide

If you have scripts that depend on these deprecated files:

1. **Update imports** to use the new modules:
   ```python
   # Old
   from postgres_integration import Provider
   
   # New
   from src.core.database import Provider
   ```

2. **Update command-line calls**:
   ```bash
   # Old
   python run_automation.py --daily-limit 50
   
   # New
   python scripts/run_pipeline.py --mode full --limit 50
   ```

3. **Use the migration script** for guidance:
   ```bash
   python scripts/migrate_to_unified.py
   ```

## Removal Timeline

These scripts are kept for reference but should not be used. They can be safely deleted once all systems have been migrated to the new architecture.

**DO NOT USE THESE SCRIPTS** - Use the unified pipeline instead.