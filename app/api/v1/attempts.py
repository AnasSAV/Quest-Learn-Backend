from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, get_current_student
from app.models.user import User
from app.models.assignment import Assignment
from app.models.question import Question
from app.models.attempt import Attempt, AttemptStatus, Response
from app.models.classroom import ClassroomMember
from app.schemas.attempt import (
    ResponseCreate,
    AttemptSubmit,
    Response as ResponseSchema,
    Attempt as AttemptSchema,
    AttemptSummary,
    AttemptDetail
)
from app.services.grading import grading_service

router = APIRouter()


@router.post("/{attempt_id}/answer", response_model=ResponseSchema)
async def submit_answer(
    attempt_id: int,
    answer_data: ResponseCreate,
    db: AsyncSession = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    """Submit an answer for a question in an attempt."""
    # Get attempt with assignment and question
    attempt_query = select(Attempt).options(
        selectinload(Attempt.assignment)
    ).where(
        Attempt.id == attempt_id,
        Attempt.student_id == current_student.id
    )
    
    attempt_result = await db.execute(attempt_query)
    attempt = attempt_result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found"
        )
    
    # Check if attempt is still in progress
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attempt is no longer active"
        )
    
    # Check if assignment is still open (with grace period)
    if attempt.assignment.is_past_due:
        # Allow late submission but mark as late
        pass
    
    # Get the question
    question = await db.get(Question, answer_data.question_id)
    if not question or question.assignment_id != attempt.assignment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid question for this attempt"
        )
    
    # Check if response already exists
    existing_response_query = select(Response).where(
        Response.attempt_id == attempt_id,
        Response.question_id == answer_data.question_id
    )
    existing_response_result = await db.execute(existing_response_query)
    existing_response = existing_response_result.scalar_one_or_none()
    
    if existing_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Answer already submitted for this question"
        )
    
    # Validate time limit (with grace period of 5 seconds)
    grace_period = 5
    if answer_data.time_taken_seconds > (question.per_question_seconds + grace_period):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time limit exceeded for this question"
        )
    
    # Grade the response
    is_correct, points_earned = await grading_service.grade_response(
        db, answer_data.question_id, answer_data.chosen_option, answer_data.time_taken_seconds
    )
    
    # Create response record
    response = Response(
        attempt_id=attempt_id,
        question_id=answer_data.question_id,
        chosen_option=answer_data.chosen_option.upper(),
        is_correct=is_correct,
        time_taken_seconds=answer_data.time_taken_seconds
    )
    
    db.add(response)
    
    # Update attempt score
    attempt.total_score += points_earned
    
    await db.commit()
    await db.refresh(response)
    
    return ResponseSchema.from_orm(response)


@router.post("/{attempt_id}/submit", response_model=AttemptSchema)
async def submit_attempt(
    attempt_id: int,
    submit_data: AttemptSubmit,
    db: AsyncSession = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    """Submit/finalize an attempt."""
    # Get attempt with assignment
    attempt_query = select(Attempt).options(
        selectinload(Attempt.assignment),
        selectinload(Attempt.responses)
    ).where(
        Attempt.id == attempt_id,
        Attempt.student_id == current_student.id
    )
    
    attempt_result = await db.execute(attempt_query)
    attempt = attempt_result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found"
        )
    
    # Check if attempt is still in progress
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attempt has already been submitted"
        )
    
    # Recalculate final score
    total_score, max_possible_score = await grading_service.calculate_attempt_score(db, attempt_id)
    
    # Determine status based on due date
    status = AttemptStatus.SUBMITTED
    if attempt.assignment.due_at and datetime.utcnow() > attempt.assignment.due_at:
        status = AttemptStatus.LATE
    
    # Update attempt
    attempt.submitted_at = datetime.utcnow()
    attempt.total_score = total_score
    attempt.max_possible_score = max_possible_score
    attempt.status = status
    
    await db.commit()
    await db.refresh(attempt)
    
    return AttemptSchema.from_orm(attempt)


@router.get("/my", response_model=List[AttemptSummary])
async def get_my_attempts(
    db: AsyncSession = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    """Get all attempts by the current student."""
    query = select(Attempt).options(
        selectinload(Attempt.assignment)
    ).where(
        Attempt.student_id == current_student.id
    ).order_by(Attempt.started_at.desc())
    
    result = await db.execute(query)
    attempts = result.scalars().all()
    
    return [
        AttemptSummary(
            id=attempt.id,
            assignment_title=attempt.assignment.title,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            total_score=attempt.total_score,
            max_possible_score=attempt.max_possible_score,
            status=attempt.status,
            score_percentage=attempt.score_percentage
        )
        for attempt in attempts
    ]


@router.get("/{attempt_id}", response_model=AttemptDetail)
async def get_attempt_detail(
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    """Get detailed information about an attempt."""
    query = select(Attempt).options(
        selectinload(Attempt.assignment),
        selectinload(Attempt.student),
        selectinload(Attempt.responses).selectinload(Response.question)
    ).where(
        Attempt.id == attempt_id,
        Attempt.student_id == current_student.id
    )
    
    result = await db.execute(query)
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found"
        )
    
    # Only show details for completed attempts
    if attempt.status == AttemptStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot view details of in-progress attempt"
        )
    
    # Format response data
    from app.schemas.attempt import ResponseWithQuestion
    
    responses_with_questions = []
    for response in attempt.responses:
        responses_with_questions.append(ResponseWithQuestion(
            id=response.id,
            attempt_id=response.attempt_id,
            question_id=response.question_id,
            chosen_option=response.chosen_option,
            time_taken_seconds=response.time_taken_seconds,
            is_correct=response.is_correct,
            answered_at=response.answered_at,
            question_prompt=response.question.prompt_text,
            question_points=response.question.points,
            correct_option=response.question.correct_option.value
        ))
    
    attempt_dict = AttemptSchema.from_orm(attempt).dict()
    attempt_dict.update({
        "assignment_title": attempt.assignment.title,
        "student_name": attempt.student.full_name,
        "responses": responses_with_questions
    })
    
    return AttemptDetail(**attempt_dict)


@router.get("/assignment/{assignment_id}/my", response_model=AttemptSchema)
async def get_my_assignment_attempt(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    """Get student's attempt for a specific assignment."""
    # Check if student is enrolled in the classroom
    assignment_query = select(Assignment).options(
        selectinload(Assignment.classroom)
    ).where(Assignment.id == assignment_id)
    
    assignment_result = await db.execute(assignment_query)
    assignment = assignment_result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check enrollment
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
    
    # Get attempt
    attempt_query = select(Attempt).where(
        Attempt.assignment_id == assignment_id,
        Attempt.student_id == current_student.id
    )
    attempt_result = await db.execute(attempt_query)
    attempt = attempt_result.scalar_one_or_none()
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No attempt found for this assignment"
        )
    
    return AttemptSchema.from_orm(attempt)
