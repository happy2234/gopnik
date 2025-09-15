"""
Unit tests for integrity validation system.
"""

import pytest
import tempfile
import shutil
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.gopnik.utils.integrity_validator import (
    IntegrityValidator, ValidationResult, ValidationIssue, IntegrityReport,
    create_cli_validator, validate_document_cli
)
from src.gopnik.utils.crypto import CryptographicUtils
from src.gopnik.utils.audit_logger import AuditLogger
from src.gopnik.models.audit import AuditLog, AuditOperation, AuditLevel


class TestValidationIssue:
    """Test suite for ValidationIssue class."""
    
    def test_validation_issue_creation(self):
        """Test validation issue creation."""
        issue = ValidationIssue(
            type="hash_mismatch",
            severity="error",
            message="Document hash does not match expected value",
            details={"expected": "abc123", "actual": "def456"},
            affected_component="document_file",
            recommendation="Check document integrity"
        )
        
        assert issue.type == "hash_mismatch"
        assert issue.severity == "error"
        assert issue.message == "Document hash does not match expected value"
        assert issue.details["expected"] == "abc123"
        assert issue.affected_component == "document_file"
        assert issue.recommendation == "Check document integrity"
    
    def test_validation_issue_to_dict(self):
        """Test validation issue dictionary conversion."""
        issue = ValidationIssue(
            type="test_issue",
            severity="warning",
            message="Test message"
        )
        
        issue_dict = issue.to_dict()
        
        assert issue_dict["type"] == "test_issue"
        assert issue_dict["severity"] == "warning"
        assert issue_dict["message"] == "Test message"
        assert "details" in issue_dict
        assert "affected_component" in issue_dict
        assert "recommendation" in issue_dict


class TestIntegrityReport:
    """Test suite for IntegrityReport class."""
    
    def test_integrity_report_creation(self):
        """Test integrity report creation."""
        timestamp = datetime.now(timezone.utc)
        report = IntegrityReport(
            document_id="test_doc",
            validation_timestamp=timestamp,
            overall_result=ValidationResult.VALID
        )
        
        assert report.document_id == "test_doc"
        assert report.validation_timestamp == timestamp
        assert report.overall_result == ValidationResult.VALID
        assert len(report.issues) == 0
    
    def test_add_issue(self):
        """Test adding issues to report."""
        report = IntegrityReport(
            document_id="test_doc",
            validation_timestamp=datetime.now(timezone.utc),
            overall_result=ValidationResult.VALID
        )
        
        report.add_issue(
            "test_issue",
            "error",
            "Test error message",
            details={"key": "value"}
        )
        
        assert len(report.issues) == 1
        assert report.issues[0].type == "test_issue"
        assert report.issues[0].severity == "error"
        assert report.issues[0].message == "Test error message"
        assert report.issues[0].details["key"] == "value"
    
    def test_has_errors_and_warnings(self):
        """Test error and warning detection."""
        report = IntegrityReport(
            document_id="test_doc",
            validation_timestamp=datetime.now(timezone.utc),
            overall_result=ValidationResult.VALID
        )
        
        assert not report.has_errors()
        assert not report.has_warnings()
        
        report.add_issue("error_issue", "error", "Error message")
        assert report.has_errors()
        assert not report.has_warnings()
        
        report.add_issue("warning_issue", "warning", "Warning message")
        assert report.has_errors()
        assert report.has_warnings()
    
    def test_get_issues_by_severity(self):
        """Test filtering issues by severity."""
        report = IntegrityReport(
            document_id="test_doc",
            validation_timestamp=datetime.now(timezone.utc),
            overall_result=ValidationResult.VALID
        )
        
        report.add_issue("error1", "error", "Error 1")
        report.add_issue("error2", "error", "Error 2")
        report.add_issue("warning1", "warning", "Warning 1")
        report.add_issue("info1", "info", "Info 1")
        
        errors = report.get_issues_by_severity("error")
        warnings = report.get_issues_by_severity("warning")
        infos = report.get_issues_by_severity("info")
        
        assert len(errors) == 2
        assert len(warnings) == 1
        assert len(infos) == 1
    
    def test_get_summary(self):
        """Test report summary generation."""
        report = IntegrityReport(
            document_id="test_doc",
            validation_timestamp=datetime.now(timezone.utc),
            overall_result=ValidationResult.VALID,
            signature_valid=True,
            audit_trail_valid=True,
            processing_time=1.5
        )
        
        report.add_issue("error1", "error", "Error 1")
        report.add_issue("warning1", "warning", "Warning 1")
        
        summary = report.get_summary()
        
        assert summary["document_id"] == "test_doc"
        assert summary["overall_result"] == "valid"
        assert summary["total_issues"] == 2
        assert summary["errors"] == 1
        assert summary["warnings"] == 1
        assert summary["info"] == 0
        assert summary["signature_valid"] is True
        assert summary["audit_trail_valid"] is True
        assert summary["processing_time"] == 1.5
    
    def test_to_dict_and_json(self):
        """Test dictionary and JSON conversion."""
        timestamp = datetime.now(timezone.utc)
        report = IntegrityReport(
            document_id="test_doc",
            validation_timestamp=timestamp,
            overall_result=ValidationResult.VALID
        )
        
        report.add_issue("test_issue", "info", "Test message")
        
        # Test to_dict
        report_dict = report.to_dict()
        assert report_dict["document_id"] == "test_doc"
        assert report_dict["overall_result"] == "valid"
        assert len(report_dict["issues"]) == 1
        assert "summary" in report_dict
        
        # Test to_json
        json_str = report.to_json()
        assert isinstance(json_str, str)
        
        # Verify JSON can be parsed back
        parsed = json.loads(json_str)
        assert parsed["document_id"] == "test_doc"


class TestIntegrityValidator:
    """Test suite for IntegrityValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.crypto = CryptographicUtils()
        self.audit_logger = AuditLogger(storage_path=self.temp_dir / "audit")
        self.validator = IntegrityValidator(
            crypto_utils=self.crypto,
            audit_logger=self.audit_logger
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.audit_logger.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        assert self.validator.crypto is not None
        assert self.validator.audit_logger is not None
        
        # Test with default parameters
        validator_default = IntegrityValidator()
        assert validator_default.crypto is not None
        assert validator_default.audit_logger is None
    
    def test_validate_missing_document(self):
        """Test validation of missing document."""
        missing_path = self.temp_dir / "missing_document.pdf"
        
        report = self.validator.validate_document_integrity(missing_path)
        
        assert report.overall_result == ValidationResult.MISSING_DATA
        assert report.has_errors()
        assert any(issue.type == "missing_document" for issue in report.issues)
    
    def test_validate_document_basic(self):
        """Test basic document validation."""
        # Create test document
        test_content = b"This is a test document for validation"
        doc_path = self.temp_dir / "test_document.txt"
        
        with open(doc_path, 'wb') as f:
            f.write(test_content)
        
        # Calculate expected hash
        expected_hash = self.crypto.generate_sha256_hash_from_bytes(test_content)
        
        # Validate document
        report = self.validator.validate_document_integrity(
            document_path=doc_path,
            expected_hash=expected_hash
        )
        
        assert report.overall_result == ValidationResult.VALID
        assert report.document_hash == expected_hash
        assert report.expected_hash == expected_hash
        assert not report.has_errors()
    
    def test_validate_document_hash_mismatch(self):
        """Test validation with hash mismatch."""
        # Create test document
        test_content = b"This is a test document"
        doc_path = self.temp_dir / "test_document.txt"
        
        with open(doc_path, 'wb') as f:
            f.write(test_content)
        
        # Use wrong expected hash
        wrong_hash = "wrong_hash_value"
        
        # Validate document
        report = self.validator.validate_document_integrity(
            document_path=doc_path,
            expected_hash=wrong_hash
        )
        
        assert report.overall_result == ValidationResult.HASH_MISMATCH
        assert report.has_errors()
        assert any(issue.type == "hash_mismatch" for issue in report.issues)
        assert report.expected_hash == wrong_hash
        assert report.document_hash != wrong_hash
    
    def test_validate_with_audit_log(self):
        """Test validation with audit log."""
        # Create test document
        test_content = b"Test document with audit log"
        doc_path = self.temp_dir / "test_document.txt"
        
        with open(doc_path, 'wb') as f:
            f.write(test_content)
        
        # Create audit log
        document_hash = self.crypto.generate_sha256_hash_from_bytes(test_content)
        audit_log = AuditLog(
            operation=AuditOperation.DOCUMENT_REDACTION,
            timestamp=datetime.now(timezone.utc),
            document_id="test_document",
            output_hash=document_hash
        )
        
        # Sign the audit log
        self.crypto.generate_rsa_key_pair()
        content_hash = audit_log.get_content_hash()
        signature = self.crypto.sign_data_rsa(content_hash)
        audit_log.signature = signature
        
        # Validate document
        report = self.validator.validate_document_integrity(
            document_path=doc_path,
            audit_log_data=audit_log
        )
        
        assert report.overall_result == ValidationResult.VALID
        assert report.signature_valid is True
        assert report.audit_trail_valid is True
        assert not report.has_errors()
    
    def test_validate_with_invalid_signature(self):
        """Test validation with invalid signature."""
        # Create test document
        test_content = b"Test document with invalid signature"
        doc_path = self.temp_dir / "test_document.txt"
        
        with open(doc_path, 'wb') as f:
            f.write(test_content)
        
        # Create audit log with invalid signature
        document_hash = self.crypto.generate_sha256_hash_from_bytes(test_content)
        audit_log = AuditLog(
            operation=AuditOperation.DOCUMENT_REDACTION,
            timestamp=datetime.now(timezone.utc),
            document_id="test_document",
            output_hash=document_hash,
            signature="invalid_signature"
        )
        
        # Set up crypto keys for validation
        self.crypto.generate_rsa_key_pair()
        
        # Validate document
        report = self.validator.validate_document_integrity(
            document_path=doc_path,
            audit_log_data=audit_log
        )
        
        assert report.overall_result == ValidationResult.SIGNATURE_MISMATCH
        assert report.signature_valid is False
        assert report.has_errors()
        assert any(issue.type == "invalid_signature" for issue in report.issues)
    
    def test_validate_with_audit_log_file(self):
        """Test validation with audit log file."""
        # Create test document
        test_content = b"Test document with audit log file"
        doc_path = self.temp_dir / "test_document.txt"
        
        with open(doc_path, 'wb') as f:
            f.write(test_content)
        
        # Create audit log file
        document_hash = self.crypto.generate_sha256_hash_from_bytes(test_content)
        audit_log = AuditLog(
            operation=AuditOperation.DOCUMENT_REDACTION,
            timestamp=datetime.now(timezone.utc),
            document_id="test_document",
            output_hash=document_hash
        )
        
        audit_log_path = self.temp_dir / "audit_log.json"
        with open(audit_log_path, 'w') as f:
            json.dump(audit_log.to_dict(), f)
        
        # Validate document
        report = self.validator.validate_document_integrity(
            document_path=doc_path,
            audit_log_path=audit_log_path
        )
        
        assert report.overall_result == ValidationResult.VALID
        assert not report.has_errors()
    
    def test_validate_with_corrupted_audit_log(self):
        """Test validation with corrupted audit log file."""
        # Create test document
        test_content = b"Test document"
        doc_path = self.temp_dir / "test_document.txt"
        
        with open(doc_path, 'wb') as f:
            f.write(test_content)
        
        # Create corrupted audit log file
        audit_log_path = self.temp_dir / "corrupted_audit.json"
        with open(audit_log_path, 'w') as f:
            f.write("invalid json content")
        
        # Validate document
        report = self.validator.validate_document_integrity(
            document_path=doc_path,
            audit_log_path=audit_log_path
        )
        
        # Should still validate the document, but report audit log issues
        assert report.document_hash is not None
        assert any(issue.type == "audit_log_load_failed" for issue in report.issues)
    
    def test_validate_empty_file(self):
        """Test validation of empty file."""
        # Create empty document
        doc_path = self.temp_dir / "empty_document.txt"
        doc_path.touch()
        
        # Validate document
        report = self.validator.validate_document_integrity(doc_path)
        
        assert report.has_errors()
        assert any(issue.type == "empty_file" for issue in report.issues)
        assert report.metadata["file_size_bytes"] == 0
    
    def test_validate_large_file(self):
        """Test validation of large file."""
        # Create large document (simulate with metadata)
        doc_path = self.temp_dir / "large_document.txt"
        with open(doc_path, 'wb') as f:
            f.write(b"x" * 1000)  # Small file for testing
        
        # Mock file size to appear large
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 150 * 1024 * 1024  # 150MB
            
            report = self.validator.validate_document_integrity(doc_path)
            
            assert any(issue.type == "large_file" for issue in report.issues)
            assert report.metadata["file_size_bytes"] == 150 * 1024 * 1024
    
    def test_validate_batch_documents(self):
        """Test batch validation of multiple documents."""
        # Create multiple test documents
        doc_paths = []
        for i in range(3):
            doc_path = self.temp_dir / f"document_{i}.txt"
            with open(doc_path, 'wb') as f:
                f.write(f"Test document {i}".encode())
            doc_paths.append(doc_path)
        
        # Validate batch
        reports = self.validator.validate_batch_documents(self.temp_dir, file_pattern="*.txt")
        
        assert len(reports) == 3
        for report in reports:
            assert report.overall_result == ValidationResult.VALID
            assert not report.has_errors()
    
    def test_validate_batch_with_audit_logs(self):
        """Test batch validation with audit logs."""
        # Create test document
        doc_path = self.temp_dir / "test_doc.txt"
        test_content = b"Test document with audit"
        with open(doc_path, 'wb') as f:
            f.write(test_content)
        
        # Create audit directory and log
        audit_dir = self.temp_dir / "audit_logs"
        audit_dir.mkdir()
        
        document_hash = self.crypto.generate_sha256_hash_from_bytes(test_content)
        audit_log = AuditLog(
            operation=AuditOperation.DOCUMENT_REDACTION,
            timestamp=datetime.now(timezone.utc),
            document_id="test_doc",
            output_hash=document_hash
        )
        
        audit_log_path = audit_dir / "test_doc_audit.json"
        with open(audit_log_path, 'w') as f:
            json.dump(audit_log.to_dict(), f)
        
        # Validate batch
        reports = self.validator.validate_batch_documents(
            self.temp_dir,
            audit_dir=audit_dir,
            file_pattern="*.txt"
        )
        
        assert len(reports) == 1
        assert reports[0].overall_result == ValidationResult.VALID
    
    def test_generate_validation_summary(self):
        """Test validation summary generation."""
        # Create sample reports
        reports = []
        
        # Valid report
        valid_report = IntegrityReport(
            document_id="valid_doc",
            validation_timestamp=datetime.now(timezone.utc),
            overall_result=ValidationResult.VALID,
            signature_valid=True,
            processing_time=1.0
        )
        reports.append(valid_report)
        
        # Invalid report with errors
        invalid_report = IntegrityReport(
            document_id="invalid_doc",
            validation_timestamp=datetime.now(timezone.utc),
            overall_result=ValidationResult.HASH_MISMATCH,
            signature_valid=False,
            processing_time=1.5
        )
        invalid_report.add_issue("hash_mismatch", "error", "Hash mismatch")
        invalid_report.add_issue("signature_invalid", "error", "Invalid signature")
        reports.append(invalid_report)
        
        # Generate summary
        summary = self.validator.generate_validation_summary(reports)
        
        assert summary["total_documents"] == 2
        assert summary["valid_documents"] == 1
        assert summary["invalid_documents"] == 1
        assert summary["total_issues"] == 2
        assert summary["validation_results"]["valid"] == 1
        assert summary["validation_results"]["hash_mismatch"] == 1
        assert summary["issue_types"]["hash_mismatch"] == 1
        assert summary["issue_types"]["signature_invalid"] == 1
        assert summary["average_processing_time"] == 1.25
        assert summary["reports_with_errors"] == 1
        assert summary["signed_documents"] == 1
        assert summary["unsigned_documents"] == 1
    
    def test_generate_validation_summary_empty(self):
        """Test validation summary with empty reports list."""
        summary = self.validator.generate_validation_summary([])
        
        assert summary["total_documents"] == 0
        assert summary["valid_documents"] == 0
        assert summary["invalid_documents"] == 0
        assert summary["total_issues"] == 0
        assert summary["average_processing_time"] == 0
    
    def test_export_validation_report_json(self):
        """Test exporting validation report to JSON."""
        # Create test report
        report = IntegrityReport(
            document_id="test_doc",
            validation_timestamp=datetime.now(timezone.utc),
            overall_result=ValidationResult.VALID
        )
        report.add_issue("test_issue", "info", "Test message")
        
        # Export to JSON
        output_path = self.temp_dir / "validation_report.json"
        self.validator.export_validation_report(report, output_path, format='json')
        
        assert output_path.exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["total_reports"] == 1
        assert len(data["reports"]) == 1
        assert data["reports"][0]["document_id"] == "test_doc"
        assert "summary" in data
    
    def test_export_validation_report_csv(self):
        """Test exporting validation report to CSV."""
        # Create test reports
        reports = []
        for i in range(2):
            report = IntegrityReport(
                document_id=f"doc_{i}",
                validation_timestamp=datetime.now(timezone.utc),
                overall_result=ValidationResult.VALID,
                processing_time=1.0 + i
            )
            reports.append(report)
        
        # Export to CSV
        output_path = self.temp_dir / "validation_report.csv"
        self.validator.export_validation_report(reports, output_path, format='csv')
        
        assert output_path.exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 3  # Header + 2 data rows
        assert 'Document ID' in lines[0]
        assert 'doc_0' in lines[1]
        assert 'doc_1' in lines[2]
    
    def test_export_validation_report_invalid_format(self):
        """Test exporting with invalid format."""
        report = IntegrityReport(
            document_id="test_doc",
            validation_timestamp=datetime.now(timezone.utc),
            overall_result=ValidationResult.VALID
        )
        
        output_path = self.temp_dir / "report.txt"
        
        with pytest.raises(ValueError, match="Unsupported export format"):
            self.validator.export_validation_report(report, output_path, format='txt')
    
    def test_audit_trail_validation_missing_fields(self):
        """Test audit trail validation with missing required fields."""
        # Create document
        doc_path = self.temp_dir / "test_doc.txt"
        with open(doc_path, 'wb') as f:
            f.write(b"test content")
        
        # Create audit log with missing fields
        audit_log = AuditLog(
            operation=AuditOperation.DOCUMENT_REDACTION,
            timestamp=datetime.now(timezone.utc),
            document_id="",  # Missing document ID
            id=""  # Missing audit ID
        )
        
        report = self.validator.validate_document_integrity(
            document_path=doc_path,
            audit_log_data=audit_log
        )
        
        assert report.audit_trail_valid is False
        assert any(issue.type == "missing_document_id" for issue in report.issues)
        assert any(issue.type == "missing_audit_id" for issue in report.issues)
    
    def test_audit_trail_validation_future_timestamp(self):
        """Test audit trail validation with future timestamp."""
        # Create document
        doc_path = self.temp_dir / "test_doc.txt"
        with open(doc_path, 'wb') as f:
            f.write(b"test content")
        
        # Create audit log with future timestamp
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        audit_log = AuditLog(
            operation=AuditOperation.DOCUMENT_REDACTION,
            timestamp=future_time,
            document_id="test_doc"
        )
        
        report = self.validator.validate_document_integrity(
            document_path=doc_path,
            audit_log_data=audit_log
        )
        
        assert any(issue.type == "future_timestamp" for issue in report.issues)
    
    def test_metadata_validation_filename_mismatch(self):
        """Test metadata validation with filename mismatch."""
        # Create document
        doc_path = self.temp_dir / "actual_document.txt"
        with open(doc_path, 'wb') as f:
            f.write(b"test content")
        
        # Create audit log with different filename
        audit_log = AuditLog(
            operation=AuditOperation.DOCUMENT_REDACTION,
            timestamp=datetime.now(timezone.utc),
            document_id="test_doc",
            file_paths=["/path/to/different_document.txt"]
        )
        
        report = self.validator.validate_document_integrity(
            document_path=doc_path,
            audit_log_data=audit_log
        )
        
        assert any(issue.type == "filename_mismatch" for issue in report.issues)


class TestCLIIntegration:
    """Test suite for CLI integration functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_cli_validator(self):
        """Test CLI validator creation."""
        validator = create_cli_validator()
        assert isinstance(validator, IntegrityValidator)
        assert validator.crypto is not None
        assert validator.audit_logger is None
        
        # Test with storage path
        validator_with_storage = create_cli_validator(
            storage_path=self.temp_dir,
            enable_signing=True
        )
        assert validator_with_storage.audit_logger is not None
        validator_with_storage.audit_logger.close()
    
    def test_validate_document_cli_success(self):
        """Test CLI validation function with successful validation."""
        # Create test document
        doc_path = self.temp_dir / "test_document.txt"
        test_content = b"Test document for CLI validation"
        
        with open(doc_path, 'wb') as f:
            f.write(test_content)
        
        # Calculate expected hash
        crypto = CryptographicUtils()
        expected_hash = crypto.generate_sha256_hash_from_bytes(test_content)
        
        # Test CLI validation
        exit_code = validate_document_cli(
            document_path=str(doc_path),
            expected_hash=expected_hash,
            verbose=True
        )
        
        assert exit_code == 0
    
    def test_validate_document_cli_failure(self):
        """Test CLI validation function with validation failure."""
        # Create test document
        doc_path = self.temp_dir / "test_document.txt"
        with open(doc_path, 'wb') as f:
            f.write(b"Test document")
        
        # Use wrong expected hash
        wrong_hash = "wrong_hash_value"
        
        # Test CLI validation
        exit_code = validate_document_cli(
            document_path=str(doc_path),
            expected_hash=wrong_hash
        )
        
        assert exit_code == 1
    
    def test_validate_document_cli_error(self):
        """Test CLI validation function with error."""
        # Test with non-existent document
        exit_code = validate_document_cli(
            document_path="/non/existent/document.txt"
        )
        
        assert exit_code == 1  # Missing document returns validation failure
    
    def test_validate_document_cli_with_output(self):
        """Test CLI validation with output file."""
        # Create test document
        doc_path = self.temp_dir / "test_document.txt"
        with open(doc_path, 'wb') as f:
            f.write(b"Test document")
        
        output_path = self.temp_dir / "validation_report.json"
        
        # Test CLI validation with output
        exit_code = validate_document_cli(
            document_path=str(doc_path),
            output_path=str(output_path),
            verbose=True
        )
        
        assert exit_code == 0
        assert output_path.exists()
        
        # Verify output file content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert len(data["reports"]) == 1
        assert data["reports"][0]["document_id"] == "test_document"