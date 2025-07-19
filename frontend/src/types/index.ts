export interface Provider {
  id: number;
  provider_name: string;
  address: string;
  city: string;
  ward?: string;
  phone?: string;
  website?: string;
  specialties?: any;
  english_proficiency: string;
  english_proficiency_score: number;
  business_hours?: any;
  ai_description?: string;
  ai_english_experience?: string;
  ai_review_summary?: string;
  seo_title?: string;
  seo_description?: string;
  seo_focus_keyword?: string;
  seo_keywords?: string;
  featured_image_url?: string;
  status: 'pending' | 'approved' | 'rejected';
  wordpress_id?: number;
  last_synced?: string;
  created_at?: string;
}

export interface User {
  id: string;
  username: string;
}

export interface DashboardOverview {
  providers: {
    total: number;
    approved: number;
    pending: number;
    rejected: number;
    synced_to_wordpress: number;
    with_ai_content: number;
  };
  recent_activity: {
    new_providers_24h: number;
    recent_syncs_24h: number;
  };
  api_usage: Record<string, { total: number; count: number }>;
  content_generation: {
    total_approved: number;
    fully_processed: number;
    completion_rate: number;
  };
}

export interface ProviderStats {
  status_breakdown: Record<string, number>;
  top_cities: Array<{ city: string; count: number }>;
  proficiency_breakdown: Record<string, number>;
  content_completion: {
    total: number;
    with_description: number;
    with_experience: number;
    with_reviews: number;
    with_seo: number;
  };
}

export interface PaginationInfo {
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

export interface ProvidersResponse {
  providers: Provider[];
  pagination: PaginationInfo;
}

export interface SyncStatus {
  sync_overview: {
    total_providers: number;
    synced_providers: number;
    pending_sync: number;
    synced_last_24h: number;
    sync_percentage: number;
  };
  recent_operations: Array<{
    operation: string;
    status: string;
    count: number;
    last_operation: string;
  }>;
  recent_errors: Array<{
    provider_id: number;
    error: string;
    timestamp: string;
  }>;
  batch_running?: boolean;
}

export interface ContentGenerationStatus {
  batch_running: boolean;
  content_stats: {
    total_approved: number;
    with_description: number;
    with_experience: number;
    with_reviews: number;
    with_seo: number;
    fully_complete: number;
    pending_content: number;
  };
}