#!/usr/bin/env python3
"""
Analyze provider distribution to identify high-value SEO combinations
This helps prioritize which taxonomy pages to generate first
"""

import os
import sys
from collections import defaultdict
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(__file__))

from src.core.database import DatabaseManager
from sqlalchemy import text


def analyze_provider_distribution():
    """Analyze current provider distribution for SEO prioritization"""
    
    db = DatabaseManager()
    session = db.get_session()
    
    print("📊 PROVIDER DISTRIBUTION ANALYSIS FOR SEO")
    print("=" * 60)
    
    try:
        # Get total provider count
        total = session.execute(text("SELECT COUNT(*) FROM providers")).scalar()
        print(f"\n📍 Total Providers: {total}")
        
        # Analyze by location (city/ward)
        print("\n🌍 LOCATION DISTRIBUTION:")
        print("-" * 40)
        
        locations = session.execute(text("""
            SELECT 
                city,
                ward,
                COUNT(*) as count
            FROM providers
            WHERE city IS NOT NULL AND city != ''
            GROUP BY city, ward
            ORDER BY count DESC
            LIMIT 20
        """)).fetchall()
        
        location_counts = defaultdict(int)
        ward_combinations = []
        
        for city, ward, count in locations:
            location = f"{ward}, {city}" if ward else city
            print(f"  {location}: {count} providers")
            location_counts[city] += count
            
            if ward:
                ward_combinations.append((city, ward, count))
        
        # Analyze by specialty
        print("\n🏥 SPECIALTY DISTRIBUTION:")
        print("-" * 40)
        
        # Handle JSON specialties field
        specialties_query = session.execute(text("""
            SELECT specialties::text, COUNT(*) as count
            FROM providers
            WHERE specialties IS NOT NULL
            GROUP BY specialties::text
            ORDER BY count DESC
            LIMIT 20
        """)).fetchall()
        
        specialty_counts = defaultdict(int)
        for spec_data, count in specialties_query:
            # Handle both array and string formats
            if isinstance(spec_data, list):
                for spec in spec_data:
                    specialty_counts[spec] += count
            elif isinstance(spec_data, str):
                # Try to parse as array-like string
                if spec_data.startswith('['):
                    try:
                        import json
                        specs = json.loads(spec_data.replace("'", '"'))
                        for spec in specs:
                            specialty_counts[spec] += count
                    except:
                        specialty_counts[spec_data] += count
                else:
                    specialty_counts[spec_data] += count
        
        for specialty, count in sorted(specialty_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {specialty}: {count} providers")
        
        # Find high-value combinations (location + specialty)
        print("\n🏆 HIGH-VALUE SEO COMBINATIONS (Tier 1: 5+ providers):")
        print("-" * 40)
        
        combinations = session.execute(text("""
            SELECT 
                city,
                ward,
                specialties::text as specialties,
                COUNT(*) as count
            FROM providers
            WHERE specialties IS NOT NULL 
                AND city IS NOT NULL 
                AND city != ''
            GROUP BY city, ward, specialties::text
            HAVING COUNT(*) >= 5
            ORDER BY count DESC
            LIMIT 20
        """)).fetchall()
        
        tier1_combinations = []
        for city, ward, specialties, count in combinations:
            location = f"{ward}, {city}" if ward else city
            # Parse specialties
            if isinstance(specialties, str) and specialties.startswith('['):
                try:
                    import json
                    spec_list = json.loads(specialties.replace("'", '"'))
                    specialty_str = spec_list[0] if spec_list else "Healthcare"
                except:
                    specialty_str = specialties
            else:
                specialty_str = specialties if specialties else "Healthcare"
            
            combination = f"{specialty_str} in {location}"
            print(f"  {combination}: {count} providers")
            tier1_combinations.append((city, ward, specialty_str, count))
        
        # Find Tier 2 combinations (1-4 providers)
        print("\n📈 TIER 2 COMBINATIONS (1-4 providers):")
        print("-" * 40)
        
        tier2_query = session.execute(text("""
            SELECT 
                city,
                ward,
                COUNT(*) as count
            FROM providers
            WHERE city IS NOT NULL AND city != ''
            GROUP BY city, ward
            HAVING COUNT(*) BETWEEN 1 AND 4
            ORDER BY count DESC
            LIMIT 10
        """)).fetchall()
        
        tier2_combinations = []
        for city, ward, count in tier2_query:
            location = f"{ward}, {city}" if ward else city
            print(f"  {location}: {count} providers")
            tier2_combinations.append((city, ward, count))
        
        # Report on providers with missing locations
        print("\n⚠️ PROVIDERS NEEDING LOCATION FIX:")
        print("-" * 40)
        
        missing_location_count = session.execute(text("""
            SELECT COUNT(*) 
            FROM providers 
            WHERE city IS NULL OR city = ''
        """)).scalar()
        
        if missing_location_count > 0:
            print(f"  {missing_location_count} providers with missing city data")
            print("  These providers are excluded from SEO analysis")
            print("  Run: python3 utility/fix_missing_locations.py to fix")
        else:
            print("  ✅ All providers have location data")
        
        # Summary statistics
        print("\n📊 SEO CONTENT GENERATION PRIORITIES:")
        print("-" * 40)
        
        # Count unique locations
        unique_locations = session.execute(text("""
            SELECT COUNT(DISTINCT CONCAT(COALESCE(city, ''), '|', COALESCE(ward, '')))
            FROM providers
        """)).scalar()
        
        # Count unique specialties
        unique_specialties = len(specialty_counts)
        
        # Estimate total combinations
        potential_combinations = unique_locations * unique_specialties
        
        print(f"  Unique Locations: {unique_locations}")
        print(f"  Unique Specialties: {unique_specialties}")
        print(f"  Potential Combination Pages: {potential_combinations}")
        print(f"  Tier 1 Pages (5+ providers): {len(tier1_combinations)}")
        print(f"  Tier 2 Pages (1-4 providers): {len(tier2_combinations)}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 40)
        print("1. START WITH: High-value Tokyo wards (Minato, Shinjuku, Shibuya)")
        print("2. FOCUS ON: Healthcare, Dentistry, General Medicine combinations")
        print("3. PRIORITY: Generate content for all Tier 1 combinations first")
        print("4. ESTIMATE: ~50-100 high-priority pages for immediate impact")
        
        # Export data for content generation
        print("\n📁 EXPORTING PRIORITY DATA...")
        
        priority_data = {
            "tier1": tier1_combinations,
            "tier2": tier2_combinations,
            "locations": dict(location_counts),
            "specialties": dict(specialty_counts),
            "total_providers": total
        }
        
        import json
        with open('seo_priority_data.json', 'w') as f:
            json.dump(priority_data, f, indent=2, default=str)
        
        print("✅ Priority data exported to seo_priority_data.json")
        
        return priority_data
        
    finally:
        session.close()


if __name__ == "__main__":
    analyze_provider_distribution()