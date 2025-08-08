from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.assignment import Assignment


class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    teacher_id: Mapped[int] = mapped_column(
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
    teacher: Mapped["User"] = relationship("User", back_populates="owned_classrooms")
    members: Mapped[List["ClassroomMember"]] = relationship(
        "ClassroomMember",
        back_populates="classroom",
        cascade="all, delete-orphan"
    )
    assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment",
        back_populates="classroom",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_classrooms_teacher_id", "teacher_id"),
        Index("idx_classrooms_code", "code"),
        Index("idx_classrooms_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Classroom(id={self.id}, name='{self.name}', code='{self.code}')>"


class ClassroomMember(Base):
    __tablename__ = "classroom_members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    classroom_id: Mapped[int] = mapped_column(
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="members")
    student: Mapped["User"] = relationship("User", back_populates="classroom_memberships")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("classroom_id", "student_id", name="uq_classroom_student"),
        Index("idx_classroom_members_classroom_id", "classroom_id"),
        Index("idx_classroom_members_student_id", "student_id"),
        Index("idx_classroom_members_joined_at", "joined_at"),
    )

    def __repr__(self) -> str:
        return f"<ClassroomMember(classroom_id={self.classroom_id}, student_id={self.student_id})>"
