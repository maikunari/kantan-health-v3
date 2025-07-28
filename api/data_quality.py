"""
Data Quality API Blueprint
Handles data completeness tracking and quality metrics for providers
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
import os
import logging
from postgres_integration import Provider, get_postgres_config

logger = logging.getLogger(__name__)

data_quality_bp = Blueprint('data_quality', __name__)

# Database setup
config = get_postgres_config()
engine = create_engine(
    f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
)
Session = sessionmaker(bind=engine)

def calculate_field_completeness():
    """Calculate completeness for all tracked fields"""
    fields_config = [
        # Basic Information
        {'field': 'provider_name', 'display': 'Provider Name', 'category': 'basic', 'required': True},
        {'field': 'address', 'display': 'Address', 'category': 'basic', 'required': True},
        {'field': 'city', 'display': 'City', 'category': 'basic', 'required': True},
        {'field': 'phone', 'display': 'Phone Number', 'category': 'basic', 'required': False},
        {'field': 'website', 'display': 'Website', 'category': 'basic', 'required': False},
        {'field': 'specialties', 'display': 'Medical Specialties', 'category': 'basic', 'required': True},
        {'field': 'english_proficiency', 'display': 'English Proficiency', 'category': 'basic', 'required': True},
        {'field': 'proficiency_score', 'display': 'Proficiency Score', 'category': 'basic', 'required': True},
        
        # Location & Navigation
        {'field': 'latitude', 'display': 'Latitude', 'category': 'location', 'required': True},
        {'field': 'longitude', 'display': 'Longitude', 'category': 'location', 'required': True},
        {'field': 'google_place_id', 'display': 'Google Place ID', 'category': 'location', 'required': True},
        {'field': 'nearest_station', 'display': 'Nearest Station', 'category': 'location', 'required': False},
        
        # Accessibility
        {'field': 'wheelchair_accessible', 'display': 'Wheelchair Access', 'category': 'accessibility', 'required': False},
        {'field': 'parking_available', 'display': 'Parking Available', 'category': 'accessibility', 'required': False},
        
        # AI Generated Content
        {'field': 'ai_description', 'display': 'AI Description', 'category': 'content', 'required': True},
        {'field': 'ai_excerpt', 'display': 'AI Excerpt', 'category': 'content', 'required': False},
        {'field': 'english_experience_summary', 'display': 'English Experience', 'category': 'content', 'required': False},
        {'field': 'review_summary', 'display': 'Review Summary', 'category': 'content', 'required': False},
        
        # SEO & Marketing
        {'field': 'seo_title', 'display': 'SEO Title', 'category': 'seo', 'required': True},
        {'field': 'seo_meta_description', 'display': 'SEO Description', 'category': 'seo', 'required': True},
        {'field': 'selected_featured_image', 'display': 'Featured Image', 'category': 'seo', 'required': False},
        
        # Reviews & Ratings
        {'field': 'rating', 'display': 'Google Rating', 'category': 'metadata', 'required': False},
        {'field': 'total_reviews', 'display': 'Review Count', 'category': 'metadata', 'required': False},
        
        # Business Information
        {'field': 'business_hours', 'display': 'Business Hours', 'category': 'basic', 'required': False},
        {'field': 'photo_urls', 'display': 'Photo URLs', 'category': 'metadata', 'required': False},
    ]
    
    session = Session()
    try:
        total_providers = session.query(Provider).count()
        field_stats = []
        
        for field_config in fields_config:
            field_name = field_config['field']
            
            # Count non-null, non-empty values
            if field_name in ['photo_urls', 'business_hours', 'specialties']:
                # JSON fields - check for non-null and non-empty
                completed = session.execute(text(f"""
                    SELECT COUNT(*) FROM providers 
                    WHERE {field_name} IS NOT NULL 
                    AND {field_name}::text NOT IN ('[]', '{{}}', 'null', '""')
                """)).scalar()
            elif field_name in ['latitude', 'longitude', 'rating', 'total_reviews', 'proficiency_score']:
                # Numeric fields
                completed = session.execute(text(f"""
                    SELECT COUNT(*) FROM providers 
                    WHERE {field_name} IS NOT NULL
                """)).scalar()
            else:
                # Text fields - check for non-null and non-empty
                completed = session.execute(text(f"""
                    SELECT COUNT(*) FROM providers 
                    WHERE {field_name} IS NOT NULL 
                    AND TRIM({field_name}) != ''
                """)).scalar()
            
            missing = total_providers - completed
            percentage = (completed / total_providers * 100) if total_providers > 0 else 0
            
            field_stats.append({
                'field_name': field_name,
                'display_name': field_config['display'],
                'category': field_config['category'],
                'required': field_config['required'],
                'completed': completed,
                'missing': missing,
                'percentage': round(percentage, 1)
            })
        
        return field_stats
    finally:
        session.close()

@data_quality_bp.route('/overview', methods=['GET'])
def get_data_quality_overview():
    """Get comprehensive data quality overview"""
    try:
        session = Session()
        
        # Get total provider count
        total_providers = session.query(Provider).count()
        
        # Calculate field completeness
        field_completeness = calculate_field_completeness()
        
        # Calculate average completeness score
        required_fields = [f for f in field_completeness if f['required']]
        if required_fields:
            avg_completeness = sum(f['percentage'] for f in required_fields) / len(required_fields)
        else:
            avg_completeness = 0
        
        # Count critical missing data
        missing_location = session.execute(text("""
            SELECT COUNT(*) FROM providers 
            WHERE latitude IS NULL OR longitude IS NULL
        """)).scalar()
        
        missing_ai_content = session.execute(text("""
            SELECT COUNT(*) FROM providers 
            WHERE ai_description IS NULL OR TRIM(ai_description) = ''
        """)).scalar()
        
        missing_contact = session.execute(text("""
            SELECT COUNT(*) FROM providers 
            WHERE (phone IS NULL OR TRIM(phone) = '') 
            AND (website IS NULL OR TRIM(website) = '')
        """)).scalar()
        
        missing_accessibility = session.execute(text("""
            SELECT COUNT(*) FROM providers 
            WHERE wheelchair_accessible IS NULL 
            OR parking_available IS NULL
        """)).scalar()
        
        # Count providers by completeness tiers
        # Calculate individual provider completeness scores
        providers_completeness = []
        providers = session.query(Provider).all()
        
        for provider in providers:
            score = 0
            total_fields = len(required_fields)
            
            for field_config in required_fields:
                field_name = field_config['field_name']
                value = getattr(provider, field_name, None)
                
                if value is not None:
                    if isinstance(value, str) and value.strip():
                        score += 1
                    elif not isinstance(value, str):
                        score += 1
            
            completeness_percent = (score / total_fields * 100) if total_fields > 0 else 0
            providers_completeness.append(completeness_percent)
        
        # Categorize providers
        complete = sum(1 for p in providers_completeness if p >= 90)
        almost_complete = sum(1 for p in providers_completeness if 70 <= p < 90)
        partial = sum(1 for p in providers_completeness if 40 <= p < 70)
        incomplete = sum(1 for p in providers_completeness if p < 40)
        
        session.close()
        
        return jsonify({
            'total_providers': total_providers,
            'average_completeness': round(avg_completeness, 1),
            'field_completeness': field_completeness,
            'providers_by_completeness': {
                'complete': complete,
                'almost_complete': almost_complete,
                'partial': partial,
                'incomplete': incomplete
            },
            'critical_missing': {
                'missing_location': missing_location,
                'missing_ai_content': missing_ai_content,
                'missing_contact': missing_contact,
                'missing_accessibility': missing_accessibility
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching data quality overview: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_quality_bp.route('/provider/<int:provider_id>/completeness', methods=['GET'])
def get_provider_completeness(provider_id):
    """Get completeness details for a specific provider"""
    try:
        session = Session()
        provider = session.query(Provider).filter_by(id=provider_id).first()
        
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404
        
        # Define all trackable fields
        trackable_fields = {
            'provider_name': 'Provider Name',
            'address': 'Address',
            'city': 'City',
            'phone': 'Phone Number',
            'website': 'Website',
            'specialties': 'Medical Specialties',
            'proficiency_score': 'Proficiency Score',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'ai_description': 'AI Description',
            'ai_excerpt': 'AI Excerpt',
            'seo_title': 'SEO Title',
            'seo_meta_description': 'SEO Description',
            'english_experience_summary': 'English Experience',
            'review_summary': 'Review Summary',
            'business_hours': 'Business Hours',
            'wheelchair_accessible': 'Wheelchair Access',
            'parking_available': 'Parking Available',
            'selected_featured_image': 'Featured Image',
            'nearest_station': 'Nearest Station',
            'rating': 'Google Rating',
            'total_reviews': 'Review Count'
        }
        
        field_status = {}
        missing_fields = []
        completed_count = 0
        
        for field_name, display_name in trackable_fields.items():
            value = getattr(provider, field_name, None)
            is_complete = False
            
            if value is not None:
                if isinstance(value, str):
                    is_complete = bool(value.strip())
                elif isinstance(value, (dict, list)):
                    is_complete = bool(value)
                else:
                    is_complete = True
            
            field_status[field_name] = is_complete
            
            if is_complete:
                completed_count += 1
            else:
                missing_fields.append(display_name)
        
        completeness_score = (completed_count / len(trackable_fields) * 100)
        
        session.close()
        
        return jsonify({
            'provider_id': provider_id,
            'provider_name': provider.provider_name,
            'completeness_score': round(completeness_score, 1),
            'missing_fields': missing_fields,
            'field_status': field_status
        })
        
    except Exception as e:
        logger.error(f"Error fetching provider completeness: {str(e)}")
        return jsonify({'error': str(e)}), 500

@data_quality_bp.route('/providers/missing-fields', methods=['GET'])
def get_providers_missing_fields():
    """Get providers filtered by missing field types"""
    try:
        field_type = request.args.get('field_type', 'location')  # location, content, contact, accessibility
        limit = request.args.get('limit', 50, type=int)
        
        session = Session()
        
        if field_type == 'location':
            providers = session.query(Provider).filter(
                (Provider.latitude.is_(None)) | (Provider.longitude.is_(None))
            ).limit(limit).all()
        elif field_type == 'content':
            providers = session.query(Provider).filter(
                (Provider.ai_description.is_(None)) | (Provider.ai_description == '')
            ).limit(limit).all()
        elif field_type == 'contact':
            providers = session.query(Provider).filter(
                ((Provider.phone.is_(None)) | (Provider.phone == '')) &
                ((Provider.website.is_(None)) | (Provider.website == ''))
            ).limit(limit).all()
        elif field_type == 'accessibility':
            providers = session.query(Provider).filter(
                (Provider.wheelchair_accessible.is_(None)) |
                (Provider.parking_available.is_(None))
            ).limit(limit).all()
        else:
            providers = []
        
        result = []
        for provider in providers:
            result.append({
                'id': provider.id,
                'provider_name': provider.provider_name,
                'city': provider.city,
                'status': provider.status,
                'missing_reason': f'Missing {field_type} data'
            })
        
        session.close()
        
        return jsonify({
            'providers': result,
            'field_type': field_type,
            'count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error fetching providers with missing fields: {str(e)}")
        return jsonify({'error': str(e)}), 500