from sqlalchemy import Column, ForeignKey, Boolean, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import String, DateTime
from ..db.base import Base

class Assignment(Base):
    __tablename__ = "assignment"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    classroom_id = Column(UUID(as_uuid=True), ForeignKey("classroom.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    opens_at = Column(DateTime(timezone=True))
    due_at = Column(DateTime(timezone=True))
    shuffle_questions = Column(Boolean, nullable=False, server_default=text("false"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))