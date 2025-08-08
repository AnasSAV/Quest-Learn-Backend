from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...db.session import get_db
from .auth import get_current_user, CurrentUser
from ...models.user import UserRole
from ...models.classroom import Classroom, ClassroomMember
from ...schemas.classroom import JoinClassRequest

router = APIRouter(prefix="/students", tags=["students"])

@router.post("/join")
def join_class(payload: JoinClassRequest, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if user.role != UserRole.STUDENT.value:
        raise HTTPException(403, "Only students can join classrooms")
    classroom = db.query(Classroom).filter(Classroom.code == payload.code).first()
    if not classroom:
        raise HTTPException(404, "Invalid class code")
    existing = db.query(ClassroomMember).filter(ClassroomMember.classroom_id == classroom.id, ClassroomMember.student_id == user.id).first()
    if existing:
        return {"status": "already_joined"}
    db.add(ClassroomMember(classroom_id=classroom.id, student_id=user.id))
    db.commit()
    return {"status": "joined", "classroom_id": str(classroom.id)}