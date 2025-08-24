export interface Provider {
  id: number;
  provider_name: string;
  address: string;
  city: string;
  prefecture?: string;
  district?: string;
  ward?: string;
  phone?: string;
  website?: string;
  specialties?: any;
  english_proficiency: string;
  english_proficiency_score: number;
  rating?: number;
  total_reviews?: number;
  review_content?: string;
  review_keywords?: string;
  review_highlights?: string;
  review_summary?: string;
  english_experience_summary?: string;
  business_hours?: any;
  ai_description?: string;
  ai_english_experience?: string;
  ai_review_summary?: string;
  ai_excerpt?: string;
  seo_title?: string;
  seo_description?: string;
  seo_meta_description?: string;
  seo_focus_keyword?: string;
  seo_keywords?: string;
  featured_image_url?: string;
  selected_featured_image?: string;
  photo_urls?: string[];
  status: 'pending' | 'approved' | 'rejected' | 'description_generated' | 'published';
  wordpress_post_id?: number;
  wordpress_id?: number;
  last_synced?: string;
  last_wordpress_sync?: string;
  created_at?: string;
  latitude?: number;
  longitude?: number;
  google_place_id?: string;
  nearest_station?: string;
  wheelchair_accessible?: string;
  parking_available?: string;
  primary_fingerprint?: string;
  secondary_fingerprint?: string;
  fuzzy_fingerprint?: string;
  content_hash?: string;
  wordpress_status?: string;
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
    total_providers: number;
    total_approved: number;
    total_pending: number;
    with_description: number;
    with_experience: number;
    with_reviews: number;
    with_seo: number;
    fully_complete: number;
    pending_content: number;
  };
}

export interface DataQualityField {
  field_name: string;
  display_name: string;
  category: 'basic' | 'location' | 'content' | 'seo' | 'metadata' | 'accessibility';
  required: boolean;
  completed: number;
  missing: number;
  percentage: number;
}

export interface ProviderCompleteness {
  provider_id: number;
  provider_name: string;
  completeness_score: number;
  missing_fields: string[];
  field_status: Record<string, boolean>;
}

export interface DataQualityOverview {
  total_providers: number;
  average_completeness: number;
  field_completeness: DataQualityField[];
  providers_by_completeness: {
    complete: number;
    almost_complete: number;
    partial: number;
    incomplete: number;
  };
  critical_missing: {
    missing_location: number;
    missing_ai_content: number;
    missing_contact: number;
    missing_accessibility: number;
  };
}