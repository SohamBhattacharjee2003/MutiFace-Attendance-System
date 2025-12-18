# Authentication System Documentation

## Overview
This authentication system provides secure user registration and login functionality using JWT tokens and bcrypt password hashing.

## Backend Setup

### 1. Install Dependencies
```bash
cd Backend
pip install -r requirements.txt
```

The following packages are required for authentication:
- `bcrypt` - For secure password hashing
- `pyjwt` - For JWT token generation and verification

### 2. Environment Variables
Make sure your `.env` file contains:
```
MONGO_URI=mongodb://127.0.0.1:27017
FLASK_SECRET_KEY=your-secret-key-here  # Change this to a secure random string
```

### 3. API Endpoints

#### Signup
- **URL**: `POST /api/auth/signup`
- **Body**:
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "password123"
}
```
- **Response**:
```json
{
  "message": "User created successfully",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "60f7b3b3e7b3a732e8b4567a",
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

#### Login
- **URL**: `POST /api/auth/login`
- **Body**:
```json
{
  "email": "john@example.com",
  "password": "password123"
}
```
- **Response**:
```json
{
  "message": "Login successful",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "60f7b3b3e7b3a732e8b4567a",
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

#### Verify Token
- **URL**: `GET /api/auth/verify`
- **Headers**: `Authorization: Bearer <token>`
- **Response**:
```json
{
  "valid": true,
  "user": {
    "id": "60f7b3b3e7b3a732e8b4567a",
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

#### Get Current User
- **URL**: `GET /api/auth/me`
- **Headers**: `Authorization: Bearer <token>`
- **Response**:
```json
{
  "user": {
    "id": "60f7b3b3e7b3a732e8b4567a",
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2024-12-18T10:30:00Z"
  }
}
```

## Frontend Integration

### 1. API Functions
The following functions are available in `src/utils/api.js`:

- `signup(name, email, password)` - Register a new user
- `login(email, password)` - Login existing user
- `verifyToken()` - Verify if current token is valid
- `getCurrentUser()` - Get current user details
- `logout()` - Logout and clear local storage

### 2. Token Storage
Tokens are automatically stored in `localStorage` upon successful login/signup:
- `token` - JWT token
- `user` - User object (id, name, email)

### 3. Making Authenticated Requests
To make authenticated requests, include the token in the Authorization header:
```javascript
const token = localStorage.getItem("token");
fetch(`${API_URL}/some-protected-route`, {
  headers: {
    "Authorization": `Bearer ${token}`
  }
});
```

## Security Features

1. **Password Hashing**: Passwords are hashed using bcrypt with automatic salt generation
2. **JWT Tokens**: Secure token-based authentication with 7-day expiration
3. **Email Validation**: Email format validation on signup
4. **Password Requirements**: Minimum 6 characters
5. **Token Verification**: Middleware to protect routes requiring authentication

## Protecting Backend Routes

To protect a route, use the `@token_required` decorator:

```python
from middleware.auth_middleware import token_required

@app.route("/protected-route", methods=["GET"])
@token_required
def protected_route():
    # Access current user via request.current_user
    user_id = request.current_user['user_id']
    email = request.current_user['email']
    return jsonify({"message": "Access granted!"})
```

For optional authentication (route works with or without token):
```python
from middleware.auth_middleware import optional_token

@app.route("/optional-auth-route", methods=["GET"])
@optional_token
def optional_route():
    if request.current_user:
        # User is authenticated
        user_id = request.current_user['user_id']
    else:
        # User is not authenticated
        pass
    return jsonify({"message": "Works either way!"})
```

## Database Schema

### Users Collection
```javascript
{
  "_id": ObjectId,
  "name": String,
  "email": String,          // unique, lowercase
  "password": Binary,       // bcrypt hashed
  "created_at": DateTime,
  "updated_at": DateTime
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200` - Success
- `201` - Created (signup)
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid credentials or token)
- `404` - Not Found
- `409` - Conflict (user already exists)
- `500` - Internal Server Error

Error responses format:
```json
{
  "error": "Error message describing what went wrong"
}
```

## Testing

### Using curl
```bash
# Signup
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"password123"}'

# Verify Token (replace TOKEN with actual token)
curl -X GET http://localhost:5000/api/auth/verify \
  -H "Authorization: Bearer TOKEN"
```

## Running the Application

1. Start MongoDB (if not already running)
2. Start the backend server:
```bash
cd Backend
python app.py
```
3. Start the frontend:
```bash
cd Frontend
npm run dev
```

The frontend login page will now be fully functional with backend authentication!
