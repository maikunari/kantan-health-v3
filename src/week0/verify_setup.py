#!/usr/bin/env python3
"""
Verify all requirements are installed and database is initialized
"""

import sys
import subprocess
import importlib
import logging
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class SetupVerifier:
    """Verify and setup system components"""
    
    def __init__(self):
        self.missing_packages = []
        self.installed_packages = []
        self.unnecessary_packages = []
        
    def check_requirements(self) -> Dict:
        """Check if all required packages are installed"""
        logger.info("=" * 80)
        logger.info("CHECKING PACKAGE REQUIREMENTS")
        logger.info("=" * 80)
        
        # Core required packages for the campaign
        required_packages = {
            # Database
            'sqlalchemy': 'SQLAlchemy',
            'psycopg2': 'psycopg2-binary',
            
            # API integrations
            'requests': 'requests',
            'googlemaps': 'googlemaps',
            'anthropic': 'anthropic',
            
            # Configuration
            'dotenv': 'python-dotenv',
            
            # Data processing
            'pandas': 'pandas',
            
            # Japanese text processing
            'cutlet': 'cutlet',
            
            # Utilities
            'pytz': 'pytz',
            'dateutil': 'python-dateutil',
            
            # Google Cloud monitoring (for cost tracking)
            'google.cloud.monitoring': 'google-cloud-monitoring',
            'google.cloud.billing': 'google-cloud-billing',
        }
        
        # Optional packages (not critical for campaign)
        optional_packages = {
            'flask': 'flask',
            'flask_cors': 'Flask-CORS',
            'flask_sqlalchemy': 'Flask-SQLAlchemy',
            'flask_restful': 'Flask-RESTful',
            'flask_login': 'Flask-Login',
            'flask_limiter': 'flask-limiter',
            'gunicorn': 'gunicorn',
            'celery': 'celery',
            'redis': 'redis',
            'nltk': 'nltk',
            'textblob': 'textblob',
            'pyairtable': 'pyairtable',
            'pytrends': 'pytrends',
            'psutil': 'psutil',
        }
        
        results = {
            'required': {},
            'optional': {},
            'missing_required': [],
            'missing_optional': []
        }
        
        # Check required packages
        logger.info("\n📦 Checking REQUIRED packages:")
        for module_name, package_name in required_packages.items():
            try:
                importlib.import_module(module_name)
                results['required'][package_name] = True
                logger.info(f"  ✅ {package_name}")
                self.installed_packages.append(package_name)
            except ImportError:
                results['required'][package_name] = False
                results['missing_required'].append(package_name)
                logger.error(f"  ❌ {package_name} - MISSING")
                self.missing_packages.append(package_name)
        
        # Check optional packages
        logger.info("\n📦 Checking OPTIONAL packages (not needed for campaign):")
        for module_name, package_name in optional_packages.items():
            try:
                importlib.import_module(module_name)
                results['optional'][package_name] = True
                logger.info(f"  ✓ {package_name} (installed but not required)")
                self.unnecessary_packages.append(package_name)
            except ImportError:
                results['optional'][package_name] = False
                results['missing_optional'].append(package_name)
                logger.info(f"  ○ {package_name} (not installed, not required)")
        
        return results
    
    def check_database_connection(self) -> Dict:
        """Check if database is accessible"""
        logger.info("\n" + "=" * 80)
        logger.info("CHECKING DATABASE CONNECTION")
        logger.info("=" * 80)
        
        result = {
            'connected': False,
            'initialized': False,
            'provider_count': 0,
            'tables': []
        }
        
        try:
            import os
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            
            from dotenv import load_dotenv
            load_dotenv('config/.env')
            
            from sqlalchemy import create_engine, inspect, text
            
            # Get database config
            db_config = {
                'user': os.getenv('POSTGRES_USER', 'postgres'),
                'password': os.getenv('POSTGRES_PASSWORD', 'password'),
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'database': os.getenv('POSTGRES_DB', 'directory')
            }
            
            # Create connection
            db_url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:5432/{db_config['database']}"
            engine = create_engine(db_url)
            
            # Test connection
            with engine.connect() as conn:
                result['connected'] = True
                logger.info(f"✅ Connected to database: {db_config['database']}")
                
                # Check tables
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                result['tables'] = tables
                
                if 'providers' in tables:
                    result['initialized'] = True
                    
                    # Count providers
                    count_result = conn.execute(text("SELECT COUNT(*) FROM providers"))
                    result['provider_count'] = count_result.scalar()
                    
                    logger.info(f"✅ Database initialized with {len(tables)} tables")
                    logger.info(f"✅ Provider count: {result['provider_count']}")
                    logger.info(f"   Tables: {', '.join(tables)}")
                else:
                    logger.warning("⚠️ Database connected but 'providers' table not found")
                    
        except Exception as e:
            logger.error(f"❌ Database connection failed: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    def initialize_database(self) -> bool:
        """Initialize database tables if needed"""
        logger.info("\n" + "=" * 80)
        logger.info("INITIALIZING DATABASE")
        logger.info("=" * 80)
        
        try:
            import os
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            
            from src.core.database import DatabaseManager, Base
            
            # Initialize database manager (this creates tables)
            db = DatabaseManager()
            
            # Verify tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'providers' in tables and 'metrics' in tables:
                logger.info(f"✅ Database initialized successfully")
                logger.info(f"   Created tables: {', '.join(tables)}")
                return True
            else:
                logger.error(f"❌ Database initialization incomplete")
                logger.error(f"   Expected: providers, metrics")
                logger.error(f"   Found: {', '.join(tables)}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {str(e)}")
            return False
    
    def install_missing_packages(self, packages: List[str]) -> bool:
        """Install missing required packages"""
        if not packages:
            return True
            
        logger.info("\n" + "=" * 80)
        logger.info("INSTALLING MISSING PACKAGES")
        logger.info("=" * 80)
        
        for package in packages:
            logger.info(f"Installing {package}...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                logger.info(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError:
                logger.error(f"❌ Failed to install {package}")
                return False
        
        return True
    
    def generate_minimal_requirements(self):
        """Generate minimal requirements.txt for campaign"""
        logger.info("\n" + "=" * 80)
        logger.info("MINIMAL REQUIREMENTS FOR CAMPAIGN")
        logger.info("=" * 80)
        
        minimal_requirements = """# Minimal requirements for healthcare provider campaign
# Database
sqlalchemy==2.0.31
psycopg2-binary==2.9.9

# API integrations
requests==2.31.0
googlemaps==4.10.0
anthropic==0.34.1

# Configuration
python-dotenv==1.0.1

# Data processing
pandas==2.2.2

# Japanese text processing
cutlet>=0.3.0

# Utilities
pytz==2023.3
python-dateutil==2.8.2

# Google Cloud monitoring (for cost tracking)
google-cloud-monitoring>=2.0.0
google-cloud-billing>=1.11.0
"""
        
        logger.info("Creating minimal requirements file...")
        with open('requirements-minimal.txt', 'w') as f:
            f.write(minimal_requirements)
        
        logger.info("✅ Created requirements-minimal.txt")
        logger.info("\nUnnecessary packages for campaign:")
        for pkg in self.unnecessary_packages[:10]:  # Show first 10
            logger.info(f"  - {pkg}")
        if len(self.unnecessary_packages) > 10:
            logger.info(f"  ... and {len(self.unnecessary_packages) - 10} more")
    
    def run_complete_verification(self):
        """Run complete system verification"""
        logger.info("=" * 80)
        logger.info("HEALTHCARE PROVIDER CAMPAIGN - SYSTEM VERIFICATION")
        logger.info("=" * 80)
        
        # 1. Check packages
        package_results = self.check_requirements()
        
        # 2. Install missing required packages if any
        if package_results['missing_required']:
            logger.warning(f"\n⚠️ Missing {len(package_results['missing_required'])} required packages")
            response = input("Install missing packages? (y/n): ")
            if response.lower() == 'y':
                success = self.install_missing_packages(package_results['missing_required'])
                if not success:
                    logger.error("Failed to install some packages")
                    return False
        
        # 3. Check database
        db_results = self.check_database_connection()
        
        # 4. Initialize database if needed
        if db_results['connected'] and not db_results['initialized']:
            logger.warning("\n⚠️ Database connected but not initialized")
            response = input("Initialize database tables? (y/n): ")
            if response.lower() == 'y':
                success = self.initialize_database()
                if not success:
                    logger.error("Failed to initialize database")
                    return False
        elif not db_results['connected']:
            logger.error("\n❌ Cannot connect to database. Check your configuration.")
            return False
        
        # 5. Generate minimal requirements
        self.generate_minimal_requirements()
        
        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 80)
        
        if not package_results['missing_required'] and db_results['initialized']:
            logger.info("✅ System ready for healthcare provider campaign!")
            logger.info(f"   - All required packages installed")
            logger.info(f"   - Database initialized with {db_results['provider_count']} providers")
            logger.info(f"   - {len(self.unnecessary_packages)} optional packages can be skipped")
            return True
        else:
            logger.error("❌ System not ready. Please fix issues above.")
            return False


if __name__ == "__main__":
    verifier = SetupVerifier()
    success = verifier.run_complete_verification()
    sys.exit(0 if success else 1)