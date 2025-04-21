from flask import Blueprint, request, jsonify, make_response, current_app
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from app.models import User, db
from argon2 import PasswordHasher
from datetime import timedelta
import redis
import os
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Initialize PasswordHasher
ph = PasswordHasher()

# Redis client will be initialized during request
redis_client = None

# Initialize and return Redis client for token blacklisting
def get_redis_client():
    global redis_client
    if redis_client is None:
        try:
            redis_url = current_app.config.get('REDIS_URL', os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
            redis_client = redis.from_url(redis_url)
        except redis.exceptions.ConnectionError:
            logger.warning("Redis connection failed - token blacklisting won't work")
            redis_client = None
    return redis_client

# Add security headers to all auth blueprint responses
@auth_bp.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

# Register a new user with hashed password
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    # Check if user exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    user = User(username=data['username'], password_hash=ph.hash(data['password']))
    db.session.add(user)
    db.session.commit()
    
    # EXPLICITLY create response with status code
    response = jsonify({
        'message': 'User created successfully',
        'user_id': user.id
    })
    response.status_code = 201  # Force the status code
    return response

# Authenticate user and return JWT access token
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()
    
    try:
        if not user or not ph.verify(user.password_hash, data.get('password', '')):
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=str(user.id))
    return jsonify(access_token=access_token), 200

# Generate new access token using refresh token
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify(access_token=access_token), 200

#Invalidate current token by adding to blacklist in Redis
@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    redis = get_redis_client()
    # Only blacklist if Redis is available
    if redis:
        # Store the JTI in Redis with an expiry matching token lifetime
        redis.setex(jti, timedelta(hours=1), 'revoked')
    return jsonify(message="Successfully logged out"), 200