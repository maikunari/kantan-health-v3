#!/usr/bin/env python3
"""
Publish Approved Providers to WordPress
Syncs providers with status='approved' from PostgreSQL to WordPress CPTs.
"""

from wordpress_sync import WordPressHealthcareSync
from postgres_integration import Provider
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://postgres:password@localhost:5432/directory")
Session = sessionmaker(bind=engine)
session = Session()
providers = session.query(Provider).filter_by(status="approved").limit(50).all()
sync = WordPressHealthcareSync()
for provider in providers:
    sync.create_wordpress_post(provider.__dict__)
    provider.status = "published"
    session.commit()
session.close()