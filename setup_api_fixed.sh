#!/bin/bash
# Run this on the droplet as deploy user

echo "🔧 Setting up Healthcare API on droplet..."

# Install dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv redis-server

# Create directory
sudo mkdir -p /var/www/healthcare-api
sudo cp -r ~/api-deploy/* /var/www/healthcare-api/

# Create virtual environment
cd /var/www/healthcare-api
sudo python3 -m venv venv
sudo chown -R deploy:www-data /var/www/healthcare-api

# Activate venv and install packages
source venv/bin/activate
pip install -r requirements-api.txt

# Set final permissions
sudo chown -R www-data:www-data /var/www/healthcare-api
sudo chmod -R 755 /var/www/healthcare-api

# Install systemd service
sudo cp healthcare-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable healthcare-api
sudo systemctl start healthcare-api

# Add nginx config
echo ""
echo "⚠️  Now add the API location to nginx:"
echo "  1. sudo nano /etc/nginx/sites-available/kantanhealth.jp"
echo "  2. Find the server block with SSL (port 443)"
echo "  3. Add the contents from healthcare-api.nginx"
echo "  4. sudo nginx -t"
echo "  5. sudo systemctl reload nginx"
echo ""
echo "✅ Check API status with: sudo systemctl status healthcare-api"
