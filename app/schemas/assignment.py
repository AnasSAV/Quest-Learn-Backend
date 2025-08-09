from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class AssignmentCreate(BaseModel):
    classroom_id: UUID
    title: str
    description: Optional[str] = None
    opens_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    shuffle_questions: bool = False

class AssignmentOut(BaseModel):
    id: UUID
    classroom_id: UUID
    title: str

    class Config:
        from_attributes = True

class AssignmentSummary(BaseModel):
    id: UUID
    classroom_id: UUID
    title: str
    description: Optional[str] = None
    opens_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    shuffle_questions: bool = False
    created_at: datetime
    classroom_name: str
    total_questions: int
    total_attempts: int
    unique_students_attempted: int
    completed_attempts: int
    average_score: Optional[float] = None
    is_active: bool  # True if assignment is currently open for submissions
    
    # Student-specific fields (populated when student_id parameter is provided)
    student_status: Optional[str] = None  # NOT_STARTED, IN_PROGRESS, SUBMITTED, LATE
    student_score: Optional[int] = None
    student_submitted_at: Optional[datetime] = None
    student_started_at: Optional[datetime] = None
    is_submitted_by_student: Optional[bool] = None

    class Config:
        from_attributes = True
