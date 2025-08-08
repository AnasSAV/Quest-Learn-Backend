from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, get_current_teacher, get_current_student, get_current_user
from app.models.user import User
from app.models.classroom import Classroom, ClassroomMember
from app.models.assignment import Assignment
from app.models.question import Question
from app.models.attempt import Attempt
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentUpdate,
    Assignment as AssignmentSchema,
    AssignmentDetail,
    AssignmentSummary,
    PublishAssignment
)
from app.schemas.question import QuestionForStudent
from app.schemas.attempt import StartAttemptResponse

router = APIRouter()


@router.post("/", response_model=AssignmentSchema)
async def create_assignment(
    assignment_data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Create a new assignment."""
    # Verify teacher owns the classroom
    classroom_query = select(Classroom).where(
        Classroom.id == assignment_data.classroom_id,
        Classroom.teacher_id == current_teacher.id
    )
    classroom_result = await db.execute(classroom_query)
    classroom = classroom_result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found or access denied"
        )
    
    assignment = Assignment(
        classroom_id=assignment_data.classroom_id,
        title=assignment_data.title,
        description=assignment_data.description,
        opens_at=assignment_data.opens_at,
        due_at=assignment_data.due_at,
        shuffle_questions=assignment_data.shuffle_questions,
        created_by=current_teacher.id
    )
    
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    
    return AssignmentSchema.from_orm(assignment)


@router.get("/{assignment_id}", response_model=AssignmentDetail)
async def get_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assignment details."""
    query = select(Assignment).options(
        selectinload(Assignment.classroom).selectinload(Classroom.teacher),
        selectinload(Assignment.questions)
    ).where(Assignment.id == assignment_id)
    
    result = await db.execute(query)
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check access permissions
    has_access = False
    if current_user.role.value == "TEACHER" and assignment.classroom.teacher_id == current_user.id:
        has_access = True
    elif current_user.role.value == "STUDENT":
        # Check if student is enrolled in the classroom
        membership_query = select(ClassroomMember).where(
            ClassroomMember.classroom_id == assignment.classroom_id,
            ClassroomMember.student_id == current_user.id
        )
        membership_result = await db.execute(membership_query)
        if membership_result.scalar_one_or_none():
            has_access = True
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Calculate totals
    total_points = sum(q.points for q in assignment.questions)
    question_count = len(assignment.questions)
    
    return AssignmentDetail(
        id=assignment.id,
        classroom_id=assignment.classroom_id,
        title=assignment.title,
        description=assignment.description,
        opens_at=assignment.opens_at,
        due_at=assignment.due_at,
        shuffle_questions=assignment.shuffle_questions,
        created_by=assignment.created_by,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
        classroom_name=assignment.classroom.name,
        teacher_name=assignment.classroom.teacher.full_name,
        total_points=total_points,
        question_count=question_count,
        is_open=assignment.is_open,
        is_past_due=assignment.is_past_due
    )


@router.put("/{assignment_id}", response_model=AssignmentSchema)
async def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Update assignment (only before it opens or has attempts)."""
    # Get assignment with classroom
    query = select(Assignment).options(
        selectinload(Assignment.classroom)
    ).where(Assignment.id == assignment_id)
    
    result = await db.execute(query)
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Verify ownership
    if assignment.classroom.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if assignment has attempts
    attempts_query = select(func.count(Attempt.id)).where(Attempt.assignment_id == assignment_id)
    attempts_result = await db.execute(attempts_query)
    attempt_count = attempts_result.scalar()
    
    if attempt_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify assignment with existing attempts"
        )
    
    # Update fields
    update_data = assignment_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)
    
    await db.commit()
    await db.refresh(assignment)
    
    return AssignmentSchema.from_orm(assignment)


@router.post("/{assignment_id}/publish")
async def publish_assignment(
    assignment_id: int,
    publish_data: PublishAssignment,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Publish assignment with specific dates."""
    # Get assignment with classroom
    query = select(Assignment).options(
        selectinload(Assignment.classroom)
    ).where(Assignment.id == assignment_id)
    
    result = await db.execute(query)
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Verify ownership
    if assignment.classroom.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if assignment has questions
    questions_query = select(func.count(Question.id)).where(Question.assignment_id == assignment_id)
    questions_result = await db.execute(questions_query)
    question_count = questions_result.scalar()
    
    if question_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish assignment without questions"
        )
    
    # Update dates
    if publish_data.opens_at:
        assignment.opens_at = publish_data.opens_at
    if publish_data.due_at:
        assignment.due_at = publish_data.due_at
    
    await db.commit()
    
    return {"message": "Assignment published successfully"}


@router.get("/{assignment_id}/start", response_model=StartAttemptResponse)
async def start_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    """Start an assignment attempt for a student."""
    # Get assignment with questions
    query = select(Assignment).options(
        selectinload(Assignment.questions),
        selectinload(Assignment.classroom)
    ).where(Assignment.id == assignment_id)
    
    result = await db.execute(query)
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check if student is enrolled in classroom
    membership_query = select(ClassroomMember).where(
        ClassroomMember.classroom_id == assignment.classroom_id,
        ClassroomMember.student_id == current_student.id
    )
    membership_result = await db.execute(membership_query)
    membership = membership_result.scalar_one_or_none()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this classroom"
        )
    
    # Check if assignment is open
    if not assignment.is_open:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment is not currently open"
        )
    
    # Check if student already has an attempt
    existing_attempt_query = select(Attempt).where(
        Attempt.assignment_id == assignment_id,
        Attempt.student_id == current_student.id
    )
    existing_attempt_result = await db.execute(existing_attempt_query)
    existing_attempt = existing_attempt_result.scalar_one_or_none()
    
    if existing_attempt:
        if existing_attempt.status.value in ["SUBMITTED", "LATE"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already completed this assignment"
            )
        # Return existing in-progress attempt
        attempt = existing_attempt
    else:
        # Create new attempt
        total_points = sum(q.points for q in assignment.questions)
        attempt = Attempt(
            assignment_id=assignment_id,
            student_id=current_student.id,
            max_possible_score=total_points
        )
        db.add(attempt)
        await db.commit()
        await db.refresh(attempt)
    
    # Prepare questions for student (without correct answers)
    questions = assignment.questions
    if assignment.shuffle_questions:
        import random
        questions = random.sample(questions, len(questions))
    else:
        questions = sorted(questions, key=lambda q: q.order_index)
    
    question_dicts = [QuestionForStudent.from_question(q).dict() for q in questions]
    total_time_seconds = sum(q.per_question_seconds for q in questions)
    
    return StartAttemptResponse(
        attempt_id=attempt.id,
        questions=question_dicts,
        total_time_seconds=total_time_seconds,
        started_at=attempt.started_at
    )


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Delete an assignment (only if no attempts exist)."""
    # Get assignment with classroom
    query = select(Assignment).options(
        selectinload(Assignment.classroom)
    ).where(Assignment.id == assignment_id)
    
    result = await db.execute(query)
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Verify ownership
    if assignment.classroom.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if assignment has attempts
    attempts_query = select(func.count(Attempt.id)).where(Attempt.assignment_id == assignment_id)
    attempts_result = await db.execute(attempts_query)
    attempt_count = attempts_result.scalar()
    
    if attempt_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete assignment with existing attempts"
        )
    
    await db.delete(assignment)
    await db.commit()
    
    return {"message": "Assignment deleted successfully"}
