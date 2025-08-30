#!/bin/bash

# Install required dependencies for the campaign
echo "Installing required dependencies..."

# Core dependencies
pip install python-dotenv
pip install sqlalchemy
pip install psycopg2-binary
pip install requests
pip install googlemaps
pip install anthropic
pip install pandas
pip install cutlet
pip install pytz
pip install python-dateutil

# Google Cloud monitoring (optional but recommended)
pip install google-cloud-monitoring
pip install google-cloud-billing

echo "Dependencies installed successfully!"
echo ""
echo "You can now run:"
echo "  python3 src/campaign/enhanced_pipeline.py --test"