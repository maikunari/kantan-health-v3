#!/usr/bin/env python3
"""
Thorough Duplicate Content Finder
Checks for duplicate content across all fields and compares with WordPress
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from collections import defaultdict
import hashlib

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

def check_database_duplicates():
    """Check for duplicate content in database"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("🔍 Checking for duplicate content in DATABASE...")
    print("=" * 60)
    
    # Check each content field for duplicates
    fields_to_check = [
        ('ai_description', 'AI Description'),
        ('ai_excerpt', 'AI Excerpt'), 
        ('review_summary', 'Review Summary'),
        ('english_experience_summary', 'English Experience Summary')
    ]
    
    all_duplicates = {}
    
    for field, field_name in fields_to_check:
        print(f"\n🔍 Checking {field_name} duplicates...")
        
        # Find duplicates in this field
        query = f"""
        WITH duplicate_content AS (
            SELECT {field}, COUNT(*) as usage_count, 
                   STRING_AGG(CONCAT(id, ':', provider_name, ':', city), ' | ') as providers
            FROM providers 
            WHERE {field} IS NOT NULL 
              AND TRIM({field}) != ''
              AND LENGTH({field}) > 20
            GROUP BY {field}
            HAVING COUNT(*) > 1
        )
        SELECT {field} as content, usage_count, providers
        FROM duplicate_content
        ORDER BY usage_count DESC;
        """
        
        cursor.execute(query)
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"📊 Found {len(duplicates)} duplicate {field_name}:")
            print("-" * 80)
            
            all_duplicates[field] = duplicates
            
            for dup in duplicates:
                providers = dup['providers'].split(' | ')
                print(f"\n🔄 Used by {dup['usage_count']} providers:")
                content_preview = dup['content'][:100] + "..." if len(dup['content']) > 100 else dup['content']
                print(f"   Content: {content_preview}")
                print("   Providers:")
                for provider in providers:
                    parts = provider.split(':')
                    if len(parts) >= 3:
                        provider_id, name, city = parts[0], parts[1], parts[2]
                        print(f"     ID: {provider_id:>3} | {name:<35} | {city}")
        else:
            print(f"✅ No duplicate {field_name} found")
    
    cursor.close()
    conn.close()
    return all_duplicates

def get_wordpress_providers():
    """Fetch all providers from WordPress with ACF data"""
    wp_url = os.getenv('WORDPRESS_URL')
    wp_user = os.getenv('WORDPRESS_USERNAME') 
    wp_pass = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
    
    if not all([wp_url, wp_user, wp_pass]):
        print("❌ WordPress credentials missing")
        return []
    
    print("\n🔍 Fetching providers from WordPress...")
    
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
    
    print(f"📊 Total WordPress providers: {len(providers)}")
    return providers

def check_wordpress_duplicates():
    """Check for duplicate content on WordPress"""
    providers = get_wordpress_providers()
    
    if not providers:
        print("❌ No WordPress providers to check")
        return {}
    
    print("\n🔍 Checking for duplicate content on WORDPRESS...")
    print("=" * 60)
    
    # Group content by field
    fields_to_check = [
        ('ai_description', 'AI Description'),
        ('ai_excerpt', 'AI Excerpt'),
        ('review_summary', 'Review Summary'), 
        ('english_experience_summary', 'English Experience Summary')
    ]
    
    all_wp_duplicates = {}
    
    for field_key, field_name in fields_to_check:
        print(f"\n🔍 Checking WordPress {field_name} duplicates...")
        
        # Collect content from WordPress ACF fields
        content_map = defaultdict(list)
        
        for provider in providers:
            acf_data = provider.get('acf', {})
            content = acf_data.get(field_key, '')
            
            if content and len(str(content).strip()) > 20:
                content_clean = str(content).strip()
                provider_info = f"{provider['id']}:{provider['title']['rendered']}"
                content_map[content_clean].append(provider_info)
        
        # Find duplicates
        duplicates = {content: providers_list for content, providers_list in content_map.items() 
                     if len(providers_list) > 1}
        
        if duplicates:
            print(f"📊 Found {len(duplicates)} duplicate {field_name} on WordPress:")
            print("-" * 80)
            
            all_wp_duplicates[field_key] = duplicates
            
            for content, providers_list in duplicates.items():
                print(f"\n🔄 Used by {len(providers_list)} providers:")
                content_preview = content[:100] + "..." if len(content) > 100 else content
                print(f"   Content: {content_preview}")
                print("   Providers:")
                for provider_info in providers_list:
                    parts = provider_info.split(':', 1)
                    if len(parts) >= 2:
                        wp_id, name = parts[0], parts[1]
                        print(f"     WP ID: {wp_id:>4} | {name}")
        else:
            print(f"✅ No duplicate {field_name} found on WordPress")
    
    return all_wp_duplicates

def check_content_similarity():
    """Check for similar (not identical) content that might be duplicates"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print(f"\n🔍 Checking for SIMILAR content (potential duplicates)...")
    print("=" * 60)
    
    # Check for descriptions with same length (often indicates similar content)
    cursor.execute("""
        SELECT LENGTH(ai_description) as desc_length, COUNT(*) as count,
               STRING_AGG(CONCAT(id, ':', provider_name, ':', city), ' | ') as providers
        FROM providers 
        WHERE ai_description IS NOT NULL 
          AND LENGTH(ai_description) > 200
        GROUP BY LENGTH(ai_description)
        HAVING COUNT(*) > 1
        ORDER BY count DESC, desc_length;
    """)
    
    length_groups = cursor.fetchall()
    
    suspicious_groups = [group for group in length_groups if group['count'] > 1]
    
    if suspicious_groups:
        print(f"📊 Found {len(suspicious_groups)} groups with same description length:")
        print("-" * 80)
        
        for group in suspicious_groups:
            print(f"\nLength: {group['desc_length']} chars | {group['count']} providers:")
            providers = group['providers'].split(' | ')
            for provider in providers:
                parts = provider.split(':')
                if len(parts) >= 3:
                    provider_id, name, city = parts[0], parts[1], parts[2]
                    print(f"   ID: {provider_id:>3} | {name:<35} | {city}")
            
            # Get actual content for manual review
            if group['count'] <= 3:  # Only for small groups
                print("   📄 Content preview:")
                cursor.execute("""
                    SELECT id, provider_name, ai_description
                    FROM providers 
                    WHERE LENGTH(ai_description) = %s
                    ORDER BY provider_name
                """, (group['desc_length'],))
                
                content_samples = cursor.fetchall()
                for sample in content_samples:
                    preview = sample['ai_description'][:150] + "..."
                    print(f"      ID {sample['id']}: {preview}")
    else:
        print("✅ No suspicious length groupings found")
    
    cursor.close()
    conn.close()
    return suspicious_groups

def generate_duplicate_fix_commands(db_duplicates, wp_duplicates):
    """Generate commands to fix duplicate content"""
    if not db_duplicates and not wp_duplicates:
        print("\n✅ No duplicate content found - no fixes needed!")
        return
    
    print(f"\n🛠️  Fix Commands for Duplicate Content:")
    print("-" * 60)
    
    all_affected_providers = set()
    
    # Collect provider IDs from database duplicates
    for field, duplicates in db_duplicates.items():
        for dup in duplicates:
            providers = dup['providers'].split(' | ')
            for provider in providers[1:]:  # Skip first one, regenerate the rest
                parts = provider.split(':')
                if len(parts) >= 1:
                    all_affected_providers.add(int(parts[0]))
    
    # Collect provider IDs from WordPress duplicates  
    for field, duplicates in wp_duplicates.items():
        for content, providers_list in duplicates.items():
            # Note: WordPress IDs are different from database IDs
            print(f"   # WordPress duplicates in {field} field - manual review needed")
    
    if all_affected_providers:
        affected_list = sorted(list(all_affected_providers))
        print(f"\n1. Regenerate content for {len(affected_list)} providers with duplicates:")
        print(f"   # Provider IDs: {affected_list}")
        print(f"   python3 run_mega_batch_automation.py --limit {len(affected_list)} --dry-run")
        print(f"   python3 run_mega_batch_automation.py --limit {len(affected_list)}")
        
        print(f"\n2. Sync updated content to WordPress:")
        print("   python3 wordpress_sync_manager.py --sync-all --limit 20")
        
        print(f"\n3. Process in smaller batches if needed:")
        batch_size = 5
        for i in range(0, len(affected_list), batch_size):
            batch = affected_list[i:i+batch_size]
            print(f"   # Batch {i//batch_size + 1}: IDs {batch}")
            print(f"   python3 run_mega_batch_automation.py --limit {len(batch)}")

def main():
    print("🔍 Thorough Duplicate Content Analysis")
    print("=" * 60)
    
    # Check database duplicates
    db_duplicates = check_database_duplicates()
    
    # Check WordPress duplicates
    wp_duplicates = check_wordpress_duplicates()
    
    # Check similar content
    similar_content = check_content_similarity()
    
    # Generate fix commands
    generate_duplicate_fix_commands(db_duplicates, wp_duplicates)
    
    print("\n✅ Thorough duplicate analysis complete!")

if __name__ == "__main__":
    main()