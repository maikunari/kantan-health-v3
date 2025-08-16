#!/usr/bin/env python3
"""
Create collection_progress table for tracking search coverage
Enables resumable collection and progress monitoring
"""

import os
import sys
import psycopg2
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def create_collection_progress_table():
    """Create table to track collection progress by geographic area"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'database': os.getenv('POSTGRES_DB', 'directory'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', '')
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        print("📊 Creating collection_progress table...")
        
        # Create collection_progress table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS collection_progress (
                id SERIAL PRIMARY KEY,
                prefecture VARCHAR(100),
                city VARCHAR(100),
                ward VARCHAR(100),
                search_type VARCHAR(50),  -- 'grid', 'district', 'text', 'nearby'
                search_params JSONB,       -- Store search parameters
                queries_executed INTEGER DEFAULT 0,
                providers_found INTEGER DEFAULT 0,
                providers_added INTEGER DEFAULT 0,
                duplicates_found INTEGER DEFAULT 0,
                last_search_date TIMESTAMP,
                next_page_token TEXT,      -- For resuming paginated searches
                search_status VARCHAR(20) DEFAULT 'pending',  -- pending, in_progress, completed, failed
                coverage_percentage DECIMAL(5,2),
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("📍 Creating indexes for collection_progress...")
        
        # Index for finding incomplete searches
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_collection_status 
            ON collection_progress(search_status, city, ward)
        """)
        
        # Index for geographic queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_collection_location 
            ON collection_progress(prefecture, city, ward)
        """)
        
        # Index for search type
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_collection_type 
            ON collection_progress(search_type)
        """)
        
        # Index for date-based queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_collection_date 
            ON collection_progress(last_search_date)
        """)
        
        print("📊 Creating search_queue table for planned searches...")
        
        # Create search queue for managing upcoming searches
        cur.execute("""
            CREATE TABLE IF NOT EXISTS search_queue (
                id SERIAL PRIMARY KEY,
                priority INTEGER DEFAULT 100,  -- Lower number = higher priority
                search_type VARCHAR(50),
                search_params JSONB,
                city VARCHAR(100),
                ward VARCHAR(100),
                specialty VARCHAR(100),
                estimated_results INTEGER,
                status VARCHAR(20) DEFAULT 'queued',  -- queued, processing, completed, failed
                attempts INTEGER DEFAULT 0,
                last_attempt TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        # Index for queue processing
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_queue_priority 
            ON search_queue(status, priority, created_at)
            WHERE status = 'queued'
        """)
        
        print("📊 Creating collection_stats table for daily summaries...")
        
        # Create collection stats table for tracking daily progress
        cur.execute("""
            CREATE TABLE IF NOT EXISTS collection_stats (
                id SERIAL PRIMARY KEY,
                collection_date DATE DEFAULT CURRENT_DATE,
                city VARCHAR(100),
                total_searches INTEGER DEFAULT 0,
                total_providers_found INTEGER DEFAULT 0,
                total_providers_added INTEGER DEFAULT 0,
                total_duplicates INTEGER DEFAULT 0,
                total_api_calls INTEGER DEFAULT 0,
                total_cost DECIMAL(10,2) DEFAULT 0.00,
                avg_providers_per_search DECIMAL(5,2),
                coverage_estimate DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index for date queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_stats_date 
            ON collection_stats(collection_date, city)
        """)
        
        # Commit changes
        conn.commit()
        print("✅ Collection progress tables created successfully")
        
        # Show table structure
        print("\n📋 Table structures created:")
        tables = ['collection_progress', 'search_queue', 'collection_stats']
        
        for table in tables:
            cur.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
                LIMIT 5
            """)
            
            print(f"\n  {table}:")
            for row in cur.fetchall():
                print(f"    - {row[0]}: {row[1]}")
            print("    ...")
        
        # Close connection
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


def add_sample_progress_data():
    """Add sample data to demonstrate the progress tracking"""
    
    db_params = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'database': os.getenv('POSTGRES_DB', 'directory'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', '')
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        print("\n📝 Adding sample progress data...")
        
        # Add some sample completed searches
        sample_searches = [
            ('Tokyo', 'Tokyo', 'Shinjuku', 'district', 'completed', 14, 8, 75.0),
            ('Tokyo', 'Tokyo', 'Shibuya', 'district', 'completed', 10, 6, 65.0),
            ('Tokyo', 'Tokyo', 'Minato', 'district', 'completed', 19, 12, 85.0),
            ('Kanagawa', 'Yokohama', None, 'grid', 'in_progress', 5, 3, 25.0),
            ('Osaka', 'Osaka', 'Namba', 'district', 'pending', 0, 0, 0.0),
        ]
        
        for prefecture, city, ward, search_type, status, found, added, coverage in sample_searches:
            cur.execute("""
                INSERT INTO collection_progress 
                (prefecture, city, ward, search_type, search_status, 
                 providers_found, providers_added, coverage_percentage, last_search_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT DO NOTHING
            """, (prefecture, city, ward, search_type, status, found, added, coverage))
        
        conn.commit()
        
        # Show current progress
        print("\n📊 Current collection progress:")
        cur.execute("""
            SELECT city, ward, search_status, providers_added, coverage_percentage
            FROM collection_progress
            ORDER BY coverage_percentage DESC
            LIMIT 10
        """)
        
        for row in cur.fetchall():
            ward_str = f"{row[1]}" if row[1] else "All"
            print(f"  - {row[0]} ({ward_str}): {row[2]} - {row[3]} providers ({row[4]:.1f}% coverage)")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"⚠️ Warning adding sample data: {str(e)}")


if __name__ == "__main__":
    print("🚀 Collection Progress Tracking Migration")
    print("=" * 50)
    print(f"Started: {datetime.now()}")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('config/.env')
    
    # Run migration
    create_collection_progress_table()
    
    # Add sample data
    add_sample_progress_data()
    
    print("\n" + "=" * 50)
    print(f"Completed: {datetime.now()}")
    print("✅ Collection progress tracking ready!")