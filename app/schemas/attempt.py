from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class AttemptOut(BaseModel):
    id: UUID
    assignment_id: UUID
    student_id: UUID
    started_at: datetime
    submitted_at: Optional[datetime] = None
    total_score: int
    status: str
    
    class Config:
        from_attributes = True

class ResponseOut(BaseModel):
    id: UUID
    attempt_id: UUID
    question_id: UUID
    chosen_option: str
    is_correct: int
    time_taken_seconds: int
    
    class Config:
        from_attributes = True
