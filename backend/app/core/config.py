"""Module use for storing settings and giving access to them via the "settings" variable"""

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """A class used to store the settings for standard access"""

    def __init__(self):
        self.MONGODB_ATLAS_URI: str = os.getenv(
            "MONGODB_ATLAS_URI", "mongodb://root:example@mongodb:27017"
        )  # MongoDB connection URI (str)
        self.DB_NAME: str = os.getenv("DB_NAME", "dev_db")  # Database name (str)
        self.ENVIRONMENT: str = os.getenv(
            "ENVIRONMENT", "development"
        )  # App environment, e.g., 'development', 'production' (str)

        self.JWT_SECRET_KEY: str | None = os.getenv(
            "JWT_SECRET_KEY"
        )  # Secret key for JWT signing (str)
        self.JWT_ALGORITHM: str | None = os.getenv(
            "JWT_ALGORITHM"
        )  # Algorithm used for JWT, e.g., 'HS256' (str)
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
        )  # Access token expiry in minutes (int)
        self.REFRESH_TOKEN_EXPIRE_DAYS: int = int(
            os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)
        )  # Refresh token expiry in days (int)

        if not self.JWT_SECRET_KEY or not self.JWT_ALGORITHM:
            raise ValueError(
                "JWT_SECRET_KEY and JWT_ALGORITHM must be set in environment variables."
            )


settings = Settings()
