import os
from functools import wraps
from flask import request, jsonify
import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "1234")

def token_required(f):
    """
    Decorator to protect routes that require authentication.
    Usage: @token_required before any route function
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                # Extract token (format: "Bearer <token>")
                parts = auth_header.split()
                if len(parts) == 2 and parts[0].lower() == 'bearer':
                    token = parts[1]
            except IndexError:
                return jsonify({"error": "Invalid token format"}), 401
        
        if not token:
            return jsonify({"error": "Authentication token is required"}), 401
        
        try:
            # Decode and verify token
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.current_user = payload  # Attach user info to request
            
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            print(f"Token verification error: {e}")
            return jsonify({"error": "Token verification failed"}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def optional_token(f):
    """
    Decorator for routes where authentication is optional.
    If token is provided and valid, user info is attached to request.
    If not, the route continues without user info.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                parts = auth_header.split()
                if len(parts) == 2 and parts[0].lower() == 'bearer':
                    token = parts[1]
            except IndexError:
                pass
        
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                request.current_user = payload
            except:
                request.current_user = None
        else:
            request.current_user = None
        
        return f(*args, **kwargs)
    
    return decorated
