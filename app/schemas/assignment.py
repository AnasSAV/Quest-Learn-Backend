from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# Base schemas
class AssignmentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    opens_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    shuffle_questions: bool = False


class AssignmentCreate(AssignmentBase):
    classroom_id: int


class AssignmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    opens_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    shuffle_questions: Optional[bool] = None


# Response schemas
class Assignment(AssignmentBase):
    id: int
    classroom_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    question_count: Optional[int] = None

    class Config:
        from_attributes = True


class AssignmentDetail(Assignment):
    classroom_name: str
    teacher_name: str
    total_points: int
    question_count: int
    is_open: bool
    is_past_due: bool


class AssignmentSummary(BaseModel):
    id: int
    title: str
    question_count: int
    total_points: int
    opens_at: Optional[datetime]
    due_at: Optional[datetime]
    is_open: bool
    is_past_due: bool


class PublishAssignment(BaseModel):
    opens_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
