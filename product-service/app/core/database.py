from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from app.core.config import settings

client: AsyncIOMotorClient = None
db = None

sync_client: MongoClient = None
sync_db = None


async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_CONNECTION_URL)
    db = client[settings.MONGODB_DATABASE]
    print(f"Connected to MongoDB: {settings.MONGODB_DATABASE}")


async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("Closed MongoDB connection")


def get_database():
    return db


def get_sync_database():
    """Sync client for RabbitMQ consumer thread."""
    global sync_client, sync_db
    if sync_db is None:
        sync_client = MongoClient(settings.MONGODB_CONNECTION_URL)
        sync_db = sync_client[settings.MONGODB_DATABASE]
    return sync_db
