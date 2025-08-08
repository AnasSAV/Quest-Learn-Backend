from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from ...db.session import get_db
from .auth import get_current_user, CurrentUser
from ...models.user import UserRole
from ...models.question import Question
from ...schemas.question import QuestionCreate, QuestionOut
from ...services.storage import upload_png, public_url, signed_url, delete_image
from ...core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/questions", tags=["questions"])

@router.post("", response_model=QuestionOut)
async def create_question(
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can create questions")
    if payload.correct_option not in ("A", "B", "C", "D"):
        raise HTTPException(400, "correct_option must be A/B/C/D")
    q = Question(**payload.model_dump())
    db.add(q)
    db.commit()
    db.refresh(q)
    return q

@router.post("/upload")
async def upload_question_image(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
):
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can upload images")
    if file.content_type != "image/png":
        raise HTTPException(400, "Only PNG allowed")

    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty or invalid file")
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large. Max {settings.MAX_UPLOAD_MB} MB")

    key = f"questions/{user.id}/{uuid4()}.png"
    ok, path_or_err = upload_png(data, key)
    if not ok:
        raise HTTPException(500, f"Upload failed: {path_or_err}")

    pub = public_url(key)
    url = pub or signed_url(key, expires_sec=3600)

    return {"image_key": key, "url": url, "public": bool(pub)}

# Static path so it can't collide with /{question_id}
@router.delete("/image")
def delete_question_image(
    image_key: str = Query(..., description="Bucket key, e.g. questions/<uid>/<file>.png"),
    user: CurrentUser = Depends(get_current_user),
):
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can delete images")
    ok, msg = delete_image(image_key)
    if not ok:
        raise HTTPException(500, f"Deletion failed: {msg}")
    return {"status": "success", "image_key": image_key}

@router.delete("/{question_id}")
def delete_question(
    question_id: UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
    purge_image: bool = True,
):
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can delete questions")

    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(404, "question not found")

    # try to remove the PNG first (non-fatal if it fails)
    if purge_image and q.image_key:
        try:
            delete_image(q.image_key)
        except Exception:
            pass

    db.delete(q)
    db.commit()
    return {"status": "deleted", "question_id": str(question_id)}
