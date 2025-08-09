from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime
from ...db.session import get_db
from .auth import get_current_user, CurrentUser
from ...models.user import UserRole, User
from ...models.question import Question
from ...models.assignment import Assignment
from ...models.attempt import Attempt, AttemptStatus, Response
from ...models.classroom import Classroom
from ...schemas.assignment import AssignmentCreate, AssignmentOut, AssignmentSummary
from ...schemas.question import QuestionOut
from ...schemas.attempt import AssignmentResults, StudentAttemptResult

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

@router.get("/classroom/{classroom_id}", response_model=list[AssignmentSummary])
def get_assignments_by_classroom(
    classroom_id: str,
    student_id: str = None,  # Optional query parameter
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Get all assignments for a specific classroom with detailed statistics and optional student status"""
    # Verify the classroom exists
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(404, "Classroom not found")
    
    # Get current time for determining if assignment is active
    now = datetime.utcnow()
    
    # Build the base query with different filters based on user role
    base_query = (
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
        .filter(Assignment.classroom_id == classroom_id)
    )
    
    # Apply role-based filtering
    if user.role == UserRole.TEACHER.value:
        assignments_query = base_query.filter(Assignment.created_by == user.id)
    else:
        assignments_query = base_query
    
    assignments_query = (
        assignments_query
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
    
    # If student_id is provided, get student-specific attempt status for each assignment
    student_attempts = {}
    if student_id:
        # Verify student_id access permissions
        if user.role == UserRole.STUDENT.value and str(user.id) != student_id:
            raise HTTPException(403, "Students can only view their own assignment status")
        
        # Get all attempts by this student for assignments in this classroom
        student_attempt_data = (
            db.query(
                Attempt.assignment_id,
                Attempt.status,
                Attempt.total_score,
                Attempt.submitted_at,
                Attempt.started_at
            )
            .filter(
                Attempt.student_id == student_id,
                Attempt.assignment_id.in_([row.id for row in assignments_data])
            )
            .all()
        )
        
        # Create a lookup dictionary for student attempts
        student_attempts = {
            str(attempt.assignment_id): {
                "status": attempt.status.value,
                "total_score": attempt.total_score,
                "submitted_at": attempt.submitted_at,
                "started_at": attempt.started_at,
                "is_submitted": attempt.status in [AttemptStatus.SUBMITTED.value, AttemptStatus.LATE.value]
            }
            for attempt in student_attempt_data
        }
    
    # Convert to list of dictionaries for the response model
    assignments_list = []
    for row in assignments_data:
        assignment_dict = {
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
        }
        
        # Add student-specific status if student_id was provided
        if student_id:
            assignment_id = str(row.id)
            if assignment_id in student_attempts:
                attempt_info = student_attempts[assignment_id]
                assignment_dict.update({
                    'student_status': attempt_info['status'],
                    'student_score': attempt_info['total_score'],
                    'student_submitted_at': attempt_info['submitted_at'],
                    'student_started_at': attempt_info['started_at'],
                    'is_submitted_by_student': attempt_info['is_submitted']
                })
            else:
                # Student hasn't started this assignment
                assignment_dict.update({
                    'student_status': 'NOT_STARTED',
                    'student_score': None,
                    'student_submitted_at': None,
                    'student_started_at': None,
                    'is_submitted_by_student': False
                })
        
        assignments_list.append(assignment_dict)
    
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

@router.get("/{assignment_id}/questions", response_model=list[QuestionOut])
def get_assignment_questions(
    assignment_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Get all questions for a specific assignment"""
    # First verify the assignment exists
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(404, "Assignment not found")
    
    # Check if user has permission to view this assignment
    # Teachers can only view assignments they created
    # Students can view questions for assignments in their classrooms (handled separately)
    if user.role == UserRole.TEACHER.value:
        if assignment.created_by != user.id:
            raise HTTPException(403, "You can only view questions for assignments you created")
    else:
        # For students, we would need to check if they're enrolled in the classroom
        # This would require a classroom membership check
        raise HTTPException(403, "Students should access questions through attempt endpoints")
    
    # Fetch questions ordered by order_index
    questions = (
        db.query(Question)
        .filter(Question.assignment_id == assignment_id)
        .order_by(Question.order_index.asc())
        .all()
    )
    
    return questions

@router.get("/{assignment_id}/results", response_model=AssignmentResults)
def get_assignment_results(
    assignment_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Get detailed results for all students in a specific assignment"""
    # Verify the assignment exists and user has permission
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(404, "Assignment not found")
    
    # Only teachers can view assignment results
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can view assignment results")
    
    # Teachers can only view results for assignments they created
    if assignment.created_by != user.id:
        raise HTTPException(403, "You can only view results for assignments you created")
    
    # Get classroom info
    classroom = db.query(Classroom).filter(Classroom.id == assignment.classroom_id).first()
    
    # Calculate max possible score for the assignment
    total_points = db.query(func.sum(Question.points)).filter(Question.assignment_id == assignment_id).scalar() or 0
    
    # Get all students who have access to this assignment (assuming all users with STUDENT role for now)
    # In a real application, you'd want to filter by classroom enrollment
    students_query = db.query(User).filter(User.role == UserRole.STUDENT.value)
    
    # Get all attempts for this assignment with student info
    attempts_data = (
        db.query(
            User.id.label('student_id'),
            User.full_name.label('student_name'),
            User.email.label('student_email'),
            Attempt.id.label('attempt_id'),
            Attempt.status,
            Attempt.total_score,
            Attempt.started_at,
            Attempt.submitted_at
        )
        .outerjoin(Attempt, (User.id == Attempt.student_id) & (Attempt.assignment_id == assignment_id))
        .filter(User.role == UserRole.STUDENT.value)
        .all()
    )
    
    # Process the data into student results
    student_results = []
    students_attempted = 0
    students_completed = 0
    total_scores = []
    
    for row in attempts_data:
        # Calculate time taken if both start and submit times exist
        time_taken_minutes = None
        if row.started_at and row.submitted_at:
            time_delta = row.submitted_at - row.started_at
            time_taken_minutes = time_delta.total_seconds() / 60
        
        # Calculate percentage
        percentage = None
        if row.total_score is not None and total_points > 0:
            percentage = (row.total_score / total_points) * 100
        
        # Track statistics
        if row.attempt_id:
            students_attempted += 1
            if row.status == AttemptStatus.SUBMITTED.value:
                students_completed += 1
                total_scores.append(row.total_score)
        
        student_result = {
            'student_id': row.student_id,
            'student_name': row.student_name,
            'student_email': row.student_email,
            'attempt_id': row.attempt_id,
            'status': row.status,
            'total_score': row.total_score,
            'max_possible_score': total_points,
            'percentage': percentage,
            'started_at': row.started_at,
            'submitted_at': row.submitted_at,
            'time_taken_minutes': time_taken_minutes
        }
        student_results.append(student_result)
    
    # Calculate average score
    average_score = sum(total_scores) / len(total_scores) if total_scores else None
    
    return {
        'assignment_id': assignment.id,
        'assignment_title': assignment.title,
        'classroom_name': classroom.name if classroom else 'Unknown',
        'total_students': len(attempts_data),
        'students_attempted': students_attempted,
        'students_completed': students_completed,
        'average_score': average_score,
        'max_possible_score': total_points,
        'student_results': student_results
    }

@router.get("/{assignment_id}/student/{student_id}/result", response_model=StudentAttemptResult)
def get_student_assignment_result(
    assignment_id: str,
    student_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Get detailed results for a specific student's assignment attempt"""
    # Verify the assignment exists
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(404, "Assignment not found")
    
    # Check permissions
    if user.role == UserRole.TEACHER.value:
        # Teachers can only view results for assignments they created
        if assignment.created_by != user.id:
            raise HTTPException(403, "You can only view results for assignments you created")
    elif user.role == UserRole.STUDENT.value:
        # Students can only view their own results
        if str(user.id) != student_id:
            raise HTTPException(403, "You can only view your own results")
    else:
        raise HTTPException(403, "Invalid user role")
    # Get the student's attempt for this assignment
    attempt = (
        db.query(Attempt)
        .filter(Attempt.assignment_id == assignment_id, Attempt.student_id == student_id)
        .first()
    )
    
    if not attempt:
        raise HTTPException(404, "No attempt found for this student and assignment")
    
    # Get student info
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(404, "Student not found")
    
    # Calculate max possible score
    max_possible_score = db.query(func.sum(Question.points)).filter(Question.assignment_id == assignment_id).scalar() or 0
    
    # Calculate percentage
    percentage = (attempt.total_score / max_possible_score * 100) if max_possible_score > 0 else 0
    
    # Calculate time taken
    time_taken_minutes = None
    if attempt.started_at and attempt.submitted_at:
        time_delta = attempt.submitted_at - attempt.started_at
        time_taken_minutes = time_delta.total_seconds() / 60
    
    # Get detailed responses (only if attempt is submitted)
    responses = []
    if attempt.status == AttemptStatus.SUBMITTED.value:
        responses_data = (
            db.query(
                Response.question_id,
                Response.chosen_option,
                Response.is_correct,
                Response.time_taken_seconds,
                Question.prompt_text,
                Question.image_key,  # Include image_key in query
                Question.option_a,
                Question.option_b,
                Question.option_c,
                Question.option_d,
                Question.correct_option,
                Question.points,
                Question.order_index
            )
            .join(Question, Response.question_id == Question.id)
            .filter(Response.attempt_id == attempt.id)
            .order_by(Question.order_index)
            .all()
        )
        
        for row in responses_data:
            response = {
                "question_id": str(row.question_id),
                "prompt_text": row.prompt_text,
                "image_key": row.image_key,  # Include image_key
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

@router.delete("/{assignment_id}")
def delete_assignment(assignment_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    a = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not a:
        raise HTTPException(404, "assignment not found")
    db.delete(a)
    db.commit()
    return {"message": "Assignment deleted successfully"}
