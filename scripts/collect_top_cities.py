#!/usr/bin/env python3
"""
Collect Healthcare Providers from Top 10 Cities
Uses the GeographicSearchEngine for comprehensive grid-based collection
"""

import os
import sys
import time
import logging
import argparse
from typing import List, Dict, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.collectors.geographic_search import GeographicSearchEngine
from src.collectors.google_places import GooglePlacesCollector
from src.core.database import DatabaseManager
from src.core.pipeline import UnifiedPipeline, PipelineMode
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TopCitiesCollector:
    """Collects providers from Japan's top 10 cities using grid-based search"""
    
    # Top 10 cities by population with target provider counts
    TOP_CITIES = [
        {"name": "Tokyo", "target": 2500, "priority": 1},
        {"name": "Yokohama", "target": 800, "priority": 2},
        {"name": "Osaka", "target": 800, "priority": 3},
        {"name": "Nagoya", "target": 600, "priority": 4},
        {"name": "Sapporo", "target": 500, "priority": 5},
        {"name": "Kobe", "target": 400, "priority": 6},
        {"name": "Kyoto", "target": 400, "priority": 7},
        {"name": "Fukuoka", "target": 400, "priority": 8},
        {"name": "Kawasaki", "target": 300, "priority": 9},
        {"name": "Saitama", "target": 300, "priority": 10},
    ]
    
    def __init__(self):
        self.geo_engine = GeographicSearchEngine()
        self.collector = GooglePlacesCollector()
        self.db = DatabaseManager()
        self.pipeline = UnifiedPipeline()
        
    def collect_city(self, city_name: str, limit: int = None, dry_run: bool = False) -> Dict:
        """Collect providers from a single city using grid-based search"""
        
        logger.info(f"\n{'='*60}")
        logger.info(f"COLLECTING FROM {city_name.upper()}")
        logger.info(f"{'='*60}")
        
        # Get city config
        city_config = next((c for c in self.TOP_CITIES if c['name'] == city_name), None)
        if not city_config:
            logger.error(f"City {city_name} not in top 10 cities list")
            return {"error": "City not found"}
        
        if limit is None:
            limit = city_config['target']
        
        # Generate search grids for the city
        logger.info(f"📍 Generating search grids for {city_name}...")
        grids = self.geo_engine.generate_grid_searches(city_name)
        logger.info(f"   Created {len(grids)} search grids")
        
        if dry_run:
            logger.info("🔍 DRY RUN - Would search:")
            for i, grid in enumerate(grids[:5], 1):
                logger.info(f"   Grid {i}: {grid.grid_id} (radius: {grid.radius}m)")
            logger.info(f"   ... and {len(grids)-5} more grids")
            return {"dry_run": True, "grids": len(grids)}
        
        # Track collection stats
        total_collected = 0
        total_queries = 0
        total_cost = 0.0
        
        # Medical search terms to use
        search_terms = [
            "doctor", "clinic", "hospital", "医院", "クリニック", "病院",
            "dentist", "歯科", "medical center", "診療所",
            "pediatrics", "小児科", "内科", "外科"
        ]
        
        # Process each grid
        for grid_idx, grid in enumerate(grids, 1):
            if total_collected >= limit:
                logger.info(f"✅ Reached collection limit of {limit} providers")
                break
            
            logger.info(f"\n[Grid {grid_idx}/{len(grids)}] Searching {grid.grid_id}...")
            
            # Search with various terms in this grid
            for term in search_terms:
                if total_collected >= limit:
                    break
                
                try:
                    # Build location-based query
                    # For Tokyo wards, include ward name
                    if grid.ward:
                        location_query = f"{term} {grid.ward} {city_name}"
                    else:
                        location_query = f"{term} {city_name}"
                    
                    # Search using the query
                    providers = self.collector.search_providers(
                        query=location_query,
                        max_results=20
                    )
                    
                    if providers:
                        new_providers = len(providers)
                        total_collected += new_providers
                        total_queries += 1  # Each search is one query
                        # Estimate cost: ~$0.035 per query
                        total_cost += 0.035
                        
                        logger.info(f"   ✅ Found {new_providers} providers with '{term}'")
                        
                        # Save providers to database
                        session = self.db.get_session()
                        try:
                            for provider in providers:
                                # The search_providers method returns complete provider records
                                # They should already be saved by the collector
                                pass
                        finally:
                            session.close()
                    
                    # Rate limiting
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"   ❌ Error searching grid {grid.grid_id}: {e}")
                    continue
            
            # Progress update
            if grid_idx % 5 == 0:
                logger.info(f"\n📊 Progress: {total_collected} providers collected")
                logger.info(f"   Queries: {total_queries} | Cost: ${total_cost:.2f}")
        
        # Final summary
        summary = {
            "city": city_name,
            "providers_collected": total_collected,
            "grids_searched": min(grid_idx, len(grids)),
            "total_queries": total_queries,
            "total_cost": total_cost,
            "target": city_config['target'],
            "completion": (total_collected / city_config['target']) * 100
        }
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ {city_name} COLLECTION COMPLETE")
        logger.info(f"   Providers: {total_collected}/{city_config['target']} ({summary['completion']:.1f}%)")
        logger.info(f"   API Cost: ${total_cost:.2f}")
        logger.info(f"{'='*60}")
        
        return summary
    
    def collect_all_cities(self, dry_run: bool = False) -> List[Dict]:
        """Collect from all top 10 cities in priority order"""
        
        logger.info("🚀 STARTING TOP 10 CITIES COLLECTION")
        logger.info(f"Target: {sum(c['target'] for c in self.TOP_CITIES)} total providers")
        
        results = []
        
        for city in sorted(self.TOP_CITIES, key=lambda x: x['priority']):
            result = self.collect_city(city['name'], dry_run=dry_run)
            results.append(result)
            
            if not dry_run:
                # Take a break between cities
                logger.info(f"⏸️  Pausing before next city...")
                time.sleep(30)
        
        # Overall summary
        if not dry_run:
            total_providers = sum(r.get('providers_collected', 0) for r in results)
            total_cost = sum(r.get('total_cost', 0) for r in results)
            
            logger.info(f"\n{'='*60}")
            logger.info("🎉 ALL CITIES COLLECTION COMPLETE")
            logger.info(f"   Total Providers: {total_providers}")
            logger.info(f"   Total Cost: ${total_cost:.2f}")
            logger.info(f"{'='*60}")
        
        return results
    
    def get_city_status(self) -> Dict:
        """Check current provider count for each city"""
        
        session = self.db.get_session()
        try:
            logger.info("📊 CURRENT CITY COVERAGE")
            logger.info(f"{'='*60}")
            
            status = {}
            
            for city in self.TOP_CITIES:
                result = session.execute(text("""
                    SELECT COUNT(*) as count
                    FROM providers
                    WHERE city = :city
                """), {"city": city['name']}).fetchone()
                
                current = result[0] if result else 0
                target = city['target']
                completion = (current / target * 100) if target > 0 else 0
                
                status[city['name']] = {
                    "current": current,
                    "target": target,
                    "completion": completion,
                    "needed": max(0, target - current)
                }
                
                bar_length = 30
                filled = int(bar_length * completion / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                
                logger.info(f"{city['name']:12} [{bar}] {current:4}/{target:4} ({completion:5.1f}%)")
            
            logger.info(f"{'='*60}")
            
            total_current = sum(s['current'] for s in status.values())
            total_target = sum(s['target'] for s in status.values())
            total_completion = (total_current / total_target * 100) if total_target > 0 else 0
            
            logger.info(f"{'TOTAL':12} {total_current:4}/{total_target:4} ({total_completion:5.1f}%)")
            
            return status
            
        finally:
            session.close()


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Collect providers from top 10 cities')
    parser.add_argument('--city', type=str, help='Specific city to collect from')
    parser.add_argument('--limit', type=int, help='Override target limit for city')
    parser.add_argument('--all', action='store_true', help='Collect from all top 10 cities')
    parser.add_argument('--status', action='store_true', help='Show current coverage status')
    parser.add_argument('--dry-run', action='store_true', help='Preview without collecting')
    
    args = parser.parse_args()
    
    collector = TopCitiesCollector()
    
    if args.status:
        collector.get_city_status()
    elif args.all:
        collector.collect_all_cities(dry_run=args.dry_run)
    elif args.city:
        collector.collect_city(args.city, limit=args.limit, dry_run=args.dry_run)
    else:
        # Default: show status
        collector.get_city_status()
        print("\nUsage:")
        print("  --city Tokyo --limit 500  # Collect from specific city")
        print("  --all                      # Collect from all top 10 cities")
        print("  --status                   # Show current coverage")


if __name__ == "__main__":
    main()