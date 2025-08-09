from pydantic import BaseModel
from typing import Optional, List
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
    is_correct: bool  # Changed from int to bool
    time_taken_seconds: int
    
    class Config:
        from_attributes = True

class StudentResult(BaseModel):
    student_id: UUID
    student_name: str
    student_email: str
    attempt_id: Optional[UUID] = None
    status: Optional[str] = None
    total_score: Optional[int] = None
    max_possible_score: int
    percentage: Optional[float] = None
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    time_taken_minutes: Optional[float] = None

class AssignmentResults(BaseModel):
    assignment_id: UUID
    assignment_title: str
    classroom_name: str
    total_students: int
    students_attempted: int
    students_completed: int
    average_score: Optional[float] = None
    max_possible_score: int
    student_results: List[StudentResult]

class StudentAttemptResult(BaseModel):
    attempt_id: UUID
    assignment_id: UUID
    assignment_title: str
    student_id: UUID
    student_name: str
    status: str
    total_score: int
    max_possible_score: int
    percentage: float
    started_at: datetime
    submitted_at: Optional[datetime] = None
    time_taken_minutes: Optional[float] = None
    responses: List[dict]  # Question responses with correct/incorrect info
