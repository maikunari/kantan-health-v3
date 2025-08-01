#!/usr/bin/env python3
"""
Update Google Places data for a single provider
"""

import argparse
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from postgres_integration import Provider, get_postgres_config
from google_places_integration import GooglePlacesIntegration
from activity_logger import activity_logger

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Update Google Places data for a single provider')
    parser.add_argument('--provider-id', type=int, required=True, help='Provider ID to update')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    args = parser.parse_args()
    
    # Initialize database
    config = get_postgres_config()
    engine = create_engine(
        f"postgresql://{config['user']}:{config['password']}@{config['host']}:5432/{config['database']}"
    )
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get provider
        provider = session.query(Provider).filter_by(id=args.provider_id).first()
        
        if not provider:
            logger.error(f"Provider with ID {args.provider_id} not found")
            return 1
        
        logger.info(f"Updating Google Places data for: {provider.provider_name}")
        
        if args.dry_run:
            logger.info("DRY RUN - No changes will be made")
            return 0
        
        # Initialize Google Places integration
        gp_integration = GooglePlacesIntegration()
        
        updated_fields = []
        
        # Fetch fresh Google Places data
        if provider.google_place_id:
            logger.info(f"Using existing Google Place ID: {provider.google_place_id}")
            place_details = gp_integration.get_place_details(provider.google_place_id)
        else:
            logger.info("Searching for provider on Google Places...")
            search_query = f"{provider.provider_name} {provider.address}"
            place_details = gp_integration.search_and_get_details(search_query)
        
        if place_details:
            # Update business hours
            if 'opening_hours' in place_details:
                provider.business_hours = place_details.get('opening_hours', {}).get('weekday_text', [])
                updated_fields.append('business_hours')
                logger.info("✓ Updated business hours")
            
            # Update rating and reviews
            if 'rating' in place_details:
                provider.rating = place_details.get('rating')
                updated_fields.append('rating')
                logger.info(f"✓ Updated rating: {provider.rating}")
            
            if 'user_ratings_total' in place_details:
                provider.total_reviews = place_details.get('user_ratings_total')
                updated_fields.append('total_reviews')
                logger.info(f"✓ Updated review count: {provider.total_reviews}")
            
            # Update wheelchair accessibility
            if 'wheelchair_accessible_entrance' in place_details:
                provider.wheelchair_accessible = place_details.get('wheelchair_accessible_entrance')
                updated_fields.append('wheelchair_accessible')
                logger.info(f"✓ Updated wheelchair accessibility: {provider.wheelchair_accessible}")
            
            # Update parking availability (if available in place details)
            # Note: Google Places API doesn't always provide parking info directly
            
            # Update phone number if missing
            if not provider.phone and 'formatted_phone_number' in place_details:
                provider.phone = place_details.get('formatted_phone_number')
                updated_fields.append('phone')
                logger.info(f"✓ Updated phone: {provider.phone}")
            
            # Update website if missing
            if not provider.website and 'website' in place_details:
                provider.website = place_details.get('website')
                updated_fields.append('website')
                logger.info(f"✓ Updated website: {provider.website}")
            
            # Update Google Place ID if not set
            if not provider.google_place_id and 'place_id' in place_details:
                provider.google_place_id = place_details.get('place_id')
                updated_fields.append('google_place_id')
                logger.info(f"✓ Updated Google Place ID: {provider.google_place_id}")
            
            # Commit changes
            if updated_fields:
                session.commit()
                logger.info(f"Successfully updated {len(updated_fields)} fields: {', '.join(updated_fields)}")
                
                # Log activity
                activity_logger.log_activity(
                    activity_type='update_google_data_single',
                    activity_category='data_quality',
                    description=f'Updated Google Places data for {provider.provider_name}',
                    provider_id=provider.id,
                    provider_name=provider.provider_name,
                    details={
                        'updated_fields': updated_fields,
                        'field_count': len(updated_fields)
                    },
                    status='success'
                )
            else:
                logger.warning("No fields were updated - all data already complete")
        else:
            logger.error("Failed to fetch Google Places data")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Error updating provider: {str(e)}")
        session.rollback()
        
        # Log error
        activity_logger.log_activity(
            activity_type='update_google_data_single',
            activity_category='data_quality',
            description=f'Failed to update Google Places data for provider {args.provider_id}',
            provider_id=args.provider_id,
            details={'error': str(e)},
            status='error',
            error_message=str(e)
        )
        
        return 1
        
    finally:
        session.close()

if __name__ == "__main__":
    exit(main())