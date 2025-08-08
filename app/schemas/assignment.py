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
