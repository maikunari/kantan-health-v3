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

  // Settings
  SETTINGS_CONFIG: '/api/settings/config',
  SETTINGS_UPDATE_WORDPRESS: '/api/settings/config/wordpress',
  SETTINGS_UPDATE_GOOGLE: '/api/settings/config/google',
  SETTINGS_UPDATE_CLAUDE: '/api/settings/config/claude',
  SETTINGS_UPDATE_ADMIN: '/api/settings/config/admin',
  SETTINGS_TEST_WORDPRESS: '/api/settings/test/wordpress',
  SETTINGS_TEST_GOOGLE: '/api/settings/test/google',
  SETTINGS_TEST_CLAUDE: '/api/settings/test/claude',
  SETTINGS_BACKUP: '/api/settings/backup',

  // Data Quality
  DATA_QUALITY_OVERVIEW: '/api/data-quality/overview',
  DATA_QUALITY_PROVIDER_COMPLETENESS: '/api/data-quality/provider',
  DATA_QUALITY_MISSING_FIELDS: '/api/data-quality/providers/missing-fields',

  // Data Completion
  DATA_COMPLETION_GEOCODE: '/api/data-completion/geocode',
  DATA_COMPLETION_GOOGLE_PLACES: '/api/data-completion/google-places',
  DATA_COMPLETION_AI_CONTENT: '/api/data-completion/ai-content',
  DATA_COMPLETION_COMPLETE_ALL: '/api/data-completion/complete-all',
  DATA_COMPLETION_PROVIDER_FIELDS: '/api/data-completion/provider',
  DATA_COMPLETION_STATUS: '/api/data-completion/status',
};