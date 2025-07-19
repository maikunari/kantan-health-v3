export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/auth/login',
  LOGOUT: '/auth/logout',
  CHECK_AUTH: '/auth/check',
  CURRENT_USER: '/auth/me',

  // Providers
  PROVIDERS: '/providers',
  PROVIDER_STATS: '/providers/stats',
  PROVIDER_BULK_UPDATE: '/providers/bulk-update',

  // Dashboard
  DASHBOARD_OVERVIEW: '/dashboard/overview',
  DASHBOARD_TIMELINE: '/dashboard/metrics/timeline',
  DASHBOARD_COSTS: '/dashboard/metrics/costs',
  SYSTEM_HEALTH: '/dashboard/system/health',

  // Content Generation
  CONTENT_GENERATE: '/content/generate',
  CONTENT_STATUS: '/content/status',
  CONTENT_PREVIEW: '/content/preview',
  CONTENT_REGENERATE: '/content/regenerate',
  CONTENT_BATCH_STATUS: '/content/batch-status',

  // WordPress Sync
  SYNC: '/sync/sync',
  SYNC_STATUS: '/sync/status',
  SYNC_CHECK: '/sync/check',
  SYNC_TEST_CONNECTION: '/sync/test-connection',
  SYNC_FORCE_UPDATE: '/sync/force-update',
  SYNC_BATCH_STATUS: '/sync/batch-status',
};