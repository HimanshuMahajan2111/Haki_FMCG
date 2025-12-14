import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health Check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

// RFP Scanner
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

// Products
export const getProducts = async (skip = 0, limit = 50) => {
  const response = await api.get(`/api/products?skip=${skip}&limit=${limit}`);
  return response.data;
};

export const searchProducts = async (query, limit = 10) => {
  const response = await api.post('/api/products/search', { query, limit });
  return response.data;
};

// Analytics
export const getDashboardAnalytics = async () => {
  const response = await api.get('/api/analytics/dashboard');
  return response.data;
};

// Agent Logs
export const getAgentLogs = async (agentName = null, limit = 50) => {
  const params = { limit };
  if (agentName) params.agent_name = agentName;
  
  const response = await api.get('/api/agents/logs', { params });
  return response.data;
};

export default api;
