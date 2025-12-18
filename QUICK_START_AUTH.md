# Quick Start Guide - Authentication Setup

## 🚀 Quick Setup

### 1. Install Backend Dependencies
```bash
cd Backend
pip install bcrypt pyjwt
```

### 2. Set Environment Variables
Create or update `.env` file in Backend folder:
```
MONGO_URI=mongodb://127.0.0.1:27017
FLASK_SECRET_KEY=your-super-secret-key-change-this
```

### 3. Start Backend Server
```bash
cd Backend
python app.py
```

Backend will run on: http://localhost:5000

### 4. Start Frontend
```bash
cd Frontend
npm install  # if not already done
npm run dev
```

Frontend will run on: http://localhost:5173

## 🎯 Test Authentication

### Test Signup
1. Open http://localhost:5173/login
2. Click "Signup" tab
3. Fill in:
   - Full Name: Test User
   - Email: test@example.com
   - Password: password123
4. Click "Create Account"
5. You should be redirected to dashboard (if route exists)

### Test Login
1. Click "Login" tab
2. Fill in:
   - Email: test@example.com
   - Password: password123
3. Click "Login"
4. You should be redirected to dashboard

## 📝 What Was Added

### Backend Files
- ✅ `routes/auth.py` - Authentication endpoints (signup, login, verify, me)
- ✅ `middleware/auth_middleware.py` - Token verification decorators
- ✅ Updated `app.py` - Registered auth blueprint
- ✅ Updated `requirements.txt` - Added bcrypt and pyjwt

### Frontend Files
- ✅ Updated `utils/api.js` - Added auth API functions
- ✅ Updated `pages/Login.jsx` - Connected to backend auth
- ✅ Created `utils/auth.js` - Auth helpers and ProtectedRoute component

## 🔒 Protecting Routes

### Backend Example
```python
from middleware.auth_middleware import token_required

@app.route("/api/protected", methods=["GET"])
@token_required
def protected_endpoint():
    user_id = request.current_user['user_id']
    return jsonify({"message": f"Hello user {user_id}"})
```

### Frontend Example
```jsx
import { ProtectedRoute } from './utils/auth';

// In your router
<Route 
  path="/dashboard" 
  element={
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  } 
/>
```

## 🧪 Test with curl

```bash
# Signup
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

## ✨ Features Included

- ✅ User registration with email validation
- ✅ Secure password hashing with bcrypt
- ✅ JWT token-based authentication
- ✅ Token expiration (7 days)
- ✅ Protected routes with middleware
- ✅ Frontend token storage in localStorage
- ✅ Automatic login/signup redirection
- ✅ Error handling and validation
- ✅ Loading states in UI

## 🎨 UI Features

- Beautiful animated login/signup forms
- Error message display
- Loading states on buttons
- Form validation
- Smooth transitions between login/signup

## 🗄️ Database

A new `users` collection will be created in MongoDB with:
- name
- email (unique, lowercase)
- password (bcrypt hashed)
- created_at
- updated_at

## 📚 Next Steps

1. **Protect existing routes** - Add `@token_required` to routes that need authentication
2. **Add user profile** - Create user profile page showing user info
3. **Add logout button** - Import and use `logout()` from `utils/api.js`
4. **Customize redirects** - Change redirect paths in Login.jsx
5. **Add password reset** - Implement forgot password functionality

## ❓ Troubleshooting

**Issue**: "Import bcrypt could not be resolved"
**Solution**: Run `pip install bcrypt pyjwt` in Backend folder

**Issue**: "MongoDB connection failed"
**Solution**: Make sure MongoDB is running and MONGO_URI is correct in .env

**Issue**: "Cannot read token"
**Solution**: Clear localStorage and try logging in again

**Issue**: CORS errors
**Solution**: Backend already configured for localhost:5173, restart backend if needed

Enjoy your new authentication system! 🎉
