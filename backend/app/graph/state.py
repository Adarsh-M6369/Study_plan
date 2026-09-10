from typing import List, Dict, Any, Optional, TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    LangGraph TypedDict State for the Study Guide Generation Pipeline.
    """
    messages: List[BaseMessage]
    user_id: str
    difficulty: str  # "Beginner" | "Intermediate" | "Advanced"
    topic: Optional[str]
    custom_instructions: Optional[str]
    context: str
    tool_results: List[Dict[str, Any]]
    structured_output: Optional[Dict[str, Any]]
    next_step: Optional[str]
    error: Optional[str]
