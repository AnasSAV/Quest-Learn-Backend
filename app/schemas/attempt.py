from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from app.models.attempt import AttemptStatus


# Base schemas
class ResponseBase(BaseModel):
    question_id: int
    chosen_option: str = Field(..., regex="^[ABCD]$")
    time_taken_seconds: int = Field(..., ge=0)

    @validator('chosen_option')
    def validate_chosen_option(cls, v):
        return v.upper()


class ResponseCreate(ResponseBase):
    pass


class AttemptStart(BaseModel):
    assignment_id: int


class AttemptSubmit(BaseModel):
    pass


# Response schemas
class Response(ResponseBase):
    id: int
    attempt_id: int
    is_correct: bool
    answered_at: datetime

    class Config:
        from_attributes = True


class ResponseWithQuestion(Response):
    question_prompt: Optional[str]
    question_points: int
    correct_option: str


class Attempt(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    started_at: datetime
    submitted_at: Optional[datetime]
    total_score: int
    max_possible_score: int
    status: AttemptStatus
    score_percentage: float
    duration_seconds: Optional[int]

    class Config:
        from_attributes = True


class AttemptDetail(Attempt):
    assignment_title: str
    student_name: str
    responses: List[ResponseWithQuestion]


class AttemptSummary(BaseModel):
    id: int
    assignment_title: str
    started_at: datetime
    submitted_at: Optional[datetime]
    total_score: int
    max_possible_score: int
    status: AttemptStatus
    score_percentage: float


class StartAttemptResponse(BaseModel):
    attempt_id: int
    questions: List[dict]  # List of QuestionForStudent
    total_time_seconds: int
    started_at: datetime
