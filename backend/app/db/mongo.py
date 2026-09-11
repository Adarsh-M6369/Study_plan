import logging
import datetime
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

logger = logging.getLogger("db.mongo")

_client: Optional[AsyncIOMotorClient] = None
_db = None

# Resilient user-isolated in-memory fallback store
_memory_store: Dict[str, Dict[str, Dict[str, Any]]] = {
    "documents": {},
    "chunks": {},
    "study_packs": {},
    "user_quiz_history": {}
}


async def init_mongo_connection() -> Optional[AsyncIOMotorClient]:
    """
    Connects to MongoDB using settings.MONGO_URL, falling back to settings.MONGO_URL_local.
    Target database is settings.DB_NAME (Studypack_generator).
    Sets up dedicated indexes on 'documents', 'chunks', 'study_packs', and 'user_quiz_history'.
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
            clean_url_log = url.split('@')[-1] if '@' in url else url
            logger.info(f"Attempting MongoDB connection to ({source_type}): {clean_url_log}")
            client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=2500)
            await client.admin.command('ping')
            _client = client
            _db = client[settings.DB_NAME]
            logger.info(f"Successfully connected to MongoDB database '{settings.DB_NAME}' via {source_type}")

            # Create compound multi-tenant indexes across the 3 core collections
            try:
                await _db.documents.create_index([("user_id", 1), ("created_at", -1)])
                await _db.documents.create_index([("document_id", 1), ("user_id", 1)], unique=True)
                await _db.chunks.create_index([("user_id", 1), ("document_id", 1), ("chunk_index", 1)])
                await _db.study_packs.create_index([("user_id", 1), ("created_at", -1)])
                await _db.study_packs.create_index([("pack_id", 1), ("user_id", 1)])
                await _db.user_quiz_history.create_index([("user_id", 1), ("completed_at", -1)])
                logger.info("Multi-tenant compound indexes verified on 'documents', 'chunks', 'study_packs', and 'user_quiz_history'.")
            except Exception as idx_err:
                logger.warning(f"Index creation note: {idx_err}")

            return _client
        except Exception as e:
            logger.warning(f"MongoDB connection to {source_type} failed: {e}")

    logger.warning("All MongoDB connections offline. Running with resilient isolated in-memory storage fallback.")
    return None


async def get_db():
    global _db
    if _db is None:
        await init_mongo_connection()
    return _db


# =====================================================================
# 1. COLLECTION: documents (Full metadata, page breakdown & status)
# =====================================================================

async def save_document(
    user_id: str,
    document_id: str,
    filename: str,
    title: str,
    page_count: int,
    chunk_count: int,
    chapters: List[str],
    clean_text: str,
    pages_data: Optional[List[Dict[str, Any]]] = None,
    status: str = "indexed"
) -> Dict[str, Any]:
    """
    Saves complete parsed document metadata, page-by-page mapping, and chapters in 'documents' collection,
    strictly scoped by user_id and document_id.
    """
    db = await get_db()
    now = datetime.datetime.utcnow().isoformat()

    # Clean pages_data to store exact content and page number details
    formatted_pages = []
    if pages_data:
        for p in pages_data:
            formatted_pages.append({
                "page_number": p.get("page_number", 1),
                "text": p.get("text", "")[:5000],  # store page text content
                "char_count": len(p.get("text", "")),
                "chapter_title": p.get("chapter_title", "")
            })

    record = {
        "_id": f"{user_id}_{document_id}",
        "document_id": document_id,
        "user_id": user_id,
        "filename": filename,
        "title": title,
        "page_count": page_count,
        "chunk_count": chunk_count,
        "chapters": chapters,
        "pages": formatted_pages,
        "clean_text_preview": clean_text[:20000],
        "status": status,
        "created_at": now,
        "updated_at": now
    }

    if db is not None:
        try:
            await db.documents.update_one(
                {"document_id": document_id, "user_id": user_id},
                {"$set": record},
                upsert=True
            )
            # Also keep backward compatibility with user_documents
            await db.user_documents.update_one(
                {"document_id": document_id, "user_id": user_id},
                {"$set": record},
                upsert=True
            )
            logger.info(f"Saved document '{title}' ({page_count} pages, {chunk_count} chunks) in MongoDB 'documents' collection for user '{user_id}'.")
            return record
        except Exception as e:
            logger.error(f"Failed to persist document to MongoDB: {e}")

    # In-memory tenant partition
    if user_id not in _memory_store["documents"]:
        _memory_store["documents"][user_id] = {}
    _memory_store["documents"][user_id][document_id] = record
    return record


async def get_documents(user_id: str) -> List[Dict[str, Any]]:
    """Retrieves all documents belonging strictly to the specified user_id from 'documents' collection."""
    db = await get_db()
    if db is not None:
        try:
            cursor = db.documents.find({"user_id": user_id}).sort("created_at", -1)
            docs = await cursor.to_list(length=100)
            if not docs:
                # fallback check for user_documents
                cursor_old = db.user_documents.find({"user_id": user_id}).sort("created_at", -1)
                docs = await cursor_old.to_list(length=100)
            return docs
        except Exception as e:
            logger.error(f"Error fetching documents: {e}")

    return list(_memory_store["documents"].get(user_id, {}).values())


async def get_document_by_id(user_id: str, document_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves single document enforcing strict user_id isolation."""
    db = await get_db()
    if db is not None:
        try:
            doc = await db.documents.find_one({"document_id": document_id, "user_id": user_id})
            if not doc:
                doc = await db.user_documents.find_one({"document_id": document_id, "user_id": user_id})
            return doc
        except Exception as e:
            logger.error(f"Error fetching document {document_id}: {e}")

    return _memory_store["documents"].get(user_id, {}).get(document_id)


# =====================================================================
# 2. COLLECTION: chunks (Stores EVERY individual chunk with page/index)
# =====================================================================

async def save_chunks(chunks_list: List[Dict[str, Any]]) -> int:
    """
    Batch inserts all individual extracted chunks into MongoDB 'chunks' collection in Studypack_generator.
    Each chunk document contains:
      - document_id, user_id, chunk_index, page_number, text, chapter_title, segment_index, created_at
    """
    if not chunks_list:
        return 0

    db = await get_db()
    now = datetime.datetime.utcnow().isoformat()

    formatted_records = []
    for c in chunks_list:
        doc_id = str(c.get("document_id", "doc_0"))
        user_id = str(c.get("user_id", "default_user"))
        idx = int(c.get("chunk_index", 0))

        record = {
            "_id": f"{user_id}_{doc_id}_chk_{idx}",
            "document_id": doc_id,
            "user_id": user_id,
            "chunk_index": idx,
            "page_number": c.get("page_number", 1),
            "text": c.get("text", ""),
            "chapter_title": c.get("chapter_title", ""),
            "segment_index": c.get("segment_index", 0),
            "char_count": len(c.get("text", "")),
            "created_at": c.get("created_at") or now
        }
        formatted_records.append(record)

    if db is not None:
        try:
            for r in formatted_records:
                await db.chunks.update_one(
                    {"_id": r["_id"]},
                    {"$set": r},
                    upsert=True
                )
            logger.info(f"Successfully saved {len(formatted_records)} chunks in MongoDB 'chunks' collection.")
            return len(formatted_records)
        except Exception as e:
            logger.error(f"Failed saving chunks to MongoDB: {e}")

    # Fallback to in-memory store
    for r in formatted_records:
        uid = r["user_id"]
        if uid not in _memory_store["chunks"]:
            _memory_store["chunks"][uid] = {}
        _memory_store["chunks"][uid][r["_id"]] = r

    return len(formatted_records)


async def get_chunks_by_document(user_id: str, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves all chunks belonging to a document and user from 'chunks' collection,
    ordered by chunk_index.
    """
    db = await get_db()
    query = {"user_id": user_id}
    if document_id:
        query["document_id"] = document_id

    if db is not None:
        try:
            cursor = db.chunks.find(query).sort("chunk_index", 1)
            chunks = await cursor.to_list(length=1000)
            return chunks
        except Exception as e:
            logger.error(f"Failed fetching chunks from MongoDB: {e}")

    # In-memory retrieval
    all_user_chunks = list(_memory_store["chunks"].get(user_id, {}).values())
    if document_id:
        all_user_chunks = [c for c in all_user_chunks if c.get("document_id") == document_id]
    all_user_chunks.sort(key=lambda x: x.get("chunk_index", 0))
    return all_user_chunks


# =====================================================================
# 3. COLLECTION: study_packs (Generated summaries, MCQs, Q&As, etc.)
# =====================================================================

async def save_study_pack(user_id: str, study_pack_data: dict, document_id: Optional[str] = None) -> str:
    """
    Saves generated study pack (20 MCQs, 5 Q&As, summary, roadmap, glossary)
    in collection 'study_packs' scoped strictly by user_id and document_id.
    """
    db = await get_db()
    pack_id = study_pack_data.get("id") or f"pack_{int(datetime.datetime.utcnow().timestamp()*1000)}"
    now = datetime.datetime.utcnow().isoformat()
    doc_id = document_id or study_pack_data.get("document_id")

    record = {
        "_id": f"{user_id}_{pack_id}",
        "pack_id": pack_id,
        "document_id": doc_id,
        "user_id": user_id,
        "title": study_pack_data.get("title", "Study Pack"),
        "difficulty": study_pack_data.get("difficulty", "Intermediate"),
        "data": study_pack_data,
        "created_at": now
    }

    if db is not None:
        try:
            await db.study_packs.update_one(
                {"pack_id": pack_id, "user_id": user_id},
                {"$set": record},
                upsert=True
            )
            logger.info(f"Saved study pack '{pack_id}' in MongoDB 'study_packs' collection for user '{user_id}'.")
            return pack_id
        except Exception as e:
            logger.error(f"Failed to persist study pack: {e}")

    if user_id not in _memory_store["study_packs"]:
        _memory_store["study_packs"][user_id] = {}
    _memory_store["study_packs"][user_id][pack_id] = record
    return pack_id


async def get_study_packs_by_user(user_id: str) -> List[dict]:
    """Retrieves all study packs belonging strictly to the authenticated user."""
    db = await get_db()
    if db is not None:
        try:
            cursor = db.study_packs.find({"user_id": user_id}).sort("created_at", -1)
            results = await cursor.to_list(length=100)
            return [r["data"] for r in results if "data" in r]
        except Exception as e:
            logger.error(f"Failed reading study packs: {e}")

    return [
        rec["data"]
        for rec in _memory_store["study_packs"].get(user_id, {}).values()
        if "data" in rec
    ]


async def get_study_pack_by_id(pack_id: str, user_id: str) -> Optional[dict]:
    """Retrieves single study pack with multi-tenant user_id verification."""
    db = await get_db()
    if db is not None:
        try:
            doc = await db.study_packs.find_one({"pack_id": pack_id, "user_id": user_id})
            if doc and "data" in doc:
                return doc["data"]
        except Exception as e:
            logger.error(f"Failed to get study pack: {e}")

    rec = _memory_store["study_packs"].get(user_id, {}).get(pack_id)
    return rec.get("data") if rec else None


# =====================================================================
# 4. COLLECTION: user_quiz_history (Quiz submissions and analytics)
# =====================================================================

async def save_quiz_result(
    user_id: str,
    pack_id: str,
    document_id: Optional[str],
    score: int,
    total: int,
    answers: Dict[str, str]
) -> Dict[str, Any]:
    """
    Records student interactive quiz submissions, scores, and completion status
    in collection 'user_quiz_history' scoped strictly by user_id.
    """
    db = await get_db()
    now = datetime.datetime.utcnow().isoformat()
    quiz_id = f"quiz_{int(datetime.datetime.utcnow().timestamp()*1000)}"
    pct = round((score / total * 100), 1) if total > 0 else 0.0

    record = {
        "_id": f"{user_id}_{quiz_id}",
        "quiz_id": quiz_id,
        "user_id": user_id,
        "pack_id": pack_id,
        "document_id": document_id,
        "score": score,
        "total": total,
        "percentage": pct,
        "answers": answers,
        "completed_at": now
    }

    if db is not None:
        try:
            await db.user_quiz_history.insert_one(record)
            logger.info(f"Recorded quiz result ({score}/{total}) in 'user_quiz_history' for user '{user_id}'.")
            return record
        except Exception as e:
            logger.error(f"Failed to save quiz result: {e}")

    if user_id not in _memory_store["user_quiz_history"]:
        _memory_store["user_quiz_history"][user_id] = {}
    _memory_store["user_quiz_history"][user_id][quiz_id] = record
    return record


async def get_user_quiz_history(user_id: str) -> List[Dict[str, Any]]:
    """Retrieves quiz score history for the user."""
    db = await get_db()
    if db is not None:
        try:
            cursor = db.user_quiz_history.find({"user_id": user_id}).sort("completed_at", -1)
            return await cursor.to_list(length=50)
        except Exception as e:
            logger.error(f"Error fetching quiz history: {e}")

    return list(_memory_store["user_quiz_history"].get(user_id, {}).values())


# =====================================================================
# 5. COLLECTION: mcp_connectors (MCP Connector Configuration & Status)
# =====================================================================

async def save_connector_config(
    user_id: str,
    connector_id: str,
    enabled: bool,
    config: Optional[Dict[str, Any]] = None,
    status: str = "connected"
) -> Dict[str, Any]:
    """
    Saves or updates user configuration and active status for an MCP connector
    in collection 'mcp_connectors' strictly scoped by user_id and connector_id.
    """
    db = await get_db()
    now = datetime.datetime.utcnow().isoformat()
    record = {
        "_id": f"{user_id}_{connector_id}",
        "user_id": user_id,
        "connector_id": connector_id,
        "enabled": enabled,
        "status": status if enabled else "disconnected",
        "config": config or {},
        "updated_at": now
    }

    if db is not None:
        try:
            await db.mcp_connectors.update_one(
                {"user_id": user_id, "connector_id": connector_id},
                {"$set": record},
                upsert=True
            )
            logger.info(f"Saved MCP connector '{connector_id}' (enabled={enabled}) for user '{user_id}'.")
            return record
        except Exception as e:
            logger.error(f"Failed to persist connector config: {e}")

    if "mcp_connectors" not in _memory_store:
        _memory_store["mcp_connectors"] = {}
    if user_id not in _memory_store["mcp_connectors"]:
        _memory_store["mcp_connectors"][user_id] = {}
    _memory_store["mcp_connectors"][user_id][connector_id] = record
    return record


async def get_user_connectors(user_id: str) -> List[Dict[str, Any]]:
    """Retrieves all MCP connector configurations for the authenticated user."""
    db = await get_db()
    if db is not None:
        try:
            cursor = db.mcp_connectors.find({"user_id": user_id})
            return await cursor.to_list(length=50)
        except Exception as e:
            logger.error(f"Error fetching user MCP connectors: {e}")

    if "mcp_connectors" not in _memory_store:
        _memory_store["mcp_connectors"] = {}
    return list(_memory_store["mcp_connectors"].get(user_id, {}).values())


async def get_connector_config(user_id: str, connector_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves specific MCP connector configuration for the user."""
    db = await get_db()
    if db is not None:
        try:
            return await db.mcp_connectors.find_one({"user_id": user_id, "connector_id": connector_id})
        except Exception as e:
            logger.error(f"Error fetching connector {connector_id}: {e}")

    if "mcp_connectors" not in _memory_store:
        _memory_store["mcp_connectors"] = {}
    return _memory_store["mcp_connectors"].get(user_id, {}).get(connector_id)


# =====================================================================
# Backward-compatibility aliases
# =====================================================================
save_user_document = save_document
get_user_documents = get_documents
get_user_document_by_id = get_document_by_id

async def save_document_metadata(user_id: str, doc_metadata: dict) -> None:
    await save_document(
        user_id=user_id,
        document_id=doc_metadata.get("document_id", "doc_0"),
        filename=doc_metadata.get("filename", "document.pdf"),
        title=doc_metadata.get("title", "Lecture Notes"),
        page_count=doc_metadata.get("page_count", 1),
        chunk_count=doc_metadata.get("chunk_count", 0),
        chapters=doc_metadata.get("chapters", []),
        clean_text=doc_metadata.get("clean_text", ""),
        pages_data=doc_metadata.get("pages_data")
    )

