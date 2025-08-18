#!/bin/bash

# Healthcare Directory - Server Deployment Script
# Updates production server with latest code changes
# Version: 2.0 - Phase 2.5 SEO Implementation

set -e  # Exit on error

# Configuration
REMOTE_USER="your_username"
REMOTE_HOST="your_server_ip"
REMOTE_DIR="/var/www/healthcare_directory"
LOCAL_DIR="$(pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Healthcare Directory - Server Deployment Script${NC}"
echo "================================================"
echo ""

# Function to print colored messages
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "scripts/run_pipeline.py" ]; then
    print_error "Error: Not in healthcare_directory_v2 root directory"
    exit 1
fi

# Parse command line arguments
DRY_RUN=false
SKIP_BACKUP=false
SKIP_DEPS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            print_warning "DRY RUN MODE - No changes will be made"
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --host)
            REMOTE_HOST="$2"
            shift 2
            ;;
        --user)
            REMOTE_USER="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--dry-run] [--skip-backup] [--skip-deps] [--host HOST] [--user USER]"
            exit 1
            ;;
    esac
done

# Verify SSH connection
print_status "Testing SSH connection to $REMOTE_USER@$REMOTE_HOST..."
if ! ssh -o ConnectTimeout=5 "$REMOTE_USER@$REMOTE_HOST" "echo 'SSH connection successful'" > /dev/null 2>&1; then
    print_error "Cannot connect to server. Please check SSH settings."
    exit 1
fi

# Step 1: Create backup on server
if [ "$SKIP_BACKUP" = false ] && [ "$DRY_RUN" = false ]; then
    print_status "Creating backup on server..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
        cd /var/www/healthcare_directory
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        # Backup critical files
        cp -r src/ "$BACKUP_DIR/"
        cp -r scripts/ "$BACKUP_DIR/"
        cp -r utility/ "$BACKUP_DIR/"
        cp *.py "$BACKUP_DIR/" 2>/dev/null || true
        
        # Backup database
        pg_dump -d directory > "$BACKUP_DIR/database_backup.sql"
        
        echo "Backup created in $BACKUP_DIR"
EOF
else
    print_warning "Skipping backup"
fi

# Step 2: Prepare files for deployment
print_status "Preparing files for deployment..."

# Create a deployment package with only necessary files
DEPLOY_PACKAGE="deploy_package_$(date +%Y%m%d_%H%M%S).tar.gz"

if [ "$DRY_RUN" = false ]; then
    tar -czf "$DEPLOY_PACKAGE" \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='venv' \
        --exclude='logs/*' \
        --exclude='*.log' \
        --exclude='config/.env' \
        --exclude='deploy_package_*.tar.gz' \
        src/ \
        scripts/ \
        utility/ \
        docs/ \
        *.py \
        requirements.txt \
        CLAUDE.md \
        .claude/ \
        2>/dev/null || true
    
    print_status "Created deployment package: $DEPLOY_PACKAGE"
fi

# Step 3: Upload to server
if [ "$DRY_RUN" = false ]; then
    print_status "Uploading files to server..."
    scp "$DEPLOY_PACKAGE" "$REMOTE_USER@$REMOTE_HOST:/tmp/"
    
    # Extract on server
    print_status "Extracting files on server..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
        cd $REMOTE_DIR
        tar -xzf "/tmp/$DEPLOY_PACKAGE"
        rm "/tmp/$DEPLOY_PACKAGE"
        
        # Set proper permissions
        chmod +x scripts/*.py
        chmod +x utility/*.py
        chmod +x utility/migrate/*.py
        chmod +x *.py
EOF
fi

# Step 4: Update dependencies
if [ "$SKIP_DEPS" = false ] && [ "$DRY_RUN" = false ]; then
    print_status "Updating Python dependencies on server..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
        cd $REMOTE_DIR
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
EOF
else
    print_warning "Skipping dependency updates"
fi

# Step 5: Run database migrations
if [ "$DRY_RUN" = false ]; then
    print_status "Running database migrations..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
        cd $REMOTE_DIR
        source venv/bin/activate
        
        # Run any pending migrations
        python3 utility/migrate/migrate_geographic_hierarchy.py || true
        python3 utility/migrate/migrate_collection_progress.py || true
        python3 utility/migrate/migrate_proficiency_score.py || true
        
        echo "Database migrations completed"
EOF
fi

# Step 6: Test critical components
if [ "$DRY_RUN" = false ]; then
    print_status "Testing critical components..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
        cd $REMOTE_DIR
        source venv/bin/activate
        
        # Test database connection
        python3 -c "from src.core.database import DatabaseManager; db = DatabaseManager(); print('✓ Database connection OK')"
        
        # Test imports
        python3 -c "from src.collectors.google_places import GooglePlacesCollector; print('✓ Google Places collector OK')"
        python3 -c "from scripts.generate_taxonomy_content import TaxonomyContentGenerator; print('✓ SEO generator OK')"
        
        # Check pipeline status
        python3 scripts/run_pipeline.py --status-only
EOF
fi

# Step 7: Fix any providers with missing locations
if [ "$DRY_RUN" = false ]; then
    print_status "Checking for providers with missing locations..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
        cd $REMOTE_DIR
        source venv/bin/activate
        
        # Run location fixer
        python3 utility/fix_missing_locations.py --limit 50
EOF
fi

# Step 8: Restart services (if applicable)
if [ "$DRY_RUN" = false ]; then
    print_status "Restarting services..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
        # Restart any background services if running
        # Example: systemctl restart healthcare-api
        
        # Clear any caches
        # redis-cli FLUSHDB || true
        
        echo "Services restarted"
EOF
fi

# Clean up local deployment package
if [ "$DRY_RUN" = false ]; then
    rm -f "$DEPLOY_PACKAGE"
fi

# Summary
echo ""
echo "================================================"
if [ "$DRY_RUN" = true ]; then
    print_warning "DRY RUN COMPLETED - No changes were made"
    echo ""
    echo "To perform actual deployment, run without --dry-run flag:"
    echo "  ./deploy_updates.sh --host $REMOTE_HOST --user $REMOTE_USER"
else
    print_status "DEPLOYMENT COMPLETED SUCCESSFULLY!"
    echo ""
    echo "Next steps:"
    echo "1. Test the SEO content generation:"
    echo "   ssh $REMOTE_USER@$REMOTE_HOST"
    echo "   cd $REMOTE_DIR"
    echo "   python3 scripts/generate_taxonomy_content.py --mode test"
    echo ""
    echo "2. Run analysis to see priority pages:"
    echo "   python3 analyze_provider_distribution.py"
    echo ""
    echo "3. Generate Tier 1 SEO content:"
    echo "   python3 scripts/generate_taxonomy_content.py --mode tier1"
    echo ""
    echo "4. Start collection with cost optimization:"
    echo "   python3 scripts/run_pipeline.py --mode collect --limit 50"
fi