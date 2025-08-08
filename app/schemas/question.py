from typing import Dict, Optional
from pydantic import BaseModel, Field, validator
from app.models.question import QuestionOption


# Base schemas
class QuestionBase(BaseModel):
    prompt_text: Optional[str] = None
    image_url: str = Field(..., description="URL to the question image in Supabase storage")
    option_a: str = Field(..., min_length=1)
    option_b: str = Field(..., min_length=1)
    option_c: str = Field(..., min_length=1)
    option_d: str = Field(..., min_length=1)
    correct_option: QuestionOption
    per_question_seconds: int = Field(..., ge=10, le=600)  # 10 seconds to 10 minutes
    points: int = Field(..., ge=1, le=100)
    order_index: int = Field(..., ge=1)


class QuestionCreate(QuestionBase):
    assignment_id: int


class QuestionUpdate(BaseModel):
    prompt_text: Optional[str] = None
    image_url: Optional[str] = None
    option_a: Optional[str] = Field(None, min_length=1)
    option_b: Optional[str] = Field(None, min_length=1)
    option_c: Optional[str] = Field(None, min_length=1)
    option_d: Optional[str] = Field(None, min_length=1)
    correct_option: Optional[QuestionOption] = None
    per_question_seconds: Optional[int] = Field(None, ge=10, le=600)
    points: Optional[int] = Field(None, ge=1, le=100)
    order_index: Optional[int] = Field(None, ge=1)


# Response schemas
class Question(QuestionBase):
    id: int
    assignment_id: int

    class Config:
        from_attributes = True


class QuestionForStudent(BaseModel):
    """Question schema for students (without correct answer)."""
    id: int
    prompt_text: Optional[str]
    image_url: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    per_question_seconds: int
    points: int
    order_index: int

    class Config:
        from_attributes = True

    @classmethod
    def from_question(cls, question: "Question"):
        return cls(
            id=question.id,
            prompt_text=question.prompt_text,
            image_url=question.image_url,
            option_a=question.option_a,
            option_b=question.option_b,
            option_c=question.option_c,
            option_d=question.option_d,
            per_question_seconds=question.per_question_seconds,
            points=question.points,
            order_index=question.order_index
        )


class QuestionWithStats(Question):
    """Question with statistics for teachers."""
    total_responses: int
    correct_responses: int
    accuracy_rate: float
    average_time_seconds: float
