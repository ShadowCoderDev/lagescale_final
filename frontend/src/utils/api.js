import axios from 'axios';
import { USER_API_BASE_URL, PRODUCT_API_BASE_URL, ORDER_API_BASE_URL } from '../config/api';

export const userApi = axios.create({
  baseURL: USER_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

export const productApi = axios.create({
  baseURL: PRODUCT_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

export const orderApi = axios.create({
  baseURL: ORDER_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

userApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      if (error.request) {
        error.message = `Network Error: Cannot connect to server. Please check if the backend service is running.`;
        error.networkError = true;
      } else {
        error.message = `Request Error: ${error.message}`;
      }
    } else if (error.response?.status === 401) {
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

productApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      if (error.request) {
        error.message = `Network Error: Cannot connect to server. Please check if the backend service is running.`;
        error.networkError = true;
      } else {
        error.message = `Request Error: ${error.message}`;
      }
    }
    return Promise.reject(error);
  }
);

orderApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      if (error.request) {
        error.message = `Network Error: Cannot connect to server. Please check if the backend service is running.`;
        error.networkError = true;
      } else {
        error.message = `Request Error: ${error.message}`;
      }
    } else if (error.response?.status === 401) {
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
