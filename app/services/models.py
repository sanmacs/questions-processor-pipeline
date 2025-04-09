from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class Tag(BaseModel):
    id: str
    name: str

class QuestionTaggingResponse(BaseModel):
    id: str
    question: str
    tags: List[Tag] = Field(default_factory=list)
    difficulty_level: int

class Step(BaseModel):
    explanation: str
    output: str

class MathReasoning(BaseModel):
    id: str
    question: str
    steps: list[Step]
    final_answer: str

class Question(BaseModel):
    id: str
    question: str
    assertion: str
    reason: str
    # table: Dict[str, str] = Field(default_factory=dict)
    passage: str
    a: str
    b: str
    c: str
    d: str
    final_answer: str
    solution: list[Step]
    topic: str
    sub_topic: str
    question_type: str
    allocated_marks: int
    reference_exam: str

class Solution(BaseModel):
    id: str
    qid: str
    steps: list[Step]
    final_answer: str

class Questions(BaseModel):
    questions: List[Question]

class Subtopic(BaseModel):
    """Represents a subtopic/concept within a unit."""
    name: str
    description: Optional[str]

class Unit(BaseModel):
    """Represents a unit in the syllabus."""
    name: str
    subtopics: List[Subtopic]

class SyllabusStructure(BaseModel):
    """Represents the complete syllabus structure."""
    subject: str
    units: List[Unit]