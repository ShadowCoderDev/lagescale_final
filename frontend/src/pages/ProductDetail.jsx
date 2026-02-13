import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { productApi } from "../utils/api";
import { API_ENDPOINTS } from "../config/api";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import "./ProductDetail.css";

const ProductDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [addedToCart, setAddedToCart] = useState(false);
  const { isAuthenticated, isAdmin } = useAuth();
  const { addToCart, isInCart, getItemQuantity } = useCart();

  useEffect(() => {
    const fetchProduct = async () => {
      setLoading(true);
      setError("");

      try {
        const response = await productApi.get(API_ENDPOINTS.PRODUCT_DETAIL(id));
        setProduct(response.data);
      } catch (err) {
        if (err.networkError || !err.response) {
          setError(
            "خطای شبکه: اتصال به سرور امکان‌پذیر نیست. لطفاً مطمئن شوید سرویس‌های بکند در حال اجرا هستند.",
          );
        } else {
          setError(
            err.response?.data?.error ||
              err.response?.data?.message ||
              `بارگذاری محصول ناموفق بود (وضعیت: ${err.response?.status || "نامشخص"}). لطفاً دوباره تلاش کنید.`,
          );
        }
      } finally {
        setLoading(false);
      }
    };

    fetchProduct();
  }, [id]);

  const handleDelete = async () => {
    if (
      !window.confirm("آیا مطمئن هستید که می‌خواهید این محصول را حذف کنید؟")
    ) {
      return;
    }

    try {
      await productApi.delete(API_ENDPOINTS.PRODUCT_DETAIL(id));
      navigate("/products");
    } catch (err) {
      if (err.networkError || !err.response) {
        alert(
          `خطای شبکه: اتصال به سرویس محصول امکان‌پذیر نیست. ` +
            "لطفاً مطمئن شوید سرویس بکند در حال اجرا است.",
        );
      } else {
        alert(
          err.response?.data?.error ||
            err.response?.data?.message ||
            `حذف محصول ناموفق بود (وضعیت: ${err.response?.status || "نامشخص"}).`,
        );
      }
    }
  };

  const handleAddToCart = () => {
    if (quantity <= 0) {
      alert("لطفاً تعداد معتبر وارد کنید");
      return;
    }

    if (quantity > product.stockQuantity) {
      alert(`فقط ${product.stockQuantity} عدد در انبار موجود است`);
      return;
    }

    addToCart(product, quantity);
    setAddedToCart(true);

    setTimeout(() => {
      setAddedToCart(false);
    }, 2000);
  };

  const handleQuantityChange = (e) => {
    const value = parseInt(e.target.value);
    if (!isNaN(value) && value >= 1) {
      setQuantity(value);
    }
  };

  if (loading) {
    return <div className="loading">در حال بارگذاری محصول...</div>;
  }

  if (error) {
    return (
      <div className="container">
        <div className="error-message">{error}</div>
        <Link
          to="/products"
          className="btn btn-secondary"
          style={{ marginTop: "20px" }}
        >
          بازگشت به محصولات
        </Link>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="container">
        <div className="error-message">محصول یافت نشد</div>
        <Link
          to="/products"
          className="btn btn-secondary"
          style={{ marginTop: "20px" }}
        >
          بازگشت به محصولات
        </Link>
      </div>
    );
  }

  return (
    <div className="container">
      <Link
        to="/products"
        className="link"
        style={{ marginBottom: "20px", display: "inline-block" }}
      >
        → بازگشت به محصولات
      </Link>

      <div className="card product-detail">
        <h1>{product.name}</h1>

        <div className="product-info">
          <div className="info-row">
            <strong>کد محصول:</strong>
            <span>{product.sku}</span>
          </div>
          <div className="info-row">
            <strong>دسته‌بندی:</strong>
            <span>{product.category}</span>
          </div>
          <div className="info-row">
            <strong>قیمت:</strong>
            <span className="price">
              ${parseFloat(product.price).toFixed(2)}
            </span>
          </div>
          <div className="info-row">
            <strong>موجودی:</strong>
            <span
              className={
                product.stockQuantity > 0 ? "in-stock" : "out-of-stock"
              }
            >
              {product.stockQuantity}
            </span>
          </div>
          {product.description && (
            <div className="info-row">
              <strong>توضیحات:</strong>
              <p>{product.description}</p>
            </div>
          )}
          <div className="info-row">
            <strong>وضعیت:</strong>
            <span className={product.isActive ? "active" : "inactive"}>
              {product.isActive ? "فعال" : "غیرفعال"}
            </span>
          </div>
          {product.createdAt && (
            <div className="info-row">
              <strong>تاریخ ایجاد:</strong>
              <span>{new Date(product.createdAt).toLocaleString("fa-IR")}</span>
            </div>
          )}
          {product.updatedAt && (
            <div className="info-row">
              <strong>آخرین بروزرسانی:</strong>
              <span>{new Date(product.updatedAt).toLocaleString("fa-IR")}</span>
            </div>
          )}
        </div>

        {product.stockQuantity > 0 && product.isActive && (
          <div className="add-to-cart-section">
            <div className="quantity-selector">
              <label htmlFor="quantity">تعداد:</label>
              <input
                type="number"
                id="quantity"
                min="1"
                max={product.stockQuantity}
                value={quantity}
                onChange={handleQuantityChange}
              />
              <span className="stock-info">
                {getItemQuantity(product.id) > 0 &&
                  `(${getItemQuantity(product.id)} در سبد خرید) `}
                {product.stockQuantity} موجود
              </span>
            </div>
            <button
              onClick={handleAddToCart}
              className="btn btn-primary"
              style={{ marginTop: "10px" }}
            >
              افزودن به سبد خرید
            </button>
            {addedToCart && (
              <span
                className="success-message"
                style={{ marginRight: "10px", color: "green" }}
              >
                ✓ به سبد خرید اضافه شد!
              </span>
            )}
          </div>
        )}

        {product.stockQuantity === 0 && (
          <div
            className="out-of-stock-message"
            style={{
              marginTop: "20px",
              padding: "10px",
              backgroundColor: "#ffebee",
              color: "#c62828",
              borderRadius: "4px",
            }}
          >
            ناموجود
          </div>
        )}

        {!product.isActive && isAdmin && (
          <div
            className="inactive-message"
            style={{
              marginTop: "20px",
              padding: "10px",
              backgroundColor: "#fff3e0",
              color: "#e65100",
              borderRadius: "4px",
            }}
          >
            این محصول غیرفعال است و برای مشتریان قابل مشاهده نیست
          </div>
        )}

        {isAuthenticated && isAdmin && (
          <div className="product-actions">
            <Link to={`/products/${id}/edit`} className="btn btn-primary">
              ویرایش محصول
            </Link>
            <button onClick={handleDelete} className="btn btn-danger">
              حذف محصول
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductDetail;
