from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, get_current_teacher
from app.models.user import User
from app.models.classroom import Classroom, ClassroomMember
from app.models.assignment import Assignment
from app.schemas.classroom import (
    ClassroomCreate,
    ClassroomUpdate,
    Classroom as ClassroomSchema,
    ClassroomWithMemberCount,
    ClassroomDetail,
    ClassroomInvite,
    EnrollStudent,
    ClassroomMember as ClassroomMemberSchema
)
import secrets
import string

router = APIRouter()


@router.post("/classrooms", response_model=ClassroomSchema)
async def create_classroom(
    classroom_data: ClassroomCreate,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Create a new classroom."""
    # Generate unique classroom code
    while True:
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        # Check if code already exists
        existing_query = select(Classroom).where(Classroom.code == code)
        existing_result = await db.execute(existing_query)
        if not existing_result.scalar_one_or_none():
            break
    
    classroom = Classroom(
        name=classroom_data.name,
        code=code,
        teacher_id=current_teacher.id
    )
    
    db.add(classroom)
    await db.commit()
    await db.refresh(classroom)
    
    return ClassroomSchema.from_orm(classroom)


@router.get("/classrooms", response_model=List[ClassroomWithMemberCount])
async def get_teacher_classrooms(
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get all classrooms for the current teacher."""
    query = select(
        Classroom,
        func.count(ClassroomMember.id).label("member_count")
    ).outerjoin(
        ClassroomMember, Classroom.id == ClassroomMember.classroom_id
    ).where(
        Classroom.teacher_id == current_teacher.id
    ).group_by(Classroom.id).order_by(Classroom.created_at.desc())
    
    result = await db.execute(query)
    rows = result.all()
    
    classrooms = []
    for classroom, member_count in rows:
        classroom_dict = ClassroomSchema.from_orm(classroom).dict()
        classroom_dict["member_count"] = member_count or 0
        classrooms.append(ClassroomWithMemberCount(**classroom_dict))
    
    return classrooms


@router.get("/classrooms/{classroom_id}", response_model=ClassroomDetail)
async def get_classroom_detail(
    classroom_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get detailed classroom information including members."""
    query = select(Classroom).options(
        selectinload(Classroom.members).selectinload(ClassroomMember.student)
    ).where(
        Classroom.id == classroom_id,
        Classroom.teacher_id == current_teacher.id
    )
    
    result = await db.execute(query)
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )
    
    # Format members data
    members = []
    for member in classroom.members:
        members.append(ClassroomMemberSchema(
            id=member.id,
            student_id=member.student_id,
            student_name=member.student.full_name,
            student_email=member.student.email,
            joined_at=member.joined_at
        ))
    
    classroom_dict = ClassroomSchema.from_orm(classroom).dict()
    classroom_dict["members"] = members
    
    return ClassroomDetail(**classroom_dict)


@router.put("/classrooms/{classroom_id}", response_model=ClassroomSchema)
async def update_classroom(
    classroom_id: int,
    classroom_data: ClassroomUpdate,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Update classroom information."""
    query = select(Classroom).where(
        Classroom.id == classroom_id,
        Classroom.teacher_id == current_teacher.id
    )
    result = await db.execute(query)
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )
    
    # Update fields
    if classroom_data.name is not None:
        classroom.name = classroom_data.name
    
    await db.commit()
    await db.refresh(classroom)
    
    return ClassroomSchema.from_orm(classroom)


@router.post("/classrooms/{classroom_id}/invite", response_model=ClassroomInvite)
async def generate_classroom_invite(
    classroom_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Generate or refresh classroom invite code."""
    query = select(Classroom).where(
        Classroom.id == classroom_id,
        Classroom.teacher_id == current_teacher.id
    )
    result = await db.execute(query)
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )
    
    # Generate new code if requested
    while True:
        new_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        # Check if code already exists
        existing_query = select(Classroom).where(Classroom.code == new_code)
        existing_result = await db.execute(existing_query)
        if not existing_result.scalar_one_or_none():
            break
    
    classroom.code = new_code
    await db.commit()
    
    return ClassroomInvite(code=new_code)


@router.post("/classrooms/{classroom_id}/enroll")
async def enroll_student_by_email(
    classroom_id: int,
    student_data: EnrollStudent,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Manually enroll a student by email."""
    # Verify classroom ownership
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
    
    # Find student by email
    student_query = select(User).where(
        User.email == student_data.email,
        User.role == "STUDENT"
    )
    student_result = await db.execute(student_query)
    student = student_result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found with this email"
        )
    
    # Check if already enrolled
    existing_query = select(ClassroomMember).where(
        ClassroomMember.classroom_id == classroom_id,
        ClassroomMember.student_id == student.id
    )
    existing_result = await db.execute(existing_query)
    existing_member = existing_result.scalar_one_or_none()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is already enrolled in this classroom"
        )
    
    # Create membership
    membership = ClassroomMember(
        classroom_id=classroom_id,
        student_id=student.id
    )
    
    db.add(membership)
    await db.commit()
    
    return {"message": f"Student {student.full_name} successfully enrolled"}


@router.get("/classrooms/{classroom_id}/members", response_model=List[ClassroomMemberSchema])
async def get_classroom_members(
    classroom_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get all members of a classroom."""
    # Verify classroom ownership
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
    
    # Get members
    members_query = select(ClassroomMember).options(
        selectinload(ClassroomMember.student)
    ).where(ClassroomMember.classroom_id == classroom_id)
    
    members_result = await db.execute(members_query)
    members = members_result.scalars().all()
    
    return [
        ClassroomMemberSchema(
            id=member.id,
            student_id=member.student_id,
            student_name=member.student.full_name,
            student_email=member.student.email,
            joined_at=member.joined_at
        )
        for member in members
    ]


@router.delete("/classrooms/{classroom_id}")
async def delete_classroom(
    classroom_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Delete a classroom and all associated data."""
    query = select(Classroom).where(
        Classroom.id == classroom_id,
        Classroom.teacher_id == current_teacher.id
    )
    result = await db.execute(query)
    classroom = result.scalar_one_or_none()
    
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )
    
    # Check if classroom has assignments
    assignments_query = select(func.count(Assignment.id)).where(
        Assignment.classroom_id == classroom_id
    )
    assignments_result = await db.execute(assignments_query)
    assignment_count = assignments_result.scalar()
    
    if assignment_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete classroom with existing assignments"
        )
    
    await db.delete(classroom)
    await db.commit()
    
    return {"message": "Classroom deleted successfully"}
