import { Link, useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext";
import "./Cart.css";

const Cart = () => {
  const navigate = useNavigate();
  const {
    cartItems,
    removeFromCart,
    updateQuantity,
    clearCart,
    getTotalPrice,
    getTotalItems,
  } = useCart();

  const handleQuantityChange = (productId, newQuantity) => {
    const quantity = parseInt(newQuantity);
    if (!isNaN(quantity) && quantity >= 0) {
      updateQuantity(productId, quantity);
    }
  };

  const handleRemove = (productId) => {
    if (window.confirm("این محصول از سبد خرید حذف شود؟")) {
      removeFromCart(productId);
    }
  };

  const handleClearCart = () => {
    if (window.confirm("همه محصولات از سبد خرید حذف شوند؟")) {
      clearCart();
    }
  };

  const handleCheckout = () => {
    navigate("/checkout");
  };

  if (cartItems.length === 0) {
    return (
      <div className="container">
        <div className="empty-state">
          <div className="empty-state-icon">🛒</div>
          <h2>سبد خرید خالی است</h2>
          <p>هنوز محصولی به سبد خرید اضافه نکرده‌اید</p>
          <Link to="/products" className="btn btn-primary btn-lg">
            <span>🛍️</span> مشاهده محصولات
          </Link>
        </div>
      </div>
    );
  }

  const totalPrice = getTotalPrice();
  const totalItems = getTotalItems();

  return (
    <div className="container">
      <h1>
        سبد خرید ({totalItems} {totalItems === 1 ? "مورد" : "مورد"})
      </h1>

      <div className="card">
        <table className="table cart-table">
          <thead>
            <tr>
              <th>محصول</th>
              <th>قیمت</th>
              <th>تعداد</th>
              <th>جمع جزء</th>
              <th>عملیات</th>
            </tr>
          </thead>
          <tbody>
            {cartItems.map((item) => {
              const subtotal = item.price * item.quantity;
              const isOutOfStock = item.quantity > item.stockQuantity;

              return (
                <tr
                  key={item.id}
                  className={isOutOfStock ? "out-of-stock-row" : ""}
                >
                  <td>
                    <Link to={`/products/${item.id}`} className="product-name">
                      {item.name}
                    </Link>
                    <div className="product-meta">
                      <span className="sku">کد: {item.sku}</span>
                      <span className="category">{item.category}</span>
                    </div>
                    {isOutOfStock && (
                      <div className="stock-warning">
                        فقط {item.stockQuantity} عدد در انبار موجود است
                      </div>
                    )}
                  </td>
                  <td className="price">${item.price.toFixed(2)}</td>
                  <td>
                    <input
                      type="number"
                      min="1"
                      max={item.stockQuantity}
                      value={item.quantity}
                      onChange={(e) =>
                        handleQuantityChange(item.id, e.target.value)
                      }
                      className="quantity-input"
                    />
                  </td>
                  <td className="subtotal">${subtotal.toFixed(2)}</td>
                  <td>
                    <button
                      onClick={() => handleRemove(item.id)}
                      className="btn btn-danger btn-sm"
                    >
                      حذف
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        <div className="cart-summary">
          <div className="summary-row">
            <span className="summary-label">جمع جزء:</span>
            <span className="summary-value">${totalPrice.toFixed(2)}</span>
          </div>
          <div className="summary-row total-row">
            <span className="summary-label">جمع کل:</span>
            <span className="summary-value">${totalPrice.toFixed(2)}</span>
          </div>
        </div>

        <div className="cart-actions">
          <button onClick={handleClearCart} className="btn btn-secondary">
            خالی کردن سبد
          </button>
          <Link to="/products" className="btn btn-secondary">
            ادامه خرید
          </Link>
          <button
            onClick={handleCheckout}
            className="btn btn-primary"
            disabled={cartItems.some(
              (item) => item.quantity > item.stockQuantity,
            )}
          >
            پرداخت
          </button>
        </div>

        {cartItems.some((item) => item.quantity > item.stockQuantity) && (
          <div className="checkout-warning">
            لطفاً تعداد محصولات ناموجود را قبل از ادامه فرآیند خرید تنظیم کنید.
          </div>
        )}
      </div>
    </div>
  );
};

export default Cart;
