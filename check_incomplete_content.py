#!/usr/bin/env python3
"""Check providers with incomplete content"""

from postgres_integration import PostgresIntegration, Provider
from sqlalchemy import or_, and_, func

db = PostgresIntegration()
session = db.Session()

# Check different states of incomplete content
incomplete_ai = session.query(Provider).filter(
    or_(Provider.ai_description.is_(None), Provider.ai_description == '')
).count()

incomplete_seo = session.query(Provider).filter(
    or_(Provider.seo_title.is_(None), Provider.seo_title == '')
).count()

incomplete_image = session.query(Provider).filter(
    or_(Provider.selected_featured_image.is_(None), Provider.selected_featured_image == '')
).count()

# Has AI content but no WordPress post
has_ai_no_wp = session.query(Provider).filter(
    Provider.ai_description.isnot(None)
).filter(
    Provider.ai_description != ''
).filter(
    Provider.wordpress_post_id.is_(None)
).count()

print('=== INCOMPLETE CONTENT SUMMARY ===')
print(f'Missing AI descriptions: {incomplete_ai}')
print(f'Missing SEO titles: {incomplete_seo}')
print(f'Missing featured images: {incomplete_image}')
print(f'Has AI content but no WordPress post: {has_ai_no_wp}')

# Show some examples
print('\n=== EXAMPLES OF INCOMPLETE PROVIDERS ===')

# Providers missing AI content
missing_ai = session.query(Provider).filter(
    or_(Provider.ai_description.is_(None), Provider.ai_description == '')
).limit(3).all()

print('\nMissing AI Content:')
for p in missing_ai:
    print(f'  ID {p.id}: {p.provider_name} (Status: {p.status})')

# Providers with AI but no WordPress
print('\nHas AI Content but No WordPress Post:')
has_content = session.query(Provider).filter(
    Provider.ai_description.isnot(None)
).filter(
    Provider.ai_description != ''
).filter(
    Provider.wordpress_post_id.is_(None)
).limit(3).all()

for p in has_content:
    print(f'  ID {p.id}: {p.provider_name} (Status: {p.status})')

session.close()

print('\n=== HOW TO PROCESS THESE PROVIDERS ===')
print('1. For missing AI content: Use run_unified_pipeline.py')
print('   python3 run_unified_pipeline.py --mode content --limit 50')
print('\n2. For specific providers:')
print('   python3 run_unified_pipeline.py --provider-ids 419 420 423')
print('\n3. For WordPress sync (providers with content):')
print('   python3 run_unified_pipeline.py --mode sync')
print('\n4. Or use the web interface:')
print('   - Go to Add Providers page')
print('   - The pipeline will automatically process incomplete providers')