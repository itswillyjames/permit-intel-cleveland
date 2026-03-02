import axios from 'axios';

// Determine the API base URL
const getApiBaseUrl = () => {
  // In production (deployed), use the same origin as the app
  // In development, use localhost:8000
  if (process.env.REACT_APP_API_BASE_URL) {
    return process.env.REACT_APP_API_BASE_URL;
  }
  
  if (process.env.NODE_ENV === 'production') {
    // Use the same origin (protocol + host)
    return window.location.origin;
  }
  
  // Development fallback
  return 'http://localhost:8000';
};

const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;
