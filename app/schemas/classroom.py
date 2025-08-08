from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# Base schemas
class ClassroomBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ClassroomCreate(ClassroomBase):
    pass


class ClassroomUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


# Response schemas
class Classroom(ClassroomBase):
    id: int
    code: str
    teacher_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClassroomWithMemberCount(Classroom):
    member_count: int


class ClassroomMember(BaseModel):
    id: int
    student_id: int
    student_name: str
    student_email: str
    joined_at: datetime

    class Config:
        from_attributes = True


class ClassroomDetail(Classroom):
    members: List[ClassroomMember]


# Join classroom schema
class JoinClassroom(BaseModel):
    code: str = Field(..., min_length=6, max_length=10)


class EnrollStudent(BaseModel):
    email: str = Field(..., description="Student email address")


# Invite response
class ClassroomInvite(BaseModel):
    code: str
    invite_url: Optional[str] = None
