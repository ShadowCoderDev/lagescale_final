/**
 * API Configuration
 * Centralized configuration for API endpoints
 */

// API Base URLs - using same origin (nginx proxy)
export const USER_API_BASE_URL = import.meta.env.VITE_USER_API_BASE_URL || '';
export const PRODUCT_API_BASE_URL = import.meta.env.VITE_PRODUCT_API_BASE_URL || '';
export const ORDER_API_BASE_URL = import.meta.env.VITE_ORDER_API_BASE_URL || '';

// API Endpoint Paths
export const API_ENDPOINTS = {
  // User Service
  USER_LOGIN: '/api/users/login/',
  USER_REGISTER: '/api/users/register/',
  USER_PROFILE: '/api/users/profile/',
  USER_LOGOUT: '/api/users/logout/',
  USER_TOKEN_REFRESH: '/api/users/token/refresh/',

  // Product Service
  PRODUCTS_LIST: '/api/products/',
  PRODUCTS_SEARCH: '/api/products/search/',
  PRODUCT_DETAIL: (id) => `/api/products/${id}/`,
  PRODUCT_STOCK: (id) => `/api/products/${id}/stock/`,

  // Order Service (checkout = validate + pay + create order)
  ORDERS_LIST: '/api/orders/',
  ORDER_CREATE: '/api/orders/',  // This is now checkout - pay first, then create
  ORDER_DETAIL: (id) => `/api/orders/${id}`,
  ORDER_CANCEL: (id) => `/api/orders/${id}/cancel`,
};
