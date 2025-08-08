from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, get_current_teacher
from app.models.user import User
from app.models.assignment import Assignment
from app.models.attempt import Attempt, AttemptStatus
from app.schemas.attempt import AttemptDetail
from app.services.grading import grading_service
from app.services.exports import exports_service

router = APIRouter()


@router.get("/assignments/{assignment_id}/summary")
async def get_assignment_results_summary(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get summary statistics for an assignment."""
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
    
    # Get assignment statistics
    stats = await grading_service.get_assignment_statistics(db, assignment_id)
    
    return {
        "assignment_id": assignment_id,
        "assignment_title": assignment.title,
        "statistics": stats
    }


@router.get("/assignments/{assignment_id}/detailed", response_model=List[AttemptDetail])
async def get_assignment_detailed_results(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get detailed results for all attempts in an assignment."""
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
    
    # Get all completed attempts
    attempts_query = select(Attempt).options(
        selectinload(Attempt.student),
        selectinload(Attempt.responses).selectinload(
            lambda response: response.question
        )
    ).where(
        Attempt.assignment_id == assignment_id,
        Attempt.status.in_([AttemptStatus.SUBMITTED, AttemptStatus.LATE])
    ).order_by(Attempt.submitted_at.desc())
    
    attempts_result = await db.execute(attempts_query)
    attempts = attempts_result.scalars().all()
    
    # Format detailed results
    detailed_results = []
    for attempt in attempts:
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
        
        from app.schemas.attempt import Attempt as AttemptSchema
        attempt_dict = AttemptSchema.from_orm(attempt).dict()
        attempt_dict.update({
            "assignment_title": assignment.title,
            "student_name": attempt.student.full_name,
            "responses": responses_with_questions
        })
        
        detailed_results.append(AttemptDetail(**attempt_dict))
    
    return detailed_results


@router.get("/assignments/{assignment_id}/questions")
async def get_assignment_question_analytics(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get question-level analytics for an assignment."""
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
    
    # Get question statistics
    question_stats = await grading_service.get_question_statistics(db, assignment_id)
    
    return {
        "assignment_id": assignment_id,
        "assignment_title": assignment.title,
        "question_statistics": question_stats
    }


@router.get("/assignments/{assignment_id}/export/csv")
async def export_assignment_results_csv(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Export assignment results as CSV file."""
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
    
    # Generate CSV content
    csv_content = await exports_service.export_assignment_results_csv(db, assignment_id)
    
    # Create safe filename
    safe_title = "".join(c for c in assignment.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"assignment_{assignment_id}_{safe_title}_results.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/assignments/{assignment_id}/export/questions-csv")
async def export_question_statistics_csv(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Export question statistics as CSV file."""
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
    
    # Generate CSV content
    csv_content = await exports_service.export_question_statistics_csv(db, assignment_id)
    
    # Create safe filename
    safe_title = "".join(c for c in assignment.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"assignment_{assignment_id}_{safe_title}_questions.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/classrooms/{classroom_id}/export/summary-csv")
async def export_classroom_summary_csv(
    classroom_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Export classroom assignment summary as CSV file."""
    # Verify teacher owns the classroom
    from app.models.classroom import Classroom
    
    classroom_query = select(Classroom).where(
        Classroom.id == classroom_id,
        Classroom.teacher_id == current_teacher.id
    )
    classroom_result = await db.execute(classroom_query)
    classroom = classroom_result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )
    
    # Generate CSV content
    csv_content = await exports_service.export_classroom_summary_csv(db, classroom_id)
    
    # Create safe filename
    safe_name = "".join(c for c in classroom.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"classroom_{classroom_id}_{safe_name}_summary.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
