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
def fix_id(doc):
    """Convert MongoDB _id to string id and handle datetime objects"""
    if doc:
        doc["id"] = str(doc.get("id") or doc.get("_id"))
        if "_id" in doc:
            del doc["_id"]
    return doc

async def to_list(cursor, limit=100):
    """Helper to convert cursor to list with fixed IDs"""
    return [fix_id(doc) for doc in await cursor.to_list(length=limit)]