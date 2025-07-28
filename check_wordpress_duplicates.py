#!/usr/bin/env python3
"""
Check WordPress Duplicates
Checks for duplicate WordPress posts that may have been created by the buggy publish_approved.py script
"""

import os
import requests
import sys
from dotenv import load_dotenv
from postgres_integration import get_postgres_config, Provider
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from collections import defaultdict

def get_wordpress_credentials():
    """Get WordPress credentials from environment"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
    load_dotenv(config_path)
    
    return {
        'url': os.getenv('WORDPRESS_URL', 'https://care-compass.jp'),
        'username': os.getenv('WORDPRESS_USERNAME'),
        'password': os.getenv('WORDPRESS_APPLICATION_PASSWORD')
    }

def check_wordpress_duplicates():
    """Check for duplicate WordPress posts"""
    print("🔍 CHECKING FOR WORDPRESS DUPLICATES")
    print("=" * 60)
    
    # Get database connection
    config = get_postgres_config()
    engine = create_engine(f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get WordPress credentials
    wp_creds = get_wordpress_credentials()
    if not all([wp_creds['url'], wp_creds['username'], wp_creds['password']]):
        print("❌ Missing WordPress credentials in .env file")
        return
    
    # Get all providers with WordPress post IDs
    providers = session.execute(text('''
        SELECT id, provider_name, wordpress_post_id, status, primary_fingerprint
        FROM providers 
        WHERE wordpress_post_id IS NOT NULL
        ORDER BY wordpress_post_id
    ''')).fetchall()
    
    print(f"📊 Found {len(providers)} providers with WordPress post IDs in database")
    
    # Group by fingerprint to find potential duplicates
    fingerprint_groups = defaultdict(list)
    for provider in providers:
        if provider.primary_fingerprint:
            fingerprint_groups[provider.primary_fingerprint].append(provider)
    
    # Find potential duplicates based on fingerprints
    potential_duplicates = []
    for fingerprint, provider_group in fingerprint_groups.items():
        if len(provider_group) > 1:
            potential_duplicates.append(provider_group)
    
    if potential_duplicates:
        print(f"\n🚨 Found {len(potential_duplicates)} potential duplicate groups based on fingerprints:")
        print("-" * 60)
        
        for i, group in enumerate(potential_duplicates, 1):
            print(f"\nGroup {i} (Fingerprint: {group[0].primary_fingerprint[:16]}...):")
            for provider in group:
                print(f"  ID {provider.id}: {provider.provider_name}")
                print(f"    WordPress ID: {provider.wordpress_post_id}, Status: {provider.status}")
    else:
        print("✅ No fingerprint-based duplicates found in database")
    
    # Check WordPress directly for posts with same titles
    print(f"\n🔍 CHECKING WORDPRESS DIRECTLY FOR DUPLICATE TITLES")
    print("-" * 60)
    
    try:
        # Get all healthcare provider posts from WordPress
        response = requests.get(
            f"{wp_creds['url']}/wp-json/wp/v2/healthcare_provider",
            auth=(wp_creds['username'], wp_creds['password']),
            params={'per_page': 100}  # Adjust if you have more than 100 posts
        )
        
        if response.status_code == 200:
            wp_posts = response.json()
            print(f"📊 Found {len(wp_posts)} healthcare provider posts in WordPress")
            
            # Group by title to find duplicates
            title_groups = defaultdict(list)
            for post in wp_posts:
                title = post['title']['rendered'].strip()
                title_groups[title].append(post)
            
            wp_duplicates = []
            for title, post_group in title_groups.items():
                if len(post_group) > 1:
                    wp_duplicates.append((title, post_group))
            
            if wp_duplicates:
                print(f"\n🚨 Found {len(wp_duplicates)} duplicate titles in WordPress:")
                print("-" * 60)
                
                for title, posts in wp_duplicates:
                    print(f"\nDuplicate: '{title}'")
                    for post in posts:
                        print(f"  WordPress ID: {post['id']}, Status: {post['status']}")
                        print(f"  URL: {post['link']}")
                        print(f"  Modified: {post['modified']}")
                
                print(f"\n⚠️  RECOMMENDED ACTIONS:")
                print(f"   1. Review duplicates in WordPress admin")
                print(f"   2. Keep the most recent/complete post")
                print(f"   3. Delete older duplicate posts")
                print(f"   4. Update database to remove wordpress_post_id for deleted posts")
                
            else:
                print("✅ No duplicate titles found in WordPress")
                
        else:
            print(f"❌ Failed to fetch WordPress posts: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking WordPress: {str(e)}")
    
    session.close()

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Usage: python3 check_wordpress_duplicates.py")
        print("Checks for duplicate WordPress posts that may have been created")
        return
    
    check_wordpress_duplicates()

if __name__ == "__main__":
    main()