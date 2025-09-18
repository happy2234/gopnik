"""
Tests for web processing workflow.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile
import json
from pathlib import Path
import io

# Skip tests if web dependencies are not available
try:
    from src.gopnik.interfaces.api.app import create_app
    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False


@pytest.mark.skipif(not WEB_AVAILABLE, reason="Web dependencies not available")
class TestWebProcessing:
    """Test cases for web processing workflow."""
    
    @pytest.fixture
    def client(self):
        """Create test client with web interface."""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_pdf_file(self):
        """Create a sample PDF file for testing."""
        # Create a minimal PDF-like content
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n%%EOF"
        return ("test.pdf", io.BytesIO(pdf_content), "application/pdf")
    
    def test_get_available_profiles(self, client):
        """Test getting available redaction profiles."""
        response = client.get("/api/web/profiles")
        assert response.status_code == 200
        
        data = response.json()
        assert "profiles" in data
        
        profiles = data["profiles"]
        assert "default" in profiles
        assert "healthcare" in profiles
        assert "financial" in profiles
        
        # Check profile structure
        default_profile = profiles["default"]
        assert "name" in default_profile
        assert "description" in default_profile
        assert "features" in default_profile
        assert "icon" in default_profile
    
    @patch('src.gopnik.interfaces.web.processing.processing_manager')
    def test_upload_and_process_success(self, mock_manager, client, sample_pdf_file):
        """Test successful file upload and processing start."""
        # Mock the processing manager
        mock_manager.create_job = AsyncMock(return_value="test-job-id")
        
        filename, file_content, content_type = sample_pdf_file
        
        response = client.post(
            "/api/web/upload",
            files={"file": (filename, file_content, content_type)},
            data={
                "profile": "default",
                "preview_mode": "true",
                "audit_trail": "true"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "job_id" in data
        assert data["status"] == "processing"
        assert "message" in data
    
    @patch('src.gopnik.interfaces.web.processing.processing_manager')
    def test_get_job_status(self, mock_manager, client):
        """Test getting job status."""
        # Mock job status
        mock_status = {
            "job_id": "test-job-id",
            "status": "processing",
            "progress": 50,
            "current_step": "detect",
            "step_message": "Detecting PII...",
            "created_at": "2024-01-01T12:00:00",
            "completed_at": None,
            "result": None,
            "error": None
        }
        
        mock_manager.get_job_status = AsyncMock(return_value=mock_status)
        
        response = client.get("/api/web/jobs/test-job-id/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["job_id"] == "test-job-id"
        assert data["status"] == "processing"
        assert data["progress"] == 50
        assert data["current_step"] == "detect"
    
    @patch('src.gopnik.interfaces.web.processing.processing_manager')
    def test_download_result_success(self, mock_manager, client):
        """Test successful file download."""
        # Create a temporary file for download
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(b"fake pdf content")
            temp_path = Path(temp_file.name)
        
        try:
            # Mock the processing manager
            mock_manager.get_download_file = AsyncMock(return_value=temp_path)
            mock_manager.get_job_status = AsyncMock(return_value={
                "result": {"filename": "redacted_test.pdf"}
            })
            
            response = client.get("/api/web/jobs/test-job-id/download")
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/octet-stream"
            
        finally:
            # Cleanup
            temp_path.unlink(missing_ok=True)
    
    @patch('src.gopnik.interfaces.web.processing.processing_manager')
    def test_download_audit_trail(self, mock_manager, client):
        """Test audit trail download."""
        # Create a temporary audit file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            audit_data = {"job_id": "test-job-id", "detections": []}
            temp_file.write(json.dumps(audit_data).encode())
            temp_path = Path(temp_file.name)
        
        try:
            # Mock the processing manager
            mock_manager.get_job_status = AsyncMock(return_value={
                "status": "completed",
                "result": {"audit_file": str(temp_path)}
            })
            
            response = client.get("/api/web/jobs/test-job-id/audit")
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            
        finally:
            # Cleanup
            temp_path.unlink(missing_ok=True)
    
    @patch('src.gopnik.interfaces.web.processing.processing_manager')
    def test_job_not_found(self, mock_manager, client):
        """Test handling of non-existent job."""
        from fastapi import HTTPException
        mock_manager.get_job_status = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Job not found")
        )
        
        response = client.get("/api/web/jobs/nonexistent-job/status")
        assert response.status_code == 404
    
    @patch('src.gopnik.interfaces.web.processing.processing_manager')
    def test_cancel_job(self, mock_manager, client):
        """Test job cancellation."""
        mock_manager.get_job_status = AsyncMock(return_value={
            "status": "processing"
        })
        
        response = client.delete("/api/web/jobs/test-job-id")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["job_id"] == "test-job-id"
    
    def test_upload_invalid_file_type(self, client):
        """Test upload with invalid file type."""
        # Create a text file
        text_content = io.BytesIO(b"This is not a PDF")
        
        response = client.post(
            "/api/web/upload",
            files={"file": ("test.txt", text_content, "text/plain")},
            data={"profile": "default"}
        )
        
        # Should fail due to invalid file type
        assert response.status_code in [400, 422, 500]  # Various possible error codes
    
    def test_upload_large_file(self, client):
        """Test upload with file too large."""
        # Create a large file (simulate 15MB)
        large_content = io.BytesIO(b"x" * (15 * 1024 * 1024))
        
        response = client.post(
            "/api/web/upload",
            files={"file": ("large.pdf", large_content, "application/pdf")},
            data={"profile": "default"}
        )
        
        # Should fail due to file size
        assert response.status_code in [413, 422, 500]  # Various possible error codes


@pytest.mark.skipif(not WEB_AVAILABLE, reason="Web dependencies not available")
class TestWebProcessingManager:
    """Test cases for WebProcessingManager class."""
    
    @pytest.fixture
    def mock_upload_file(self):
        """Create a mock UploadFile."""
        mock_file = MagicMock()
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.read = AsyncMock(return_value=b"fake pdf content")
        mock_file.seek = AsyncMock()
        return mock_file
    
    @patch('src.gopnik.interfaces.web.processing.DocumentProcessor')
    @patch('src.gopnik.interfaces.web.processing.ProfileManager')
    def test_processing_manager_initialization(self, mock_profile_manager, mock_processor):
        """Test WebProcessingManager initialization."""
        from src.gopnik.interfaces.web.processing import WebProcessingManager
        
        manager = WebProcessingManager()
        
        assert manager.jobs == {}
        assert manager.temp_dir.exists()
        assert hasattr(manager, 'processor')
        assert hasattr(manager, 'profile_manager')
    
    @patch('src.gopnik.interfaces.web.processing.DocumentProcessor')
    @patch('src.gopnik.interfaces.web.processing.ProfileManager')
    async def test_create_job_validation(self, mock_profile_manager, mock_processor, mock_upload_file):
        """Test job creation with file validation."""
        from src.gopnik.interfaces.web.processing import WebProcessingManager
        
        manager = WebProcessingManager()
        
        # Test with valid file
        job_id = await manager.create_job(mock_upload_file)
        assert job_id in manager.jobs
        assert manager.jobs[job_id].status == 'pending'
        
        # Cleanup
        manager._cleanup_temp_files(manager.jobs[job_id].temp_files)
    
    def test_job_model_validation(self):
        """Test WebProcessingJob model validation."""
        from src.gopnik.interfaces.web.processing import WebProcessingJob
        from datetime import datetime
        
        job = WebProcessingJob(
            job_id="test-id",
            filename="test.pdf",
            profile="default",
            status="pending",
            created_at=datetime.now()
        )
        
        assert job.job_id == "test-id"
        assert job.filename == "test.pdf"
        assert job.profile == "default"
        assert job.status == "pending"
        assert job.progress == 0
        assert job.current_step == "upload"


if __name__ == "__main__":
    pytest.main([__file__])