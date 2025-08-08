from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, ForeignKey, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.classroom import Classroom
    from app.models.question import Question
    from app.models.attempt import Attempt


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    classroom_id: Mapped[int] = mapped_column(
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    opens_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="assignments")
    created_by_user: Mapped["User"] = relationship("User", back_populates="created_assignments")
    questions: Mapped[List["Question"]] = relationship(
        "Question",
        back_populates="assignment",
        cascade="all, delete-orphan",
        order_by="Question.order_index"
    )
    attempts: Mapped[List["Attempt"]] = relationship(
        "Attempt",
        back_populates="assignment",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_assignments_classroom_id", "classroom_id"),
        Index("idx_assignments_created_by", "created_by"),
        Index("idx_assignments_opens_at", "opens_at"),
        Index("idx_assignments_due_at", "due_at"),
        Index("idx_assignments_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Assignment(id={self.id}, title='{self.title}', classroom_id={self.classroom_id})>"

    @property
    def is_open(self) -> bool:
        """Check if assignment is currently open for submissions."""
        now = datetime.utcnow()
        if self.opens_at and now < self.opens_at:
            return False
        if self.due_at and now > self.due_at:
            return False
        return True

    @property
    def is_past_due(self) -> bool:
        """Check if assignment is past due date."""
        if not self.due_at:
            return False
        return datetime.utcnow() > self.due_at
