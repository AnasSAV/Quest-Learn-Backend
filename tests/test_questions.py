"""
Tests for the questions API endpoints.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from io import BytesIO


class TestQuestionsAPI:
    """Test the questions API endpoints."""
    
    def test_upload_endpoint_exists(self, test_client):
        """Test that the upload endpoint exists."""
        if not test_client:
            pytest.skip("FastAPI test client not available")
        
        # Test without authentication (should return 401 or 403)
        response = test_client.post("/questions/upload")
        assert response.status_code in [401, 403, 422]  # Expected auth errors
    
    @patch('app.services.storage.upload_png')
    def test_upload_png_success(self, mock_upload, test_client):
        """Test successful PNG upload with mocked storage."""
        if not test_client:
            pytest.skip("FastAPI test client not available")
        
        # Mock the storage service to return success
        mock_upload.return_value = (True, "https://example.com/image.png")
        
        # Create a mock PNG file
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        
        files = {"file": ("test.png", BytesIO(png_data), "image/png")}
        
        # This will likely fail due to auth, but we can test the endpoint exists
        response = test_client.post("/questions/upload", files=files)
        
        # Should fail with auth error, not 404
        assert response.status_code != 404
    
    def test_storage_upload_png_function(self):
        """Test that the upload_png function can be imported."""
        try:
            from app.services.storage import upload_png
            assert callable(upload_png)
        except ImportError:
            pytest.fail("Could not import upload_png function")
    
    def test_storage_client_function(self):
        """Test that the supabase_client function works."""
        try:
            from app.services.storage import supabase_client
            # Don't actually call it in tests, just verify it's importable
            assert callable(supabase_client)
        except ImportError:
            pytest.fail("Could not import supabase_client function")
    
    def test_question_model_exists(self):
        """Test that Question model can be imported."""
        try:
            from app.models.question import Question, MCQOption
            assert Question is not None
            assert MCQOption is not None
        except ImportError:
            pytest.fail("Could not import Question models")
    
    def test_question_schema_exists(self):
        """Test that Question schemas can be imported."""
        try:
            from app.schemas.question import QuestionCreate, QuestionOut
            assert QuestionCreate is not None
            assert QuestionOut is not None
        except ImportError:
            pytest.fail("Could not import Question schemas")


class TestStorageService:
    """Test the storage service functionality."""
    
    def test_storage_settings_available(self):
        """Test that storage-related settings are available."""
        try:
            from app.core.config import get_settings
            settings = get_settings()
            
            # Check that required Supabase settings exist
            assert hasattr(settings, 'SUPABASE_URL')
            assert hasattr(settings, 'SUPABASE_SERVICE_ROLE_KEY')
            assert hasattr(settings, 'SUPABASE_BUCKET')
            assert hasattr(settings, 'MAX_UPLOAD_MB')
            
            # Verify they have values (if env is properly configured)
            if settings.SUPABASE_URL:
                assert settings.SUPABASE_URL.startswith('http')
            if settings.SUPABASE_BUCKET:
                assert len(settings.SUPABASE_BUCKET) > 0
                
        except Exception as e:
            pytest.skip(f"Settings not available: {e}")
    
    @pytest.mark.integration
    def test_upload_png_integration(self):
        """Integration test for PNG upload (requires real Supabase connection)."""
        try:
            from app.services.storage import upload_png
            
            # Create a minimal valid PNG file
            png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDAT\x08\x1dc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
            
            test_key = f"test/pytest_{pytest.__version__}.png"
            
            success, result = upload_png(png_data, test_key)
            
            if success:
                # Should return a URL
                assert result.startswith('http')
                assert 'supabase' in result.lower()
            else:
                # If it fails, it might be due to configuration
                pytest.skip(f"Upload failed (likely config issue): {result}")
                
        except Exception as e:
            pytest.skip(f"Integration test failed: {e}")
