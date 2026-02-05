/**
 * Payment Page
 * Simulated payment gateway
 */

import { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { orderApi } from '../utils/api';
import { API_ENDPOINTS } from '../config/api';
import './Payment.css';

const Payment = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { cartItems, getTotalPrice, clearCart } = useCart();
  useAuth(); // Auth check is done by ProtectedRoute
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(1); // 1: review, 2: processing, 3: success/fail
  // Idempotency key to prevent duplicate orders
  const [idempotencyKey] = useState(() => `order-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);

  // Get notes from checkout page
  const notes = location.state?.notes || '';

  // Note: Authentication is handled by ProtectedRoute in App.jsx

  // Redirect if cart is empty
  if (cartItems.length === 0 && step === 1) {
    return (
      <div className="payment-container">
        <div className="payment-card">
          <h1>درگاه پرداخت</h1>
          <p>سبد خرید شما خالی است.</p>
          <Link to="/products" className="btn btn-primary">
            بازگشت به فروشگاه
          </Link>
        </div>
      </div>
    );
  }

  const totalPrice = getTotalPrice();

  const handlePayment = async () => {
    setStep(2);
    setLoading(true);
    setError('');

    // Simulate payment gateway delay
    await new Promise(resolve => setTimeout(resolve, 2000));

    try {
      const orderData = {
        items: cartItems.map((item) => ({
          product_id: item.id,
          quantity: item.quantity,
        })),
        notes: notes || null,
        // Idempotency key to prevent duplicate orders on retry/double-click
        idempotency_key: idempotencyKey,
      };

      const response = await orderApi.post(API_ENDPOINTS.ORDER_CREATE, orderData);

      // Success!
      clearCart();
      setStep(3);

      // Redirect to order detail after 2 seconds
      setTimeout(() => {
        navigate(`/orders/${response.data.id}`, {
          state: { paymentSuccess: true },
        });
      }, 2000);

    } catch (err) {
      console.error('Payment error:', err);
      
      // Get error message
      let errorMessage = 'پرداخت ناموفق بود.';
      if (err.networkError || !err.response) {
        errorMessage = 'خطای شبکه: اتصال به سرور امکان‌پذیر نیست.';
      } else {
        const errorData = err.response?.data;
        errorMessage = errorData?.detail || errorData?.message || errorMessage;
      }

      // Show failed step briefly then redirect
      setStep(4); // Failed step
      setError(errorMessage);
      
      // Redirect to checkout with error after 3 seconds
      setTimeout(() => {
        navigate('/checkout', {
          state: { paymentFailed: true, errorMessage },
        });
      }, 3000);
    } finally {
      setLoading(false);
    }
  };

  // Processing step
  if (step === 2) {
    return (
      <div className="payment-container">
        <div className="payment-card processing">
          <div className="processing-animation">
            <div className="spinner"></div>
          </div>
          <h2>در حال پردازش پرداخت...</h2>
          <p>لطفاً صبر کنید و از این صفحه خارج نشوید.</p>
        </div>
      </div>
    );
  }

  // Success step
  if (step === 3) {
    return (
      <div className="payment-container">
        <div className="payment-card success">
          <div className="success-icon">✓</div>
          <h2>پرداخت موفق!</h2>
          <p>سفارش شما با موفقیت ثبت شد.</p>
          <p className="redirect-text">در حال انتقال به صفحه سفارش...</p>
        </div>
      </div>
    );
  }

  // Failed step
  if (step === 4) {
    return (
      <div className="payment-container">
        <div className="payment-card failed">
          <div className="failed-icon">✗</div>
          <h2>پرداخت ناموفق</h2>
          <p>{error}</p>
          <p className="redirect-text">در حال بازگشت...</p>
        </div>
      </div>
    );
  }

  // Review step (main payment page)
  return (
    <div className="payment-container">
      <div className="payment-gateway">
        {/* Header */}
        <div className="gateway-header">
          <div className="bank-logo">🏦</div>
          <h1>درگاه پرداخت امن</h1>
          <p>پرداخت از طریق کلیه کارت‌های عضو شتاب</p>
        </div>

        {/* Order Summary */}
        <div className="payment-summary">
          <h3>اطلاعات پرداخت</h3>
          <div className="summary-row">
            <span>فروشگاه:</span>
            <span>فروشگاه آنلاین</span>
          </div>
          <div className="summary-row">
            <span>تعداد اقلام:</span>
            <span>{cartItems.length} مورد</span>
          </div>
          <div className="summary-row total">
            <span>مبلغ قابل پرداخت:</span>
            <span className="amount">${totalPrice.toFixed(2)}</span>
          </div>
        </div>

        {/* Card Info (Simulated) */}
        <div className="card-info">
          <h3>اطلاعات کارت</h3>
          <div className="card-field">
            <label>شماره کارت</label>
            <input 
              type="text" 
              placeholder="XXXX-XXXX-XXXX-XXXX"
              defaultValue="6037-XXXX-XXXX-1234"
              disabled
            />
          </div>
          <div className="card-row">
            <div className="card-field">
              <label>CVV2</label>
              <input type="text" placeholder="XXX" defaultValue="***" disabled />
            </div>
            <div className="card-field">
              <label>تاریخ انقضا</label>
              <input type="text" placeholder="MM/YY" defaultValue="12/28" disabled />
            </div>
          </div>
          <div className="card-field">
            <label>رمز دوم (پویا)</label>
            <input type="password" placeholder="رمز یکبار مصرف" defaultValue="******" disabled />
          </div>
        </div>

        {/* Error Message */}
        {error && <div className="payment-error">{error}</div>}

        {/* Actions */}
        <div className="payment-actions">
          <button 
            onClick={() => navigate('/checkout')} 
            className="btn-cancel"
            disabled={loading}
          >
            انصراف
          </button>
          <button 
            onClick={handlePayment} 
            className="btn-pay"
            disabled={loading}
          >
            {loading ? 'در حال پرداخت...' : `پرداخت ${totalPrice.toFixed(2)}$`}
          </button>
        </div>

        {/* Security Notice */}
        <div className="security-notice">
          <span className="lock-icon">🔒</span>
          <span>این صفحه امن است و اطلاعات شما محفوظ می‌ماند.</span>
        </div>
      </div>
    </div>
  );
};

export default Payment;

