#!/usr/bin/env python3
"""
Cleanup Duplicate WordPress Posts
Identifies and removes duplicate healthcare provider posts, keeping only the first one published.
"""

import os
import requests
from collections import defaultdict
from dotenv import load_dotenv
from postgres_integration import PostgresIntegration, Provider

class DuplicateCleanup:
    def __init__(self):
        """Initialize cleanup with WordPress credentials"""
        load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))
        self.wordpress_url = os.getenv('WORDPRESS_URL')
        self.username = os.getenv('WORDPRESS_USERNAME')
        self.application_password = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        self.db = PostgresIntegration()
    
    def get_all_wordpress_posts(self):
        """Get all healthcare provider posts from WordPress"""
        all_posts = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.wordpress_url}/wp-json/wp/v2/healthcare_provider"
            params = {'per_page': per_page, 'page': page}
            
            response = requests.get(url, auth=(self.username, self.application_password), params=params)
            if response.status_code != 200:
                print(f"❌ Error fetching posts: {response.status_code}")
                break
            
            posts = response.json()
            if not posts:
                break
                
            all_posts.extend(posts)
            print(f"📄 Fetched page {page}: {len(posts)} posts")
            page += 1
        
        print(f"📊 Total WordPress posts: {len(all_posts)}")
        return all_posts
    
    def identify_duplicates(self, posts):
        """Identify duplicate posts by provider name and city"""
        provider_posts = defaultdict(list)
        
        for post in posts:
            title = post.get('title', {}).get('rendered', '')
            city = post.get('meta', {}).get('provider_city', '')
            google_place_id = post.get('meta', {}).get('google_place_id', '')
            
            # Group by name and city
            key = f"{title}_{city}"
            provider_posts[key].append({
                'id': post['id'],
                'title': title,
                'city': city,
                'google_place_id': google_place_id,
                'date': post.get('date', ''),
                'post': post
            })
        
        # Find duplicates
        duplicates = {}
        for key, posts_list in provider_posts.items():
            if len(posts_list) > 1:
                # Sort by date to keep the earliest
                posts_list.sort(key=lambda x: x['date'])
                duplicates[key] = {
                    'keep': posts_list[0],
                    'remove': posts_list[1:]
                }
        
        return duplicates
    
    def cleanup_wordpress_duplicates(self, duplicates):
        """Remove duplicate posts from WordPress"""
        removed_count = 0
        
        for key, duplicate_info in duplicates.items():
            keep_post = duplicate_info['keep']
            remove_posts = duplicate_info['remove']
            
            print(f"\n🔄 Processing duplicates for: {keep_post['title']}")
            print(f"✅ Keeping post ID {keep_post['id']} (published: {keep_post['date']})")
            
            for remove_post in remove_posts:
                try:
                    # Delete the duplicate post
                    delete_url = f"{self.wordpress_url}/wp-json/wp/v2/healthcare_provider/{remove_post['id']}"
                    response = requests.delete(delete_url, auth=(self.username, self.application_password))
                    
                    if response.status_code == 200:
                        print(f"🗑️ Deleted duplicate post ID {remove_post['id']}")
                        removed_count += 1
                    else:
                        print(f"❌ Failed to delete post ID {remove_post['id']}: {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error deleting post ID {remove_post['id']}: {str(e)}")
        
        return removed_count
    
    def update_database_records(self, duplicates):
        """Update database records with the correct WordPress post IDs"""
        session = self.db.Session()
        updated_count = 0
        
        try:
            for key, duplicate_info in duplicates.items():
                keep_post = duplicate_info['keep']
                google_place_id = keep_post.get('google_place_id', '')
                wordpress_post_id = keep_post['id']
                
                if google_place_id:
                    # Update all database records with this Google Place ID
                    providers = session.query(Provider).filter(
                        Provider.google_place_id == google_place_id
                    ).all()
                    
                    for provider in providers:
                        provider.wordpress_post_id = wordpress_post_id
                        provider.status = 'published'
                        updated_count += 1
                        print(f"📄 Updated DB record: {provider.provider_name} → WordPress ID {wordpress_post_id}")
                
                session.commit()
                
        except Exception as e:
            print(f"❌ Error updating database: {str(e)}")
            session.rollback()
        finally:
            session.close()
        
        return updated_count
    
    def run_cleanup(self):
        """Main cleanup process"""
        print("🧹 Starting duplicate cleanup process...")
        print("=" * 50)
        
        # Step 1: Get all WordPress posts
        print("📥 Fetching all WordPress posts...")
        posts = self.get_all_wordpress_posts()
        
        # Step 2: Identify duplicates
        print("\n🔍 Identifying duplicates...")
        duplicates = self.identify_duplicates(posts)
        
        if not duplicates:
            print("✅ No duplicates found!")
            return
        
        print(f"⚠️ Found {len(duplicates)} sets of duplicates:")
        for key, duplicate_info in duplicates.items():
            provider_name = duplicate_info['keep']['title']
            duplicate_count = len(duplicate_info['remove'])
            print(f"   - {provider_name}: {duplicate_count} duplicates")
        
        # Step 3: Cleanup WordPress
        confirm = input(f"\n🚨 Delete {sum(len(d['remove']) for d in duplicates.values())} duplicate posts? (y/N): ")
        if confirm.lower() == 'y':
            print("\n🗑️ Removing duplicate WordPress posts...")
            removed_count = self.cleanup_wordpress_duplicates(duplicates)
            print(f"✅ Removed {removed_count} duplicate posts")
            
            # Step 4: Update database
            print("\n📄 Updating database records...")
            updated_count = self.update_database_records(duplicates)
            print(f"✅ Updated {updated_count} database records")
            
            print("\n🎉 Cleanup complete!")
        else:
            print("❌ Cleanup cancelled")

if __name__ == "__main__":
    cleanup = DuplicateCleanup()
    cleanup.run_cleanup() 