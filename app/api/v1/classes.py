from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.classroom import Classroom, ClassroomMember
from app.schemas.classroom import Classroom as ClassroomSchema

router = APIRouter()


@router.get("/{classroom_id}", response_model=ClassroomSchema)
async def get_classroom(
    classroom_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get classroom information (accessible by both teachers and students)."""
    # Teachers can access their own classrooms
    if current_user.role.value == "TEACHER":
        query = select(Classroom).where(
            Classroom.id == classroom_id,
            Classroom.teacher_id == current_user.id
        )
    else:
        # Students can access classrooms they're enrolled in
        query = select(Classroom).join(
            ClassroomMember, Classroom.id == ClassroomMember.classroom_id
        ).where(
            Classroom.id == classroom_id,
            ClassroomMember.student_id == current_user.id
        )
    
    result = await db.execute(query)
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found or access denied"
        )
    
    return ClassroomSchema.from_orm(classroom)
