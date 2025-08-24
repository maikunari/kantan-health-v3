#!/usr/bin/env python3
"""
Check specific provider descriptions for quality issues
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

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

def check_suspicious_groups():
    """Check the content of providers with same-length descriptions"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check the 801-char group
    provider_ids_801 = [372, 369, 263]
    print("🔍 Checking 801-character description group:")
    print("=" * 60)
    
    for provider_id in provider_ids_801:
        cursor.execute("""
            SELECT id, provider_name, city, ai_description, ai_excerpt
            FROM providers WHERE id = %s
        """, (provider_id,))
        
        result = cursor.fetchone()
        if result:
            print(f"\nID: {result['id']} | {result['provider_name']} | {result['city']}")
            print("-" * 60)
            print(f"Description: {result['ai_description']}")
            print(f"Excerpt: {result['ai_excerpt']}")
    
    # Check the 823-char group  
    provider_ids_823 = [352, 301, 271]
    print(f"\n\n🔍 Checking 823-character description group:")
    print("=" * 60)
    
    for provider_id in provider_ids_823:
        cursor.execute("""
            SELECT id, provider_name, city, ai_description, ai_excerpt
            FROM providers WHERE id = %s
        """, (provider_id,))
        
        result = cursor.fetchone()
        if result:
            print(f"\nID: {result['id']} | {result['provider_name']} | {result['city']}")
            print("-" * 60)
            print(f"Description: {result['ai_description']}")
            print(f"Excerpt: {result['ai_excerpt']}")
    
    cursor.close()
    conn.close()

def check_random_sample():
    """Check a random sample of descriptions for quality"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print(f"\n\n🔍 Random sample of provider descriptions:")
    print("=" * 60)
    
    cursor.execute("""
        SELECT id, provider_name, city, ai_description, ai_excerpt
        FROM providers 
        WHERE ai_description IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 5
    """)
    
    results = cursor.fetchall()
    
    for result in results:
        print(f"\nID: {result['id']} | {result['provider_name']} | {result['city']}")
        print("-" * 60)
        description_preview = result['ai_description'][:200] + "..." if len(result['ai_description']) > 200 else result['ai_description']
        excerpt_preview = result['ai_excerpt'][:100] + "..." if len(result['ai_excerpt']) > 100 else result['ai_excerpt']
        print(f"Description: {description_preview}")
        print(f"Excerpt: {excerpt_preview}")
    
    cursor.close()
    conn.close()

def find_providers_by_pattern():
    """Search for specific patterns that might indicate problems"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print(f"\n\n🔍 Searching for specific problematic patterns:")
    print("=" * 60)
    
    # Search patterns that might indicate issues
    patterns = [
        ("Empty/null descriptions", "ai_description IS NULL OR TRIM(ai_description) = ''"),
        ("'fail' descriptions", "ai_description = 'fail'"),
        ("Contains 'fail'", "ai_description ILIKE '%fail%'"),
        ("Contains 'error'", "ai_description ILIKE '%error%'"),
        ("Very short descriptions", "LENGTH(ai_description) < 50"),
        ("Apologetic descriptions", "ai_description ILIKE '%sorry%' OR ai_description ILIKE '%apologize%'"),
        ("Generic descriptions", "ai_description ILIKE '%this clinic%' OR ai_description ILIKE '%this hospital%'")
    ]
    
    for pattern_name, pattern_sql in patterns:
        cursor.execute(f"""
            SELECT COUNT(*) as count,
                   STRING_AGG(CONCAT(id, ':', provider_name), '; ') as examples
            FROM providers 
            WHERE {pattern_sql}
        """)
        
        result = cursor.fetchone()
        if result['count'] > 0:
            print(f"{pattern_name}: {result['count']} providers")
            examples = result['examples'].split('; ')[:3]  # Show first 3
            for example in examples:
                print(f"   {example}")
            if result['count'] > 3:
                print(f"   ... and {result['count'] - 3} more")
        else:
            print(f"{pattern_name}: 0 providers ✅")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    print("🔍 Specific Description Checker")
    print("=" * 60)
    
    check_suspicious_groups()
    check_random_sample()
    find_providers_by_pattern()
    
    print("\n✅ Specific description check complete!")