import axios, { AxiosResponse } from 'axios';
import { API_BASE_URL } from '../config/api';

// Debug logging
console.log('API_BASE_URL from env:', process.env.REACT_APP_API_URL);
console.log('API_BASE_URL being used:', API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login or handle unauthorized
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;