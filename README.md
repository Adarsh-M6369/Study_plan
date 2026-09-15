# 🎓 Study Guide & Exam Prep Generator

An AI-powered **Study Guide & Exam Preparation Generator** that transforms lecture notes, textbooks, and study material into a complete, personalized study pack.

The application uses **Retrieval-Augmented Generation (RAG)**, **LangGraph**, **ChromaDB**, **Model Context Protocol (MCP)**, and large language models to generate structured educational content directly from the user's study material.

It can generate:

* 📚 Summary notes
* 🧠 Key concepts and glossary
* 📝 20 high-yield multiple-choice questions
* ✍️ 5 analytical short-answer questions
* 🗺️ Personalized study roadmap
* 📄 Downloadable PDF study packs
* 🃏 Anki / Quizlet-compatible flashcards

The project consists of a **FastAPI backend** and a **React + Vite + Tailwind CSS frontend**, with **Clerk authentication** and a multi-tenant vector database architecture.

---

## ✨ Why This Project?

Preparing for exams often requires students to manually convert large amounts of lecture material into:

* concise notes,
* important concepts,
* practice questions,
* flashcards,
* and a study schedule.

This process can be time-consuming and inconsistent.

The **Study Guide & Exam Prep Generator** automates this process.

Instead of manually reading a large PDF and creating questions yourself, you can upload your study material and specify your preferred difficulty level.

The system analyzes the material using an AI + RAG pipeline and generates a structured study pack based specifically on the uploaded content.

### Example Workflow

```text
Lecture Notes / PDF
        ↓
PDF Parsing & Cleaning
        ↓
Text Chunking
        ↓
ChromaDB Vector Storage
        ↓
Semantic Retrieval (RAG)
        ↓
LangGraph Reasoning Pipeline
        ↓
LLM Generation
        ↓
Structured Study Pack
        ↓
┌───────────────────────────────┐
│ Summary Notes                 │
│ Glossary                      │
│ 20 MCQs                       │
│ 5 Analytical Q&As             │
│ Study Roadmap                 │
└───────────────────────────────┘
        ↓
PDF / Anki / Quizlet Export
```

---

# 🌟 Key Features

## 1. 📄 Intelligent PDF Processing

The application accepts lecture notes and other educational PDFs.

The PDF parser is implemented using `pypdf` and includes strict validation.

### 150-Page Limit

Uploaded PDFs are limited to **150 pages**.

If a document exceeds the limit, the backend returns an HTTP `400` validation error rather than attempting to process an excessively large document.

### Text Cleaning

The parser also performs text normalization to remove common PDF artifacts such as:

* repeated headers,
* repeated footers,
* unnecessary whitespace,
* broken text layouts,
* formatting artifacts.

This produces cleaner input for downstream RAG processing.

---

# 2. 🧠 Retrieval-Augmented Generation (RAG)

The application uses **Retrieval-Augmented Generation** so that generated educational content is grounded in the user's uploaded material.

Instead of simply asking an LLM a question, the system first retrieves relevant sections from the user's study material.

```text
User Material
     ↓
Text Extraction
     ↓
Chunking
     ↓
Embeddings
     ↓
ChromaDB
     ↓
Relevant Context Retrieval
     ↓
LLM
     ↓
Educational Content
```

This helps the generated questions, explanations, and summaries remain relevant to the source material.

---

# 3. 🗄️ Multi-Tenant ChromaDB Vector Store

The project uses **ChromaDB** as its vector database.

Each user's documents are isolated using metadata filtering based on:

```text
user_id
```

This means retrieval is performed only against the documents belonging to the authenticated user.

Conceptually:

```text
User A
 ├── Lecture 1
 ├── Lecture 2
 └── Lecture 3

User B
 ├── Lecture 1
 └── Lecture 2
```

When User A performs a query, the vector search is restricted to User A's documents.

### Resilient Retrieval

The vector store includes:

* semantic similarity search,
* retry logic using Tenacity,
* lexical/keyword fallback,
* handling for zero-result semantic searches.

If semantic retrieval fails, the application can fall back to keyword-based retrieval rather than immediately failing the entire generation pipeline.

---

# 4. 🔄 LangGraph Agent Pipeline

The core AI workflow is implemented using **LangGraph**.

The application represents the generation process as a stateful graph.

The state tracks information such as:

```text
messages
user_id
difficulty
context
structured_output
next_step
```

The graph controls the flow between different processing stages.

A simplified version of the pipeline is:

```text
                ┌──────────────┐
                │ User Input   │
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │  Ingestion   │
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │ RAG Retrieval│
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │  Reasoning   │
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │ MCP Tools    │
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │  Synthesis   │
                └──────┬───────┘
                       ↓
                ┌──────────────┐
                │ Study Pack   │
                └──────────────┘
```

This architecture makes the AI workflow easier to extend and maintain.

---

# 5. 🎯 Difficulty-Based Question Generation

The user can choose between three difficulty levels.

### 🟢 Beginner

Designed for foundational understanding.

Questions focus on:

* direct recall,
* definitions,
* basic concepts,
* intuitive analogies.

### 🟡 Intermediate

Designed for students who understand the fundamentals.

Questions focus on:

* application,
* conceptual relationships,
* synthesis,
* interpretation.

### 🔴 Advanced

Designed for deeper exam preparation.

Questions focus on:

* edge cases,
* complex mechanisms,
* subtle distinctions,
* challenging distractors,
* higher-order reasoning.

This allows the same study material to generate different levels of examination difficulty.

---

# 6. 🤖 LLM Failover

The application uses **Google Gemini as the primary LLM** and **Groq as a fallback provider**.

The LangChain fallback mechanism allows the application to switch providers when the primary model encounters a failure.

Conceptually:

```text
             Request
                ↓
         ┌──────────────┐
         │ Gemini Model │
         └──────┬───────┘
                │
          Failure?
          /     \
        No       Yes
        ↓         ↓
    Response   Groq Fallback
                  ↓
               Response
```

This improves reliability and prevents a temporary model/provider failure from stopping the entire workflow.

---

# 7. 🔌 Model Context Protocol (MCP)

The project integrates **Model Context Protocol (MCP)** through an asynchronous stdio client.

MCP provides a standardized mechanism for connecting the AI workflow with external tools and capabilities.

The MCP client includes retry behavior with exponential backoff to improve reliability when communicating with MCP services.

---

# 8. 📚 Structured Educational Output

The system generates a complete study pack rather than returning an unstructured AI response.

## 📝 20 Multiple Choice Questions

Each generated MCQ contains:

* Question
* Four options
* Correct answer
* Detailed explanation

Example structure:

```text
Question:
What is the primary purpose of...

A. ...
B. ...
C. ...
D. ...

Correct Answer: B

Explanation:
...
```

---

## ✍️ 5 Analytical Short Questions

The system generates five conceptual questions with:

* question prompt,
* model answer,
* important scoring points.

These questions are designed to encourage deeper understanding rather than simple memorization.

---

## 📖 Summary Notes

The application synthesizes the retrieved educational material into clean Markdown notes.

The summary focuses on:

* important concepts,
* relationships,
* definitions,
* exam-relevant information.

---

## 📚 Key Terms Glossary

Important terminology is extracted and presented with academic definitions.

The frontend displays the glossary in a responsive table.

---

## 🗺️ Study Roadmap

The generator creates a suggested sequence for studying the material.

The roadmap includes:

* study order,
* topics,
* recommended time,
* progression through the material.

Example:

```text
Step 1 → Understand Fundamentals
         ↓
Step 2 → Review Important Concepts
         ↓
Step 3 → Practice MCQs
         ↓
Step 4 → Attempt Analytical Questions
         ↓
Step 5 → Final Revision
```

---

# 9. 📄 PDF Export

The project uses **ReportLab** to generate a downloadable study pack.

The generated PDF can contain:

* study roadmap,
* summary notes,
* glossary,
* MCQs,
* answer key,
* analytical questions.

The PDF engine creates a multi-page formatted document suitable for offline studying or printing.

---

# 10. 🃏 Anki / Quizlet Export

The application also provides CSV export functionality for spaced repetition.

The exporter produces a two-column format:

```text
Question,Answer
"What is ...?","The answer is ..."
```

The generated CSV can be imported into compatible flashcard applications such as Anki or Quizlet.

---

# 11. 🔐 Authentication

The application uses **Clerk** for authentication.

Users can authenticate using supported social login providers such as:

* Google
* Facebook
* GitHub

The frontend uses:

```text
@clerk/clerk-react
```

The backend verifies authentication tokens before processing protected requests.

Authentication is important because the vector database uses the authenticated user's `user_id` to maintain tenant-level data isolation.

---

# 12. 💻 Modern React Frontend

The frontend is built using:

* React
* Vite
* Tailwind CSS
* Axios
* Clerk

The interface is divided into reusable components.

### Main UI Areas

#### Ingestion Zone

Allows users to:

* drag and drop a PDF,
* upload lecture notes,
* enter raw text,
* select their input method.

#### Difficulty Selector

Allows the user to choose:

```text
Beginner
Intermediate
Advanced
```

#### Study Pack Dashboard

Displays:

* summary,
* glossary,
* study roadmap.

#### Interactive Quiz

Displays the generated MCQs with:

* answer selection,
* instant feedback,
* explanations,
* score tracking.

#### Short Q&A

Provides expandable analytical questions and model answers.

#### Export Bar

Provides download options for:

* PDF study pack,
* Anki/Quizlet CSV.

---

# 🏗️ System Architecture

```text
                         ┌─────────────────────┐
                         │      React UI       │
                         │  Vite + Tailwind    │
                         └──────────┬──────────┘
                                    │
                              Axios / API
                                    │
                                    ↓
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │       Backend       │
                         └──────────┬──────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               ↓                    ↓                    ↓
        ┌─────────────┐      ┌──────────────┐     ┌────────────┐
        │   Clerk     │      │  LangGraph   │     │  MongoDB   │
        │    Auth     │      │   Workflow   │     │  Database  │
        └─────────────┘      └──────┬───────┘     └────────────┘
                                    │
                         ┌──────────┴──────────┐
                         ↓                     ↓
                  ┌──────────────┐      ┌─────────────┐
                  │   ChromaDB   │      │ MCP Client  │
                  │     RAG      │      │    Tools    │
                  └──────┬───────┘      └─────────────┘
                         │
                         ↓
                 ┌───────────────┐
                 │  Gemini LLM   │
                 │       ↓       │
                 │ Groq Fallback │
                 └───────────────┘
                         │
                         ↓
                  Structured Output
                         │
             ┌───────────┴───────────┐
             ↓                       ↓
       ┌─────────────┐        ┌─────────────┐
       │ ReportLab   │        │ CSV Export  │
       │ PDF Export  │        │ Anki/Quizlet │
       └─────────────┘        └─────────────┘
```

---

# 📁 Repository Structure

```text
study-guide-generator/
│
├── .env
├── requirements.txt
├── README.md
│
├── backend/
│   ├── server.py
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       │
│       ├── auth/
│       │   ├── __init__.py
│       │   └── clerk.py
│       │
│       ├── db/
│       │   ├── __init__.py
│       │   └── mongo.py
│       │
│       ├── graph/
│       │   ├── __init__.py
│       │   ├── state.py
│       │   ├── nodes.py
│       │   ├── router.py
│       │   └── workflow.py
│       │
│       ├── rag/
│       │   ├── __init__.py
│       │   ├── parser.py
│       │   ├── splitter.py
│       │   └── store.py
│       │
│       ├── mcp/
│       │   ├── __init__.py
│       │   └── client.py
│       │
│       ├── exports/
│       │   ├── __init__.py
│       │   ├── pdf_engine.py
│       │   └── csv_engine.py
│       │
│       └── schemas/
│           ├── __init__.py
│           ├── request.py
│           └── study_pack.py
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── .env
    │
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css
        │
        ├── components/
        │   ├── Navbar.jsx
        │   ├── IngestionZone.jsx
        │   ├── DifficultySelector.jsx
        │   ├── StudyPackDashboard.jsx
        │   ├── InteractiveQuiz.jsx
        │   ├── ShortQACard.jsx
        │   └── ExportBar.jsx
        │
        └── services/
            └── api.js
```

---

# 🛠️ Technology Stack

| Technology        | Purpose                         |
| ----------------- | ------------------------------- |
| **React**         | Frontend UI                     |
| **Vite**          | Frontend development/build tool |
| **Tailwind CSS**  | Styling                         |
| **FastAPI**       | Backend REST API                |
| **Python**        | Backend implementation          |
| **LangGraph**     | Stateful AI workflow            |
| **ChromaDB**      | Vector database / RAG           |
| **pypdf**         | PDF parsing                     |
| **MongoDB**       | Application data storage        |
| **Clerk**         | Authentication                  |
| **Google Gemini** | Primary LLM                     |
| **Groq**          | LLM fallback                    |
| **MCP**           | Tool integration                |
| **Tenacity**      | Retry mechanisms                |
| **ReportLab**     | PDF generation                  |
| **Axios**         | Frontend API communication      |

---

# 🚀 Installation & Setup

Follow these steps to run the project locally.

## Prerequisites

Make sure the following are installed:

* Python 3.10+
* Node.js 18+
* npm
* Git
* MongoDB or a MongoDB Atlas account

You will also need API credentials for:

* Google Gemini
* Groq
* Clerk
* MongoDB

---

# 1️⃣ Clone the Repository

```bash
git clone https://github.com/Adarsh-M6369/Study_plan.git
```

Move into the project directory:

```bash
cd Study_plan
```

---

# 2️⃣ Create a Python Virtual Environment

It is recommended to use a virtual environment for the backend.

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

After activation, your terminal should show something similar to:

```text
(venv)
```

---

# 3️⃣ Install Backend Dependencies

From the project root:

```bash
pip install -r requirements.txt
```

If you are using a newer Python installation and `pip` is not available through the `python` command, use:

```bash
python -m pip install -r requirements.txt
```

---

# 4️⃣ Configure Backend Environment Variables

Create a `.env` file in the project root.

Example:

```env
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key

MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/
MONGO_URL_local=mongodb://127.0.0.1:27017

CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
JWT_SECRET_KEY=your_jwt_secret_key
```

### Important

Do not commit your `.env` file to GitHub.

Add it to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
node_modules/
```

---

# 5️⃣ Configure Clerk

Create a Clerk application and configure the authentication providers you want to use.

You will need the appropriate Clerk publishable key for the frontend and the JWT configuration required by the backend.

The frontend environment file should contain:

```env
VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
VITE_API_URL=http://127.0.0.1:8000
```

Create this file inside:

```text
frontend/.env
```

---

# 6️⃣ Start the Backend

From the project root:

```bash
python backend/server.py
```

The FastAPI backend should start on:

```text
http://127.0.0.1:8000
```

### API Documentation

FastAPI automatically provides Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

You can use this page to inspect and test the available API endpoints.

### Health Check

The application also provides:

```text
http://127.0.0.1:8000/health
```

A successful response confirms that the backend is running.

---

# 7️⃣ Install Frontend Dependencies

Open a **new terminal**.

Navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

---

# 8️⃣ Configure Frontend Environment Variables

Inside the `frontend` directory, create:

```text
.env
```

Add:

```env
VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
VITE_API_URL=http://127.0.0.1:8000
```

Make sure the API URL points to the FastAPI server.

---

# 9️⃣ Start the React Frontend

From the `frontend` directory:

```bash
npm run dev
```

Vite will provide a local development URL, normally:

```text
http://localhost:5173
```

Open that URL in your browser.

---

# 🔄 Running the Complete Application

You need **two terminals** running simultaneously.

### Terminal 1 — Backend

```bash
cd Study_plan
python backend/server.py
```

Backend:

```text
http://127.0.0.1:8000
```

### Terminal 2 — Frontend

```bash
cd Study_plan/frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

Then open the frontend URL in your browser.

---

# 🧪 How to Use the Application

## Step 1 — Sign In

Authenticate using the configured Clerk login provider.

---

## Step 2 — Upload Study Material

Use the ingestion section to either:

* upload a PDF,
* or enter raw study text.

PDF documents must not exceed **150 pages**.

---

## Step 3 — Select Difficulty

Choose:

```text
Beginner
Intermediate
Advanced
```

This controls the complexity of the generated questions and explanations.

---

## Step 4 — Generate the Study Pack

The backend processes the material through the RAG + LangGraph pipeline.

The application then generates:

```text
✓ Summary
✓ Glossary
✓ Study Roadmap
✓ 20 MCQs
✓ 5 Analytical Q&As
```

---

## Step 5 — Practice

Use the interactive quiz interface to answer the generated MCQs.

The application provides:

* immediate feedback,
* correct answers,
* explanations,
* score tracking.

---

## Step 6 — Export

Download the generated study material as:

### PDF

A complete formatted study pack generated using ReportLab.

### CSV

A flashcard-compatible CSV suitable for Anki/Quizlet workflows.

---

# 🔒 Security & Data Isolation

The application is designed with authenticated, multi-user usage in mind.

User identity is obtained through Clerk authentication.

The authenticated `user_id` is used when interacting with the vector store so that retrieval is scoped to the appropriate user's data.

Conceptually:

```text
Authenticated User
       ↓
    user_id
       ↓
ChromaDB Metadata Filter
       ↓
Only matching documents
       ↓
RAG Context
       ↓
AI Generation
```

This prevents the retrieval pipeline from intentionally mixing documents belonging to different users.

---

# 🧩 Backend Modules

## `app/main.py`

Main FastAPI application.

Responsible for:

* application initialization,
* CORS,
* API routers,
* exception handling.

---

## `app/config.py`

Central configuration management.

Reads configuration values from environment variables.

---

## `app/auth/clerk.py`

Handles Clerk JWT verification and authentication-related functionality.

---

## `app/db/mongo.py`

Handles MongoDB connectivity using Motor/PyMongo.

---

## `app/rag/parser.py`

Responsible for:

* PDF parsing,
* page validation,
* text extraction,
* text cleaning.

---

## `app/rag/splitter.py`

Splits extracted documents into manageable chunks for vector retrieval.

---

## `app/rag/store.py`

Handles:

* ChromaDB,
* embeddings/vector search,
* metadata filtering,
* retry logic,
* lexical fallback.

---

## `app/graph/`

Contains the LangGraph workflow.

### `state.py`

Defines the state shared between graph nodes.

### `nodes.py`

Contains processing nodes for ingestion, retrieval, reasoning, MCP integration, and synthesis.

### `router.py`

Controls conditional routing between graph nodes.

### `workflow.py`

Builds and compiles the complete LangGraph StateGraph.

---

## `app/mcp/client.py`

Implements the asynchronous MCP client connection and retry behavior.

---

## `app/exports/`

Contains the export engines.

### `pdf_engine.py`

Generates the final study pack PDF.

### `csv_engine.py`

Generates Anki/Quizlet-compatible CSV files.

---

# 🎨 Frontend Components

## `Navbar.jsx`

Application navigation and Clerk user controls.

## `IngestionZone.jsx`

PDF upload and raw-text ingestion interface.

## `DifficultySelector.jsx`

Beginner / Intermediate / Advanced selection.

## `StudyPackDashboard.jsx`

Displays generated study content.

## `InteractiveQuiz.jsx`

Interactive MCQ interface with score tracking.

## `ShortQACard.jsx`

Expandable analytical question and answer cards.

## `ExportBar.jsx`

PDF and CSV export controls.

---

# 📊 Complete Data Flow

The complete application flow can be summarized as:

```text
                 USER
                  │
                  ↓
            Clerk Login
                  │
                  ↓
        Upload PDF / Text
                  │
                  ↓
        FastAPI Backend
                  │
                  ↓
       PDF Parsing & Cleaning
                  │
                  ↓
           Text Chunking
                  │
                  ↓
        ChromaDB Vector Store
                  │
                  ↓
        Semantic Retrieval
                  │
                  ↓
        LangGraph Workflow
                  │
        ┌─────────┴─────────┐
        ↓                   ↓
   MCP Tools            LLM Provider
                            │
                    ┌───────┴───────┐
                    ↓               ↓
                 Gemini           Groq
                 Primary         Fallback
                    │               │
                    └───────┬───────┘
                            ↓
                    Structured Output
                            │
          ┌─────────────────┼─────────────────┐
          ↓                 ↓                 ↓
       Summary          Questions         Roadmap
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ↓
                     Study Pack UI
                            │
                    ┌───────┴────────┐
                    ↓                ↓
                  PDF              CSV
                ReportLab       Anki/Quizlet
```

---

# 🚧 Future Improvements

Potential future improvements include:

* 📈 Student progress analytics
* 🧠 Adaptive question difficulty
* 📅 Calendar-based study scheduling
* 🔔 Study reminders
* 📊 Performance dashboards
* 📚 Multiple document collections
* 🔎 Improved hybrid search
* 🎙️ AI-generated audio summaries
* 💬 Conversational AI tutor
* 🧪 More question types
* 🏆 Gamification and achievement system
* ☁️ Cloud deployment
* 👥 Collaborative study groups

---

# 📌 Project Highlights

This project demonstrates practical implementation of several modern AI engineering concepts:

* **RAG-based AI applications**
* **Vector databases**
* **Multi-tenant retrieval**
* **Stateful LLM workflows**
* **LLM provider fallback**
* **MCP tool integration**
* **Structured AI outputs**
* **Authentication**
* **REST API development**
* **React frontend development**
* **PDF generation**
* **Spaced-repetition export**

It combines these technologies into a complete end-to-end AI educational application rather than a simple LLM chatbot.

---

# 📜 License

Add your preferred license here.

For example:

```text
MIT License
```

---

# 👨‍💻 Author

**Adarsh M**

GitHub:

https://github.com/Adarsh-M6369

---

# ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

Feedback, suggestions, and contributions are welcome.
