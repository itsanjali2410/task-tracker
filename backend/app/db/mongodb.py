from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    
mongodb = MongoDB()

async def connect_to_mongo():
    """Connect to MongoDB"""
    logger.info("Connecting to MongoDB...")
    mongodb.client = AsyncIOMotorClient(settings.MONGODB_URI)
    logger.info("Connected to MongoDB successfully")

async def close_mongo_connection():
    """Close MongoDB connection"""
    logger.info("Closing MongoDB connection...")
    mongodb.client.close()
    logger.info("MongoDB connection closed")

def get_database():
    """Get database instance"""
    return mongodb.client[settings.DB_NAME]
