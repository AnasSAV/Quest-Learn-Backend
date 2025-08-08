from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...db.session import get_db
from .auth import get_current_user, CurrentUser
from ...models.user import UserRole
from ...models.question import Question
from ...models.assignment import Assignment
from ...schemas.assignment import AssignmentCreate, AssignmentOut

router = APIRouter(prefix="/assignments", tags=["assignments"])

@router.post("", response_model=AssignmentOut)
def create_assignment(payload: AssignmentCreate, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can create assignments")
    a = Assignment(**payload.model_dump(), created_by=user.id)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a

@router.get("/{assignment_id}")
def get_assignment(
    assignment_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    a = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not a:
        raise HTTPException(404, "assignment not found")

    # fetch questions ordered
    qs = (
        db.query(Question)
        .filter(Question.assignment_id == assignment_id)
        .order_by(Question.order_index.asc())
        .all()
    )

    is_teacher = user.role == UserRole.TEACHER.value

    questions_payload = []
    for q in qs:
        item = {
            "id": str(q.id),
            "prompt_text": q.prompt_text,
            "image_key": q.image_key,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "per_question_seconds": q.per_question_seconds,
            "points": q.points,
            "order_index": q.order_index,
        }
        if is_teacher:
            item["correct_option"] = q.correct_option.value  # visible to teachers only
        questions_payload.append(item)

    return {
        "id": str(a.id),
        "title": a.title,
        "classroom_id": str(a.classroom_id),
        "questions": questions_payload,
    }

@router.delete("/{assignment_id}")
def delete_assignment(assignment_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    a = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not a:
        raise HTTPException(404, "assignment not found")
    db.delete(a)
    db.commit()
    return {"message": "Assignment deleted successfully"}
