import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.core.security import get_password_hash


class TestAuth:
    @pytest.mark.asyncio
    async def test_register_teacher(self, client: AsyncClient):
        """Test teacher registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "teacher@test.com",
                "password": "testpassword123",
                "full_name": "Test Teacher",
                "role": "TEACHER"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["email"] == "teacher@test.com"
        assert data["user"]["role"] == "TEACHER"
        assert data["token"]["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_student(self, client: AsyncClient):
        """Test student registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "student@test.com",
                "password": "testpassword123",
                "full_name": "Test Student",
                "role": "STUDENT"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "STUDENT"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email."""
        # First registration
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@test.com",
                "password": "testpassword123",
                "full_name": "First User",
                "role": "TEACHER"
            }
        )
        
        # Second registration with same email
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@test.com",
                "password": "testpassword123",
                "full_name": "Second User",
                "role": "STUDENT"
            }
        )
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful login."""
        # Create user directly in database
        user = User(
            email="login@test.com",
            password_hash=get_password_hash("testpassword123"),
            full_name="Login Test",
            role=UserRole.TEACHER
        )
        db_session.add(user)
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@test.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["email"] == "login@test.com"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_invalid_role(self, client: AsyncClient):
        """Test registration with invalid role."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid@test.com",
                "password": "testpassword123",
                "full_name": "Invalid Role",
                "role": "INVALID_ROLE"
            }
        )
        
        assert response.status_code == 400
        assert "Invalid role" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@test.com",
                "password": "123",  # Too short
                "full_name": "Weak Password",
                "role": "STUDENT"
            }
        )
        
        assert response.status_code == 422  # Validation error
