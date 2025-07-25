"""Module use for providing database connection utilities"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDB:
    """Class used for storing MongoDB connections informations
    """
    client: AsyncIOMotorClient
    db = None

mongodb = MongoDB()

async def connect_to_mongo():
    """function used to connect to mongodb
    """
    mongodb.client = AsyncIOMotorClient(settings.MONGODB_URI)
    mongodb.db = mongodb.client[settings.DB_NAME] # pyright: ignore[reportAttributeAccessIssue]
    print("Connected to MongoDB")

async def close_mongo_connection():
    """function used to close the mongodb connection
    """
    mongodb.client.close()
    print("Closed MongoDB connection")

def get_db():
    """return the current mongoDB connection for access

    Returns:
        current mongoDB connection
    """
    return mongodb.db
