from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class QuestionCreate(BaseModel):
    assignment_id: UUID
    prompt_text: Optional[str] = None
    image_key: Optional[str] = None
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str  # A, B, C, or D
    per_question_seconds: int
    points: int = 1
    order_index: int = 0

class QuestionOut(BaseModel):
    id: UUID
    assignment_id: UUID
    prompt_text: Optional[str] = None
    image_key: Optional[str] = None
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    per_question_seconds: int
    points: int
    order_index: int
    
    class Config:
        from_attributes = True

class StartAttemptResponse(BaseModel):
    attempt_id: UUID
    questions: List[dict]  # question payload without correct_option

class AnswerRequest(BaseModel):
    question_id: UUID
    chosen_option: str
    time_taken_seconds: int