"""Module for providing MongoDB Atlas connection utilities."""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


class MongoDB:
    """Class for storing MongoDB connection information."""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None


mongodb = MongoDB()


async def connect_to_mongo():
    """Connect to MongoDB Atlas using the URI from settings."""
    try:
        mongodb.client = AsyncIOMotorClient(settings.MONGODB_ATLAS_URI)
        mongodb.db = mongodb.client[settings.DB_NAME]  # pyright: ignore[reportAttributeAccessIssue]
        await mongodb.client.admin.command("ping")
        print("Connected to MongoDB Atlas")
    except Exception as e:
        print(f"Failed to connect to MongoDB Atlas: {e}")
        mongodb.client = None
        mongodb.db = None


async def close_mongo_connection():
    """Close the MongoDB Atlas connection."""
    try:
        if mongodb.client:
            mongodb.client.close()
            print("Closed MongoDB Atlas connection")
    except Exception as e:
        print(f"Error closing MongoDB Atlas connection: {e}")


def get_db():
    """Return the current MongoDB database connection.

    Returns:
        The current MongoDB database connection.

    Raises:
        RuntimeError: If the database connection is not established.
    """
    if mongodb.db is None:
        raise RuntimeError("MongoDB connection has not been established.")
    return mongodb.db
