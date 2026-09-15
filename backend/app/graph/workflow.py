import logging
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes import retrieve_node, reasoner_node, mcp_tool_node, synthesis_node
from app.graph.router import reasoner_router

logger = logging.getLogger("graph.workflow")


def build_study_pack_graph():
    """
    Constructs the LangGraph StateGraph pipeline for Study Pack generation.
    Pipeline:
      START -> retrieve -> reasoner -> (conditional router) -> [mcp_tool -> synthesis | synthesis] -> END
    """
    workflow = StateGraph(AgentState)

    # Register Nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("reasoner", reasoner_node)
    workflow.add_node("mcp_tool", mcp_tool_node)
    workflow.add_node("synthesis", synthesis_node)

    # Define Edges
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "reasoner")

    # Conditional routing from reasoner
    workflow.add_conditional_edges(
        "reasoner",
        reasoner_router,
        {
            "mcp_tool": "mcp_tool",
            "synthesis": "synthesis"
        }
    )

    # Edge from mcp_tool to synthesis
    workflow.add_edge("mcp_tool", "synthesis")

    # Edge from synthesis to END
    workflow.add_edge("synthesis", END)

    app = workflow.compile()
    logger.info("Compiled Study Pack LangGraph workflow successfully.")
    return app


_compiled_graph = None


def get_study_pack_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_study_pack_graph()
    return _compiled_graph


async def run_study_pack_pipeline(
    user_id: str,
    document_id: Optional[str] = None,
    difficulty: str = "Intermediate",
    topic: Optional[str] = None,
    custom_instructions: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes the full compiled LangGraph pipeline for the authenticated user.
    """
    graph = get_study_pack_graph()
    initial_state: AgentState = {
        "messages": [],
        "user_id": user_id,
        "document_id": document_id,
        "difficulty": difficulty,
        "topic": topic or "General Lecture Notes",
        "custom_instructions": custom_instructions,
        "context": "",
        "tool_results": [],
        "structured_output": None,
        "next_step": None,
        "error": None
    }

    trace_config = {
        "run_name": f"StudyPack - {topic or 'General'}",
        "tags": ["studypack-pipeline", difficulty, f"user:{user_id}"],
        "metadata": {
            "user_id": user_id,
            "document_id": document_id or "none",
            "difficulty": difficulty,
            "topic": topic or "General Lecture Notes"
        }
    }

    final_state = await graph.ainvoke(initial_state, config=trace_config)
    return final_state.get("structured_output") or {}

