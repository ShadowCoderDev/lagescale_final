/**
 * Orders Page
 * Displays user's order history
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { orderApi } from '../utils/api';
import { API_ENDPOINTS } from '../config/api';
import { useAuth } from '../context/AuthContext';
import './Orders.css';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const { isAuthenticated } = useAuth();

  const pageSize = 10;

  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    fetchOrders();
  }, [page, statusFilter, isAuthenticated]);

  const fetchOrders = async () => {
    setLoading(true);
    setError('');

    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });

      if (statusFilter) {
        params.append('status', statusFilter);
      }

      const response = await orderApi.get(
        `${API_ENDPOINTS.ORDERS_LIST}?${params.toString()}`
      );

      setOrders(response.data.orders || []);
      setTotal(response.data.total || 0);
      setTotalPages(Math.ceil((response.data.total || 0) / pageSize));
    } catch (err) {
      console.error('Error fetching orders:', err);

      if (err.networkError || !err.response) {
        setError(
          `خطای شبکه: اتصال به سرویس سفارش امکان‌پذیر نیست. ` +
          'لطفاً مطمئن شوید سرویس بکند در حال اجرا است.'
        );
      } else if (err.response?.status === 401) {
        setError('برای مشاهده سفارشات باید وارد شوید.');
      } else {
        const errorData = err.response?.data;
        setError(
          errorData?.detail ||
          errorData?.error ||
          errorData?.message ||
          `بارگذاری سفارشات ناموفق بود (وضعیت: ${err.response?.status || 'نامشخص'}).`
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newStatus) => {
    setStatusFilter(newStatus);
    setPage(1); // Reset to first page
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

  if (!isAuthenticated) {
    return (
      <div className="container">
        <div className="empty-state">
          <div className="empty-state-icon">🔐</div>
          <h2>ورود به حساب کاربری</h2>
          <p>برای مشاهده سفارشات خود لطفاً وارد شوید</p>
          <Link to="/login" className="btn btn-primary btn-lg">
            <span>👤</span> ورود به حساب
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <h1>سفارشات من</h1>

      {/* Status Filter */}
      <div className="card filters-card">
        <label htmlFor="status-filter">فیلتر بر اساس وضعیت:</label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => handleFilterChange(e.target.value)}
          className="status-filter"
        >
          <option value="">همه سفارشات</option>
          <option value="PENDING">در انتظار</option>
          <option value="PAID">پرداخت شده</option>
          <option value="PROCESSING">در حال پردازش</option>
          <option value="SHIPPED">ارسال شده</option>
          <option value="DELIVERED">تحویل داده شده</option>
          <option value="CANCELED">لغو شده</option>
          <option value="FAILED">ناموفق</option>
        </select>
        {statusFilter && (
          <button
            onClick={() => handleFilterChange('')}
            className="btn btn-secondary btn-sm"
            style={{ marginRight: '10px' }}
          >
            پاک‌سازی فیلتر
          </button>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">در حال بارگذاری سفارشات...</div>
      ) : orders.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📦</div>
          <h2>{statusFilter ? 'سفارشی یافت نشد' : 'هنوز سفارشی ندارید'}</h2>
          <p>
            {statusFilter
              ? `هیچ سفارشی با وضعیت "${statusFilter}" وجود ندارد`
              : 'اولین خرید خود را انجام دهید!'}
          </p>
          <Link to="/products" className="btn btn-primary btn-lg">
            <span>🛍️</span> شروع خرید
          </Link>
        </div>
      ) : (
        <>
          <div className="card">
            <p className="orders-count">
              نمایش {orders.length} از {total} سفارش
            </p>

            <div className="orders-list">
              {orders.map((order) => (
                <div key={order.id} className="order-card">
                  <div className="order-header">
                    <div className="order-info">
                      <h3>
                        <Link to={`/orders/${order.id}`} className="order-link">
                          سفارش #{order.id}
                        </Link>
                      </h3>
                      <span className="order-date">
                        {new Date(order.created_at).toLocaleDateString('fa-IR', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>
                    <span className={`status-badge ${getStatusBadgeClass(order.status)}`}>
                      {order.status}
                    </span>
                  </div>

                  <div className="order-body">
                    <div className="order-items">
                      <strong>اقلام:</strong>
                      <ul>
                        {order.items.slice(0, 3).map((item) => (
                          <li key={item.id}>
                            {item.product_name} x {item.quantity}
                          </li>
                        ))}
                        {order.items.length > 3 && (
                          <li>+ {order.items.length - 3} مورد دیگر</li>
                        )}
                      </ul>
                    </div>

                    <div className="order-total">
                      <strong>مجموع:</strong> ${parseFloat(order.total_amount).toFixed(2)}
                    </div>
                  </div>

                  <div className="order-footer">
                    <Link to={`/orders/${order.id}`} className="btn btn-primary btn-sm">
                      مشاهده جزئیات
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn btn-secondary"
              >
                قبلی
              </button>
              <span>
                صفحه {page} از {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn btn-secondary"
              >
                بعدی
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Orders;

