#!/usr/bin/env python3
"""
Database Models
SQLAlchemy models for the healthcare directory
"""

from sqlalchemy import Column, Integer, String, Text, Float, JSON, TIMESTAMP, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Provider(Base):
    """Healthcare provider model"""
    __tablename__ = "providers"
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Basic information
    provider_name = Column(String(255), nullable=False, index=True)
    provider_name_romaji = Column(String(500))  # Romanized version for Japanese names
    address = Column(Text)
    city = Column(String(100), index=True)
    prefecture = Column(String(100))
    district = Column(String(100))
    phone = Column(String(50))
    website = Column(Text)
    google_place_id = Column(String(255), unique=True, index=True)
    
    # Medical information
    specialties = Column(JSON)
    english_proficiency = Column(String(50))
    proficiency_score = Column(Integer, default=0)
    
    # Reviews and ratings
    rating = Column(Float)
    total_reviews = Column(Integer)
    review_content = Column(JSON)
    review_keywords = Column(JSON)
    review_highlights = Column(JSON)
    
    # AI-generated content
    ai_description = Column(Text)
    ai_excerpt = Column(Text)
    review_summary = Column(Text)
    english_experience_summary = Column(Text)
    seo_title = Column(String(100))
    seo_meta_description = Column(String(200))
    selected_featured_image = Column(Text)
    
    # Location data
    latitude = Column(Float)
    longitude = Column(Float)
    nearest_station = Column(Text)
    
    
    # Accessibility
    business_hours = Column(JSON)
    wheelchair_accessible = Column(String(50))
    parking_available = Column(String(50))
    
    # Status and tracking
    status = Column(String(50), default="pending", index=True)
    created_at = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # WordPress integration
    wordpress_post_id = Column(Integer, index=True)
    last_wordpress_sync = Column(TIMESTAMP)
    content_hash = Column(String(64), index=True)
    wordpress_status = Column(String(20), default="pending", index=True)
    
    # Deduplication fingerprints
    primary_fingerprint = Column(String(32), index=True)
    secondary_fingerprint = Column(String(32), index=True)
    fuzzy_fingerprint = Column(String(32), index=True)


class Metric(Base):
    """System metrics for tracking performance"""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(String, index=True)
    metric_type = Column(String(50), index=True)
    value = Column(Float)
    details = Column(JSON)


class ActivityLog(Base):
    """Activity logging for system operations"""
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action = Column(String(100), nullable=False)
    details = Column(JSON)
    source = Column(String(50))
    user = Column(String(100))
    status = Column(String(20))
    duration = Column(Float)


class PipelineRun(Base):
    """Track pipeline execution runs"""
    __tablename__ = "pipeline_runs"
    
    id = Column(Integer, primary_key=True)
    run_id = Column(String(36), unique=True, index=True)
    run_type = Column(String(50))
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(20), default="running")
    
    # Counters
    total_providers = Column(Integer, default=0)
    successful_providers = Column(Integer, default=0)
    failed_providers = Column(Integer, default=0)
    
    # Phase tracking
    collection_count = Column(Integer, default=0)
    content_generated = Column(Integer, default=0)
    wordpress_synced = Column(Integer, default=0)
    
    # Cost tracking
    api_calls = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Configuration
    config = Column(JSON)
    errors = Column(JSON)


class PipelineStep(Base):
    """Track individual steps within a pipeline run"""
    __tablename__ = "pipeline_steps"
    
    id = Column(Integer, primary_key=True)
    run_id = Column(String(36), index=True)
    provider_id = Column(Integer, index=True)
    provider_name = Column(String(255))
    step_name = Column(String(50))
    status = Column(String(20))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    details = Column(JSON)


class WordPressSyncOperation(Base):
    """Track WordPress sync operations"""
    __tablename__ = "wordpress_sync_operations"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    operation_type = Column(String(50))
    provider_id = Column(Integer, index=True)
    wordpress_post_id = Column(Integer)
    status = Column(String(20))
    error_message = Column(Text)
    content_hash_before = Column(String(64))
    content_hash_after = Column(String(64))
    fields_updated = Column(JSON)
    duration = Column(Float)