import axios from 'axios';

// Use relative URL when in production (same origin), absolute in development
const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '' : 'http://localhost:8000');

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ==================== Health Check ====================
export const healthCheck = async () => {
  const response = await api.get('/api/v1/health');
  return response.data;
};

// ==================== RFP Workflow ====================
export const submitRFP = async (rfpData) => {
  const response = await api.post('/api/v1/rfp', rfpData);
  return response.data;
};

export const getWorkflowStatus = async (workflowId) => {
  const response = await api.get(`/api/v1/rfp/status/${workflowId}`);
  return response.data;
};

export const listWorkflows = async (statusFilter = null, limit = 50) => {
  const params = { limit };
  if (statusFilter) params.status_filter = statusFilter;
  const response = await api.get('/api/v1/rfp/workflows', { params });
  return response.data;
};

export const getChallengeRFPs = async () => {
  const response = await api.get('/api/challenge/rfps');
  return response.data;
};

export const runChallengePipeline = async (rfpId) => {
  const response = await api.post(`/api/challenge/run?rfp_id=${rfpId || ''}`);
  return response.data;
};

// Legacy RFP endpoints (for backward compatibility)
export const scanRFPs = async (forceRescan = false) => {
  const response = await api.post('/api/rfp/scan', { force_rescan: forceRescan });
  return response.data;
};

export const getLatestRFPs = async () => {
  const response = await api.get('/api/rfp/latest');
  return response.data;
};

export const getRFPHistory = async (limit = 10) => {
  const response = await api.get(`/api/rfp/history?limit=${limit}`);
  return response.data;
};

export const processRFP = async (rfpId, rfpData) => {
  const response = await api.post('/api/rfp/process', {
    rfp_id: rfpId,
    rfp_data: rfpData,
  });
  return response.data;
};

// ==================== Products ====================
export const getProducts = async (skip = 0, limit = 50) => {
  const response = await api.get(`/api/products?skip=${skip}&limit=${limit}`);
  return response.data;
};

export const searchProducts = async (query, limit = 10) => {
  const response = await api.post('/api/products/search', { query, limit });
  return response.data;
};

// ==================== Analytics Endpoints ====================
export const getDashboard = async (days = 30) => {
  const response = await api.get(`/api/v1/analytics/dashboard?days=${days}`);
  return response.data;
};

export const getRFPProcessing = async (days = 30) => {
  const response = await api.get(`/api/v1/analytics/rfp-processing?days=${days}`);
  return response.data;
};

export const getMatchAccuracy = async (days = 30) => {
  const response = await api.get(`/api/v1/analytics/match-accuracy?days=${days}`);
  return response.data;
};

export const getWinRates = async (days = 30) => {
  const response = await api.get(`/api/v1/analytics/win-rates?days=${days}`);
  return response.data;
};

export const getAgentPerformance = async (days = 30) => {
  const response = await api.get(`/api/v1/analytics/agent-performance?days=${days}`);
  return response.data;
};

export const getSystemHealth = async () => {
  const response = await api.get('/api/v1/analytics/system-health');
  return response.data;
};

export const getRealtimeMetrics = async () => {
  const response = await api.get('/api/v1/analytics/realtime');
  return response.data;
};

export const getPerformanceMetrics = async () => {
  const response = await api.get('/api/v1/analytics/performance');
  return response.data;
};

export const getBottlenecks = async () => {
  const response = await api.get('/api/v1/analytics/bottlenecks');
  return response.data;
};

export const getCacheStats = async () => {
  const response = await api.get('/api/v1/analytics/cache-stats');
  return response.data;
};

export const clearCache = async (pattern = '*') => {
  const response = await api.post('/api/v1/analytics/cache/clear', { pattern });
  return response.data;
};

export const getErrors = async () => {
  const response = await api.get('/api/v1/analytics/errors');
  return response.data;
};

export const getErrorById = async (errorId) => {
  const response = await api.get(`/api/v1/analytics/errors/${errorId}`);
  return response.data;
};

export const exportAnalytics = async () => {
  const response = await api.get('/api/v1/analytics/export');
  return response.data;
};

// Legacy analytics endpoint
export const getDashboardAnalytics = async () => {
  try {
    return await getDashboard(30);
  } catch (error) {
    // Fallback to old endpoint if new one fails
    const response = await api.get('/api/analytics/dashboard');
    return response.data;
  }
};

// ==================== Agent Logs ====================
export const getAgentLogs = async (agentName = null, limit = 50) => {
  const params = { limit };
  if (agentName) params.agent_name = agentName;
  
  const response = await api.get('/api/agents/logs', { params });
  return response.data;
};

// ==================== WebSocket Connection ====================
export const createWebSocket = () => {
  // Determine WebSocket URL based on current location
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = import.meta.env.PROD ? window.location.host : 'localhost:8000';
  return new WebSocket(`${wsProtocol}//${wsHost}/ws/updates`);
};

export default api;
