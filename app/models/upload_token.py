from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User


class UploadToken(Base):
    __tablename__ = "upload_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hint: Mapped[str] = mapped_column(String(255), nullable=False)  # Suggested filename/key
    presigned_url: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    created_by_user: Mapped["User"] = relationship("User", back_populates="upload_tokens")

    # Indexes
    __table_args__ = (
        Index("idx_upload_tokens_created_by", "created_by"),
        Index("idx_upload_tokens_expires_at", "expires_at"),
        Index("idx_upload_tokens_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<UploadToken(id={self.id}, created_by={self.created_by}, content_type='{self.content_type}')>"

    @property
    def is_expired(self) -> bool:
        """Check if the upload token has expired."""
        return datetime.utcnow() > self.expires_at
