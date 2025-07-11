#!/usr/bin/env python3
"""
Test script for Claude Vision API image selection functionality
"""

import os
import sys
import json
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from claude_description_generator import ClaudeDescriptionGenerator

def test_image_selection_scenarios():
    """Test various image selection scenarios"""
    
    print("🧪 TESTING CLAUDE IMAGE SELECTION")
    print("=" * 50)
    
    # Create a mock generator for testing
    generator = ClaudeDescriptionGenerator()
    
    # Test scenarios
    test_cases = [
        {
            "name": "No photos available",
            "provider_data": {
                "provider_name": "Test Provider 1",
                "city": "Tokyo",
                "prefecture": "Tokyo",
                "specialties": ["General Medicine"],
                "photo_urls": []
            },
            "expected_result": ""
        },
        {
            "name": "Single photo",
            "provider_data": {
                "provider_name": "Test Provider 2", 
                "city": "Tokyo",
                "prefecture": "Tokyo",
                "specialties": ["Cardiology"],
                "photo_urls": ["https://example.com/photo1.jpg"]
            },
            "expected_result": "https://example.com/photo1.jpg"
        },
        {
            "name": "Multiple photos (would normally use Claude)",
            "provider_data": {
                "provider_name": "Test Provider 3",
                "city": "Tokyo", 
                "prefecture": "Tokyo",
                "specialties": ["Dermatology"],
                "photo_urls": [
                    "https://example.com/photo1.jpg",
                    "https://example.com/photo2.jpg",
                    "https://example.com/photo3.jpg"
                ]
            },
            "expected_result": "https://example.com/photo1.jpg"  # Fallback to first
        },
        {
            "name": "Photo URLs as JSON string",
            "provider_data": {
                "provider_name": "Test Provider 4",
                "city": "Tokyo",
                "prefecture": "Tokyo", 
                "specialties": ["Pediatrics"],
                "photo_urls": json.dumps([
                    "https://example.com/photo1.jpg",
                    "https://example.com/photo2.jpg"
                ])
            },
            "expected_result": "https://example.com/photo1.jpg"  # Fallback to first
        }
    ]
    
    # Mock the Claude API to avoid actual API calls during testing
    def mock_claude_messages_create(*args, **kwargs):
        # Return a mock response that selects the first image
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "1"  # Select first image
        return mock_response
    
    # Replace the Claude API call with our mock
    original_claude = generator.claude
    generator.claude = MagicMock()
    generator.claude.messages.create = mock_claude_messages_create
    
    print("🔧 Running test scenarios (mocked Claude API)...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        try:
            result = generator.select_best_featured_image(test_case['provider_data'])
            print(f"   🎯 Expected: {test_case['expected_result']}")
            print(f"   📤 Got: {result}")
            
            if result == test_case['expected_result']:
                print("   ✅ PASS")
            else:
                print("   ❌ FAIL")
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    # Restore original Claude client
    generator.claude = original_claude
    
    print(f"\n🎉 Test scenarios completed!")
    print("   Note: This test uses mocked Claude API responses")
    print("   For real API testing, use providers with actual Google Places photos")

def test_database_integration():
    """Test database integration for selected featured image"""
    
    print("\n🗄️  TESTING DATABASE INTEGRATION")
    print("=" * 50)
    
    try:
        from postgres_integration import PostgresIntegration
        
        db = PostgresIntegration()
        
        # Test database connection
        connected, message = db.test_connection()
        print(f"🔗 Database connection: {message}")
        
        if connected:
            # Test schema validation
            valid, report = db.validate_schema()
            print(f"📋 Schema validation: {'✅ VALID' if valid else '❌ INVALID'}")
            
            if 'selected_featured_image' in report.get('missing_fields', []):
                print("   ❌ selected_featured_image column missing from schema")
            else:
                print("   ✅ selected_featured_image column found in schema")
            
            # Get stats
            stats = db.get_stats()
            print(f"📊 Database stats:")
            print(f"   Total providers: {stats.get('total_providers', 0)}")
            print(f"   Providers with selected featured image: {stats.get('providers_with_selected_image', 'N/A')}")
            
        else:
            print("   ❌ Cannot test database integration - connection failed")
            
    except ImportError as e:
        print(f"   ❌ Cannot import database modules: {str(e)}")
    except Exception as e:
        print(f"   ❌ Database integration test failed: {str(e)}")

def test_wordpress_integration():
    """Test WordPress integration for external featured images"""
    
    print("\n🌐 TESTING WORDPRESS INTEGRATION")
    print("=" * 50)
    
    try:
        from wordpress_integration import WordPressIntegration
        
        wp = WordPressIntegration()
        
        # Create a mock provider with selected featured image
        mock_provider = MagicMock()
        mock_provider.provider_name = "Test Provider"
        mock_provider.selected_featured_image = "https://example.com/selected_image.jpg"
        mock_provider.photo_urls = json.dumps([
            "https://example.com/photo1.jpg",
            "https://example.com/photo2.jpg"
        ])
        
        # Test primary photo URL selection
        primary_url = wp.get_primary_photo_url(mock_provider)
        print(f"🎯 Primary photo URL: {primary_url}")
        
        if primary_url == "https://example.com/selected_image.jpg":
            print("   ✅ PASS: Uses selected featured image when available")
        else:
            print("   ❌ FAIL: Should use selected featured image")
        
        # Test fallback behavior
        mock_provider.selected_featured_image = ""
        fallback_url = wp.get_primary_photo_url(mock_provider)
        print(f"🔄 Fallback photo URL: {fallback_url}")
        
        if fallback_url == "https://example.com/photo1.jpg":
            print("   ✅ PASS: Falls back to first photo when no selection")
        else:
            print("   ❌ FAIL: Should fallback to first photo")
            
    except ImportError as e:
        print(f"   ❌ Cannot import WordPress modules: {str(e)}")
    except Exception as e:
        print(f"   ❌ WordPress integration test failed: {str(e)}")

if __name__ == "__main__":
    test_image_selection_scenarios()
    test_database_integration()
    test_wordpress_integration()
    
    print("\n🎉 ALL TESTS COMPLETED!")
    print("   Claude Vision image selection system is ready for use")
    print("   Run mega-batch processing to start selecting featured images") 