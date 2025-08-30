#!/usr/bin/env python3
"""
Unified Pipeline for Healthcare Provider Collection
Coordinates search, process, and publish phases
"""

import logging
from typing import List, Dict, Optional
from ..core.database import DatabaseManager
from ..collectors.google_places import GooglePlacesCollector
from ..processors.ai_content import AIContentProcessor
from ..publishers.wordpress import WordPressPublisher

logger = logging.getLogger(__name__)


class UnifiedPipeline:
    """Coordinates the complete provider collection pipeline"""
    
    def __init__(self):
        """Initialize pipeline components"""
        self.db = DatabaseManager()
        self.collector = GooglePlacesCollector()
        self.ai_processor = AIContentProcessor()
        self.publisher = WordPressPublisher()
        
        logger.info("✅ Unified Pipeline initialized")
    
    def run_search_phase(self, queries: List[str], limit_per_query: int = 10) -> List[Dict]:
        """Execute search phase
        
        Args:
            queries: List of search queries
            limit_per_query: Max results per query
            
        Returns:
            List of provider records
        """
        all_providers = []
        
        for query in queries:
            try:
                results = self.collector.search_providers(query, limit=limit_per_query)
                
                for result in results:
                    provider_record = self.collector.create_provider_record(result)
                    if provider_record:
                        all_providers.append(provider_record)
                        
            except Exception as e:
                logger.error(f"Search failed for '{query}': {str(e)}")
        
        return all_providers
    
    def run_process_phase(self, providers: List[Dict]) -> int:
        """Execute content processing phase
        
        Args:
            providers: List of provider records
            
        Returns:
            Number of providers processed
        """
        processed = 0
        
        for provider in providers:
            try:
                # Save to database
                saved = self.db.create_or_update_provider(provider)
                
                if saved:
                    # Generate AI content
                    content = self.ai_processor.generate_provider_content(saved)
                    
                    if content:
                        self.db.update_provider_content(saved.id, content)
                        processed += 1
                        
            except Exception as e:
                logger.error(f"Processing failed for provider: {str(e)}")
        
        return processed
    
    def run_publish_phase(self, limit: int = 10) -> int:
        """Execute WordPress publish phase
        
        Args:
            limit: Maximum providers to publish
            
        Returns:
            Number of providers published
        """
        # Get providers ready for WordPress
        providers = self.db.get_providers_needing_wordpress(limit=limit)
        
        if not providers:
            return 0
        
        # Sync to WordPress
        result = self.publisher.sync_providers(providers)
        
        return result.get('synced', 0)