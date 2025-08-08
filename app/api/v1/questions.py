from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, get_current_teacher
from app.models.user import User
from app.models.assignment import Assignment
from app.models.question import Question
from app.models.attempt import Attempt
from app.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    Question as QuestionSchema,
    QuestionWithStats
)

router = APIRouter()


@router.post("/", response_model=QuestionSchema)
async def create_question(
    question_data: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Create a new question for an assignment."""
    # Verify teacher owns the assignment
    assignment_query = select(Assignment).options(
        selectinload(Assignment.classroom)
    ).where(Assignment.id == question_data.assignment_id)
    
    assignment_result = await db.execute(assignment_query)
    assignment = assignment_result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    if assignment.classroom.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if assignment has attempts
    attempts_query = select(func.count(Attempt.id)).where(Attempt.assignment_id == question_data.assignment_id)
    attempts_result = await db.execute(attempts_query)
    attempt_count = attempts_result.scalar()
    
    if attempt_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add questions to assignment with existing attempts"
        )
    
    question = Question(
        assignment_id=question_data.assignment_id,
        prompt_text=question_data.prompt_text,
        image_url=question_data.image_url,
        option_a=question_data.option_a,
        option_b=question_data.option_b,
        option_c=question_data.option_c,
        option_d=question_data.option_d,
        correct_option=question_data.correct_option,
        per_question_seconds=question_data.per_question_seconds,
        points=question_data.points,
        order_index=question_data.order_index
    )
    
    db.add(question)
    await db.commit()
    await db.refresh(question)
    
    return QuestionSchema.from_orm(question)


@router.get("/{question_id}", response_model=QuestionSchema)
async def get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get question details."""
    query = select(Question).options(
        selectinload(Question.assignment).selectinload(Assignment.classroom)
    ).where(Question.id == question_id)
    
    result = await db.execute(query)
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Verify ownership
    if question.assignment.classroom.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return QuestionSchema.from_orm(question)


@router.put("/{question_id}", response_model=QuestionSchema)
async def update_question(
    question_id: int,
    question_data: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Update a question (only if no attempts exist)."""
    query = select(Question).options(
        selectinload(Question.assignment).selectinload(Assignment.classroom)
    ).where(Question.id == question_id)
    
    result = await db.execute(query)
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Verify ownership
    if question.assignment.classroom.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if assignment has attempts
    attempts_query = select(func.count(Attempt.id)).where(Attempt.assignment_id == question.assignment_id)
    attempts_result = await db.execute(attempts_query)
    attempt_count = attempts_result.scalar()
    
    if attempt_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify question in assignment with existing attempts"
        )
    
    # Update fields
    update_data = question_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)
    
    await db.commit()
    await db.refresh(question)
    
    return QuestionSchema.from_orm(question)


@router.get("/assignment/{assignment_id}", response_model=List[QuestionSchema])
async def get_assignment_questions(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get all questions for an assignment."""
    # Verify teacher owns the assignment
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
    
    if assignment.classroom.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get questions
    questions_query = select(Question).where(
        Question.assignment_id == assignment_id
    ).order_by(Question.order_index)
    
    questions_result = await db.execute(questions_query)
    questions = questions_result.scalars().all()
    
    return [QuestionSchema.from_orm(question) for question in questions]


@router.get("/assignment/{assignment_id}/stats", response_model=List[QuestionWithStats])
async def get_assignment_question_stats(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get question statistics for an assignment."""
    # Verify teacher owns the assignment
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
    
    if assignment.classroom.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get questions with statistics
    from app.models.attempt import Response
    from sqlalchemy import case
    
    query = select(
        Question,
        func.count(Response.id).label("total_responses"),
        func.sum(case((Response.is_correct == True, 1), else_=0)).label("correct_responses"),
        func.avg(Response.time_taken_seconds).label("average_time_seconds")
    ).outerjoin(
        Response, Question.id == Response.question_id
    ).where(
        Question.assignment_id == assignment_id
    ).group_by(Question.id).order_by(Question.order_index)
    
    result = await db.execute(query)
    rows = result.all()
    
    questions_with_stats = []
    for question, total_responses, correct_responses, avg_time in rows:
        accuracy_rate = (correct_responses / total_responses * 100) if total_responses > 0 else 0
        
        question_dict = QuestionSchema.from_orm(question).dict()
        question_dict.update({
            "total_responses": total_responses or 0,
            "correct_responses": correct_responses or 0,
            "accuracy_rate": round(accuracy_rate, 2),
            "average_time_seconds": round(avg_time, 2) if avg_time else 0
        })
        
        questions_with_stats.append(QuestionWithStats(**question_dict))
    
    return questions_with_stats


@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Delete a question (only if no attempts exist)."""
    query = select(Question).options(
        selectinload(Question.assignment).selectinload(Assignment.classroom)
    ).where(Question.id == question_id)
    
    result = await db.execute(query)
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Verify ownership
    if question.assignment.classroom.teacher_id != current_teacher.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if assignment has attempts
    attempts_query = select(func.count(Attempt.id)).where(Attempt.assignment_id == question.assignment_id)
    attempts_result = await db.execute(attempts_query)
    attempt_count = attempts_result.scalar()
    
    if attempt_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete question from assignment with existing attempts"
        )
    
    await db.delete(question)
    await db.commit()
    
    return {"message": "Question deleted successfully"}
