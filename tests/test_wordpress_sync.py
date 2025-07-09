#!/usr/bin/env python3
"""
Unit Tests for WordPress Sync Enhancement
Tests the core components of the WordPress sync system.
"""

import unittest
import tempfile
import shutil
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

# Add parent directory to path to import modules
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from content_hash_service import ContentHashService, ContentComparison
from wordpress_update_service import WordPressUpdateService
from sync_management_service import SyncManagementService, SyncOperation, SyncStatus
from postgres_integration import Provider

class TestContentHashService(unittest.TestCase):
    """Test ContentHashService functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.content_hash_service = ContentHashService()
        
        # Create mock provider
        self.mock_provider = Mock(spec=Provider)
        self.mock_provider.id = 1
        self.mock_provider.provider_name = "Test Provider"
        self.mock_provider.ai_description = "Test AI description"
        self.mock_provider.ai_excerpt = "Test excerpt"
        self.mock_provider.specialties = ["Internal Medicine"]
        self.mock_provider.city = "Tokyo"
        self.mock_provider.address = "123 Test St, Tokyo"
        self.mock_provider.phone = "03-1234-5678"
        self.mock_provider.website = "https://test.com"
        self.mock_provider.english_proficiency = "High"
        self.mock_provider.rating = 4.5
        self.mock_provider.total_reviews = 100
        self.mock_provider.business_hours = {"Monday": "9:00-17:00"}
        self.mock_provider.wheelchair_accessible = True
        self.mock_provider.parking_available = True
        self.mock_provider.latitude = 35.6762
        self.mock_provider.longitude = 139.6503
        self.mock_provider.nearest_station = "Tokyo Station"
        self.mock_provider.photo_urls = ["https://example.com/photo1.jpg"]
        self.mock_provider.content_hash = None
    
    def test_generate_provider_hash(self):
        """Test hash generation for provider"""
        hash1 = self.content_hash_service.generate_provider_hash(self.mock_provider)
        
        # Hash should be 64 characters (SHA256)
        self.assertEqual(len(hash1), 64)
        self.assertIsInstance(hash1, str)
        
        # Same provider should generate same hash
        hash2 = self.content_hash_service.generate_provider_hash(self.mock_provider)
        self.assertEqual(hash1, hash2)
    
    def test_hash_consistency(self):
        """Test that hash is consistent across multiple calls"""
        hashes = []
        for _ in range(5):
            hash_val = self.content_hash_service.generate_provider_hash(self.mock_provider)
            hashes.append(hash_val)
        
        # All hashes should be identical
        self.assertEqual(len(set(hashes)), 1)
    
    def test_content_changed_no_previous_hash(self):
        """Test content change detection when no previous hash exists"""
        self.mock_provider.content_hash = None
        
        result = self.content_hash_service.content_changed(self.mock_provider)
        self.assertTrue(result)
    
    def test_content_changed_with_same_hash(self):
        """Test content change detection when content is unchanged"""
        original_hash = self.content_hash_service.generate_provider_hash(self.mock_provider)
        self.mock_provider.content_hash = original_hash
        
        result = self.content_hash_service.content_changed(self.mock_provider)
        self.assertFalse(result)
    
    def test_content_changed_with_different_hash(self):
        """Test content change detection when content has changed"""
        self.mock_provider.content_hash = "different_hash"
        
        result = self.content_hash_service.content_changed(self.mock_provider)
        self.assertTrue(result)
    
    def test_compare_content_initial_sync(self):
        """Test content comparison for initial sync"""
        self.mock_provider.content_hash = None
        
        comparison = self.content_hash_service.compare_content(self.mock_provider)
        
        self.assertIsInstance(comparison, ContentComparison)
        self.assertTrue(comparison.needs_update)
        self.assertIsNone(comparison.old_hash)
        self.assertIsNotNone(comparison.new_hash)
        self.assertEqual(comparison.changed_fields, ["initial_sync"])
    
    def test_compare_content_no_changes(self):
        """Test content comparison when no changes detected"""
        original_hash = self.content_hash_service.generate_provider_hash(self.mock_provider)
        self.mock_provider.content_hash = original_hash
        
        comparison = self.content_hash_service.compare_content(self.mock_provider)
        
        self.assertFalse(comparison.needs_update)
        self.assertEqual(comparison.old_hash, original_hash)
        self.assertEqual(comparison.new_hash, original_hash)
        self.assertEqual(comparison.changed_fields, [])
    
    def test_compare_content_with_changes(self):
        """Test content comparison when changes detected"""
        self.mock_provider.content_hash = "old_hash"
        
        comparison = self.content_hash_service.compare_content(self.mock_provider)
        
        self.assertTrue(comparison.needs_update)
        self.assertEqual(comparison.old_hash, "old_hash")
        self.assertNotEqual(comparison.new_hash, "old_hash")
        self.assertIsInstance(comparison.changed_fields, list)

class TestWordPressUpdateService(unittest.TestCase):
    """Test WordPressUpdateService functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock environment variables
        with patch.dict(os.environ, {
            'WORDPRESS_URL': 'https://test.com',
            'WORDPRESS_USERNAME': 'testuser',
            'WORDPRESS_APPLICATION_PASSWORD': 'testpass'
        }):
            self.wp_service = WordPressUpdateService()
        
        # Create mock provider
        self.mock_provider = Mock(spec=Provider)
        self.mock_provider.id = 1
        self.mock_provider.provider_name = "Test Provider"
        self.mock_provider.wordpress_post_id = 123
        self.mock_provider.ai_description = "Test description"
        self.mock_provider.ai_excerpt = "Test excerpt"
        self.mock_provider.city = "Tokyo"
        self.mock_provider.address = "123 Test St"
        self.mock_provider.phone = "03-1234-5678"
        self.mock_provider.website = "https://test.com"
        self.mock_provider.specialties = ["Internal Medicine"]
        self.mock_provider.english_proficiency = "High"
        self.mock_provider.rating = 4.5
        self.mock_provider.total_reviews = 100
        self.mock_provider.business_hours = {"Monday": "9:00-17:00"}
        self.mock_provider.wheelchair_accessible = True
        self.mock_provider.parking_available = True
        self.mock_provider.latitude = 35.6762
        self.mock_provider.longitude = 139.6503
        self.mock_provider.nearest_station = "Tokyo Station"
        self.mock_provider.photo_urls = []
        self.mock_provider.prefecture = "Tokyo"
        self.mock_provider.district = "Chiyoda"
        self.mock_provider.content_hash = None
        self.mock_provider.last_wordpress_sync = None
        self.mock_provider.wordpress_status = "pending"
    
    def test_initialization_with_missing_credentials(self):
        """Test service initialization with missing credentials"""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                WordPressUpdateService()
    
    def test_update_existing_post_no_wordpress_id(self):
        """Test update with provider that has no WordPress post ID"""
        self.mock_provider.wordpress_post_id = None
        
        with self.assertRaises(ValueError):
            self.wp_service.update_existing_post(self.mock_provider)
    
    @patch('wordpress_update_service.ContentHashService')
    def test_update_existing_post_no_changes(self, mock_content_service):
        """Test update when no changes are detected"""
        # Mock content service to return no changes
        mock_comparison = Mock()
        mock_comparison.needs_update = False
        mock_content_service.return_value.compare_content.return_value = mock_comparison
        
        result = self.wp_service.update_existing_post(self.mock_provider)
        
        self.assertEqual(result['status'], 'no_changes')
        self.assertEqual(result['provider_name'], 'Test Provider')
        self.assertEqual(result['post_id'], 123)
    
    @patch('wordpress_update_service.ContentHashService')
    def test_update_existing_post_dry_run(self, mock_content_service):
        """Test update in dry run mode"""
        # Mock content service to return changes
        mock_comparison = Mock()
        mock_comparison.needs_update = True
        mock_comparison.new_hash = "new_hash"
        mock_comparison.changed_fields = ["ai_description"]
        mock_content_service.return_value.compare_content.return_value = mock_comparison
        
        result = self.wp_service.update_existing_post(self.mock_provider, dry_run=True)
        
        self.assertEqual(result['status'], 'dry_run')
        self.assertEqual(result['provider_name'], 'Test Provider')
        self.assertEqual(result['post_id'], 123)
        self.assertEqual(result['changes'], ["ai_description"])
    
    @patch('wordpress_update_service.ContentHashService')
    @patch('wordpress_update_service.PostgresIntegration')
    def test_update_existing_post_success(self, mock_postgres, mock_content_service):
        """Test successful WordPress post update"""
        # Mock content service
        mock_comparison = Mock()
        mock_comparison.needs_update = True
        mock_comparison.new_hash = "new_hash"
        mock_comparison.changed_fields = ["ai_description"]
        mock_content_service.return_value.compare_content.return_value = mock_comparison
        
        # Mock database session
        mock_session = Mock()
        mock_db_provider = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_db_provider
        mock_postgres.return_value.Session.return_value = mock_session
        
        # Mock successful WordPress API response
        mock_response = Mock()
        mock_response.status_code = 200
        self.wp_service.session.post = Mock(return_value=mock_response)
        
        result = self.wp_service.update_existing_post(self.mock_provider)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['provider_name'], 'Test Provider')
        self.assertEqual(result['post_id'], 123)
        self.assertIn('duration_ms', result)
        self.assertEqual(result['changes'], ["ai_description"])
    
    @patch('wordpress_update_service.ContentHashService')
    def test_update_existing_post_api_error(self, mock_content_service):
        """Test handling of WordPress API errors"""
        # Mock content service
        mock_comparison = Mock()
        mock_comparison.needs_update = True
        mock_comparison.new_hash = "new_hash"
        mock_comparison.changed_fields = ["ai_description"]
        mock_content_service.return_value.compare_content.return_value = mock_comparison
        
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        self.wp_service.session.post = Mock(return_value=mock_response)
        
        result = self.wp_service.update_existing_post(self.mock_provider)
        
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['provider_name'], 'Test Provider')
        self.assertEqual(result['post_id'], 123)
        self.assertIn('error', result)
    
    def test_generate_post_content(self):
        """Test WordPress post content generation"""
        content = self.wp_service._generate_post_content(self.mock_provider)
        
        self.assertIsInstance(content, str)
        self.assertIn('Test Provider', content)
        self.assertIn('Tokyo', content)
        self.assertIn('Test description', content)
        self.assertIn('Internal Medicine', content)
    
    def test_generate_acf_fields(self):
        """Test ACF fields generation"""
        acf_fields = self.wp_service._generate_acf_fields(self.mock_provider)
        
        self.assertIsInstance(acf_fields, dict)
        self.assertEqual(acf_fields['provider_phone'], '03-1234-5678')
        self.assertEqual(acf_fields['wheelchair_accessible'], 'Yes')
        self.assertEqual(acf_fields['parking_available'], 'Yes')
        self.assertEqual(acf_fields['english_proficiency'], 'High')
        self.assertEqual(acf_fields['provider_city'], 'Tokyo')
    
    def test_clean_address(self):
        """Test address cleaning functionality"""
        test_cases = [
            ("123 Test St, Tokyo, Japan", "123 Test St, Tokyo"),
            ("456 Main St,Japan", "456 Main St"),
            ("789 Oak Ave Japan", "789 Oak Ave"),
            ("No Japan here", "No Japan here"),
            ("", "")
        ]
        
        for input_addr, expected in test_cases:
            result = self.wp_service._clean_address(input_addr)
            self.assertEqual(result, expected)
    
    def test_clean_website_url(self):
        """Test website URL cleaning"""
        test_cases = [
            ("https://test.com?utm_source=google", "https://test.com"),
            ("https://test.com/page/?param=value", "https://test.com/page"),
            ("https://test.com/", "https://test.com"),
            ("https://test.com", "https://test.com"),
            ("", "")
        ]
        
        for input_url, expected in test_cases:
            result = self.wp_service._clean_website_url(input_url)
            self.assertEqual(result, expected)

class TestSyncManagementService(unittest.TestCase):
    """Test SyncManagementService functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('sync_management_service.PostgresIntegration'), \
             patch('sync_management_service.ContentHashService'), \
             patch('sync_management_service.WordPressUpdateService'):
            self.sync_service = SyncManagementService()
        
        # Create mock provider
        self.mock_provider = Mock(spec=Provider)
        self.mock_provider.id = 1
        self.mock_provider.provider_name = "Test Provider"
        self.mock_provider.wordpress_post_id = 123
        self.mock_provider.city = "Tokyo"
        self.mock_provider.ai_description = "Test description"
    
    def test_plan_sync_operation_no_providers(self):
        """Test sync planning when no providers found"""
        self.sync_service._get_target_providers = Mock(return_value=[])
        
        plan = self.sync_service.plan_sync_operation(SyncOperation.UPDATE_SINGLE)
        
        self.assertEqual(plan.operation_type, SyncOperation.UPDATE_SINGLE)
        self.assertEqual(len(plan.target_providers), 0)
        self.assertEqual(plan.estimated_duration, 0)
    
    def test_plan_sync_operation_with_providers(self):
        """Test sync planning with providers"""
        providers = [self.mock_provider]
        self.sync_service._get_target_providers = Mock(return_value=providers)
        
        plan = self.sync_service.plan_sync_operation(
            SyncOperation.UPDATE_SINGLE,
            filters={'provider_name': 'Test Provider'}
        )
        
        self.assertEqual(plan.operation_type, SyncOperation.UPDATE_SINGLE)
        self.assertEqual(len(plan.target_providers), 1)
        self.assertEqual(plan.provider_count, 1)
        self.assertGreater(plan.estimated_duration, 0)
    
    @patch('sync_management_service.datetime')
    def test_execute_sync_plan_success(self, mock_datetime):
        """Test successful sync plan execution"""
        # Mock datetime
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Create plan
        plan = Mock()
        plan.operation_id = "test_op_123"
        plan.operation_type = SyncOperation.UPDATE_SINGLE
        plan.target_providers = [self.mock_provider]
        
        # Mock sync execution
        self.sync_service._execute_single_update = Mock(return_value={
            'total': 1,
            'success': 1,
            'failed': 0,
            'no_changes': 0,
            'details': [{'status': 'success'}]
        })
        
        result = self.sync_service.execute_sync_plan(plan)
        
        self.assertEqual(result.operation_id, "test_op_123")
        self.assertEqual(result.status, SyncStatus.SUCCESS)
        self.assertEqual(result.providers_processed, 1)
        self.assertEqual(result.providers_updated, 1)
        self.assertEqual(result.providers_failed, 0)
    
    def test_execute_sync_plan_failure(self):
        """Test sync plan execution with failures"""
        plan = Mock()
        plan.operation_id = "test_op_123"
        plan.operation_type = SyncOperation.UPDATE_SINGLE
        plan.target_providers = [self.mock_provider]
        
        # Mock sync execution with failure
        self.sync_service._execute_single_update = Mock(return_value={
            'total': 1,
            'success': 0,
            'failed': 1,
            'no_changes': 0,
            'details': [{'status': 'failed', 'error': 'Test error'}]
        })
        
        result = self.sync_service.execute_sync_plan(plan)
        
        self.assertEqual(result.status, SyncStatus.FAILED)
        self.assertEqual(result.providers_processed, 1)
        self.assertEqual(result.providers_updated, 0)
        self.assertEqual(result.providers_failed, 1)
    
    def test_execute_sync_plan_exception(self):
        """Test sync plan execution with exception"""
        plan = Mock()
        plan.operation_id = "test_op_123"
        plan.operation_type = SyncOperation.UPDATE_SINGLE
        plan.target_providers = [self.mock_provider]
        
        # Mock sync execution to raise exception
        self.sync_service._execute_single_update = Mock(side_effect=Exception("Test error"))
        
        result = self.sync_service.execute_sync_plan(plan)
        
        self.assertEqual(result.status, SyncStatus.FAILED)
        self.assertIn("Test error", result.errors)
    
    def test_get_sync_status_active_operation(self):
        """Test getting status of active operation"""
        # Add mock active operation
        mock_result = Mock()
        mock_result.operation_id = "test_op_123"
        mock_result.status = SyncStatus.RUNNING
        self.sync_service.active_operations["test_op_123"] = mock_result
        
        result = self.sync_service.get_sync_status("test_op_123")
        
        self.assertEqual(result, mock_result)
        self.assertEqual(result.operation_id, "test_op_123")
    
    def test_get_sync_status_nonexistent_operation(self):
        """Test getting status of non-existent operation"""
        result = self.sync_service.get_sync_status("nonexistent")
        
        self.assertIsNone(result)
    
    def test_cancel_sync_operation(self):
        """Test cancelling sync operation"""
        # Add mock active operation
        mock_result = Mock()
        mock_result.status = SyncStatus.RUNNING
        self.sync_service.active_operations["test_op_123"] = mock_result
        
        success = self.sync_service.cancel_sync_operation("test_op_123")
        
        self.assertTrue(success)
        self.assertEqual(mock_result.status, SyncStatus.CANCELLED)
    
    def test_cancel_nonexistent_operation(self):
        """Test cancelling non-existent operation"""
        success = self.sync_service.cancel_sync_operation("nonexistent")
        
        self.assertFalse(success)

class TestIntegration(unittest.TestCase):
    """Integration tests for the WordPress sync system"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.test_env = {
            'WORDPRESS_URL': 'https://test-wordpress.com',
            'WORDPRESS_USERNAME': 'test_user',
            'WORDPRESS_APPLICATION_PASSWORD': 'test_pass'
        }
    
    @patch('wordpress_update_service.requests.Session')
    @patch('sync_management_service.PostgresIntegration')
    def test_full_sync_workflow(self, mock_postgres, mock_session):
        """Test complete sync workflow from planning to execution"""
        # Mock database
        mock_db_session = Mock()
        mock_provider = Mock(spec=Provider)
        mock_provider.id = 1
        mock_provider.provider_name = "Integration Test Provider"
        mock_provider.wordpress_post_id = 456
        mock_provider.city = "Tokyo"
        mock_provider.ai_description = "Test description"
        mock_provider.content_hash = None
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_provider]
        mock_postgres.return_value.Session.return_value = mock_db_session
        
        # Mock WordPress API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.return_value.post.return_value = mock_response
        
        with patch.dict(os.environ, self.test_env):
            # Initialize services
            sync_service = SyncManagementService()
            
            # Create and execute sync plan
            plan = sync_service.plan_sync_operation(
                SyncOperation.UPDATE_SINGLE,
                filters={'provider_name': 'Integration Test Provider'}
            )
            
            self.assertEqual(plan.operation_type, SyncOperation.UPDATE_SINGLE)
            self.assertIsNotNone(plan.operation_id)
            self.assertGreater(plan.estimated_duration, 0)
            
            # Execute the plan
            result = sync_service.execute_sync_plan(plan)
            
            # Verify results
            self.assertIsNotNone(result)
            self.assertEqual(result.operation_id, plan.operation_id)
            self.assertIn(result.status, [SyncStatus.SUCCESS, SyncStatus.FAILED])

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 