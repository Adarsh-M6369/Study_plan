from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str = Field(..., description="The message text content")
    sources: Optional[List[Dict[str, Any]]] = Field(default=None, description="MCP or document sources used")
    timestamp: Optional[str] = None


class StudyChatRequest(BaseModel):
    message: str = Field(..., description="The student's study question or query")
    history: Optional[List[ChatMessage]] = Field(default=[], description="Previous conversation turn history")
    document_id: Optional[str] = Field(default=None, description="Active uploaded document ID for context")


class StudyChatResponse(BaseModel):
    reply: str = Field(..., description="The AI Academic response in Markdown")
    sources: List[Dict[str, Any]] = Field(default=[], description="List of MCP connectors and document sources queried")
    is_study_question: bool = Field(default=True, description="Whether the prompt was classified as an academic study query")
