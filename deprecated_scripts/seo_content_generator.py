#!/usr/bin/env python3
"""
SEO Content Generator
Generates SEO-optimized titles and meta descriptions for healthcare providers
focusing on location and specialties for search optimization.
"""

import logging
from typing import List, Dict, Tuple
from claude_description_generator import ClaudeDescriptionGenerator
from postgres_integration import PostgresIntegration, Provider

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SEOContentGenerator:
    """Standalone SEO content generator for healthcare providers"""
    
    def __init__(self):
        self.description_generator = ClaudeDescriptionGenerator()
        self.db = PostgresIntegration()
        logger.info("✅ SEO Content Generator initialized")
    
    def generate_seo_for_provider(self, provider: Provider) -> Tuple[str, str]:
        """Generate SEO content for a single provider"""
        provider_data = self._convert_provider_to_dict(provider)
        return self.description_generator.generate_seo_content(provider_data)
    
    def generate_seo_for_providers(self, providers: List[Provider], batch_size: int = 5) -> List[Tuple[str, str]]:
        """Generate SEO content for multiple providers"""
        provider_data_list = [self._convert_provider_to_dict(provider) for provider in providers]
        return self.description_generator.generate_batch_seo_content(provider_data_list, batch_size)
    
    def _convert_provider_to_dict(self, provider: Provider) -> Dict:
        """Convert Provider object to dictionary for SEO generation"""
        return {
            'provider_name': provider.provider_name,
            'city': provider.city,
            'prefecture': provider.prefecture,
            'district': provider.district,
            'specialties': provider.specialties if provider.specialties else ['General Medicine'],
            'english_proficiency': provider.english_proficiency,
            'rating': provider.rating,
            'total_reviews': provider.total_reviews,
            'review_content': provider.review_content
        }
    
    def update_providers_with_seo_content(self, providers: List[Provider], batch_size: int = 5) -> int:
        """Generate and update providers with SEO content"""
        session = self.db.Session()
        updated_count = 0
        
        try:
            logger.info(f"🚀 Generating SEO content for {len(providers)} providers...")
            
            # Generate SEO content in batches
            seo_content_results = self.generate_seo_for_providers(providers, batch_size)
            
            # Update providers with SEO content
            for provider, (seo_title, seo_meta) in zip(providers, seo_content_results):
                provider.seo_title = seo_title
                provider.seo_meta_description = seo_meta
                updated_count += 1
                
                logger.info(f"✅ Updated SEO content for {provider.provider_name}")
                logger.info(f"   Title: {seo_title}")
                logger.info(f"   Meta: {seo_meta}")
            
            session.commit()
            logger.info(f"🎉 Successfully updated {updated_count} providers with SEO content")
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error updating providers with SEO content: {str(e)}")
            
        finally:
            session.close()
        
        return updated_count
    
    def generate_seo_for_all_providers(self, batch_size: int = 5) -> int:
        """Generate SEO content for all providers that don't have it"""
        session = self.db.Session()
        
        try:
            # Get providers without SEO content
            providers = session.query(Provider).filter(
                Provider.seo_title.is_(None) | 
                Provider.seo_meta_description.is_(None) |
                Provider.seo_title == '' |
                Provider.seo_meta_description == ''
            ).all()
            
            if not providers:
                logger.info("ℹ️ All providers already have SEO content")
                return 0
                
            logger.info(f"🔍 Found {len(providers)} providers needing SEO content")
            return self.update_providers_with_seo_content(providers, batch_size)
            
        finally:
            session.close()
    
    def generate_seo_for_description_generated_providers(self, batch_size: int = 5) -> int:
        """Generate SEO content for providers with generated descriptions but no SEO content"""
        session = self.db.Session()
        
        try:
            # Get providers with descriptions but no SEO content
            providers = session.query(Provider).filter(
                Provider.status == 'description_generated',
                Provider.ai_description.isnot(None),
                Provider.ai_description != '',
                (Provider.seo_title.is_(None) | Provider.seo_title == '') |
                (Provider.seo_meta_description.is_(None) | Provider.seo_meta_description == '')
            ).all()
            
            if not providers:
                logger.info("ℹ️ All providers with descriptions already have SEO content")
                return 0
                
            logger.info(f"🔍 Found {len(providers)} providers with descriptions needing SEO content")
            return self.update_providers_with_seo_content(providers, batch_size)
            
        finally:
            session.close()


def main():
    """Main execution function"""
    generator = SEOContentGenerator()
    
    print("🔍 SEO CONTENT GENERATOR")
    print("=" * 50)
    print("Choose an option:")
    print("1. Generate SEO content for all providers without it")
    print("2. Generate SEO content for providers with descriptions only")
    print("3. Test with sample providers")
    print("4. Show statistics")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            print("\n🚀 Generating SEO content for all providers without it...")
            updated_count = generator.generate_seo_for_all_providers()
            print(f"✅ Updated {updated_count} providers with SEO content")
            
        elif choice == "2":
            print("\n🚀 Generating SEO content for providers with descriptions...")
            updated_count = generator.generate_seo_for_description_generated_providers()
            print(f"✅ Updated {updated_count} providers with SEO content")
            
        elif choice == "3":
            print("\n🧪 Testing with sample providers...")
            session = generator.db.Session()
            try:
                # Get 3 sample providers
                providers = session.query(Provider).limit(3).all()
                if providers:
                    print(f"Testing with {len(providers)} sample providers:")
                    for provider in providers:
                        print(f"   - {provider.provider_name} ({provider.city})")
                    
                    seo_results = generator.generate_seo_for_providers(providers, batch_size=3)
                    for provider, (title, meta) in zip(providers, seo_results):
                        print(f"\n✅ {provider.provider_name}:")
                        print(f"   Title: {title}")
                        print(f"   Meta: {meta}")
                else:
                    print("❌ No providers found in database")
            finally:
                session.close()
                
        elif choice == "4":
            print("\n📊 SEO Content Statistics...")
            session = generator.db.Session()
            try:
                total_providers = session.query(Provider).count()
                providers_with_seo = session.query(Provider).filter(
                    Provider.seo_title.isnot(None),
                    Provider.seo_title != '',
                    Provider.seo_meta_description.isnot(None),
                    Provider.seo_meta_description != ''
                ).count()
                
                print(f"   Total providers: {total_providers}")
                print(f"   Providers with SEO content: {providers_with_seo}")
                print(f"   Providers needing SEO content: {total_providers - providers_with_seo}")
                print(f"   SEO completion rate: {(providers_with_seo / total_providers * 100):.1f}%")
                
            finally:
                session.close()
                
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main() 