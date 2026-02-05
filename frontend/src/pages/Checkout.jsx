/**
 * Checkout Page
 * Review order before payment
 */

import { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import './Checkout.css';

const Checkout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { cartItems, getTotalPrice } = useCart();
  const { user } = useAuth();
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');

  // Check if redirected from failed payment
  useEffect(() => {
    if (location.state?.paymentFailed) {
      setError(location.state.errorMessage || 'پرداخت ناموفق بود.');
      // Clear the state to prevent showing error on refresh
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  // Note: Authentication is handled by ProtectedRoute in App.jsx

  // Redirect to cart if cart is empty
  if (cartItems.length === 0) {
    return (
      <div className="container">
        <div className="empty-state">
          <div className="empty-state-icon">🛒</div>
          <h2>سبد خرید خالی است</h2>
          <p>ابتدا محصولاتی به سبد خرید اضافه کنید</p>
          <Link to="/products" className="btn btn-primary btn-lg">
            <span>🛍️</span> مشاهده محصولات
          </Link>
        </div>
      </div>
    );
  }

  const totalPrice = getTotalPrice();

  const handleGoToPayment = (e) => {
    e.preventDefault();
    // Navigate to payment page with notes
    navigate('/payment', { state: { notes: notes.trim() } });
  };

  return (
    <div className="container">
      <h1>تسویه حساب</h1>

      <div className="checkout-layout">
        {/* Order Summary */}
        <div className="order-summary card">
          <h2>خلاصه سفارش</h2>
          
          <div className="summary-items">
            {cartItems.map((item) => (
              <div key={item.id} className="summary-item">
                <div className="item-info">
                  <span className="item-name">{item.name}</span>
                  <span className="item-quantity">x {item.quantity}</span>
                </div>
                <span className="item-price">
                  ${(item.price * item.quantity).toFixed(2)}
                </span>
              </div>
            ))}
          </div>

          <div className="summary-totals">
            <div className="summary-row">
              <span>جمع جزء:</span>
              <span>${totalPrice.toFixed(2)}</span>
            </div>
            <div className="summary-row total">
              <span>جمع کل:</span>
              <span>${totalPrice.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Checkout Form */}
        <div className="checkout-form card">
          <h2>اطلاعات سفارش</h2>

          <form onSubmit={handleGoToPayment}>
            <div className="form-group">
              <label htmlFor="user-email">ایمیل:</label>
              <input
                type="text"
                id="user-email"
                value={user?.email || ''}
                disabled
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label htmlFor="notes">یادداشت (اختیاری):</label>
              <textarea
                id="notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="توضیحات یا دستورالعمل‌های خاص..."
                rows="3"
                maxLength="500"
                className="form-control"
              />
            </div>

            {error && (
              <div className="error-message payment-error">
                <span className="error-icon">⚠️</span>
                <div>
                  <strong>پرداخت ناموفق</strong>
                  <p>{error}</p>
                </div>
              </div>
            )}

            <div className="checkout-actions">
              <Link to="/cart" className="btn btn-secondary">
                بازگشت به سبد
              </Link>
              <button type="submit" className="btn btn-primary btn-pay">
                {error ? 'تلاش مجدد' : 'ادامه به درگاه پرداخت'}
              </button>
            </div>
          </form>

          <div className="checkout-info">
            <p>
              ✓ بررسی موجودی و قیمت در لحظه پرداخت<br/>
              ✓ پرداخت امن از طریق درگاه بانکی<br/>
              ✓ ثبت سفارش بعد از پرداخت موفق
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Checkout;

