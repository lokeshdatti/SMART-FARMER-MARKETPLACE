import os

# Helper function to load environment variables from .env manually
def load_dotenv(env_path):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    key = key.strip()
                    if key not in os.environ:
                        os.environ[key] = val.strip()

# Locate application directory and load env configuration
base_dir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(base_dir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-green-veg-2026')
    
    # Configure Database Connection (SQLite fallback, MySQL compatible)
    # If the user has a local SQLite, it's stored in C:\Lokesh\marketplace.db
    # If they specify MySQL in .env, it connects to MySQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(base_dir, 'marketplace.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SMTP email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587)) if os.environ.get('MAIL_PORT') else None
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
