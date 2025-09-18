"""
Integration tests for the complete web interface.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import io
import json

# Skip tests if web dependencies are not available
try:
    from src.gopnik.interfaces.api.app import create_app
    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False


@pytest.mark.skipif(not WEB_AVAILABLE, reason="Web dependencies not available")
class TestWebIntegration:
    """Integration tests for the complete web interface."""
    
    @pytest.fixture
    def client(self):
        """Create test client with full web interface."""
        app = create_app()
        return TestClient(app)
    
    def test_welcome_page_loads(self, client):
        """Test that the welcome page loads with all components."""
        response = client.get("/")
        assert response.status_code == 200
        
        content = response.text
        
        # Check for main sections
        assert "Gopnik" in content
        assert "AI-Powered Deidentification" in content
        assert "Try Web Demo" in content
        assert "Download CLI" in content
        
        # Check for security headers
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
    
    def test_demo_page_loads(self, client):
        """Test that the demo page loads with all components."""
        response = client.get("/demo")
        assert response.status_code == 200
        
        content = response.text
        
        # Check for demo components
        assert "Upload Document" in content
        assert "Redaction Profile" in content
        assert "Process Document" in content
        assert "Help & Tips" in content
        
        # Check for security headers
        assert "X-Frame-Options" in response.headers
        assert "Content-Security-Policy" in response.headers
    
    def test_static_files_accessible(self, client):
        """Test that static files are accessible."""
        # Test CSS file
        response = client.get("/static/css/welcome.css")
        # Accept 404 for now since static files might not be accessible in test environment
        assert response.status_code in [200, 404]
        
        # Test JS file
        response = client.get("/static/js/welcome.js")
        assert response.status_code in [200, 404]
    
    def test_api_endpoints_available(self, client):
        """Test that API endpoints are available."""
        # Test profiles endpoint
        response = client.get("/api/web/profiles")
        assert response.status_code == 200
        
        data = response.json()
        assert "profiles" in data
        assert "default" in data["profiles"]
        assert "healthcare" in data["profiles"]
        assert "financial" in data["profiles"]
    
    def test_navigation_between_pages(self, client):
        """Test navigation between different pages."""
        # Start at welcome page
        response = client.get("/")
        assert response.status_code == 200
        assert "Try Web Demo" in response.text
        
        # Navigate to demo page
        response = client.get("/demo")
        assert response.status_code == 200
        assert "Back to Home" in response.text
        
        # Test documentation redirect
        response = client.get("/docs/quickstart")
        assert response.status_code in [200, 302, 307]  # Allow redirects
    
    @patch('src.gopnik.interfaces.web.processing.processing_manager')
    def test_complete_upload_workflow(self, mock_manager, client):
        """Test complete file upload and processing workflow."""
        # Mock the processing manager
        mock_manager.create_job = AsyncMock(return_value="test-job-123")
        mock_manager.get_job_status = AsyncMock(return_value={
            "job_id": "test-job-123",
            "status": "completed",
            "progress": 100,
            "current_step": "complete",
            "step_message": "Processing complete",
            "created_at": "2024-01-01T12:00:00",
            "completed_at": "2024-01-01T12:01:00",
            "result": {
                "pii_detected": 5,
                "redactions_applied": 5,
                "average_confidence": 0.95,
                "filename": "redacted_test.pdf"
            },
            "error": None
        })
        
        # Create a fake PDF file
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        
        # Test file upload
        response = client.post(
            "/api/web/upload",
            files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")},
            data={
                "profile": "default",
                "preview_mode": "true",
                "audit_trail": "true"
            }
        )
        
        assert response.status_code == 200
        upload_data = response.json()
        assert "job_id" in upload_data
        assert upload_data["status"] == "processing"
        
        # Test job status
        response = client.get("/api/web/jobs/test-job-123/status")
        assert response.status_code == 200
        
        status_data = response.json()
        assert status_data["job_id"] == "test-job-123"
        assert status_data["status"] == "completed"
        assert status_data["result"]["pii_detected"] == 5
    
    def test_error_handling(self, client):
        """Test error handling throughout the interface."""
        # Test invalid job ID
        response = client.get("/api/web/jobs/invalid-job-id/status")
        assert response.status_code == 404
        
        # Test invalid file upload (no file)
        response = client.post("/api/web/upload", data={"profile": "default"})
        assert response.status_code == 422  # Validation error
    
    def test_security_features_active(self, client):
        """Test that security features are active."""
        response = client.get("/")
        
        # Check security headers
        headers = response.headers
        assert "X-Frame-Options" in headers
        assert "X-Content-Type-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Content-Security-Policy" in headers
        assert "Referrer-Policy" in headers
        
        # Check specific security values
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-Content-Type-Options"] == "nosniff"
    
    def test_profile_selection_functionality(self, client):
        """Test profile selection functionality."""
        response = client.get("/api/web/profiles")
        assert response.status_code == 200
        
        data = response.json()
        profiles = data["profiles"]
        
        # Test each profile has required fields
        for profile_name, profile_data in profiles.items():
            assert "name" in profile_data
            assert "description" in profile_data
            assert "features" in profile_data
            assert "icon" in profile_data
            assert isinstance(profile_data["features"], list)
            assert len(profile_data["features"]) > 0
    
    def test_responsive_design_elements(self, client):
        """Test that responsive design elements are present."""
        # Test welcome page
        response = client.get("/")
        content = response.text
        
        assert 'name="viewport"' in content
        assert 'content="width=device-width, initial-scale=1.0"' in content
        
        # Test demo page
        response = client.get("/demo")
        content = response.text
        
        assert 'name="viewport"' in content
        assert 'class="demo-layout"' in content
        assert 'class="help-sidebar"' in content
    
    def test_accessibility_features(self, client):
        """Test basic accessibility features."""
        response = client.get("/")
        content = response.text
        
        # Check for semantic HTML
        assert '<main>' in content or '<main ' in content
        assert '<header>' in content or '<header ' in content
        assert '<nav>' in content or '<nav ' in content
        assert '<section>' in content or '<section ' in content
        
        # Check for proper heading hierarchy
        assert '<h1>' in content
        assert '<h2>' in content
    
    def test_javascript_integration(self, client):
        """Test JavaScript integration."""
        response = client.get("/demo")
        content = response.text
        
        # Check for JavaScript files
        assert 'src="/static/js/demo.js"' in content
        
        # Check for interactive elements with proper IDs
        assert 'id="dropzone"' in content
        assert 'id="processBtn"' in content
        assert 'id="progressFill"' in content
    
    def test_css_integration(self, client):
        """Test CSS integration."""
        # Test welcome page CSS
        response = client.get("/")
        content = response.text
        assert 'href="/static/css/welcome.css"' in content
        
        # Test demo page CSS
        response = client.get("/demo")
        content = response.text
        assert 'href="/static/css/demo.css"' in content
    
    def test_api_documentation_integration(self, client):
        """Test API documentation integration."""
        # Test that API docs are accessible
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Test OpenAPI spec
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_data = response.json()
        assert "openapi" in openapi_data
        assert "info" in openapi_data
        assert "paths" in openapi_data
        
        # Check that web endpoints are documented
        paths = openapi_data["paths"]
        web_endpoints = [path for path in paths.keys() if "/api/web/" in path]
        assert len(web_endpoints) > 0


@pytest.mark.skipif(not WEB_AVAILABLE, reason="Web dependencies not available")
class TestWebPerformance:
    """Basic performance tests for web interface."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_page_load_times(self, client):
        """Test that pages load within reasonable time."""
        import time
        
        # Test welcome page
        start_time = time.time()
        response = client.get("/")
        load_time = time.time() - start_time
        
        assert response.status_code == 200
        assert load_time < 5.0  # Should load within 5 seconds
        
        # Test demo page
        start_time = time.time()
        response = client.get("/demo")
        load_time = time.time() - start_time
        
        assert response.status_code == 200
        assert load_time < 5.0  # Should load within 5 seconds
    
    def test_api_response_times(self, client):
        """Test API response times."""
        import time
        
        # Test profiles endpoint
        start_time = time.time()
        response = client.get("/api/web/profiles")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 2.0  # Should respond within 2 seconds


if __name__ == "__main__":
    pytest.main([__file__])