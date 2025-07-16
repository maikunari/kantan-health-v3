#!/usr/bin/env python3
"""
Content Quality Analysis Script
Identifies providers with missing, duplicate, or incomplete content
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from collections import Counter
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

def find_failed_descriptions():
    """Find providers with description = 'fail' or similar failure indicators"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("🔍 Finding providers with failed descriptions...")
    
    query = """
    SELECT id, provider_name, city, ai_description, ai_excerpt
    FROM providers 
    WHERE ai_description = 'fail' 
       OR ai_description ILIKE '%fail%'
       OR ai_description ILIKE '%error%'
       OR ai_description ILIKE '%unable%'
       OR ai_description IS NULL
       OR TRIM(ai_description) = ''
    ORDER BY provider_name;
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"📊 Found {len(results)} providers with failed/missing descriptions:")
    print("-" * 80)
    
    for row in results:
        status = "NULL" if row['ai_description'] is None else f"'{row['ai_description'][:50]}...'"
        print(f"ID: {row['id']:3} | {row['provider_name']:<40} | {row['city']:<10} | {status}")
    
    cursor.close()
    conn.close()
    return results

def find_duplicate_descriptions():
    """Find providers with identical descriptions"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n🔍 Finding providers with duplicate descriptions...")
    
    # Find descriptions that appear more than once
    query = """
    SELECT ai_description, COUNT(*) as count
    FROM providers 
    WHERE ai_description IS NOT NULL 
      AND TRIM(ai_description) != ''
      AND ai_description != 'fail'
    GROUP BY ai_description
    HAVING COUNT(*) > 1
    ORDER BY count DESC;
    """
    
    cursor.execute(query)
    duplicates = cursor.fetchall()
    
    print(f"📊 Found {len(duplicates)} duplicate descriptions:")
    print("-" * 80)
    
    total_affected = 0
    for dup in duplicates:
        count = dup['count']
        description_preview = dup['ai_description'][:100] + "..." if len(dup['ai_description']) > 100 else dup['ai_description']
        print(f"Used by {count} providers: {description_preview}")
        
        # Get the specific providers using this description
        detail_query = """
        SELECT id, provider_name, city
        FROM providers 
        WHERE ai_description = %s
        ORDER BY provider_name;
        """
        cursor.execute(detail_query, (dup['ai_description'],))
        providers = cursor.fetchall()
        
        for provider in providers:
            print(f"  → ID: {provider['id']:3} | {provider['provider_name']:<40} | {provider['city']}")
        print()
        total_affected += count
    
    print(f"Total providers affected by duplicates: {total_affected}")
    
    cursor.close()
    conn.close()
    return duplicates

def find_missing_content():
    """Find providers missing various types of content"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n🔍 Analyzing missing content across all providers...")
    
    # Get comprehensive content status
    query = """
    SELECT 
        id,
        provider_name,
        city,
        CASE WHEN ai_description IS NULL OR TRIM(ai_description) = '' OR ai_description = 'fail' THEN 'MISSING' ELSE 'OK' END as description_status,
        CASE WHEN ai_excerpt IS NULL OR TRIM(ai_excerpt) = '' OR ai_excerpt = 'fail' THEN 'MISSING' ELSE 'OK' END as excerpt_status,
        CASE WHEN review_summary IS NULL OR TRIM(review_summary) = '' THEN 'MISSING' ELSE 'OK' END as review_status,
        CASE WHEN english_experience_summary IS NULL OR TRIM(english_experience_summary) = '' THEN 'MISSING' ELSE 'OK' END as english_status,
        CASE WHEN business_hours IS NULL OR business_hours::text = '' OR business_hours::text = '{}' THEN 'MISSING' ELSE 'OK' END as hours_status,
        CASE WHEN latitude IS NULL OR longitude IS NULL THEN 'MISSING' ELSE 'OK' END as location_status,
        CASE WHEN phone IS NULL OR TRIM(phone) = '' THEN 'MISSING' ELSE 'OK' END as phone_status,
        CASE WHEN website IS NULL OR TRIM(website) = '' THEN 'MISSING' ELSE 'OK' END as website_status
    FROM providers 
    ORDER BY provider_name;
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Analyze missing content statistics
    stats = {
        'description': 0, 'excerpt': 0, 'review': 0, 'english': 0,
        'hours': 0, 'location': 0, 'phone': 0, 'website': 0
    }
    
    missing_any = []
    critical_missing = []  # Missing description or excerpt
    
    for row in results:
        issues = []
        if row['description_status'] == 'MISSING':
            stats['description'] += 1
            issues.append('description')
        if row['excerpt_status'] == 'MISSING':
            stats['excerpt'] += 1
            issues.append('excerpt')
        if row['review_status'] == 'MISSING':
            stats['review'] += 1
            issues.append('review')
        if row['english_status'] == 'MISSING':
            stats['english'] += 1
            issues.append('english')
        if row['hours_status'] == 'MISSING':
            stats['hours'] += 1
            issues.append('hours')
        if row['location_status'] == 'MISSING':
            stats['location'] += 1
            issues.append('location')
        if row['phone_status'] == 'MISSING':
            stats['phone'] += 1
            issues.append('phone')
        if row['website_status'] == 'MISSING':
            stats['website'] += 1
            issues.append('website')
        
        if issues:
            missing_any.append((row, issues))
            if 'description' in issues or 'excerpt' in issues:
                critical_missing.append((row, issues))
    
    total_providers = len(results)
    
    print(f"📊 Content Analysis Summary (Total Providers: {total_providers}):")
    print("-" * 60)
    print(f"Missing AI Description:     {stats['description']:3} ({stats['description']/total_providers*100:.1f}%)")
    print(f"Missing AI Excerpt:         {stats['excerpt']:3} ({stats['excerpt']/total_providers*100:.1f}%)")
    print(f"Missing Review Summary:     {stats['review']:3} ({stats['review']/total_providers*100:.1f}%)")
    print(f"Missing English Summary:    {stats['english']:3} ({stats['english']/total_providers*100:.1f}%)")
    print(f"Missing Business Hours:     {stats['hours']:3} ({stats['hours']/total_providers*100:.1f}%)")
    print(f"Missing Location Data:      {stats['location']:3} ({stats['location']/total_providers*100:.1f}%)")
    print(f"Missing Phone:              {stats['phone']:3} ({stats['phone']/total_providers*100:.1f}%)")
    print(f"Missing Website:            {stats['website']:3} ({stats['website']/total_providers*100:.1f}%)")
    
    print(f"\n🚨 Critical Issues (Missing Description/Excerpt): {len(critical_missing)} providers")
    if critical_missing:
        print("-" * 80)
        for row, issues in critical_missing[:20]:  # Show first 20
            issues_str = ", ".join(issues)
            print(f"ID: {row['id']:3} | {row['provider_name']:<40} | {row['city']:<10} | Missing: {issues_str}")
        if len(critical_missing) > 20:
            print(f"... and {len(critical_missing) - 20} more")
    
    cursor.close()
    conn.close()
    return results, stats, critical_missing

def find_content_quality_issues():
    """Find additional content quality issues"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n🔍 Finding content quality issues...")
    
    # Find very short descriptions (likely incomplete)
    query = """
    SELECT id, provider_name, city, ai_description, LENGTH(ai_description) as desc_length
    FROM providers 
    WHERE ai_description IS NOT NULL 
      AND ai_description != 'fail'
      AND LENGTH(ai_description) < 50
    ORDER BY desc_length;
    """
    
    cursor.execute(query)
    short_descriptions = cursor.fetchall()
    
    if short_descriptions:
        print(f"📊 Found {len(short_descriptions)} providers with very short descriptions (<50 chars):")
        print("-" * 80)
        for row in short_descriptions:
            print(f"ID: {row['id']:3} | {row['provider_name']:<40} | {row['city']:<10} | Length: {row['desc_length']} | '{row['ai_description']}'")
    
    # Find descriptions with error indicators
    query = """
    SELECT id, provider_name, city, ai_description
    FROM providers 
    WHERE ai_description ILIKE '%sorry%'
       OR ai_description ILIKE '%cannot%'
       OR ai_description ILIKE '%unable%'
       OR ai_description ILIKE '%insufficient%'
       OR ai_description ILIKE '%not available%'
    ORDER BY provider_name;
    """
    
    cursor.execute(query)
    error_descriptions = cursor.fetchall()
    
    if error_descriptions:
        print(f"\n📊 Found {len(error_descriptions)} providers with error-indicating descriptions:")
        print("-" * 80)
        for row in error_descriptions:
            print(f"ID: {row['id']:3} | {row['provider_name']:<40} | {row['city']:<10}")
            print(f"     Description: {row['ai_description'][:100]}...")
    
    cursor.close()
    conn.close()
    return short_descriptions, error_descriptions

def generate_fix_commands(failed_descriptions, critical_missing):
    """Generate commands to fix the identified issues"""
    print("\n🛠️  Suggested Fix Commands:")
    print("-" * 60)
    
    if failed_descriptions or critical_missing:
        # Get unique provider IDs that need content generation
        provider_ids = set()
        
        for row in failed_descriptions:
            provider_ids.add(row['id'])
        
        for row, issues in critical_missing:
            if 'description' in issues or 'excerpt' in issues:
                provider_ids.add(row['id'])
        
        print("1. Regenerate AI content for problematic providers:")
        print(f"   python3 run_mega_batch_automation.py --limit {len(provider_ids)} --dry-run")
        print(f"   python3 run_mega_batch_automation.py --limit {len(provider_ids)}")
        
        print("\n2. Sync updated content to WordPress:")
        print("   python3 wordpress_sync_manager.py --sync-all --limit 50 --dry-run")
        print("   python3 wordpress_sync_manager.py --sync-all --limit 50")
        
        print("\n3. For specific providers with issues, use:")
        print("   python3 wordpress_sync_manager.py --sync-provider \"Provider Name\" --force")
        
        if len(provider_ids) > 10:
            print(f"\n4. Process in smaller batches for reliability:")
            print("   python3 run_mega_batch_automation.py --limit 10")
            print("   # Repeat until all providers are processed")

def main():
    parser = argparse.ArgumentParser(description='Analyze provider content quality issues')
    parser.add_argument('--failed-only', action='store_true', help='Only show failed descriptions')
    parser.add_argument('--duplicates-only', action='store_true', help='Only show duplicate descriptions')
    parser.add_argument('--missing-only', action='store_true', help='Only show missing content analysis')
    parser.add_argument('--quality-only', action='store_true', help='Only show quality issues')
    args = parser.parse_args()
    
    print("🔍 Healthcare Directory Content Quality Analysis")
    print("=" * 60)
    
    failed_descriptions = []
    duplicates = []
    critical_missing = []
    
    if not any([args.failed_only, args.duplicates_only, args.missing_only, args.quality_only]):
        # Run all analyses
        failed_descriptions = find_failed_descriptions()
        duplicates = find_duplicate_descriptions()
        results, stats, critical_missing = find_missing_content()
        short_descriptions, error_descriptions = find_content_quality_issues()
        generate_fix_commands(failed_descriptions, critical_missing)
    else:
        if args.failed_only:
            failed_descriptions = find_failed_descriptions()
        if args.duplicates_only:
            duplicates = find_duplicate_descriptions()
        if args.missing_only:
            results, stats, critical_missing = find_missing_content()
        if args.quality_only:
            short_descriptions, error_descriptions = find_content_quality_issues()
    
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main()