from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...db.session import get_db
from .auth import get_current_user, CurrentUser
from ...models.user import UserRole, User
from ...models.classroom import Classroom, ClassroomMember
from ...schemas.classroom import JoinClassRequest, ClassroomOut

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

@router.get("/{student_id}/classrooms", response_model=list[ClassroomOut])
def get_student_classrooms(
    student_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """Get all classrooms that a specific student is enrolled in"""
    
    # Verify the student exists
    student = db.query(User).filter(User.id == student_id, User.role == UserRole.STUDENT.value).first()
    if not student:
        raise HTTPException(404, "Student not found")
    
    # Permission checks
    if user.role == UserRole.STUDENT.value:
        # Students can only view their own classrooms
        if str(user.id) != student_id:
            raise HTTPException(403, "Students can only view their own classrooms")
    elif user.role == UserRole.TEACHER.value:
        # Teachers can view any student's classrooms (for administrative purposes)
        pass
    else:
        raise HTTPException(403, "Invalid user role")
    
    # Get all classrooms the student is enrolled in
    classrooms = (
        db.query(Classroom)
        .join(ClassroomMember, Classroom.id == ClassroomMember.classroom_id)
        .filter(ClassroomMember.student_id == student_id)
        .all()
    )
    
    return classrooms

@router.get("/my-classrooms", response_model=list[ClassroomOut])
def get_my_classrooms(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """Get all classrooms that the current student is enrolled in"""
    
    # Only students can use this endpoint
    if user.role != UserRole.STUDENT.value:
        raise HTTPException(403, "Only students can use this endpoint")
    
    # Get all classrooms the current user is enrolled in
    classrooms = (
        db.query(Classroom)
        .join(ClassroomMember, Classroom.id == ClassroomMember.classroom_id)
        .filter(ClassroomMember.student_id == user.id)
        .all()
    )
    
    return classrooms

