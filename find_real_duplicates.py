#!/usr/bin/env python3
"""
Advanced Duplicate Content Detector
Uses text similarity analysis to find actual duplicate content
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import re
from difflib import SequenceMatcher

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

def normalize_text(text):
    """Normalize text for comparison by removing provider-specific details"""
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove provider-specific patterns that might vary
    patterns = [
        r'\b(dr\.|doctor)\s+\w+',  # Doctor names
        r'\d+\.\d+/5',  # Ratings
        r'\d+\s+(patient|review)s?',  # Review counts
        r'(located|situated)\s+in\s+\w+',  # Location mentions
        r'\b\w+\s+(ward|district|area)',  # Ward/district names
        r'\b(tokyo|osaka|yokohama|fukuoka|kyoto)\b',  # City names
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '[PLACEHOLDER]', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def calculate_similarity(text1, text2):
    """Calculate similarity ratio between two texts"""
    normalized1 = normalize_text(text1)
    normalized2 = normalize_text(text2)
    
    return SequenceMatcher(None, normalized1, normalized2).ratio()

def find_content_duplicates():
    """Find providers with similar content using text analysis"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("🔍 Advanced Duplicate Detection - Text Similarity Analysis")
    print("=" * 70)
    
    # Get all providers with content
    cursor.execute("""
        SELECT id, provider_name, city, ai_description, ai_excerpt,
               review_summary, english_experience_summary
        FROM providers 
        WHERE ai_description IS NOT NULL 
          AND LENGTH(ai_description) > 100
        ORDER BY id;
    """)
    
    providers = cursor.fetchall()
    print(f"📊 Analyzing {len(providers)} providers for content similarity...")
    
    # Fields to check for duplicates
    fields = [
        ('ai_description', 'AI Description'),
        ('ai_excerpt', 'AI Excerpt'),
        ('review_summary', 'Review Summary'),
        ('english_experience_summary', 'English Experience Summary')
    ]
    
    duplicates_found = {}
    
    for field_name, field_display in fields:
        print(f"\n🔍 Checking {field_display}...")
        
        field_duplicates = []
        checked_pairs = set()
        
        for i, provider1 in enumerate(providers):
            content1 = provider1[field_name]
            if not content1 or len(content1.strip()) < 50:
                continue
                
            similar_providers = []
            
            for j, provider2 in enumerate(providers):
                if i >= j:  # Skip same provider and already checked pairs
                    continue
                    
                content2 = provider2[field_name]
                if not content2 or len(content2.strip()) < 50:
                    continue
                
                # Skip if already checked this pair
                pair_key = tuple(sorted([provider1['id'], provider2['id']]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)
                
                similarity = calculate_similarity(content1, content2)
                
                # Consider 85%+ similarity as potential duplicate
                if similarity >= 0.85:
                    similar_providers.append({
                        'provider': provider2,
                        'similarity': similarity
                    })
            
            if similar_providers:
                field_duplicates.append({
                    'main_provider': provider1,
                    'similar_providers': similar_providers,
                    'content': content1
                })
        
        if field_duplicates:
            duplicates_found[field_name] = field_duplicates
            print(f"⚠️  Found {len(field_duplicates)} potential duplicate groups:")
            print("-" * 70)
            
            for dup_group in field_duplicates:
                main = dup_group['main_provider']
                similars = dup_group['similar_providers']
                
                print(f"\n🔄 Main Provider: ID {main['id']} | {main['provider_name']} | {main['city']}")
                print(f"   Similar providers:")
                
                for similar in similars:
                    sim_provider = similar['provider']
                    similarity_pct = similar['similarity'] * 100
                    print(f"     ID {sim_provider['id']} | {sim_provider['provider_name']:<35} | {sim_provider['city']:<10} | {similarity_pct:.1f}% similar")
                
                # Show content preview
                content_preview = dup_group['content'][:150] + "..."
                print(f"   Content preview: {content_preview}")
                print()
        else:
            print(f"✅ No similar {field_display} found")
    
    cursor.close()
    conn.close()
    return duplicates_found

def check_exact_matches():
    """Check for exact text matches (word-for-word duplicates)"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print(f"\n🔍 Checking for EXACT word-for-word duplicates...")
    print("-" * 70)
    
    fields = [
        ('ai_description', 'AI Description'),
        ('ai_excerpt', 'AI Excerpt'),
        ('review_summary', 'Review Summary'),
        ('english_experience_summary', 'English Experience Summary')
    ]
    
    exact_duplicates = {}
    
    for field_name, field_display in fields:
        # Find exact matches
        query = f"""
        WITH duplicates AS (
            SELECT {field_name}, COUNT(*) as count
            FROM providers 
            WHERE {field_name} IS NOT NULL 
              AND LENGTH({field_name}) > 50
            GROUP BY {field_name}
            HAVING COUNT(*) > 1
        )
        SELECT p.id, p.provider_name, p.city, p.{field_name}, d.count
        FROM providers p
        JOIN duplicates d ON p.{field_name} = d.{field_name}
        ORDER BY d.count DESC, p.provider_name;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        if results:
            exact_duplicates[field_name] = results
            print(f"⚠️  Found {len(results)} providers with exact {field_display} duplicates:")
            print("-" * 70)
            
            current_content = None
            current_count = 0
            
            for result in results:
                if result[field_name] != current_content:
                    current_content = result[field_name]
                    current_count = result['count']
                    print(f"\n🔄 Exact duplicate used by {current_count} providers:")
                    content_preview = current_content[:100] + "..." if len(current_content) > 100 else current_content
                    print(f"   Content: {content_preview}")
                    print("   Providers:")
                
                print(f"     ID {result['id']:>3} | {result['provider_name']:<35} | {result['city']}")
        else:
            print(f"✅ No exact {field_display} duplicates found")
    
    cursor.close()
    conn.close()
    return exact_duplicates

def generate_fix_suggestions(similarity_duplicates, exact_duplicates):
    """Generate suggestions for fixing duplicate content"""
    if not similarity_duplicates and not exact_duplicates:
        print(f"\n✅ No duplicate content detected!")
        return
    
    print(f"\n🛠️  Duplicate Content Fix Recommendations:")
    print("-" * 70)
    
    all_affected_ids = set()
    
    # Collect IDs from similarity duplicates
    for field, dup_groups in similarity_duplicates.items():
        for group in dup_groups:
            all_affected_ids.add(group['main_provider']['id'])
            for similar in group['similar_providers']:
                all_affected_ids.add(similar['provider']['id'])
    
    # Collect IDs from exact duplicates
    for field, duplicates in exact_duplicates.items():
        for dup in duplicates:
            all_affected_ids.add(dup['id'])
    
    if all_affected_ids:
        affected_list = sorted(list(all_affected_ids))
        print(f"1. Regenerate content for {len(affected_list)} providers with duplicate/similar content:")
        print(f"   Provider IDs: {affected_list}")
        print(f"   python3 run_mega_batch_automation.py --limit {len(affected_list)} --dry-run")
        print(f"   python3 run_mega_batch_automation.py --limit {len(affected_list)}")
        
        print(f"\n2. For high-priority fixes, process the most duplicated content first:")
        if exact_duplicates:
            print("   # Focus on exact duplicates first")
        if similarity_duplicates:
            print("   # Then address high-similarity content")
        
        print(f"\n3. After content regeneration, sync to WordPress:")
        print("   python3 wordpress_sync_manager.py --sync-all --limit 25")
        
        print(f"\n4. Process in smaller batches for better control:")
        batch_size = 5
        batches = (len(affected_list) + batch_size - 1) // batch_size
        print(f"   # Process {len(affected_list)} providers in {batches} batches:")
        for i in range(0, len(affected_list), batch_size):
            batch = affected_list[i:i+batch_size]
            batch_num = i // batch_size + 1
            print(f"   # Batch {batch_num}: python3 run_mega_batch_automation.py --limit {len(batch)}")

def main():
    print("🔍 Advanced Duplicate Content Detection")
    print("=" * 70)
    
    # Check for exact matches first
    exact_duplicates = check_exact_matches()
    
    # Check for similar content
    similarity_duplicates = find_content_duplicates()
    
    # Generate fix suggestions
    generate_fix_suggestions(similarity_duplicates, exact_duplicates)
    
    print("\n✅ Advanced duplicate analysis complete!")

if __name__ == "__main__":
    main()