from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, get_current_student
from app.models.user import User, UserRole
from app.models.classroom import Classroom, ClassroomMember
from app.models.assignment import Assignment
from app.schemas.classroom import JoinClassroom
from app.schemas.assignment import AssignmentSummary

router = APIRouter()


@router.post("/join")
async def join_classroom(
    join_data: JoinClassroom,
    db: AsyncSession = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    """Join a classroom using invite code."""
    # Find classroom by code
    classroom_query = select(Classroom).where(Classroom.code == join_data.code.upper())
    classroom_result = await db.execute(classroom_query)
    classroom = classroom_result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid classroom code"
        )
    
    # Check if already a member
    existing_query = select(ClassroomMember).where(
        ClassroomMember.classroom_id == classroom.id,
        ClassroomMember.student_id == current_student.id
    )
    existing_result = await db.execute(existing_query)
    existing_member = existing_result.scalar_one_or_none()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of this classroom"
        )
    
    # Create membership
    membership = ClassroomMember(
        classroom_id=classroom.id,
        student_id=current_student.id
    )
    
    db.add(membership)
    await db.commit()
    
    return {
        "message": f"Successfully joined {classroom.name}",
        "classroom_id": classroom.id,
        "classroom_name": classroom.name
    }


@router.get("/classrooms")
async def get_student_classrooms(
    db: AsyncSession = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    """Get all classrooms the student is enrolled in."""
    query = select(ClassroomMember).options(
        selectinload(ClassroomMember.classroom).selectinload(Classroom.teacher)
    ).where(ClassroomMember.student_id == current_student.id)
    
    result = await db.execute(query)
    memberships = result.scalars().all()
    
    classrooms = []
    for membership in memberships:
        classroom = membership.classroom
        classrooms.append({
            "id": classroom.id,
            "name": classroom.name,
            "code": classroom.code,
            "teacher_name": classroom.teacher.full_name,
            "joined_at": membership.joined_at,
            "created_at": classroom.created_at
        })
    
    return classrooms


@router.get("/classrooms/{classroom_id}/assignments", response_model=List[AssignmentSummary])
async def get_classroom_assignments(
    classroom_id: int,
    db: AsyncSession = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    """Get all assignments for a classroom the student is enrolled in."""
    # Verify student is member of classroom
    membership_query = select(ClassroomMember).where(
        ClassroomMember.classroom_id == classroom_id,
        ClassroomMember.student_id == current_student.id
    )
    membership_result = await db.execute(membership_query)
    membership = membership_result.scalar_one_or_none()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this classroom"
        )
    
    # Get assignments for the classroom
    from sqlalchemy import func
    from app.models.question import Question
    
    assignments_query = select(
        Assignment,
        func.count(Question.id).label("question_count"),
        func.coalesce(func.sum(Question.points), 0).label("total_points")
    ).outerjoin(
        Question, Assignment.id == Question.assignment_id
    ).where(
        Assignment.classroom_id == classroom_id
    ).group_by(Assignment.id).order_by(Assignment.created_at.desc())
    
    assignments_result = await db.execute(assignments_query)
    rows = assignments_result.all()
    
    assignments = []
    for assignment, question_count, total_points in rows:
        assignments.append(AssignmentSummary(
            id=assignment.id,
            title=assignment.title,
            question_count=question_count or 0,
            total_points=total_points or 0,
            opens_at=assignment.opens_at,
            due_at=assignment.due_at,
            is_open=assignment.is_open,
            is_past_due=assignment.is_past_due
        ))
    
    return assignments


@router.post("/classrooms/{classroom_id}/leave")
async def leave_classroom(
    classroom_id: int,
    db: AsyncSession = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    """Leave a classroom."""
    # Find membership
    membership_query = select(ClassroomMember).where(
        ClassroomMember.classroom_id == classroom_id,
        ClassroomMember.student_id == current_student.id
    )
    membership_result = await db.execute(membership_query)
    membership = membership_result.scalar_one_or_none()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a member of this classroom"
        )
    
    # Check if student has any attempts in this classroom's assignments
    from app.models.attempt import Attempt
    from sqlalchemy import func
    
    attempts_query = select(func.count(Attempt.id)).select_from(
        Attempt.join(Assignment, Attempt.assignment_id == Assignment.id)
    ).where(
        Assignment.classroom_id == classroom_id,
        Attempt.student_id == current_student.id
    )
    attempts_result = await db.execute(attempts_query)
    attempt_count = attempts_result.scalar()
    
    if attempt_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot leave classroom with existing assignment attempts"
        )
    
    await db.delete(membership)
    await db.commit()
    
    return {"message": "Successfully left the classroom"}
