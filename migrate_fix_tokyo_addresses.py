#!/usr/bin/env python3
"""
Migration script to fix Tokyo address parsing issues
Corrects providers where district names are incorrectly stored as city names
"""

from postgres_integration import PostgresIntegration, Provider
from datetime import datetime

def fix_tokyo_addresses():
    """Fix providers with incorrect Tokyo address parsing"""
    print("🏢 TOKYO ADDRESS MIGRATION")
    print("=" * 50)
    
    pg = PostgresIntegration()
    session = pg.Session()
    
    try:
        # Find providers with problematic city parsing (City suffix in city field)
        problematic_providers = session.query(Provider).filter(
            Provider.city.like('%City%')
        ).all()
        
        print(f"📊 Found {len(problematic_providers)} providers with incorrect city parsing")
        
        if not problematic_providers:
            print("✅ No providers need fixing")
            return
        
        # Group by type of fix needed
        tokyo_fixes = []
        other_fixes = []
        
        for provider in problematic_providers:
            # Check if this looks like a Tokyo address
            if (provider.prefecture in ['Tokyo', '東京都', 'Tokyo Metropolis'] or 
                'Tokyo' in provider.address):
                tokyo_fixes.append(provider)
            else:
                other_fixes.append(provider)
        
        print(f"🗾 Tokyo providers to fix: {len(tokyo_fixes)}")
        print(f"🏙️ Other providers: {len(other_fixes)}")
        
        # Fix Tokyo providers
        fixed_count = 0
        for provider in tokyo_fixes:
            old_city = provider.city
            old_district = provider.district or "(empty)"
            
            # Apply Tokyo address fix
            if provider.city.endswith(' City'):
                # Move city to district and set city to Tokyo
                new_district = provider.city.replace(' City', '')
                new_city = 'Tokyo'
                
                provider.city = new_city
                provider.district = new_district
                
                print(f"✅ Fixed: {provider.provider_name}")
                print(f"   Old: City='{old_city}', District='{old_district}'")
                print(f"   New: City='{new_city}', District='{new_district}'")
                print(f"   Address: {provider.address}")
                
                fixed_count += 1
        
        # Commit changes
        session.commit()
        
        print(f"\n📈 MIGRATION SUMMARY:")
        print(f"   Tokyo providers fixed: {fixed_count}")
        print(f"   Other providers (need manual review): {len(other_fixes)}")
        
        if other_fixes:
            print(f"\n⚠️ PROVIDERS NEEDING MANUAL REVIEW:")
            for provider in other_fixes[:5]:  # Show first 5
                print(f"   - {provider.provider_name} (City: {provider.city}, Prefecture: {provider.prefecture})")
        
        session.close()
        
        return fixed_count
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        session.rollback()
        session.close()
        return 0

def verify_fixes():
    """Verify that the fixes were applied correctly"""
    print("\n🔍 VERIFICATION")
    print("=" * 30)
    
    pg = PostgresIntegration()
    session = pg.Session()
    
    try:
        # Check for remaining problematic entries
        remaining_issues = session.query(Provider).filter(
            Provider.city.like('%City%')
        ).all()
        
        print(f"Remaining providers with 'City' in city field: {len(remaining_issues)}")
        
        # Check Tokyo providers
        tokyo_providers = session.query(Provider).filter(
            Provider.city == 'Tokyo'
        ).all()
        
        print(f"Providers with city='Tokyo': {len(tokyo_providers)}")
        
        # Show sample of fixed providers
        sample_tokyo = tokyo_providers[:3]
        for provider in sample_tokyo:
            print(f"  ✅ {provider.provider_name}")
            print(f"     City: {provider.city}, District: {provider.district}")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error during verification: {str(e)}")
        session.close()

if __name__ == "__main__":
    print("🚀 Starting Tokyo address migration...")
    
    # Run the migration
    fixed_count = fix_tokyo_addresses()
    
    if fixed_count > 0:
        # Verify the results
        verify_fixes()
        
        print(f"\n🎉 Migration completed successfully!")
        print(f"Fixed {fixed_count} Tokyo addresses")
    else:
        print(f"\n⚠️ No providers were fixed") 