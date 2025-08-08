from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime
from ...db.session import get_db
from .auth import get_current_user, CurrentUser
from ...models.user import UserRole
from ...models.question import Question
from ...models.assignment import Assignment
from ...models.attempt import Attempt, AttemptStatus
from ...models.classroom import Classroom
from ...schemas.assignment import AssignmentCreate, AssignmentOut, AssignmentSummary

router = APIRouter(prefix="/assignments", tags=["assignments"])

@router.post("", response_model=AssignmentOut)
def create_assignment(payload: AssignmentCreate, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can create assignments")
    a = Assignment(**payload.model_dump(), created_by=user.id)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a

@router.get("/all", response_model=list[AssignmentSummary])
def get_all_assignments(db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can view assignments")
    
    # Get current time for determining if assignment is active
    now = datetime.utcnow()
    
    # Build complex query with aggregated data
    assignments_query = (
        db.query(
            Assignment.id,
            Assignment.classroom_id,
            Assignment.title,
            Assignment.description,
            Assignment.opens_at,
            Assignment.due_at,
            Assignment.shuffle_questions,
            Assignment.created_at,
            Classroom.name.label('classroom_name'),
            func.count(Question.id).label('total_questions'),
            func.count(Attempt.id).label('total_attempts'),
            func.count(func.distinct(Attempt.student_id)).label('unique_students_attempted'),
            func.sum(
                case(
                    (Attempt.status == AttemptStatus.SUBMITTED.value, 1),
                    else_=0
                )
            ).label('completed_attempts'),
            func.avg(
                case(
                    (Attempt.status == AttemptStatus.SUBMITTED.value, Attempt.total_score),
                    else_=None
                )
            ).label('average_score'),
            case(
                (Assignment.opens_at.is_(None), True),  # No open time means always open
                (Assignment.due_at.is_(None), Assignment.opens_at <= now),  # No due date, check only open time
                else_=(Assignment.opens_at <= now) & (Assignment.due_at >= now)
            ).label('is_active')
        )
        .join(Classroom, Assignment.classroom_id == Classroom.id)
        .outerjoin(Question, Assignment.id == Question.assignment_id)
        .outerjoin(Attempt, Assignment.id == Attempt.assignment_id)
        .filter(Assignment.created_by == user.id)
        .group_by(
            Assignment.id,
            Assignment.classroom_id,
            Assignment.title,
            Assignment.description,
            Assignment.opens_at,
            Assignment.due_at,
            Assignment.shuffle_questions,
            Assignment.created_at,
            Classroom.name
        )
        .order_by(Assignment.created_at.desc())
    )
    
    assignments_data = assignments_query.all()
    
    # Convert to list of dictionaries for the response model
    assignments_list = []
    for row in assignments_data:
        assignments_list.append({
            'id': row.id,
            'classroom_id': row.classroom_id,
            'title': row.title,
            'description': row.description,
            'opens_at': row.opens_at,
            'due_at': row.due_at,
            'shuffle_questions': row.shuffle_questions,
            'created_at': row.created_at,
            'classroom_name': row.classroom_name,
            'total_questions': row.total_questions or 0,
            'total_attempts': row.total_attempts or 0,
            'unique_students_attempted': row.unique_students_attempted or 0,
            'completed_attempts': row.completed_attempts or 0,
            'average_score': float(row.average_score) if row.average_score is not None else None,
            'is_active': row.is_active
        })
    
    return assignments_list

@router.get("/{assignment_id}")
def get_assignment(
    assignment_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    a = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not a:
        raise HTTPException(404, "assignment not found")

    # fetch questions ordered
    qs = (
        db.query(Question)
        .filter(Question.assignment_id == assignment_id)
        .order_by(Question.order_index.asc())
        .all()
    )

    is_teacher = user.role == UserRole.TEACHER.value

    questions_payload = []
    for q in qs:
        item = {
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
        if is_teacher:
            item["correct_option"] = q.correct_option.value  # visible to teachers only
        questions_payload.append(item)

    return {
        "id": str(a.id),
        "title": a.title,
        "classroom_id": str(a.classroom_id),
        "questions": questions_payload,
    }

@router.delete("/{assignment_id}")
def delete_assignment(assignment_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    a = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not a:
        raise HTTPException(404, "assignment not found")
    db.delete(a)
    db.commit()
    return {"message": "Assignment deleted successfully"}
