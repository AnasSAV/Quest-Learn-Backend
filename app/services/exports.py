import csv
import io
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.attempt import Attempt, Response
from app.models.assignment import Assignment
from app.models.question import Question
from app.models.user import User


class ExportsService:
    @staticmethod
    async def export_assignment_results_csv(
        db: AsyncSession,
        assignment_id: int
    ) -> str:
        """
        Export assignment results to CSV format.
        
        Returns:
            CSV content as string
        """
        # Get assignment with all related data
        assignment_query = select(Assignment).options(
            selectinload(Assignment.questions)
        ).where(Assignment.id == assignment_id)
        assignment_result = await db.execute(assignment_query)
        assignment = assignment_result.scalar_one()
        
        # Get all attempts with responses
        attempts_query = select(Attempt).options(
            selectinload(Attempt.student),
            selectinload(Attempt.responses).selectinload(Response.question)
        ).where(
            Attempt.assignment_id == assignment_id,
            Attempt.status.in_(["SUBMITTED", "LATE"])
        )
        attempts_result = await db.execute(attempts_query)
        attempts = attempts_result.scalars().all()
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Prepare headers
        headers = [
            "Student Name",
            "Student Email",
            "Started At",
            "Submitted At",
            "Duration (minutes)",
            "Status",
            "Total Score",
            "Max Possible Score",
            "Score Percentage"
        ]
        
        # Add question headers
        questions = sorted(assignment.questions, key=lambda q: q.order_index)
        for i, question in enumerate(questions, 1):
            headers.extend([
                f"Q{i} Answer",
                f"Q{i} Correct",
                f"Q{i} Time (seconds)",
                f"Q{i} Points Earned"
            ])
        
        writer.writerow(headers)
        
        # Write attempt data
        for attempt in attempts:
            # Create response lookup by question_id
            responses_by_question = {r.question_id: r for r in attempt.responses}
            
            row = [
                attempt.student.full_name,
                attempt.student.email,
                attempt.started_at.isoformat(),
                attempt.submitted_at.isoformat() if attempt.submitted_at else "",
                round(attempt.duration_seconds / 60, 2) if attempt.duration_seconds else "",
                attempt.status.value,
                attempt.total_score,
                attempt.max_possible_score,
                round(attempt.score_percentage, 2)
            ]
            
            # Add question response data
            for question in questions:
                response = responses_by_question.get(question.id)
                if response:
                    points_earned = question.points if response.is_correct else 0
                    row.extend([
                        response.chosen_option,
                        "Yes" if response.is_correct else "No",
                        response.time_taken_seconds,
                        points_earned
                    ])
                else:
                    # No response for this question
                    row.extend(["", "", "", ""])
            
            writer.writerow(row)
        
        return output.getvalue()

    @staticmethod
    async def export_question_statistics_csv(
        db: AsyncSession,
        assignment_id: int
    ) -> str:
        """
        Export question-level statistics to CSV format.
        """
        # Get questions for the assignment
        questions_query = select(Question).where(
            Question.assignment_id == assignment_id
        ).order_by(Question.order_index)
        questions_result = await db.execute(questions_query)
        questions = questions_result.scalars().all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        headers = [
            "Question #",
            "Question Text",
            "Correct Answer",
            "Points",
            "Total Responses",
            "Correct Responses",
            "Accuracy Rate (%)",
            "Average Time (seconds)",
            "Option A Count",
            "Option B Count", 
            "Option C Count",
            "Option D Count"
        ]
        writer.writerow(headers)
        
        # Get response statistics for each question
        for i, question in enumerate(questions, 1):
            # Get all responses for this question
            responses_query = select(Response).where(Response.question_id == question.id)
            responses_result = await db.execute(responses_query)
            responses = responses_result.scalars().all()
            
            if not responses:
                row = [
                    i,
                    question.prompt_text or f"Question {i}",
                    question.correct_option.value,
                    question.points,
                    0, 0, 0, 0, 0, 0, 0, 0
                ]
            else:
                correct_responses = sum(1 for r in responses if r.is_correct)
                total_responses = len(responses)
                accuracy_rate = (correct_responses / total_responses) * 100
                average_time = sum(r.time_taken_seconds for r in responses) / total_responses
                
                # Count option selections
                option_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
                for response in responses:
                    if response.chosen_option in option_counts:
                        option_counts[response.chosen_option] += 1
                
                row = [
                    i,
                    question.prompt_text or f"Question {i}",
                    question.correct_option.value,
                    question.points,
                    total_responses,
                    correct_responses,
                    round(accuracy_rate, 2),
                    round(average_time, 2),
                    option_counts["A"],
                    option_counts["B"],
                    option_counts["C"],
                    option_counts["D"]
                ]
            
            writer.writerow(row)
        
        return output.getvalue()

    @staticmethod
    async def export_classroom_summary_csv(
        db: AsyncSession,
        classroom_id: int
    ) -> str:
        """
        Export classroom assignment summary to CSV format.
        """
        # Get all assignments for the classroom
        assignments_query = select(Assignment).where(
            Assignment.classroom_id == classroom_id
        ).order_by(Assignment.created_at)
        assignments_result = await db.execute(assignments_query)
        assignments = assignments_result.scalars().all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        headers = [
            "Assignment Title",
            "Created Date",
            "Opens At",
            "Due At",
            "Total Questions",
            "Total Points",
            "Total Attempts",
            "Average Score (%)",
            "Completion Rate (%)"
        ]
        writer.writerow(headers)
        
        # Get classroom member count
        from app.models.classroom import ClassroomMember
        from sqlalchemy import func
        
        members_query = select(func.count(ClassroomMember.id)).where(
            ClassroomMember.classroom_id == classroom_id
        )
        members_result = await db.execute(members_query)
        total_students = members_result.scalar() or 0
        
        for assignment in assignments:
            # Get assignment statistics
            attempts_query = select(Attempt).where(
                Attempt.assignment_id == assignment.id,
                Attempt.status.in_(["SUBMITTED", "LATE"])
            )
            attempts_result = await db.execute(attempts_query)
            attempts = attempts_result.scalars().all()
            
            questions_query = select(func.count(Question.id)).where(
                Question.assignment_id == assignment.id
            )
            questions_result = await db.execute(questions_query)
            total_questions = questions_result.scalar() or 0
            
            total_points_query = select(func.sum(Question.points)).where(
                Question.assignment_id == assignment.id
            )
            total_points_result = await db.execute(total_points_query)
            total_points = total_points_result.scalar() or 0
            
            # Calculate statistics
            total_attempts = len(attempts)
            average_score = sum(attempt.score_percentage for attempt in attempts) / total_attempts if attempts else 0
            completion_rate = (total_attempts / total_students * 100) if total_students > 0 else 0
            
            row = [
                assignment.title,
                assignment.created_at.date().isoformat(),
                assignment.opens_at.isoformat() if assignment.opens_at else "",
                assignment.due_at.isoformat() if assignment.due_at else "",
                total_questions,
                total_points,
                total_attempts,
                round(average_score, 2),
                round(completion_rate, 2)
            ]
            
            writer.writerow(row)
        
        return output.getvalue()


# Global exports service instance
exports_service = ExportsService()
