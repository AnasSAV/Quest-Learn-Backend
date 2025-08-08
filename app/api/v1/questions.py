from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import uuid4
from ...db.session import get_db
from .auth import get_current_user, CurrentUser
from ...models.user import UserRole
from ...models.question import Question, MCQOption
from ...schemas.question import QuestionCreate, QuestionOut
from ...services.storage import upload_png
from ...core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/questions", tags=["questions"])

@router.post("", response_model=QuestionOut)
async def create_question(payload: QuestionCreate, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can create questions")
    if payload.correct_option not in ("A","B","C","D"):
        raise HTTPException(400, "correct_option must be A/B/C/D")
    q = Question(**payload.model_dump())
    db.add(q)
    db.commit()
    db.refresh(q)
    return q

@router.post("/upload")
async def upload_question_image(file: UploadFile = File(...), db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can upload images")
    if file.content_type not in ("image/png",):
        raise HTTPException(400, "Only PNG allowed")
    data = await file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(413, f"File too large. Max {settings.MAX_UPLOAD_MB} MB")
    key = f"questions/{user.id}/{uuid4()}.png"
    ok, path = upload_png(data, key)
    if not ok:
        raise HTTPException(500, f"Upload failed: {path}")
    return {"image_key": path}