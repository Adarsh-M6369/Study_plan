import logging
from typing import Literal
from app.graph.state import AgentState

logger = logging.getLogger("graph.router")


def reasoner_router(state: AgentState) -> Literal["mcp_tool", "synthesis"]:
    """
    Decides whether to route to MCP tool node or proceed directly to synthesis.
    """
    next_step = state.get("next_step")
    if next_step == "mcp_tool":
        logger.info("Routing from reasoner to mcp_tool.")
        return "mcp_tool"
    logger.info("Routing from reasoner to synthesis.")
    return "synthesis"
