from sqlalchemy import Column, ForeignKey, Integer, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import DateTime, Enum
from ..db.base import Base
from .question import MCQOption
import enum

class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    LATE = "LATE"

class Attempt(Base):
    __tablename__ = "attempt"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignment.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=text("now()"))
    submitted_at = Column(DateTime(timezone=True))
    total_score = Column(Integer, nullable=False, server_default=text("0"))
    status = Column(Enum(AttemptStatus, name="attempt_status"), nullable=False, server_default=text("'IN_PROGRESS'"))

class Response(Base):
    __tablename__ = "response"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    attempt_id = Column(UUID(as_uuid=True), ForeignKey("attempt.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("question.id", ondelete="CASCADE"), nullable=False)
    chosen_option = Column(Enum(MCQOption, name="mcq_option"), nullable=False)
    is_correct = Column(Boolean, nullable=False)  # Boolean type to match database
    time_taken_seconds = Column(Integer, nullable=False)