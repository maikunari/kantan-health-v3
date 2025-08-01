#!/usr/bin/env python3
"""
Disabled Activity Logger - Emergency fallback
Use this to temporarily disable activity logging if it's causing issues
"""

from typing import Optional, Dict, Any, List

class ActivityLogger:
    """Disabled activity logger that does nothing"""
    
    def __init__(self):
        pass
    
    def log_activity(self, *args, **kwargs) -> bool:
        """Disabled - does nothing"""
        return True
    
    def log_provider_creation(self, *args, **kwargs):
        """Disabled - does nothing"""
        pass
    
    def log_content_generation(self, *args, **kwargs):
        """Disabled - does nothing"""
        pass
    
    def log_data_quality_update(self, *args, **kwargs):
        """Disabled - does nothing"""
        pass
    
    def log_wordpress_sync(self, *args, **kwargs):
        """Disabled - does nothing"""
        pass
    
    def log_duplicate_cleanup(self, *args, **kwargs):
        """Disabled - does nothing"""
        pass
    
    def get_recent_activities(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """Disabled - returns empty list"""
        return []
    
    def get_activity_summary(self, *args, **kwargs) -> Dict[str, Any]:
        """Disabled - returns empty dict"""
        return {}
    
    def close(self):
        """Disabled - does nothing"""
        pass

# Disabled singleton instance
activity_logger = ActivityLogger()