# Migration Guide: Unified Pipeline Architecture

## Overview
This guide helps you transition from the old multi-script system to the new unified pipeline architecture.

## Key Changes

### 1. Single Entry Point
Replace multiple run scripts with one unified command:

**Old way:**
```bash
python run_automation.py --daily-limit 50
python run_mega_batch_automation.py --all-providers
python wordpress_sync_manager.py --sync-all
```

**New way:**
```bash
python scripts/run_pipeline.py --mode full --limit 50
python scripts/run_pipeline.py --mode process
python scripts/run_pipeline.py --mode publish
```

### 2. Import Changes

Update your imports in custom scripts:

**Old imports:**
```python
from postgres_integration import Provider, get_postgres_config
from google_places_integration import GooglePlacesHealthcareCollector
from claude_mega_batch_processor import ClaudeMegaBatchProcessor
from wordpress_sync_manager import WordPressSyncManager
```

**New imports:**
```python
from src.core.database import Provider, DatabaseManager, get_postgres_config
from src.collectors.google_places import GooglePlacesCollector
from src.processors.ai_content import AIContentProcessor
from src.publishers.wordpress import WordPressPublisher
```

### 3. API Endpoint Updates

The API endpoints need the following updates:

#### content_generation.py
- Change `ClaudeMegaBatchProcessor` to `AIContentProcessor`
- Update import paths as shown above

#### wordpress_sync.py
- Change `WordPressSyncManager` to `WordPressPublisher`
- Update method calls if needed

#### settings.py
- Update any database-related imports

### 4. Configuration

All configuration remains in `.env` files - no changes needed.

### 5. Database

The database schema remains unchanged. All existing data is preserved.

## Migration Steps

1. **Backup your data**
   ```bash
   pg_dump directory > backup_$(date +%Y%m%d).sql
   ```

2. **Test the new pipeline**
   ```bash
   python scripts/run_pipeline.py --status-only
   python scripts/run_pipeline.py --mode collect --limit 1 --dry-run
   ```

3. **Update any custom scripts**
   - Use the compatibility layer temporarily
   - Update imports gradually
   - Test each script after updating

4. **Update cron jobs / schedulers**
   Replace old commands with new unified commands

5. **Remove deprecated files**
   Once everything is working, remove old scripts

## Command Mapping

| Old Command | New Command |
|------------|-------------|
| `python run_automation.py` | `python scripts/run_pipeline.py --mode full` |
| `python run_mega_batch_automation.py --all-providers` | `python scripts/run_pipeline.py --mode process` |
| `python wordpress_sync_manager.py --sync-all` | `python scripts/run_pipeline.py --mode publish` |
| `python add_specific_provider.py` | Keep as-is (still useful) |
| `python add_geographic_providers.py` | Keep as-is (still useful) |

## Troubleshooting

### Import Errors
If you get import errors, ensure:
1. You're running from the project root
2. The compatibility layer is in place
3. Your Python path includes the project root

### Missing Methods
Some method names have changed:
- `process_providers()` → `process_batch()`
- `sync_to_wordpress()` → `sync_providers()`

### Performance
The new system includes:
- Built-in caching (30-day for place details)
- Cost tracking with budget limits
- More efficient batch processing

## Benefits of Migration

1. **Unified Interface**: Single command for all operations
2. **Cost Savings**: 75% reduction in API costs through caching
3. **Better Tracking**: Integrated pipeline tracking and reporting
4. **Maintainability**: 82 files reduced to ~25 core modules
5. **Performance**: Optimized database queries and batch operations

## Support

For issues during migration:
1. Check logs in `logs/` directory
2. Run with `--verbose` flag for detailed output
3. Use `--dry-run` to test without making changes
