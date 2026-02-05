/**
 * Products List Page
 * Displays products with search
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { productApi } from '../utils/api';
import { API_ENDPOINTS } from '../config/api';
import { useAuth } from '../context/AuthContext';
import './ProductsList.css';

const ProductsList = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrevious, setHasPrevious] = useState(false);
  const { isAdmin } = useAuth();

  // Fetch products
  const fetchProducts = async () => {
    setLoading(true);
    setError('');

    try {
      const params = new URLSearchParams();
      params.append('page', page);

      // Use search endpoint if query exists, otherwise list endpoint
      const endpoint = searchQuery
        ? `${API_ENDPOINTS.PRODUCTS_SEARCH}?q=${encodeURIComponent(searchQuery)}&${params.toString()}`
        : `${API_ENDPOINTS.PRODUCTS_LIST}?${params.toString()}`;

      const response = await productApi.get(endpoint);

      if (response.data && Array.isArray(response.data.results)) {
        setProducts(response.data.results);
        setHasNext(!!response.data.next);
        setHasPrevious(!!response.data.previous);
      } else {
        setProducts([]);
        setHasNext(false);
        setHasPrevious(false);
      }
    } catch (err) {
      if (err.networkError || !err.response) {
        setError('خطای شبکه: اتصال به سرور امکان‌پذیر نیست.');
      } else {
        setError(err.response?.data?.detail || 'بارگذاری محصولات ناموفق بود.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [page]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchProducts();
  };

  const handleClear = () => {
    setSearchQuery('');
    setPage(1);
    fetchProducts();
  };

  const handleDelete = async (productId) => {
    if (!window.confirm('آیا مطمئن هستید که می‌خواهید این محصول را حذف کنید؟')) {
      return;
    }

    try {
      await productApi.delete(API_ENDPOINTS.PRODUCT_DETAIL(productId));
      fetchProducts();
    } catch (err) {
      alert(err.response?.data?.detail || 'حذف محصول ناموفق بود.');
    }
  };

  if (loading && products.length === 0) {
    return <div className="loading">در حال بارگذاری محصولات...</div>;
  }

  return (
    <div className="container">
      <h1>محصولات</h1>

      {/* Search */}
      <div className="card">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="جستجوی محصولات..."
            className="search-input"
          />
          <button type="submit" className="btn btn-primary">
            جستجو
          </button>
          {searchQuery && (
            <button type="button" onClick={handleClear} className="btn btn-secondary">
              پاک‌سازی
            </button>
          )}
        </form>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Products Table */}
      {products.length === 0 ? (
        <div className="card">
          <p>محصولی یافت نشد.</p>
        </div>
      ) : (
        <>
          <div className="card">
            <table className="table">
              <thead>
                <tr>
                  <th>نام</th>
                  <th>دسته‌بندی</th>
                  <th>قیمت</th>
                  <th>موجودی</th>
                  <th>عملیات</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product.id}>
                    <td>
                      <Link to={`/products/${product.id}`} className="link">
                        {product.name}
                      </Link>
                    </td>
                    <td>{product.category}</td>
                    <td>${parseFloat(product.price).toFixed(2)}</td>
                    <td>{product.stockQuantity}</td>
                    <td>
                      <div className="action-buttons">
                        <Link
                          to={`/products/${product.id}`}
                          className="btn btn-primary btn-sm"
                        >
                          مشاهده
                        </Link>
                        {isAdmin && (
                          <>
                            <Link
                              to={`/products/${product.id}/edit`}
                              className="btn btn-secondary btn-sm"
                            >
                              ویرایش
                            </Link>
                            <button
                              onClick={() => handleDelete(product.id)}
                              className="btn btn-danger btn-sm"
                            >
                              حذف
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {(hasNext || hasPrevious) && (
            <div className="pagination">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={!hasPrevious}
                className="btn btn-secondary"
              >
                قبلی
              </button>
              <span>صفحه {page}</span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={!hasNext}
                className="btn btn-secondary"
              >
                بعدی
              </button>
            </div>
          )}
        </>
      )}

      {isAdmin && (
        <div className="card">
          <Link to="/products/new" className="btn btn-primary">
            ایجاد محصول جدید
          </Link>
        </div>
      )}
    </div>
  );
};

export default ProductsList;
