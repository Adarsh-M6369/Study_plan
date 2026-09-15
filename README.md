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

6. **Modern React Vite + Tailwind Frontend**:
   - **Clerk Authentication Gate**: Social sign-in (Google, Facebook, GitHub) via `@clerk/clerk-react`.
   - **Dual-Tab Ingestion Zone**: Drag-and-drop PDF upload (up to 150 pages) and raw text input.
   - **Interactive Study Pack Studio**: Summary notes, responsive glossary table, and 5-step roadmap.
   - **Interactive Quiz Studio**: 20 MCQs with instant feedback, explanations, and score tracking.
   - **Collapsible Conceptual Q&As**: 5 analytical questions with expandable model solutions.
   - **Export Bar**: Triggers for ReportLab PDF and Anki/Quizlet CSV downloads.

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
│       │   ├── parser.py                # pypdf parsing, text cleaner, 150-page strict limit check
│       │   ├── splitter.py              # Equidistant segment & chapter chunking
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
└── frontend/                            # React + Vite + Tailwind CSS Application
    ├── package.json
    ├── vite.config.js
    ├── index.html
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── .env                             # VITE_CLERK_PUBLISHABLE_KEY & VITE_API_URL
    └── src/
        ├── main.jsx                     # ClerkProvider wrapper
        ├── App.jsx                      # Protected routes & main application state
        ├── index.css                    # Tailwind directives
        ├── components/
        │   ├── Navbar.jsx               # Clerk UserButton, Auth triggers, and brand header
        │   ├── IngestionZone.jsx        # Drag-and-drop PDF upload & raw text input tab
        │   ├── DifficultySelector.jsx   # Beginner / Intermediate / Advanced toggle
        │   ├── StudyPackDashboard.jsx   # Markdown summaries, glossary table, and study order
        │   ├── InteractiveQuiz.jsx      # 20 MCQs with instant feedback & explanations
        │   ├── ShortQACard.jsx          # 5 Short Q&As with collapsible model answers
        │   └── ExportBar.jsx            # Triggers for PDF and Anki/Quizlet CSV downloads
        └── services/
            └── api.js                   # Axios client injecting Clerk session token in headers
```

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

### 2. Configure Environment Variables
Edit `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
MONGO_URL=mongodb+srv://...
MONGO_URL_local=mongodb://127.0.0.1:27017
CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
JWT_SECRET_KEY=your_jwt_secret_key
```

### 3. Launch Backend Server
The backend entry point is located at `backend/server.py`:
```bash
python backend/server.py
```
- API Docs & Swagger UI: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

### 4. Launch React Frontend
```bash
cd frontend
npm run dev
```
- Web Application URL: `http://localhost:5173`

