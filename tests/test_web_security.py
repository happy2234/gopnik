"""
Tests for web security features.
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import Request

# Skip tests if web dependencies are not available
try:
    from src.gopnik.interfaces.web.security import (
        RateLimitMiddleware, SecurityHeaders, SessionManager,
        SecureFileHandler, CloudflareIntegration, WebSecurityManager
    )
    from src.gopnik.interfaces.api.app import create_app
    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False


@pytest.mark.skipif(not WEB_AVAILABLE, reason="Web dependencies not available")
class TestSecurityHeaders:
    """Test security headers functionality."""
    
    def test_add_security_headers(self):
        """Test adding security headers to response."""
        from starlette.responses import Response
        
        response = Response("test content")
        secured_response = SecurityHeaders.add_security_headers(response)
        
        # Check for security headers
        assert "Content-Security-Policy" in secured_response.headers
        assert "X-Content-Type-Options" in secured_response.headers
        assert "X-Frame-Options" in secured_response.headers
        assert "X-XSS-Protection" in secured_response.headers
        assert "Referrer-Policy" in secured_response.headers
        assert "Permissions-Policy" in secured_response.headers
        
        # Check specific values
        assert secured_response.headers["X-Frame-Options"] == "DENY"
        assert secured_response.headers["X-Content-Type-Options"] == "nosniff"
    
    def test_hsts_header_for_https(self):
        """Test HSTS header is added for HTTPS requests."""
        from starlette.responses import Response
        
        response = Response("test content")
        response.headers["X-Forwarded-Proto"] = "https"
        
        secured_response = SecurityHeaders.add_security_headers(response)
        
        assert "Strict-Transport-Security" in secured_response.headers
        assert "max-age=31536000" in secured_response.headers["Strict-Transport-Security"]


@pytest.mark.skipif(not WEB_AVAILABLE, reason="Web dependencies not available")
class TestSessionManager:
    """Test session management functionality."""
    
    def test_create_session(self):
        """Test session creation."""
        manager = SessionManager()
        
        session_id = manager.create_session("192.168.1.1")
        
        assert session_id is not None
        assert len(session_id) > 20  # Should be a secure token
        assert session_id in manager.sessions
        
        session = manager.sessions[session_id]
        assert session["client_ip"] == "192.168.1.1"
        assert "created_at" in session
        assert "last_accessed" in session
        assert "jobs" in session
    
    def test_get_session(self):
        """Test session retrieval."""
        manager = SessionManager()
        
        session_id = manager.create_session("192.168.1.1")
        session = manager.get_session(session_id)
        
        assert session is not None
        assert session["client_ip"] == "192.168.1.1"
    
    def test_get_nonexistent_session(self):
        """Test retrieving non-existent session."""
        manager = SessionManager()
        
        session = manager.get_session("nonexistent")
        assert session is None
    
    def test_session_expiration(self):
        """Test session expiration."""
        manager = SessionManager(session_timeout=1)  # 1 second timeout
        
        session_id = manager.create_session("192.168.1.1")
        
        # Session should exist initially
        session = manager.get_session(session_id)
        assert session is not None
        
        # Wait for expiration
        time.sleep(2)
        
        # Session should be expired and removed
        session = manager.get_session(session_id)
        assert session is None
        assert session_id not in manager.sessions
    
    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        manager = SessionManager(session_timeout=1)
        
        # Create multiple sessions
        session1 = manager.create_session("192.168.1.1")
        session2 = manager.create_session("192.168.1.2")
        
        assert len(manager.sessions) == 2
        
        # Wait for expiration
        time.sleep(2)
        
        # Cleanup expired sessions
        manager.cleanup_expired_sessions()
        
        assert len(manager.sessions) == 0


@pytest.mark.skipif(not WEB_AVAILABLE, reason="Web dependencies not available")
class TestSecureFileHandler:
    """Test secure file handling functionality."""
    
    def test_secure_filename(self):
        """Test secure filename generation."""
        filename = SecureFileHandler.secure_filename("test document.pdf")
        
        # Should not contain original filename
        assert "test document" not in filename
        assert filename.endswith(".pdf")
        assert "_" in filename  # Should have timestamp and random parts
    
    def test_secure_filename_invalid_extension(self):
        """Test secure filename with invalid extension."""
        with pytest.raises(ValueError):
            SecureFileHandler.secure_filename("malicious.exe")
    
    def test_secure_filename_path_traversal(self):
        """Test secure filename prevents path traversal."""
        filename = SecureFileHandler.secure_filename("../../../etc/passwd.pdf")
        
        # Should only contain the filename part
        assert "../" not in filename
        assert "etc" not in filename
        assert "passwd" not in filename
        assert filename.endswith(".pdf")
    
    def test_secure_delete(self):
        """Test secure file deletion."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"sensitive data")
            temp_path = Path(temp_file.name)
        
        # File should exist
        assert temp_path.exists()
        
        # Securely delete it
        SecureFileHandler.secure_delete(temp_path)
        
        # File should be gone
        assert not temp_path.exists()
    
    def test_validate_file_content_pdf(self):
        """Test PDF file content validation."""
        # Create a fake PDF file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(b"%PDF-1.4\nfake pdf content")
            temp_path = Path(temp_file.name)
        
        try:
            result = SecureFileHandler.validate_file_content(temp_path, "application/pdf")
            assert result is True
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_validate_file_content_invalid_pdf(self):
        """Test invalid PDF file content validation."""
        # Create a fake file with wrong content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(b"This is not a PDF file")
            temp_path = Path(temp_file.name)
        
        try:
            result = SecureFileHandler.validate_file_content(temp_path, "application/pdf")
            assert result is False
        finally:
            temp_path.unlink(missing_ok=True)


@pytest.mark.skipif(not WEB_AVAILABLE, reason="Web dependencies not available")
class TestCloudflareIntegration:
    """Test Cloudflare integration functionality."""
    
    def test_is_cloudflare_request(self):
        """Test Cloudflare request detection."""
        # Mock request with Cloudflare headers
        mock_request = MagicMock()
        mock_request.headers = {
            "CF-Ray": "12345",
            "CF-Connecting-IP": "1.2.3.4"
        }
        
        result = CloudflareIntegration.is_cloudflare_request(mock_request)
        assert result is True
    
    def test_is_not_cloudflare_request(self):
        """Test non-Cloudflare request detection."""
        mock_request = MagicMock()
        mock_request.headers = {}
        
        result = CloudflareIntegration.is_cloudflare_request(mock_request)
        assert result is False
    
    def test_get_real_ip_cloudflare(self):
        """Test getting real IP from Cloudflare headers."""
        mock_request = MagicMock()
        mock_request.headers = {"CF-Connecting-IP": "1.2.3.4"}
        mock_request.client.host = "5.6.7.8"
        
        ip = CloudflareIntegration.get_real_ip(mock_request)
        assert ip == "1.2.3.4"
    
    def test_get_real_ip_fallback(self):
        """Test getting real IP fallback."""
        mock_request = MagicMock()
        mock_request.headers = {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}
        mock_request.client.host = "9.10.11.12"
        
        ip = CloudflareIntegration.get_real_ip(mock_request)
        assert ip == "1.2.3.4"
    
    def test_get_country_code(self):
        """Test getting country code from Cloudflare."""
        mock_request = MagicMock()
        mock_request.headers = {"CF-IPCountry": "US"}
        
        country = CloudflareIntegration.get_country_code(mock_request)
        assert country == "US"


@pytest.mark.skipif(not WEB_AVAILABLE, reason="Web dependencies not available")
class TestWebSecurityManager:
    """Test web security manager functionality."""
    
    def test_check_request_security_normal(self):
        """Test security check for normal request."""
        manager = WebSecurityManager()
        
        mock_request = MagicMock()
        mock_request.url.path = "/api/web/upload"
        mock_request.url.query = ""
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}
        
        result = manager.check_request_security(mock_request)
        assert result is True
    
    def test_check_request_security_blocked_ip(self):
        """Test security check for blocked IP."""
        manager = WebSecurityManager()
        manager.blocked_ips.add("192.168.1.1")
        
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            manager.check_request_security(mock_request)
        
        assert exc_info.value.status_code == 403
    
    def test_suspicious_activity_detection(self):
        """Test suspicious activity detection."""
        manager = WebSecurityManager()
        
        mock_request = MagicMock()
        mock_request.url.path = "/api/web/upload?id=1' union select * from users--"
        mock_request.url.query = "id=1' union select * from users--"
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}
        mock_request.method = "GET"
        
        # This should detect suspicious activity but not block immediately
        result = manager.check_request_security(mock_request)
        assert result is True
        
        # Check that suspicious activity was logged
        assert "192.168.1.1" in manager.suspicious_activity
        assert len(manager.suspicious_activity["192.168.1.1"]) > 0


@pytest.mark.skipif(not WEB_AVAILABLE, reason="Web dependencies not available")
class TestRateLimitMiddleware:
    """Test rate limiting middleware."""
    
    def test_rate_limit_initialization(self):
        """Test rate limit middleware initialization."""
        from fastapi import FastAPI
        
        app = FastAPI()
        middleware = RateLimitMiddleware(app, calls=10, period=60)
        
        assert middleware.calls == 10
        assert middleware.period == 60
        assert isinstance(middleware.clients, dict)
    
    def test_get_client_ip_direct(self):
        """Test getting client IP from direct connection."""
        from fastapi import FastAPI
        
        app = FastAPI()
        middleware = RateLimitMiddleware(app)
        
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client.host = "192.168.1.1"
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.1"
    
    def test_get_client_ip_forwarded(self):
        """Test getting client IP from forwarded headers."""
        from fastapi import FastAPI
        
        app = FastAPI()
        middleware = RateLimitMiddleware(app)
        
        mock_request = MagicMock()
        mock_request.headers = {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}
        mock_request.client.host = "192.168.1.1"
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "1.2.3.4"


@pytest.mark.skipif(not WEB_AVAILABLE, reason="Web dependencies not available")
class TestSecurityIntegration:
    """Test security integration with FastAPI app."""
    
    @pytest.fixture
    def client(self):
        """Create test client with security middleware."""
        app = create_app()
        return TestClient(app)
    
    def test_security_headers_in_response(self, client):
        """Test that security headers are added to responses."""
        response = client.get("/")
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
    
    def test_rate_limiting_protection(self, client):
        """Test rate limiting protection."""
        # This test would need to make many requests to trigger rate limiting
        # For now, just test that the endpoint is accessible
        response = client.get("/")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])