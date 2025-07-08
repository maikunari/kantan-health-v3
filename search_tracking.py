#!/usr/bin/env python3
"""
Search Query Tracking System
Tracks what searches have been performed to prevent duplicate Google Places API calls
and optimize data collection efficiency.

Features:
1. Query fingerprinting to identify similar searches
2. Geographic coverage tracking
3. Specialty/keyword search history
4. Time-based search expiration (searches older than X days can be repeated)
5. Search performance analytics

Usage:
    tracker = SearchTracker()
    
    # Check if search already performed
    if not tracker.should_perform_search(city="Tokyo", specialty="cardiology"):
        print("Search already performed recently")
    else:
        # Perform search and record it
        results = perform_google_search()
        tracker.record_search(city="Tokyo", specialty="cardiology", results_count=len(results))
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, text
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

@dataclass
class SearchQuery:
    """Container for search query information"""
    city: str
    specialty: str
    search_type: str  # "nearby", "text_search", etc.
    radius: Optional[int] = None
    keywords: Optional[List[str]] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)

class SearchHistory(Base):
    """Database model for tracking search history"""
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True)
    query_fingerprint = Column(String(32), nullable=False, index=True)
    city = Column(String(100), nullable=False, index=True) 
    specialty = Column(String(100), nullable=False)
    search_type = Column(String(50), nullable=False)
    radius = Column(Integer)
    keywords = Column(JSON)
    
    # Search results and performance
    results_count = Column(Integer, default=0)
    new_providers_found = Column(Integer, default=0)
    duplicates_found = Column(Integer, default=0)
    api_calls_used = Column(Integer, default=1)
    
    # Timing information
    search_date = Column(DateTime, default=datetime.utcnow)
    execution_time_seconds = Column(Integer)
    
    # Geographic coverage
    coverage_area = Column(JSON)  # Store bounding box or coverage info
    
    def __repr__(self):
        return f"<SearchHistory(city='{self.city}', specialty='{self.specialty}', date='{self.search_date}')>"

class SearchTracker:
    """Manages search query tracking and deduplication"""
    
    def __init__(self, expiry_days: int = 7):
        """Initialize search tracker
        
        Args:
            expiry_days: Number of days after which searches can be repeated
        """
        self.expiry_days = expiry_days
        self.setup_database()
        
        # Define search similarity thresholds
        self.city_aliases = {
            # Tokyo variants
            'tokyo': ['tokyo', '東京', 'tokyo-to', 'tokyo city'],
            'yokohama': ['yokohama', '横浜', 'yokohama-shi', 'yokohama city'],
            'osaka': ['osaka', '大阪', 'osaka-shi', 'osaka city'],
            'nagoya': ['nagoya', '名古屋', 'nagoya-shi', 'nagoya city'],
            'kyoto': ['kyoto', '京都', 'kyoto-shi', 'kyoto city'],
            'fukuoka': ['fukuoka', '福岡', 'fukuoka-shi', 'fukuoka city'],
        }
        
        self.specialty_aliases = {
            'cardiology': ['cardiology', 'cardiologist', 'heart doctor', '循環器科'],
            'dermatology': ['dermatology', 'dermatologist', 'skin doctor', '皮膚科'],
            'general_medicine': ['general medicine', 'general practitioner', 'family doctor', '内科'],
            'pediatrics': ['pediatrics', 'pediatrician', 'children doctor', '小児科'],
            'gynecology': ['gynecology', 'gynecologist', 'women health', '婦人科'],
            'orthopedics': ['orthopedics', 'orthopedic surgeon', 'bone doctor', '整形外科'],
        }
    
    def setup_database(self):
        """Setup database connection and create tables"""
        load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))
        
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_password = os.getenv("POSTGRES_PASSWORD", "password")
        db_host = os.getenv("POSTGRES_HOST", "localhost")
        
        self.engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:5432/directory")
        self.Session = sessionmaker(bind=self.engine)
        
        # Create table if it doesn't exist
        try:
            Base.metadata.create_all(self.engine)
        except Exception as e:
            print(f"⚠️ Warning: Could not create search_history table: {e}")
    
    def normalize_location(self, city: str) -> str:
        """Normalize city name for consistent tracking"""
        city_lower = city.lower().strip()
        
        # Check aliases
        for normalized, aliases in self.city_aliases.items():
            if city_lower in aliases:
                return normalized
        
        return city_lower
    
    def normalize_specialty(self, specialty: str) -> str:
        """Normalize specialty name for consistent tracking"""
        specialty_lower = specialty.lower().strip()
        
        # Check aliases
        for normalized, aliases in self.specialty_aliases.items():
            if specialty_lower in aliases:
                return normalized
        
        return specialty_lower
    
    def generate_query_fingerprint(self, search_query: SearchQuery) -> str:
        """Generate unique fingerprint for search query"""
        # Normalize components
        normalized_city = self.normalize_location(search_query.city)
        normalized_specialty = self.normalize_specialty(search_query.specialty)
        
        # Create fingerprint string
        fingerprint_components = [
            normalized_city,
            normalized_specialty,
            search_query.search_type,
            str(search_query.radius or ""),
            "|".join(sorted(search_query.keywords or []))
        ]
        
        fingerprint_text = "|".join(fingerprint_components)
        return hashlib.md5(fingerprint_text.encode('utf-8')).hexdigest()
    
    def should_perform_search(self, city: str, specialty: str, search_type: str = "nearby", 
                            radius: Optional[int] = None, keywords: Optional[List[str]] = None) -> bool:
        """Check if search should be performed or if it's been done recently
        
        Returns:
            True if search should be performed, False if recently done
        """
        search_query = SearchQuery(
            city=city,
            specialty=specialty, 
            search_type=search_type,
            radius=radius,
            keywords=keywords
        )
        
        fingerprint = self.generate_query_fingerprint(search_query)
        
        session = self.Session()
        try:
            # Check for recent searches
            cutoff_date = datetime.utcnow() - timedelta(days=self.expiry_days)
            
            recent_search = session.query(SearchHistory).filter(
                SearchHistory.query_fingerprint == fingerprint,
                SearchHistory.search_date >= cutoff_date
            ).first()
            
            if recent_search:
                days_ago = (datetime.utcnow() - recent_search.search_date).days
                print(f"⏭️ Search already performed {days_ago} days ago: {city} + {specialty}")
                print(f"   Found {recent_search.results_count} results, {recent_search.new_providers_found} new providers")
                return False
            
            return True
            
        finally:
            session.close()
    
    def record_search(self, city: str, specialty: str, results_count: int, 
                     new_providers_found: int = 0, duplicates_found: int = 0,
                     search_type: str = "nearby", radius: Optional[int] = None,
                     keywords: Optional[List[str]] = None, api_calls_used: int = 1,
                     execution_time_seconds: Optional[int] = None) -> int:
        """Record a completed search in the tracking system
        
        Returns:
            ID of the created search history record
        """
        search_query = SearchQuery(
            city=city,
            specialty=specialty,
            search_type=search_type,
            radius=radius,
            keywords=keywords
        )
        
        fingerprint = self.generate_query_fingerprint(search_query)
        
        session = self.Session()
        try:
            search_record = SearchHistory(
                query_fingerprint=fingerprint,
                city=self.normalize_location(city),
                specialty=self.normalize_specialty(specialty),
                search_type=search_type,
                radius=radius,
                keywords=keywords,
                results_count=results_count,
                new_providers_found=new_providers_found,
                duplicates_found=duplicates_found,
                api_calls_used=api_calls_used,
                execution_time_seconds=execution_time_seconds
            )
            
            session.add(search_record)
            session.commit()
            
            record_id = search_record.id
            print(f"📊 Recorded search: {city} + {specialty} → {results_count} results ({new_providers_found} new)")
            
            return record_id
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error recording search: {str(e)}")
            return -1
        finally:
            session.close()
    
    def get_search_statistics(self, days: int = 30) -> Dict:
        """Get search statistics for the last N days"""
        session = self.Session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get basic stats
            recent_searches = session.query(SearchHistory).filter(
                SearchHistory.search_date >= cutoff_date
            ).all()
            
            if not recent_searches:
                return {"total_searches": 0, "days": days}
            
            total_searches = len(recent_searches)
            total_results = sum(s.results_count for s in recent_searches)
            total_new_providers = sum(s.new_providers_found for s in recent_searches)
            total_api_calls = sum(s.api_calls_used for s in recent_searches)
            
            # City breakdown
            city_stats = {}
            for search in recent_searches:
                city = search.city
                if city not in city_stats:
                    city_stats[city] = {"searches": 0, "results": 0, "new_providers": 0}
                city_stats[city]["searches"] += 1
                city_stats[city]["results"] += search.results_count
                city_stats[city]["new_providers"] += search.new_providers_found
            
            # Specialty breakdown
            specialty_stats = {}
            for search in recent_searches:
                specialty = search.specialty
                if specialty not in specialty_stats:
                    specialty_stats[specialty] = {"searches": 0, "results": 0, "new_providers": 0}
                specialty_stats[specialty]["searches"] += 1
                specialty_stats[specialty]["results"] += search.results_count
                specialty_stats[specialty]["new_providers"] += search.new_providers_found
            
            return {
                "days": days,
                "total_searches": total_searches,
                "total_results": total_results,
                "total_new_providers": total_new_providers,
                "total_api_calls": total_api_calls,
                "avg_results_per_search": total_results / total_searches if total_searches > 0 else 0,
                "cities": city_stats,
                "specialties": specialty_stats
            }
            
        finally:
            session.close()
    
    def get_coverage_gaps(self) -> List[Dict]:
        """Identify potential coverage gaps in searches"""
        session = self.Session()
        try:
            # Define target coverage
            target_cities = ['tokyo', 'yokohama', 'osaka', 'nagoya', 'kyoto', 'fukuoka']
            target_specialties = ['general_medicine', 'cardiology', 'dermatology', 'pediatrics']
            
            # Get recent search coverage
            cutoff_date = datetime.utcnow() - timedelta(days=self.expiry_days)
            recent_searches = session.query(SearchHistory).filter(
                SearchHistory.search_date >= cutoff_date
            ).all()
            
            searched_combinations = set()
            for search in recent_searches:
                searched_combinations.add((search.city, search.specialty))
            
            # Find gaps
            gaps = []
            for city in target_cities:
                for specialty in target_specialties:
                    if (city, specialty) not in searched_combinations:
                        gaps.append({
                            "city": city,
                            "specialty": specialty,
                            "priority": "high" if city in ['tokyo', 'yokohama'] else "medium"
                        })
            
            return gaps
            
        finally:
            session.close()
    
    def cleanup_old_searches(self, days_to_keep: int = 90) -> int:
        """Remove old search records to keep database clean
        
        Returns:
            Number of records deleted
        """
        session = self.Session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            deleted_count = session.query(SearchHistory).filter(
                SearchHistory.search_date < cutoff_date
            ).delete()
            
            session.commit()
            
            if deleted_count > 0:
                print(f"🧹 Cleaned up {deleted_count} old search records (older than {days_to_keep} days)")
            
            return deleted_count
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error cleaning up old searches: {str(e)}")
            return 0
        finally:
            session.close()

# Utility functions
def should_search(city: str, specialty: str, **kwargs) -> bool:
    """Convenience function to check if search should be performed"""
    tracker = SearchTracker()
    return tracker.should_perform_search(city, specialty, **kwargs)

def record_search_result(city: str, specialty: str, results_count: int, **kwargs) -> int:
    """Convenience function to record search results"""
    tracker = SearchTracker()
    return tracker.record_search(city, specialty, results_count, **kwargs)

if __name__ == "__main__":
    # Test the search tracking system
    tracker = SearchTracker()
    
    print("🔍 SEARCH TRACKING SYSTEM TEST")
    print("=" * 60)
    
    # Test search checking
    test_searches = [
        ("Tokyo", "cardiology"),
        ("Yokohama", "dermatology"), 
        ("Osaka", "general_medicine")
    ]
    
    for city, specialty in test_searches:
        should_search = tracker.should_perform_search(city, specialty)
        print(f"📍 {city} + {specialty}: {'SEARCH' if should_search else 'SKIP'}")
        
        if should_search:
            # Simulate recording a search
            tracker.record_search(
                city=city,
                specialty=specialty,
                results_count=25,
                new_providers_found=5,
                duplicates_found=20
            )
    
    # Show statistics
    print(f"\n📊 Search Statistics:")
    stats = tracker.get_search_statistics(days=30)
    print(f"   Total searches: {stats['total_searches']}")
    print(f"   Total results: {stats['total_results']}")
    print(f"   Total new providers: {stats['total_new_providers']}")
    
    # Show coverage gaps
    print(f"\n🕳️ Coverage Gaps:")
    gaps = tracker.get_coverage_gaps()
    for gap in gaps[:5]:  # Show first 5 gaps
        print(f"   {gap['city']} + {gap['specialty']} (priority: {gap['priority']})")
    
    print(f"\n✅ Search tracking system ready!") 