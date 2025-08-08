from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Integer, ForeignKey, Boolean, Enum, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.assignment import Assignment
    from app.models.question import Question


class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    LATE = "LATE"


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    total_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_possible_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[AttemptStatus] = mapped_column(
        Enum(AttemptStatus),
        default=AttemptStatus.IN_PROGRESS,
        nullable=False
    )

    # Relationships
    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="attempts")
    student: Mapped["User"] = relationship("User", back_populates="attempts")
    responses: Mapped[List["Response"]] = relationship(
        "Response",
        back_populates="attempt",
        cascade="all, delete-orphan"
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="uq_assignment_student_attempt"),
        Index("idx_attempts_assignment_id", "assignment_id"),
        Index("idx_attempts_student_id", "student_id"),
        Index("idx_attempts_status", "status"),
        Index("idx_attempts_started_at", "started_at"),
        Index("idx_attempts_submitted_at", "submitted_at"),
    )

    def __repr__(self) -> str:
        return f"<Attempt(id={self.id}, assignment_id={self.assignment_id}, student_id={self.student_id}, status='{self.status}')>"

    @property
    def score_percentage(self) -> float:
        """Calculate score as percentage."""
        if self.max_possible_score == 0:
            return 0.0
        return (self.total_score / self.max_possible_score) * 100

    @property
    def duration_seconds(self) -> Optional[int]:
        """Calculate attempt duration in seconds."""
        if not self.submitted_at:
            return None
        return int((self.submitted_at - self.started_at).total_seconds())


class Response(Base):
    __tablename__ = "responses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chosen_option: Mapped[str] = mapped_column(String(1), nullable=False)  # A, B, C, or D
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    time_taken_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    attempt: Mapped["Attempt"] = relationship("Attempt", back_populates="responses")
    question: Mapped["Question"] = relationship("Question", back_populates="responses")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question_response"),
        Index("idx_responses_attempt_id", "attempt_id"),
        Index("idx_responses_question_id", "question_id"),
        Index("idx_responses_is_correct", "is_correct"),
        Index("idx_responses_answered_at", "answered_at"),
    )

    def __repr__(self) -> str:
        return f"<Response(id={self.id}, attempt_id={self.attempt_id}, question_id={self.question_id}, chosen='{self.chosen_option}', correct={self.is_correct})>"
