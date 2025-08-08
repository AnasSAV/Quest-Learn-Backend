from pydantic import BaseModel
from uuid import UUID

class ClassroomCreate(BaseModel):
    name: str

class ClassroomOut(BaseModel):
    id: UUID
    name: str
    code: str

    class Config:
        from_attributes = True

class JoinClassRequest(BaseModel):
    code: str