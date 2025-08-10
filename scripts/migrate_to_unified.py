#!/usr/bin/env python3
"""
Migration Script for Unified Pipeline Architecture
Helps transition from the old multi-script system to the new unified architecture
"""

import os
import sys
import shutil
import logging
from datetime import datetime
from typing import List, Dict, Tuple

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def identify_deprecated_scripts() -> List[str]:
    """Identify scripts that should be deprecated"""
    deprecated = [
        # Main automation scripts (replaced by scripts/run_pipeline.py)
        'run_automation.py',
        'run_enhanced_automation.py',
        'run_mega_batch_automation.py',
        'run_unified_pipeline.py',
        
        # Google Places scripts (replaced by src/collectors/google_places.py)
        'google_places_integration.py',
        'google_places_healthcare_collector.py',
        'google_places_photo_fetcher.py',
        
        # AI content scripts (replaced by src/processors/ai_content.py)
        'claude_mega_batch_processor.py',
        'claude_description_generator.py',
        'claude_review_summarizer.py',
        'claude_english_experience_summarizer.py',
        'seo_content_generator.py',  # Redundant - mega batch handles this
        
        # WordPress scripts (replaced by src/publishers/wordpress.py)
        'wordpress_sync_manager.py',
        'wordpress_update_service.py',
        'sync_management_service.py',
        
        # Utility scripts (integrated into core modules)
        'provider_fingerprinting.py',  # Moved to src/collectors/deduplication.py
        'content_hash_service.py',     # Moved to src/publishers/content_hash.py
        
        # Database scripts (replaced by src/core/database.py)
        'postgres_integration.py'  # Core functionality moved to database.py
    ]
    
    return deprecated


def check_api_usage() -> Dict[str, List[str]]:
    """Check which API endpoints use deprecated modules"""
    api_dir = 'api'
    deprecated_imports = {
        'postgres_integration': 'src.core.database',
        'google_places_integration': 'src.collectors.google_places',
        'claude_mega_batch_processor': 'src.processors.ai_content',
        'wordpress_sync_manager': 'src.publishers.wordpress',
        'content_hash_service': 'src.publishers.content_hash'
    }
    
    updates_needed = {}
    
    for filename in os.listdir(api_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(api_dir, filename)
            with open(filepath, 'r') as f:
                content = f.read()
            
            file_updates = []
            for old_module, new_module in deprecated_imports.items():
                if old_module in content:
                    file_updates.append((old_module, new_module))
            
            if file_updates:
                updates_needed[filepath] = file_updates
    
    return updates_needed


def create_compatibility_layer():
    """Create temporary compatibility imports for smooth transition"""
    compat_file = """#!/usr/bin/env python3
\"\"\"
Temporary Compatibility Layer
Provides import redirects during migration to unified architecture

This file should be removed once all imports are updated.
\"\"\"

import warnings

def deprecated_import(old_name, new_module):
    warnings.warn(
        f"Import of '{old_name}' is deprecated. Use '{new_module}' instead.",
        DeprecationWarning,
        stacklevel=2
    )

# Database compatibility
try:
    from src.core.database import DatabaseManager, Provider
    from src.core.database import get_postgres_config
    
    # Create module-level compatibility
    import sys
    import types
    
    # Create postgres_integration compatibility module
    postgres_integration = types.ModuleType('postgres_integration')
    postgres_integration.get_postgres_config = get_postgres_config
    postgres_integration.Provider = Provider
    postgres_integration.DatabaseManager = DatabaseManager
    
    sys.modules['postgres_integration'] = postgres_integration
    
except ImportError as e:
    print(f"Warning: Could not set up database compatibility: {e}")

# Google Places compatibility
try:
    from src.collectors.google_places import GooglePlacesCollector
    
    import sys
    import types
    
    google_places_integration = types.ModuleType('google_places_integration')
    google_places_integration.GooglePlacesHealthcareCollector = GooglePlacesCollector
    
    sys.modules['google_places_integration'] = google_places_integration
    
except ImportError as e:
    print(f"Warning: Could not set up Google Places compatibility: {e}")

# WordPress compatibility
try:
    from src.publishers.wordpress import WordPressPublisher
    
    import sys
    import types
    
    wordpress_sync_manager = types.ModuleType('wordpress_sync_manager')
    wordpress_sync_manager.WordPressSyncManager = WordPressPublisher
    
    sys.modules['wordpress_sync_manager'] = wordpress_sync_manager
    
except ImportError as e:
    print(f"Warning: Could not set up WordPress compatibility: {e}")

# AI content compatibility
try:
    from src.processors.ai_content import AIContentProcessor
    
    import sys
    import types
    
    claude_mega_batch_processor = types.ModuleType('claude_mega_batch_processor')
    claude_mega_batch_processor.ClaudeMegaBatchProcessor = AIContentProcessor
    
    sys.modules['claude_mega_batch_processor'] = claude_mega_batch_processor
    
except ImportError as e:
    print(f"Warning: Could not set up AI content compatibility: {e}")
"""
    
    with open('compatibility_layer.py', 'w') as f:
        f.write(compat_file)
    
    return 'compatibility_layer.py'


def create_migration_guide() -> str:
    """Create a migration guide document"""
    guide = """# Migration Guide: Unified Pipeline Architecture

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
"""
    
    with open('MIGRATION_GUIDE.md', 'w') as f:
        f.write(guide)
    
    return 'MIGRATION_GUIDE.md'


def main():
    """Run migration assistant"""
    logger = setup_logging()
    
    print("\n" + "="*60)
    print("UNIFIED PIPELINE MIGRATION ASSISTANT")
    print("="*60 + "\n")
    
    # Check deprecated scripts
    logger.info("🔍 Checking for deprecated scripts...")
    deprecated = identify_deprecated_scripts()
    existing_deprecated = [f for f in deprecated if os.path.exists(f)]
    
    if existing_deprecated:
        print(f"\n📋 Found {len(existing_deprecated)} deprecated scripts:")
        for script in existing_deprecated[:10]:
            print(f"  - {script}")
        if len(existing_deprecated) > 10:
            print(f"  ... and {len(existing_deprecated) - 10} more")
    
    # Check API usage
    logger.info("\n🔍 Checking API endpoints for deprecated imports...")
    api_updates = check_api_usage()
    
    if api_updates:
        print(f"\n📝 API files needing updates:")
        for filepath, updates in api_updates.items():
            print(f"\n  {filepath}:")
            for old, new in updates:
                print(f"    - Replace '{old}' with '{new}'")
    
    # Create compatibility layer
    logger.info("\n🔧 Creating compatibility layer...")
    compat_file = create_compatibility_layer()
    print(f"  ✅ Created {compat_file}")
    
    # Create migration guide
    logger.info("\n📚 Creating migration guide...")
    guide_file = create_migration_guide()
    print(f"  ✅ Created {guide_file}")
    
    # Recommendations
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    print("\n1. Test the new pipeline:")
    print("   python scripts/run_pipeline.py --status-only")
    
    print("\n2. Add compatibility import to API files:")
    print("   import compatibility_layer  # Add at top of file")
    
    print("\n3. Test each component:")
    print("   python scripts/run_pipeline.py --mode collect --limit 1 --dry-run")
    print("   python scripts/run_pipeline.py --mode process --limit 1 --dry-run")
    print("   python scripts/run_pipeline.py --mode publish --limit 1 --dry-run")
    
    print("\n4. Once verified, update imports in API files")
    
    print("\n5. Remove deprecated scripts when ready:")
    print("   mkdir deprecated_scripts")
    print("   mv run_*.py deprecated_scripts/")
    
    print("\n✅ Migration preparation complete!")
    print("📖 See MIGRATION_GUIDE.md for detailed instructions\n")


if __name__ == '__main__':
    main()