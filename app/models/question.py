from sqlalchemy import Column, ForeignKey, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import String, Enum
from ..db.base import Base
import enum

class MCQOption(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"

class Question(Base):
    __tablename__ = "question"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignment.id", ondelete="CASCADE"), nullable=False)
    prompt_text = Column(String)
    image_key = Column(String)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)
    correct_option = Column(Enum(MCQOption, name="mcq_option"), nullable=False)
    per_question_seconds = Column(Integer, nullable=False)
    points = Column(Integer, nullable=False, server_default=text("1"))
    order_index = Column(Integer, nullable=False, server_default=text("0"))
