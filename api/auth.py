"""
Authentication API Blueprint
Simple authentication system for the healthcare directory
"""

from flask import Blueprint, request, jsonify, session
import os
import functools
import logging
import hashlib

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def simple_hash(password):
    """Simple password hashing for development"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(stored_hash, password):
    """Check password against stored hash"""
    return stored_hash == simple_hash(password)

# Simple session-based authentication
users = {
    'admin': {
        'id': '1',
        'username': 'admin',
        'password_hash': simple_hash(os.getenv('ADMIN_PASSWORD', 'admin123'))
    }
}

def login_required(f):
    """Decorator to require authentication"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def init_auth(app):
    """Initialize authentication with the app"""
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

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
        if user and check_password(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user['id'],
                    'username': user['username']
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
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user info"""
    return jsonify({
        'user': {
            'id': session['user_id'],
            'username': session['username']
        }
    }), 200

@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'username': session['username']
            }
        }), 200
    else:
        return jsonify({'authenticated': False}), 200