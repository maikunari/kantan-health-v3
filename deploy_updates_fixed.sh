#!/bin/bash

# Healthcare Directory - Server Deployment Script (Fixed for actual server)
# Updates production server with latest code changes
# Version: 2.1 - Corrected for home directory deployment

set -e  # Exit on error

# Configuration
REMOTE_USER="deploy"
REMOTE_HOST="206.189.156.138"
REMOTE_DIR="~"  # Application is in home directory
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
SETUP_VENV=false

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
        --setup-venv)
            SETUP_VENV=true
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
            echo "Usage: $0 [--dry-run] [--skip-backup] [--skip-deps] [--setup-venv] [--host HOST] [--user USER]"
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

# Step 0: Setup virtual environment if needed
if [ "$SETUP_VENV" = true ] && [ "$DRY_RUN" = false ]; then
    print_status "Setting up Python virtual environment on server..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
        # Check if venv exists
        if [ ! -d "venv" ]; then
            echo "Creating virtual environment..."
            python3 -m venv venv
            source venv/bin/activate
            pip install --upgrade pip
            echo "Virtual environment created"
        else
            echo "Virtual environment already exists"
        fi
EOF
fi

# Step 1: Create backup on server
if [ "$SKIP_BACKUP" = false ] && [ "$DRY_RUN" = false ]; then
    print_status "Creating backup on server..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
        cd ~
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        # Backup critical files and directories
        for item in src scripts utility *.py docs CLAUDE.md; do
            if [ -e "$item" ]; then
                cp -r "$item" "$BACKUP_DIR/" 2>/dev/null || true
            fi
        done
        
        # Backup database if pg_dump is available
        if command -v pg_dump &> /dev/null; then
            pg_dump -d directory > "$BACKUP_DIR/database_backup.sql" 2>/dev/null || echo "Database backup skipped (pg_dump failed)"
        else
            echo "Database backup skipped (pg_dump not available)"
        fi
        
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
    # Check which files exist locally before creating tar
    TAR_FILES=""
    for item in src scripts utility docs "*.py" requirements.txt CLAUDE.md .claude analyze_provider_distribution.py; do
        if ls $item 2>/dev/null 1>&2; then
            TAR_FILES="$TAR_FILES $item"
        fi
    done
    
    if [ -n "$TAR_FILES" ]; then
        tar -czf "$DEPLOY_PACKAGE" \
            --exclude='*.pyc' \
            --exclude='__pycache__' \
            --exclude='.git' \
            --exclude='venv' \
            --exclude='logs/*' \
            --exclude='*.log' \
            --exclude='config/.env' \
            --exclude='deploy_package_*.tar.gz' \
            $TAR_FILES
        
        print_status "Created deployment package: $DEPLOY_PACKAGE"
    else
        print_error "No files to deploy!"
        exit 1
    fi
fi

# Step 3: Upload to server
if [ "$DRY_RUN" = false ]; then
    print_status "Uploading files to server..."
    scp "$DEPLOY_PACKAGE" "$REMOTE_USER@$REMOTE_HOST:~/"
    
    # Extract on server
    print_status "Extracting files on server..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << EOF
        cd ~
        tar -xzf "$DEPLOY_PACKAGE"
        rm "$DEPLOY_PACKAGE"
        
        # Set proper permissions
        chmod +x scripts/*.py 2>/dev/null || true
        chmod +x utility/*.py 2>/dev/null || true
        chmod +x utility/migrate/*.py 2>/dev/null || true
        chmod +x *.py 2>/dev/null || true
        
        echo "Files extracted and permissions set"
EOF
fi

# Step 4: Check for virtual environment and update dependencies
if [ "$SKIP_DEPS" = false ] && [ "$DRY_RUN" = false ]; then
    print_status "Checking Python environment on server..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
        cd ~
        
        # Check if venv exists, create if not
        if [ ! -d "venv" ]; then
            echo "Creating virtual environment..."
            python3 -m venv venv
        fi
        
        # Activate and update dependencies
        source venv/bin/activate
        echo "Python version: $(python --version)"
        echo "Pip version: $(pip --version)"
        
        # Upgrade pip first
        pip install --upgrade pip
        
        # Install requirements if file exists
        if [ -f "requirements.txt" ]; then
            echo "Installing requirements..."
            pip install -r requirements.txt
        else
            echo "No requirements.txt found, installing essential packages..."
            pip install psycopg2-binary sqlalchemy python-dotenv requests
        fi
        
        echo "Dependencies updated"
EOF
else
    print_warning "Skipping dependency updates"
fi

# Step 5: Copy environment file if it doesn't exist
if [ "$DRY_RUN" = false ]; then
    print_status "Checking environment configuration..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
        cd ~
        
        # Create config directory if it doesn't exist
        mkdir -p config
        
        # Check if .env exists
        if [ ! -f "config/.env" ]; then
            echo "⚠️  No config/.env file found on server"
            echo "Please create config/.env with your API keys"
        else
            echo "✓ config/.env exists"
        fi
EOF
fi

# Step 6: Run database migrations
if [ "$DRY_RUN" = false ]; then
    print_status "Running database migrations..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
        cd ~
        
        # Check if we can connect to database
        if [ -f "config/.env" ] && [ -d "venv" ]; then
            source venv/bin/activate
            
            # Run migrations if they exist
            for migration in utility/migrate/*.py; do
                if [ -f "$migration" ]; then
                    echo "Running $(basename $migration)..."
                    python3 "$migration" 2>/dev/null || echo "  Migration skipped or already applied"
                fi
            done
            
            echo "Database migrations completed"
        else
            echo "Skipping migrations (missing config/.env or venv)"
        fi
EOF
fi

# Step 7: Test critical components
if [ "$DRY_RUN" = false ]; then
    print_status "Testing critical components..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
        cd ~
        
        if [ -f "config/.env" ] && [ -d "venv" ]; then
            source venv/bin/activate
            
            # Test database connection
            python3 -c "
try:
    from src.core.database import DatabaseManager
    db = DatabaseManager()
    print('✓ Database connection OK')
except Exception as e:
    print(f'✗ Database connection failed: {e}')
" 2>/dev/null || echo "✗ Database test failed"
            
            # Test imports
            python3 -c "
try:
    from src.collectors.google_places import GooglePlacesCollector
    print('✓ Google Places collector OK')
except Exception as e:
    print(f'✗ Google Places import failed: {e}')
" 2>/dev/null || echo "✗ Google Places import failed"
            
            # Check if generate_taxonomy_content.py exists
            if [ -f "scripts/generate_taxonomy_content.py" ]; then
                python3 -c "
try:
    from scripts.generate_taxonomy_content import TaxonomyContentGenerator
    print('✓ SEO generator OK')
except Exception as e:
    print(f'✗ SEO generator import failed: {e}')
" 2>/dev/null || echo "✗ SEO generator import failed"
            fi
            
            # Check pipeline status
            if [ -f "scripts/run_pipeline.py" ]; then
                echo "Checking pipeline status..."
                python3 scripts/run_pipeline.py --status-only 2>/dev/null || echo "Pipeline status check failed"
            fi
        else
            echo "Skipping tests (missing config/.env or venv)"
        fi
EOF
fi

# Step 8: Fix any providers with missing locations
if [ "$DRY_RUN" = false ]; then
    print_status "Checking for providers with missing locations..."
    ssh "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
        cd ~
        
        if [ -f "utility/fix_missing_locations.py" ] && [ -f "config/.env" ] && [ -d "venv" ]; then
            source venv/bin/activate
            
            # Run location fixer with limit
            python3 utility/fix_missing_locations.py --limit 50 2>/dev/null || echo "Location fix skipped"
        else
            echo "Location fixer not available or environment not ready"
        fi
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
    echo "  ./deploy_updates_fixed.sh"
else
    print_status "DEPLOYMENT COMPLETED!"
    echo ""
    echo "⚠️  IMPORTANT: Please check on the server:"
    echo ""
    echo "1. Ensure config/.env exists with your API keys:"
    echo "   ssh $REMOTE_USER@$REMOTE_HOST"
    echo "   cd ~"
    echo "   cat config/.env  # Should show your API keys"
    echo ""
    echo "2. If config/.env is missing, create it:"
    echo "   nano config/.env"
    echo "   # Add your API keys (see local config/.env for reference)"
    echo ""
    echo "3. Test the new features:"
    echo "   source venv/bin/activate"
    echo "   python3 analyze_provider_distribution.py"
    echo "   python3 scripts/generate_taxonomy_content.py --mode test --dry-run"
    echo ""
    echo "4. Generate SEO content:"
    echo "   python3 scripts/generate_taxonomy_content.py --mode tier1"
    echo ""
    echo "5. Run optimized collection:"
    echo "   python3 scripts/run_pipeline.py --mode collect --limit 50"
fi