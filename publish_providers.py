#!/usr/bin/env python3
"""
Publish providers to WordPress
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.core.pipeline import UnifiedPipeline, PipelineMode

# Initialize pipeline
pipeline = UnifiedPipeline()

# Run publishing phase
print("🚀 Starting WordPress publishing...")
results = pipeline.run(mode=PipelineMode.PUBLISH, limit=25)

print(f"\n✅ Publishing complete!")
print(f"   Created: {results['phases'].get('publishing', {}).get('created', 0)}")
print(f"   Updated: {results['phases'].get('publishing', {}).get('updated', 0)}")
print(f"   Failed: {results['phases'].get('publishing', {}).get('failed', 0)}")