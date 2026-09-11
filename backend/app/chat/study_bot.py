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
    Queries active Model Context Protocol (MCP) connectors only when relevant to specific technical/scientific lookups.
    Avoids searching Wikipedia for generic conversational study commands like 'tell me the study plan'.
    """
    sources = []
    clean_q = query.strip().lower()

    # Skip MCP lookups for general conversational study requests
    generic_study_phrases = ["study plan", "how to study", "give me a plan", "revision schedule", "timetable", "tips for exam", "how to prepare"]
    if any(p in clean_q for p in generic_study_phrases) and len(clean_q.split()) <= 6:
        return sources

    user_connectors = await get_user_connectors(user_id)
    active_connector_ids = {c["connector_id"]: c.get("config", {}) for c in user_connectors if c.get("enabled", False)}

    # Query Wikipedia only for specific concepts/topics
    if any(clean_q.startswith(w) for w in ["what is", "define", "who is", "explain"]) or "wikipedia" in clean_q or "wikipedia_connector" in active_connector_ids:
        # Extract core subject
        concept = re.sub(r"(?i)^(what is|what are|define|explain|who is|tell me about)\s+", "", query).strip(" ?.!:")
        if concept and len(concept.split()) <= 5:
            try:
                wiki_res = await run_mcp_connector_tool("wikipedia_connector", "search_wikipedia", {"query": concept}, active_connector_ids.get("wikipedia_connector", {}))
                if wiki_res.get("summary") and "represents a foundational academic concept" not in wiki_res.get("summary", ""):
                    sources.append({
                        "type": "Wikipedia MCP",
                        "title": wiki_res.get("title", concept.title()),
                        "snippet": wiki_res.get("summary"),
                        "url": wiki_res.get("url", "")
                    })
            except Exception as e:
                logger.warning(f"Wikipedia MCP query failed: {e}")

    # Query ArXiv MCP if query mentions science/tech/math/research/papers
    is_stem = any(w in clean_q for w in ["arxiv", "research paper", "preprints", "scientific literature", "quantum", "neural network", "transformer model", "relativity"])
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
    if "news_connector" in active_connector_ids or any(w in clean_q for w in ["latest news", "current discovery", "recent breakthrough"]):
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
    Searches ChromaDB vector store and MongoDB chunks for the user's uploaded lecture notes when relevant.
    """
    doc_sources = []
    try:
        store = get_vector_store()
        chunks = store.search(user_id=user_id, query_text=query, n_results=3)
        for c in chunks:
            if c.get("text") and len(c.get("text", "").strip()) > 30:
                doc_sources.append({
                    "type": "Uploaded Course Notes",
                    "title": f"Page {c.get('metadata', {}).get('page_number', 'N/A')} ({c.get('metadata', {}).get('chapter_title', 'Lecture Chunk')})",
                    "snippet": c.get("text", "")[:300] + "..."
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
    Processes student chat inquiries directly with the LLM with strict academic guardrails,
    supplemented by active MCP tools and course notes when relevant.
    """
    history = history or []

    # 1. Guardrail Check: Strict academic/study enforcement
    if not is_academic_query(message):
        rejection_reply = (
            "### 🛡️ Study Guide AI &bull; Academic Guardrail\n\n"
            "I am your dedicated **AI Academic Study Tutor & Curriculum Assistant**.\n\n"
            "I can only assist with **educational, scientific, curriculum, research, exam preparation, and study guide questions**.\n\n"
            "**Here are a few things you can ask me:**\n"
            "- *\"Create a customized 4-week study plan for my biology exam\"*\n"
            "- *\"Explain the key mechanisms of Cellular Respiration with analogies\"*\n"
            "- *\"Summarize Chapter 3 of my uploaded lecture notes\"*\n"
            "- *\"What are the core differences between TCP and UDP with examples?\"*\n"
            "- *\"Generate 3 practice conceptual questions with model solutions\"*\n\n"
            "Please ask an academic or study-related question to continue!"
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

    # 3. Format Context for LLM if present
    context_blocks = []
    if doc_sources:
        context_blocks.append("--- RELEVANT UPLOADED LECTURE NOTES ---")
        for s in doc_sources:
            context_blocks.append(f"[{s['title']}]: {s['snippet']}")

    if mcp_sources:
        context_blocks.append("--- LIVE MCP KNOWLEDGE SOURCES ---")
        for s in mcp_sources:
            context_blocks.append(f"[{s['type']} - {s['title']}]: {s['snippet']}")

    context_section = "\n\n".join(context_blocks) if context_blocks else ""

    # 4. Construct Socratic Academic Prompt for Direct LLM Intelligence
    system_prompt = (
        "You are an elite, highly knowledgeable AI Academic Professor and Study Tutor.\n"
        "Your goal is to answer the student's study question directly, intelligently, and comprehensively from your own knowledge.\n\n"
        "CORE RULES:\n"
        "1. Provide structured, engaging, and thorough academic answers with clear Markdown formatting (tables, bullet points, step-by-step breakdowns, bold highlights, formulas).\n"
        "2. Be actionable and pedagogical (e.g. explain the 'why' and 'how', provide study frameworks like Pomodoro, Active Recall, Feynman Technique, spaced repetition).\n"
        "3. DO NOT output robotic boilerplate phrases like 'Based on the entry in Wikipedia MCP' or 'According to Model Context Protocol'. Speak naturally and authoritatively as an inspiring academic tutor.\n"
        "4. If relevant uploaded course notes are provided in the context, integrate and reference their specific topics smoothly.\n"
        "5. Conclude with a helpful '💡 Tutor Tip' or '🎯 Practice Check' when appropriate."
    )

    llm_messages = [SystemMessage(content=system_prompt)]

    # Include recent conversation turns (up to last 6)
    for h in history[-6:]:
        if h.role == "user":
            llm_messages.append(HumanMessage(content=h.content))
        elif h.role == "assistant":
            llm_messages.append(AIMessage(content=h.content))

    user_prompt_text = f"Student Question: {message}"
    if context_section:
        user_prompt_text += f"\n\n{context_section}"

    llm_messages.append(HumanMessage(content=user_prompt_text))

    llm = get_llm_with_fallback()
    reply_text = ""

    if llm:
        try:
            response = await llm.ainvoke(llm_messages)
            reply_text = response.content.strip()
        except Exception as e:
            logger.error(f"Error calling LLM for study chat: {e}")
            reply_text = ""

    if not reply_text:
        reply_text = f"""### 📚 Study Plan & Strategy Guide

Here is a structured academic study framework designed for optimal retention and exam success:

#### 1. 🎯 Diagnostic Assessment & Goal Setting
- **Identify Core Syllabus Scope**: Break down major chapters and determine high-weight topics.
- **Set SMART Milestones**: Allocate specific study hours to challenging concepts.

#### 2. ⏳ Structured Weekly Routine
| Phase | Strategy | Daily Time |
| :--- | :--- | :--- |
| **Concept Learning** | Active reading, Cornell note-taking & Feynman explanation | 45-60 mins |
| **Practice & Recall** | Self-testing, flashcards & solving past exam problems | 30-45 mins |
| **Spaced Review** | Reviewing difficult concepts from previous sessions | 15-20 mins |

#### 3. 💡 High-Efficiency Study Techniques
- **Active Recall**: Test yourself by closing the textbook and writing down core principles from memory.
- **Spaced Repetition**: Revisit difficult formulas and terms at intervals (Day 1, Day 3, Day 7).
- **Pomodoro Technique**: 25 minutes of deep focus followed by a 5-minute break.

---
💡 **Tutor Tip**: Ask me to generate a personalized timetable for a specific subject (e.g. Calculus, Physics, Biology) or quiz you on any chapter!
"""

    return StudyChatResponse(
        reply=reply_text,
        sources=all_sources,
        is_study_question=True
    )
