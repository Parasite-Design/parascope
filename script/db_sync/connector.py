import config
import pyodbc
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient

class SqlConnector:
    def __init__(self):
        required_configs = [
            config.ODBC_DRIVER_VERSION,
            config.SQL_SERVER,
            config.SQL_DATABASE_NAME,
            config.SQL_USERNAME,
            config.SQL_PASSWORD,
        ]
        if any(val is None for val in required_configs):
            raise ValueError("One or more required database configuration values are missing.")

        try:
            self.connection = pyodbc.connect(
                f"DRIVER={{ODBC Driver {config.ODBC_DRIVER_VERSION} for SQL Server}};"
                f"SERVER={config.SQL_SERVER};"
                f"DATABASE={config.SQL_DATABASE_NAME};"
                f"UID={config.SQL_USERNAME};"
                f"PWD={config.SQL_PASSWORD};"
                f"Encrypt={config.ENCRYPT};"
                f"TrustServerCertificate={config.TRUST_SERVER_CERT};"
            )
            self.cursor = self.connection.cursor()
        except pyodbc.Error as e:
            print(f"SQL Database connection failed: {e}")
            self.connection = None
            self.cursor = None

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class MongoDbConnector:
    """
    MongoDB Connector class with context manager support.
    """

    def __init__(self):
        required_configs = [
            config.MONGODB_URI,
            config.MONGODB_DATABASE_NAME,
        ]
        if any(val is None for val in required_configs):
            raise ValueError("One or more required MongoDB configuration values are missing.")

        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None

        try:
            self.client = AsyncIOMotorClient(config.MONGODB_URI)
            self.db = self.client[config.MONGODB_DATABASE_NAME] # pyright: ignore[reportArgumentType]
            # Test connection (async, so we provide a sync wrapper for context manager)
            # For async usage, call await self.ping()
            print("MongoDB client initialized")
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            self.client = None
            self.db = None

    async def ping(self):
        """Async ping to test connection."""
        if self.client:
            try:
                await self.client.admin.command("ping")
            except Exception as e:
                print(f"Failed to ping MongoDB Atlas: {e}")
                self.client = None
                self.db = None

    def close(self):
        if self.client:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

if __name__ == "__main__":
    with SqlConnector() as conn:
        pass

if __name__ == "__main__":
    import asyncio

    async def main():
        with MongoDbConnector() as mongo:
            if mongo.client:
                await mongo.ping()

    asyncio.run(main())

