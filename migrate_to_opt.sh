#!/bin/bash

# Script to migrate healthcare directory from home to /opt
# This creates a more professional deployment structure

set -e

REMOTE_USER="deploy"
REMOTE_HOST="206.189.156.138"
NEW_DIR="/opt/healthcare-directory"
OLD_DIR="~"

echo "Healthcare Directory - Migration to /opt"
echo "========================================"
echo ""
echo "This will migrate your application from ~/ to /opt/healthcare-directory"
echo ""

# Check SSH connection
echo "Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 "$REMOTE_USER@$REMOTE_HOST" "echo 'Connected'" > /dev/null 2>&1; then
    echo "❌ Cannot connect to server"
    exit 1
fi

echo "✓ Connected to server"
echo ""

# Perform migration
ssh "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
    set -e
    
    echo "Starting migration process..."
    echo ""
    
    # 1. Create new directory structure
    echo "1. Creating /opt/healthcare-directory..."
    sudo mkdir -p /opt/healthcare-directory
    sudo chown -R deploy:deploy /opt/healthcare-directory
    
    # 2. Copy application files
    echo "2. Copying application files..."
    cd ~
    
    # Copy main directories
    for dir in src scripts utility docs backups config venv; do
        if [ -d "$dir" ]; then
            echo "   Copying $dir..."
            cp -r "$dir" /opt/healthcare-directory/
        fi
    done
    
    # Copy Python files
    echo "   Copying Python files..."
    cp *.py /opt/healthcare-directory/ 2>/dev/null || true
    
    # Copy other important files
    for file in requirements.txt CLAUDE.md .env; do
        if [ -f "$file" ]; then
            echo "   Copying $file..."
            cp "$file" /opt/healthcare-directory/
        fi
    done
    
    # 3. Fix permissions
    echo "3. Setting permissions..."
    cd /opt/healthcare-directory
    chmod -R 755 .
    chmod 600 config/.env 2>/dev/null || true
    
    # Make scripts executable
    find . -name "*.py" -type f -exec chmod +x {} \;
    
    # 4. Create convenience symlink
    echo "4. Creating convenience symlink..."
    ln -sfn /opt/healthcare-directory ~/healthcare_app
    
    # 5. Test the new installation
    echo "5. Testing new installation..."
    cd /opt/healthcare-directory
    
    if [ -d "venv" ]; then
        source venv/bin/activate
        
        # Test imports
        python3 -c "
import sys
sys.path.insert(0, '/opt/healthcare-directory')
try:
    from src.core.database import DatabaseManager
    print('   ✓ Database module OK')
except:
    print('   ⚠ Database module failed')
"
    fi
    
    # 6. Create systemd service file (optional)
    echo "6. Creating systemd service template..."
    sudo tee /opt/healthcare-directory/healthcare-directory.service > /dev/null << 'SERVICE'
[Unit]
Description=Healthcare Directory Pipeline
After=network.target postgresql.service

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/healthcare-directory
Environment="PATH=/opt/healthcare-directory/venv/bin"
ExecStart=/opt/healthcare-directory/venv/bin/python /opt/healthcare-directory/scripts/run_pipeline.py --mode full --limit 100
Restart=on-failure
StandardOutput=append:/opt/healthcare-directory/logs/pipeline.log
StandardError=append:/opt/healthcare-directory/logs/pipeline.error.log

[Install]
WantedBy=multi-user.target
SERVICE
    
    echo ""
    echo "========================================="
    echo "✓ MIGRATION COMPLETED SUCCESSFULLY!"
    echo ""
    echo "New location: /opt/healthcare-directory"
    echo "Convenience symlink: ~/healthcare_app"
    echo ""
    echo "Old files remain in home directory as backup"
    echo "You can remove them later with: rm -rf ~/src ~/scripts ~/utility"
    echo ""
    echo "To use the new location:"
    echo "  cd /opt/healthcare-directory"
    echo "  source venv/bin/activate"
    echo "  python3 scripts/run_pipeline.py --status-only"
    
EOF

echo ""
echo "Migration complete! Your application is now at /opt/healthcare-directory"
echo ""
echo "Next steps:"
echo "1. SSH to server: ssh $REMOTE_USER@$REMOTE_HOST"
echo "2. Go to new location: cd /opt/healthcare-directory"
echo "3. Activate environment: source venv/bin/activate"
echo "4. Test the system: python3 scripts/run_pipeline.py --status-only"