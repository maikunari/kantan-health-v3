#!/usr/bin/env python3
"""
Temporary Compatibility Layer
Provides import redirects during migration to unified architecture

This file should be removed once all imports are updated.
"""

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
