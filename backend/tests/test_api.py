"""
Integration tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from app.auth import create_access_token

client = TestClient(app)


@pytest.fixture
def auth_token():
    """Create a test authentication token."""
    token = create_access_token(
        data={"sub": "test@example.com", "email": "test@example.com", "role": "admin"}
    )
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Create authentication headers."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAuthEndpoints:
    """Tests for authentication endpoints."""
    
    def test_login_success(self):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401


class TestCallEndpoints:
    """Tests for call management endpoints."""
    
    def test_list_calls_requires_auth(self):
        """Test that listing calls requires authentication."""
        response = client.get("/api/v1/calls")
        assert response.status_code == 403
    
    def test_list_calls_with_auth(self, auth_headers):
        """Test listing calls with authentication."""
        response = client.get("/api/v1/calls", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "calls" in data
        assert "total" in data


class TestLeadEndpoints:
    """Tests for lead management endpoints."""
    
    def test_list_leads_requires_auth(self):
        """Test that listing leads requires authentication."""
        response = client.get("/api/v1/leads")
        assert response.status_code == 403
    
    def test_list_leads_with_auth(self, auth_headers):
        """Test listing leads with authentication."""
        response = client.get("/api/v1/leads", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert "total" in data


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
