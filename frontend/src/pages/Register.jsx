/**
 * Register Page
 * Handles user registration
 */

import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { userApi } from '../utils/api';
import { API_ENDPOINTS } from '../config/api';
import './Register.css';

const Register = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  // Redirect if already authenticated
  useEffect(() => {
    // Only redirect if not loading and authenticated
    if (!authLoading && isAuthenticated) {
      navigate('/products', { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validate passwords match
    if (formData.password !== formData.password2) {
      setError('رمزهای عبور مطابقت ندارند.');
      return;
    }

    setLoading(true);

    try {
      const response = await userApi.post(API_ENDPOINTS.USER_REGISTER, {
        email: formData.email,
        password: formData.password,
        password2: formData.password2,
        first_name: formData.first_name,
        last_name: formData.last_name,
      });

      // Backend sets cookies automatically, we just need user data
      const userData = response.data.user;

      if (userData) {
        // Login will fetch profile using cookies automatically
        await login(userData);
        // Navigate after registration completes
        navigate('/products', { replace: true });
      } else {
        setError('ثبت‌نام موفق بود اما اطلاعات کاربر دریافت نشد. لطفاً وارد شوید.');
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
        // Handle validation errors - Django REST Framework returns errors as object
        if (typeof errorData === 'object' && !errorData.message) {
          const errorMessages = Object.entries(errorData)
            .map(([key, value]) => {
              if (Array.isArray(value)) {
                return `${key}: ${value.join(', ')}`;
              }
              if (typeof value === 'object' && value !== null) {
                return `${key}: ${JSON.stringify(value)}`;
              }
              return `${key}: ${value}`;
            })
            .join('\n');
          setError(errorMessages || 'اعتبارسنجی ناموفق بود. لطفاً ورودی‌های خود را بررسی کنید.');
        } else {
          setError(errorData.error || errorData.message || errorData.detail || 'ثبت‌نام ناموفق بود.');
        }
      } else if (err.message) {
        setError(err.message);
      } else {
        setError(`ثبت‌نام ناموفق بود (وضعیت: ${err.response?.status || 'نامشخص'}). لطفاً دوباره تلاش کنید.`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-container">
      <div className="register-card">
        <h1>ثبت‌نام</h1>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">ایمیل *</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="first_name">نام</label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label htmlFor="last_name">نام خانوادگی</label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">رمز عبور *</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              disabled={loading}
              minLength={8}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password2">تکرار رمز عبور *</label>
            <input
              type="password"
              id="password2"
              name="password2"
              value={formData.password2}
              onChange={handleChange}
              required
              disabled={loading}
              minLength={8}
            />
          </div>

          {error && (
            <div className="error-message" style={{ whiteSpace: 'pre-line' }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: '100%' }}
          >
            {loading ? 'در حال ثبت‌نام...' : 'ثبت‌نام'}
          </button>

          <div style={{ marginTop: '20px', textAlign: 'center' }}>
            <span>قبلاً ثبت‌نام کرده‌اید؟ </span>
            <Link to="/login" className="link">
              وارد شوید
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Register;
