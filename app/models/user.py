from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.classroom import Classroom, ClassroomMember
    from app.models.assignment import Assignment
    from app.models.attempt import Attempt
    from app.models.upload_token import UploadToken


class UserRole(str, enum.Enum):
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
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
    # Teacher relationships
    owned_classrooms: Mapped[List["Classroom"]] = relationship(
        "Classroom", 
        back_populates="teacher",
        cascade="all, delete-orphan"
    )
    created_assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment",
        back_populates="created_by_user",
        cascade="all, delete-orphan"
    )
    upload_tokens: Mapped[List["UploadToken"]] = relationship(
        "UploadToken",
        back_populates="created_by_user",
        cascade="all, delete-orphan"
    )

    # Student relationships
    classroom_memberships: Mapped[List["ClassroomMember"]] = relationship(
        "ClassroomMember",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    attempts: Mapped[List["Attempt"]] = relationship(
        "Attempt",
        back_populates="student",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_role", "role"),
        Index("idx_users_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
