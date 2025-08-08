import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.classroom import Classroom
from app.core.security import get_password_hash, create_access_token


async def create_test_teacher(db_session: AsyncSession) -> tuple[User, str]:
    """Create a test teacher and return user and token."""
    teacher = User(
        email="teacher@test.com",
        password_hash=get_password_hash("testpassword123"),
        full_name="Test Teacher",
        role=UserRole.TEACHER
    )
    db_session.add(teacher)
    await db_session.commit()
    await db_session.refresh(teacher)
    
    token = create_access_token(
        data={"sub": str(teacher.id), "email": teacher.email, "role": teacher.role.value}
    )
    
    return teacher, token


async def create_test_student(db_session: AsyncSession) -> tuple[User, str]:
    """Create a test student and return user and token."""
    student = User(
        email="student@test.com",
        password_hash=get_password_hash("testpassword123"),
        full_name="Test Student",
        role=UserRole.STUDENT
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)
    
    token = create_access_token(
        data={"sub": str(student.id), "email": student.email, "role": student.role.value}
    )
    
    return student, token


class TestTeachers:
    @pytest.mark.asyncio
    async def test_create_classroom(self, client: AsyncClient, db_session: AsyncSession):
        """Test classroom creation by teacher."""
        teacher, token = await create_test_teacher(db_session)
        
        response = await client.post(
            "/api/v1/teachers/classrooms",
            json={"name": "Math 101"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Math 101"
        assert "code" in data
        assert len(data["code"]) == 6

    @pytest.mark.asyncio
    async def test_get_teacher_classrooms(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting teacher's classrooms."""
        teacher, token = await create_test_teacher(db_session)
        
        # Create a classroom
        classroom = Classroom(
            name="Test Classroom",
            code="TEST01",
            teacher_id=teacher.id
        )
        db_session.add(classroom)
        await db_session.commit()
        
        response = await client.get(
            "/api/v1/teachers/classrooms",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Classroom"
        assert data[0]["member_count"] == 0

    @pytest.mark.asyncio
    async def test_create_classroom_unauthorized(self, client: AsyncClient, db_session: AsyncSession):
        """Test classroom creation without teacher role."""
        student, token = await create_test_student(db_session)
        
        response = await client.post(
            "/api/v1/teachers/classrooms",
            json={"name": "Unauthorized Classroom"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_classroom_invite(self, client: AsyncClient, db_session: AsyncSession):
        """Test generating classroom invite code."""
        teacher, token = await create_test_teacher(db_session)
        
        # Create classroom
        classroom = Classroom(
            name="Test Classroom",
            code="OLD001",
            teacher_id=teacher.id
        )
        db_session.add(classroom)
        await db_session.commit()
        await db_session.refresh(classroom)
        
        response = await client.post(
            f"/api/v1/teachers/classrooms/{classroom.id}/invite",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert data["code"] != "OLD001"  # Should be a new code

    @pytest.mark.asyncio
    async def test_get_classroom_detail(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting detailed classroom information."""
        teacher, token = await create_test_teacher(db_session)
        
        # Create classroom
        classroom = Classroom(
            name="Detailed Classroom",
            code="DET001",
            teacher_id=teacher.id
        )
        db_session.add(classroom)
        await db_session.commit()
        await db_session.refresh(classroom)
        
        response = await client.get(
            f"/api/v1/teachers/classrooms/{classroom.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Detailed Classroom"
        assert "members" in data

    @pytest.mark.asyncio
    async def test_update_classroom(self, client: AsyncClient, db_session: AsyncSession):
        """Test updating classroom information."""
        teacher, token = await create_test_teacher(db_session)
        
        # Create classroom
        classroom = Classroom(
            name="Old Name",
            code="UPD001",
            teacher_id=teacher.id
        )
        db_session.add(classroom)
        await db_session.commit()
        await db_session.refresh(classroom)
        
        response = await client.put(
            f"/api/v1/teachers/classrooms/{classroom.id}",
            json={"name": "New Name"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_access_other_teacher_classroom(self, client: AsyncClient, db_session: AsyncSession):
        """Test that teacher cannot access another teacher's classroom."""
        # Create first teacher and classroom
        teacher1, _ = await create_test_teacher(db_session)
        classroom = Classroom(
            name="Teacher 1 Classroom",
            code="T1C001",
            teacher_id=teacher1.id
        )
        db_session.add(classroom)
        await db_session.commit()
        await db_session.refresh(classroom)
        
        # Create second teacher
        teacher2 = User(
            email="teacher2@test.com",
            password_hash=get_password_hash("testpassword123"),
            full_name="Test Teacher 2",
            role=UserRole.TEACHER
        )
        db_session.add(teacher2)
        await db_session.commit()
        await db_session.refresh(teacher2)
        
        token2 = create_access_token(
            data={"sub": str(teacher2.id), "email": teacher2.email, "role": teacher2.role.value}
        )
        
        # Try to access teacher1's classroom
        response = await client.get(
            f"/api/v1/teachers/classrooms/{classroom.id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        assert response.status_code == 404  # Should not find classroom
