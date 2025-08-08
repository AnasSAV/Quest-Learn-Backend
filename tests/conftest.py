"""
Test configuration and fixtures for the test suite.
"""
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@pytest.fixture(scope="session")
def database_url():
    """Get the database URL from environment variables."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        pytest.skip("DATABASE_URL not set in environment")
    return db_url

@pytest.fixture(scope="session")
def db_engine(database_url):
    """Create a database engine for testing."""
    engine = create_engine(database_url)
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")
def db_session(db_engine):
    """Create a database session for testing."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI application."""
    try:
        from app.main import app
        return TestClient(app)
    except ImportError:
        pytest.skip("Cannot import FastAPI app")

@pytest.fixture
def test_user_credentials():
    """Test user credentials for authentication tests."""
    return {
        "email": "test@example.com",
        "password": "testpassword"
    }

@pytest.fixture
def base_url():
    """Base URL for the API."""
    return "http://localhost:8000"
