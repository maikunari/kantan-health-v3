# Healthcare Directory - Server Deployment Guide

## Overview

This guide covers deploying updates to your production server, including the Phase 2.5 SEO content generation features and all recent optimizations.

## Prerequisites

1. **SSH Access**: Ensure you have SSH access to your server
2. **Server Requirements**:
   - Python 3.12+
   - PostgreSQL database
   - Virtual environment at `/var/www/healthcare_directory/venv`
   - Sufficient disk space for backups

## Quick Deployment

### Using the Automated Script

```bash
# Make script executable
chmod +x deploy_updates.sh

# Run deployment (replace with your actual credentials)
./deploy_updates.sh --host your_server_ip --user your_username

# Test mode (no changes)
./deploy_updates.sh --dry-run --host your_server_ip --user your_username
```

## Manual Deployment Steps

If you prefer manual deployment or the script fails, follow these steps:

### 1. Connect to Server

```bash
ssh your_username@your_server_ip
cd /var/www/healthcare_directory
```

### 2. Create Backup

```bash
# Create backup directory
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup code
cp -r src/ scripts/ utility/ *.py "$BACKUP_DIR/"

# Backup database
pg_dump -d directory > "$BACKUP_DIR/database_backup.sql"

echo "Backup created in $BACKUP_DIR"
```

### 3. Pull Latest Code

If using Git:
```bash
git pull origin main
```

If copying files manually:
```bash
# From your local machine
rsync -avz --exclude='venv' --exclude='logs' --exclude='config/.env' \
  ./ your_username@your_server_ip:/var/www/healthcare_directory/
```

### 4. Update Dependencies

```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Run Database Migrations

```bash
# Check for any schema changes
python3 utility/migrate/migrate_geographic_hierarchy.py
python3 utility/migrate/migrate_collection_progress.py
python3 utility/migrate/migrate_proficiency_score.py
```

### 6. Fix Data Quality Issues

```bash
# Fix providers with missing locations
python3 utility/fix_missing_locations.py

# Analyze current distribution
python3 analyze_provider_distribution.py
```

### 7. Test Critical Components

```bash
# Test database connection
python3 utility/tests/test_db_connection.py

# Test pipeline status
python3 scripts/run_pipeline.py --status-only

# Test SEO content generator
python3 scripts/generate_taxonomy_content.py --mode test --dry-run
```

## Key Changes in This Update

### 1. SEO Content Generation Fixes
- **Removed exact numbers**: Content now uses descriptive terms instead of "8+ doctors"
- **Location filtering**: Providers with unknown locations excluded from SEO analysis
- **Tier-based generation**: Priority system for high-value combinations

### 2. Cost Optimization
- **Exclusion list system**: Filters duplicates before API calls
- **Session rejection tracking**: Prevents re-processing rejected providers
- **Negative result caching**: 30-day cache for rejected providers
- **Expected savings**: 94% reduction in duplicate API calls

### 3. Data Quality Improvements
- **Romanization**: Japanese names converted for English-proficient providers only
- **Location fixing**: New utility to repair missing city data
- **Fingerprint deduplication**: Better duplicate detection

### 4. Updated File Structure

```
healthcare_directory_v2/
├── src/
│   ├── collectors/
│   │   └── google_places.py (UPDATED: exclusion lists, romanization)
│   └── processors/
│       └── ai_content.py (UPDATED: descriptive terms)
├── scripts/
│   ├── generate_taxonomy_content.py (UPDATED: no exact numbers)
│   └── run_pipeline.py (unchanged)
├── utility/
│   └── fix_missing_locations.py (NEW: location repair tool)
├── analyze_provider_distribution.py (UPDATED: exclude unknowns)
└── docs/
    └── TERMINAL_COMMANDS_GUIDE.md (UPDATED: new workflows)
```

## Post-Deployment Testing

### 1. Verify SEO Content Generation

```bash
# Test single page generation
python3 scripts/generate_taxonomy_content.py --mode test

# Check output for descriptive terms (no numbers)
# Should see: "Multiple verified providers" not "8+ doctors"
```

### 2. Test Collection with Exclusions

```bash
# Run small collection test
python3 scripts/run_pipeline.py --mode collect --limit 5 --dry-run

# Check logs for exclusion filtering
grep "Filtered out" logs/pipeline_*.log
```

### 3. Verify Location Fixes

```bash
# Check for providers needing fixes
python3 -c "
from src.core.database import DatabaseManager
from sqlalchemy import text

db = DatabaseManager()
session = db.get_session()
count = session.execute(text(
    'SELECT COUNT(*) FROM providers WHERE city IS NULL OR city = \"\";'
)).scalar()
print(f'Providers with missing city: {count}')
session.close()
"
```

### 4. Test Romanization

```bash
# Check a provider with Japanese name
python3 -c "
from src.collectors.google_places import GooglePlacesCollector
collector = GooglePlacesCollector()

# Test examples
print(collector.extract_romaji_name('日の出薬局 Hinode Pharmacy'))
# Should output: 'Hinode Pharmacy'
"
```

## Production Checklist

- [ ] Backup created successfully
- [ ] Code updated to latest version
- [ ] Dependencies installed/updated
- [ ] Database migrations completed
- [ ] Location data fixed for existing providers
- [ ] SEO content generation tested
- [ ] Collection with exclusions tested
- [ ] API keys verified in config/.env
- [ ] Logs directory writable
- [ ] Cache directory accessible

## Monitoring After Deployment

### Check API Costs

```bash
# View today's API usage
python3 scripts/run_pipeline.py --status-only

# Monitor cost reduction
tail -f logs/pipeline_*.log | grep -E "cost|excluded|filtered"
```

### Monitor SEO Content Generation

```bash
# Watch content generation progress
python3 scripts/generate_taxonomy_content.py --mode tier1

# Check generated content in database
psql -d directory -c "
SELECT taxonomy_type, location, specialty, priority_tier, created_at 
FROM taxonomy_content 
ORDER BY created_at DESC 
LIMIT 10;
"
```

### Track Collection Efficiency

```bash
# View exclusion effectiveness
grep "Filtered out" logs/pipeline_*.log | tail -20

# Check rejection rates
grep "Rejected" logs/pipeline_*.log | wc -l
```

## Rollback Procedure

If issues occur after deployment:

```bash
# 1. Restore code from backup
cd /var/www/healthcare_directory
LATEST_BACKUP=$(ls -t backups/ | head -1)
cp -r "backups/$LATEST_BACKUP/"* ./

# 2. Restore database if needed
psql -d directory < "backups/$LATEST_BACKUP/database_backup.sql"

# 3. Restart services
source venv/bin/activate
python3 scripts/run_pipeline.py --status-only
```

## Security Notes

1. **Never commit `.env` files** to version control
2. **Use SSH keys** instead of passwords for server access
3. **Restrict database access** to localhost only
4. **Regular backups** before any deployment
5. **Test in staging** environment first if available

## Support

For issues or questions:
1. Check logs in `/var/www/healthcare_directory/logs/`
2. Review error messages in systemd journals (if using services)
3. Test individual components as shown above
4. Verify all environment variables are set correctly

## Next Steps After Deployment

1. **Generate Priority SEO Content**:
   ```bash
   python3 scripts/generate_taxonomy_content.py --mode tier1
   ```

2. **Run Optimized Collection**:
   ```bash
   python3 scripts/run_pipeline.py --mode full --limit 100
   ```

3. **Monitor Cost Savings**:
   ```bash
   # Compare before/after API costs
   python3 scripts/run_pipeline.py --status-only
   ```

4. **Publish to WordPress**:
   ```bash
   python3 publish_approved.py --limit 50
   ```

---
Last Updated: 2025-01-26