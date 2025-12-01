from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

client = None
db = None

def init_db():
    global client, db
    if settings.mongo_uri:
        client = AsyncIOMotorClient(settings.mongo_uri)
        db = client[settings.mongo_db]
    else:
        db = None
