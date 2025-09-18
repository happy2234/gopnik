"""
Tests for API profile and validation endpoints.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from src.gopnik.interfaces.api.app import create_app
from src.gopnik.models.profiles import ProfileManager, RedactionProfile, RedactionStyle, ProfileValidationError
from src.gopnik.utils.integrity_validator import IntegrityValidator, IntegrityReport, ValidationResult, ValidationIssue
from src.gopnik.interfaces.api.routers.validation import get_integrity_validator
from src.gopnik.config import GopnikConfig


@pytest.fixture
def mock_config():
    """Mock configuration."""
    return Mock(spec=GopnikConfig)


@pytest.fixture
def mock_profile_manager():
    """Mock profile manager."""
    # Use real profile manager but with temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create sample profile files
        default_profile_data = {
            "name": "default",
            "description": "Default redaction profile",
            "visual_rules": {"faces": True, "signatures": True},
            "text_rules": {"names": True, "emails": True},
            "redaction_style": "solid_black",
            "confidence_threshold": 0.7,
            "multilingual_support": ["en", "es"],
            "version": "1.0"
        }
        
        healthcare_profile_data = {
            "name": "healthcare_hipaa",
            "description": "HIPAA compliant healthcare profile",
            "visual_rules": {"faces": True, "signatures": True, "barcodes": True},
            "text_rules": {"names": True, "emails": True, "phone_numbers": True, "addresses": True},
            "redaction_style": "solid_black",
            "confidence_threshold": 0.8,
            "multilingual_support": ["en"],
            "version": "1.0"
        }
        
        # Write profile files
        import yaml
        with open(tmp_path / "default.yaml", 'w') as f:
            yaml.dump(default_profile_data, f)
        with open(tmp_path / "healthcare_hipaa.yaml", 'w') as f:
            yaml.dump(healthcare_profile_data, f)
        
        # Create real profile manager with temp directory
        manager = ProfileManager(profile_directories=[tmp_path])
        yield manager


@pytest.fixture
def mock_integrity_validator():
    """Mock integrity validator."""
    validator = Mock(spec=IntegrityValidator)
    
    # Create sample validation report
    sample_report = IntegrityReport(
        document_id="test_doc",
        validation_timestamp=datetime.now(timezone.utc),
        overall_result=ValidationResult.VALID,
        document_hash="abc123",
        expected_hash="abc123",
        signature_valid=True,
        audit_trail_valid=True,
        processing_time=0.5
    )
    
    validator.validate_document_integrity.return_value = sample_report
    validator.validate_batch_documents.return_value = [sample_report]
    
    return validator


@pytest.fixture
def test_client(mock_config, mock_profile_manager, mock_integrity_validator):
    """Create test client with mocked dependencies."""
    app = create_app()
    
    # Override dependencies in app state
    app.state.config = mock_config
    app.state.profile_manager = mock_profile_manager
    
    # Use dependency override for the integrity validator
    app.dependency_overrides[get_integrity_validator] = lambda: mock_integrity_validator
    
    client = TestClient(app)
    
    yield client
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


class TestProfileEndpoints:
    """Test profile management endpoints."""
    
    def test_list_profiles(self, test_client, mock_profile_manager):
        """Test listing all profiles."""
        response = test_client.get("/api/v1/profiles")
        
        assert response.status_code == 200
        profiles = response.json()
        assert len(profiles) == 2
        profile_names = [p["name"] for p in profiles]
        assert "default" in profile_names
        assert "healthcare_hipaa" in profile_names
    
    def test_get_profile_success(self, test_client, mock_profile_manager):
        """Test getting a specific profile."""
        response = test_client.get("/api/v1/profiles/default")
        
        assert response.status_code == 200
        profile = response.json()
        assert profile["name"] == "default"
        assert profile["description"] == "Default redaction profile"
        assert profile["visual_rules"]["faces"] is True
        assert profile["confidence_threshold"] == 0.7
    
    def test_get_profile_not_found(self, test_client, mock_profile_manager):
        """Test getting a non-existent profile."""
        response = test_client.get("/api/v1/profiles/nonexistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_create_profile_success(self, test_client, mock_profile_manager):
        """Test creating a new profile."""
        profile_data = {
            "name": "test_profile",
            "description": "Test profile",
            "visual_rules": {"faces": True},
            "text_rules": {"names": True},
            "redaction_style": "solid_black",
            "confidence_threshold": 0.8,
            "multilingual_support": ["en"]
        }
        
        response = test_client.post("/api/v1/profiles", json=profile_data)
        
        assert response.status_code == 201
        created_profile = response.json()
        assert created_profile["name"] == "test_profile"
        assert created_profile["description"] == "Test profile"
    
    def test_create_profile_already_exists(self, test_client, mock_profile_manager):
        """Test creating a profile that already exists."""
        profile_data = {
            "name": "default",
            "description": "Test profile",
            "visual_rules": {"faces": True},
            "text_rules": {"names": True},
            "redaction_style": "solid_black",
            "confidence_threshold": 0.8,
            "multilingual_support": ["en"]
        }
        
        response = test_client.post("/api/v1/profiles", json=profile_data)
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    def test_create_profile_validation_error(self, test_client, mock_profile_manager):
        """Test creating a profile with validation errors."""
        profile_data = {
            "name": "invalid_profile",
            "description": "Invalid profile",
            "visual_rules": {"faces": True},
            "text_rules": {"names": True},
            "redaction_style": "solid_black",
            "confidence_threshold": 1.5,  # Invalid threshold
            "multilingual_support": ["en"]
        }
        
        response = test_client.post("/api/v1/profiles", json=profile_data)
        
        # Should get 422 for invalid data (Pydantic validation)
        assert response.status_code == 422
    
    def test_update_profile_success(self, test_client, mock_profile_manager):
        """Test updating an existing profile."""
        update_data = {
            "description": "Updated description",
            "confidence_threshold": 0.9
        }
        
        response = test_client.put("/api/v1/profiles/default", json=update_data)
        
        assert response.status_code == 200
        updated_profile = response.json()
        assert updated_profile["name"] == "default"
    
    def test_update_profile_not_found(self, test_client, mock_profile_manager):
        """Test updating a non-existent profile."""
        update_data = {
            "description": "Updated description"
        }
        
        response = test_client.put("/api/v1/profiles/nonexistent", json=update_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_delete_profile_success(self, test_client, mock_profile_manager):
        """Test deleting a profile."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.unlink') as mock_unlink:
            
            response = test_client.delete("/api/v1/profiles/healthcare_hipaa")
            
            assert response.status_code == 204
            mock_unlink.assert_called_once()
    
    def test_delete_profile_not_found(self, test_client, mock_profile_manager):
        """Test deleting a non-existent profile."""
        response = test_client.delete("/api/v1/profiles/nonexistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_delete_default_profile(self, test_client, mock_profile_manager):
        """Test that default profile cannot be deleted."""
        response = test_client.delete("/api/v1/profiles/default")
        
        assert response.status_code == 400
        assert "Cannot delete the default profile" in response.json()["detail"]


class TestValidationEndpoints:
    """Test document validation endpoints."""
    
    def test_validate_document_with_path(self, test_client, mock_integrity_validator):
        """Test validating a document with explicit path."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(b"test document content")
            tmp_path = tmp_file.name
        
        try:
            response = test_client.get(
                f"/api/v1/validate/test_doc?document_path={tmp_path}"
            )
            
            assert response.status_code == 200
            validation = response.json()
            assert validation["document_id"] == "test_doc"
            assert validation["is_valid"] is True
            assert validation["integrity_check"] is True
            assert validation["audit_trail_valid"] is True
            
            # Verify the validator was called
            assert mock_integrity_validator.validate_document_integrity.called
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_validate_document_not_found(self, test_client, mock_integrity_validator):
        """Test validating a non-existent document."""
        with patch('src.gopnik.interfaces.api.routers.validation._find_document_by_id', return_value=None):
            response = test_client.get("/api/v1/validate/nonexistent_doc")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
    
    def test_validate_document_with_expected_hash(self, test_client, mock_integrity_validator):
        """Test validating a document with expected hash."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(b"test document content")
            tmp_path = tmp_file.name
        
        try:
            response = test_client.get(
                f"/api/v1/validate/test_doc?document_path={tmp_path}&expected_hash=abc123"
            )
            
            assert response.status_code == 200
            validation = response.json()
            assert validation["document_id"] == "test_doc"
            assert validation["is_valid"] is True
            
            # Verify the validator was called
            assert mock_integrity_validator.validate_document_integrity.called
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_validate_document_with_validation_errors(self, test_client, mock_integrity_validator):
        """Test validating a document with validation errors."""
        # Create a report with errors
        error_report = IntegrityReport(
            document_id="test_doc",
            validation_timestamp=datetime.now(timezone.utc),
            overall_result=ValidationResult.HASH_MISMATCH,
            document_hash="abc123",
            expected_hash="def456",
            signature_valid=False,
            audit_trail_valid=False,
            processing_time=0.5
        )
        error_report.add_issue(
            "hash_mismatch",
            "error",
            "Document hash does not match expected hash"
        )
        error_report.add_issue(
            "invalid_signature",
            "warning",
            "Signature validation failed"
        )
        
        mock_integrity_validator.validate_document_integrity.return_value = error_report
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(b"test document content")
            tmp_path = tmp_file.name
        
        try:
            response = test_client.get(
                f"/api/v1/validate/test_doc?document_path={tmp_path}"
            )
            
            assert response.status_code == 200
            validation = response.json()
            assert validation["document_id"] == "test_doc"
            assert validation["is_valid"] is False
            assert validation["integrity_check"] is False
            assert validation["audit_trail_valid"] is False
            assert len(validation["errors"]) == 1
            assert len(validation["warnings"]) == 1
            assert "hash does not match" in validation["errors"][0]
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_validate_batch_documents(self, test_client, mock_integrity_validator):
        """Test batch document validation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test documents
            doc1_path = Path(tmp_dir) / "doc1.pdf"
            doc2_path = Path(tmp_dir) / "doc2.pdf"
            doc1_path.write_bytes(b"document 1 content")
            doc2_path.write_bytes(b"document 2 content")
            
            # Create sample reports
            report1 = IntegrityReport(
                document_id="doc1",
                validation_timestamp=datetime.now(timezone.utc),
                overall_result=ValidationResult.VALID,
                processing_time=0.3
            )
            report2 = IntegrityReport(
                document_id="doc2",
                validation_timestamp=datetime.now(timezone.utc),
                overall_result=ValidationResult.VALID,
                processing_time=0.4
            )
            
            mock_integrity_validator.validate_batch_documents.return_value = [report1, report2]
            
            response = test_client.post(
                f"/api/v1/validate/batch?document_dir={tmp_dir}&file_pattern=*.pdf"
            )
            
            assert response.status_code == 200
            validations = response.json()
            assert len(validations) == 2
            assert validations[0]["document_id"] == "doc1"
            assert validations[1]["document_id"] == "doc2"
            
            assert mock_integrity_validator.validate_batch_documents.called
    
    def test_validate_batch_documents_directory_not_found(self, test_client, mock_integrity_validator):
        """Test batch validation with non-existent directory."""
        response = test_client.post(
            "/api/v1/validate/batch?document_dir=/nonexistent/directory"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_detailed_validation_report(self, test_client, mock_integrity_validator):
        """Test getting detailed validation report."""
        # Create detailed report with issues
        detailed_report = IntegrityReport(
            document_id="test_doc",
            validation_timestamp=datetime.now(timezone.utc),
            overall_result=ValidationResult.VALID,
            document_hash="abc123",
            expected_hash="abc123",
            signature_valid=True,
            audit_trail_valid=True,
            processing_time=0.5
        )
        detailed_report.add_issue(
            "signature_valid",
            "info",
            "Cryptographic signature is valid"
        )
        detailed_report.metadata = {"file_size_bytes": 1024}
        
        mock_integrity_validator.validate_document_integrity.return_value = detailed_report
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(b"test document content")
            tmp_path = tmp_file.name
        
        try:
            response = test_client.get(
                f"/api/v1/validate/test_doc/report?document_path={tmp_path}"
            )
            
            assert response.status_code == 200
            report = response.json()
            assert report["document_id"] == "test_doc"
            assert report["overall_result"] == "valid"
            assert report["document_hash"] == "abc123"
            assert report["expected_hash"] == "abc123"
            assert report["signature_valid"] is True
            assert report["audit_trail_valid"] is True
            assert len(report["issues"]) == 1
            assert report["metadata"]["file_size_bytes"] == 1024
            assert "summary" in report
        finally:
            Path(tmp_path).unlink(missing_ok=True)


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_find_document_by_id(self):
        """Test finding document by ID."""
        from src.gopnik.interfaces.api.routers.validation import _find_document_by_id
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test document
            doc_path = Path(tmp_dir) / "test_doc.pdf"
            doc_path.write_bytes(b"test content")
            
            # Change to temp directory
            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)
                found_path = _find_document_by_id("test_doc")
                assert found_path is not None
                assert found_path.name == "test_doc.pdf"
            finally:
                os.chdir(old_cwd)
    
    def test_find_audit_log_by_id(self):
        """Test finding audit log by document ID."""
        from src.gopnik.interfaces.api.routers.validation import _find_audit_log_by_id
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test audit log
            audit_path = Path(tmp_dir) / "test_doc_audit.json"
            audit_path.write_text('{"id": "test_audit"}')
            
            # Change to temp directory
            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)
                found_path = _find_audit_log_by_id("test_doc")
                assert found_path is not None
                assert found_path.name == "test_doc_audit.json"
            finally:
                os.chdir(old_cwd)


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_profile_manager_exception(self, test_client):
        """Test handling of profile manager exceptions."""
        # Create a client with a broken profile manager
        from unittest.mock import Mock
        app = test_client.app
        broken_manager = Mock()
        broken_manager.list_profiles.side_effect = Exception("Database error")
        app.state.profile_manager = broken_manager
        
        response = test_client.get("/api/v1/profiles")
        
        assert response.status_code == 500
        assert "Failed to list profiles" in response.json()["detail"]
    
    def test_integrity_validator_exception(self, test_client):
        """Test handling of integrity validator exceptions."""
        # Override the validator to raise an exception
        from unittest.mock import Mock
        
        broken_validator = Mock()
        broken_validator.validate_document_integrity.side_effect = Exception("Validation error")
        
        # Override the dependency in the test client
        test_client.app.dependency_overrides[get_integrity_validator] = lambda: broken_validator
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(b"test document content")
            tmp_path = tmp_file.name
        
        try:
            response = test_client.get(
                f"/api/v1/validate/test_doc?document_path={tmp_path}"
            )
            
            assert response.status_code == 500
            assert "Validation failed" in response.json()["detail"]
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_invalid_json_request(self, test_client):
        """Test handling of invalid JSON requests."""
        response = test_client.post(
            "/api/v1/profiles",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity


if __name__ == "__main__":
    pytest.main([__file__])