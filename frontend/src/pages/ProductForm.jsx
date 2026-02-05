/**
 * Product Form Page
 * Create or edit a product (requires authentication)
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { productApi } from '../utils/api';
import { API_ENDPOINTS } from '../config/api';
import { useAuth } from '../context/AuthContext';
import './ProductForm.css';

const ProductForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = !!id;
  const { isAdmin, loading: authLoading } = useAuth();

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    stockQuantity: '',
    category: '',
    sku: '',
    isActive: true,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [loadingProduct, setLoadingProduct] = useState(isEdit);

  // Load product data if editing
  useEffect(() => {
    if (isEdit) {
      const fetchProduct = async () => {
        try {
          const response = await productApi.get(API_ENDPOINTS.PRODUCT_DETAIL(id));
          const product = response.data;
          setFormData({
            name: product.name || '',
            description: product.description || '',
            price: product.price || '',
            stockQuantity: product.stockQuantity || '',
            category: product.category || '',
            sku: product.sku || '',
            isActive: product.isActive !== undefined ? product.isActive : true,
          });
        } catch (err) {
          setError(
            err.response?.data?.error ||
            err.response?.data?.message ||
            'بارگذاری محصول ناموفق بود.'
          );
        } finally {
          setLoadingProduct(false);
        }
      };

      fetchProduct();
    }
  }, [id, isEdit]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = {
        ...formData,
        price: parseFloat(formData.price),
        stockQuantity: parseInt(formData.stockQuantity),
      };

      if (isEdit) {
        await productApi.put(API_ENDPOINTS.PRODUCT_DETAIL(id), payload);
      } else {
        await productApi.post(API_ENDPOINTS.PRODUCTS_LIST, payload);
      }

      navigate('/products');
    } catch (err) {
      console.error('Full error:', err);
      console.error('Response:', err.response);



      // Handle network errors
      if (err.networkError || !err.response) {
        setError(
          'خطای شبکه: اتصال به سرور امکان‌پذیر نیست. لطفاً مطمئن شوید سرویس‌های بکند در حال اجرا هستند.'
        );
        return;
      }

      const errorData = err.response?.data;

      // Check for permission denied (403)
      if (err.response?.status === 403) {
        setError('شما مجوز انجام این عملیات را ندارید. فقط مدیران می‌توانند محصولات را ایجاد یا ویرایش کنند.');
        return;
      }

      if (errorData) {
        // Handle validation errors
        if (typeof errorData === 'object') {
          const errorMessages = Object.entries(errorData)
            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
            .join('\n');
          setError(errorMessages);
        } else {
          setError(errorData.error || errorData.message || 'ذخیره محصول ناموفق بود.');
        }
      } else {
        setError(`ذخیره محصول ناموفق بود (وضعیت: ${err.response?.status || 'نامشخص'}). لطفاً دوباره تلاش کنید.`);
      }
    } finally {
      setLoading(false);
    }
  };

  // Check if user is admin
  useEffect(() => {
    if (!authLoading && !isAdmin) {
      navigate('/products', { replace: true });
    }
  }, [isAdmin, authLoading, navigate]);

  if (loadingProduct || authLoading) {
    return <div className="loading">در حال بارگذاری...</div>;
  }

  if (!isAdmin) {
    return null; // Will redirect
  }

  return (
    <div className="container">
      <h1>{isEdit ? 'ویرایش محصول' : 'ایجاد محصول جدید'}</h1>

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">نام محصول *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">توضیحات</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows="4"
              disabled={loading}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="sku">کد محصول *</label>
              <input
                type="text"
                id="sku"
                name="sku"
                value={formData.sku}
                onChange={handleChange}
                required
                disabled={loading || isEdit}
              />
              {isEdit && <small style={{ color: '#666' }}>کد محصول قابل تغییر نیست</small>}
            </div>

            <div className="form-group">
              <label htmlFor="category">دسته‌بندی *</label>
              <input
                type="text"
                id="category"
                name="category"
                value={formData.category}
                onChange={handleChange}
                required
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="price">قیمت *</label>
              <input
                type="number"
                id="price"
                name="price"
                value={formData.price}
                onChange={handleChange}
                step="0.01"
                min="0"
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="stockQuantity">موجودی انبار *</label>
              <input
                type="number"
                id="stockQuantity"
                name="stockQuantity"
                value={formData.stockQuantity}
                onChange={handleChange}
                min="0"
                required
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <input
                type="checkbox"
                name="isActive"
                checked={formData.isActive}
                onChange={handleChange}
                disabled={loading}
              />
              فعال
            </label>
          </div>

          {error && (
            <div className="error-message" style={{ whiteSpace: 'pre-line' }}>
              {error}
            </div>
          )}

          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'در حال ذخیره...' : isEdit ? 'بروزرسانی محصول' : 'ایجاد محصول'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/products')}
              className="btn btn-secondary"
              disabled={loading}
            >
              انصراف
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProductForm;
