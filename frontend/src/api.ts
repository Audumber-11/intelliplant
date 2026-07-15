import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export const endpoints = {
  health: () => api.get('/health'),
  assets: () => api.get('/api/assets'),
  sensors: () => api.get('/api/sensors'),
  incidents: () => api.get('/api/incidents'),
  permits: () => api.get('/api/permits'),
  permitsActive: () => api.get('/api/permits/active'),
  riskCurrent: () => api.get('/api/risk/current'),
  dashboardKpis: () => api.get('/api/dashboard/kpis'),
  emergencyActive: () => api.get('/api/emergency/active'),
  audits: () => api.get('/api/audits'),
  heatmapLayout: () => api.get('/api/heatmap/layout'),
  heatmapLive: (gridSize?: number) => api.get('/api/heatmap/live', { params: { grid_size: gridSize || 15 } }),
  heatmapZones: () => api.get('/api/heatmap/zones'),
  heatmapLocations: () => api.get('/api/heatmap/locations'),
  heatmapMusterRoutes: () => api.get('/api/heatmap/muster-routes'),
  incidentPatterns: () => api.get('/api/incidents-analysis/patterns'),
  incidentRecurrence: () => api.get('/api/incidents-analysis/recurrence-risk'),
  permitConflicts: () => api.get('/api/permits-analysis/conflicts'),
  permitRisk: () => api.get('/api/permits-analysis/risk-assessment'),
  emergencyMetrics: () => api.get('/api/emergency-analysis/metrics'),
  emergencyMuster: (type?: string) => api.get('/api/emergency-analysis/muster-plan', { params: { emergency_type: type || 'fire' } }),
  auditChecklist: (standard: string) => api.get(`/api/audits/checklist/${standard}`),
  auditCompliance: () => api.get('/api/audits/compliance-score'),

  // CCTV Analytics
  cctvSummary: () => api.get('/api/cctv/summary'),
  cctvAlerts: (severity?: string) => api.get('/api/cctv/alerts', { params: { severity } }),
  cctvDetections: (limit?: number) => api.get('/api/cctv/detections', { params: { limit: limit || 50 } }),
  cctvHeatmap: () => api.get('/api/cctv/heatmap'),
  cctvProcess: () => api.post('/api/cctv/process'),
  cctvAck: (alertId: string, user?: string) => api.post(`/api/cctv/alerts/${alertId}/acknowledge`, { user: user || 'operator' }),

  // IoT / SCADA
  iotMetrics: () => api.get('/api/iot/metrics'),
  iotDevices: () => api.get('/api/iot/devices'),
  iotRecent: (limit?: number) => api.get('/api/iot/recent', { params: { limit: limit || 50 } }),
  iotStream: (count?: number) => api.post('/api/iot/stream', { count: count || 10 }),

  // Knowledge Graph
  kgData: () => api.get('/api/knowledge-graph/data'),
  kgStats: () => api.get('/api/knowledge-graph/stats'),
  kgRelated: (nodeId: string, depth?: number) => api.get(`/api/knowledge-graph/related/${nodeId}`, { params: { depth: depth || 2 } }),
  kgRiskPropagation: (sourceType: string, sourceId: string, maxDepth?: number) =>
    api.post('/api/knowledge-graph/risk-propagation', { source_type: sourceType, source_id: sourceId, max_depth: maxDepth || 4 }),

  // Orchestrator
  orchStatus: () => api.get('/api/orchestrator/status'),
  orchDecisions: (limit?: number) => api.get('/api/orchestrator/decisions', { params: { limit: limit || 10 } }),
  orchAgents: () => api.get('/api/orchestrator/agents'),
  orchStart: () => api.post('/api/orchestrator/start'),
  orchStop: () => api.post('/api/orchestrator/stop'),
};

export default api;
