import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

export const checkProfile = async (payload) => {
  const response = await api.post('/api/check-profile', payload);
  return response.data;
};

export const getCheckHistory = async (limit = 20) => {
  const response = await api.get(`/api/check-history?limit=${limit}`);
  return response.data;
};

export const registerUser = async (payload) => {
  const response = await api.post('/api/register-user', payload);
  return response.data;
};

export const getProtectedUsers = async () => {
  const response = await api.get('/api/protected-users');
  return response.data;
};

export const toggleMonitoring = async (userId, active) => {
  const response = await api.patch(`/api/protected-users/${userId}/monitoring`, { active });
  return response.data;
};

export const deleteProtectedUser = async (userId) => {
  const response = await api.delete(`/api/protected-users/${userId}`);
  return response.data;
};

export const runSurveillance = async (username = '') => {
  const response = await api.post('/api/monitor-username', { username });
  return response.data;
};

export const getAlerts = async (status = '') => {
  const url = status ? `/api/alerts?status=${status}` : '/api/alerts';
  const response = await api.get(url);
  return response.data;
};

export const updateAlertStatus = async (alertId, status) => {
  const response = await api.patch(`/api/alerts/${alertId}/status`, { status });
  return response.data;
};

export const dispatchEmailAlert = async (alertId) => {
  const response = await api.post(`/api/alerts/${alertId}/dispatch-email`);
  return response.data;
};

export const getDemoProfiles = async (search = '') => {
  const url = search ? `/api/demo-profiles?search=${encodeURIComponent(search)}` : '/api/demo-profiles';
  const response = await api.get(url);
  return response.data;
};

export const createDemoProfile = async (payload) => {
  const response = await api.post('/api/demo-profiles', payload);
  return response.data;
};

export const deleteDemoProfile = async (profileId) => {
  const response = await api.delete(`/api/demo-profiles/${profileId}`);
  return response.data;
};

export const getAdminStats = async () => {
  const response = await api.get('/api/admin/stats');
  return response.data;
};

export const getAdminLogs = async (riskLevel = '', search = '') => {
  const response = await api.get(`/api/admin/logs?risk_level=${riskLevel}&search=${encodeURIComponent(search)}`);
  return response.data;
};

export const resetDemoDb = async () => {
  const response = await api.post('/api/admin/reset-demo');
  return response.data;
};

// ── Security / Device APIs ─────────────────────────────────────────────────

export const demoLogin = async (username, password) => {
  const response = await api.post('/api/demo-login', { username, password });
  return response.data;
};

export const getDeviceStatus = async (username) => {
  const response = await api.get(`/api/device-status/${username}`);
  return response.data;
};

export const verifyDevice = async (username, token) => {
  const response = await api.post('/api/verify-device', { username, token });
  return response.data;
};

export const getLoginHistory = async (username, limit = 20) => {
  const response = await api.get(`/api/login-history/${username}?limit=${limit}`);
  return response.data;
};

export default api;
