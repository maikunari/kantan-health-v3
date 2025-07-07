from dotenv import load_dotenv
from sqlalchemy import create_engine
import os

load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))
db_user = os.getenv("POSTGRES_USER", "postgres")
db_password = os.getenv("POSTGRES_PASSWORD", "password")
db_host = os.getenv("POSTGRES_HOST", "localhost")

engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:5432/directory")
try:
    with engine.connect() as connection:
        print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {str(e)}")