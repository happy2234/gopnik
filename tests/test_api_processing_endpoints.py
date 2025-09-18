"""
Tests for API processing endpoints.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from io import BytesIO

from src.gopnik.interfaces.api.app import create_app
from src.gopnik.interfaces.api.job_manager import JobManager, JobType, Job, JobStatus
from src.gopnik.core.processor import DocumentProcessor
from src.gopnik.models.profiles import ProfileManager, RedactionProfile
from src.gopnik.models.processing import ProcessingResult, BatchProcessingResult, ProcessingStatus
from src.gopnik.models.pii import PIIDetectionCollection
from src.gopnik.config import GopnikConfig


@pytest.fixture
def mock_config():
    """Mock configuration."""
    return Mock(spec=GopnikConfig)


@pytest.fixture
def mock_processor():
    """Mock document processor."""
    processor = Mock(spec=DocumentProcessor)
    
    # Mock document analyzer
    mock_analyzer = Mock()
    mock_analyzer.is_supported_format.return_value = True
    processor.document_analyzer = mock_analyzer
    
    processor.health_check.return_value = {
        'status': 'healthy',
        'components': {'ai_engine': 'available'},
        'supported_formats': ['pdf', 'png', 'jpeg'],
        'statistics': {}
    }
    return processor


@pytest.fixture
def mock_profile_manager():
    """Mock profile manager."""
    manager = Mock(spec=ProfileManager)
    manager.list_profiles.return_value = ['default', 'healthcare_hipaa']
    
    # Mock profile
    profile = Mock(spec=RedactionProfile)
    profile.name = 'default'
    profile.confidence_threshold = 0.7
    manager.load_profile.return_value = profile
    
    return manager


@pytest.fixture
def mock_job_manager():
    """Mock job manager."""
    manager = Mock(spec=JobManager)
    return manager


@pytest.fixture
def client(mock_config, mock_processor, mock_profile_manager):
    """Test client with mocked dependencies."""
    app = create_app()
    
    # Mock the lifespan context manager
    app.state.config = mock_config
    app.state.document_processor = mock_processor
    app.state.profile_manager = mock_profile_manager
    
    return TestClient(app)


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing."""
    content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    return BytesIO(content)


@pytest.fixture
def sample_image_file():
    """Create a sample image file for testing."""
    # Simple PNG header
    content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
    return BytesIO(content)


class TestProcessingEndpoints:
    """Test processing endpoints."""
    
    @patch('src.gopnik.interfaces.api.routers.processing.job_manager')
    def test_process_document_success(self, mock_job_manager, client, sample_pdf_file):
        """Test successful single document processing."""
        # Mock job creation
        job_id = "test-job-123"
        mock_job = Mock()
        mock_job.job_id = job_id
        mock_job.created_at = "2023-01-01T00:00:00Z"
        
        mock_job_manager.create_job.return_value = job_id
        mock_job_manager.get_job.return_value = mock_job
        
        # Make request
        response = client.post(
            "/api/v1/process",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")},
            data={"profile_name": "default"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == job_id
        assert data["document_id"] == "test.pdf"
        assert data["status"] == "pending"
        assert data["profile_name"] == "default"
        assert not data["success"]
        assert not data["output_available"]
        
        # Verify job manager was called
        mock_job_manager.create_job.assert_called_once_with(JobType.SINGLE_DOCUMENT)
    
    def test_process_document_no_file(self, client):
        """Test processing without file."""
        response = client.post(
            "/api/v1/process",
            data={"profile_name": "default"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_process_document_invalid_profile(self, client, sample_pdf_file, mock_profile_manager):
        """Test processing with invalid profile."""
        mock_profile_manager.load_profile.side_effect = FileNotFoundError("Profile not found")
        
        response = client.post(
            "/api/v1/process",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")},
            data={"profile_name": "nonexistent"}
        )
        
        assert response.status_code == 404
        assert "Profile 'nonexistent' not found" in response.json()["detail"]
    
    def test_process_document_unsupported_format(self, client, mock_processor):
        """Test processing unsupported file format."""
        mock_processor.document_analyzer.is_supported_format.return_value = False
        
        unsupported_file = BytesIO(b"unsupported content")
        response = client.post(
            "/api/v1/process",
            files={"file": ("test.xyz", unsupported_file, "application/octet-stream")},
            data={"profile_name": "default"}
        )
        
        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]
    
    @patch('src.gopnik.interfaces.api.routers.processing.job_manager')
    def test_process_batch_success(self, mock_job_manager, client, sample_pdf_file, sample_image_file):
        """Test successful batch processing."""
        # Mock job creation
        job_id = "batch-job-123"
        mock_job = Mock()
        mock_job.job_id = job_id
        mock_job.created_at = "2023-01-01T00:00:00Z"
        
        mock_job_manager.create_job.return_value = job_id
        mock_job_manager.get_job.return_value = mock_job
        
        # Make request with multiple files
        response = client.post(
            "/api/v1/batch",
            files=[
                ("files", ("test1.pdf", sample_pdf_file, "application/pdf")),
                ("files", ("test2.png", sample_image_file, "image/png"))
            ],
            data={"profile_name": "default"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == job_id
        assert data["total_documents"] == 2
        assert data["processed_documents"] == 0
        assert data["failed_documents"] == 0
        assert data["success_rate"] == 0.0
        assert not data["is_completed"]
        
        # Verify job manager was called
        mock_job_manager.create_job.assert_called_once_with(JobType.BATCH_PROCESSING)
    
    def test_process_batch_no_files(self, client):
        """Test batch processing without files."""
        response = client.post(
            "/api/v1/batch",
            data={"profile_name": "default"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_process_batch_too_many_files(self, client, sample_pdf_file):
        """Test batch processing with too many files."""
        files = [("files", (f"test{i}.pdf", BytesIO(b"content"), "application/pdf")) for i in range(25)]
        
        response = client.post(
            "/api/v1/batch",
            files=files,
            data={"profile_name": "default"}
        )
        
        assert response.status_code == 400
        assert "Too many files" in response.json()["detail"]
    
    @patch('src.gopnik.interfaces.api.routers.processing.job_manager')
    def test_get_job_status_success(self, mock_job_manager, client):
        """Test getting job status."""
        job_id = "test-job-123"
        
        # Mock job
        mock_job = Mock()
        mock_job.to_response.return_value = {
            "job_id": job_id,
            "status": "running",
            "created_at": "2023-01-01T00:00:00Z",
            "progress": 50.0
        }
        
        mock_job_manager.get_job.return_value = mock_job
        
        response = client.get(f"/api/v1/jobs/{job_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "running"
        assert data["progress"] == 50.0
    
    @patch('src.gopnik.interfaces.api.routers.processing.job_manager')
    def test_get_job_status_not_found(self, mock_job_manager, client):
        """Test getting status of non-existent job."""
        mock_job_manager.get_job.return_value = None
        
        response = client.get("/api/v1/jobs/nonexistent")
        
        assert response.status_code == 404
        assert "Job 'nonexistent' not found" in response.json()["detail"]
    
    @patch('src.gopnik.interfaces.api.routers.processing.job_manager')
    def test_list_jobs_success(self, mock_job_manager, client):
        """Test listing jobs."""
        # Mock jobs
        mock_jobs = []
        for i in range(3):
            job = Mock()
            job.to_response.return_value = {
                "job_id": f"job-{i}",
                "status": "completed",
                "created_at": "2023-01-01T00:00:00Z"
            }
            mock_jobs.append(job)
        
        mock_job_manager.list_jobs.return_value = mock_jobs
        mock_job_manager.get_job_count.return_value = 3
        
        response = client.get("/api/v1/jobs")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["jobs"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 50
    
    @patch('src.gopnik.interfaces.api.routers.processing.job_manager')
    def test_list_jobs_with_pagination(self, mock_job_manager, client):
        """Test listing jobs with pagination."""
        mock_job_manager.list_jobs.return_value = []
        mock_job_manager.get_job_count.return_value = 100
        
        response = client.get("/api/v1/jobs?limit=10&offset=20")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 3  # (20 // 10) + 1
        assert data["page_size"] == 10
        assert data["total"] == 100
        
        # Verify pagination parameters were passed
        mock_job_manager.list_jobs.assert_called_once_with(limit=10, offset=20)
    
    @patch('src.gopnik.interfaces.api.routers.processing.job_manager')
    def test_cancel_job_success(self, mock_job_manager, client):
        """Test cancelling a job."""
        job_id = "test-job-123"
        mock_job_manager.cancel_job.return_value = True
        
        response = client.delete(f"/api/v1/jobs/{job_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert f"Job '{job_id}' cancelled successfully" in data["message"]
    
    @patch('src.gopnik.interfaces.api.routers.processing.job_manager')
    def test_cancel_job_not_found(self, mock_job_manager, client):
        """Test cancelling non-existent job."""
        mock_job_manager.cancel_job.return_value = False
        mock_job_manager.get_job.return_value = None
        
        response = client.delete("/api/v1/jobs/nonexistent")
        
        assert response.status_code == 404
        assert "Job 'nonexistent' not found" in response.json()["detail"]
    
    @patch('src.gopnik.interfaces.api.routers.processing.job_manager')
    def test_cancel_job_cannot_cancel(self, mock_job_manager, client):
        """Test cancelling job that cannot be cancelled."""
        job_id = "completed-job"
        mock_job_manager.cancel_job.return_value = False
        
        # Mock completed job
        mock_job = Mock()
        mock_job.status = JobStatus.COMPLETED
        mock_job_manager.get_job.return_value = mock_job
        
        response = client.delete(f"/api/v1/jobs/{job_id}")
        
        assert response.status_code == 400
        assert "cannot be cancelled" in response.json()["detail"]
    
    @patch('src.gopnik.interfaces.api.routers.processing.job_manager')
    def test_download_processed_document_success(self, mock_job_manager, client):
        """Test downloading processed document."""
        job_id = "completed-job"
        
        # Create temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(b"processed document content")
            temp_path = temp_file.name
        
        try:
            # Mock completed job with result
            mock_result = Mock()
            mock_result.success = True
            mock_result.output_path = Path(temp_path)
            
            mock_job = Mock()
            mock_job.status = "completed"
            mock_job.result = mock_result
            
            mock_job_manager.get_job.return_value = mock_job
            
            response = client.get(f"/api/v1/jobs/{job_id}/download")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/octet-stream"
            assert b"processed document content" in response.content
            
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
    
    @patch('src.gopnik.interfaces.api.routers.processing.job_manager')
    def test_download_processed_document_not_completed(self, mock_job_manager, client):
        """Test downloading from non-completed job."""
        job_id = "running-job"
        
        mock_job = Mock()
        mock_job.status = "running"
        mock_job_manager.get_job.return_value = mock_job
        
        response = client.get(f"/api/v1/jobs/{job_id}/download")
        
        assert response.status_code == 400
        assert "Job not completed" in response.json()["detail"]
    
    @patch('src.gopnik.interfaces.api.routers.processing.job_manager')
    def test_download_processed_document_no_output(self, mock_job_manager, client):
        """Test downloading when no output file available."""
        job_id = "completed-job"
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.output_path = None
        
        mock_job = Mock()
        mock_job.status = "completed"
        mock_job.result = mock_result
        
        mock_job_manager.get_job.return_value = mock_job
        
        response = client.get(f"/api/v1/jobs/{job_id}/download")
        
        assert response.status_code == 404
        assert "No output file available" in response.json()["detail"]


class TestJobManager:
    """Test job manager functionality."""
    
    def test_create_job(self):
        """Test job creation."""
        manager = JobManager()
        job_id = manager.create_job(JobType.SINGLE_DOCUMENT)
        
        assert job_id is not None
        assert len(job_id) > 0
        
        job = manager.get_job(job_id)
        assert job is not None
        assert job.job_type == JobType.SINGLE_DOCUMENT
        assert job.status == JobStatus.PENDING
    
    def test_get_nonexistent_job(self):
        """Test getting non-existent job."""
        manager = JobManager()
        job = manager.get_job("nonexistent")
        assert job is None
    
    def test_list_jobs_empty(self):
        """Test listing jobs when empty."""
        manager = JobManager()
        jobs = manager.list_jobs()
        assert jobs == []
        assert manager.get_job_count() == 0
    
    def test_list_jobs_with_pagination(self):
        """Test listing jobs with pagination."""
        manager = JobManager()
        
        # Create multiple jobs
        job_ids = []
        for i in range(5):
            job_id = manager.create_job(JobType.SINGLE_DOCUMENT)
            job_ids.append(job_id)
        
        # Test pagination
        jobs_page1 = manager.list_jobs(limit=2, offset=0)
        assert len(jobs_page1) == 2
        
        jobs_page2 = manager.list_jobs(limit=2, offset=2)
        assert len(jobs_page2) == 2
        
        jobs_page3 = manager.list_jobs(limit=2, offset=4)
        assert len(jobs_page3) == 1
        
        assert manager.get_job_count() == 5
    
    def test_cancel_job(self):
        """Test job cancellation."""
        manager = JobManager()
        job_id = manager.create_job(JobType.SINGLE_DOCUMENT)
        
        # Should be able to cancel pending job
        success = manager.cancel_job(job_id)
        assert success
        
        job = manager.get_job(job_id)
        assert job.status == JobStatus.CANCELLED
        
        # Should not be able to cancel already cancelled job
        success = manager.cancel_job(job_id)
        assert not success
    
    def test_cancel_nonexistent_job(self):
        """Test cancelling non-existent job."""
        manager = JobManager()
        success = manager.cancel_job("nonexistent")
        assert not success


class TestJobModel:
    """Test Job model functionality."""
    
    def test_job_lifecycle(self):
        """Test job lifecycle methods."""
        job = Job("test-job", JobType.SINGLE_DOCUMENT)
        
        # Initial state
        assert job.status == JobStatus.PENDING
        assert job.progress == 0.0
        assert job.started_at is None
        assert job.completed_at is None
        
        # Start job
        job.start()
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None
        
        # Update progress
        job.update_progress(50.0)
        assert job.progress == 50.0
        
        # Complete job
        mock_result = Mock()
        job.complete(mock_result)
        assert job.status == JobStatus.COMPLETED
        assert job.progress == 100.0
        assert job.completed_at is not None
        assert job.result == mock_result
    
    def test_job_failure(self):
        """Test job failure handling."""
        job = Job("test-job", JobType.SINGLE_DOCUMENT)
        
        error_msg = "Processing failed"
        job.fail(error_msg)
        
        assert job.status == JobStatus.FAILED
        assert job.error == error_msg
        assert job.completed_at is not None
    
    def test_job_cancellation(self):
        """Test job cancellation."""
        job = Job("test-job", JobType.SINGLE_DOCUMENT)
        
        job.cancel()
        
        assert job.status == JobStatus.CANCELLED
        assert job.completed_at is not None
    
    def test_progress_bounds(self):
        """Test progress value bounds."""
        job = Job("test-job", JobType.SINGLE_DOCUMENT)
        
        # Test lower bound
        job.update_progress(-10.0)
        assert job.progress == 0.0
        
        # Test upper bound
        job.update_progress(150.0)
        assert job.progress == 100.0
        
        # Test normal value
        job.update_progress(75.0)
        assert job.progress == 75.0