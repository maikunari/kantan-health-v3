#!/bin/bash

# Healthcare Directory - Production Deployment Script
# Deploys updates to /opt/healthcare-directory
# Version: 3.0 - For /opt deployment

set -e  # Exit on error

# Configuration
REMOTE_USER="deploy"
REMOTE_HOST="206.189.156.138"
REMOTE_DIR="/opt/healthcare-directory"
LOCAL_DIR="$(pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Healthcare Directory - Production Deployment${NC}"
echo "=============================================="
echo "Target: $REMOTE_DIR on $REMOTE_HOST"
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
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--dry-run] [--skip-backup] [--skip-deps]"
            exit 1
            ;;
    esac
done

# Verify SSH connection
print_status "Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 "$REMOTE_USER@$REMOTE_HOST" "echo 'Connected'" > /dev/null 2>&1; then
    print_error "Cannot connect to server"
    exit 1
fi

# Step 1: Create backup
if [ "$SKIP_BACKUP" = false ] && [ "$DRY_RUN" = false ]; then
    print_status "Creating backup on server..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
        cd /opt/healthcare-directory
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        # Backup critical files
        for item in src scripts utility *.py; do
            if [ -e "$item" ]; then
                cp -r "$item" "$BACKUP_DIR/" 2>/dev/null || true
            fi
        done
        
        echo "Backup created in $BACKUP_DIR"
EOF
fi

# Step 2: Prepare deployment package
print_status "Preparing deployment package..."

DEPLOY_PACKAGE="deploy_$(date +%Y%m%d_%H%M%S).tar.gz"

if [ "$DRY_RUN" = false ]; then
    # Create package with updated files only
    tar -czf "$DEPLOY_PACKAGE" \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='venv' \
        --exclude='logs' \
        --exclude='config/.env' \
        --exclude='deploy_*.tar.gz' \
        --exclude='backups' \
        src/ \
        scripts/ \
        utility/ \
        docs/ \
        analyze_provider_distribution.py \
        add_specific_provider.py \
        add_geographic_providers.py \
        publish_approved.py \
        CLAUDE.md \
        requirements.txt \
        2>/dev/null || true
    
    print_status "Created package: $DEPLOY_PACKAGE ($(du -h $DEPLOY_PACKAGE | cut -f1))"
fi

# Step 3: Upload and extract
if [ "$DRY_RUN" = false ]; then
    print_status "Uploading to server..."
    scp "$DEPLOY_PACKAGE" "$REMOTE_USER@$REMOTE_HOST:/tmp/"
    
    print_status "Extracting files..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
        cd $REMOTE_DIR
        tar -xzf "/tmp/$DEPLOY_PACKAGE"
        rm "/tmp/$DEPLOY_PACKAGE"
        
        # Set permissions
        find . -name "*.py" -type f -exec chmod +x {} \;
        chmod 600 config/.env
        
        echo "Files extracted and permissions set"
EOF
fi

# Step 4: Update dependencies
if [ "$SKIP_DEPS" = false ] && [ "$DRY_RUN" = false ]; then
    print_status "Updating Python dependencies..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
        cd $REMOTE_DIR
        source venv/bin/activate
        pip install --upgrade pip --quiet
        pip install -r requirements.txt --quiet
        echo "Dependencies updated"
EOF
fi

# Step 5: Run tests
if [ "$DRY_RUN" = false ]; then
    print_status "Running tests..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
        cd /opt/healthcare-directory
        source venv/bin/activate
        
        # Test critical imports
        python3 -c "
from src.collectors.google_places import GooglePlacesCollector
from scripts.generate_taxonomy_content import TaxonomyContentGenerator
print('✓ All imports successful')
"
        
        # Check pipeline status
        python3 scripts/run_pipeline.py --status-only
        
        # Run location fixer
        echo "Checking for missing locations..."
        python3 utility/fix_missing_locations.py --limit 10
EOF
fi

# Clean up
if [ "$DRY_RUN" = false ]; then
    rm -f "$DEPLOY_PACKAGE"
fi

# Summary
echo ""
echo "=============================================="
if [ "$DRY_RUN" = true ]; then
    print_warning "DRY RUN COMPLETED - No changes made"
else
    print_status "DEPLOYMENT SUCCESSFUL!"
    echo ""
    echo "📋 Next Steps:"
    echo ""
    echo "1. Connect to server:"
    echo "   ssh $REMOTE_USER@$REMOTE_HOST"
    echo "   cd /opt/healthcare-directory"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Check provider distribution:"
    echo "   python3 analyze_provider_distribution.py"
    echo ""
    echo "3. Test SEO content generation:"
    echo "   python3 scripts/generate_taxonomy_content.py --mode test --dry-run"
    echo ""
    echo "4. Generate Tier 1 content (5+ providers):"
    echo "   python3 scripts/generate_taxonomy_content.py --mode tier1"
    echo ""
    echo "5. Run optimized collection:"
    echo "   python3 scripts/run_pipeline.py --mode collect --limit 50"
    echo ""
    echo "💡 The exclusion list will prevent duplicate API calls"
    echo "💡 Romanization only applies to English-proficient providers"
    echo "💡 SEO content uses descriptive terms, not exact numbers"
fi