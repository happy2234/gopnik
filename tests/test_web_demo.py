"""
Tests for web interface demo page.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
from pathlib import Path

# Skip tests if web dependencies are not available
try:
    from src.gopnik.interfaces.api.app import create_app
    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False


@pytest.mark.skipif(not WEB_AVAILABLE, reason="Web dependencies not available")
class TestDemoPage:
    """Test cases for the demo page functionality."""
    
    @pytest.fixture
    def client(self):
        """Create test client with web interface."""
        app = create_app()
        return TestClient(app)
    
    def test_demo_page_loads(self, client):
        """Test that the demo page loads successfully."""
        response = client.get("/demo")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Check for key content
        content = response.text
        assert "Gopnik Demo" in content
        assert "Upload Document" in content
        assert "Redaction Profile" in content
    
    def test_demo_page_contains_upload_section(self, client):
        """Test that the demo page contains upload functionality."""
        response = client.get("/demo")
        content = response.text
        
        # Check for upload elements
        assert 'id="dropzone"' in content
        assert 'id="fileInput"' in content
        assert "Drop your document here" in content
        assert "browse files" in content
        
        # Check for supported formats
        assert "PDF" in content
        assert "PNG" in content
        assert "JPG" in content
        assert "TIFF" in content
    
    def test_demo_page_contains_profile_selection(self, client):
        """Test that the demo page contains profile selection."""
        response = client.get("/demo")
        content = response.text
        
        # Check for profile options
        assert "Default" in content
        assert "Healthcare (HIPAA)" in content
        assert "Financial" in content
        
        # Check for profile features
        assert "Names" in content
        assert "Emails" in content
        assert "Phone Numbers" in content
        assert "PHI" in content
        assert "SSN" in content
    
    def test_demo_page_contains_processing_controls(self, client):
        """Test that the demo page contains processing controls."""
        response = client.get("/demo")
        content = response.text
        
        # Check for processing elements
        assert 'id="processBtn"' in content
        assert "Process Document" in content
        assert "Show preview before download" in content
        assert "Generate audit trail" in content
    
    def test_demo_page_contains_status_section(self, client):
        """Test that the demo page contains processing status section."""
        response = client.get("/demo")
        content = response.text
        
        # Check for status elements
        assert 'id="processingStatus"' in content
        assert "Processing Document" in content
        assert 'id="progressFill"' in content
        assert "Uploading document" in content
        assert "Analyzing content" in content
        assert "Detecting PII" in content
        assert "Applying redactions" in content
    
    def test_demo_page_contains_results_section(self, client):
        """Test that the demo page contains results section."""
        response = client.get("/demo")
        content = response.text
        
        # Check for results elements
        assert 'id="resultsSection"' in content
        assert "Processing Complete" in content
        assert 'id="piiCount"' in content
        assert 'id="redactionCount"' in content
        assert 'id="confidenceScore"' in content
        assert "Download Redacted Document" in content
        assert "Preview Changes" in content
        assert "View Audit Trail" in content
    
    def test_demo_page_contains_help_sidebar(self, client):
        """Test that the demo page contains help sidebar."""
        response = client.get("/demo")
        content = response.text
        
        # Check for help content
        assert "Help & Tips" in content
        assert "Supported Formats" in content
        assert "PII Detection" in content
        assert "Security" in content
        assert "Need More?" in content
        
        # Check for security information
        assert "Files processed locally" in content
        assert "No data stored on servers" in content
        assert "Cryptographic audit trails" in content
    
    def test_demo_page_responsive_design(self, client):
        """Test that the demo page has responsive design elements."""
        response = client.get("/demo")
        content = response.text
        
        # Check for responsive CSS classes and viewport meta tag
        assert 'name="viewport"' in content
        assert 'content="width=device-width, initial-scale=1.0"' in content
        
        # Check for CSS link
        assert 'href="/static/css/demo.css"' in content
        
        # Check for responsive grid classes
        assert 'class="demo-layout"' in content
        assert 'class="help-sidebar"' in content
    
    def test_demo_page_javascript_integration(self, client):
        """Test that the demo page includes JavaScript functionality."""
        response = client.get("/demo")
        content = response.text
        
        # Check for JavaScript inclusion
        assert 'src="/static/js/demo.js"' in content
        
        # Check for interactive elements with IDs
        assert 'id="dropzone"' in content
        assert 'id="fileInput"' in content
        assert 'id="processBtn"' in content
        
        # Check for data attributes for JavaScript interaction
        assert 'data-profile="default"' in content
        assert 'data-profile="healthcare"' in content
        assert 'data-profile="financial"' in content
    
    def test_demo_page_accessibility(self, client):
        """Test that the demo page has accessibility features."""
        response = client.get("/demo")
        content = response.text
        
        # Check for semantic HTML elements
        assert '<main' in content
        assert '<section' in content
        assert '<header' in content
        assert '<nav' in content
        
        # Check for ARIA labels and roles (basic check)
        assert 'alt=' in content or 'aria-' in content or 'role=' in content
        
        # Check for proper heading hierarchy
        assert '<h1>' in content
        assert '<h2>' in content
        assert '<h3>' in content
    
    @patch('src.gopnik.interfaces.web.routes.templates')
    def test_demo_page_template_error_handling(self, mock_templates, client):
        """Test error handling when demo template fails to load."""
        mock_templates.TemplateResponse.side_effect = Exception("Template error")
        
        response = client.get("/demo")
        assert response.status_code == 500


@pytest.mark.skipif(not WEB_AVAILABLE, reason="Web dependencies not available")
class TestDemoFunctionality:
    """Test cases for demo page interactive functionality."""
    
    @pytest.fixture
    def client(self):
        """Create test client with web interface."""
        app = create_app()
        return TestClient(app)
    
    def test_demo_page_navigation(self, client):
        """Test navigation elements on demo page."""
        response = client.get("/demo")
        content = response.text
        
        # Check for navigation links
        assert 'href="/"' in content  # Back to home
        assert 'href="/docs"' in content  # Documentation
        
        # Check for logo link
        assert 'Gopnik' in content
        assert 'Demo' in content
    
    def test_demo_page_form_elements(self, client):
        """Test form elements and inputs on demo page."""
        response = client.get("/demo")
        content = response.text
        
        # Check for form inputs
        assert 'type="file"' in content
        assert 'type="checkbox"' in content
        assert 'accept=".pdf,.png,.jpg,.jpeg,.tiff"' in content
        
        # Check for buttons
        assert 'id="processBtn"' in content
        assert 'disabled' in content  # Process button should start disabled
    
    def test_demo_page_css_classes(self, client):
        """Test that demo page has proper CSS classes for styling."""
        response = client.get("/demo")
        content = response.text
        
        # Check for key CSS classes
        assert 'class="card"' in content
        assert 'class="btn btn-primary"' in content
        assert 'class="dropzone"' in content
        assert 'class="profile-option"' in content
        assert 'class="progress-bar"' in content


if __name__ == "__main__":
    pytest.main([__file__])