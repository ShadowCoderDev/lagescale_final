/**
 * API Client Utilities
 * Axios instances for user-service, product-service, and order-service
 * Uses cookie-based authentication (HTTP-only cookies)
 */

import axios from 'axios';
import { USER_API_BASE_URL, PRODUCT_API_BASE_URL, ORDER_API_BASE_URL } from '../config/api';

// Create axios instance for user-service
export const userApi = axios.create({
  baseURL: USER_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies automatically (access_token, refresh_token)
});

// Create axios instance for product-service
export const productApi = axios.create({
  baseURL: PRODUCT_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies automatically
});

// Create axios instance for order-service
export const orderApi = axios.create({
  baseURL: ORDER_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies automatically
});

// Response interceptor for user-service
userApi.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle network errors
    if (!error.response) {
      if (error.request) {
        error.message = `Network Error: Cannot connect to server. Please check if the backend service is running.`;
        error.networkError = true;
      } else {
        error.message = `Request Error: ${error.message}`;
      }
    } else if (error.response?.status === 401) {
      // 401 means user is not authenticated (cookie invalid/missing)
      // Redirect to login if not already there
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Response interceptor for product-service
productApi.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle network errors
    if (!error.response) {
      if (error.request) {
        error.message = `Network Error: Cannot connect to server. Please check if the backend service is running.`;
        error.networkError = true;
      } else {
        error.message = `Request Error: ${error.message}`;
      }
    }
    // For product-service errors, just reject - let components handle it
    return Promise.reject(error);
  }
);

// Response interceptor for order-service
orderApi.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle network errors
    if (!error.response) {
      if (error.request) {
        error.message = `Network Error: Cannot connect to server. Please check if the backend service is running.`;
        error.networkError = true;
      } else {
        error.message = `Request Error: ${error.message}`;
      }
    } else if (error.response?.status === 401) {
      // 401 means user is not authenticated
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
