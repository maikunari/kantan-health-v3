#!/usr/bin/env python3
"""
Comprehensive validation of existing healthcare provider collection system
Tests all components to identify what's working vs what needs repair
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('validation_report.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ExistingComponentValidator:
    """Validate all existing components before enhancement"""
    
    def __init__(self):
        self.validation_results = {}
        self.critical_issues = []
        self.warnings = []
        
    def run_comprehensive_validation(self):
        """Execute full system validation"""
        logger.info("=" * 80)
        logger.info("STARTING COMPREHENSIVE SYSTEM VALIDATION")
        logger.info("=" * 80)
        
        # Define test order (dependencies first)
        validation_sequence = [
            ('environment_config', self.test_environment_config),
            ('database_connectivity', self.test_database_connection),
            ('google_places_api', self.test_google_places_integration),
            ('wordpress_api', self.test_wordpress_integration),
            ('romaji_converter', self.test_romaji_converter),
            ('duplicate_detection', self.test_duplicate_detection),
            ('ai_content_processor', self.test_ai_content_processing),
            ('pipeline_orchestration', self.test_pipeline_coordination),
        ]
        
        validation_report = {
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'summary': {
                'total_tested': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0,
                'warnings': 0
            }
        }
        
        for component_name, test_method in validation_sequence:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing: {component_name}")
            logger.info(f"{'='*60}")
            
            try:
                result = test_method()
                validation_report['components'][component_name] = result
                validation_report['summary']['total_tested'] += 1
                
                if result['status'] == 'pass':
                    validation_report['summary']['passed'] += 1
                    logger.info(f"✅ {component_name}: PASSED")
                elif result['status'] == 'fail':
                    validation_report['summary']['failed'] += 1
                    logger.error(f"❌ {component_name}: FAILED")
                    self.critical_issues.extend(result.get('issues', []))
                elif result['status'] == 'warning':
                    validation_report['summary']['warnings'] += 1
                    logger.warning(f"⚠️ {component_name}: WARNING")
                    self.warnings.extend(result.get('issues', []))
                    
            except Exception as e:
                validation_report['components'][component_name] = {
                    'status': 'error',
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                    'needs_repair': True
                }
                validation_report['summary']['errors'] += 1
                logger.error(f"💥 {component_name}: ERROR - {str(e)}")
                self.critical_issues.append(f"{component_name}: {str(e)}")
        
        # Generate final report
        validation_report['critical_issues'] = self.critical_issues
        validation_report['warnings'] = self.warnings
        validation_report['repair_priorities'] = self.generate_repair_priorities(validation_report)
        
        # Save report
        self.save_validation_report(validation_report)
        self.print_summary(validation_report)
        
        return validation_report
    
    def test_environment_config(self) -> Dict:
        """Test environment configuration"""
        logger.info("Testing environment configuration...")
        
        result = {
            'status': 'pass',
            'issues': [],
            'details': {}
        }
        
        # Check for .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', '.env')
        if not os.path.exists(env_path):
            result['status'] = 'fail'
            result['issues'].append('.env file not found at config/.env')
            result['needs_repair'] = True
            return result
            
        # Check required environment variables
        from dotenv import load_dotenv
        load_dotenv(env_path)
        
        required_vars = {
            'POSTGRES_USER': os.getenv('POSTGRES_USER'),
            'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD'),
            'POSTGRES_HOST': os.getenv('POSTGRES_HOST'),
            'POSTGRES_DB': os.getenv('POSTGRES_DB'),
            'GOOGLE_PLACES_API_KEY': os.getenv('GOOGLE_PLACES_API_KEY'),
            'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
            'WORDPRESS_URL': os.getenv('WORDPRESS_URL'),
            'WORDPRESS_USERNAME': os.getenv('WORDPRESS_USERNAME'),
            'WORDPRESS_APPLICATION_PASSWORD': os.getenv('WORDPRESS_APPLICATION_PASSWORD')
        }
        
        missing_vars = []
        for var_name, value in required_vars.items():
            if not value:
                missing_vars.append(var_name)
            else:
                result['details'][var_name] = 'configured' if 'PASSWORD' not in var_name else '***'
        
        if missing_vars:
            result['status'] = 'fail'
            result['issues'].append(f"Missing environment variables: {', '.join(missing_vars)}")
            result['needs_repair'] = True
        
        return result
    
    def test_database_connection(self) -> Dict:
        """Test database connectivity and connection pooling issues"""
        logger.info("Testing database connectivity...")
        
        result = {
            'status': 'pass',
            'issues': [],
            'details': {},
            'root_cause': None
        }
        
        try:
            from src.core.database import DatabaseManager
            
            # Test 1: Basic connection
            db = DatabaseManager()
            result['details']['connection'] = 'established'
            
            # Test 2: Check connection pooling configuration
            engine = db.engine
            pool = engine.pool
            
            # CRITICAL ISSUE: Using NullPool
            if pool.__class__.__name__ == 'NullPool':
                result['status'] = 'fail'
                result['issues'].append('Using NullPool - creates new connection for every request')
                result['root_cause'] = 'NullPool causes connection instability and performance issues'
                result['needs_repair'] = True
            else:
                result['details']['connection_pool'] = pool.__class__.__name__
            
            # Test 3: Multiple rapid connections (simulate concurrent access)
            logger.info("Testing multiple rapid database connections...")
            connection_test_results = []
            
            for i in range(10):
                try:
                    session = db.get_session()
                    # Simple query to test connection
                    count = session.execute("SELECT COUNT(*) FROM providers").scalar()
                    session.close()
                    connection_test_results.append(True)
                except Exception as e:
                    connection_test_results.append(False)
                    result['issues'].append(f"Connection {i+1} failed: {str(e)}")
            
            success_rate = sum(connection_test_results) / len(connection_test_results)
            result['details']['connection_success_rate'] = f"{success_rate*100:.1f}%"
            
            if success_rate < 1.0:
                result['status'] = 'fail'
                result['issues'].append(f"Connection instability: {(1-success_rate)*100:.1f}% failure rate")
            
            # Test 4: Check provider count and basic operations
            session = db.get_session()
            try:
                provider_count = session.query(db.Session().query(Provider).count()).scalar()
                result['details']['provider_count'] = provider_count
                
                # Test get_provider_by_id
                if provider_count > 0:
                    test_provider = db.get_provider_by_id(1)
                    if test_provider:
                        result['details']['read_operations'] = 'working'
                    else:
                        result['issues'].append('get_provider_by_id returned None for ID 1')
                        
            except Exception as e:
                result['issues'].append(f"Database query failed: {str(e)}")
                result['status'] = 'fail'
            finally:
                session.close()
                
        except ImportError as e:
            result['status'] = 'error'
            result['error'] = f"Cannot import DatabaseManager: {str(e)}"
            result['needs_repair'] = True
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            result['needs_repair'] = True
        
        return result
    
    def test_google_places_integration(self) -> Dict:
        """Test Google Places API integration"""
        logger.info("Testing Google Places API integration...")
        
        result = {
            'status': 'pass',
            'issues': [],
            'details': {},
            'root_cause': None
        }
        
        try:
            from src.collectors.google_places import GooglePlacesCollector
            
            # Initialize collector
            collector = GooglePlacesCollector()
            result['details']['collector_initialized'] = True
            
            # Test 1: Check API key configuration
            if not collector.api_key:
                result['status'] = 'fail'
                result['issues'].append('Google Places API key not configured')
                result['needs_repair'] = True
                return result
            
            # Test 2: Test search functionality
            logger.info("Testing Google Places search...")
            test_query = "English speaking doctor Tokyo"
            
            try:
                # Check if search_providers method exists
                if hasattr(collector, 'search_providers'):
                    results = collector.search_providers(test_query, limit=1)
                    if results:
                        result['details']['search_working'] = True
                        result['details']['sample_result'] = results[0].get('name', 'No name')
                    else:
                        result['status'] = 'warning'
                        result['issues'].append('Search returned no results')
                else:
                    result['status'] = 'fail'
                    result['issues'].append('search_providers method not found')
                    
            except Exception as e:
                result['status'] = 'fail'
                result['issues'].append(f"Search test failed: {str(e)}")
                result['root_cause'] = 'API integration may be broken or quota exceeded'
            
            # Test 3: Check rate limiting
            if hasattr(collector, 'rate_limiter'):
                result['details']['rate_limiting'] = 'configured'
            else:
                result['issues'].append('No rate limiting configured')
            
            # Test 4: Check romaji converter integration
            if hasattr(collector, 'romaji_converter'):
                result['details']['romaji_converter'] = 'integrated'
            else:
                result['issues'].append('Romaji converter not integrated')
                
        except ImportError as e:
            result['status'] = 'error'
            result['error'] = f"Cannot import GooglePlacesCollector: {str(e)}"
            result['needs_repair'] = True
        except Exception as e:
            result['status'] = 'error'  
            result['error'] = str(e)
            result['needs_repair'] = True
        
        return result
    
    def test_wordpress_integration(self) -> Dict:
        """Test WordPress API integration"""
        logger.info("Testing WordPress API integration...")
        
        result = {
            'status': 'pass',
            'issues': [],
            'details': {},
            'root_cause': None
        }
        
        try:
            from src.publishers.wordpress import WordPressPublisher
            
            # Initialize publisher
            publisher = WordPressPublisher()
            result['details']['publisher_initialized'] = True
            
            # Test 1: Check WordPress configuration
            if not publisher.wordpress_url:
                result['status'] = 'fail'
                result['issues'].append('WordPress URL not configured')
                result['needs_repair'] = True
                return result
            
            if not publisher.wordpress_username or not publisher.wordpress_password:
                result['status'] = 'fail'
                result['issues'].append('WordPress credentials not configured')
                result['needs_repair'] = True
                return result
            
            # Test 2: Test API connectivity
            logger.info("Testing WordPress REST API connectivity...")
            import requests
            
            try:
                # Test authentication
                test_url = f"{publisher.wordpress_url}/wp-json/wp/v2/users/me"
                response = requests.get(
                    test_url,
                    auth=(publisher.wordpress_username, publisher.wordpress_password),
                    timeout=10
                )
                
                if response.status_code == 200:
                    result['details']['api_authentication'] = 'successful'
                    result['details']['authenticated_user'] = response.json().get('name', 'Unknown')
                elif response.status_code == 401:
                    result['status'] = 'fail'
                    result['issues'].append('WordPress authentication failed')
                    result['root_cause'] = 'Invalid credentials or application password'
                    result['needs_repair'] = True
                else:
                    result['status'] = 'warning'
                    result['issues'].append(f'WordPress API returned status {response.status_code}')
                    
            except requests.exceptions.ConnectionError:
                result['status'] = 'fail'
                result['issues'].append('Cannot connect to WordPress site')
                result['root_cause'] = 'WordPress URL may be incorrect or site is down'
                result['needs_repair'] = True
            except Exception as e:
                result['status'] = 'fail'
                result['issues'].append(f'WordPress API test failed: {str(e)}')
            
            # Test 3: Check ACF field mappings
            if hasattr(publisher, 'prepare_acf_fields'):
                result['details']['acf_field_mapping'] = 'configured'
            else:
                result['issues'].append('ACF field mapping not configured')
                
        except ImportError as e:
            result['status'] = 'error'
            result['error'] = f"Cannot import WordPressPublisher: {str(e)}"
            result['needs_repair'] = True
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            result['needs_repair'] = True
        
        return result
    
    def test_romaji_converter(self) -> Dict:
        """Test romaji converter functionality"""
        logger.info("Testing romaji converter...")
        
        result = {
            'status': 'pass',
            'issues': [],
            'details': {}
        }
        
        try:
            from src.utils.romaji_converter import BusinessNameRomajiConverter
            
            converter = BusinessNameRomajiConverter()
            result['details']['converter_initialized'] = True
            
            # Test conversions
            test_cases = [
                ('東京クリニック', 'Tokyo Clinic'),
                ('山田内科', 'Yamada Internal Medicine'),
                ('さくら病院', 'Sakura Hospital')
            ]
            
            for japanese, expected_contains in test_cases:
                converted = converter.convert_business_name_intelligently(japanese)
                if converted and converted != japanese:
                    result['details'][f'conversion_{japanese}'] = converted
                else:
                    result['issues'].append(f'Failed to convert: {japanese}')
                    result['status'] = 'warning'
                    
        except ImportError as e:
            result['status'] = 'warning'
            result['issues'].append(f"Romaji converter not found: {str(e)}")
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def test_duplicate_detection(self) -> Dict:
        """Test existing duplicate detection system"""
        logger.info("Testing duplicate detection...")
        
        result = {
            'status': 'pass',
            'issues': [],
            'details': {},
            'root_cause': None
        }
        
        try:
            # Check if deduplication module exists
            dedup_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'collectors',
                'deduplication.py'
            )
            
            if os.path.exists(dedup_path):
                from src.collectors.deduplication import DuplicateDetector
                
                detector = DuplicateDetector()
                result['details']['detector_initialized'] = True
                
                # Test detection logic
                test_provider = {
                    'provider_name': 'Test Clinic',
                    'address': '123 Test St, Tokyo',
                    'phone': '03-1234-5678'
                }
                
                # Should not detect as duplicate for new provider
                is_duplicate = detector.check_duplicate(test_provider)
                
                if isinstance(is_duplicate, dict):
                    result['details']['detection_logic'] = 'working'
                    
                    # Check for geographic exclusion (SHOULD NOT EXIST)
                    if 'geographic' in str(detector.check_duplicate).lower():
                        result['status'] = 'fail'
                        result['issues'].append('Geographic exclusion still present in code')
                        result['root_cause'] = 'Geographic exclusion needs to be removed'
                        result['needs_repair'] = True
                else:
                    result['details']['detection_response'] = 'unexpected format'
                    
            else:
                result['status'] = 'warning'
                result['issues'].append('Deduplication module not found')
                result['details']['module_exists'] = False
                
        except ImportError as e:
            result['status'] = 'warning'
            result['issues'].append(f"Cannot import DuplicateDetector: {str(e)}")
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def test_ai_content_processing(self) -> Dict:
        """Test AI content generation"""
        logger.info("Testing AI content processing...")
        
        result = {
            'status': 'pass',
            'issues': [],
            'details': {}
        }
        
        try:
            from src.processors.ai_content import AIContentProcessor
            
            processor = AIContentProcessor()
            result['details']['processor_initialized'] = True
            
            # Check API key
            if not processor.api_key:
                result['status'] = 'fail'
                result['issues'].append('Anthropic API key not configured')
                result['needs_repair'] = True
                return result
            
            # Check batch processing capability
            if hasattr(processor, 'generate_mega_batch'):
                result['details']['mega_batch_capable'] = True
            else:
                result['issues'].append('Mega batch processing not implemented')
                
            # Check content validation
            if hasattr(processor, 'validate_content'):
                result['details']['content_validation'] = 'configured'
            else:
                result['issues'].append('Content validation not implemented')
                
        except ImportError as e:
            result['status'] = 'warning'
            result['issues'].append(f"Cannot import AIContentProcessor: {str(e)}")
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def test_pipeline_coordination(self) -> Dict:
        """Test pipeline orchestration"""
        logger.info("Testing pipeline orchestration...")
        
        result = {
            'status': 'pass',
            'issues': [],
            'details': {}
        }
        
        try:
            # Check if pipeline script exists
            pipeline_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'scripts',
                'run_pipeline.py'
            )
            
            if os.path.exists(pipeline_path):
                result['details']['pipeline_script'] = 'exists'
                
                # Try to import and check structure
                sys.path.append(os.path.dirname(pipeline_path))
                
                # Check for key components
                with open(pipeline_path, 'r') as f:
                    content = f.read()
                    
                    if 'collect' in content and 'process' in content and 'publish' in content:
                        result['details']['pipeline_phases'] = 'collect → process → publish'
                    else:
                        result['status'] = 'warning'
                        result['issues'].append('Pipeline phases incomplete')
                        
                    if 'checkpoint' in content.lower():
                        result['details']['checkpoint_recovery'] = 'implemented'
                    else:
                        result['issues'].append('No checkpoint recovery found')
                        
            else:
                result['status'] = 'fail'
                result['issues'].append('Pipeline script not found')
                result['needs_repair'] = True
                
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def generate_repair_priorities(self, validation_report: Dict) -> List[Dict]:
        """Generate prioritized list of repairs needed"""
        priorities = []
        
        # Priority 1: Critical failures
        for component, details in validation_report['components'].items():
            if details.get('status') in ['fail', 'error']:
                priority = {
                    'priority': 1,
                    'component': component,
                    'issue': details.get('root_cause') or 'Component failure',
                    'repair_action': self.get_repair_action(component, details)
                }
                priorities.append(priority)
        
        # Priority 2: Warnings that affect functionality
        for component, details in validation_report['components'].items():
            if details.get('status') == 'warning':
                priority = {
                    'priority': 2,
                    'component': component,
                    'issue': ', '.join(details.get('issues', [])),
                    'repair_action': self.get_repair_action(component, details)
                }
                priorities.append(priority)
        
        return sorted(priorities, key=lambda x: x['priority'])
    
    def get_repair_action(self, component: str, details: Dict) -> str:
        """Get specific repair action for component"""
        repair_actions = {
            'database_connectivity': 'Replace NullPool with proper connection pooling (pool_size=10, max_overflow=20)',
            'google_places_api': 'Fix API integration and implement rate limiting',
            'wordpress_api': 'Verify credentials and fix authentication',
            'duplicate_detection': 'Remove geographic exclusion and implement identity-based detection',
            'pipeline_orchestration': 'Create or fix pipeline orchestration script',
            'romaji_converter': 'Implement or fix romaji conversion module',
            'ai_content_processor': 'Configure API key and implement batch processing'
        }
        
        return repair_actions.get(component, 'Review and fix component issues')
    
    def save_validation_report(self, report: Dict):
        """Save validation report to file"""
        report_path = os.path.join(
            os.path.dirname(__file__),
            f'validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"\n📄 Full report saved to: {report_path}")
    
    def print_summary(self, report: Dict):
        """Print validation summary"""
        logger.info("\n" + "=" * 80)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 80)
        
        summary = report['summary']
        logger.info(f"Total Components Tested: {summary['total_tested']}")
        logger.info(f"✅ Passed: {summary['passed']}")
        logger.info(f"❌ Failed: {summary['failed']}")
        logger.info(f"⚠️  Warnings: {summary['warnings']}")
        logger.info(f"💥 Errors: {summary['errors']}")
        
        if report['critical_issues']:
            logger.info("\n🚨 CRITICAL ISSUES:")
            for issue in report['critical_issues']:
                logger.info(f"  - {issue}")
        
        if report['repair_priorities']:
            logger.info("\n🔧 REPAIR PRIORITIES:")
            for priority in report['repair_priorities'][:5]:  # Show top 5
                logger.info(f"  P{priority['priority']}: {priority['component']}")
                logger.info(f"      Issue: {priority['issue']}")
                logger.info(f"      Action: {priority['repair_action']}")


if __name__ == "__main__":
    validator = ExistingComponentValidator()
    report = validator.run_comprehensive_validation()
    
    # Return exit code based on validation results
    if report['summary']['failed'] > 0 or report['summary']['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)