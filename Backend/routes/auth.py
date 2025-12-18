import os
import re
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import bcrypt
import jwt

load_dotenv()

auth_bp = Blueprint("auth", __name__)

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "1234")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["attendance_db"]
    users_col = db["users"]
    print("✅ MongoDB connected in auth route")
except Exception as e:
    print(f"❌ MongoDB connection failed in auth route: {e}")
    client = None
    users_col = None

# Helper function to validate email
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Helper function to generate JWT token
def generate_token(user_id, email):
    payload = {
        'user_id': str(user_id),
        'email': email,
        'exp': datetime.now(timezone.utc) + timedelta(days=7),  # Token expires in 7 days
        'iat': datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

# Signup Route
@auth_bp.route("/signup", methods=["POST"])
def signup():
    if users_col is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        data = request.get_json()
        
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        # Validation
        if not name:
            return jsonify({"error": "Name is required"}), 400
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        if not is_valid_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        if not password:
            return jsonify({"error": "Password is required"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters long"}), 400
        
        # Check if user already exists
        existing_user = users_col.find_one({"email": email})
        if existing_user:
            return jsonify({"error": "User with this email already exists"}), 409
        
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user document
        user_doc = {
            "name": name,
            "email": email,
            "password": hashed_password,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Insert user into database
        result = users_col.insert_one(user_doc)
        user_id = result.inserted_id
        
        # Generate JWT token
        token = generate_token(user_id, email)
        
        return jsonify({
            "message": "User created successfully",
            "token": token,
            "user": {
                "id": str(user_id),
                "name": name,
                "email": email
            }
        }), 201
        
    except Exception as e:
        print(f"Error in signup: {e}")
        return jsonify({"error": "An error occurred during signup"}), 500

# Login Route
@auth_bp.route("/login", methods=["POST"])
def login():
    if users_col is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        data = request.get_json()
        
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        # Validation
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        if not password:
            return jsonify({"error": "Password is required"}), 400
        
        # Find user by email
        user = users_col.find_one({"email": email})
        
        if not user:
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Check password
        if not bcrypt.checkpw(password.encode('utf-8'), user["password"]):
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Generate JWT token
        token = generate_token(user["_id"], email)
        
        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": str(user["_id"]),
                "name": user["name"],
                "email": user["email"]
            }
        }), 200
        
    except Exception as e:
        print(f"Error in login: {e}")
        return jsonify({"error": "An error occurred during login"}), 500

# Verify Token Route (optional - to check if token is still valid)
@auth_bp.route("/verify", methods=["GET"])
def verify_token():
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({"error": "No token provided"}), 401
        
        # Extract token (format: "Bearer <token>")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({"error": "Invalid token format"}), 401
        
        token = parts[1]
        
        # Verify token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            
            # Get user from database
            user = users_col.find_one({"email": payload['email']})
            
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            return jsonify({
                "valid": True,
                "user": {
                    "id": str(user["_id"]),
                    "name": user["name"],
                    "email": user["email"]
                }
            }), 200
            
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
            
    except Exception as e:
        print(f"Error in verify token: {e}")
        return jsonify({"error": "An error occurred during token verification"}), 500

# Get Current User Route
@auth_bp.route("/me", methods=["GET"])
def get_current_user():
    if users_col is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({"error": "No token provided"}), 401
        
        # Extract token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({"error": "Invalid token format"}), 401
        
        token = parts[1]
        
        # Verify token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            
            # Get user from database
            user = users_col.find_one({"email": payload['email']})
            
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            return jsonify({
                "user": {
                    "id": str(user["_id"]),
                    "name": user["name"],
                    "email": user["email"],
                    "created_at": user.get("created_at").isoformat() if user.get("created_at") else None
                }
            }), 200
            
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
            
    except Exception as e:
        print(f"Error in get current user: {e}")
        return jsonify({"error": "An error occurred"}), 500
