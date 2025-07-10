#!/usr/bin/env python3
"""
WordPress Sync Manager - Command Line Interface
Provides comprehensive command-line interface for WordPress sync operations.
"""

import argparse
import sys
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from tabulate import tabulate
from postgres_integration import PostgresIntegration, Provider
from content_hash_service import ContentHashService
from wordpress_update_service import WordPressUpdateService
from sync_management_service import SyncManagementService, SyncOperation, SyncStatus

class WordPressSyncManager:
    """Command-line interface for WordPress sync operations"""
    
    def __init__(self):
        """Initialize the sync manager"""
        self.db = PostgresIntegration()
        self.content_hash_service = ContentHashService()
        self.wordpress_service = WordPressUpdateService()
        self.sync_service = SyncManagementService()
        
        # Color codes for output
        self.colors = {
            'success': '\033[92m',  # Green
            'error': '\033[91m',    # Red
            'warning': '\033[93m',  # Yellow
            'info': '\033[94m',     # Blue
            'bold': '\033[1m',      # Bold
            'end': '\033[0m'        # End formatting
        }
    
    def print_colored(self, text: str, color: str = 'info'):
        """Print colored text"""
        print(f"{self.colors.get(color, '')}{text}{self.colors['end']}")
    
    def print_header(self, title: str):
        """Print formatted header"""
        print("\n" + "=" * 60)
        self.print_colored(f"  {title}", 'bold')
        print("=" * 60)
    
    def sync_provider_by_name(self, provider_name: str, dry_run: bool = False):
        """Sync specific provider by name"""
        self.print_header(f"Syncing Provider: {provider_name}")
        
        session = self.db.Session()
        try:
            provider = session.query(Provider).filter(
                Provider.provider_name.ilike(f'%{provider_name}%')
            ).first()
            
            if not provider:
                self.print_colored(f"❌ Provider '{provider_name}' not found", 'error')
                return False
            
            if not provider.wordpress_post_id:
                self.print_colored(f"❌ Provider '{provider_name}' has no WordPress post ID", 'error')
                return False
            
            # Check if content needs updating
            comparison = self.content_hash_service.compare_content(provider)
            
            if not comparison.needs_update and not dry_run:
                self.print_colored(f"✅ Provider '{provider_name}' is already up to date", 'success')
                return True
            
            # Create sync plan
            plan = self.sync_service.plan_sync_operation(
                SyncOperation.UPDATE_SINGLE,
                filters={'provider_name': provider_name},
                dry_run=dry_run
            )
            
            if not plan.target_providers:
                self.print_colored(f"❌ No providers found for sync", 'error')
                return False
            
            if dry_run:
                self.print_colored(f"🧪 DRY RUN MODE - No changes will be made", 'warning')
                print(f"   Provider: {provider.provider_name}")
                print(f"   WordPress ID: {provider.wordpress_post_id}")
                print(f"   Changes detected: {comparison.changed_fields}")
                return True
            
            # Execute sync
            result = self.sync_service.execute_sync_plan(plan)
            
            if result.status == SyncStatus.SUCCESS:
                self.print_colored(f"✅ Successfully synced {provider.provider_name}", 'success')
                if result.duration:
                    print(f"   Duration: {result.duration} seconds")
                return True
            else:
                self.print_colored(f"❌ Failed to sync {provider.provider_name}", 'error')
                if result.errors:
                    for error in result.errors:
                        print(f"   Error: {error}")
                return False
                
        finally:
            session.close()
    
    def sync_single_provider(self, provider_name: str) -> Dict[str, Any]:
        """Sync a single provider by name - convenience method for external scripts"""
        try:
            success = self.sync_provider_by_name(provider_name, dry_run=False)
            
            if success:
                return {
                    'status': 'success',
                    'message': f'Successfully synced {provider_name} to WordPress'
                }
            else:
                return {
                    'status': 'failed',
                    'message': f'Failed to sync {provider_name} to WordPress'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error syncing {provider_name}: {str(e)}'
            }
    
    def sync_providers_needing_update(self, limit: int = 50, dry_run: bool = False):
        """Sync all providers that need updating"""
        self.print_header("Syncing Providers Needing Updates")
        
        # Create sync plan
        plan = self.sync_service.plan_sync_operation(
            SyncOperation.UPDATE_ALL_STALE,
            filters={'limit': limit},
            dry_run=dry_run
        )
        
        if not plan.target_providers:
            self.print_colored("✅ All WordPress posts are up to date", 'success')
            return True
        
        provider_count = len(plan.target_providers)
        self.print_colored(f"🔄 Found {provider_count} providers needing WordPress updates", 'info')
        
        if dry_run:
            self.print_colored("🧪 DRY RUN MODE - No changes will be made", 'warning')
            print("\nProviders that would be updated:")
            for i, provider in enumerate(plan.target_providers[:10], 1):
                print(f"   {i}. {provider.provider_name} (WordPress ID: {provider.wordpress_post_id})")
            
            if provider_count > 10:
                print(f"   ... and {provider_count - 10} more providers")
            
            return True
        
        # Execute sync
        result = self.sync_service.execute_sync_plan(plan)
        
        # Print results
        self.print_colored(f"\n📊 SYNC RESULTS:", 'bold')
        print(f"   ✅ Success: {result.providers_updated}")
        print(f"   ❌ Failed: {result.providers_failed}")
        print(f"   ⏭️ No changes: {result.providers_no_changes}")
        print(f"   📈 Success Rate: {result.success_rate:.1f}%")
        
        if result.duration:
            print(f"   ⏱️ Duration: {result.duration} seconds")
        
        return result.status == SyncStatus.SUCCESS
    
    def sync_providers_by_city(self, city: str, dry_run: bool = False):
        """Sync providers in specific city"""
        self.print_header(f"Syncing Providers in {city}")
        
        # Create sync plan
        plan = self.sync_service.plan_sync_operation(
            SyncOperation.UPDATE_BY_CITY,
            filters={'city': city},
            dry_run=dry_run
        )
        
        if not plan.target_providers:
            self.print_colored(f"❌ No providers found in {city}", 'error')
            return False
        
        provider_count = len(plan.target_providers)
        self.print_colored(f"🔄 Found {provider_count} providers in {city}", 'info')
        
        if dry_run:
            self.print_colored("🧪 DRY RUN MODE - No changes will be made", 'warning')
            for provider in plan.target_providers:
                print(f"   - {provider.provider_name} (WordPress ID: {provider.wordpress_post_id})")
            return True
        
        # Execute sync
        result = self.sync_service.execute_sync_plan(plan)
        
        # Print results
        self.print_colored(f"\n📊 SYNC RESULTS for {city}:", 'bold')
        print(f"   ✅ Success: {result.providers_updated}")
        print(f"   ❌ Failed: {result.providers_failed}")
        print(f"   ⏭️ No changes: {result.providers_no_changes}")
        print(f"   📈 Success Rate: {result.success_rate:.1f}%")
        
        return result.status == SyncStatus.SUCCESS
    
    def sync_providers_by_specialty(self, specialty: str, dry_run: bool = False):
        """Sync providers by specialty"""
        self.print_header(f"Syncing Providers: {specialty}")
        
        # Create sync plan
        plan = self.sync_service.plan_sync_operation(
            SyncOperation.UPDATE_BY_SPECIALTY,
            filters={'specialty': specialty},
            dry_run=dry_run
        )
        
        if not plan.target_providers:
            self.print_colored(f"❌ No providers found with specialty '{specialty}'", 'error')
            return False
        
        provider_count = len(plan.target_providers)
        self.print_colored(f"🔄 Found {provider_count} providers with specialty '{specialty}'", 'info')
        
        if dry_run:
            self.print_colored("🧪 DRY RUN MODE - No changes will be made", 'warning')
            for provider in plan.target_providers:
                print(f"   - {provider.provider_name} in {provider.city}")
            return True
        
        # Execute sync
        result = self.sync_service.execute_sync_plan(plan)
        
        # Print results
        self.print_colored(f"\n📊 SYNC RESULTS for {specialty}:", 'bold')
        print(f"   ✅ Success: {result.providers_updated}")
        print(f"   ❌ Failed: {result.providers_failed}")
        print(f"   ⏭️ No changes: {result.providers_no_changes}")
        print(f"   📈 Success Rate: {result.success_rate:.1f}%")
        
        return result.status == SyncStatus.SUCCESS
    
    def show_sync_status(self):
        """Show comprehensive sync status"""
        self.print_header("WordPress Sync Status")
        
        # Get statistics
        stats = self.sync_service.get_sync_statistics()
        
        # Provider statistics
        providers_stats = stats.get('providers', {})
        print(f"📊 Provider Statistics:")
        print(f"   Total Providers: {providers_stats.get('total', 0)}")
        print(f"   With WordPress ID: {providers_stats.get('with_wordpress_id', 0)}")
        print(f"   Sync Coverage: {providers_stats.get('sync_coverage', 0):.1f}%")
        
        # Sync performance
        sync_performance = stats.get('sync_performance', {})
        if sync_performance:
            print(f"\n📈 Sync Performance (Last 30 days):")
            for status, data in sync_performance.items():
                print(f"   {status.title()}: {data.get('count', 0)} operations, avg {data.get('avg_duration_ms', 0)}ms")
        
        # Recent activity
        recent_activity = stats.get('recent_activity', {})
        print(f"\n🔄 Recent Activity:")
        print(f"   Syncs (Last 24h): {recent_activity.get('syncs_last_24h', 0)}")
        print(f"   Providers needing update: {recent_activity.get('needs_update', 0)}")
        
        # Get recommendations
        recommendations = self.sync_service.get_sync_recommendations()
        
        if recommendations.get('recommendations'):
            print(f"\n💡 Recommendations:")
            for rec in recommendations['recommendations']:
                priority_color = {
                    'high': 'error',
                    'medium': 'warning',
                    'low': 'info'
                }.get(rec['priority'], 'info')
                
                self.print_colored(f"   [{rec['priority'].upper()}] {rec['description']}", priority_color)
                print(f"      Action: {rec['action']}")
    
    def check_provider_status(self, provider_name: str):
        """Check sync status for specific provider"""
        self.print_header(f"Provider Status: {provider_name}")
        
        session = self.db.Session()
        try:
            provider = session.query(Provider).filter(
                Provider.provider_name.ilike(f'%{provider_name}%')
            ).first()
            
            if not provider:
                self.print_colored(f"❌ Provider '{provider_name}' not found", 'error')
                return
            
            print(f"🏥 Provider: {provider.provider_name}")
            print(f"📍 City: {provider.city}")
            print(f"🆔 WordPress Post ID: {provider.wordpress_post_id or 'Not published'}")
            print(f"📄 Status: {provider.status}")
            print(f"📊 WordPress Status: {provider.wordpress_status or 'Unknown'}")
            
            # Check content hash
            if provider.wordpress_post_id:
                comparison = self.content_hash_service.compare_content(provider)
                
                if comparison.needs_update:
                    self.print_colored(f"⚠️ Content needs updating", 'warning')
                    print(f"   Changed fields: {comparison.changed_fields}")
                else:
                    self.print_colored(f"✅ Content is up to date", 'success')
                
                # Last sync info
                if provider.last_wordpress_sync:
                    last_sync = provider.last_wordpress_sync
                    if isinstance(last_sync, str):
                        last_sync = datetime.fromisoformat(last_sync)
                    
                    time_diff = datetime.now() - last_sync
                    print(f"🕒 Last sync: {last_sync.strftime('%Y-%m-%d %H:%M:%S')} ({time_diff.days} days ago)")
                else:
                    print(f"🕒 Last sync: Never")
            
            # Check if has description
            if provider.ai_description:
                desc_length = len(provider.ai_description)
                print(f"📝 AI Description: {desc_length} characters")
                
                if provider.ai_excerpt:
                    excerpt_length = len(provider.ai_excerpt)
                    print(f"📄 AI Excerpt: {excerpt_length} characters")
            else:
                self.print_colored(f"⚠️ No AI description generated", 'warning')
                
        finally:
            session.close()
    
    def show_sync_history(self, limit: int = 20):
        """Show sync operation history"""
        self.print_header("Sync History")
        
        history = self.sync_service.get_sync_history(limit)
        
        if not history:
            self.print_colored("No sync history found", 'info')
            return
        
        # Format history for table display
        table_data = []
        for entry in history:
            timestamp = entry['timestamp']
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            status_symbol = {
                'success': '✅',
                'failed': '❌',
                'pending': '⏳'
            }.get(entry['status'], '❓')
            
            table_data.append([
                timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                entry['provider_name'],
                entry['city'],
                entry['type'],
                f"{status_symbol} {entry['status']}",
                f"{entry['duration_ms']}ms" if entry['duration_ms'] else 'N/A',
                entry['error'][:50] + '...' if entry['error'] and len(entry['error']) > 50 else entry['error'] or ''
            ])
        
        headers = ['Timestamp', 'Provider', 'City', 'Type', 'Status', 'Duration', 'Error']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def test_wordpress_connection(self):
        """Test WordPress API connection"""
        self.print_header("Testing WordPress Connection")
        
        try:
            # Test connection by attempting to authenticate
            response = self.wordpress_service.session.get(
                f"{self.wordpress_service.wp_base_url}/wp-json/wp/v2/users/me",
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.print_colored(f"✅ WordPress connection successful", 'success')
                print(f"   User: {user_data.get('name', 'Unknown')}")
                print(f"   URL: {self.wordpress_service.wp_base_url}")
                print(f"   Capabilities: {', '.join(user_data.get('capabilities', {}).keys())}")
                return True
            else:
                self.print_colored(f"❌ WordPress connection failed: {response.status_code}", 'error')
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            self.print_colored(f"❌ WordPress connection error: {str(e)}", 'error')
            return False

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="WordPress Sync Manager - Bidirectional content synchronization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync specific provider
  python3 wordpress_sync_manager.py --sync-provider "DENTAL OFFICE OTANI" --dry-run
  
  # Sync all providers needing updates
  python3 wordpress_sync_manager.py --sync-all --limit 20
  
  # Sync providers in a city
  python3 wordpress_sync_manager.py --sync-city "Osaka" --dry-run
  
  # Show sync status
  python3 wordpress_sync_manager.py --status
  
  # Check specific provider
  python3 wordpress_sync_manager.py --check-provider "DENTAL OFFICE OTANI"
        """
    )
    
    # Sync operations
    parser.add_argument("--sync-provider", type=str, help="Sync specific provider by name")
    parser.add_argument("--sync-all", action='store_true', help="Sync all providers needing updates")
    parser.add_argument("--sync-city", type=str, help="Sync providers in specific city")
    parser.add_argument("--sync-specialty", type=str, help="Sync providers with specific specialty")
    
    # Options
    parser.add_argument("--dry-run", action='store_true', help="Show what would be updated without making changes")
    parser.add_argument("--limit", type=int, default=50, help="Limit number of providers to process")
    parser.add_argument("--force", action='store_true', help="Force update even if content appears unchanged")
    
    # Status operations
    parser.add_argument("--status", action='store_true', help="Show sync status for all providers")
    parser.add_argument("--check-provider", type=str, help="Check sync status for specific provider")
    parser.add_argument("--history", action='store_true', help="Show sync operation history")
    parser.add_argument("--test-connection", action='store_true', help="Test WordPress API connection")
    
    args = parser.parse_args()
    
    # Check if any operation is specified
    if not any([
        args.sync_provider, args.sync_all, args.sync_city, args.sync_specialty,
        args.status, args.check_provider, args.history, args.test_connection
    ]):
        parser.print_help()
        sys.exit(1)
    
    # Initialize manager
    try:
        manager = WordPressSyncManager()
    except Exception as e:
        print(f"❌ Failed to initialize sync manager: {str(e)}")
        sys.exit(1)
    
    # Execute operations
    success = True
    
    try:
        if args.test_connection:
            success = manager.test_wordpress_connection()
        elif args.sync_provider:
            success = manager.sync_provider_by_name(args.sync_provider, dry_run=args.dry_run)
        elif args.sync_all:
            success = manager.sync_providers_needing_update(limit=args.limit, dry_run=args.dry_run)
        elif args.sync_city:
            success = manager.sync_providers_by_city(args.sync_city, dry_run=args.dry_run)
        elif args.sync_specialty:
            success = manager.sync_providers_by_specialty(args.sync_specialty, dry_run=args.dry_run)
        elif args.status:
            manager.show_sync_status()
        elif args.check_provider:
            manager.check_provider_status(args.check_provider)
        elif args.history:
            manager.show_sync_history()
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 