#!/usr/bin/env python3
"""
Geographic Search Engine for Healthcare Provider Discovery
Implements grid-based searching, nearby search, and district-level targeting
"""

import math
import time
import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SearchGrid:
    """Represents a geographic search grid square"""
    center_lat: float
    center_lng: float
    radius: int  # meters
    grid_id: str
    city: str
    ward: Optional[str] = None
    
    def __hash__(self):
        return hash(self.grid_id)
    
    def __eq__(self, other):
        return self.grid_id == other.grid_id


class GeographicSearchEngine:
    """
    Advanced geographic search system for comprehensive provider discovery.
    Uses grid-based searching to ensure complete coverage of geographic areas.
    """
    
    # Major city coordinates for grid generation
    CITY_CENTERS = {
        "Tokyo": {"lat": 35.6762, "lng": 139.6503, "radius_km": 25},
        "Yokohama": {"lat": 35.4437, "lng": 139.6380, "radius_km": 20},
        "Osaka": {"lat": 34.6937, "lng": 135.5023, "radius_km": 15},
        "Nagoya": {"lat": 35.1815, "lng": 136.9066, "radius_km": 15},
        "Sapporo": {"lat": 43.0642, "lng": 141.3469, "radius_km": 15},
        "Kobe": {"lat": 34.6901, "lng": 135.1955, "radius_km": 12},
        "Kyoto": {"lat": 35.0116, "lng": 135.7681, "radius_km": 10},
        "Fukuoka": {"lat": 33.5904, "lng": 130.4017, "radius_km": 12},
        "Kawasaki": {"lat": 35.5309, "lng": 139.7031, "radius_km": 10},
        "Saitama": {"lat": 35.8617, "lng": 139.6455, "radius_km": 10},
        # Additional major cities
        "Sendai": {"lat": 38.2682, "lng": 140.8694, "radius_km": 10},
        "Hiroshima": {"lat": 34.3853, "lng": 132.4553, "radius_km": 10},
        "Niigata": {"lat": 37.9026, "lng": 139.0238, "radius_km": 10},
        "Hamamatsu": {"lat": 34.7108, "lng": 137.7261, "radius_km": 10},
        "Kumamoto": {"lat": 32.8032, "lng": 130.7079, "radius_km": 10},
        "Okayama": {"lat": 34.6555, "lng": 133.9195, "radius_km": 10},
        "Shizuoka": {"lat": 34.9756, "lng": 138.3827, "radius_km": 10},
        "Kagoshima": {"lat": 31.5966, "lng": 130.5571, "radius_km": 10},
    }
    
    # Ward/District center coordinates for Tokyo
    TOKYO_WARD_CENTERS = {
        "Shinjuku": {"lat": 35.6938, "lng": 139.7036},
        "Shibuya": {"lat": 35.6580, "lng": 139.7016},
        "Minato": {"lat": 35.6585, "lng": 139.7454},
        "Chiyoda": {"lat": 35.6940, "lng": 139.7535},
        "Chuo": {"lat": 35.6706, "lng": 139.7720},
        "Bunkyo": {"lat": 35.7172, "lng": 139.7520},
        "Taito": {"lat": 35.7127, "lng": 139.7800},
        "Sumida": {"lat": 35.7107, "lng": 139.8014},
        "Koto": {"lat": 35.6729, "lng": 139.8173},
        "Shinagawa": {"lat": 35.6092, "lng": 139.7302},
        "Meguro": {"lat": 35.6413, "lng": 139.6982},
        "Ota": {"lat": 35.5614, "lng": 139.7161},
        "Setagaya": {"lat": 35.6464, "lng": 139.6530},
        "Nakano": {"lat": 35.7078, "lng": 139.6637},
        "Suginami": {"lat": 35.6994, "lng": 139.6363},
        "Toshima": {"lat": 35.7323, "lng": 139.7150},
        "Kita": {"lat": 35.7528, "lng": 139.7337},
        "Arakawa": {"lat": 35.7361, "lng": 139.7833},
        "Itabashi": {"lat": 35.7512, "lng": 139.7095},
        "Nerima": {"lat": 35.7357, "lng": 139.6516},
        "Adachi": {"lat": 35.7753, "lng": 139.8048},
        "Katsushika": {"lat": 35.7434, "lng": 139.8473},
        "Edogawa": {"lat": 35.7068, "lng": 139.8683},
    }
    
    def __init__(self, grid_size_meters: int = 1000):
        """
        Initialize the geographic search engine.
        
        Args:
            grid_size_meters: Size of each grid square in meters (default 1km)
        """
        self.grid_size = grid_size_meters
        self.searched_grids: Set[str] = set()
        self.search_history: List[Dict] = []
        
        logger.info(f"✅ Geographic Search Engine initialized (grid size: {grid_size_meters}m)")
    
    def generate_grid_searches(self, city: str, specialties: List[str] = None) -> List[SearchGrid]:
        """
        Generate a grid of search points covering an entire city.
        
        Args:
            city: City name to generate grid for
            specialties: Medical specialties to search for
            
        Returns:
            List of SearchGrid objects covering the city
        """
        if city not in self.CITY_CENTERS:
            logger.warning(f"City {city} not in predefined centers")
            return []
        
        center = self.CITY_CENTERS[city]
        radius_km = center["radius_km"]
        
        grids = []
        
        # Calculate grid boundaries
        # 1 degree latitude ≈ 111 km
        # 1 degree longitude ≈ 111 km * cos(latitude)
        lat_step = self.grid_size / 111000  # Convert meters to degrees
        lng_step = self.grid_size / (111000 * math.cos(math.radians(center["lat"])))
        
        # Generate grid from southwest to northeast
        num_steps = int(radius_km * 1000 / self.grid_size)
        
        for lat_offset in range(-num_steps, num_steps + 1):
            for lng_offset in range(-num_steps, num_steps + 1):
                grid_lat = center["lat"] + (lat_offset * lat_step)
                grid_lng = center["lng"] + (lng_offset * lng_step)
                
                # Check if point is within radius
                distance = self._calculate_distance(
                    center["lat"], center["lng"],
                    grid_lat, grid_lng
                )
                
                if distance <= radius_km:
                    grid_id = f"{city}_{lat_offset+num_steps}_{lng_offset+num_steps}"
                    
                    # Determine which ward this grid belongs to (for Tokyo)
                    ward = None
                    if city == "Tokyo":
                        ward = self._find_nearest_ward(grid_lat, grid_lng)
                    
                    grid = SearchGrid(
                        center_lat=grid_lat,
                        center_lng=grid_lng,
                        radius=self.grid_size // 2,  # Search radius is half grid size
                        grid_id=grid_id,
                        city=city,
                        ward=ward
                    )
                    grids.append(grid)
        
        logger.info(f"📍 Generated {len(grids)} grid squares for {city} ({radius_km}km radius)")
        return grids
    
    def generate_nearby_searches(self, center_lat: float, center_lng: float, 
                                radius_meters: int = 2000, 
                                overlap_factor: float = 0.8) -> List[Dict]:
        """
        Generate overlapping nearby searches for comprehensive coverage.
        
        Args:
            center_lat: Center latitude
            center_lng: Center longitude
            radius_meters: Search radius in meters
            overlap_factor: Overlap between circles (0.8 = 20% overlap)
            
        Returns:
            List of search parameters for nearby search API
        """
        searches = []
        
        # Start with center point
        searches.append({
            "location": f"{center_lat},{center_lng}",
            "radius": radius_meters,
            "type": "doctor|hospital|clinic|dentist",
            "search_id": f"nearby_{center_lat:.4f}_{center_lng:.4f}_0"
        })
        
        # Add surrounding points in a hexagonal pattern for optimal coverage
        # Hexagonal packing is most efficient for circle coverage
        step_distance = radius_meters * 2 * overlap_factor
        angles = [0, 60, 120, 180, 240, 300]  # Hexagonal pattern
        
        for ring in range(1, 3):  # Two rings around center
            for angle in angles:
                # Calculate new point
                angle_rad = math.radians(angle)
                lat_offset = (step_distance * ring * math.sin(angle_rad)) / 111000
                lng_offset = (step_distance * ring * math.cos(angle_rad)) / (111000 * math.cos(math.radians(center_lat)))
                
                new_lat = center_lat + lat_offset
                new_lng = center_lng + lng_offset
                
                searches.append({
                    "location": f"{new_lat},{new_lng}",
                    "radius": radius_meters,
                    "type": "doctor|hospital|clinic|dentist",
                    "search_id": f"nearby_{new_lat:.4f}_{new_lng:.4f}_{ring}_{angle}"
                })
        
        logger.info(f"🎯 Generated {len(searches)} overlapping nearby searches")
        return searches
    
    def generate_district_searches(self, city: str, districts: List[str], 
                                  specialties: List[str] = None) -> List[Dict]:
        """
        Generate targeted searches for specific districts/wards.
        
        Args:
            city: City name
            districts: List of district/ward names
            specialties: Medical specialties to search
            
        Returns:
            List of search queries for district-level searches
        """
        if not specialties:
            specialties = ["doctor", "clinic", "hospital", "dentist"]
        
        searches = []
        
        for district in districts:
            # Get district center if available
            district_center = None
            if city == "Tokyo" and district in self.TOKYO_WARD_CENTERS:
                district_center = self.TOKYO_WARD_CENTERS[district]
            
            for specialty in specialties:
                # Text search queries
                search_queries = [
                    f"{specialty} {district} {city}",
                    f"English {specialty} {district}",
                    f"{specialty} near {district} station",
                ]
                
                for query in search_queries:
                    search = {
                        "query": query,
                        "type": "text_search",
                        "district": district,
                        "city": city,
                        "specialty": specialty
                    }
                    searches.append(search)
                
                # If we have coordinates, add nearby search
                if district_center:
                    searches.append({
                        "location": f"{district_center['lat']},{district_center['lng']}",
                        "radius": 2000,  # 2km radius for district
                        "type": "nearby_search",
                        "keyword": f"{specialty}",
                        "district": district,
                        "city": city,
                        "specialty": specialty
                    })
        
        logger.info(f"📍 Generated {len(searches)} district searches for {len(districts)} districts")
        return searches
    
    def _calculate_distance(self, lat1: float, lng1: float, 
                           lat2: float, lng2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _find_nearest_ward(self, lat: float, lng: float) -> Optional[str]:
        """
        Find the nearest Tokyo ward to a given coordinate.
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            Name of nearest ward or None
        """
        min_distance = float('inf')
        nearest_ward = None
        
        for ward, center in self.TOKYO_WARD_CENTERS.items():
            distance = self._calculate_distance(lat, lng, center["lat"], center["lng"])
            if distance < min_distance:
                min_distance = distance
                nearest_ward = ward
        
        return nearest_ward if min_distance < 5 else None  # Within 5km
    
    def track_search(self, search_params: Dict, results_count: int):
        """
        Track search execution for progress monitoring and deduplication.
        
        Args:
            search_params: Parameters used for the search
            results_count: Number of results found
        """
        search_record = {
            "timestamp": datetime.now().isoformat(),
            "params": search_params,
            "results": results_count
        }
        
        self.search_history.append(search_record)
        
        # Mark grid as searched if applicable
        if "grid_id" in search_params:
            self.searched_grids.add(search_params["grid_id"])
    
    def get_unsearched_grids(self, all_grids: List[SearchGrid]) -> List[SearchGrid]:
        """
        Filter out already searched grids.
        
        Args:
            all_grids: List of all possible grids
            
        Returns:
            List of grids that haven't been searched yet
        """
        return [grid for grid in all_grids if grid.grid_id not in self.searched_grids]
    
    def estimate_search_count(self, cities: List[str]) -> Dict[str, int]:
        """
        Estimate the number of searches needed for complete coverage.
        
        Args:
            cities: List of cities to cover
            
        Returns:
            Dictionary with search count estimates
        """
        estimates = {
            "grid_searches": 0,
            "district_searches": 0,
            "total_api_calls": 0,
            "estimated_cost": 0.0
        }
        
        for city in cities:
            if city in self.CITY_CENTERS:
                # Estimate grid searches
                radius_km = self.CITY_CENTERS[city]["radius_km"]
                area_km2 = math.pi * radius_km ** 2
                grid_area_km2 = (self.grid_size / 1000) ** 2
                num_grids = int(area_km2 / grid_area_km2)
                estimates["grid_searches"] += num_grids
        
        # Estimate API calls (with pagination, each search might be 1-3 calls)
        estimates["total_api_calls"] = estimates["grid_searches"] * 2  # Average 2 pages per search
        estimates["estimated_cost"] = estimates["total_api_calls"] * 0.032  # $0.032 per search
        
        return estimates
    
    def generate_collection_plan(self, cities: List[str], 
                                 specialties: List[str],
                                 use_grid: bool = True,
                                 use_districts: bool = True) -> Dict:
        """
        Generate a comprehensive collection plan for multiple cities.
        
        Args:
            cities: Cities to collect from
            specialties: Medical specialties to search
            use_grid: Whether to use grid-based searching
            use_districts: Whether to use district-based searching
            
        Returns:
            Complete collection plan with all search parameters
        """
        plan = {
            "cities": cities,
            "specialties": specialties,
            "grid_searches": [],
            "district_searches": [],
            "estimated_providers": 0,
            "estimated_cost": 0.0,
            "estimated_time_hours": 0.0
        }
        
        for city in cities:
            if use_grid and city in self.CITY_CENTERS:
                grids = self.generate_grid_searches(city, specialties)
                plan["grid_searches"].extend(grids)
            
            if use_districts:
                # Use predefined districts or generate based on city
                districts = self._get_city_districts(city)
                if districts:
                    district_searches = self.generate_district_searches(
                        city, districts, specialties
                    )
                    plan["district_searches"].extend(district_searches)
        
        # Calculate estimates
        total_searches = len(plan["grid_searches"]) + len(plan["district_searches"])
        plan["estimated_providers"] = total_searches * 15  # Average 15 providers per search
        plan["estimated_cost"] = total_searches * 0.05  # Include pagination costs
        plan["estimated_time_hours"] = total_searches * 3 / 3600  # 3 seconds per search with pagination
        
        logger.info(f"📋 Collection plan: {total_searches} searches, "
                   f"~{plan['estimated_providers']} providers, "
                   f"${plan['estimated_cost']:.2f} cost, "
                   f"{plan['estimated_time_hours']:.1f} hours")
        
        return plan
    
    def _get_city_districts(self, city: str) -> List[str]:
        """Get list of districts for a city."""
        if city == "Tokyo":
            return list(self.TOKYO_WARD_CENTERS.keys())
        
        # Add other cities' districts as needed
        city_districts = {
            "Osaka": ["Kita", "Chuo", "Naniwa", "Tennoji", "Namba"],
            "Yokohama": ["Naka", "Nishi", "Minami", "Tsurumi", "Kohoku"],
            # Add more as needed
        }
        
        return city_districts.get(city, [])