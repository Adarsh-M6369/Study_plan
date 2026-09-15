import re
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from app.config import settings
from app.auth.clerk import get_current_user, AuthenticatedUser
from app.db.mongo import (
    init_mongo_connection,
    save_study_pack,
    save_document,
    get_documents,
    save_chunks,
    get_chunks_by_document,
    save_user_document,
    get_user_documents,
    get_study_packs_by_user,
    save_quiz_result,
    get_user_quiz_history,
    save_connector_config,
    get_user_connectors,
    get_connector_config
)
from app.mcp import (
    CONNECTOR_DEFINITIONS,
    run_mcp_connector_tool,
    test_connector_connection
)
from app.rag.parser import parse_pdf_bytes, clean_text
from app.rag.splitter import split_text_into_chunks
from app.rag.store import get_vector_store
from app.graph.workflow import run_study_pack_pipeline
from app.exports.pdf_engine import generate_study_pack_pdf
from app.exports.csv_engine import generate_anki_csv
from app.schemas.request import (
    IngestTextRequest,
    GenerateRequest,
    UploadResponse,
    QuizSubmitRequest,
    MCPConnectRequest,
    MCPDisconnectRequest,
    MCPTestRequest,
    MCPExecuteToolRequest
)
from app.schemas.study_pack import StudyPack, MCQItem
from app.schemas.chat import StudyChatRequest, StudyChatResponse
from app.chat import process_study_chat

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("app.main")

app = FastAPI(
    title="Study Guide Generator API",
    description="Full-stack AI-powered study pack generator with RAG, LangGraph, and Clerk authentication.",
    version="1.0.0"
)

# Setup CORS
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    settings.FRONTEND_URL,
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initializes MongoDB connection and creates multi-tenant indexes on startup."""
    logger.info("Starting Study Guide Generator API backend...")
    await init_mongo_connection()
    if settings.is_langsmith_enabled:
        logger.info(f"🎯 LangSmith Tracing: ENABLED (Project: {settings.LANGCHAIN_PROJECT}, Endpoint: {settings.LANGCHAIN_ENDPOINT})")
    else:
        logger.info("ℹ️ LangSmith Tracing: DISABLED (LANGCHAIN_API_KEY or LANGSMITH_API_KEY not configured)")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend status."""
    return {
        "status": "ok",
        "service": "Study Guide Generator API",
        "auth": "Clerk JWT Enabled",
        "langsmith_tracing": "enabled" if settings.is_langsmith_enabled else "disabled",
        "langsmith_project": settings.LANGCHAIN_PROJECT if settings.is_langsmith_enabled else None
    }


@app.post("/api/upload", response_model=UploadResponse, tags=["Document Ingestion"])
async def upload_file(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Uploads and parses a PDF (enforcing strict 150-page limit) or raw lecture text,
    detects chapters, splits into sequential semantic chunks (1500 chars / 200 overlap),
    saves all chunks & page metadata into MongoDB 'chunks' and 'documents' collections,
    and indexes into the user's multi-tenant ChromaDB store.
    """
    user_id = user.user_id
    doc_title = title or (file.filename if file else "Pasted Lecture Notes")
    doc_id = f"doc_{abs(hash(doc_title + user_id)) % 1000000}"

    pages_data = []
    page_count = 1
    detected_chapters = []
    full_text = ""

    if file:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported for file upload. Use raw_text for other notes."
            )
        pdf_bytes = await file.read()
        full_text, pages_data, page_count, detected_chapters = parse_pdf_bytes(pdf_bytes, filename=file.filename)
    elif raw_text and raw_text.strip():
        cleaned = clean_text(raw_text)
        if not cleaned:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided text is empty.")
        pages_data = [{"page_number": 1, "text": cleaned, "source": doc_title, "chapter_title": doc_title}]
        page_count = 1
        detected_chapters = [doc_title]
        full_text = cleaned
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide either a PDF file or raw_text to ingest."
        )

    # 1. Chunk the text with 150-page optimization and segment distribution
    chunks = split_text_into_chunks(pages_data, chunk_size=1500, chunk_overlap=200, n_target_segments=6)

    # 2. Batch Insert all chunks into MongoDB 'chunks' collection in Studypack_generator
    db_chunks = []
    for idx, c in enumerate(chunks):
        db_chunks.append({
            "document_id": str(doc_id),
            "user_id": user_id,
            "chunk_index": idx,
            "page_number": c.get("page_number", 1),
            "text": c.get("text", ""),
            "chapter_title": c.get("chapter_title", ""),
            "segment_index": c.get("segment_index", 0),
            "char_count": len(c.get("text", ""))
        })
    await save_chunks(db_chunks)

    # 3. Index into ChromaDB vector store
    store = get_vector_store()
    chunk_count = store.add_documents(user_id=user_id, document_id=doc_id, chunks=chunks)

    # 4. Record multi-tenant document metadata & full page data in MongoDB 'documents' collection
    await save_document(
        user_id=user_id,
        document_id=doc_id,
        filename=file.filename if file else doc_title,
        title=doc_title,
        page_count=page_count,
        chunk_count=chunk_count,
        chapters=detected_chapters,
        clean_text=full_text,
        pages_data=pages_data
    )

    return UploadResponse(
        status="success",
        document_id=doc_id,
        title=doc_title,
        page_count=page_count,
        chunk_count=chunk_count,
        chapters=detected_chapters,
        message=f"Successfully parsed {page_count} pages and indexed {chunk_count} chunks across {len(detected_chapters)} chapters in MongoDB."
    )


@app.get("/api/documents", tags=["Documents"])
async def get_documents_endpoint(user: AuthenticatedUser = Depends(get_current_user)):
    """Retrieves all documents belonging strictly to the authenticated user from MongoDB."""
    docs = await get_documents(user.user_id)
    return {"status": "success", "documents": docs}


@app.post("/api/generate", response_model=StudyPack, tags=["Study Pack Generation"])
async def generate_study_guide(
    request: GenerateRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Protected generation endpoint that executes the LangGraph workflow and returns
    structured study pack JSON (20 MCQs, 5 Q&As, summary, glossary, roadmap).
    """
    user_id = user.user_id
    logger.info(f"Generating study pack for user '{user_id}' on topic '{request.topic}' with difficulty '{request.difficulty}'")

    result = await run_study_pack_pipeline(
        user_id=user_id,
        document_id=request.document_id,
        difficulty=request.difficulty,
        topic=request.topic,
        custom_instructions=request.custom_instructions
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate study pack. Please check that material is uploaded and try again."
        )

    # Persist in MongoDB / study_packs collection scoped by user_id and document_id
    await save_study_pack(user_id=user_id, study_pack_data=result, document_id=request.document_id)

    return result


@app.get("/api/history", tags=["Study Pack History"])
async def get_history(user: AuthenticatedUser = Depends(get_current_user)):
    """Retrieves previously generated study packs for the authenticated user."""
    packs = await get_study_packs_by_user(user.user_id)
    return {"status": "success", "study_packs": packs}


@app.post("/api/quiz/submit", tags=["Quiz History"])
async def submit_quiz(
    request: QuizSubmitRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Records student interactive quiz submissions, scores, and completion status
    in MongoDB collection 'user_quiz_history' strictly scoped by user_id.
    """
    record = await save_quiz_result(
        user_id=user.user_id,
        pack_id=request.pack_id,
        document_id=request.document_id,
        score=request.score,
        total=request.total,
        answers=request.answers
    )
    return {"status": "success", "quiz_record": record}


@app.get("/api/quiz/history", tags=["Quiz History"])
async def get_quiz_history(user: AuthenticatedUser = Depends(get_current_user)):
    """Retrieves past quiz attempts and scores for the authenticated user."""
    history = await get_user_quiz_history(user.user_id)
    return {"status": "success", "quiz_history": history}


@app.post("/api/export/pdf", tags=["Exports"])
async def export_pdf(pack: Dict[str, Any]):
    """
    Accepts the study pack JSON and streams a downloadable multi-page .pdf generated via ReportLab.
    """
    try:
        pdf_stream = generate_study_pack_pdf(pack)
        raw_title = str(pack.get("title") or "Study_Pack")
        clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', raw_title)[:30]
        filename = f"{clean_name}_Study_Pack.pdf"
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        logger.error(f"Error compiling ReportLab PDF: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF compilation error: {str(e)}")


@app.post("/api/export/csv", tags=["Exports"])
async def export_csv(mcqs: List[Dict[str, Any]]):
    """
    Accepts the MCQs array and streams a downloadable 2-column HTML-formatted .csv for Anki / Quizlet.
    """
    try:
        clean_mcqs = [m if isinstance(m, dict) else m.model_dump() for m in mcqs]
        csv_data = generate_anki_csv(clean_mcqs)
        csv_bytes = csv_data.encode("utf-8")
        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="Anki_Quizlet_Flashcards.csv"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        logger.error(f"Error compiling Anki CSV: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"CSV compilation error: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating Anki CSV: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"CSV generation error: {str(e)}")


# =====================================================================
# MCP CONNECTORS ENDPOINTS
# =====================================================================

@app.get("/api/mcp/connectors", tags=["MCP Connectors"])
async def get_connectors(user: AuthenticatedUser = Depends(get_current_user)):
    """
    Retrieves all available Model Context Protocol (MCP) Connectors along with
    the authenticated user's connection status and settings from MongoDB.
    """
    user_id = user.user_id
    user_configs = await get_user_connectors(user_id)
    configs_by_id = {c["connector_id"]: c for c in user_configs}

    result = []
    for defn in CONNECTOR_DEFINITIONS:
        cid = defn["id"]
        user_cfg = configs_by_id.get(cid)
        is_enabled = user_cfg.get("enabled", defn.get("default_enabled", False)) if user_cfg else defn.get("default_enabled", False)
        status_val = user_cfg.get("status", "connected" if is_enabled else "disconnected") if user_cfg else ("connected" if is_enabled else "disconnected")
        saved_config = user_cfg.get("config", {}) if user_cfg else {}

        result.append({
            **defn,
            "connected": is_enabled,
            "status": status_val,
            "active_config": saved_config
        })

    return {"status": "success", "connectors": result}


@app.post("/api/mcp/connect", tags=["MCP Connectors"])
async def connect_connector(
    request: MCPConnectRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Connects/enables an MCP connector for the authenticated user and saves configuration in MongoDB.
    """
    record = await save_connector_config(
        user_id=user.user_id,
        connector_id=request.connector_id,
        enabled=True,
        config=request.config,
        status="connected"
    )
    return {"status": "success", "message": f"Connected to {request.connector_id} successfully.", "connector": record}


@app.post("/api/mcp/disconnect", tags=["MCP Connectors"])
async def disconnect_connector(
    request: MCPDisconnectRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Disconnects/disables an MCP connector for the authenticated user in MongoDB.
    """
    record = await save_connector_config(
        user_id=user.user_id,
        connector_id=request.connector_id,
        enabled=False,
        status="disconnected"
    )
    return {"status": "success", "message": f"Disconnected {request.connector_id}.", "connector": record}


@app.post("/api/mcp/test", tags=["MCP Connectors"])
async def test_connector(
    request: MCPTestRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Tests live connection latency and connectivity for a specified MCP connector.
    """
    cfg = request.config or {}
    if not cfg:
        db_cfg = await get_connector_config(user.user_id, request.connector_id)
        if db_cfg and "config" in db_cfg:
            cfg = db_cfg["config"]

    res = await test_connector_connection(request.connector_id, cfg)
    return res


@app.post("/api/mcp/execute", tags=["MCP Connectors"])
async def execute_tool(
    request: MCPExecuteToolRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Directly invokes an MCP tool across the connected connector.
    """
    db_cfg = await get_connector_config(user.user_id, request.connector_id)
    cfg = db_cfg.get("config", {}) if db_cfg else {}
    res = await run_mcp_connector_tool(request.connector_id, request.tool_name, request.arguments or {}, cfg)
    return {"status": "success", "tool_result": res}


# =====================================================================
# AI STUDY CHATBOT & MCP ASSISTANT ENDPOINT
# =====================================================================

@app.post("/api/chat/study", response_model=StudyChatResponse, tags=["AI Study Chatbot"])
async def study_chat_endpoint(
    request: StudyChatRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    AI Study Chatbot with strict academic/curriculum guardrails,
    real-time multi-connector MCP queries (Wikipedia, ArXiv, NewsAPI),
    and course notes retrieval.
    """
    try:
        response = await process_study_chat(
            user_id=user.user_id,
            message=request.message,
            history=request.history or [],
            document_id=request.document_id
        )
        return response
    except Exception as e:
        logger.error(f"Error in study_chat_endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat generation error: {str(e)}"
        )

