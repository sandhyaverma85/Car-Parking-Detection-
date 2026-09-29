// API client — all requests go through here
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: BASE_URL });

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Redirect to login on 401, except for auth endpoints
api.interceptors.response.use(
  (r) => r,
  (err) => {
    const isAuthEndpoint = err.config?.url?.includes('/auth/login') || err.config?.url?.includes('/auth/signup');
    if (err.response?.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────
export const login = (email: string, password: string) =>
  api.post('/api/v1/auth/login', { email, password });

// ── Parking ───────────────────────────────────────────────────
export const getParkingZones = () => api.get('/api/v1/parking/');
export const getNearbyParking = (lat: number, lon: number, radius = 1.0) =>
  api.get('/api/v1/parking/nearby', { params: { latitude: lat, longitude: lon, radius_km: radius } });

// ── Violations ────────────────────────────────────────────────
export const getViolations = (params?: Record<string, string>) =>
  api.get('/api/v1/violations/', { params });
export const updateViolationStatus = (id: number, status: string) =>
  api.patch(`/api/v1/violations/${id}/status`, { status });
export const getEvidenceUrl = (id: number) => `${BASE_URL}/api/v1/violations/${id}/evidence`;

// ── Cameras ───────────────────────────────────────────────────
export const getCameras = () => api.get('/api/v1/cameras/');
export const getCameraFootageUrl = (id: string) => {
  const token = localStorage.getItem('token');
  return `${BASE_URL}/api/v1/cameras/${id}/footage${token ? `?token=${encodeURIComponent(token)}` : ''}`;
};
export const getCameraTelemetry = (id: string) => api.get(`/api/v1/cameras/${id}/telemetry`);
export const getModelInfo = () => api.get('/api/v1/cameras/model-info');

// ── Analytics ─────────────────────────────────────────────────
export const getAnalytics = () => api.get('/api/v1/analytics/violations');
export const getOccupancyAnalytics = () => api.get('/api/v1/analytics/occupancy');

// ── Users ─────────────────────────────────────────────────────
export const getMe = () => api.get('/api/v1/users/me');
export const getUsers = () => api.get('/api/v1/users/');

// ── AI Dynamic Detection & Telemetry ──────────────────────────
export const detectImage = (formData: FormData) =>
  api.post('/api/v1/ai/detect-image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
export const getFeedTelemetry = (feedId: string) => api.get(`/api/v1/ai/telemetry/${feedId}`);
export const getFleetStatus = () => api.get('/api/v1/ai/fleet-status');

// ── WebSocket ─────────────────────────────────────────────────
export const WS_BASE = BASE_URL.replace('http', 'ws');

export default api;
