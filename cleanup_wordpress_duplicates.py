#!/usr/bin/env python3
"""
WordPress Duplicate Cleanup Script
Finds and removes duplicate WordPress posts while preserving database integrity
"""

import os
import requests
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv
from postgres_integration import get_postgres_config, Provider
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from collections import defaultdict
from typing import List, Dict, Any

class WordPressDuplicateCleanup:
    def __init__(self):
        """Initialize the cleanup service"""
        # Get WordPress credentials
        config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
        load_dotenv(config_path)
        
        self.wp_url = os.getenv('WORDPRESS_URL', 'https://care-compass.jp')
        self.wp_username = os.getenv('WORDPRESS_USERNAME')
        self.wp_password = os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        
        if not all([self.wp_url, self.wp_username, self.wp_password]):
            raise ValueError("Missing WordPress credentials in .env file")
        
        # Setup database
        config = get_postgres_config()
        self.engine = create_engine(f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}")
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Setup WordPress session
        self.wp_session = requests.Session()
        self.wp_session.auth = (self.wp_username, self.wp_password)
        self.wp_session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Healthcare-Directory-Cleanup/1.0'
        })
    
    def get_all_wordpress_posts(self) -> List[Dict[str, Any]]:
        """Fetch all healthcare provider posts from WordPress"""
        print("🔍 Fetching all WordPress healthcare provider posts...")
        
        all_posts = []
        page = 1
        per_page = 100
        
        while True:
            try:
                response = self.wp_session.get(
                    f"{self.wp_url}/wp-json/wp/v2/healthcare_provider",
                    params={
                        'per_page': per_page,
                        'page': page,
                        'status': 'any'  # Include drafts, published, etc.
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    posts = response.json()
                    if not posts:
                        break
                    
                    all_posts.extend(posts)
                    print(f"   Fetched page {page}: {len(posts)} posts")
                    page += 1
                else:
                    print(f"❌ Failed to fetch WordPress posts: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"❌ Error fetching WordPress posts: {str(e)}")
                break
        
        print(f"📊 Total WordPress posts found: {len(all_posts)}")
        return all_posts
    
    def find_duplicates(self, posts: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Find duplicate posts based on title"""
        print("\n🔍 Analyzing posts for duplicates...")
        
        # Group posts by normalized title
        title_groups = defaultdict(list)
        
        for post in posts:
            # Normalize title for comparison
            title = post['title']['rendered'].strip().lower()
            title_groups[title].append(post)
        
        # Find groups with multiple posts
        duplicates = []
        for title, post_group in title_groups.items():
            if len(post_group) > 1:
                duplicates.append(post_group)
        
        print(f"🔍 Found {len(duplicates)} duplicate groups")
        return duplicates
    
    def analyze_duplicate_group(self, duplicate_group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a group of duplicate posts to determine which to keep"""
        print(f"\n📋 Analyzing duplicate group: '{duplicate_group[0]['title']['rendered']}'")
        
        # Sort by modification date (newest first)
        sorted_posts = sorted(duplicate_group, key=lambda p: p['modified'], reverse=True)
        
        analysis = {
            'title': duplicate_group[0]['title']['rendered'],
            'total_posts': len(duplicate_group),
            'posts': [],
            'recommended_keep': None,
            'recommended_delete': []
        }
        
        for i, post in enumerate(sorted_posts):
            post_info = {
                'wp_id': post['id'],
                'status': post['status'],
                'modified': post['modified'],
                'link': post['link'],
                'content_length': len(post['content']['rendered']),
                'is_newest': i == 0,
                'has_featured_image': post.get('featured_media', 0) > 0
            }
            
            # Check if this post is referenced in our database
            db_provider = self.session.execute(text('''
                SELECT id, provider_name, status
                FROM providers 
                WHERE wordpress_post_id = :wp_id
            '''), {'wp_id': post['id']}).fetchone()
            
            if db_provider:
                post_info['db_provider_id'] = db_provider.id
                post_info['db_provider_name'] = db_provider.provider_name
                post_info['db_status'] = db_provider.status
            else:
                post_info['db_provider_id'] = None
                post_info['db_provider_name'] = None
                post_info['db_status'] = None
            
            analysis['posts'].append(post_info)
            
            print(f"   Post {post['id']}: {post['status']} | Modified: {post['modified']}")
            print(f"   Content: {post_info['content_length']} chars | DB Reference: {post_info['db_provider_id'] or 'None'}")
        
        # Determine which post to keep (priority order):
        # 1. Post with database reference and published status
        # 2. Newest post with database reference
        # 3. Newest published post
        # 4. Newest post overall
        
        keep_post = None
        for post_info in analysis['posts']:
            if post_info['db_provider_id'] and post_info['status'] == 'publish':
                keep_post = post_info
                break
        
        if not keep_post:
            for post_info in analysis['posts']:
                if post_info['db_provider_id']:
                    keep_post = post_info
                    break
        
        if not keep_post:
            for post_info in analysis['posts']:
                if post_info['status'] == 'publish':
                    keep_post = post_info
                    break
        
        if not keep_post:
            keep_post = analysis['posts'][0]  # Newest overall
        
        analysis['recommended_keep'] = keep_post
        analysis['recommended_delete'] = [p for p in analysis['posts'] if p['wp_id'] != keep_post['wp_id']]
        
        print(f"   🎯 Recommended KEEP: Post {keep_post['wp_id']} (DB: {keep_post['db_provider_id'] or 'None'})")
        print(f"   🗑️  Recommended DELETE: {len(analysis['recommended_delete'])} posts")
        
        return analysis
    
    def delete_wordpress_post(self, wp_id: int, dry_run: bool = False) -> bool:
        """Delete a WordPress post"""
        if dry_run:
            print(f"   🧪 DRY RUN: Would delete WordPress post {wp_id}")
            return True
        
        try:
            # First try to trash the post (safer)
            response = self.wp_session.delete(
                f"{self.wp_url}/wp-json/wp/v2/healthcare_provider/{wp_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"   ✅ Moved post {wp_id} to trash")
                return True
            else:
                print(f"   ❌ Failed to delete post {wp_id}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error deleting post {wp_id}: {str(e)}")
            return False
    
    def update_database_references(self, wp_id_to_delete: int, wp_id_to_keep: int, dry_run: bool = False):
        """Update database references from deleted post to kept post"""
        try:
            # Check if there are providers referencing the post to be deleted
            providers_to_update = self.session.execute(text('''
                SELECT id, provider_name
                FROM providers 
                WHERE wordpress_post_id = :wp_id_delete
            '''), {'wp_id_delete': wp_id_to_delete}).fetchall()
            
            if not providers_to_update:
                return
            
            print(f"   🔄 Updating {len(providers_to_update)} database references...")
            
            for provider in providers_to_update:
                if dry_run:
                    print(f"      🧪 DRY RUN: Would update provider {provider.id} ({provider.provider_name})")
                    print(f"         From WordPress ID {wp_id_to_delete} → {wp_id_to_keep}")
                else:
                    self.session.execute(text('''
                        UPDATE providers 
                        SET wordpress_post_id = :wp_id_keep
                        WHERE id = :provider_id
                    '''), {
                        'wp_id_keep': wp_id_to_keep,
                        'provider_id': provider.id
                    })
                    print(f"      ✅ Updated provider {provider.id} ({provider.provider_name})")
            
            if not dry_run:
                self.session.commit()
                
        except Exception as e:
            print(f"   ❌ Error updating database references: {str(e)}")
            if not dry_run:
                self.session.rollback()
    
    def cleanup_duplicates(self, dry_run: bool = False, auto_confirm: bool = False):
        """Main cleanup process"""
        print("🧹 WORDPRESS DUPLICATE CLEANUP")
        print("=" * 60)
        
        # Fetch all posts
        all_posts = self.get_all_wordpress_posts()
        if not all_posts:
            print("❌ No WordPress posts found or failed to fetch")
            return
        
        # Find duplicates
        duplicate_groups = self.find_duplicates(all_posts)
        if not duplicate_groups:
            print("✅ No duplicates found!")
            return
        
        print(f"\n🚨 Found {len(duplicate_groups)} duplicate groups to clean up")
        
        total_deletions = 0
        successful_deletions = 0
        
        for i, duplicate_group in enumerate(duplicate_groups, 1):
            print(f"\n{'='*60}")
            print(f"DUPLICATE GROUP {i}/{len(duplicate_groups)}")
            print(f"{'='*60}")
            
            # Analyze the group
            analysis = self.analyze_duplicate_group(duplicate_group)
            
            if not analysis['recommended_delete']:
                print("   ⏭️ No posts recommended for deletion")
                continue
            
            # Show cleanup plan
            print(f"\n📋 CLEANUP PLAN:")
            print(f"   🎯 KEEP: Post {analysis['recommended_keep']['wp_id']}")
            print(f"   🗑️  DELETE: {len(analysis['recommended_delete'])} duplicate posts")
            
            for post_info in analysis['recommended_delete']:
                print(f"      - Post {post_info['wp_id']} ({post_info['status']}) | DB: {post_info['db_provider_id'] or 'None'}")
            
            # Confirm before proceeding
            if not auto_confirm and not dry_run:
                confirm = input(f"\n   ❓ Proceed with cleanup for '{analysis['title']}'? (y/N): ").lower()
                if confirm != 'y':
                    print("   ⏭️ Skipped by user")
                    continue
            
            # Execute cleanup
            wp_id_to_keep = analysis['recommended_keep']['wp_id']
            
            for post_info in analysis['recommended_delete']:
                wp_id_to_delete = post_info['wp_id']
                total_deletions += 1
                
                # Update database references first
                self.update_database_references(wp_id_to_delete, wp_id_to_keep, dry_run)
                
                # Delete the WordPress post
                if self.delete_wordpress_post(wp_id_to_delete, dry_run):
                    successful_deletions += 1
        
        # Summary
        print(f"\n{'='*60}")
        print(f"🎉 CLEANUP SUMMARY")
        print(f"{'='*60}")
        print(f"   Total duplicate groups: {len(duplicate_groups)}")
        print(f"   Posts processed for deletion: {total_deletions}")
        print(f"   Successfully {'would be ' if dry_run else ''}deleted: {successful_deletions}")
        print(f"   Failed deletions: {total_deletions - successful_deletions}")
        
        if dry_run:
            print(f"\n💡 This was a DRY RUN - no actual changes were made")
            print(f"   Run without --dry-run to execute the cleanup")
        else:
            print(f"\n✅ Cleanup completed!")
            print(f"   Database references updated to prevent orphaned entries")
            print(f"   Check your WordPress admin to verify results")
    
    def close(self):
        """Clean up resources"""
        self.session.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Clean up duplicate WordPress posts")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without making changes')
    parser.add_argument('--auto-confirm', action='store_true', help='Automatically confirm all deletions (use with caution!)')
    
    args = parser.parse_args()
    
    try:
        cleanup = WordPressDuplicateCleanup()
        cleanup.cleanup_duplicates(dry_run=args.dry_run, auto_confirm=args.auto_confirm)
        cleanup.close()
        
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()