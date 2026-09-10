# 🎓 Study Guide & Exam Prep Generator

A full-stack, enterprise-grade AI study companion built with **FastAPI**, **LangGraph**, **ChromaDB RAG**, **Model Context Protocol (MCP)**, **ReportLab**, and **Streamlit**.

---

## 🌟 Key Features

1. **Strict 150-Page PDF Parser & Text Cleaner**:
   - Parses lecture notes via `pypdf` with strict 150-page boundary enforcement (HTTP 400 validation if `> 150` pages).
   - Strips header/footer artifacts and normalizes text layout.

2. **Resilient Multi-Tenant Vector Store (ChromaDB)**:
   - Multi-tenant data isolation using `user_id` metadata filtering.
   - Vector store lookup with Tenacity retries (`stop=2`, `wait=1s`).
   - Keyword/lexical fallback retrieval if semantic similarity search fails or returns zero matches.

3. **LangGraph StateGraph Pipeline**:
   - **State**: Tracks `messages`, `user_id`, `difficulty`, `context`, `structured_output`, and `next_step`.
   - **Difficulty Tuning**:
     - *Beginner*: Direct recall & intuitive analogies.
     - *Intermediate*: Application & conceptual synthesis.
     - *Advanced*: Edge cases, intricate mechanics & challenging distractors.
   - **MCP Tool Integration**: Asynchronous stdio MCP client with exponential backoff retries.
   - **LLM Failover**: Primary Google Gemini with Groq fallback using `.with_fallbacks()`.

4. **Structured Educational Outputs**:
   - **20 High-Yield MCQs** with 4 choices (A, B, C, D), correct answers, and thorough explanations.
   - **5 Analytical Short Q&As** with full model answers and key scoring points.
   - **Synthesized Summary Notes** in clean Markdown.
   - **Key Terms Glossary** with academic definitions.
   - **Suggested Study Roadmap** sequence with time estimates.

5. **Exporters**:
   - **ReportLab PDF Engine**: Multi-page styled study pack PDF with roadmap timeline, 2-column glossary table, notes, and 20 MCQs with answer keys.
   - **Anki / Quizlet CSV Exporter**: 2-column HTML-formatted CSV ready for spaced repetition import.

6. **Interactive Streamlit Frontend (5 Tabs)**:
   - **Tab 1: Ingest Notes** (PDF with page verification + raw text paste).
   - **Tab 2: Configure & Generate** (Difficulty selection & LangGraph trigger).
   - **Tab 3: Study Pack View** (Roadmap, summary notes, glossary, 5 Q&As).
   - **Tab 4: Interactive Quiz** (20 MCQs with instant feedback mode & live scoring).
   - **Tab 5: Export Center** (Side-by-side downloads for PDF & Anki CSV).

---

## 📁 Repository Structure

```
study-guide-generator/
├── .env
├── requirements.txt
├── README.md
│
├── backend/
│   ├── server.py                        # Uvicorn entry point (runs app.main:app with reload=True)
│   └── app/
│       ├── __init__.py
│       ├── main.py                      # FastAPI application, CORS, routers & exception handlers
│       ├── config.py                    # Exact settings specification with dotenv and os.getenv
│       │
│       ├── auth/
│       │   ├── __init__.py
│       │   └── clerk.py                 # JWT token verification using JWT_SECRET_KEY / Clerk setup
│       │
│       ├── db/
│       │   ├── __init__.py
│       │   └── mongo.py                 # Motor / PyMongo connection using MONGO_URL / MONGO_URL_local
│       │
│       ├── graph/
│       │   ├── __init__.py
│       │   ├── state.py                 # TypedDict AgentState definition
│       │   ├── nodes.py                 # Ingestion, RAG, reasoning, MCP tools, synthesis
│       │   ├── router.py                # LangGraph conditional edge routing
│       │   └── workflow.py              # Compiled StateGraph pipeline
│       │
│       ├── rag/
│       │   ├── __init__.py
│       │   ├── parser.py                # pypdf parsing, text cleaner, 15-page strict limit check
│       │   ├── splitter.py              # Semantic / Recursive character text chunking
│       │   └── store.py                 # Resilient Chroma / Vector search with retry & fallback
│       │
│       ├── mcp/
│       │   ├── __init__.py
│       │   └── client.py                # MCP stdio client connector with Tenacity retries
│       │
│       ├── exports/
│       │   ├── __init__.py
│       │   ├── pdf_engine.py            # ReportLab multi-page study pack PDF compiler
│       │   └── csv_engine.py            # Anki / Quizlet 2-column HTML-formatted CSV exporter
│       │
│       └── schemas/
│           ├── __init__.py
│           ├── request.py               # Ingestion & query request Pydantic models
│           └── study_pack.py            # Schema for 20 MCQs, 5 Q&As, summary, glossary, roadmap
│
└── frontend/
    ├── app.py                           # Main Streamlit dashboard (tabs, quiz UI, controls)
    ├── auth.py                          # Clerk OAuth session handling & token storage
    ├── components/
    │   ├── upload_tab.py                # PDF upload widget and raw text fallbacks
    │   ├── study_pack_view.py           # Summaries, key terms glossary, and study sequence
    │   ├── quiz_view.py                 # Interactive MCQ practice cards with instant validation
    │   └── download_buttons.py          # Streamlit triggers for ReportLab PDF & Anki CSV
    └── utils/
        └── api_client.py                # HTTP client connecting to http://127.0.0.1:8000
```

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Edit `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
MONGO_URL=mongodb+srv://...
MONGO_URL_local=mongodb://127.0.0.1:27017
JWT_SECRET_KEY=dev_jwt_secret_key_change_in_production
```

### 3. Launch Backend Server
The backend entry point is located at `backend/server.py`:
```bash
python backend/server.py
```
- API Docs & Swagger UI: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

### 4. Launch Streamlit Frontend
```bash
streamlit run frontend/app.py
```
- Dashboard URL: `http://localhost:8501`
