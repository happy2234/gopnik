"""
Unit tests for audit logging system.
"""

import pytest
import tempfile
import shutil
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.gopnik.utils.audit_logger import AuditLogger
from src.gopnik.models.audit import AuditLog, AuditTrail, AuditOperation, AuditLevel


class TestAuditLogger:
    """Test suite for AuditLogger class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directory for test storage
        self.temp_dir = Path(tempfile.mkdtemp())
        self.audit_logger = AuditLogger(
            storage_path=self.temp_dir,
            enable_signing=True,
            auto_sign=True
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.audit_logger.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test audit logger initialization."""
        assert self.audit_logger.storage_path == self.temp_dir
        assert self.audit_logger.enable_signing is True
        assert self.audit_logger.auto_sign is True
        
        # Check database file exists
        assert self.audit_logger.db_path.exists()
        
        # Check signing keys exist
        key_path = self.temp_dir / "signing_keys"
        assert key_path.exists()
        assert (key_path / "private_key.pem").exists()
        assert (key_path / "public_key.pem").exists()
    
    def test_database_initialization(self):
        """Test database schema initialization."""
        with sqlite3.connect(self.audit_logger.db_path) as conn:
            # Check tables exist
            tables = conn.execute("""
                SELECT name FROM sqlite_master WHERE type='table'
            """).fetchall()
            
            table_names = [table[0] for table in tables]
            assert 'audit_logs' in table_names
            assert 'audit_trails' in table_names
            
            # Check indexes exist
            indexes = conn.execute("""
                SELECT name FROM sqlite_master WHERE type='index'
            """).fetchall()
            
            index_names = [index[0] for index in indexes]
            assert any('idx_operation' in name for name in index_names)
            assert any('idx_timestamp' in name for name in index_names)
    
    def test_create_audit_trail(self):
        """Test audit trail creation."""
        metadata = {"test": "data", "version": "1.0"}
        trail = self.audit_logger.create_audit_trail("Test Trail", metadata)
        
        assert isinstance(trail, AuditTrail)
        assert trail.name == "Test Trail"
        assert trail.metadata == metadata
        assert len(trail.id) > 0
        
        # Check it's stored in database
        with sqlite3.connect(self.audit_logger.db_path) as conn:
            row = conn.execute("""
                SELECT * FROM audit_trails WHERE id = ?
            """, (trail.id,)).fetchone()
            
            assert row is not None
            assert row[1] == "Test Trail"  # name column
    
    def test_log_operation(self):
        """Test basic operation logging."""
        audit_log = self.audit_logger.log_operation(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            level=AuditLevel.INFO,
            document_id="test_doc_123",
            user_id="user_456"
        )
        
        assert isinstance(audit_log, AuditLog)
        assert audit_log.operation == AuditOperation.DOCUMENT_UPLOAD
        assert audit_log.level == AuditLevel.INFO
        assert audit_log.document_id == "test_doc_123"
        assert audit_log.user_id == "user_456"
        assert audit_log.is_signed()  # Should be auto-signed
        
        # Check it's stored in database
        stored_log = self.audit_logger.get_audit_log(audit_log.id)
        assert stored_log is not None
        assert stored_log.operation == AuditOperation.DOCUMENT_UPLOAD
    
    def test_log_document_operation(self):
        """Test document operation logging."""
        audit_log = self.audit_logger.log_document_operation(
            operation=AuditOperation.PII_DETECTION,
            document_id="doc_789",
            user_id="user_123",
            profile_name="healthcare_hipaa"
        )
        
        assert audit_log.operation == AuditOperation.PII_DETECTION
        assert audit_log.document_id == "doc_789"
        assert audit_log.user_id == "user_123"
        assert audit_log.profile_name == "healthcare_hipaa"
    
    def test_log_error(self):
        """Test error logging."""
        error_message = "Test error occurred"
        audit_log = self.audit_logger.log_error(
            error_message=error_message,
            document_id="error_doc",
            user_id="error_user"
        )
        
        assert audit_log.operation == AuditOperation.ERROR_OCCURRED
        assert audit_log.level == AuditLevel.ERROR
        assert audit_log.error_message == error_message
        assert audit_log.document_id == "error_doc"
        assert audit_log.user_id == "error_user"
    
    def test_log_system_operation(self):
        """Test system operation logging."""
        audit_log = self.audit_logger.log_system_operation(
            operation=AuditOperation.SYSTEM_STARTUP,
            level=AuditLevel.INFO
        )
        
        assert audit_log.operation == AuditOperation.SYSTEM_STARTUP
        assert audit_log.level == AuditLevel.INFO
        assert audit_log.document_id is None
        assert audit_log.user_id is None
    
    def test_signing_and_verification(self):
        """Test audit log signing and verification."""
        # Test with auto-signing disabled
        logger_no_auto = AuditLogger(
            storage_path=self.temp_dir / "no_auto",
            enable_signing=True,
            auto_sign=False
        )
        
        audit_log = logger_no_auto.log_operation(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            document_id="test_doc"
        )
        
        # Should not be signed initially
        assert not audit_log.is_signed()
        
        # Sign manually
        logger_no_auto.sign_audit_log(audit_log)
        assert audit_log.is_signed()
        
        # Verify signature
        is_valid = logger_no_auto.verify_audit_log(audit_log)
        assert is_valid is True
        
        # Test with modified content (should fail verification)
        original_message = audit_log.error_message
        audit_log.error_message = "Modified content"
        is_valid_modified = logger_no_auto.verify_audit_log(audit_log)
        assert is_valid_modified is False
        
        # Restore original content
        audit_log.error_message = original_message
        logger_no_auto.close()
    
    def test_audit_trail_integration(self):
        """Test audit trail integration with logging."""
        # Create trail
        trail = self.audit_logger.create_audit_trail("Integration Test")
        
        # Log some operations
        log1 = self.audit_logger.log_operation(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            document_id="doc1"
        )
        log2 = self.audit_logger.log_operation(
            operation=AuditOperation.PII_DETECTION,
            document_id="doc1"
        )
        log3 = self.audit_logger.log_operation(
            operation=AuditOperation.DOCUMENT_REDACTION,
            document_id="doc1"
        )
        
        # Check trail contains logs
        assert len(trail.logs) == 3
        assert log1 in trail.logs
        assert log2 in trail.logs
        assert log3 in trail.logs
        
        # Retrieve trail from database
        stored_trail = self.audit_logger.get_audit_trail(trail.id)
        assert stored_trail is not None
        assert len(stored_trail.logs) == 3
    
    def test_query_logs(self):
        """Test audit log querying."""
        # Create test logs
        self.audit_logger.log_operation(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            level=AuditLevel.INFO,
            document_id="doc1",
            user_id="user1"
        )
        self.audit_logger.log_operation(
            operation=AuditOperation.PII_DETECTION,
            level=AuditLevel.INFO,
            document_id="doc1",
            user_id="user1"
        )
        self.audit_logger.log_operation(
            operation=AuditOperation.ERROR_OCCURRED,
            level=AuditLevel.ERROR,
            document_id="doc2",
            user_id="user2"
        )
        
        # Query by operation
        upload_logs = self.audit_logger.query_logs(operation=AuditOperation.DOCUMENT_UPLOAD)
        assert len(upload_logs) == 1
        assert upload_logs[0].operation == AuditOperation.DOCUMENT_UPLOAD
        
        # Query by level
        error_logs = self.audit_logger.query_logs(level=AuditLevel.ERROR)
        assert len(error_logs) == 1
        assert error_logs[0].level == AuditLevel.ERROR
        
        # Query by document ID
        doc1_logs = self.audit_logger.query_logs(document_id="doc1")
        assert len(doc1_logs) == 2
        
        # Query by user ID
        user1_logs = self.audit_logger.query_logs(user_id="user1")
        assert len(user1_logs) == 2
        
        # Query with limit
        limited_logs = self.audit_logger.query_logs(limit=1)
        assert len(limited_logs) == 1
    
    def test_query_logs_with_time_range(self):
        """Test querying logs with time range."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)
        
        # Create log
        audit_log = self.audit_logger.log_operation(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            document_id="time_test"
        )
        
        # Query with time range that includes the log
        logs_in_range = self.audit_logger.query_logs(
            start_time=past,
            end_time=future
        )
        assert len(logs_in_range) >= 1
        assert any(log.id == audit_log.id for log in logs_in_range)
        
        # Query with time range that excludes the log
        logs_out_of_range = self.audit_logger.query_logs(
            start_time=past,
            end_time=past + timedelta(minutes=30)
        )
        assert not any(log.id == audit_log.id for log in logs_out_of_range)
    
    def test_export_to_json(self):
        """Test JSON export functionality."""
        # Create test logs
        self.audit_logger.log_operation(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            document_id="export_test"
        )
        self.audit_logger.log_operation(
            operation=AuditOperation.PII_DETECTION,
            document_id="export_test"
        )
        
        # Export to JSON
        output_path = self.temp_dir / "export_test.json"
        count = self.audit_logger.export_logs_to_json(
            output_path,
            document_id="export_test"
        )
        
        assert count == 2
        assert output_path.exists()
        
        # Verify JSON content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['total_logs'] == 2
        assert len(data['logs']) == 2
        assert 'export_timestamp' in data
        assert 'query_params' in data
    
    def test_export_to_csv(self):
        """Test CSV export functionality."""
        # Create test logs
        self.audit_logger.log_operation(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            document_id="csv_test"
        )
        
        # Export to CSV
        output_path = self.temp_dir / "export_test.csv"
        count = self.audit_logger.export_logs_to_csv(
            output_path,
            document_id="csv_test"
        )
        
        assert count == 1
        assert output_path.exists()
        
        # Verify CSV content
        with open(output_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) >= 2  # Header + at least one data row
        assert 'ID' in lines[0]  # Check header
        assert 'Operation' in lines[0]
    
    def test_validate_all_logs(self):
        """Test validation of all logs."""
        # Create some logs
        self.audit_logger.log_operation(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            document_id="validate_test1"
        )
        self.audit_logger.log_operation(
            operation=AuditOperation.PII_DETECTION,
            document_id="validate_test2"
        )
        
        # Validate all logs
        total, valid, issues = self.audit_logger.validate_all_logs()
        
        assert total >= 2
        assert valid >= 2  # Should be valid since auto-signing is enabled
        assert len(issues) == 0  # No issues expected
    
    def test_statistics(self):
        """Test statistics generation."""
        # Create test logs
        self.audit_logger.log_operation(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            level=AuditLevel.INFO
        )
        self.audit_logger.log_operation(
            operation=AuditOperation.ERROR_OCCURRED,
            level=AuditLevel.ERROR
        )
        
        stats = self.audit_logger.get_statistics()
        
        assert 'total_logs' in stats
        assert 'operations' in stats
        assert 'levels' in stats
        assert 'signed_logs' in stats
        assert 'error_logs' in stats
        assert 'signing_enabled' in stats
        assert stats['signing_enabled'] is True
        assert stats['total_logs'] >= 2
    
    def test_cleanup_old_logs(self):
        """Test cleanup of old logs."""
        # Create old log by manually inserting with old timestamp
        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()
        
        with sqlite3.connect(self.audit_logger.db_path) as conn:
            conn.execute("""
                INSERT INTO audit_logs (
                    id, operation, timestamp, level
                ) VALUES (?, ?, ?, ?)
            """, (
                "old_log_id",
                AuditOperation.DOCUMENT_UPLOAD.value,
                old_timestamp,
                AuditLevel.INFO.value
            ))
            conn.commit()
        
        # Create recent log
        self.audit_logger.log_operation(
            operation=AuditOperation.DOCUMENT_UPLOAD
        )
        
        # Cleanup with 365 day retention
        deleted_count = self.audit_logger.cleanup_old_logs(retention_days=365)
        
        assert deleted_count >= 1
        
        # Verify old log is gone
        old_log = self.audit_logger.get_audit_log("old_log_id")
        assert old_log is None
    
    def test_set_current_trail(self):
        """Test setting current audit trail."""
        # Create trail
        trail = self.audit_logger.create_audit_trail("Test Trail")
        trail_id = trail.id
        
        # Create new logger instance
        logger2 = AuditLogger(storage_path=self.temp_dir / "logger2")
        
        # Set current trail
        retrieved_trail = logger2.set_current_trail(trail_id)
        
        assert retrieved_trail is None  # Trail doesn't exist in logger2's database
        
        # Test with existing trail
        current_trail = self.audit_logger.set_current_trail(trail_id)
        assert current_trail is not None
        assert current_trail.id == trail_id
        assert self.audit_logger.current_trail == current_trail
        
        logger2.close()
    
    def test_signing_disabled(self):
        """Test audit logger with signing disabled."""
        logger_no_sign = AuditLogger(
            storage_path=self.temp_dir / "no_sign",
            enable_signing=False
        )
        
        audit_log = logger_no_sign.log_operation(
            operation=AuditOperation.DOCUMENT_UPLOAD
        )
        
        # Should not be signed
        assert not audit_log.is_signed()
        
        # Verification should return False for unsigned logs
        is_valid = logger_no_sign.verify_audit_log(audit_log)
        assert is_valid is False
        
        logger_no_sign.close()
    
    def test_thread_safety(self):
        """Test thread safety of audit logger."""
        import threading
        import time
        
        results = []
        errors = []
        
        def log_operations(thread_id):
            try:
                for i in range(10):
                    audit_log = self.audit_logger.log_operation(
                        operation=AuditOperation.DOCUMENT_UPLOAD,
                        document_id=f"thread_{thread_id}_doc_{i}",
                        user_id=f"thread_{thread_id}_user"
                    )
                    results.append(audit_log.id)
                    time.sleep(0.001)  # Small delay to increase chance of race conditions
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_operations, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 50  # 5 threads * 10 operations each
        assert len(set(results)) == 50  # All IDs should be unique
    
    def test_error_handling(self):
        """Test error handling in audit logger."""
        # Test with invalid storage path (should handle gracefully)
        with pytest.raises(Exception):
            invalid_logger = AuditLogger(storage_path=Path("/invalid/path/that/does/not/exist"))
    
    def test_get_nonexistent_log(self):
        """Test retrieving non-existent audit log."""
        log = self.audit_logger.get_audit_log("nonexistent_id")
        assert log is None
    
    def test_get_nonexistent_trail(self):
        """Test retrieving non-existent audit trail."""
        trail = self.audit_logger.get_audit_trail("nonexistent_id")
        assert trail is None
    
    def test_complex_audit_log_data(self):
        """Test audit log with complex data structures."""
        complex_details = {
            "nested": {"data": "value"},
            "list": [1, 2, 3],
            "boolean": True,
            "null_value": None
        }
        
        audit_log = self.audit_logger.log_operation(
            operation=AuditOperation.PII_DETECTION,
            document_id="complex_test",
            details=complex_details,
            file_paths=["/path/1", "/path/2"],
            warning_messages=["Warning 1", "Warning 2"]
        )
        
        # Retrieve and verify
        stored_log = self.audit_logger.get_audit_log(audit_log.id)
        assert stored_log is not None
        assert stored_log.details == complex_details
        assert stored_log.file_paths == ["/path/1", "/path/2"]
        assert stored_log.warning_messages == ["Warning 1", "Warning 2"]