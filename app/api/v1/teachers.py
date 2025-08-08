import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...db.session import get_db
from .auth import get_current_user, CurrentUser
from ...models.user import UserRole
from ...models.classroom import Classroom, ClassroomMember
from ...schemas.classroom import ClassroomCreate, ClassroomOut

router = APIRouter(prefix="/teachers", tags=["teachers"])

@router.post("/classrooms", response_model=ClassroomOut)
def create_classroom(payload: ClassroomCreate, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can create classrooms")
    code = secrets.token_urlsafe(6)
    c = Classroom(name=payload.name, code=code, teacher_id=user.id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@router.get("/classrooms/all")
def list_classrooms(db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can list classrooms")
    classrooms = db.query(Classroom).filter(Classroom.teacher_id == user.id).all()
    return {"count": len(classrooms), "classrooms": [{"id": c.id, "name": c.name} for c in classrooms]}
    return {"count": len(members), "members": [{"student_id": m.student_id} for m in members]}


@router.get("/classrooms/{classroom_id}/members")
def list_members(classroom_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id, Classroom.teacher_id == user.id).first()
    if not classroom:
        raise HTTPException(404, "classroom not found")
    members = db.query(ClassroomMember).filter(ClassroomMember.classroom_id == classroom_id).all()
    return {"count": len(members), "members": [{"student_id": m.student_id} for m in members]}

@router.delete("/classrooms/{classroom_id}")
def delete_classroom(classroom_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can delete classrooms")
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id, Classroom.teacher_id == user.id).first()
    if not classroom:
        raise HTTPException(404, "classroom not found")
    db.delete(classroom)
    db.commit()
    return {"message": "Classroom deleted successfully"}