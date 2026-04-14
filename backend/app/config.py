import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg://postgres:ConnectR9_4@localhost:5432/rehabconnect')
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'