#!/usr/bin/env python3
"""
Generate AI content for a single provider
This script is designed to work with the Data Manager UI for individual provider regeneration
"""

import argparse
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from postgres_integration import Provider, get_postgres_config
from claude_description_generator import ProviderDescriptionGenerator
from claude_english_experience_summarizer import EnglishExperienceSummarizer
from claude_review_summarizer import ReviewSummarizer
from activity_logger import activity_logger
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Generate AI content for a single provider')
    parser.add_argument('--provider-id', type=int, required=True, help='Provider ID to generate content for')
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
        
        logger.info(f"Generating AI content for: {provider.provider_name}")
        
        if args.dry_run:
            logger.info("DRY RUN - No changes will be made")
            return 0
        
        # Initialize generators
        description_generator = ProviderDescriptionGenerator()
        english_experience_generator = EnglishExperienceSummarizer()
        review_summarizer = ReviewSummarizer()
        
        updated_fields = []
        
        # Generate AI description and SEO fields
        try:
            logger.info("Generating AI description and SEO content...")
            result = description_generator.generate_enhanced_description(provider)
            
            if result and result.get('success'):
                provider.ai_description = result.get('description')
                provider.ai_excerpt = result.get('excerpt')
                provider.seo_title = result.get('seo_title')
                provider.seo_meta_description = result.get('seo_meta_description')
                updated_fields.extend(['ai_description', 'ai_excerpt', 'seo_title', 'seo_meta_description'])
                logger.info("✓ Generated AI description and SEO content")
            else:
                logger.warning("Failed to generate AI description")
        except Exception as e:
            logger.error(f"Error generating AI description: {str(e)}")
        
        # Small delay between API calls
        time.sleep(1)
        
        # Generate English experience summary
        try:
            logger.info("Generating English experience summary...")
            english_exp = english_experience_generator.generate_english_experience_summary(provider)
            
            if english_exp:
                provider.english_experience_summary = english_exp
                updated_fields.append('english_experience_summary')
                logger.info("✓ Generated English experience summary")
        except Exception as e:
            logger.error(f"Error generating English experience: {str(e)}")
        
        # Small delay between API calls
        time.sleep(1)
        
        # Generate review summary if provider has reviews
        if provider.reviews and len(provider.reviews) > 0:
            try:
                logger.info("Generating review summary...")
                review_summary = review_summarizer.generate_review_summary(provider)
                
                if review_summary:
                    provider.review_summary = review_summary
                    updated_fields.append('review_summary')
                    logger.info("✓ Generated review summary")
            except Exception as e:
                logger.error(f"Error generating review summary: {str(e)}")
        
        # Commit changes
        if updated_fields:
            session.commit()
            logger.info(f"Successfully updated {len(updated_fields)} fields: {', '.join(updated_fields)}")
            
            # Log activity
            activity_logger.log_activity(
                activity_type='generate_ai_content_single',
                activity_category='content_generation',
                description=f'Generated AI content for {provider.provider_name}',
                provider_id=provider.id,
                provider_name=provider.provider_name,
                details={
                    'updated_fields': updated_fields,
                    'field_count': len(updated_fields)
                },
                status='success'
            )
        else:
            logger.warning("No fields were updated")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error generating provider content: {str(e)}")
        session.rollback()
        
        # Log error
        activity_logger.log_activity(
            activity_type='generate_ai_content_single',
            activity_category='content_generation',
            description=f'Failed to generate AI content for provider {args.provider_id}',
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