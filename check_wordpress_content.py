#!/usr/bin/env python3
"""
WordPress Content Quality Checker
Compares database content with what's published on WordPress
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
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

def get_wordpress_providers():
    """Fetch all healthcare providers from WordPress"""
    wp_url = os.getenv('WORDPRESS_URL')
    wp_user = os.getenv('WORDPRESS_USERNAME')
    wp_pass = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
    
    if not all([wp_url, wp_user, wp_pass]):
        print("❌ WordPress credentials missing in .env file")
        return []
    
    print("🔍 Fetching providers from WordPress...")
    
    providers = []
    page = 1
    per_page = 100
    
    while True:
        url = f"{wp_url}/wp-json/wp/v2/healthcare_provider"
        params = {
            'page': page,
            'per_page': per_page,
            'status': 'publish'
        }
        
        try:
            response = requests.get(
                url, 
                params=params,
                auth=HTTPBasicAuth(wp_user, wp_pass),
                timeout=30
            )
            
            if response.status_code == 200:
                page_providers = response.json()
                if not page_providers:
                    break
                providers.extend(page_providers)
                print(f"   Fetched page {page}: {len(page_providers)} providers")
                page += 1
            else:
                print(f"❌ WordPress API error: {response.status_code}")
                break
                
        except Exception as e:
            print(f"❌ Error fetching from WordPress: {e}")
            break
    
    print(f"📊 Total WordPress providers found: {len(providers)}")
    return providers

def get_acf_field_value(wp_provider, field_name):
    """Extract ACF field value from WordPress provider data"""
    acf_data = wp_provider.get('acf', {})
    return acf_data.get(field_name, '')

def compare_database_vs_wordpress():
    """Compare database content with WordPress content"""
    # Get database providers
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT id, provider_name, wordpress_post_id, ai_description, ai_excerpt,
               review_summary, english_experience_summary, last_wordpress_sync
        FROM providers 
        WHERE wordpress_post_id IS NOT NULL
        ORDER BY provider_name;
    """)
    
    db_providers = cursor.fetchall()
    print(f"📊 Database providers with WordPress IDs: {len(db_providers)}")
    
    # Get WordPress providers
    wp_providers = get_wordpress_providers()
    
    # Create lookup by WordPress ID
    wp_lookup = {str(provider['id']): provider for provider in wp_providers}
    
    print(f"\n🔍 Comparing database vs WordPress content...")
    print("-" * 80)
    
    issues = []
    content_mismatches = []
    missing_descriptions = []
    
    for db_provider in db_providers:
        wp_id = str(db_provider['wordpress_post_id'])
        provider_name = db_provider['provider_name']
        
        if wp_id not in wp_lookup:
            issues.append(f"❌ Provider '{provider_name}' (ID: {db_provider['id']}) not found in WordPress (WP ID: {wp_id})")
            continue
        
        wp_provider = wp_lookup[wp_id]
        
        # Check ACF field content
        wp_description = get_acf_field_value(wp_provider, 'ai_description')
        wp_excerpt = get_acf_field_value(wp_provider, 'ai_excerpt')
        wp_review_summary = get_acf_field_value(wp_provider, 'review_summary')
        wp_english_summary = get_acf_field_value(wp_provider, 'english_experience_summary')
        
        # Check for missing descriptions on WordPress
        if not wp_description or wp_description.lower() in ['fail', 'error', '']:
            missing_descriptions.append({
                'id': db_provider['id'],
                'name': provider_name,
                'wp_id': wp_id,
                'db_description': db_provider['ai_description'][:100] if db_provider['ai_description'] else 'NULL',
                'wp_description': wp_description
            })
        
        # Check for content mismatches
        if db_provider['ai_description'] and wp_description:
            if db_provider['ai_description'].strip() != wp_description.strip():
                content_mismatches.append({
                    'id': db_provider['id'],
                    'name': provider_name,
                    'wp_id': wp_id,
                    'field': 'ai_description',
                    'db_length': len(db_provider['ai_description']),
                    'wp_length': len(wp_description)
                })
    
    # Report findings
    print(f"\n📊 Content Analysis Results:")
    print(f"   Total database providers: {len(db_providers)}")
    print(f"   Total WordPress providers: {len(wp_providers)}")
    print(f"   General issues: {len(issues)}")
    print(f"   Missing/failed descriptions: {len(missing_descriptions)}")
    print(f"   Content mismatches: {len(content_mismatches)}")
    
    if issues:
        print(f"\n🚨 General Issues:")
        for issue in issues:
            print(f"   {issue}")
    
    if missing_descriptions:
        print(f"\n🚨 Providers with missing/failed descriptions on WordPress:")
        print("-" * 80)
        for provider in missing_descriptions:
            print(f"ID: {provider['id']:3} | {provider['name']:<40} | WP ID: {provider['wp_id']}")
            print(f"     DB: {provider['db_description']}")
            print(f"     WP: '{provider['wp_description']}'")
            print()
    
    if content_mismatches:
        print(f"\n⚠️  Content length mismatches (possible sync issues):")
        print("-" * 80)
        for mismatch in content_mismatches[:10]:  # Show first 10
            print(f"ID: {mismatch['id']:3} | {mismatch['name']:<40} | Field: {mismatch['field']}")
            print(f"     DB length: {mismatch['db_length']}, WP length: {mismatch['wp_length']}")
        if len(content_mismatches) > 10:
            print(f"... and {len(content_mismatches) - 10} more mismatches")
    
    cursor.close()
    conn.close()
    
    return issues, missing_descriptions, content_mismatches

def check_specific_content_issues():
    """Check for specific content quality problems"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print(f"\n🔍 Checking for specific content quality issues...")
    
    # Check for very short descriptions
    cursor.execute("""
        SELECT id, provider_name, ai_description, LENGTH(ai_description) as desc_length
        FROM providers 
        WHERE ai_description IS NOT NULL 
          AND LENGTH(ai_description) < 100
        ORDER BY desc_length;
    """)
    short_descriptions = cursor.fetchall()
    
    # Check for generic/template descriptions
    cursor.execute("""
        SELECT id, provider_name, ai_description
        FROM providers 
        WHERE ai_description ILIKE '%healthcare provider%'
           OR ai_description ILIKE '%medical facility%'
           OR ai_description ILIKE '%this clinic%'
           OR ai_description ILIKE '%this hospital%'
        ORDER BY provider_name;
    """)
    generic_descriptions = cursor.fetchall()
    
    # Check for duplicate descriptions
    cursor.execute("""
        SELECT ai_description, COUNT(*) as provider_count, 
               STRING_AGG(provider_name, ', ') as providers
        FROM providers 
        WHERE ai_description IS NOT NULL 
          AND LENGTH(ai_description) > 50
        GROUP BY ai_description
        HAVING COUNT(*) > 1
        ORDER BY provider_count DESC;
    """)
    duplicate_descriptions = cursor.fetchall()
    
    print(f"📊 Content Quality Issues:")
    print(f"   Very short descriptions (<100 chars): {len(short_descriptions)}")
    print(f"   Generic/template descriptions: {len(generic_descriptions)}")
    print(f"   Duplicate descriptions: {len(duplicate_descriptions)}")
    
    if short_descriptions:
        print(f"\n⚠️  Very short descriptions:")
        for desc in short_descriptions[:5]:
            print(f"   ID: {desc['id']:3} | {desc['provider_name']:<30} | Length: {desc['desc_length']}")
    
    if generic_descriptions:
        print(f"\n⚠️  Generic/template descriptions:")
        for desc in generic_descriptions[:5]:
            preview = desc['ai_description'][:80] + "..." if len(desc['ai_description']) > 80 else desc['ai_description']
            print(f"   ID: {desc['id']:3} | {desc['provider_name']:<30} | {preview}")
    
    if duplicate_descriptions:
        print(f"\n⚠️  Duplicate descriptions:")
        for dup in duplicate_descriptions[:3]:
            print(f"   Used by {dup['provider_count']} providers: {dup['providers']}")
            preview = dup['ai_description'][:100] + "..." if len(dup['ai_description']) > 100 else dup['ai_description']
            print(f"      Content: {preview}")
            print()
    
    cursor.close()
    conn.close()
    
    return short_descriptions, generic_descriptions, duplicate_descriptions

def generate_fix_commands_wordpress(missing_descriptions, content_mismatches):
    """Generate commands to fix WordPress content issues"""
    if missing_descriptions or content_mismatches:
        print(f"\n🛠️  Suggested Fix Commands:")
        print("-" * 60)
        
        if missing_descriptions:
            provider_names = [p['name'] for p in missing_descriptions[:5]]
            print("1. Force sync specific providers with missing content:")
            for name in provider_names:
                print(f"   python3 wordpress_sync_manager.py --sync-provider \"{name}\" --force")
        
        if content_mismatches:
            print(f"\n2. Bulk sync to fix content mismatches:")
            print("   python3 wordpress_sync_manager.py --sync-all --force --limit 20")
        
        print(f"\n3. Regenerate content if quality issues persist:")
        print("   python3 run_mega_batch_automation.py --limit 10 --dry-run")
        print("   python3 run_mega_batch_automation.py --limit 10")

def main():
    parser = argparse.ArgumentParser(description='Check WordPress content quality')
    parser.add_argument('--wordpress-only', action='store_true', help='Only check WordPress comparison')
    parser.add_argument('--quality-only', action='store_true', help='Only check content quality issues')
    args = parser.parse_args()
    
    print("🔍 WordPress Content Quality Analysis")
    print("=" * 60)
    
    if not any([args.wordpress_only, args.quality_only]):
        # Run all checks
        issues, missing_descriptions, content_mismatches = compare_database_vs_wordpress()
        short_descriptions, generic_descriptions, duplicate_descriptions = check_specific_content_issues()
        generate_fix_commands_wordpress(missing_descriptions, content_mismatches)
    else:
        if args.wordpress_only:
            issues, missing_descriptions, content_mismatches = compare_database_vs_wordpress()
            generate_fix_commands_wordpress(missing_descriptions, content_mismatches)
        if args.quality_only:
            short_descriptions, generic_descriptions, duplicate_descriptions = check_specific_content_issues()
    
    print("\n✅ WordPress analysis complete!")

if __name__ == "__main__":
    main()