/**
 * API Configuration
 * Centralized API configuration for the entire application
 * Uses environment variables for flexibility across environments
 */

// Backend API URL
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// API endpoints
export const API_CONFIG = {
  // Base URL
  BASE_URL: BACKEND_URL,
  API_URL: `${BACKEND_URL}/api`,

  // Auth Endpoints
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    ME: '/auth/me',
  },

  // Task Endpoints
  TASKS: {
    LIST: '/tasks',
    CREATE: '/tasks',
    GET: (id) => `/tasks/${id}`,
    UPDATE: (id) => `/tasks/${id}`,
    DELETE: (id) => `/tasks/${id}`,
  },

  // User Endpoints
  USERS: {
    LIST: '/users',
    CREATE: '/users',
    GET: (id) => `/users/${id}`,
    UPDATE: (id) => `/users/${id}`,
    DELETE: (id) => `/users/${id}`,
  },

  // Comments Endpoints
  COMMENTS: {
    LIST: (taskId) => `/comments/task/${taskId}`,
    CREATE: '/comments',
    GET: (id) => `/comments/${id}`,
    UPDATE: (id) => `/comments/${id}`,
    DELETE: (id) => `/comments/${id}`,
  },

  // Chat Endpoints
  CHAT: {
    LIST: '/chat',
    CREATE: '/chat',
    GET: (id) => `/chat/${id}`,
  },

  // Reports Endpoints
  REPORTS: {
    STATS: '/reports/stats',
    TASK_REPORT: '/reports/tasks',
  },

  // Notifications Endpoints
  NOTIFICATIONS: {
    LIST: '/notifications',
    MARK_READ: (id) => `/notifications/${id}/read`,
    DELETE: (id) => `/notifications/${id}`,
  },

  // WebSocket URL
  WS_URL: BACKEND_URL.replace(/^http/, 'ws') + '/ws',

  // Health Check
  HEALTH: '/health',
};

// API Request Configuration
export const API_REQUEST_CONFIG = {
  timeout: 30000, // 30 seconds
  withCredentials: false,
  headers: {
    'Content-Type': 'application/json',
  },
};

// Helper function to build full API URL
export const buildApiUrl = (endpoint) => {
  return `${API_CONFIG.API_URL}${endpoint}`;
};

// Helper function to build WebSocket URL
export const buildWsUrl = (path) => {
  return `${API_CONFIG.WS_URL}${path}`;
};

// Log configuration in development
if (process.env.NODE_ENV === 'development') {
  console.log('🔗 API Configuration loaded:');
  console.log('   Base URL:', API_CONFIG.BASE_URL);
  console.log('   API URL:', API_CONFIG.API_URL);
  console.log('   WS URL:', API_CONFIG.WS_URL);
}

export default API_CONFIG;
