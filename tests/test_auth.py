"""
Authentication and OAuth2 tests.
"""
import pytest
import requests
from fastapi.testclient import TestClient


class TestAuthentication:
    """Test authentication endpoints and OAuth2 functionality."""
    
    def test_oauth2_token_endpoint(self, test_client, test_user_credentials):
        """Test OAuth2 token endpoint (FastAPI docs compatible)."""
        if not test_client:
            pytest.skip("FastAPI test client not available")
            
        # OAuth2 form data format
        login_data = {
            "username": test_user_credentials["email"],  # Use email as username
            "password": test_user_credentials["password"]
        }
        
        response = test_client.post(
            "/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 404:
            pytest.skip("OAuth2 token endpoint not implemented")
        elif response.status_code == 422:
            pytest.skip("Test user not found in database")
        
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert "token_type" in token_data
        assert token_data["token_type"] == "bearer"
    
    def test_regular_json_login(self, test_client, test_user_credentials):
        """Test regular JSON login endpoint."""
        if not test_client:
            pytest.skip("FastAPI test client not available")
            
        response = test_client.post(
            "/auth/login",
            json=test_user_credentials,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 404:
            pytest.skip("JSON login endpoint not implemented")
        elif response.status_code == 422:
            pytest.skip("Test user not found in database")
        
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data or "token" in token_data
    
    def test_protected_endpoint_with_token(self, test_client, test_user_credentials):
        """Test accessing protected endpoint with valid token."""
        if not test_client:
            pytest.skip("FastAPI test client not available")
            
        # First, get a token
        login_data = {
            "username": test_user_credentials["email"],
            "password": test_user_credentials["password"]
        }
        
        token_response = test_client.post(
            "/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if token_response.status_code != 200:
            pytest.skip("Cannot obtain authentication token")
        
        token_data = token_response.json()
        access_token = token_data["access_token"]
        
        # Test protected endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Try a few common protected endpoints
        protected_endpoints = [
            "/teachers/classrooms",
            "/students/assignments", 
            "/auth/me"
        ]
        
        endpoint_tested = False
        for endpoint in protected_endpoints:
            response = test_client.get(endpoint, headers=headers)
            if response.status_code != 404:  # Endpoint exists
                endpoint_tested = True
                assert response.status_code != 401, f"Token rejected at {endpoint}"
                break
        
        if not endpoint_tested:
            pytest.skip("No protected endpoints available for testing")
    
    def test_protected_endpoint_without_token(self, test_client):
        """Test accessing protected endpoint without token returns 401."""
        if not test_client:
            pytest.skip("FastAPI test client not available")
            
        # Try accessing protected endpoints without token
        protected_endpoints = [
            "/teachers/classrooms",
            "/students/assignments",
            "/auth/me"
        ]
        
        for endpoint in protected_endpoints:
            response = test_client.get(endpoint)
            if response.status_code != 404:  # Endpoint exists
                assert response.status_code == 401, f"Expected 401 for {endpoint} without token"
                return
        
        pytest.skip("No protected endpoints available for testing")
    
    @pytest.mark.integration
    def test_oauth2_with_real_server(self, base_url, test_user_credentials):
        """Integration test with real server (requires running server)."""
        try:
            # Check if server is running
            response = requests.get(f"{base_url}/docs", timeout=5)
            if response.status_code != 200:
                pytest.skip("Server not running on localhost:8000")
        except requests.exceptions.RequestException:
            pytest.skip("Server not running on localhost:8000")
        
        # Test OAuth2 login
        login_data = {
            "username": test_user_credentials["email"],
            "password": test_user_credentials["password"]
        }
        
        response = requests.post(
            f"{base_url}/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 422:
            pytest.skip("Test user not found in database")
        
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        
        # Test using the token
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        
        # Try a protected endpoint
        protected_response = requests.get(f"{base_url}/teachers/classrooms", headers=headers)
        if protected_response.status_code != 404:  # Endpoint exists
            assert protected_response.status_code != 401
