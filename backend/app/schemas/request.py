from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class IngestTextRequest(BaseModel):
    title: Optional[str] = Field(default="Uploaded Material", description="Title of the lecture or topic")
    text: str = Field(..., min_length=10, description="Raw text or syllabus content to ingest")


class GenerateRequest(BaseModel):
    document_id: Optional[str] = Field(default=None, description="Optional document ID to scope generation")
    topic: Optional[str] = Field(default="General Overview", description="Specific topic or focus area")
    difficulty: Literal["Beginner", "Intermediate", "Advanced"] = Field(
        default="Intermediate",
        description="Difficulty level for study guide and MCQs"
    )
    custom_instructions: Optional[str] = Field(
        default=None,
        description="Optional additional instructions or focus points"
    )


class UploadResponse(BaseModel):
    status: str = "success"
    document_id: str
    title: str
    page_count: int
    chunk_count: int
    chapters: Optional[list] = None
    message: str


class QuizSubmitRequest(BaseModel):
    pack_id: str = Field(..., description="ID of the study pack being tested")
    document_id: Optional[str] = Field(default=None, description="Optional document ID")
    score: int = Field(..., description="Number of correct answers")
    total: int = Field(default=20, description="Total number of questions")
    answers: Dict[str, str] = Field(default_factory=dict, description="Map of question_id to selected answer")


class MCPConnectRequest(BaseModel):
    connector_id: str = Field(..., description="ID of the MCP connector to configure")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Configuration settings for the connector")
    enabled: bool = Field(default=True, description="Whether the connector is enabled")


class MCPDisconnectRequest(BaseModel):
    connector_id: str = Field(..., description="ID of the MCP connector to disconnect")


class MCPTestRequest(BaseModel):
    connector_id: str = Field(..., description="ID of the MCP connector to test")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Configuration parameters to test")


class MCPExecuteToolRequest(BaseModel):
    connector_id: str = Field(..., description="Target MCP connector ID")
    tool_name: str = Field(..., description="Name of tool to execute")
    arguments: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Tool arguments")

