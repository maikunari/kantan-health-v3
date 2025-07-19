#!/usr/bin/env python3
"""
Healthcare Directory v2 - Main Flask Application
A comprehensive web interface for managing healthcare provider data
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/.env')

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
db_user = os.getenv('POSTGRES_USER', 'postgres')
db_pass = os.getenv('POSTGRES_PASSWORD', 'password')
db_host = os.getenv('POSTGRES_HOST', 'localhost')
db_name = os.getenv('POSTGRES_DB', 'directory')

app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{db_user}:{db_pass}@{db_host}:5432/{db_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import and register blueprints
from api.providers import providers_bp
from api.dashboard import dashboard_bp
from api.content_generation import content_bp
from api.wordpress_sync import sync_bp
from api.auth import auth_bp, init_auth

# Initialize authentication
init_auth(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(providers_bp, url_prefix='/api/providers')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(content_bp, url_prefix='/api/content')
app.register_blueprint(sync_bp, url_prefix='/api/sync')

@app.route('/')
def index():
    return jsonify({
        'name': 'Healthcare Directory v2 API',
        'version': '2.0',
        'endpoints': {
            'providers': '/api/providers',
            'dashboard': '/api/dashboard',
            'content': '/api/content',
            'sync': '/api/sync'
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)