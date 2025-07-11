#!/usr/bin/env python3
"""
Remove Providers with Unknown English Support
Safely removes providers with english_proficiency='Unknown' from both WordPress and database.

This script:
1. Identifies providers with "Unknown" English proficiency
2. Shows detailed preview of what will be removed
3. Requires explicit confirmation
4. Removes WordPress posts first
5. Removes database records
6. Provides comprehensive logging

Usage:
    python3 utility/cleanup/remove_unknown_english_providers.py --preview
    python3 utility/cleanup/remove_unknown_english_providers.py --execute
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from postgres_integration import PostgresIntegration, Provider
from wordpress_integration import WordPressIntegration

class UnknownEnglishProviderRemover:
    def __init__(self):
        """Initialize database and WordPress connections"""
        self.db = PostgresIntegration()
        self.wp = WordPressIntegration()
        self.session = self.db.Session()
        
    def get_unknown_english_providers(self) -> List[Provider]:
        """Get all providers with Unknown English proficiency"""
        try:
            providers = self.session.query(Provider).filter_by(
                english_proficiency='Unknown'
            ).all()
            
            print(f"🔍 Found {len(providers)} providers with Unknown English proficiency")
            return providers
            
        except Exception as e:
            print(f"❌ Error querying database: {str(e)}")
            return []
    
    def analyze_providers_for_removal(self, providers: List[Provider]) -> Dict[str, Any]:
        """Analyze providers to show what will be removed"""
        analysis = {
            'total_providers': len(providers),
            'with_wordpress_posts': 0,
            'without_wordpress_posts': 0,
            'cities': {},
            'specialties': {},
            'wordpress_post_ids': [],
            'providers_by_city': {}
        }
        
        for provider in providers:
            # WordPress status
            if provider.wordpress_post_id:
                analysis['with_wordpress_posts'] += 1
                analysis['wordpress_post_ids'].append(provider.wordpress_post_id)
            else:
                analysis['without_wordpress_posts'] += 1
            
            # City analysis
            city = provider.city or 'Unknown City'
            analysis['cities'][city] = analysis['cities'].get(city, 0) + 1
            
            if city not in analysis['providers_by_city']:
                analysis['providers_by_city'][city] = []
            analysis['providers_by_city'][city].append({
                'name': provider.provider_name,
                'wordpress_id': provider.wordpress_post_id,
                'specialties': provider.specialties or []
            })
            
            # Specialties analysis
            specialties = provider.specialties or ['Unknown']
            if isinstance(specialties, list):
                for specialty in specialties:
                    analysis['specialties'][specialty] = analysis['specialties'].get(specialty, 0) + 1
            else:
                analysis['specialties'][str(specialties)] = analysis['specialties'].get(str(specialties), 0) + 1
        
        return analysis
    
    def show_removal_preview(self, providers: List[Provider], analysis: Dict[str, Any]):
        """Show detailed preview of what will be removed"""
        print("\n" + "="*80)
        print("🗑️  PROVIDER REMOVAL PREVIEW")
        print("="*80)
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total providers to remove: {analysis['total_providers']}")
        print(f"   With WordPress posts: {analysis['with_wordpress_posts']}")
        print(f"   Without WordPress posts: {analysis['without_wordpress_posts']}")
        
        print(f"\n🏙️  CITIES AFFECTED:")
        for city, count in sorted(analysis['cities'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {city}: {count} providers")
        
        print(f"\n🏥 SPECIALTIES AFFECTED:")
        top_specialties = sorted(analysis['specialties'].items(), key=lambda x: x[1], reverse=True)[:10]
        for specialty, count in top_specialties:
            print(f"   {specialty}: {count} providers")
        
        print(f"\n📝 DETAILED BREAKDOWN BY CITY:")
        for city, city_providers in analysis['providers_by_city'].items():
            print(f"\n   📍 {city} ({len(city_providers)} providers):")
            for provider in city_providers[:5]:  # Show first 5
                wp_status = f"WP:{provider['wordpress_id']}" if provider['wordpress_id'] else "No WP"
                specialties = ', '.join(provider['specialties'][:2]) if provider['specialties'] else 'No specialties'
                print(f"      - {provider['name']} ({wp_status}) - {specialties}")
            if len(city_providers) > 5:
                print(f"      ... and {len(city_providers) - 5} more")
        
        print(f"\n⚠️  IMPACT ANALYSIS:")
        print(f"   WordPress posts to delete: {analysis['with_wordpress_posts']}")
        print(f"   Database records to delete: {analysis['total_providers']}")
        print(f"   Estimated cleanup time: 2-5 minutes")
        
        if analysis['wordpress_post_ids']:
            print(f"\n🔗 WordPress Post IDs (first 10): {analysis['wordpress_post_ids'][:10]}")
            if len(analysis['wordpress_post_ids']) > 10:
                print(f"    ... and {len(analysis['wordpress_post_ids']) - 10} more")
    
    def confirm_removal(self) -> bool:
        """Ask for explicit confirmation before removal"""
        print("\n" + "="*80)
        print("⚠️  CONFIRMATION REQUIRED")
        print("="*80)
        print("This operation will PERMANENTLY delete:")
        print("- 86 WordPress posts")
        print("- 86 database records")
        print("- All associated content and metadata")
        print("\nThis action CANNOT be undone!")
        
        response = input("\nType 'DELETE UNKNOWN PROVIDERS' to confirm removal: ")
        return response == "DELETE UNKNOWN PROVIDERS"
    
    def remove_wordpress_posts(self, providers: List[Provider]) -> Dict[str, int]:
        """Remove WordPress posts for providers"""
        results = {'success': 0, 'failed': 0, 'skipped': 0}
        
        print(f"\n🌐 Starting WordPress post removal...")
        
        for provider in providers:
            if not provider.wordpress_post_id:
                results['skipped'] += 1
                continue
            
            try:
                print(f"🗑️  Removing WP post {provider.wordpress_post_id}: {provider.provider_name}")
                
                # Delete WordPress post
                response = self.wp.delete_post(provider.wordpress_post_id)
                
                if response and response.get('deleted'):
                    results['success'] += 1
                    print(f"   ✅ Deleted WP post {provider.wordpress_post_id}")
                else:
                    results['failed'] += 1
                    print(f"   ❌ Failed to delete WP post {provider.wordpress_post_id}")
                
            except Exception as e:
                results['failed'] += 1
                print(f"   ❌ Error deleting WP post {provider.wordpress_post_id}: {str(e)}")
        
        print(f"\n📊 WordPress removal results:")
        print(f"   ✅ Success: {results['success']}")
        print(f"   ❌ Failed: {results['failed']}")
        print(f"   ⏭️ Skipped (no WP ID): {results['skipped']}")
        
        return results
    
    def remove_database_records(self, providers: List[Provider]) -> Dict[str, int]:
        """Remove database records for providers"""
        results = {'success': 0, 'failed': 0}
        
        print(f"\n🗄️  Starting database record removal...")
        
        try:
            # Delete all providers with Unknown English proficiency
            deleted_count = self.session.query(Provider).filter_by(
                english_proficiency='Unknown'
            ).delete(synchronize_session=False)
            
            self.session.commit()
            
            results['success'] = deleted_count
            print(f"✅ Successfully deleted {deleted_count} database records")
            
        except Exception as e:
            results['failed'] = len(providers)
            self.session.rollback()
            print(f"❌ Error deleting database records: {str(e)}")
        
        return results
    
    def create_removal_log(self, providers: List[Provider], wp_results: Dict, db_results: Dict):
        """Create detailed log of removal operation"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': 'remove_unknown_english_providers',
            'summary': {
                'total_providers': len(providers),
                'wordpress_results': wp_results,
                'database_results': db_results
            },
            'removed_providers': []
        }
        
        for provider in providers:
            log_data['removed_providers'].append({
                'id': provider.id,
                'name': provider.provider_name,
                'city': provider.city,
                'wordpress_post_id': provider.wordpress_post_id,
                'specialties': provider.specialties,
                'english_proficiency': provider.english_proficiency
            })
        
        # Save log file
        log_filename = f"unknown_english_removal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_path = os.path.join('utility', 'cleanup', 'logs', log_filename)
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"📋 Removal log saved to: {log_path}")
        
        return log_path
    
    def execute_removal(self) -> bool:
        """Execute the complete removal process"""
        try:
            # Get providers to remove
            providers = self.get_unknown_english_providers()
            
            if not providers:
                print("✅ No providers with Unknown English proficiency found")
                return True
            
            # Show preview and get confirmation
            analysis = self.analyze_providers_for_removal(providers)
            self.show_removal_preview(providers, analysis)
            
            if not self.confirm_removal():
                print("❌ Operation cancelled by user")
                return False
            
            print(f"\n🚀 Starting removal process for {len(providers)} providers...")
            
            # Remove WordPress posts first
            wp_results = self.remove_wordpress_posts(providers)
            
            # Remove database records
            db_results = self.remove_database_records(providers)
            
            # Create log
            log_path = self.create_removal_log(providers, wp_results, db_results)
            
            # Final summary
            print(f"\n🎉 REMOVAL COMPLETE!")
            print(f"   📊 Total providers processed: {len(providers)}")
            print(f"   🌐 WordPress deletions: {wp_results['success']}/{analysis['with_wordpress_posts']}")
            print(f"   🗄️  Database deletions: {db_results['success']}/{len(providers)}")
            print(f"   📋 Log file: {log_path}")
            
            return wp_results['failed'] == 0 and db_results['failed'] == 0
            
        except Exception as e:
            print(f"❌ Error in removal process: {str(e)}")
            return False
        finally:
            self.session.close()
    
    def preview_only(self):
        """Show preview without executing removal"""
        try:
            providers = self.get_unknown_english_providers()
            
            if not providers:
                print("✅ No providers with Unknown English proficiency found")
                return
            
            analysis = self.analyze_providers_for_removal(providers)
            self.show_removal_preview(providers, analysis)
            
            print(f"\n💡 To execute removal, run:")
            print(f"   python3 utility/cleanup/remove_unknown_english_providers.py --execute")
            
        except Exception as e:
            print(f"❌ Error in preview: {str(e)}")
        finally:
            self.session.close()

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description='Remove providers with Unknown English proficiency')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--preview', action='store_true',
                       help='Show preview of what will be removed without executing')
    group.add_argument('--execute', action='store_true',
                       help='Execute the removal process')
    
    args = parser.parse_args()
    
    print("🗑️  UNKNOWN ENGLISH PROVIDER REMOVAL TOOL")
    print("=" * 60)
    
    remover = UnknownEnglishProviderRemover()
    
    if args.preview:
        remover.preview_only()
    elif args.execute:
        success = remover.execute_removal()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 