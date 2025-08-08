import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine, async_session
from app.db.base import Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.classroom import Classroom
from app.models.assignment import Assignment
from app.models.question import Question, QuestionOption
import secrets
import string
from datetime import datetime, timedelta


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def create_demo_data() -> None:
    """Create demo data for development."""
    async with async_session() as db:
        # Check if demo data already exists
        existing_user = await db.get(User, 1)
        if existing_user:
            return

        # Create demo teacher
        teacher = User(
            email="teacher@example.com",
            password_hash=get_password_hash("password123"),
            role=UserRole.TEACHER,
            full_name="Demo Teacher"
        )
        db.add(teacher)
        await db.flush()

        # Create demo student
        student = User(
            email="student@example.com",
            password_hash=get_password_hash("password123"),
            role=UserRole.STUDENT,
            full_name="Demo Student"
        )
        db.add(student)
        await db.flush()

        # Create demo classroom
        classroom_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        classroom = Classroom(
            name="Math 101",
            code=classroom_code,
            teacher_id=teacher.id
        )
        db.add(classroom)
        await db.flush()

        # Create demo assignment
        assignment = Assignment(
            classroom_id=classroom.id,
            title="Basic Algebra Quiz",
            description="A simple quiz on basic algebra concepts",
            opens_at=datetime.utcnow(),
            due_at=datetime.utcnow() + timedelta(days=7),
            shuffle_questions=False,
            created_by=teacher.id
        )
        db.add(assignment)
        await db.flush()

        # Create demo questions
        questions_data = [
            {
                "prompt_text": "What is 2 + 2?",
                "image_url": "https://example.com/demo-question-1.png",
                "option_a": "3",
                "option_b": "4",
                "option_c": "5",
                "option_d": "6",
                "correct_option": QuestionOption.B,
                "per_question_seconds": 30,
                "points": 1,
                "order_index": 1
            },
            {
                "prompt_text": "What is 5 × 3?",
                "image_url": "https://example.com/demo-question-2.png",
                "option_a": "15",
                "option_b": "12",
                "option_c": "18",
                "option_d": "20",
                "correct_option": QuestionOption.A,
                "per_question_seconds": 45,
                "points": 2,
                "order_index": 2
            },
            {
                "prompt_text": "Solve for x: 2x + 4 = 10",
                "image_url": "https://example.com/demo-question-3.png",
                "option_a": "2",
                "option_b": "3",
                "option_c": "4",
                "option_d": "5",
                "correct_option": QuestionOption.B,
                "per_question_seconds": 60,
                "points": 3,
                "order_index": 3
            }
        ]

        for question_data in questions_data:
            question = Question(
                assignment_id=assignment.id,
                **question_data
            )
            db.add(question)

        await db.commit()
        print("Demo data created successfully!")


if __name__ == "__main__":
    asyncio.run(create_demo_data())
