import re
import logging
from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.schemas.chat import ChatMessage, StudyChatResponse
from app.graph.nodes import get_llm_with_fallback, clean_topic_title
from app.rag.store import get_vector_store
from app.db.mongo import get_user_connectors, get_chunks_by_document
from app.mcp.registry import run_mcp_connector_tool

logger = logging.getLogger("chat.study_bot")

NON_ACADEMIC_PATTERNS = [
    r"(?i)\b(celebrity|gossip|hollywood|bollywood|actor|actress|video game|gaming|fortnite|gta|roblox|minecraft|pubg|valorant|fifa|esports)\b",
    r"(?i)\b(cricket|football|soccer|baseball|basketball|nfl|nba|ipl|fifa world cup|match score|who won the match|sports betting|gambling|casino|lottery)\b",
    r"(?i)\b(dating advice|romance|tinder|horoscope|zodiac|astrology|fortune telling|tarot)\b",
    r"(?i)\b(dirty joke|vulgar|offensive|curse word|insult|profanity)\b",
    r"(?i)\b(hack a website|crack password|ddos|malware|ransomware|pirate software|bypass paywall|jailbreak)\b",
    r"(?i)\b(election gossip|who should i vote for|political scandal|partisan politics)\b"
]

ACADEMIC_KEYWORDS = [
    "explain", "define", "solve", "formula", "theorem", "proof", "derivation", "mechanism",
    "summary", "chapter", "lesson", "notes", "exam", "quiz", "mcq", "question", "concept", "principle",
    "algorithm", "science", "math", "mathematics", "physics", "chemistry", "biology", "history", "geography",
    "english", "grammar", "literature", "poem", "prose", "analysis", "compare", "contrast", "differentiate",
    "derive", "calculate", "study", "syllabus", "lecture", "definition", "term", "glossary", "research", "paper",
    "arxiv", "wikipedia", "theory", "function", "diagram", "process", "experiment", "evidence", "hypothesis",
    "thermodynamics", "quantum", "cellular", "photosynthesis", "genetics", "calculus", "algebra", "geometry",
    "statistics", "probability", "electromagnetism", "optics", "kinematics", "dynamics", "economics", "sociology"
]


def is_academic_query(message: str) -> bool:
    """
    Checks if a user query is academic / educational in nature.
    Strictly filters out non-study, casual entertainment, or malicious queries.
    """
    clean_msg = message.strip().lower()
    if len(clean_msg) < 2:
        return False

    # 1. First, check strictly prohibited non-academic domains
    for pattern in NON_ACADEMIC_PATTERNS:
        if re.search(pattern, clean_msg):
            return False

    # 2. Check explicit academic keywords
    for kw in ACADEMIC_KEYWORDS:
        if kw in clean_msg:
            return True

    # 3. Check question structure for educational questions
    if any(clean_msg.startswith(q) for q in ["what is", "what are", "why does", "why is", "how does", "how to solve", "can you explain", "tell me about"]):
        return True

    # 4. If message is at least 3 words and doesn't match banned topics, treat as inquiry
    if len(clean_msg.split()) >= 3:
        return True

    return False


async def query_all_mcp_connectors(query: str, user_id: str) -> List[Dict[str, Any]]:
    """
    Queries active Model Context Protocol (MCP) connectors for real-time academic sources,
    including Wikipedia encyclopedic summaries, ArXiv research papers, and NewsAPI scientific feeds.
    """
    sources = []
    user_connectors = await get_user_connectors(user_id)
    active_connector_ids = {c["connector_id"]: c.get("config", {}) for c in user_connectors if c.get("enabled", False)}

    # Always query Wikipedia MCP for concept definitions if query has substantial terms
    try:
        wiki_res = await run_mcp_connector_tool("wikipedia_connector", "search_wikipedia", {"query": query}, active_connector_ids.get("wikipedia_connector", {}))
        if wiki_res.get("summary"):
            sources.append({
                "type": "Wikipedia MCP",
                "title": wiki_res.get("title", "Wikipedia Article"),
                "snippet": wiki_res.get("summary"),
                "url": wiki_res.get("url", "")
            })
    except Exception as e:
        logger.warning(f"Wikipedia MCP query failed: {e}")

    # Query ArXiv MCP if query mentions science/tech/math/research or arxiv is enabled
    is_stem = any(w in query.lower() for w in ["physics", "quantum", "algorithm", "neural", "math", "model", "paper", "research", "arxiv", "theorem", "system", "computing"])
    if "arxiv_connector" in active_connector_ids or is_stem:
        try:
            arxiv_res = await run_mcp_connector_tool("arxiv_connector", "search_arxiv_papers", {"query": query, "max_results": 2}, active_connector_ids.get("arxiv_connector", {}))
            papers = arxiv_res.get("papers", [])
            for p in papers[:2]:
                sources.append({
                    "type": "ArXiv Research MCP",
                    "title": p.get("title", "ArXiv Paper"),
                    "snippet": p.get("summary", ""),
                    "url": "https://arxiv.org"
                })
        except Exception as e:
            logger.warning(f"ArXiv MCP query failed: {e}")

    # Query NewsAPI MCP if news_connector is enabled or query asks for recent developments
    if "news_connector" in active_connector_ids or any(w in query.lower() for w in ["news", "discovery", "recent", "current", "breakthrough"]):
        try:
            news_res = await run_mcp_connector_tool("news_connector", "get_latest_news", {"query": query}, active_connector_ids.get("news_connector", {}))
            articles = news_res.get("articles", [])
            for a in articles[:2]:
                sources.append({
                    "type": "NewsAPI MCP",
                    "title": a.get("title", "Academic News"),
                    "snippet": a.get("description", ""),
                    "url": a.get("url", "")
                })
        except Exception as e:
            logger.warning(f"NewsAPI MCP query failed: {e}")

    return sources


async def query_user_documents(query: str, user_id: str, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Searches ChromaDB vector store and MongoDB chunks for the user's uploaded lecture notes.
    """
    doc_sources = []
    try:
        store = get_vector_store()
        chunks = store.search(user_id=user_id, query_text=query, n_results=4)
        for c in chunks:
            doc_sources.append({
                "type": "Uploaded Course Notes",
                "title": f"Page {c.get('metadata', {}).get('page_number', 'N/A')} ({c.get('metadata', {}).get('chapter_title', 'Lecture Chunk')})",
                "snippet": c.get("text", "")[:350] + "..."
            })
    except Exception as e:
        logger.warning(f"Vector search failed: {e}")

    return doc_sources


async def process_study_chat(
    user_id: str,
    message: str,
    history: Optional[List[ChatMessage]] = None,
    document_id: Optional[str] = None
) -> StudyChatResponse:
    """
    Processes student chat inquiries with strict academic guardrails,
    real-time MCP tools retrieval (Wikipedia, ArXiv, NewsAPI), and LLM Socratic tutoring.
    """
    history = history or []

    # 1. Guardrail Check: Strict academic/study enforcement
    if not is_academic_query(message):
        rejection_reply = (
            "### 🛡️ Study Guide AI &bull; Academic Guardrail\n\n"
            "I am your dedicated **AI Academic Study Tutor & Curriculum Assistant**.\n\n"
            "I can only assist with **educational, scientific, curriculum, research, exam preparation, and study guide questions**.\n\n"
            "**Here are a few things you can ask me:**\n"
            "- *\"Explain the key mechanisms of Cellular Respiration / Quantum Entanglement\"*\n"
            "- *\"Summarize Chapter 3 of my uploaded lecture notes\"*\n"
            "- *\"What are the core differences between TCP and UDP with examples?\"*\n"
            "- *\"Search ArXiv research papers on Transformer Architectures\"*\n"
            "- *\"Generate 3 practice conceptual questions on Thermodynamics\"*\n\n"
            "Please ask an academic or course-related question to continue!"
        )
        return StudyChatResponse(
            reply=rejection_reply,
            sources=[],
            is_study_question=False
        )

    # 2. Retrieve live MCP sources and Document Context
    mcp_sources = await query_all_mcp_connectors(query=message, user_id=user_id)
    doc_sources = await query_user_documents(query=message, user_id=user_id, document_id=document_id)
    all_sources = mcp_sources + doc_sources

    # 3. Format Context for LLM
    context_blocks = []
    if doc_sources:
        context_blocks.append("--- UPLOADED LECTURE NOTES & CHUNKS ---")
        for s in doc_sources:
            context_blocks.append(f"[{s['title']}]: {s['snippet']}")

    if mcp_sources:
        context_blocks.append("--- LIVE MCP CONNECTORS (WIKIPEDIA / ARXIV / NEWSAPI) ---")
        for s in mcp_sources:
            context_blocks.append(f"[{s['type']} - {s['title']}]: {s['snippet']}")

    combined_context = "\n\n".join(context_blocks) if context_blocks else "No external notes found for this topic."

    # 4. Construct Socratic Academic Prompt
    system_prompt = (
        "You are the elite AI Academic Study Tutor & Curriculum Specialist in the StudyGuide AI platform.\n"
        "Your mission is to provide rigorous, clear, pedagogically structured, and engaging educational explanations.\n\n"
        "GUIDELINES:\n"
        "1. Strictly answer the student's academic or study question with clear headings, bullet points, intuitive analogies, formulas, and step-by-step logic.\n"
        "2. Ground your explanations in the provided Live MCP Tools (Wikipedia, ArXiv, NewsAPI) and Uploaded Course Notes when available.\n"
        "3. Explicitly mention references to sources when quoting facts (e.g. `[Wikipedia MCP]`, `[ArXiv Research]`, `[Lecture Notes]`).\n"
        "4. If relevant, include a quick '💡 Key Takeaway' and a '🎯 Practice Recall Question' at the end to deepen learning.\n"
        "5. Maintain a professional, encouraging, academic Socratic tutor tone in clean GitHub-flavored Markdown."
    )

    # Build conversation messages
    llm_messages = [SystemMessage(content=system_prompt)]

    # Include recent conversation turns (up to last 6)
    for h in history[-6:]:
        if h.role == "user":
            llm_messages.append(HumanMessage(content=h.content))
        elif h.role == "assistant":
            llm_messages.append(AIMessage(content=h.content))

    # Append current turn with MCP knowledge
    user_turn_content = (
        f"Student Academic Query: {message}\n\n"
        f"--- CONTEXT & MCP SOURCES ---\n"
        f"{combined_context}\n"
        f"-----------------------------\n\n"
        f"Please provide a comprehensive academic study explanation."
    )
    llm_messages.append(HumanMessage(content=user_turn_content))

    llm = get_llm_with_fallback()
    reply_text = ""

    if llm:
        try:
            response = await llm.ainvoke(llm_messages)
            reply_text = response.content.strip()
        except Exception as e:
            logger.error(f"Error calling LLM for study chat: {e}")
            reply_text = ""

    # Resilient fallback if LLM offline or keys unconfigured
    if not reply_text:
        source_bullets = "\n".join([f"- **{s['type']}**: {s['title']} - {s['snippet'][:150]}..." for s in all_sources[:4]])
        reply_text = f"""### 📚 Academic Concept Analysis: {clean_topic_title(message)}

Based on your academic inquiry and connected Model Context Protocol (MCP) knowledge streams:

#### 1. Core Principles & Overview
{mcp_sources[0]['snippet'] if mcp_sources else f"Foundational study analysis and core mechanisms relating to {message}."}

#### 2. Key Academic Takeaways & Context
- **Conceptual Depth**: Concepts are structured around core definitions, empirical evidence, and sequential problem-solving.
- **Active References**: Real-time knowledge retrieved across your connected MCP endpoints.

#### 3. Connected MCP Sources & Literature
{source_bullets if source_bullets else "- General Academic Curriculum Knowledge Base"}

---
💡 **Tutor Tip**: Ask me to break down specific formulas, generate practice questions, or query scientific preprints from ArXiv on this subject!
"""

    return StudyChatResponse(
        reply=reply_text,
        sources=all_sources,
        is_study_question=True
    )
