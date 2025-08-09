from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from ...db.session import get_db
from .auth import get_current_user, CurrentUser
from ...models.user import UserRole, User
from ...models.assignment import Assignment
from ...models.attempt import Attempt, AttemptStatus, Response
from ...models.question import Question
from ...schemas.question import StartAttemptResponse, AnswerRequest
from ...schemas.attempt import StudentAttemptResult
from datetime import datetime, timezone

router = APIRouter(prefix="/attempts", tags=["attempts"])

@router.post("/start/{assignment_id}", response_model=StartAttemptResponse)
def start_attempt(assignment_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if user.role != UserRole.STUDENT.value:
        raise HTTPException(403, "Only students can start attempts")
    a = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not a:
        raise HTTPException(404, "assignment not found")
    # ensure one attempt per student
    existing = db.query(Attempt).filter(and_(Attempt.assignment_id==assignment_id, Attempt.student_id==user.id)).first()
    if existing:
        att = existing
    else:
        att = Attempt(assignment_id=assignment_id, student_id=user.id)
        db.add(att)
        db.commit()
        db.refresh(att)
    # fetch questions (hide correct_option)
    qs = db.query(Question).filter(Question.assignment_id==assignment_id).order_by(Question.order_index.asc()).all()
    questions_payload = [
        {
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
        for q in qs
    ]
    return StartAttemptResponse(attempt_id=att.id, questions=questions_payload)

@router.post("/{attempt_id}/answer")
def answer_question(attempt_id: str, payload: AnswerRequest, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    att = db.query(Attempt).filter(Attempt.id==attempt_id, Attempt.student_id==user.id).first()
    if not att or att.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(400, "Invalid attempt")
    q = db.query(Question).filter(Question.id==payload.question_id).first()
    if not q:
        raise HTTPException(404, "question not found")
    
    # Check if this question belongs to the assignment
    if q.assignment_id != att.assignment_id:
        raise HTTPException(400, "Question does not belong to this assignment")
    
    # Record the answer
    is_correct = payload.chosen_option == q.correct_option.value  # Boolean instead of 1/0
    existing = db.query(Response).filter(Response.attempt_id==att.id, Response.question_id==q.id).first()
    if existing:
        existing.chosen_option = payload.chosen_option
        existing.is_correct = is_correct
        existing.time_taken_seconds = payload.time_taken_seconds
    else:
        db.add(Response(
            attempt_id=att.id, 
            question_id=q.id, 
            chosen_option=payload.chosen_option, 
            is_correct=is_correct, 
            time_taken_seconds=payload.time_taken_seconds
        ))
    
    # Check if all questions have been answered
    total_questions = db.query(func.count(Question.id)).filter(Question.assignment_id == att.assignment_id).scalar()
    answered_questions = db.query(func.count(Response.id)).filter(Response.attempt_id == att.id).scalar()
    
    # If all questions are answered, auto-submit the attempt
    if answered_questions >= total_questions:
        # Calculate total score (sum points for correct answers)
        total_score = db.query(func.sum(Question.points)).join(
            Response, Question.id == Response.question_id
        ).filter(
            Response.attempt_id == att.id,
            Response.is_correct == True  # Boolean True instead of 1
        ).scalar() or 0
        
        # Update attempt status to submitted
        att.status = AttemptStatus.SUBMITTED
        att.submitted_at = datetime.now(timezone.utc)
        att.total_score = total_score
        
        db.commit()
        return {"message": "Answer recorded. Assignment completed and submitted automatically!", "auto_submitted": True}
    
    db.commit()
    return {"message": "Answer recorded successfully", "auto_submitted": False}

@router.post("/{attempt_id}/submit")
def submit_attempt(
    attempt_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Manually submit an attempt (finish the assignment)"""
    # Get the attempt and verify ownership
    attempt = db.query(Attempt).filter(
        Attempt.id == attempt_id,
        Attempt.student_id == user.id
    ).first()
    
    if not attempt:
        raise HTTPException(404, "Attempt not found or you don't have permission to access it")
    
    # Check if attempt is still in progress
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(400, f"Attempt is already {attempt.status.value.lower()}")
    
    # Only students can submit attempts
    if user.role != UserRole.STUDENT.value:
        raise HTTPException(403, "Only students can submit attempts")
    
    # Calculate total score based on current responses
    total_score = db.query(func.sum(Question.points)).join(
        Response, Question.id == Response.question_id
    ).filter(
        Response.attempt_id == attempt_id,
        Response.is_correct == True
    ).scalar() or 0
    
    # Get assignment info for due date checking
    assignment = db.query(Assignment).filter(Assignment.id == attempt.assignment_id).first()
    
    # Determine if submission is late
    submission_time = datetime.now(timezone.utc)
    status = AttemptStatus.SUBMITTED
    
    if assignment and assignment.due_at and submission_time > assignment.due_at:
        status = AttemptStatus.LATE
    
    # Update attempt with final details
    attempt.status = status
    attempt.submitted_at = submission_time
    attempt.total_score = total_score
    
    # Get some stats for the response
    total_questions = db.query(func.count(Question.id)).filter(
        Question.assignment_id == attempt.assignment_id
    ).scalar() or 0
    
    answered_questions = db.query(func.count(Response.id)).filter(
        Response.attempt_id == attempt_id
    ).scalar() or 0
    
    db.commit()
    
    return {
        "message": "Assignment submitted successfully!",
        "status": status.value,
        "total_score": total_score,
        "questions_answered": answered_questions,
        "total_questions": total_questions,
        "submitted_at": submission_time,
        "is_late": status == AttemptStatus.LATE
    }

@router.get("/{attempt_id}/result", response_model=StudentAttemptResult)
def get_student_attempt_result(
    attempt_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Get detailed results for a specific student's attempt"""
    # Get the attempt
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(404, "Attempt not found")
    
    # Check permissions - students can only view their own attempts, teachers can view attempts for their assignments
    if user.role == UserRole.STUDENT.value:
        if attempt.student_id != user.id:
            raise HTTPException(403, "You can only view your own attempt results")
    elif user.role == UserRole.TEACHER.value:
        # Check if the teacher created this assignment
        assignment = db.query(Assignment).filter(Assignment.id == attempt.assignment_id).first()
        if not assignment or assignment.created_by != user.id:
            raise HTTPException(403, "You can only view results for assignments you created")
    
    # Get assignment and student info
    assignment = db.query(Assignment).filter(Assignment.id == attempt.assignment_id).first()
    student = db.query(User).filter(User.id == attempt.student_id).first()
    
    # Calculate max possible score
    max_possible_score = db.query(func.sum(Question.points)).filter(Question.assignment_id == attempt.assignment_id).scalar() or 0
    
    # Calculate percentage
    percentage = (attempt.total_score / max_possible_score * 100) if max_possible_score > 0 else 0
    
    # Calculate time taken
    time_taken_minutes = None
    if attempt.started_at and attempt.submitted_at:
        time_delta = attempt.submitted_at - attempt.started_at
        time_taken_minutes = time_delta.total_seconds() / 60
    
    # Get detailed responses
    responses_data = (
        db.query(
            Response.question_id,
            Response.chosen_option,
            Response.is_correct,
            Response.time_taken_seconds,
            Question.prompt_text,
            Question.option_a,
            Question.option_b,
            Question.option_c,
            Question.option_d,
            Question.correct_option,
            Question.points,
            Question.order_index
        )
        .join(Question, Response.question_id == Question.id)
        .filter(Response.attempt_id == attempt_id)
        .order_by(Question.order_index)
        .all()
    )
    
    responses = []
    for row in responses_data:
        response = {
            "question_id": str(row.question_id),
            "prompt_text": row.prompt_text,
            "option_a": row.option_a,
            "option_b": row.option_b,
            "option_c": row.option_c,
            "option_d": row.option_d,
            "chosen_option": row.chosen_option,
            "correct_option": row.correct_option.value,
            "is_correct": bool(row.is_correct),  # Ensure it's a boolean
            "points_earned": row.points if row.is_correct else 0,
            "max_points": row.points,
            "time_taken_seconds": row.time_taken_seconds,
            "order_index": row.order_index
        }
        responses.append(response)
    
    return {
        "attempt_id": attempt.id,
        "assignment_id": attempt.assignment_id,
        "assignment_title": assignment.title,
        "student_id": attempt.student_id,
        "student_name": student.full_name,
        "status": attempt.status.value,
        "total_score": attempt.total_score,
        "max_possible_score": max_possible_score,
        "percentage": percentage,
        "started_at": attempt.started_at,
        "submitted_at": attempt.submitted_at,
        "time_taken_minutes": time_taken_minutes,
        "responses": responses
    }
