/**
 * Order Detail Page
 * Shows detailed information about a single order
 */

import { useState, useEffect } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { orderApi } from '../utils/api';
import { API_ENDPOINTS } from '../config/api';
import { useAuth } from '../context/AuthContext';
import './OrderDetail.css';

const OrderDetail = () => {
  const { id } = useParams();
  const location = useLocation();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    // Show success message if payment was successful
    if (location.state?.paymentSuccess) {
      setSuccessMessage('پرداخت موفق! سفارش شما ثبت شد.');
      setTimeout(() => setSuccessMessage(''), 5000);
    }

    fetchOrder();
  }, [id, isAuthenticated]);

  const fetchOrder = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await orderApi.get(API_ENDPOINTS.ORDER_DETAIL(id));
      setOrder(response.data);
    } catch (err) {
      console.error('Error fetching order:', err);

      if (err.networkError || !err.response) {
        setError('خطای شبکه: اتصال به سرور امکان‌پذیر نیست.');
      } else if (err.response?.status === 401) {
        setError('برای مشاهده این سفارش باید وارد شوید.');
      } else if (err.response?.status === 404) {
        setError('سفارش یافت نشد.');
      } else {
        const errorData = err.response?.data;
        setError(
          errorData?.detail ||
          errorData?.message ||
          'بارگذاری سفارش ناموفق بود.'
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancelOrder = async () => {
    if (!window.confirm('آیا مطمئن هستید که می‌خواهید این سفارش را لغو کنید؟')) {
      return;
    }

    setActionLoading(true);
    setActionError('');

    try {
      await orderApi.post(API_ENDPOINTS.ORDER_CANCEL(id));
      setSuccessMessage('سفارش با موفقیت لغو شد.');
      setTimeout(() => setSuccessMessage(''), 5000);
      // Refresh order data
      fetchOrder();
    } catch (err) {
      console.error('Error canceling order:', err);

      if (err.networkError || !err.response) {
        setActionError(
          'خطای شبکه: اتصال به سرویس سفارش امکان‌پذیر نیست. ' +
          'لطفاً مطمئن شوید سرویس بکند در حال اجرا است.'
        );
      } else {
        const errorData = err.response?.data;
        setActionError(
          errorData?.detail ||
          errorData?.error ||
          errorData?.message ||
          'لغو سفارش ناموفق بود. لطفاً دوباره تلاش کنید.'
        );
      }
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadgeClass = (status) => {
    const statusClasses = {
      PENDING: 'status-pending',
      PAID: 'status-paid',
      PROCESSING: 'status-processing',
      SHIPPED: 'status-shipped',
      DELIVERED: 'status-delivered',
      CANCELED: 'status-canceled',
      FAILED: 'status-failed',
    };
    return statusClasses[status] || 'status-default';
  };

  const canCancelOrder = (order) => {
    // Only allow cancel if not yet shipped/delivered
    return order && !['SHIPPED', 'DELIVERED', 'CANCELED'].includes(order.status);
  };

  if (!isAuthenticated) {
    return (
      <div className="container">
        <h1>جزئیات سفارش</h1>
        <div className="card">
          <p>برای مشاهده جزئیات سفارش لطفاً وارد شوید.</p>
          <Link to="/login" className="btn btn-primary" style={{ marginTop: '20px' }}>
            رفتن به صفحه ورود
          </Link>
        </div>
      </div>
    );
  }

  if (loading) {
    return <div className="loading">در حال بارگذاری سفارش...</div>;
  }

  if (error) {
    return (
      <div className="container">
        <div className="error-message">{error}</div>
        <Link to="/orders" className="btn btn-secondary" style={{ marginTop: '20px' }}>
          بازگشت به سفارشات
        </Link>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="container">
        <div className="error-message">سفارش یافت نشد</div>
        <Link to="/orders" className="btn btn-secondary" style={{ marginTop: '20px' }}>
          بازگشت به سفارشات
        </Link>
      </div>
    );
  }

  return (
    <div className="container">
      <Link to="/orders" className="link" style={{ marginBottom: '20px', display: 'inline-block' }}>
        → بازگشت به سفارشات
      </Link>

      <div className="order-detail-header">
        <h1>سفارش #{order.id}</h1>
        <span className={`status-badge ${getStatusBadgeClass(order.status)}`}>
          {order.status}
        </span>
      </div>

      {successMessage && (
        <div className="success-message">{successMessage}</div>
      )}

      {actionError && (
        <div className="error-message">{actionError}</div>
      )}

      {/* Order Information */}
      <div className="card">
        <h2>اطلاعات سفارش</h2>
        <div className="info-grid">
          <div className="info-item">
            <strong>شماره سفارش:</strong>
            <span>{order.id}</span>
          </div>
          <div className="info-item">
            <strong>وضعیت:</strong>
            <span className={getStatusBadgeClass(order.status)}>
              {order.status}
            </span>
          </div>
          <div className="info-item">
            <strong>مبلغ کل:</strong>
            <span className="amount">${parseFloat(order.total_amount).toFixed(2)}</span>
          </div>
          <div className="info-item">
            <strong>تاریخ ایجاد:</strong>
            <span>
              {new Date(order.created_at).toLocaleString('fa-IR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
          <div className="info-item">
            <strong>آخرین بروزرسانی:</strong>
            <span>
              {new Date(order.updated_at).toLocaleString('fa-IR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
          {order.payment_id && (
            <div className="info-item">
              <strong>شناسه پرداخت:</strong>
              <span>{order.payment_id}</span>
            </div>
          )}
          {order.payment_status && (
            <div className="info-item">
              <strong>وضعیت پرداخت:</strong>
              <span>{order.payment_status}</span>
            </div>
          )}
          {order.notes && (
            <div className="info-item full-width">
              <strong>یادداشت‌ها:</strong>
              <p>{order.notes}</p>
            </div>
          )}
        </div>
      </div>

      {/* Order Items */}
      <div className="card">
        <h2>اقلام سفارش</h2>
        <table className="table order-items-table">
          <thead>
            <tr>
              <th>محصول</th>
              <th>کد</th>
              <th>قیمت واحد</th>
              <th>تعداد</th>
              <th>جمع جزء</th>
            </tr>
          </thead>
          <tbody>
            {order.items.map((item) => (
              <tr key={item.id}>
                <td>
                  <Link to={`/products/${item.product_id}`} className="product-link">
                    {item.product_name}
                  </Link>
                </td>
                <td>{item.product_sku}</td>
                <td>${parseFloat(item.unit_price).toFixed(2)}</td>
                <td>{item.quantity}</td>
                <td className="subtotal">
                  ${parseFloat(item.subtotal).toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="total-row">
              <td colSpan="4" style={{ textAlign: 'left' }}>
                <strong>جمع کل:</strong>
              </td>
              <td className="total">
                <strong>${parseFloat(order.total_amount).toFixed(2)}</strong>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Order Actions */}
      <div className="card order-actions-card">
        <h2>عملیات</h2>
        <div className="order-actions">
          {canCancelOrder(order) && (
            <button
              onClick={handleCancelOrder}
              className="btn btn-danger"
              disabled={actionLoading}
            >
              {actionLoading ? 'در حال لغو...' : 'لغو سفارش'}
            </button>
          )}
          {!canCancelOrder(order) && (
            <p className="no-actions">هیچ عملیاتی برای این سفارش موجود نیست.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default OrderDetail;

