import { useState, useEffect } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { useCart } from "../context/CartContext";
import { useAuth } from "../context/AuthContext";
import { orderApi } from "../utils/api";
import { API_ENDPOINTS } from "../config/api";
import "./Payment.css";

const Payment = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { cartItems, getTotalPrice, clearCart } = useCart();
  useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [step, setStep] = useState(1);
  const [idempotencyKey] = useState(
    () => `order-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
  );

  const notes = location.state?.notes || "";

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
    setError("");

    await new Promise((resolve) => setTimeout(resolve, 2000));

    try {
      const orderData = {
        items: cartItems.map((item) => ({
          product_id: item.id,
          quantity: item.quantity,
        })),
        notes: notes || null,
        idempotency_key: idempotencyKey,
      };

      const response = await orderApi.post(
        API_ENDPOINTS.ORDER_CREATE,
        orderData,
      );

      clearCart();
      setStep(3);

      setTimeout(() => {
        navigate(`/orders/${response.data.id}`, {
          state: { paymentSuccess: true },
        });
      }, 2000);
    } catch (err) {
      console.error("Payment error:", err);

      let errorMessage = "پرداخت ناموفق بود.";
      if (err.networkError || !err.response) {
        errorMessage = "خطای شبکه: اتصال به سرور امکان‌پذیر نیست.";
      } else {
        const errorData = err.response?.data;
        errorMessage = errorData?.detail || errorData?.message || errorMessage;
      }

      setStep(4);
      setError(errorMessage);

      setTimeout(() => {
        navigate("/checkout", {
          state: { paymentFailed: true, errorMessage },
        });
      }, 3000);
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <div className="payment-container">
      <div className="payment-gateway">
        <div className="gateway-header">
          <div className="bank-logo">🏦</div>
          <h1>درگاه پرداخت امن</h1>
          <p>پرداخت از طریق کلیه کارت‌های عضو شتاب</p>
        </div>

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
              <input
                type="text"
                placeholder="XXX"
                defaultValue="***"
                disabled
              />
            </div>
            <div className="card-field">
              <label>تاریخ انقضا</label>
              <input
                type="text"
                placeholder="MM/YY"
                defaultValue="12/28"
                disabled
              />
            </div>
          </div>
          <div className="card-field">
            <label>رمز دوم (پویا)</label>
            <input
              type="password"
              placeholder="رمز یکبار مصرف"
              defaultValue="******"
              disabled
            />
          </div>
        </div>

        {error && <div className="payment-error">{error}</div>}

        <div className="payment-actions">
          <button
            onClick={() => navigate("/checkout")}
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
            {loading ? "در حال پرداخت..." : `پرداخت ${totalPrice.toFixed(2)}$`}
          </button>
        </div>

        <div className="security-notice">
          <span className="lock-icon">🔒</span>
          <span>این صفحه امن است و اطلاعات شما محفوظ می‌ماند.</span>
        </div>
      </div>
    </div>
  );
};

export default Payment;
