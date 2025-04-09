from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class Step(BaseModel):
    explanation: str
    output: str


class Solution(BaseModel):
    steps: List[Step]


class QuestionCreate(BaseModel):
    id: str
    question: str
    passage: Optional[str] = None
    assertion: Optional[str] = None
    reason: Optional[str] = None
    choices: List[str]
    solution: Solution
    final_answer: str
    topic: Optional[str] = None
    sub_topic: Optional[str] = None
    question_type: Optional[str] = None
    allocated_marks: Optional[int] = None
    reference_exam: Optional[str] = None


class Question(QuestionCreate):
    id: str


class ExtractionRequest(BaseModel):
    use_openai_key: Optional[bool] = Field(False, description="Whether to use user's OpenAI key")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key (if using user's key)")


class ExtractionResponse(BaseModel):
    questions: List[Question]
    file_name: str
    extraction_id: str


class StatusEnum(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionStatus(BaseModel):
    status: StatusEnum
    message: Optional[str] = None
    progress: Optional[float] = None  # 0.0 to 1.0
    questions: Optional[List[Question]] = None
    extraction_id: str


class ErrorResponse(BaseModel):
    detail: str