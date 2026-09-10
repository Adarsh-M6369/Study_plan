import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from app.config import settings
from app.auth.clerk import get_current_user, AuthenticatedUser
from app.db.mongo import init_mongo_connection, save_study_pack, save_document_metadata, get_study_packs_by_user
from app.rag.parser import parse_pdf_bytes, clean_text
from app.rag.splitter import split_text_into_chunks
from app.rag.store import get_vector_store
from app.graph.workflow import run_study_pack_pipeline
from app.exports.pdf_engine import generate_study_pack_pdf
from app.exports.csv_engine import generate_anki_csv
from app.schemas.request import IngestTextRequest, GenerateRequest, UploadResponse
from app.schemas.study_pack import StudyPack, MCQItem

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
    settings.FRONTEND_URL,
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
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
    logger.info("Initializing Study Guide Generator backend...")
    await init_mongo_connection()
    get_vector_store()
    logger.info("Backend services initialized successfully.")


@app.get("/health", tags=["Health"])
async def health_check():
    """Returns the health status of all core backend services."""
    return {
        "status": "healthy",
        "service": "Study Guide Generator API",
        "version": "1.0.0",
        "gemini_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here"),
        "groq_configured": bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your_groq_api_key_here"),
        "mongo_configured": bool(settings.MONGO_URL or settings.MONGO_URL_local)
    }


@app.post("/api/upload", response_model=UploadResponse, tags=["RAG Ingestion"])
async def upload_document(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Uploads and parses a PDF (enforcing strict 15-page limit) or raw lecture text,
    splits into semantic chunks, and indexes into the user's multi-tenant ChromaDB store.
    """
    user_id = user.user_id
    doc_title = title or (file.filename if file else "Pasted Lecture Notes")
    doc_id = f"doc_{abs(hash(doc_title + user_id)) % 1000000}"

    pages_data = []
    page_count = 1

    if file:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported for file upload. Use raw_text for other notes."
            )
        pdf_bytes = await file.read()
        full_text, pages_data, page_count = parse_pdf_bytes(pdf_bytes, filename=file.filename)
    elif raw_text and raw_text.strip():
        cleaned = clean_text(raw_text)
        if not cleaned:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provided text is empty.")
        pages_data = [{"page_number": 1, "text": cleaned, "source": doc_title}]
        page_count = 1
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide either a PDF file or raw_text to ingest."
        )

    # Chunk the text with 150-page optimization
    chunks = split_text_into_chunks(pages_data, chunk_size=1500, chunk_overlap=200)

    # Index into ChromaDB
    store = get_vector_store()
    chunk_count = store.add_documents(user_id=user_id, document_id=doc_id, chunks=chunks)

    # Record metadata
    doc_metadata = {
        "document_id": doc_id,
        "title": doc_title,
        "page_count": page_count,
        "chunk_count": chunk_count,
        "source_type": "pdf" if file else "raw_text"
    }
    await save_document_metadata(user_id=user_id, doc_metadata=doc_metadata)

    return UploadResponse(
        status="success",
        document_id=doc_id,
        title=doc_title,
        page_count=page_count,
        chunk_count=chunk_count,
        message=f"Successfully parsed {page_count} pages and indexed {chunk_count} chunks for user."
    )


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
        difficulty=request.difficulty,
        topic=request.topic,
        custom_instructions=request.custom_instructions
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate study pack. Please check that material is uploaded and try again."
        )

    # Persist in MongoDB / fallback
    await save_study_pack(user_id=user_id, study_pack_data=result)

    return result


@app.get("/api/history", tags=["Study Pack History"])
async def get_history(user: AuthenticatedUser = Depends(get_current_user)):
    """Retrieves previously generated study packs for the authenticated user."""
    packs = await get_study_packs_by_user(user.user_id)
    return {"status": "success", "study_packs": packs}


@app.post("/api/export/pdf", tags=["Exports"])
async def export_pdf(pack: StudyPack):
    """
    Accepts the study pack JSON and streams a downloadable multi-page .pdf generated via ReportLab.
    """
    try:
        pdf_stream = generate_study_pack_pdf(pack.model_dump())
        filename = f"{pack.title.replace(' ', '_')[:30]}_Study_Pack.pdf"
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error compiling ReportLab PDF: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF compilation error: {str(e)}")


@app.post("/api/export/csv", tags=["Exports"])
async def export_csv(mcqs: List[MCQItem]):
    """
    Accepts the MCQs array and streams a downloadable 2-column HTML-formatted .csv for Anki / Quizlet.
    """
    try:
        csv_data = generate_anki_csv([m.model_dump() for m in mcqs])
        csv_bytes = csv_data.encode("utf-8")
        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=Anki_Quizlet_Flashcards.csv"}
        )
    except Exception as e:
        logger.error(f"Error generating flashcards CSV: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"CSV export error: {str(e)}")
