# Import all models here for Alembic to discover them
from app.db.session import Base
from app.models.user import User
from app.models.classroom import Classroom, ClassroomMember
from app.models.assignment import Assignment
from app.models.question import Question
from app.models.attempt import Attempt, Response
from app.models.upload_token import UploadToken

__all__ = [
    "Base",
    "User",
    "Classroom", 
    "ClassroomMember",
    "Assignment",
    "Question",
    "Attempt",
    "Response",
    "UploadToken",
]
