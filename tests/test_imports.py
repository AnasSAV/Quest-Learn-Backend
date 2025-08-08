"""
Import and module loading tests.
"""
import pytest


class TestImports:
    """Test that all modules can be imported successfully."""
    
    def test_import_main_app(self):
        """Test importing the main FastAPI app."""
        try:
            from app.main import app
            assert app is not None
        except ImportError as e:
            pytest.fail(f"Could not import main app: {e}")
    
    def test_import_models(self):
        """Test importing all model modules."""
        models = [
            "app.models.user",
            "app.models.assignment", 
            "app.models.attempt",
            "app.models.classroom",
            "app.models.question",
            "app.models.upload_token"
        ]
        
        for model_module in models:
            try:
                __import__(model_module)
            except ImportError as e:
                pytest.fail(f"Could not import {model_module}: {e}")
    
    def test_import_schemas(self):
        """Test importing all schema modules."""
        schemas = [
            "app.schemas.user",
            "app.schemas.assignment",
            "app.schemas.attempt", 
            "app.schemas.auth",
            "app.schemas.classroom",
            "app.schemas.question"
        ]
        
        for schema_module in schemas:
            try:
                __import__(schema_module)
            except ImportError as e:
                pytest.fail(f"Could not import {schema_module}: {e}")
    
    def test_import_api_routes(self):
        """Test importing all API route modules."""
        routes = [
            "app.api.v1.auth",
            "app.api.v1.assignments",
            "app.api.v1.attempts", 
            "app.api.v1.questions",
            "app.api.v1.students",
            "app.api.v1.teachers"
        ]
        
        for route_module in routes:
            try:
                __import__(route_module)
            except ImportError as e:
                pytest.fail(f"Could not import {route_module}: {e}")
    
    def test_import_core_modules(self):
        """Test importing core modules."""
        core_modules = [
            "app.core.config",
            "app.core.security"
        ]
        
        for core_module in core_modules:
            try:
                __import__(core_module)
            except ImportError as e:
                pytest.fail(f"Could not import {core_module}: {e}")
    
    def test_import_db_modules(self):
        """Test importing database modules."""
        db_modules = [
            "app.db.base",
            "app.db.session",
            "app.db.init_db"
        ]
        
        for db_module in db_modules:
            try:
                __import__(db_module)
            except ImportError as e:
                pytest.fail(f"Could not import {db_module}: {e}")
    
    def test_import_services(self):
        """Test importing service modules."""
        try:
            from app.services import storage
            assert storage is not None
        except ImportError as e:
            pytest.fail(f"Could not import storage service: {e}")
    
    def test_third_party_imports(self):
        """Test that all required third-party packages can be imported."""
        third_party = [
            "fastapi",
            "uvicorn", 
            "pydantic",
            "sqlalchemy",
            "psycopg",
            "passlib",
            "jwt",
            "supabase"
        ]
        
        for package in third_party:
            try:
                __import__(package)
            except ImportError as e:
                pytest.fail(f"Could not import required package {package}: {e}")
    
    def test_environment_variables_loaded(self):
        """Test that environment variables are properly loaded."""
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Check for critical environment variables
        critical_vars = ["DATABASE_URL"]
        
        for var in critical_vars:
            value = os.getenv(var)
            if not value:
                pytest.skip(f"Environment variable {var} not set")
            assert value, f"Environment variable {var} is empty"
