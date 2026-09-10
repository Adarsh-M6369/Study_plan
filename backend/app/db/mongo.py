import logging
import datetime
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

logger = logging.getLogger("db.mongo")

_client: Optional[AsyncIOMotorClient] = None
_db = None

# Fallback local in-memory store if MongoDB is unavailable
_memory_store: Dict[str, Dict[str, Any]] = {
    "study_packs": {},
    "documents": {},
    "users": {}
}


async def init_mongo_connection() -> Optional[AsyncIOMotorClient]:
    """
    Connects to MongoDB using settings.MONGO_URL, falling back to settings.MONGO_URL_local.
    Returns AsyncIOMotorClient or None if both fail (in which case in-memory fallback is active).
    """
    global _client, _db
    if _client is not None:
        return _client

    urls_to_try = []
    if settings.MONGO_URL:
        urls_to_try.append(("remote", settings.MONGO_URL))
    if settings.MONGO_URL_local:
        urls_to_try.append(("local", settings.MONGO_URL_local))
    if not urls_to_try:
        urls_to_try.append(("default_local", "mongodb://127.0.0.1:27017"))

    for source_type, url in urls_to_try:
        try:
            logger.info(f"Attempting MongoDB connection to ({source_type}): {url.split('@')[-1] if '@' in url else url}")
            client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=2000)
            # Test server connection ping
            await client.admin.command('ping')
            _client = client
            _db = client[settings.DB_NAME]
            logger.info(f"Successfully connected to MongoDB database '{settings.DB_NAME}' via {source_type}")
            return _client
        except Exception as e:
            logger.warning(f"MongoDB connection to {source_type} failed: {e}")

    logger.warning("All MongoDB connections failed. Running with resilient in-memory storage fallback.")
    return None


async def get_db():
    global _db
    if _db is None:
        await init_mongo_connection()
    return _db


async def save_study_pack(user_id: str, study_pack_data: dict) -> str:
    """Save generated study pack with user_id multi-tenant partition."""
    db = await get_db()
    pack_id = study_pack_data.get("id") or f"pack_{int(datetime.datetime.utcnow().timestamp()*1000)}"
    record = {
        "_id": pack_id,
        "id": pack_id,
        "user_id": user_id,
        "data": study_pack_data,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    if db is not None:
        try:
            await db.study_packs.update_one({"_id": pack_id}, {"$set": record}, upsert=True)
            return pack_id
        except Exception as e:
            logger.error(f"Failed to persist study pack to MongoDB: {e}. Storing in memory fallback.")

    # In-memory store
    _memory_store["study_packs"][pack_id] = record
    return pack_id


async def get_study_packs_by_user(user_id: str) -> List[dict]:
    """Retrieve all study packs belonging to the specified user."""
    db = await get_db()
    if db is not None:
        try:
            cursor = db.study_packs.find({"user_id": user_id}).sort("created_at", -1)
            results = await cursor.to_list(length=100)
            return [r["data"] for r in results if "data" in r]
        except Exception as e:
            logger.error(f"Failed reading study packs from MongoDB: {e}")

    # In-memory fallback
    return [
        rec["data"]
        for rec in _memory_store["study_packs"].values()
        if rec.get("user_id") == user_id and "data" in rec
    ]


async def get_study_pack_by_id(pack_id: str, user_id: str) -> Optional[dict]:
    """Retrieve single study pack with multi-tenant check."""
    db = await get_db()
    if db is not None:
        try:
            doc = await db.study_packs.find_one({"_id": pack_id, "user_id": user_id})
            if doc and "data" in doc:
                return doc["data"]
        except Exception as e:
            logger.error(f"Failed to get study pack {pack_id}: {e}")

    rec = _memory_store["study_packs"].get(pack_id)
    if rec and rec.get("user_id") == user_id:
        return rec.get("data")
    return None


async def save_document_metadata(user_id: str, doc_metadata: dict) -> None:
    """Record uploaded document metadata for user audit."""
    db = await get_db()
    doc_id = doc_metadata.get("document_id") or f"doc_{int(datetime.datetime.utcnow().timestamp())}"
    record = {
        "_id": doc_id,
        "user_id": user_id,
        "metadata": doc_metadata,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    if db is not None:
        try:
            await db.documents.update_one({"_id": doc_id}, {"$set": record}, upsert=True)
            return
        except Exception as e:
            logger.error(f"Failed to save document metadata: {e}")
    _memory_store["documents"][doc_id] = record


async def get_user_documents(user_id: str) -> List[dict]:
    db = await get_db()
    if db is not None:
        try:
            cursor = db.documents.find({"user_id": user_id}).sort("created_at", -1)
            results = await cursor.to_list(length=50)
            return [r["metadata"] for r in results if "metadata" in r]
        except Exception as e:
            logger.error(f"Error fetching user documents: {e}")

    return [
        rec["metadata"]
        for rec in _memory_store["documents"].values()
        if rec.get("user_id") == user_id and "metadata" in rec
    ]
