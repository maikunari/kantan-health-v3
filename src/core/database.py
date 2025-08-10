#!/usr/bin/env python3
"""
Unified Database Operations
Consolidates all database interactions with proper column naming
"""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, JSON, TIMESTAMP, or_, and_
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

# Load environment variables
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', '.env')
load_dotenv(config_path)

Base = declarative_base()


class Provider(Base):
    """Provider model with all fields properly mapped"""
    __tablename__ = "providers"
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Basic information
    provider_name = Column(String(255), nullable=False)
    address = Column(Text)
    city = Column(String(100))
    prefecture = Column(String(100))
    district = Column(String(100))  # Ward/district within city
    phone = Column(String(50))
    website = Column(Text)
    google_place_id = Column(String(255), unique=True)
    
    # Medical information
    specialties = Column(JSON)
    english_proficiency = Column(String(50))
    proficiency_score = Column(Integer, default=0)  # 0-5 numerical score
    
    # Reviews and ratings
    rating = Column(Float)
    total_reviews = Column(Integer)
    review_content = Column(JSON)
    review_keywords = Column(JSON)
    review_highlights = Column(JSON)
    
    # AI-generated content
    ai_description = Column(Text)
    ai_excerpt = Column(Text)
    review_summary = Column(Text)  # NOT ai_review_summary
    english_experience_summary = Column(Text)  # NOT ai_english_experience
    seo_title = Column(String(100))
    seo_meta_description = Column(String(200))
    selected_featured_image = Column(Text)
    
    # Location data
    latitude = Column(Float)
    longitude = Column(Float)
    nearest_station = Column(Text)
    
    # Photos
    photo_urls = Column(JSON)
    
    # Accessibility
    business_hours = Column(JSON)
    wheelchair_accessible = Column(String(50))
    parking_available = Column(String(50))
    
    # Status and tracking
    status = Column(String(50), default="pending")
    created_at = Column(String)
    
    # WordPress integration
    wordpress_post_id = Column(Integer)
    last_wordpress_sync = Column(TIMESTAMP)
    content_hash = Column(String(64))
    wordpress_status = Column(String(20), default="pending")
    
    # Deduplication fingerprints
    primary_fingerprint = Column(String(32))
    secondary_fingerprint = Column(String(32))
    fuzzy_fingerprint = Column(String(32))


class Metric(Base):
    """Metrics tracking for system performance"""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(String)
    metric_type = Column(String(50))
    value = Column(Float)
    details = Column(JSON)


class DatabaseManager:
    """Unified database manager with all operations"""
    
    def __init__(self):
        """Initialize database connection"""
        self.config = self._get_config()
        self.engine = self._create_engine()
        self.Session = sessionmaker(bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        logger.info("✅ Database manager initialized")
    
    def _get_config(self) -> Dict[str, str]:
        """Get database configuration from environment"""
        return {
            'user': os.getenv("POSTGRES_USER", "postgres"),
            'password': os.getenv("POSTGRES_PASSWORD", "password"),
            'host': os.getenv("POSTGRES_HOST", "localhost"),
            'database': os.getenv("POSTGRES_DB", "directory")
        }
    
    def _create_engine(self):
        """Create SQLAlchemy engine with connection pooling"""
        db_url = f"postgresql://{self.config['user']}:{self.config['password']}@{self.config['host']}:5432/{self.config['database']}"
        
        # Use NullPool to prevent connection issues
        return create_engine(db_url, poolclass=NullPool, echo=False)
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    # Provider operations
    
    def get_provider_by_id(self, provider_id: int) -> Optional[Provider]:
        """Get provider by ID"""
        session = self.Session()
        try:
            return session.query(Provider).filter_by(id=provider_id).first()
        finally:
            session.close()
    
    def get_provider_by_place_id(self, place_id: str) -> Optional[Provider]:
        """Get provider by Google Place ID"""
        session = self.Session()
        try:
            return session.query(Provider).filter_by(google_place_id=place_id).first()
        finally:
            session.close()
    
    def get_providers_needing_content(self, limit: int = None) -> List[Provider]:
        """Get providers that need AI content generation"""
        session = self.Session()
        try:
            query = session.query(Provider).filter(
                or_(
                    Provider.ai_description.is_(None),
                    Provider.ai_description == '',
                    Provider.seo_title.is_(None),
                    Provider.seo_title == '',
                    Provider.review_summary.is_(None),
                    Provider.review_summary == '',
                    Provider.english_experience_summary.is_(None),
                    Provider.english_experience_summary == ''
                )
            )
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        finally:
            session.close()
    
    def get_providers_needing_wordpress(self, limit: int = None) -> List[Provider]:
        """Get providers that need WordPress sync"""
        session = self.Session()
        try:
            query = session.query(Provider).filter(
                and_(
                    Provider.ai_description.isnot(None),
                    Provider.ai_description != '',
                    Provider.wordpress_post_id.is_(None)
                )
            )
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        finally:
            session.close()
    
    def get_providers_needing_update(self, limit: int = None) -> List[Provider]:
        """Get providers with content changes needing WordPress update"""
        session = self.Session()
        try:
            # This would work with content hash comparison
            query = session.query(Provider).filter(
                and_(
                    Provider.wordpress_post_id.isnot(None),
                    Provider.wordpress_status != 'synced'
                )
            )
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        finally:
            session.close()
    
    def create_or_update_provider(self, provider_data: Dict[str, Any]) -> Provider:
        """Create or update a provider"""
        session = self.Session()
        try:
            place_id = provider_data.get('google_place_id')
            
            if place_id:
                provider = session.query(Provider).filter_by(google_place_id=place_id).first()
            else:
                provider = None
            
            if not provider:
                provider = Provider()
                session.add(provider)
            
            # Update fields
            for key, value in provider_data.items():
                if hasattr(provider, key):
                    setattr(provider, key, value)
            
            # Set timestamps
            if not provider.created_at:
                provider.created_at = datetime.now().isoformat()
            
            session.commit()
            session.refresh(provider)
            
            return provider
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating/updating provider: {str(e)}")
            raise
        finally:
            session.close()
    
    def update_provider_content(self, provider_id: int, content_data: Dict[str, Any]) -> bool:
        """Update provider with AI-generated content"""
        session = self.Session()
        try:
            provider = session.query(Provider).filter_by(id=provider_id).first()
            
            if not provider:
                logger.error(f"Provider {provider_id} not found")
                return False
            
            # Map content fields correctly
            field_mapping = {
                'description': 'ai_description',
                'excerpt': 'ai_excerpt',
                'review_summary': 'review_summary',  # NOT ai_review_summary
                'english_experience_summary': 'english_experience_summary',  # NOT ai_english_experience
                'seo_title': 'seo_title',
                'seo_meta_description': 'seo_meta_description',
                'selected_featured_image': 'selected_featured_image'
            }
            
            for content_key, db_field in field_mapping.items():
                if content_key in content_data:
                    setattr(provider, db_field, content_data[content_key])
            
            # Update status if needed
            if provider.status == 'pending' and content_data.get('description'):
                provider.status = 'approved'
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating provider content: {str(e)}")
            return False
        finally:
            session.close()
    
    def update_wordpress_info(self, provider_id: int, wordpress_post_id: int, 
                            content_hash: str = None) -> bool:
        """Update WordPress sync information"""
        session = self.Session()
        try:
            provider = session.query(Provider).filter_by(id=provider_id).first()
            
            if not provider:
                return False
            
            provider.wordpress_post_id = wordpress_post_id
            provider.last_wordpress_sync = datetime.now()
            provider.wordpress_status = 'synced'
            
            if content_hash:
                provider.content_hash = content_hash
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating WordPress info: {str(e)}")
            return False
        finally:
            session.close()
    
    # Metric operations
    
    def log_metric(self, metric_type: str, value: float, details: Dict = None) -> None:
        """Log a metric"""
        session = self.Session()
        try:
            metric = Metric(
                timestamp=datetime.now().isoformat(),
                metric_type=metric_type,
                value=value,
                details=details or {}
            )
            session.add(metric)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging metric: {str(e)}")
        finally:
            session.close()
    
    # Utility methods
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        session = self.Session()
        try:
            total = session.query(Provider).count()
            approved = session.query(Provider).filter_by(status='approved').count()
            with_content = session.query(Provider).filter(
                Provider.ai_description.isnot(None),
                Provider.ai_description != ''
            ).count()
            synced = session.query(Provider).filter(
                Provider.wordpress_post_id.isnot(None)
            ).count()
            
            return {
                'total_providers': total,
                'approved_providers': approved,
                'providers_with_content': with_content,
                'wordpress_synced': synced,
                'pending_content': total - with_content,
                'pending_sync': with_content - synced
            }
        finally:
            session.close()
    
    def check_fingerprints(self, primary: str, secondary: str, fuzzy: str) -> Optional[Provider]:
        """Check for duplicate providers using fingerprints"""
        session = self.Session()
        try:
            # Check exact matches first
            provider = session.query(Provider).filter(
                or_(
                    Provider.primary_fingerprint == primary,
                    Provider.secondary_fingerprint == secondary
                )
            ).first()
            
            if provider:
                return provider
            
            # Check fuzzy match
            provider = session.query(Provider).filter(
                Provider.fuzzy_fingerprint == fuzzy
            ).first()
            
            return provider
        finally:
            session.close()