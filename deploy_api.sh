#!/bin/bash
# Deploy Flask API to DigitalOcean Droplet

echo "🚀 Deploying Healthcare Directory API..."

# Configuration
DROPLET_IP="206.189.156.138"  
DROPLET_USER="deploy"
REMOTE_DIR="/var/www/healthcare-api"

# Create deployment package
echo "📦 Creating deployment package..."
rm -rf deploy_temp
mkdir -p deploy_temp

# Copy necessary files
cp -r api deploy_temp/
cp -r src deploy_temp/
cp app.py deploy_temp/
cp requirements-api.txt deploy_temp/
cp -r config deploy_temp/  # Contains .env

# Create gunicorn config
cat > deploy_temp/gunicorn_config.py << 'EOF'
bind = "127.0.0.1:8000"
workers = 2
worker_class = "sync"
worker_connections = 100
max_requests = 1000
timeout = 300
keepalive = 2
EOF

# Create systemd service file
cat > deploy_temp/healthcare-api.service << 'EOF'
[Unit]
Description=Healthcare Directory API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/healthcare-api
Environment="PATH=/var/www/healthcare-api/venv/bin"
ExecStart=/var/www/healthcare-api/venv/bin/gunicorn --config gunicorn_config.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create nginx config
cat > deploy_temp/healthcare-api.nginx << 'EOF'
# Healthcare API endpoints
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Longer timeout for photo proxy
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
    
    # Disable buffering for photo streaming
    proxy_buffering off;
    
    # CORS headers (if needed)
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
}
EOF

echo "📤 Uploading to droplet..."
scp -r deploy_temp/* $DROPLET_USER@$DROPLET_IP:~/api-deploy/

echo "✅ Files uploaded. Now SSH into your droplet and run:"
echo "   ssh $DROPLET_USER@$DROPLET_IP"
echo "   cd ~/api-deploy"
echo "   bash setup_api.sh"

# Create remote setup script
cat > deploy_temp/setup_api.sh << 'EOF'
#!/bin/bash
# Run this on the droplet

echo "🔧 Setting up Healthcare API on droplet..."

# Install dependencies
apt update
apt install -y python3-pip python3-venv redis-server

# Create directory
mkdir -p /var/www/healthcare-api
cp -r ~/api-deploy/* /var/www/healthcare-api/

# Create virtual environment
cd /var/www/healthcare-api
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements-api.txt

# Set permissions
chown -R www-data:www-data /var/www/healthcare-api

# Install systemd service
cp healthcare-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable healthcare-api
systemctl start healthcare-api

# Add nginx config
echo "⚠️  Add the contents of healthcare-api.nginx to your WordPress nginx config"
echo "    Usually in: /etc/nginx/sites-available/your-wordpress-site"
echo "    Inside the 'server { ... }' block"

echo "✅ Setup complete! Check status with: systemctl status healthcare-api"
EOF

chmod +x deploy_temp/setup_api.sh