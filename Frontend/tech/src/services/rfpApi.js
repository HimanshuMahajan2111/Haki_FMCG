/**
 * RFP Workflow API Client
 * Complete integration with the FastAPI backend AI system
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, try to refresh
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken
          });
          localStorage.setItem('access_token', response.data.access_token);
          // Retry original request
          error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
          return axios(error.config);
        } catch (refreshError) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// ==================== Authentication ====================

export const authApi = {
  /**
   * Login with username and password
   * @param {string} username - User's username
   * @param {string} password - User's password
   * @returns {Promise<{access_token: string, refresh_token: string, token_type: string}>}
   */
  login: async (username, password) => {
    const response = await api.post('/api/v1/auth/login', { username, password });
    // Store tokens
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    return response.data;
  },

  /**
   * Register new user (admin only)
   */
  register: async (userData) => {
    const response = await api.post('/api/v1/auth/register', userData);
    return response.data;
  },

  /**
   * Get current user info
   */
  getCurrentUser: async () => {
    const response = await api.get('/api/v1/auth/me');
    return response.data;
  },

  /**
   * Logout (clear tokens)
   */
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  }
};

// ==================== RFP Workflow ====================

export const rfpApi = {
  /**
   * Submit a new RFP for processing
   * @param {Object} rfpData - RFP submission data
   * @returns {Promise<{workflow_id: string, status: string, ...}>}
   */
  submitRFP: async (rfpData) => {
    const response = await api.post('/api/v1/rfp/submit', {
      rfp_id: rfpData.rfp_id || `RFP-${Date.now()}`,
      customer_id: rfpData.customer_id,
      document: rfpData.document,
      deadline: rfpData.deadline,
      priority: rfpData.priority || 'normal',
      complexity: rfpData.complexity,
      estimated_value: rfpData.estimated_value,
      is_standard_product: rfpData.is_standard_product || false,
      template_id: rfpData.template_id,
      metadata: rfpData.metadata || {}
    });
    return response.data;
  },

  /**
   * Get workflow status
   * @param {string} workflowId - Workflow ID
   * @returns {Promise<{status: string, current_stage: string, ...}>}
   */
  getWorkflowStatus: async (workflowId) => {
    const response = await api.get(`/api/v1/rfp/status/${workflowId}`);
    return response.data;
  },

  /**
   * Get workflow result
   * @param {string} workflowId - Workflow ID
   * @returns {Promise<{workflow_info: Object, quote: Object, ...}>}
   */
  getWorkflowResult: async (workflowId) => {
    const response = await api.get(`/api/v1/rfp/result/${workflowId}`);
    return response.data;
  },

  /**
   * List all workflows with optional filtering
   * @param {Object} filters - Filter options
   * @returns {Promise<Array>}
   */
  listWorkflows: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.customer_id) params.append('customer_id', filters.customer_id);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.skip) params.append('skip', filters.skip);
    
    const response = await api.get(`/api/v1/rfp/workflows?${params}`);
    return response.data;
  },

  /**
   * Submit batch RFPs
   * @param {Array} rfps - Array of RFP data
   * @param {boolean} parallel - Process in parallel
   * @returns {Promise}
   */
  submitBatch: async (rfps, parallel = false) => {
    const response = await api.post('/api/v1/rfp/batch', {
      rfps,
      parallel
    });
    return response.data;
  },

  /**
   * Stream workflow updates via Server-Sent Events
   * @param {string} workflowId - Workflow ID
   * @param {Function} onMessage - Callback for messages
   * @param {Function} onError - Error callback
   * @returns {EventSource}
   */
  streamWorkflow: (workflowId, onMessage, onError) => {
    const token = localStorage.getItem('access_token');
    const eventSource = new EventSource(
      `${API_BASE_URL}/api/v1/rfp/stream/${workflowId}?token=${token}`
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    eventSource.onerror = (error) => {
      eventSource.close();
      if (onError) onError(error);
    };

    return eventSource;
  }
};

// ==================== Product Search ====================

export const productApi = {
  /**
   * Search products with filters
   * @param {string} query - Search query
   * @param {Object} filters - Search filters
   * @returns {Promise<{results: Array, total: number, ...}>}
   */
  searchProducts: async (query, filters = {}) => {
    const response = await api.post('/api/v1/products/search', {
      query,
      filters: {
        category: filters.category,
        min_price: filters.min_price,
        max_price: filters.max_price,
        in_stock: filters.in_stock,
        tags: filters.tags
      },
      limit: filters.limit || 20,
      offset: filters.offset || 0
    });
    return response.data;
  }
};

// ==================== File Management ====================

export const fileApi = {
  /**
   * Upload a file
   * @param {File} file - File to upload
   * @param {Object} metadata - Optional metadata
   * @returns {Promise<{file_id: string, url: string, ...}>}
   */
  uploadFile: async (file, metadata = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata.description) formData.append('description', metadata.description);
    if (metadata.tags) formData.append('tags', JSON.stringify(metadata.tags));

    const response = await api.post('/api/v1/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });
    return response.data;
  },

  /**
   * Download a file
   * @param {string} fileId - File ID
   * @returns {Promise<Blob>}
   */
  downloadFile: async (fileId) => {
    const response = await api.get(`/api/v1/files/${fileId}`, {
      responseType: 'blob'
    });
    return response.data;
  }
};

// ==================== Webhooks ====================

export const webhookApi = {
  /**
   * Register a webhook
   * @param {string} url - Webhook URL
   * @param {Array<string>} events - Events to subscribe to
   * @param {string} secret - Optional webhook secret
   * @returns {Promise}
   */
  registerWebhook: async (url, events, secret = null) => {
    const response = await api.post('/api/v1/webhooks', {
      url,
      events,
      secret,
      active: true
    });
    return response.data;
  },

  /**
   * List all webhooks
   * @returns {Promise<Array>}
   */
  listWebhooks: async () => {
    const response = await api.get('/api/v1/webhooks');
    return response.data;
  },

  /**
   * Get webhook details
   * @param {string} webhookId - Webhook ID
   * @returns {Promise}
   */
  getWebhook: async (webhookId) => {
    const response = await api.get(`/api/v1/webhooks/${webhookId}`);
    return response.data;
  },

  /**
   * Delete a webhook
   * @param {string} webhookId - Webhook ID
   * @returns {Promise}
   */
  deleteWebhook: async (webhookId) => {
    const response = await api.delete(`/api/v1/webhooks/${webhookId}`);
    return response.data;
  },

  /**
   * Get webhook delivery history
   * @param {string} webhookId - Webhook ID
   * @returns {Promise<Array>}
   */
  getWebhookDeliveries: async (webhookId) => {
    const response = await api.get(`/api/v1/webhooks/${webhookId}/deliveries`);
    return response.data;
  }
};

// ==================== System ====================

export const systemApi = {
  /**
   * Health check
   * @returns {Promise<{status: string, version: string, ...}>}
   */
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  /**
   * Get API documentation
   * @returns {string} - URL to API docs
   */
  getDocsUrl: () => `${API_BASE_URL}/docs`,

  /**
   * Get OpenAPI spec
   * @returns {string} - URL to OpenAPI JSON
   */
  getOpenApiUrl: () => `${API_BASE_URL}/openapi.json`
};

export default api;
