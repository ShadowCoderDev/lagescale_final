import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import "./Navbar.css";

const Navbar = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const { getTotalItems } = useCart();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const cartItemCount = getTotalItems();

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          Shop
        </Link>
        <div className="navbar-menu">
          <Link to="/products" className="navbar-link">
            محصولات
          </Link>
          <Link to="/cart" className="navbar-link cart-link">
            سبد خرید
            {cartItemCount > 0 && (
              <span className="cart-badge">{cartItemCount}</span>
            )}
          </Link>
          {isAuthenticated ? (
            <>
              <Link to="/orders" className="navbar-link">
                سفارش‌ها
              </Link>
              <Link to="/profile" className="navbar-link">
                پروفایل من
              </Link>
              <span className="navbar-user">
                {user?.full_name ||
                  user?.email ||
                  user?.first_name ||
                  "وارد شده"}
              </span>
              <button onClick={handleLogout} className="btn btn-secondary">
                خروج
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="navbar-link">
                ورود
              </Link>
              <Link
                to="/register"
                className="btn btn-primary"
                style={{ padding: "5px 15px" }}
              >
                ثبت‌نام
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
