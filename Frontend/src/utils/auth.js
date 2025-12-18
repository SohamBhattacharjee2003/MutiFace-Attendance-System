import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { verifyToken } from './api';

/**
 * Custom hook to check if user is authenticated
 * @returns {Object} { isAuthenticated, loading, user }
 */
export const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');

      if (!token) {
        setIsAuthenticated(false);
        setLoading(false);
        return;
      }

      try {
        const result = await verifyToken();
        setIsAuthenticated(true);
        setUser(result.user);
      } catch {
        setIsAuthenticated(false);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  return { isAuthenticated, loading, user };
};

/**
 * Higher-order component to protect routes
 * Redirects to login if user is not authenticated
 */
export const ProtectedRoute = ({ children }) => {
  const navigate = useNavigate();
  const { isAuthenticated, loading } = useAuth();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, loading, navigate]);

  if (loading) {
    return (
      <div className="h-screen w-full bg-[#060b23] flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return isAuthenticated ? children : null;
};

/**
 * Get current user from localStorage
 * @returns {Object|null} User object or null
 */
export const getCurrentUserFromStorage = () => {
  try {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  } catch (error) {
    console.error('Error parsing user from localStorage:', error);
    return null;
  }
};

/**
 * Check if user is logged in (has token)
 * @returns {boolean}
 */
export const isLoggedIn = () => {
  return !!localStorage.getItem('token');
};
