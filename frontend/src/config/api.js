export const USER_API_BASE_URL = import.meta.env.VITE_USER_API_BASE_URL || '';
export const PRODUCT_API_BASE_URL = import.meta.env.VITE_PRODUCT_API_BASE_URL || '';
export const ORDER_API_BASE_URL = import.meta.env.VITE_ORDER_API_BASE_URL || '';

export const API_ENDPOINTS = {
  USER_LOGIN: '/api/users/login/',
  USER_REGISTER: '/api/users/register/',
  USER_PROFILE: '/api/users/profile/',
  USER_LOGOUT: '/api/users/logout/',
  USER_TOKEN_REFRESH: '/api/users/token/refresh/',

  PRODUCTS_LIST: '/api/products/',
  PRODUCTS_SEARCH: '/api/products/search/',
  PRODUCT_DETAIL: (id) => `/api/products/${id}/`,
  PRODUCT_STOCK: (id) => `/api/products/${id}/stock/`,

  ORDERS_LIST: '/api/orders/',
  ORDER_CREATE: '/api/orders/',
  ORDER_DETAIL: (id) => `/api/orders/${id}`,
  ORDER_CANCEL: (id) => `/api/orders/${id}/cancel`,
};
