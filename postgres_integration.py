#!/usr/bin/env python3
"""
PostgreSQL Integration Module
Provides robust database operations for the Healthcare Directory automation.
Replaces airtable_integration.py for PostgreSQL storage.
"""

import os
import time
from typing import List, Dict, Tuple, Set, Any
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, JSON, text
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class Provider(Base):
    __tablename__ = "providers"
    id = Column(Integer, primary_key=True)
    provider_name = Column(String(255), nullable=False)
    address = Column(Text)
    city = Column(String(100))
    prefecture = Column(String(100))
    district = Column(String(100))  # Ward/district within city (sublocality_level_1)
    phone = Column(String(50))
    website = Column(Text)
    specialties = Column(JSON)
    english_proficiency = Column(String(50))
    rating = Column(Float)
    total_reviews = Column(Integer)
    review_content = Column(JSON)
    review_keywords = Column(JSON)
    review_highlights = Column(JSON)
    photo_urls = Column(JSON)
    nearest_station = Column(Text)
    status = Column(String(50), default="pending")
    created_at = Column(String)
    # New columns for WordPress integration
    wordpress_post_id = Column(Integer)
    ai_description = Column(Text)
    ai_excerpt = Column(Text)  # Short excerpt for provider preview (50-100 words)
    google_place_id = Column(String(255))
    business_hours = Column(JSON)  # Store business hours data
    wheelchair_accessible = Column(String(50))  # Store wheelchair accessibility status
    parking_available = Column(String(50))  # Store parking availability status
    # Fingerprint columns for deduplication
    primary_fingerprint = Column(String(32))      # name + address + city hash
    secondary_fingerprint = Column(String(32))    # name + phone + city hash  
    fuzzy_fingerprint = Column(String(32))        # fuzzy matching fingerprint

class Metric(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True)
    timestamp = Column(String)
    metric_type = Column(String(50))
    value = Column(Float)
    details = Column(JSON)

class PostgresIntegration:
    def __init__(self):
        """Initialize PostgreSQL connection with environment validation"""
        self.load_environment()
        self.engine = create_engine(f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:5432/directory")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._existing_names_cache = None

    def load_environment(self):
        """Load and validate environment variables"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', '.env')
        load_dotenv(config_path)
        self.db_user = os.getenv("POSTGRES_USER", "postgres")
        self.db_password = os.getenv("POSTGRES_PASSWORD", "password")
        self.db_host = os.getenv("POSTGRES_HOST", "localhost")
        if not self.db_user or not self.db_password:
            raise ValueError("POSTGRES_USER or POSTGRES_PASSWORD not found in config/.env")

    def validate_schema(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate database schema"""
        try:
            expected_fields = {
                "provider_name", "address", "city", "prefecture", "district", "phone", "website",
                "specialties", "english_proficiency", "rating", "total_reviews",
                "review_content", "review_keywords", "review_highlights", "photo_urls",
                "nearest_station", "status", "created_at", "wordpress_post_id", 
                "ai_description", "ai_excerpt", "google_place_id", "business_hours", "wheelchair_accessible",
                "parking_available"
            }
            current_fields = set(Provider.__table__.columns.keys())
            missing_fields = expected_fields - current_fields
            validation_report = {
                "total_fields": len(current_fields),
                "expected_fields": len(expected_fields),
                "missing_fields": list(missing_fields),
                "field_coverage": len(current_fields & expected_fields) / len(expected_fields) * 100
            }
            return len(missing_fields) == 0, validation_report
        except Exception as e:
            return False, {"error": f"Schema validation failed: {str(e)}"}

    def get_existing_provider_names(self, force_refresh: bool = False) -> Set[str]:
        """Fetch existing provider names for duplicate detection"""
        if self._existing_names_cache is not None and not force_refresh:
            return self._existing_names_cache
        try:
            print("📋 Fetching existing provider names...")
            session = self.Session()
            providers = session.query(Provider.provider_name).filter(Provider.provider_name != "").all()
            self._existing_names_cache = {p.provider_name for p in providers}
            print(f"📊 Found {len(self._existing_names_cache)} existing providers")
            session.close()
            return self._existing_names_cache
        except Exception as e:
            print(f"⚠️ Error fetching existing providers: {str(e)}")
            return set()

    def validate_provider_data(self, provider: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate provider data before saving"""
        try:
            required_fields = ["provider_name", "address"]
            for field in required_fields:
                value = provider.get(field, "").strip()
                if not value:
                    return False, f"Missing required field: {field}"
            if "rating" in provider and provider["rating"]:
                if not isinstance(provider["rating"], (int, float)) or not (0 <= provider["rating"] <= 5):
                    return False, "Rating must be a number between 0 and 5"
            if "total_reviews" in provider and provider["total_reviews"]:
                if not isinstance(provider["total_reviews"], int) or provider["total_reviews"] < 0:
                    return False, "Total Reviews must be a non-negative integer"
            if "proficiency_score" in provider and provider["proficiency_score"]:
                if not isinstance(provider["proficiency_score"], int) or not (0 <= provider["proficiency_score"] <= 5):
                    return False, "Proficiency Score must be an integer between 0 and 5"
            for field in ["provider_name", "address", "city", "prefecture"]:
                if provider.get(field):
                    provider[field] = self._clean_text(provider[field])
            return True, "Valid"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text data"""
        if not isinstance(text, str):
            return str(text)
        return " ".join(text.strip().split())

    def save_providers(self, providers: List[Dict[str, Any]], batch_size: int = 10) -> Tuple[int, int]:
        """Save providers to PostgreSQL with batch operations"""
        saved_count = 0
        error_count = 0
        valid_providers = []
        existing_names = self.get_existing_provider_names()

        print(f"🔍 Validating {len(providers)} providers...")
        for provider in providers:
            try:
                is_valid, message = self.validate_provider_data(provider)
                if not is_valid:
                    print(f"❌ Invalid data for {provider.get('provider_name', 'Unknown')}: {message}")
                    error_count += 1
                    continue
                if provider.get("provider_name", "") in existing_names:
                    print(f"⚠️ Skipping {provider['provider_name']} - already exists")
                    continue
                valid_providers.append(provider)
                print(f"✅ Validated: {provider['provider_name']} with status {provider.get('status', 'Not set')}")
            except Exception as e:
                print(f"❌ Error validating {provider.get('provider_name', 'Unknown')}: {str(e)}")
                error_count += 1

        if not valid_providers:
            print("⚠️ No valid providers to save")
            return saved_count, error_count

        print(f"💾 Batch saving {len(valid_providers)} valid providers...")
        for i in range(0, len(valid_providers), batch_size):
            batch = valid_providers[i:i + batch_size]
            success = self._save_batch_with_retry(batch)
            if success:
                saved_count += len(batch)
                for provider in batch:
                    print(f"✅ Saved: {provider['provider_name']} with status {provider.get('status', 'pending')}")
            else:
                error_count += len(batch)
            if i + batch_size < len(valid_providers):
                time.sleep(0.2)

        if saved_count > 0:
            new_names = {p["provider_name"] for p in valid_providers[:saved_count]}
            if self._existing_names_cache is not None:
                self._existing_names_cache.update(new_names)

        return saved_count, error_count

    def _save_batch_with_retry(self, batch: List[Dict[str, Any]], max_retries: int = 3) -> bool:
        """Save a batch of providers with retry logic"""
        for attempt in range(max_retries):
            try:
                session = self.Session()
                for provider in batch:
                    session.add(Provider(**provider))
                session.commit()
                session.close()
                return True
            except Exception as e:
                error_str = str(e)
                if "timeout" in error_str.lower() and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    print(f"⏳ Timeout, waiting {wait_time}s... (attempt {attempt + 1})")
                    time.sleep(wait_time)
                    continue
                print(f"❌ Error saving batch: {error_str}")
                return False
        return False

    def test_connection(self) -> Tuple[bool, str]:
        """Test PostgreSQL connection"""
        try:
            session = self.Session()
            session.execute(text("SELECT 1"))
            session.close()
            return True, "✅ PostgreSQL connection verified"
        except Exception as e:
            return False, f"❌ Connection failed: {str(e)}"

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            session = self.Session()
            total_providers = session.query(Provider).count()
            pending_providers = session.query(Provider).filter_by(status="pending").count()
            description_generated = session.query(Provider).filter_by(status="description_generated").count()
            published_providers = session.query(Provider).filter_by(status="published").count()
            session.close()
            return {
                "total_providers": total_providers,
                "pending_providers": pending_providers,
                "description_generated": description_generated,
                "published_providers": published_providers,
                "ready_for_wordpress": description_generated,
                "health_status": "healthy" if total_providers > 0 else "empty"
            }
        except Exception as e:
            return {"error": f"Could not retrieve stats: {str(e)}", "health_status": "error"}

if __name__ == "__main__":
    print("🧪 Testing PostgreSQL Integration Module")
    print("=" * 40)
    integration = PostgresIntegration()
    is_connected, message = integration.test_connection()
    print(f"Connection: {message}")
    if is_connected:
        is_valid, report = integration.validate_schema()
        print(f"\nSchema Validation: {'✅ Valid' if is_valid else '❌ Issues Found'}")
        print(f"Field Coverage: {report.get('field_coverage', 0):.1f}%")
        if report.get("missing_fields"):
            print(f"Missing Fields: {report['missing_fields']}")
        stats = integration.get_stats()
        print(f"\nDatabase Stats:")
        print(f"  Total Providers: {stats.get('total_providers', 'Unknown')}")
        print(f"  Active Providers: {stats.get('active_providers', 'Unknown')}")
        print(f"  Health Status: {stats.get('health_status', 'Unknown')}")