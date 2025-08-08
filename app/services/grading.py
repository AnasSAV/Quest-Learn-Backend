from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.attempt import Attempt, Response
from app.models.question import Question
from app.models.assignment import Assignment


class GradingService:
    @staticmethod
    async def grade_response(
        db: AsyncSession,
        question_id: int,
        chosen_option: str,
        time_taken_seconds: int
    ) -> tuple[bool, int]:
        """
        Grade a single response.
        
        Returns:
            tuple: (is_correct, points_earned)
        """
        question = await db.get(Question, question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found")
        
        is_correct = question.is_correct_answer(chosen_option)
        points_earned = question.points if is_correct else 0
        
        return is_correct, points_earned

    @staticmethod
    async def calculate_attempt_score(
        db: AsyncSession,
        attempt_id: int
    ) -> tuple[int, int]:
        """
        Calculate total score for an attempt.
        
        Returns:
            tuple: (total_score, max_possible_score)
        """
        # Get all responses for this attempt
        query = select(Response).where(Response.attempt_id == attempt_id)
        result = await db.execute(query)
        responses = result.scalars().all()
        
        if not responses:
            return 0, 0
        
        # Get question points for each response
        question_ids = [response.question_id for response in responses]
        question_query = select(Question).where(Question.id.in_(question_ids))
        question_result = await db.execute(question_query)
        questions = {q.id: q for q in question_result.scalars().all()}
        
        total_score = 0
        max_possible_score = 0
        
        for response in responses:
            question = questions.get(response.question_id)
            if question:
                max_possible_score += question.points
                if response.is_correct:
                    total_score += question.points
        
        return total_score, max_possible_score

    @staticmethod
    async def get_assignment_statistics(
        db: AsyncSession,
        assignment_id: int
    ) -> Dict[str, Any]:
        """
        Get comprehensive statistics for an assignment.
        """
        # Get all attempts for this assignment
        attempts_query = select(Attempt).where(
            Attempt.assignment_id == assignment_id,
            Attempt.status.in_(["SUBMITTED", "LATE"])
        )
        attempts_result = await db.execute(attempts_query)
        attempts = attempts_result.scalars().all()
        
        if not attempts:
            return {
                "total_attempts": 0,
                "average_score": 0,
                "highest_score": 0,
                "lowest_score": 0,
                "completion_rate": 0,
                "average_time_minutes": 0
            }
        
        # Calculate basic statistics
        scores = [attempt.score_percentage for attempt in attempts]
        durations = [attempt.duration_seconds for attempt in attempts if attempt.duration_seconds]
        
        # Get total enrolled students count (for completion rate)
        assignment_query = select(Assignment).where(Assignment.id == assignment_id)
        assignment_result = await db.execute(assignment_query)
        assignment = assignment_result.scalar_one()
        
        # Get classroom member count
        from app.models.classroom import ClassroomMember
        members_query = select(func.count(ClassroomMember.id)).where(
            ClassroomMember.classroom_id == assignment.classroom_id
        )
        members_result = await db.execute(members_query)
        total_students = members_result.scalar() or 0
        
        return {
            "total_attempts": len(attempts),
            "total_students": total_students,
            "average_score": sum(scores) / len(scores) if scores else 0,
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0,
            "completion_rate": (len(attempts) / total_students * 100) if total_students > 0 else 0,
            "average_time_minutes": (sum(durations) / len(durations) / 60) if durations else 0
        }

    @staticmethod
    async def get_question_statistics(
        db: AsyncSession,
        assignment_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get statistics for each question in an assignment.
        """
        # Get all questions for this assignment
        questions_query = select(Question).where(Question.assignment_id == assignment_id)
        questions_result = await db.execute(questions_query)
        questions = questions_result.scalars().all()
        
        question_stats = []
        
        for question in questions:
            # Get all responses for this question
            responses_query = select(Response).where(Response.question_id == question.id)
            responses_result = await db.execute(responses_query)
            responses = responses_result.scalars().all()
            
            if not responses:
                question_stats.append({
                    "question_id": question.id,
                    "question_text": question.prompt_text,
                    "total_responses": 0,
                    "correct_responses": 0,
                    "accuracy_rate": 0,
                    "average_time_seconds": 0,
                    "option_distribution": {"A": 0, "B": 0, "C": 0, "D": 0}
                })
                continue
            
            correct_responses = sum(1 for r in responses if r.is_correct)
            total_responses = len(responses)
            accuracy_rate = (correct_responses / total_responses) * 100
            average_time = sum(r.time_taken_seconds for r in responses) / total_responses
            
            # Calculate option distribution
            option_distribution = {"A": 0, "B": 0, "C": 0, "D": 0}
            for response in responses:
                if response.chosen_option in option_distribution:
                    option_distribution[response.chosen_option] += 1
            
            question_stats.append({
                "question_id": question.id,
                "question_text": question.prompt_text,
                "total_responses": total_responses,
                "correct_responses": correct_responses,
                "accuracy_rate": accuracy_rate,
                "average_time_seconds": average_time,
                "option_distribution": option_distribution
            })
        
        return question_stats


# Global grading service instance
grading_service = GradingService()
