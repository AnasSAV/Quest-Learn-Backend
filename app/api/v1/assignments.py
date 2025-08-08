from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...db.session import get_db
from .auth import get_current_user, CurrentUser
from ...models.user import UserRole
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
def get_assignment(assignment_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    a = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not a:
        raise HTTPException(404, "assignment not found")
    return {"id": str(a.id), "title": a.title, "classroom_id": str(a.classroom_id)}
