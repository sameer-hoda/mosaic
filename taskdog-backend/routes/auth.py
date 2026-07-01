"""
Authentication-related API routes for the TaskDog backend
"""
from flask import Blueprint, request, jsonify
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

bp = Blueprint('auth', __name__, url_prefix='/api')

SECRET_KEY = os.environ.get('SECRET_KEY', 'taskdog-secret-key-change-in-production')

def token_required(f):
    """Decorator to require valid JWT token."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'ok': False, 'error': 'Token is missing'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'ok': False, 'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'ok': False, 'error': 'Token is invalid'}), 401
        
        return f(current_user_id, *args, **kwargs)
    return decorated


@bp.route('/login', methods=['POST'])
def login():
    """Login endpoint to get JWT token."""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'ok': False, 
                'error': 'Username and password are required'
            }), 400
        
        # Get user from database
        from models.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, password_hash FROM users WHERE username = ? OR email = ?', (username, username))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            # Update last login
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
            conn.commit()
            conn.close()
            
            # Generate JWT token
            token = jwt.encode({
                'user_id': user['id'],
                'username': username,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, SECRET_KEY, algorithm='HS256')
            
            return jsonify({
                'ok': True,
                'token': token,
                'user_id': user['id'],
                'username': username
            })
        else:
            return jsonify({
                'ok': False, 
                'error': 'Invalid credentials'
            }), 401
    
    except Exception as e:
        print(f"Error in login: {e}")
        return jsonify({
            'ok': False, 
            'error': str(e)
        }), 500


@bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({
                'ok': False, 
                'error': 'Username, email, and password are required'
            }), 400
        
        # Check if user already exists
        from models.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        existing_user = cursor.fetchone()
        
        if existing_user:
            conn.close()
            return jsonify({
                'ok': False, 
                'error': 'Username or email already exists'
            }), 400
        
        # Create new user
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (username, email, password_hash))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'ok': True,
            'token': token,
            'user_id': user_id,
            'username': username
        })
    
    except Exception as e:
        print(f"Error in register: {e}")
        return jsonify({
            'ok': False, 
            'error': str(e)
        }), 500