from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class MCQOption(BaseModel):
    label: Literal["A", "B", "C", "D"] = Field(..., description="Option label (A, B, C, or D)")
    text: str = Field(..., description="The text of the option")


class MCQItem(BaseModel):
    id: int = Field(..., description="Question number (1 to 20)")
    question: str = Field(..., description="The multiple choice question")
    options: List[MCQOption] = Field(..., min_length=4, max_length=4, description="Four choices A, B, C, D")
    correct_answer: Literal["A", "B", "C", "D"] = Field(..., description="The correct option label")
    explanation: str = Field(..., description="Clear explanation of why this answer is correct and others are incorrect")
    difficulty: Optional[Literal["Beginner", "Intermediate", "Advanced"]] = Field(default="Intermediate")


class QAItem(BaseModel):
    id: int = Field(..., description="Question number (1 to 5)")
    question: str = Field(..., description="Conceptual or analytical short-answer question")
    model_answer: str = Field(..., description="Comprehensive model answer")
    key_points: List[str] = Field(default_factory=list, description="Key bullet points required for full marks")


class GlossaryItem(BaseModel):
    term: str = Field(..., description="Important concept, keyword, or acronym")
    definition: str = Field(..., description="Concise, precise academic definition")


class StudyRoadmapStep(BaseModel):
    step_number: int = Field(..., description="Step sequence number")
    topic: str = Field(..., description="Topic or phase name")
    estimated_minutes: int = Field(..., description="Estimated study time in minutes")
    action_item: str = Field(..., description="Specific active recall or study task to perform")


class StudyPack(BaseModel):
    title: str = Field(..., description="Title of the study guide")
    difficulty: Literal["Beginner", "Intermediate", "Advanced"] = Field(
        default="Intermediate",
        description="Applied difficulty tier"
    )
    summary_notes: str = Field(..., description="Concise, high-yield synthesized summary notes in markdown format")
    roadmap: List[StudyRoadmapStep] = Field(..., description="Suggested step-by-step study roadmap sequence")
    glossary: List[GlossaryItem] = Field(..., description="Key technical terms, definitions, and formulas")
    short_qas: List[QAItem] = Field(..., min_length=5, max_length=5, description="5 Short Q&As with model answers")
    mcqs: List[MCQItem] = Field(..., min_length=20, max_length=20, description="20 MCQs with 4 options, explanations, and answer keys")
