import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ...db.session import get_db
from .auth import get_current_user, CurrentUser
from ...models.user import UserRole, User
from ...models.classroom import Classroom, ClassroomMember
from ...models.assignment import Assignment
from ...models.attempt import Attempt, AttemptStatus, Response
from ...models.question import Question
from ...schemas.classroom import ClassroomCreate, ClassroomOut

router = APIRouter(prefix="/teachers", tags=["teachers"])

@router.post("/classrooms", response_model=ClassroomOut)
def create_classroom(payload: ClassroomCreate, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can create classrooms")
    code = secrets.token_urlsafe(6)
    c = Classroom(name=payload.name, code=code, teacher_id=user.id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@router.get("/classrooms/all")
def list_classrooms(db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can list classrooms")
    classrooms = db.query(Classroom).filter(Classroom.teacher_id == user.id).all()
    return {"count": len(classrooms), "classrooms": [{"id": c.id, "name": c.name, "code": c.code} for c in classrooms]}


@router.get("/classrooms/{classroom_id}/members")
def list_members(classroom_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id, Classroom.teacher_id == user.id).first()
    if not classroom:
        raise HTTPException(404, "classroom not found")
    members = db.query(ClassroomMember).filter(ClassroomMember.classroom_id == classroom_id).all()
    return {"count": len(members), "members": [{"student_id": m.student_id} for m in members]}

@router.get("/students/comprehensive-report")
def get_comprehensive_student_report(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get comprehensive information for all students in teacher's classrooms including 
    enrollment details and complete assignment results with question-by-question analysis.
    """
    
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can access comprehensive student reports")
    
    # Get all students who are enrolled in any of the teacher's classrooms
    students = (
        db.query(User)
        .join(ClassroomMember, User.id == ClassroomMember.student_id)
        .join(Classroom, ClassroomMember.classroom_id == Classroom.id)
        .filter(
            User.role == UserRole.STUDENT.value,
            Classroom.teacher_id == user.id
        )
        .distinct()
        .all()
    )
    
    if not students:
        return {"message": "No students found in your classrooms", "students": []}
    
    comprehensive_report = []
    
    for student in students:
        # Get student's classroom enrollments
        student_classrooms = (
            db.query(Classroom, ClassroomMember.joined_at)
            .join(ClassroomMember, Classroom.id == ClassroomMember.classroom_id)
            .filter(ClassroomMember.student_id == student.id)
            .all()
        )
        
        # Filter classrooms to only those taught by current teacher
        teacher_classrooms = [
            {
                "classroom_id": str(classroom.id),
                "classroom_name": classroom.name,
                "classroom_code": classroom.code,
                "joined_at": joined_at
            }
            for classroom, joined_at in student_classrooms 
            if classroom.teacher_id == user.id
        ]
        
        # Get assignments for this student in teacher's classrooms
        teacher_classroom_ids = [tc["classroom_id"] for tc in teacher_classrooms]
        
        if not teacher_classroom_ids:
            # Student not in any of teacher's classrooms
            continue
            
        assignments = (
            db.query(Assignment)
            .filter(
                Assignment.classroom_id.in_(teacher_classroom_ids),
                Assignment.created_by == user.id  # Only teacher's assignments
            )
            .order_by(Assignment.created_at.desc())
            .all()
        )
        
        # Get student's attempts for these assignments
        assignment_ids = [str(a.id) for a in assignments]
        student_attempts = {}
        
        if assignment_ids:
            attempts = (
                db.query(Attempt)
                .filter(
                    Attempt.student_id == student.id,
                    Attempt.assignment_id.in_(assignment_ids)
                )
                .all()
            )
            student_attempts = {str(attempt.assignment_id): attempt for attempt in attempts}
        
        # Process each assignment with detailed results
        assignment_results = []
        
        for assignment in assignments:
            assignment_id = str(assignment.id)
            attempt = student_attempts.get(assignment_id)
            
            # Get classroom info for this assignment
            assignment_classroom = next(
                (tc for tc in teacher_classrooms if tc["classroom_id"] == str(assignment.classroom_id)), 
                None
            )
            
            # Get all questions for this assignment
            questions = (
                db.query(Question)
                .filter(Question.assignment_id == assignment.id)
                .order_by(Question.order_index)
                .all()
            )
            
            # Calculate max possible score
            max_possible_score = sum(q.points for q in questions)
            
            # Prepare assignment result
            assignment_result = {
                "assignment_id": assignment_id,
                "assignment_title": assignment.title,
                "assignment_description": assignment.description,
                "classroom_name": assignment_classroom["classroom_name"] if assignment_classroom else "Unknown",
                "created_at": assignment.created_at,
                "opens_at": assignment.opens_at,
                "due_at": assignment.due_at,
                "max_possible_score": max_possible_score,
                "total_questions": len(questions),
                "attempt_status": "NOT_ATTEMPTED",
                "student_score": None,
                "percentage": None,
                "started_at": None,
                "submitted_at": None,
                "question_details": []
            }
            
            if attempt:
                assignment_result.update({
                    "attempt_status": attempt.status.value,
                    "student_score": attempt.total_score,
                    "percentage": (attempt.total_score / max_possible_score * 100) if max_possible_score > 0 else 0,
                    "started_at": attempt.started_at,
                    "submitted_at": attempt.submitted_at
                })
                
                # Get student responses for detailed question analysis
                if attempt.status in [AttemptStatus.SUBMITTED.value, AttemptStatus.LATE.value]:
                    responses = (
                        db.query(Response)
                        .filter(Response.attempt_id == attempt.id)
                        .all()
                    )
                    responses_dict = {str(resp.question_id): resp for resp in responses}
                    
                    # Build detailed question results
                    for question in questions:
                        response = responses_dict.get(str(question.id))
                        question_detail = {
                            "question_id": str(question.id),
                            "question_text": question.prompt_text,
                            "image_key": question.image_key,
                            "order_index": question.order_index,
                            "points": question.points,
                            "option_a": question.option_a,
                            "option_b": question.option_b,
                            "option_c": question.option_c,
                            "option_d": question.option_d,
                            "correct_option": question.correct_option.value,
                            "student_answer": response.chosen_option if response else None,
                            "is_correct": response.is_correct if response else False,
                            "points_earned": question.points if (response and response.is_correct) else 0,
                            "time_taken_seconds": response.time_taken_seconds if response else None
                        }
                        assignment_result["question_details"].append(question_detail)
                else:
                    # For in-progress attempts, don't show answers
                    for question in questions:
                        question_detail = {
                            "question_id": str(question.id),
                            "question_text": question.prompt_text,
                            "image_key": question.image_key,
                            "order_index": question.order_index,
                            "points": question.points,
                            "status": "IN_PROGRESS - Answers not available until submitted"
                        }
                        assignment_result["question_details"].append(question_detail)
            else:
                # No attempt made - show basic question info
                for question in questions:
                    question_detail = {
                        "question_id": str(question.id),
                        "question_text": question.prompt_text,
                        "image_key": question.image_key,
                        "order_index": question.order_index,
                        "points": question.points,
                        "status": "NOT_ATTEMPTED"
                    }
                    assignment_result["question_details"].append(question_detail)
            
            assignment_results.append(assignment_result)
        
        # Calculate overall statistics
        attempted_assignments = [ar for ar in assignment_results if ar["attempt_status"] != "NOT_ATTEMPTED"]
        completed_assignments = [ar for ar in assignment_results if ar["attempt_status"] in ["SUBMITTED", "LATE"]]
        
        total_points_earned = sum(ar["student_score"] or 0 for ar in completed_assignments)
        total_possible_points = sum(ar["max_possible_score"] for ar in completed_assignments)
        overall_percentage = (total_points_earned / total_possible_points * 100) if total_possible_points > 0 else 0
        
        student_report = {
            "student_info": {
                "student_id": str(student.id),
                "student_name": student.full_name,
                "student_email": student.email,
                "created_at": student.created_at
            },
            "classroom_enrollments": teacher_classrooms,
            "statistics": {
                "total_assignments": len(assignment_results),
                "attempted_assignments": len(attempted_assignments),
                "completed_assignments": len(completed_assignments),
                "total_points_earned": total_points_earned,
                "total_possible_points": total_possible_points,
                "overall_percentage": round(overall_percentage, 2)
            },
            "assignment_results": assignment_results
        }
        
        comprehensive_report.append(student_report)
    
    return {
        "teacher_id": str(user.id),
        "teacher_name": user.full_name,
        "total_students": len(comprehensive_report),
        "students": comprehensive_report
    }

@router.delete("/classrooms/{classroom_id}")
def delete_classroom(classroom_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    if user.role != UserRole.TEACHER.value:
        raise HTTPException(403, "Only teachers can delete classrooms")
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id, Classroom.teacher_id == user.id).first()
    if not classroom:
        raise HTTPException(404, "classroom not found")
    db.delete(classroom)
    db.commit()
    return {"message": "Classroom deleted successfully"}