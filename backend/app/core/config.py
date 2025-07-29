"""Module use for storing settings and giving access to them via the "settings" variable"""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """A class used to store the settings for standard access"""

    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "dev_db")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")


settings = Settings()
