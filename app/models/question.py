from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.attempt import Response


class QuestionOption(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    prompt_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[str] = mapped_column(String(512), nullable=False)  # Supabase storage URL
    option_a: Mapped[str] = mapped_column(Text, nullable=False)
    option_b: Mapped[str] = mapped_column(Text, nullable=False)
    option_c: Mapped[str] = mapped_column(Text, nullable=False)
    option_d: Mapped[str] = mapped_column(Text, nullable=False)
    correct_option: Mapped[QuestionOption] = mapped_column(String(1), nullable=False)
    per_question_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="questions")
    responses: Mapped[List["Response"]] = relationship(
        "Response",
        back_populates="question",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_questions_assignment_id", "assignment_id"),
        Index("idx_questions_assignment_order", "assignment_id", "order_index"),
    )

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, assignment_id={self.assignment_id}, order_index={self.order_index})>"

    def get_options_dict(self) -> dict:
        """Get question options as a dictionary."""
        return {
            "A": self.option_a,
            "B": self.option_b,
            "C": self.option_c,
            "D": self.option_d,
        }

    def is_correct_answer(self, chosen_option: str) -> bool:
        """Check if the chosen option is correct."""
        return chosen_option.upper() == self.correct_option.value
