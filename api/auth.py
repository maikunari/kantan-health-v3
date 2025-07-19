"""
Authentication API Blueprint
Simple authentication system for the healthcare directory
"""

from flask import Blueprint, request, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Simple in-memory user store (in production, use database)
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Initialize users from environment or use defaults
users = {}
admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
users['admin'] = User('1', 'admin', generate_password_hash(admin_password))

def init_auth(app):
    """Initialize Flask-Login with the app"""
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        for user in users.values():
            if user.id == user_id:
                return user
        return None

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        user = users.get(username)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout endpoint"""
    logout_user()
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user info"""
    return jsonify({
        'user': {
            'id': current_user.id,
            'username': current_user.username
        }
    }), 200

@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': current_user.id,
                'username': current_user.username
            }
        }), 200
    else:
        return jsonify({'authenticated': False}), 200