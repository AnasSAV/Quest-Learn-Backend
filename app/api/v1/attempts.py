from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ...db.session import get_db
from .auth import get_current_user, CurrentUser
from ...models.user import UserRole
from ...models.assignment import Assignment
from ...models.attempt import Attempt, AttemptStatus, Response
from ...models.question import Question
from ...schemas.question import StartAttemptResponse, AnswerRequest
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
    # naive timer check – frontend should enforce per-question timer; backend records time for analytics
    is_correct = 1 if payload.chosen_option == q.correct_option.value else 0
    existing = db.query(Response).filter(Response.attempt_id==att.id, Response.question_id==q.id).first()
    if existing:
        existing.chosen_option = payload.chosen_option
        existing.is_correct = is_correct
        existing.time_taken_seconds = payload.time_taken_seconds
    else:
        db.add(Response(attempt_id=att.id, question_id=q.id, chosen_option=payload.chosen_option, is_correct=is_correct, time_taken_seconds=payload.time_taken_seconds))
