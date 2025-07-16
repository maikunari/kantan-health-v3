#!/bin/bash
# Fix Content Issues - Healthcare Directory
# Run these commands to fix the identified content problems

echo "🔧 Fixing Content Issues - Healthcare Directory"
echo "=============================================="

echo ""
echo "1. Fix providers with missing descriptions on WordPress:"
echo "--------------------------------------------------------"

# Force sync the 5 providers with missing WordPress descriptions
python3 wordpress_sync_manager.py --sync-provider "Hirayama ENT Clinic" --force
python3 wordpress_sync_manager.py --sync-provider "Japanese Red Cross Medical Center" --force  
python3 wordpress_sync_manager.py --sync-provider "Matsugaoka Otolaryngologist" --force
python3 wordpress_sync_manager.py --sync-provider "The Jikei University Hospital" --force
python3 wordpress_sync_manager.py --sync-provider "Tokyo Medical and Dental University Hospital" --force

echo ""
echo "2. Fix content mismatches with bulk sync:"
echo "----------------------------------------"

# Sync all providers with content mismatches (process in batches)
python3 wordpress_sync_manager.py --sync-all --force --limit 30

echo ""
echo "3. Complete remaining sync operations:"
echo "-----------------------------------"

# Continue syncing remaining providers
python3 wordpress_sync_manager.py --sync-all --force --limit 30

echo ""
echo "4. Verify fixes:"
echo "---------------"

# Check the status after fixes
python3 wordpress_sync_manager.py --status

echo ""
echo "✅ Content fix process complete!"
echo ""
echo "📊 To verify the fixes worked, run:"
echo "   python3 check_wordpress_content.py --wordpress-only"