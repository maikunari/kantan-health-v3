#!/usr/bin/env python3
"""
Targeted Content Problem Finder
Specifically looks for 'fail' descriptions, duplicates, and missing content
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import argparse

# Load environment variables
load_dotenv('config/.env')

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            database=os.getenv('POSTGRES_DB', 'directory'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

def find_fail_descriptions():
    """Find all variations of failed descriptions"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("🔍 Searching for failed descriptions...")
    
    # Search for various failure patterns
    patterns = [
        "ai_description = 'fail'",
        "ai_description = 'failed'", 
        "ai_description = 'error'",
        "ai_description ILIKE '%fail%'",
        "ai_description ILIKE '%error%'",
        "ai_description ILIKE '%unable%'",
        "ai_description ILIKE '%cannot%'",
        "ai_description ILIKE '%sorry%'",
        "ai_description ILIKE '%insufficient%'",
        "ai_description ILIKE '%not enough%'",
        "ai_description IS NULL",
        "TRIM(ai_description) = ''",
        "LENGTH(ai_description) < 20"
    ]
    
    all_failed = []
    
    for pattern in patterns:
        query = f"""
        SELECT DISTINCT id, provider_name, city, ai_description, ai_excerpt,
               CASE WHEN ai_description IS NULL THEN 'NULL'
                    WHEN TRIM(ai_description) = '' THEN 'EMPTY'
                    WHEN LENGTH(ai_description) < 20 THEN 'TOO_SHORT'
                    ELSE 'FAILED_CONTENT' 
               END as issue_type
        FROM providers 
        WHERE {pattern}
        ORDER BY provider_name;
        """
        
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            for result in results:
                if result not in all_failed:
                    all_failed.append(result)
        except Exception as e:
            print(f"Warning: Pattern '{pattern}' failed: {e}")
    
    print(f"📊 Found {len(all_failed)} providers with description issues:")
    print("-" * 90)
    
    for provider in all_failed:
        desc_preview = "NULL" if provider['ai_description'] is None else f"'{provider['ai_description'][:60]}...'"
        print(f"ID: {provider['id']:3} | {provider['provider_name']:<35} | {provider['city']:<10} | {provider['issue_type']:<12} | {desc_preview}")
    
    cursor.close()
    conn.close()
    return all_failed

def find_exact_duplicates():
    """Find providers with exactly identical descriptions"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n🔍 Finding exact duplicate descriptions...")
    
    query = """
    WITH duplicate_descriptions AS (
        SELECT ai_description, COUNT(*) as usage_count
        FROM providers 
        WHERE ai_description IS NOT NULL 
          AND TRIM(ai_description) != ''
          AND LENGTH(ai_description) > 50
        GROUP BY ai_description
        HAVING COUNT(*) > 1
    )
    SELECT p.id, p.provider_name, p.city, p.ai_description, dd.usage_count
    FROM providers p
    JOIN duplicate_descriptions dd ON p.ai_description = dd.ai_description
    ORDER BY dd.usage_count DESC, p.provider_name;
    """
    
    cursor.execute(query)
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"📊 Found {len(duplicates)} providers with duplicate descriptions:")
        print("-" * 90)
        
        current_description = None
        for dup in duplicates:
            if dup['ai_description'] != current_description:
                current_description = dup['ai_description']
                print(f"\n🔄 Description used by {dup['usage_count']} providers:")
                preview = current_description[:80] + "..." if len(current_description) > 80 else current_description
                print(f"   Content: {preview}")
                print("   Providers:")
            
            print(f"     ID: {dup['id']:3} | {dup['provider_name']:<35} | {dup['city']}")
    else:
        print("✅ No exact duplicate descriptions found")
    
    cursor.close()
    conn.close()
    return duplicates

def find_similar_descriptions():
    """Find potentially similar descriptions (same length, similar words)"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n🔍 Finding potentially similar descriptions...")
    
    # Group by description length to find potential similarities
    query = """
    SELECT LENGTH(ai_description) as desc_length, COUNT(*) as count,
           STRING_AGG(CONCAT(id, ':', provider_name), '; ') as providers
    FROM providers 
    WHERE ai_description IS NOT NULL 
      AND LENGTH(ai_description) > 100
    GROUP BY LENGTH(ai_description)
    HAVING COUNT(*) > 1
    ORDER BY count DESC, desc_length;
    """
    
    cursor.execute(query)
    length_groups = cursor.fetchall()
    
    suspicious_groups = [group for group in length_groups if group['count'] > 2]
    
    if suspicious_groups:
        print(f"📊 Found {len(suspicious_groups)} groups of descriptions with same length (potentially similar):")
        print("-" * 90)
        
        for group in suspicious_groups[:5]:  # Show top 5
            print(f"Length: {group['desc_length']} chars | Used by {group['count']} providers")
            providers = group['providers'].split('; ')[:3]  # Show first 3
            for provider in providers:
                print(f"   {provider}")
            if group['count'] > 3:
                print(f"   ... and {group['count'] - 3} more")
            print()
    else:
        print("✅ No suspicious length groupings found")
    
    cursor.close()
    conn.close()
    return suspicious_groups

def check_missing_core_content():
    """Check for missing essential content"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n🔍 Checking for missing core content...")
    
    query = """
    SELECT id, provider_name, city,
           CASE WHEN ai_description IS NULL OR TRIM(ai_description) = '' THEN '❌' ELSE '✅' END as has_description,
           CASE WHEN ai_excerpt IS NULL OR TRIM(ai_excerpt) = '' THEN '❌' ELSE '✅' END as has_excerpt,
           CASE WHEN business_hours IS NULL OR business_hours::text = '{}' THEN '❌' ELSE '✅' END as has_hours,
           CASE WHEN latitude IS NULL OR longitude IS NULL THEN '❌' ELSE '✅' END as has_location,
           CASE WHEN phone IS NULL OR TRIM(phone) = '' THEN '❌' ELSE '✅' END as has_phone
    FROM providers 
    ORDER BY provider_name;
    """
    
    cursor.execute(query)
    providers = cursor.fetchall()
    
    # Count missing items
    missing_description = sum(1 for p in providers if p['has_description'] == '❌')
    missing_excerpt = sum(1 for p in providers if p['has_excerpt'] == '❌')
    missing_hours = sum(1 for p in providers if p['has_hours'] == '❌')
    missing_location = sum(1 for p in providers if p['has_location'] == '❌')
    missing_phone = sum(1 for p in providers if p['has_phone'] == '❌')
    
    print(f"📊 Content Completeness Summary (Total: {len(providers)} providers):")
    print("-" * 60)
    print(f"Missing Description: {missing_description:3} providers")
    print(f"Missing Excerpt:     {missing_excerpt:3} providers") 
    print(f"Missing Hours:       {missing_hours:3} providers")
    print(f"Missing Location:    {missing_location:3} providers")
    print(f"Missing Phone:       {missing_phone:3} providers")
    
    # Show providers missing critical content
    critical_missing = [p for p in providers if p['has_description'] == '❌' or p['has_excerpt'] == '❌']
    
    if critical_missing:
        print(f"\n🚨 Providers missing critical content (description/excerpt):")
        print("-" * 80)
        for provider in critical_missing:
            print(f"ID: {provider['id']:3} | {provider['provider_name']:<40} | Desc: {provider['has_description']} | Excerpt: {provider['has_excerpt']}")
    
    cursor.close()
    conn.close()
    return providers, critical_missing

def check_content_quality():
    """Check for quality issues in existing content"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n🔍 Checking content quality issues...")
    
    # Very short descriptions
    cursor.execute("""
        SELECT id, provider_name, ai_description, LENGTH(ai_description) as length
        FROM providers 
        WHERE ai_description IS NOT NULL 
          AND LENGTH(ai_description) < 100
        ORDER BY length;
    """)
    short_descriptions = cursor.fetchall()
    
    # Descriptions with error indicators
    cursor.execute("""
        SELECT id, provider_name, ai_description
        FROM providers 
        WHERE ai_description ILIKE '%I apologize%'
           OR ai_description ILIKE '%I cannot%'
           OR ai_description ILIKE '%unable to%'
           OR ai_description ILIKE '%insufficient information%'
           OR ai_description ILIKE '%not enough information%'
           OR ai_description ILIKE '%limited information%'
        ORDER BY provider_name;
    """)
    error_descriptions = cursor.fetchall()
    
    # Generic template descriptions
    cursor.execute("""
        SELECT id, provider_name, ai_description
        FROM providers 
        WHERE ai_description ILIKE '%this healthcare facility%'
           OR ai_description ILIKE '%this medical center%'
           OR ai_description ILIKE '%this clinic provides%'
           OR ai_description ILIKE '%healthcare provider located%'
        ORDER BY provider_name;
    """)
    generic_descriptions = cursor.fetchall()
    
    print(f"📊 Quality Issues Found:")
    print(f"   Very short descriptions (<100 chars): {len(short_descriptions)}")
    print(f"   Error/apologetic descriptions: {len(error_descriptions)}")
    print(f"   Generic template descriptions: {len(generic_descriptions)}")
    
    all_quality_issues = []
    
    if short_descriptions:
        print(f"\n⚠️  Very short descriptions:")
        for desc in short_descriptions:
            print(f"   ID: {desc['id']:3} | {desc['provider_name']:<35} | Length: {desc['length']:3} | '{desc['ai_description']}'")
            all_quality_issues.append(desc['id'])
    
    if error_descriptions:
        print(f"\n⚠️  Error/apologetic descriptions:")
        for desc in error_descriptions:
            preview = desc['ai_description'][:100] + "..." if len(desc['ai_description']) > 100 else desc['ai_description']
            print(f"   ID: {desc['id']:3} | {desc['provider_name']:<35} | {preview}")
            all_quality_issues.append(desc['id'])
    
    if generic_descriptions:
        print(f"\n⚠️  Generic template descriptions:")
        for desc in generic_descriptions:
            preview = desc['ai_description'][:100] + "..." if len(desc['ai_description']) > 100 else desc['ai_description']
            print(f"   ID: {desc['id']:3} | {desc['provider_name']:<35} | {preview}")
            all_quality_issues.append(desc['id'])
    
    cursor.close()
    conn.close()
    return list(set(all_quality_issues))  # Remove duplicates

def generate_fix_commands(failed_providers, duplicate_providers, quality_issues, critical_missing):
    """Generate specific fix commands"""
    all_problem_ids = set()
    
    # Collect all provider IDs with issues
    all_problem_ids.update([p['id'] for p in failed_providers])
    all_problem_ids.update([p['id'] for p in duplicate_providers])
    all_problem_ids.update(quality_issues)
    all_problem_ids.update([p['id'] for p in critical_missing])
    
    if all_problem_ids:
        print(f"\n🛠️  Fix Commands for {len(all_problem_ids)} providers with issues:")
        print("-" * 60)
        
        print("1. Regenerate AI content for all problematic providers:")
        print(f"   python3 run_mega_batch_automation.py --limit {len(all_problem_ids)} --dry-run")
        print(f"   python3 run_mega_batch_automation.py --limit {len(all_problem_ids)}")
        
        print("\n2. Process in smaller batches for reliability:")
        batch_size = 10
        batches = (len(all_problem_ids) + batch_size - 1) // batch_size
        print(f"   # Process {len(all_problem_ids)} providers in {batches} batches of {batch_size}")
        for i in range(batches):
            print(f"   python3 run_mega_batch_automation.py --limit {batch_size}")
        
        print("\n3. After content regeneration, sync to WordPress:")
        print("   python3 wordpress_sync_manager.py --sync-all --limit 50 --dry-run")
        print("   python3 wordpress_sync_manager.py --sync-all --limit 50")
        
        print("\n4. For urgent fixes, target specific providers:")
        # Show a few examples
        sample_providers = list(all_problem_ids)[:3]
        for provider_id in sample_providers:
            print(f"   # Fix provider ID {provider_id}")
            print(f"   python3 run_mega_batch_automation.py --limit 1  # Then sync to WordPress")

def main():
    parser = argparse.ArgumentParser(description='Find specific content problems')
    parser.add_argument('--failed-only', action='store_true', help='Only show failed descriptions')
    parser.add_argument('--duplicates-only', action='store_true', help='Only show duplicates')
    parser.add_argument('--missing-only', action='store_true', help='Only show missing content')
    parser.add_argument('--quality-only', action='store_true', help='Only show quality issues')
    args = parser.parse_args()
    
    print("🔍 Healthcare Directory Content Problem Finder")
    print("=" * 60)
    
    failed_providers = []
    duplicate_providers = []
    critical_missing = []
    quality_issues = []
    
    if not any([args.failed_only, args.duplicates_only, args.missing_only, args.quality_only]):
        # Run all analyses
        failed_providers = find_fail_descriptions()
        duplicate_providers = find_exact_duplicates()
        find_similar_descriptions()
        providers, critical_missing = check_missing_core_content()
        quality_issues = check_content_quality()
        generate_fix_commands(failed_providers, duplicate_providers, quality_issues, critical_missing)
    else:
        if args.failed_only:
            failed_providers = find_fail_descriptions()
        if args.duplicates_only:
            duplicate_providers = find_exact_duplicates()
            find_similar_descriptions()
        if args.missing_only:
            providers, critical_missing = check_missing_core_content()
        if args.quality_only:
            quality_issues = check_content_quality()
    
    print("\n✅ Content problem analysis complete!")

if __name__ == "__main__":
    main()