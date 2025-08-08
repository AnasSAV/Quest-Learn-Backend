from sqlalchemy import Column, ForeignKey, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import String, DateTime
from sqlalchemy.orm import relationship
from ..db.base import Base

class Classroom(Base):
    __tablename__ = "classroom"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))

class ClassroomMember(Base):
    __tablename__ = "classroom_member"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    classroom_id = Column(UUID(as_uuid=True), ForeignKey("classroom.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=text("now()"))