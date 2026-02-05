/**
 * Login Page
 * Handles user authentication
 */

import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { userApi } from '../utils/api';
import { API_ENDPOINTS } from '../config/api';
import './Login.css';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  // Redirect if already authenticated
  useEffect(() => {
    // Only redirect if auth context is not loading and user is authenticated
    if (!authLoading && isAuthenticated) {
      navigate('/profile', { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await userApi.post(API_ENDPOINTS.USER_LOGIN, {
        email,
        password,
      });

      // Backend sets cookies automatically, we just need user data
      const userData = response.data.user;

      if (userData) {
        // Login will fetch profile using cookies automatically
        await login(userData);
        // Navigate after login completes
        navigate('/profile', { replace: true });
      } else {
        setError('ورود موفق بود اما اطلاعات کاربر دریافت نشد. لطفاً دوباره تلاش کنید.');
      }
    } catch (err) {
      // Handle network errors
      if (err.networkError || !err.response) {
        setError(
          'خطای شبکه: اتصال به سرور امکان‌پذیر نیست. لطفاً مطمئن شوید سرویس‌های بکند در حال اجرا هستند.'
        );
        return;
      }

      const errorData = err.response?.data;
      if (errorData) {
        // Handle different error formats from Django REST Framework
        if (typeof errorData === 'object' && !errorData.message && !errorData.error) {
          // Validation errors as object
          const errorMessages = Object.entries(errorData)
            .map(([key, value]) => {
              if (Array.isArray(value)) {
                return `${key}: ${value.join(', ')}`;
              }
              return `${key}: ${value}`;
            })
            .join('\n');
          setError(errorMessages || 'اطلاعات ورود نامعتبر است.');
        } else {
          setError(
            errorData.error ||
            errorData.message ||
            errorData.detail ||
            (Array.isArray(errorData.non_field_errors) ? errorData.non_field_errors.join(', ') :
              'ورود ناموفق بود. لطفاً اطلاعات ورود خود را بررسی کنید.')
          );
        }
      } else if (err.message) {
        setError(err.message);
      } else {
        setError(`ورود ناموفق بود (وضعیت: ${err.response?.status || 'نامشخص'}). لطفاً دوباره تلاش کنید.`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>ورود</h1>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">ایمیل</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">رمز عبور</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          {error && <div className="error-message">{error}</div>}
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: '100%' }}
          >
            {loading ? 'در حال ورود...' : 'ورود'}
          </button>

          <div style={{ marginTop: '20px', textAlign: 'center' }}>
            <span>حساب کاربری ندارید؟ </span>
            <Link to="/register" className="link">
              ثبت‌نام کنید
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
