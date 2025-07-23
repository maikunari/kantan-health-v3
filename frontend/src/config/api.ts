export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/api/auth/login',
  LOGOUT: '/api/auth/logout',
  CHECK_AUTH: '/api/auth/check',
  CURRENT_USER: '/api/auth/me',

  // Providers
  PROVIDERS: '/api/providers',
  PROVIDER_STATS: '/api/providers/stats',
  PROVIDER_BULK_UPDATE: '/api/providers/bulk-update',
  
  // Add Providers
  ADD_SPECIFIC_PROVIDER: '/api/providers/add-specific',
  ADD_GEOGRAPHIC_PROVIDERS: '/api/providers/add-geographic',
  VALIDATE_PLACE_ID: '/api/providers/validate-place-id',
  SEARCH_PREVIEW: '/api/providers/search-preview',

  // Dashboard
  DASHBOARD_OVERVIEW: '/api/dashboard/overview',
  DASHBOARD_TIMELINE: '/api/dashboard/metrics/timeline',
  DASHBOARD_COSTS: '/api/dashboard/metrics/costs',
  SYSTEM_HEALTH: '/api/dashboard/system/health',

  // Content Generation
  CONTENT_GENERATE: '/api/content/generate',
  CONTENT_STATUS: '/api/content/status',
  CONTENT_PREVIEW: '/api/content/preview',
  CONTENT_REGENERATE: '/api/content/regenerate',
  CONTENT_BATCH_STATUS: '/api/content/batch-status',
  CONTENT_CHECK_PROVIDERS: '/api/content/check-providers',

  // WordPress Sync
  SYNC: '/api/sync/sync',
  SYNC_STATUS: '/api/sync/status',
  SYNC_CHECK: '/api/sync/check',
  SYNC_TEST_CONNECTION: '/api/sync/test-connection',
  SYNC_FORCE_UPDATE: '/api/sync/force-update',
  SYNC_BATCH_STATUS: '/api/sync/batch-status',
};