"""
Providers API Blueprint
Handles all provider-related operations including CRUD, search, and filtering
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import logging
from postgres_integration import Provider, get_postgres_config

logger = logging.getLogger(__name__)

providers_bp = Blueprint('providers', __name__)

# Database setup
config = get_postgres_config()
engine = create_engine(
    f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
)
Session = sessionmaker(bind=engine)

@providers_bp.route('/', methods=['GET'])
def get_providers():
    """Get paginated list of providers with optional filtering"""
    try:
        session = Session()
        
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Filter parameters
        status = request.args.get('status')
        city = request.args.get('city')
        specialty = request.args.get('specialty')
        proficiency = request.args.get('proficiency')
        search = request.args.get('search')
        
        # Sorting parameters
        sort_by = request.args.get('sort_by', 'created_at')  # Default sort by newest
        sort_order = request.args.get('sort_order', 'desc')  # Default descending
        
        # Build query
        query = session.query(Provider)
        
        if status:
            query = query.filter(Provider.status == status)
        if city:
            query = query.filter(Provider.city.ilike(f'%{city}%'))
        if specialty:
            query = query.filter(Provider.specialties.ilike(f'%{specialty}%'))
        if proficiency:
            query = query.filter(Provider.proficiency_score == int(proficiency))
        if search:
            query = query.filter(
                (Provider.provider_name.ilike(f'%{search}%')) |
                (Provider.address.ilike(f'%{search}%'))
            )
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        valid_sort_fields = {
            'created_at': Provider.created_at,
            'provider_name': Provider.provider_name,
            'city': Provider.city,
            'status': Provider.status,
            'proficiency_score': Provider.proficiency_score,
            'last_synced': Provider.last_wordpress_sync
        }
        
        if sort_by in valid_sort_fields:
            sort_field = valid_sort_fields[sort_by]
            if sort_order.lower() == 'asc':
                query = query.order_by(sort_field.asc())
            else:
                query = query.order_by(sort_field.desc())
        else:
            # Default sorting by newest first
            query = query.order_by(Provider.created_at.desc())
        
        # Apply pagination
        providers = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Convert to dict
        result = []
        for provider in providers:
            result.append({
                'id': provider.id,
                'provider_name': provider.provider_name,
                'address': provider.address,
                'city': provider.city,
                'ward': provider.district,
                'phone': provider.phone,
                'website': provider.website,
                'specialties': provider.specialties,
                'english_proficiency': provider.english_proficiency,
                'english_proficiency_score': provider.proficiency_score,
                'business_hours': provider.business_hours,
                'ai_description': provider.ai_description,
                'ai_english_experience': provider.english_experience_summary,
                'ai_review_summary': provider.review_summary,
                'seo_title': provider.seo_title,
                'seo_description': provider.seo_meta_description,
                'seo_focus_keyword': getattr(provider, 'seo_focus_keyword', None),
                'seo_keywords': getattr(provider, 'seo_keywords', None),
                'featured_image_url': provider.selected_featured_image,
                'status': provider.status,
                'wordpress_id': provider.wordpress_post_id,
                'last_synced': getattr(provider, 'last_synced', None),
                'created_at': provider.created_at if provider.created_at else None
            })
        
        session.close()
        
        return jsonify({
            'providers': result,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching providers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@providers_bp.route('/<int:provider_id>', methods=['GET'])
def get_provider(provider_id):
    """Get a single provider by ID"""
    try:
        session = Session()
        provider = session.query(Provider).filter_by(id=provider_id).first()
        
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404
        
        result = {
            'id': provider.id,
            'provider_name': provider.provider_name,
            'address': provider.address,
            'city': provider.city,
            'ward': provider.district,
            'phone': provider.phone,
            'website': provider.website,
            'specialties': provider.specialties,
            'english_proficiency': provider.english_proficiency,
            'english_proficiency_score': provider.proficiency_score,
            'business_hours': provider.business_hours,
            'ai_description': provider.ai_description,
            'ai_english_experience': provider.english_experience_summary,
            'ai_review_summary': provider.review_summary,
            'seo_title': provider.seo_title,
            'seo_description': provider.seo_meta_description,
            'seo_focus_keyword': getattr(provider, 'seo_focus_keyword', None),
            'seo_keywords': getattr(provider, 'seo_keywords', None),
            'featured_image_url': provider.selected_featured_image,
            'status': provider.status,
            'wordpress_id': provider.wordpress_post_id,
            'last_synced': getattr(provider, 'last_synced', None),
            'created_at': provider.created_at if provider.created_at else None
        }
        
        session.close()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error fetching provider {provider_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@providers_bp.route('/<int:provider_id>', methods=['PUT'])
def update_provider(provider_id):
    """Update a provider's details"""
    try:
        session = Session()
        provider = session.query(Provider).filter_by(id=provider_id).first()
        
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404
        
        data = request.json
        
        # Update allowed fields
        allowed_fields = [
            'provider_name', 'address', 'city', 'ward', 'phone', 'website',
            'specialties', 'english_proficiency', 'proficiency_score',
            'ai_description', 'english_experience_summary', 'review_summary',
            'seo_title', 'seo_meta_description', 'seo_focus_keyword', 'seo_keywords',
            'featured_image_url', 'status'
        ]
        
        for field in allowed_fields:
            if field in data:
                # Handle field name mapping
                if field == 'ward':
                    setattr(provider, 'district', data[field])
                else:
                    setattr(provider, field, data[field])
        
        session.commit()
        session.close()
        
        return jsonify({'message': 'Provider updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating provider {provider_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@providers_bp.route('/bulk-update', methods=['POST'])
def bulk_update_providers():
    """Bulk update provider status"""
    try:
        session = Session()
        data = request.json
        
        provider_ids = data.get('provider_ids', [])
        action = data.get('action')
        
        if not provider_ids or not action:
            return jsonify({'error': 'Missing provider_ids or action'}), 400
        
        if action not in ['approve', 'reject', 'pending']:
            return jsonify({'error': 'Invalid action'}), 400
        
        # Update providers
        status_map = {
            'approve': 'approved',
            'reject': 'rejected',
            'pending': 'pending'
        }
        
        updated = session.query(Provider).filter(
            Provider.id.in_(provider_ids)
        ).update(
            {'status': status_map[action]},
            synchronize_session=False
        )
        
        session.commit()
        session.close()
        
        return jsonify({
            'message': f'Updated {updated} providers',
            'updated_count': updated
        }), 200
        
    except Exception as e:
        logger.error(f"Error bulk updating providers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@providers_bp.route('/stats', methods=['GET'])
def get_provider_stats():
    """Get provider statistics"""
    try:
        session = Session()
        
        # Get counts by status
        status_stats = session.execute(text("""
            SELECT status, COUNT(*) as count
            FROM providers
            GROUP BY status
        """)).fetchall()
        
        # Get counts by city
        city_stats = session.execute(text("""
            SELECT city, COUNT(*) as count
            FROM providers
            WHERE city IS NOT NULL
            GROUP BY city
            ORDER BY count DESC
            LIMIT 10
        """)).fetchall()
        
        # Get counts by proficiency
        proficiency_stats = session.execute(text("""
            SELECT proficiency_score, COUNT(*) as count
            FROM providers
            WHERE proficiency_score IS NOT NULL
            GROUP BY proficiency_score
            ORDER BY proficiency_score
        """)).fetchall()
        
        # Get AI content completion stats
        content_stats = session.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(ai_description) as with_description,
                COUNT(english_experience_summary) as with_experience,
                COUNT(review_summary) as with_reviews,
                COUNT(seo_title) as with_seo
            FROM providers
        """)).fetchone()
        
        session.close()
        
        return jsonify({
            'status_breakdown': {row[0]: row[1] for row in status_stats},
            'top_cities': [{'city': row[0], 'count': row[1]} for row in city_stats],
            'proficiency_breakdown': {str(row[0]): row[1] for row in proficiency_stats},
            'content_completion': {
                'total': content_stats[0],
                'with_description': content_stats[1],
                'with_experience': content_stats[2],
                'with_reviews': content_stats[3],
                'with_seo': content_stats[4]
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching provider stats: {str(e)}")
        return jsonify({'error': str(e)}), 500