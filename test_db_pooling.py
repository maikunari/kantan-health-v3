#!/usr/bin/env python3
"""Test database connection pooling fix"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from src.core.database import DatabaseManager

def test_concurrent_access():
    """Test multiple concurrent database operations"""
    db = DatabaseManager()
    
    def db_operation(op_id):
        """Single database operation"""
        try:
            session = db.get_session()
            # Use proper SQLAlchemy query
            from src.core.database import Provider
            count = session.query(Provider).count()
            session.close()
            return f"Op {op_id}: Success (found {count} providers)"
        except Exception as e:
            return f"Op {op_id}: Failed - {str(e)}"
    
    print("Testing 10 concurrent database operations...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(db_operation, i) for i in range(10)]
        results = [f.result() for f in futures]
    
    # Check results
    successes = sum(1 for r in results if "Success" in r)
    failures = sum(1 for r in results if "Failed" in r)
    
    print(f"Results: {successes} successes, {failures} failures")
    for result in results[:3]:  # Show first 3 results
        print(f"  {result}")
    
    return successes == 10

if __name__ == "__main__":
    success = test_concurrent_access()
    if success:
        print("✅ Database pooling FIXED - All concurrent operations succeeded!")
    else:
        print("❌ Database pooling still has issues")
    sys.exit(0 if success else 1)