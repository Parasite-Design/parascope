import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file in the same directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

def load_json(path):
    with open(path, 'r') as file:
        return json.load(file)

# Sync config
SYNC_DELAY = int(os.getenv('SYNC_DELAY', '86400'))

# SQL database config
SQL_SERVER = os.getenv('SQL_SERVER')
SQL_DATABASE_NAME = os.getenv('SQL_DATABASE_NAME')
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')
ODBC_DRIVER_VERSION = os.getenv('ODBC_DRIVER_VERSION')
ENCRYPT = os.getenv('SQL_ENCRYPT', 'No')
TRUST_SERVER_CERT = os.getenv('SQL_TRUST_SERVER_CERTIFICATE', 'No')

# MongoDB database config
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DATABASE_NAME = os.getenv('MONGODB_DATABASE_NAME')

YEAR_LIMIT = int(os.getenv('YEAR_LIMIT', 6))

MIGRATION_CONFIG = load_json(os.getenv("MIGRATION_CONFIG_PATH"))
MIGRATION_CLEANUP_CONFIG = load_json(os.getenv("MIGRATION_CLEANUP_CONFIG_PATH"))
LINKING_CONFIG = load_json(os.getenv("LINKING_CONFIG_PATH"))
INDEXING_CONFIG = load_json(os.getenv("INDEXING_CONFIG_PATH"))
LINKING_CLEANUP_CONFIG = load_json(os.getenv("LINKING_CLEANUP_CONFIG_PATH"))

LINKING_TEMPLATE_PATH = os.getenv("LINKING_TEMPLATE_PATH")
