"""
Unit tests for audit log and integrity validation data models.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List
from unittest.mock import patch

from src.gopnik.models.audit import (
    AuditLog, AuditTrail, SystemInfo, AuditOperation, AuditLevel,
    create_document_processing_audit_chain, validate_audit_log_integrity,
    merge_audit_trails, filter_audit_logs
)


class TestAuditOperation:
    """Test AuditOperation enum functionality."""
    
    def test_operation_values(self):
        """Test operation enum values."""
        assert AuditOperation.DOCUMENT_UPLOAD.value == "document_upload"
        assert AuditOperation.PII_DETECTION.value == "pii_detection"
        assert AuditOperation.DOCUMENT_REDACTION.value == "document_redaction"
        assert AuditOperation.ERROR_OCCURRED.value == "error_occurred"


class TestAuditLevel:
    """Test AuditLevel enum functionality."""
    
    def test_level_values(self):
        """Test level enum values."""
        assert AuditLevel.DEBUG.value == "debug"
        assert AuditLevel.INFO.value == "info"
        assert AuditLevel.WARNING.value == "warning"
        assert AuditLevel.ERROR.value == "error"
        assert AuditLevel.CRITICAL.value == "critical"


class TestSystemInfo:
    """Test SystemInfo class functionality."""
    
    def test_system_info_creation(self):
        """Test system info creation with defaults."""
        system_info = SystemInfo()
        
        assert len(system_info.hostname) > 0
        assert len(system_info.platform) > 0
        assert len(system_info.python_version) > 0
        assert system_info.gopnik_version == "0.1.0"
        assert system_info.cpu_count >= 1
    
    def test_system_info_serialization(self):
        """Test system info serialization."""
        system_info = SystemInfo(
            hostname="test-host",
            gopnik_version="1.0.0",
            memory_total=8192.0,
            disk_space=500000.0
        )
        
        # Test to_dict
        info_dict = system_info.to_dict()
        assert info_dict['hostname'] == "test-host"
        assert info_dict['gopnik_version'] == "1.0.0"
        assert info_dict['memory_total'] == 8192.0
        
        # Test from_dict
        restored = SystemInfo.from_dict(info_dict)
        assert restored.hostname == system_info.hostname
        assert restored.gopnik_version == system_info.gopnik_version
        assert restored.memory_total == system_info.memory_total


class TestAuditLog:
    """Test AuditLog class functionality."""
    
    def test_audit_log_creation(self):
        """Test basic audit log creation."""
        audit_log = AuditLog(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            timestamp=datetime.now(timezone.utc),
            document_id="doc_123",
            user_id="user_456"
        )
        
        assert audit_log.operation == AuditOperation.DOCUMENT_UPLOAD
        assert audit_log.document_id == "doc_123"
        assert audit_log.user_id == "user_456"
        assert audit_log.level == AuditLevel.INFO  # Default level
        assert len(audit_log.id) > 0
    
    def test_timestamp_utc_conversion(self):
        """Test automatic UTC conversion of timestamps."""
        # Create timestamp without timezone
        naive_time = datetime(2024, 1, 1, 12, 0, 0)
        
        audit_log = AuditLog(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            timestamp=naive_time
        )
        
        assert audit_log.timestamp.tzinfo == timezone.utc
    
    def test_string_enum_conversion(self):
        """Test conversion of string enums."""
        audit_log = AuditLog(
            operation="document_upload",  # String instead of enum
            timestamp=datetime.now(timezone.utc),
            level="error"  # String instead of enum
        )
        
        assert audit_log.operation == AuditOperation.DOCUMENT_UPLOAD
        assert audit_log.level == AuditLevel.ERROR
    
    def test_class_methods(self):
        """Test audit log class methods."""
        # Test create_document_operation
        doc_log = AuditLog.create_document_operation(
            operation=AuditOperation.PII_DETECTION,
            document_id="doc_123",
            user_id="user_456",
            profile_name="healthcare"
        )
        
        assert doc_log.operation == AuditOperation.PII_DETECTION
        assert doc_log.document_id == "doc_123"
        assert doc_log.user_id == "user_456"
        assert doc_log.profile_name == "healthcare"
        
        # Test create_system_operation
        sys_log = AuditLog.create_system_operation(
            operation=AuditOperation.SYSTEM_STARTUP,
            level=AuditLevel.INFO
        )
        
        assert sys_log.operation == AuditOperation.SYSTEM_STARTUP
        assert sys_log.level == AuditLevel.INFO
        assert sys_log.document_id is None
        
        # Test create_error_log
        error_log = AuditLog.create_error_log(
            error_message="Test error occurred",
            document_id="doc_123",
            user_id="user_456"
        )
        
        assert error_log.operation == AuditOperation.ERROR_OCCURRED
        assert error_log.level == AuditLevel.ERROR
        assert error_log.error_message == "Test error occurred"
        assert error_log.document_id == "doc_123"
    
    def test_detection_summary(self):
        """Test detection summary functionality."""
        audit_log = AuditLog(
            operation=AuditOperation.PII_DETECTION,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Mock detections
        class MockDetection:
            def __init__(self, pii_type):
                self.type = MockType(pii_type)
        
        class MockType:
            def __init__(self, value):
                self.value = value
        
        detections = [
            MockDetection("face"),
            MockDetection("face"),
            MockDetection("email"),
            MockDetection("phone")
        ]
        
        audit_log.add_detection_summary(detections)
        
        expected_summary = {"face": 2, "email": 1, "phone": 1}
        assert audit_log.detections_summary == expected_summary
    
    def test_file_path_management(self):
        """Test file path management."""
        audit_log = AuditLog(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add file paths
        audit_log.add_file_path("/path/to/input.pdf")
        audit_log.add_file_path(Path("/path/to/output.pdf"))
        audit_log.add_file_path("/path/to/input.pdf")  # Duplicate
        
        assert len(audit_log.file_paths) == 2  # No duplicates
        assert "/path/to/input.pdf" in audit_log.file_paths
        assert "/path/to/output.pdf" in audit_log.file_paths
    
    def test_warning_management(self):
        """Test warning message management."""
        audit_log = AuditLog(
            operation=AuditOperation.PII_DETECTION,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add warnings
        audit_log.add_warning("Low confidence detection")
        audit_log.add_warning("Processing took longer than expected")
        audit_log.add_warning("Low confidence detection")  # Duplicate
        
        assert len(audit_log.warning_messages) == 2  # No duplicates
        assert "Low confidence detection" in audit_log.warning_messages
        assert "Processing took longer than expected" in audit_log.warning_messages
    
    def test_processing_metrics(self):
        """Test processing metrics setting."""
        audit_log = AuditLog(
            operation=AuditOperation.DOCUMENT_REDACTION,
            timestamp=datetime.now(timezone.utc)
        )
        
        audit_log.set_processing_metrics(
            processing_time=5.2,
            memory_usage=256.5
        )
        
        assert audit_log.processing_time == 5.2
        assert audit_log.memory_usage == 256.5
    
    def test_child_log_creation(self):
        """Test child audit log creation."""
        parent_log = AuditLog(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            timestamp=datetime.now(timezone.utc),
            document_id="doc_123",
            user_id="user_456",
            session_id="session_789"
        )
        
        child_log = parent_log.create_child_log(
            operation=AuditOperation.PII_DETECTION,
            profile_name="healthcare"
        )
        
        assert child_log.parent_id == parent_log.id
        assert child_log.chain_id == parent_log.id  # First child gets parent ID as chain
        assert child_log.document_id == parent_log.document_id
        assert child_log.user_id == parent_log.user_id
        assert child_log.session_id == parent_log.session_id
        assert child_log.profile_name == "healthcare"
    
    def test_content_hash(self):
        """Test content hash generation."""
        audit_log = AuditLog(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            timestamp=datetime.now(timezone.utc),
            document_id="doc_123"
        )
        
        # Get hash before signing
        hash1 = audit_log.get_content_hash()
        assert len(hash1) == 64  # SHA-256 hex length
        
        # Add signature and get hash again (should be same)
        audit_log.signature = "test_signature"
        hash2 = audit_log.get_content_hash()
        assert hash1 == hash2  # Signature excluded from hash
        
        # Modify content and get hash (should be different)
        audit_log.document_id = "doc_456"
        hash3 = audit_log.get_content_hash()
        assert hash1 != hash3
    
    def test_status_checks(self):
        """Test audit log status check methods."""
        # Error log
        error_log = AuditLog(
            operation=AuditOperation.ERROR_OCCURRED,
            timestamp=datetime.now(timezone.utc),
            level=AuditLevel.ERROR
        )
        
        assert error_log.is_error() is True
        assert error_log.is_warning() is False
        
        # Warning log
        warning_log = AuditLog(
            operation=AuditOperation.PII_DETECTION,
            timestamp=datetime.now(timezone.utc),
            level=AuditLevel.WARNING
        )
        
        assert warning_log.is_error() is False
        assert warning_log.is_warning() is True
        
        # Log with warning messages
        info_log = AuditLog(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            timestamp=datetime.now(timezone.utc),
            level=AuditLevel.INFO
        )
        info_log.add_warning("Test warning")
        
        assert info_log.is_error() is False
        assert info_log.is_warning() is True  # Has warning messages
        
        # Signed log
        signed_log = AuditLog(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            timestamp=datetime.now(timezone.utc),
            signature="test_signature"
        )
        
        assert signed_log.is_signed() is True
    
    def test_duration_calculation(self):
        """Test duration calculation between logs."""
        time1 = datetime.now(timezone.utc)
        time2 = time1 + timedelta(seconds=5)
        
        log1 = AuditLog(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            timestamp=time1
        )
        
        log2 = AuditLog(
            operation=AuditOperation.PII_DETECTION,
            timestamp=time2
        )
        
        duration = log2.get_duration_since(log1)
        assert abs(duration - 5.0) < 0.1  # Allow small floating point differences
    
    def test_audit_log_serialization(self):
        """Test audit log serialization."""
        system_info = SystemInfo(hostname="test-host")
        
        audit_log = AuditLog(
            operation=AuditOperation.DOCUMENT_REDACTION,
            timestamp=datetime.now(timezone.utc),
            level=AuditLevel.INFO,
            document_id="doc_123",
            user_id="user_456",
            profile_name="healthcare",
            system_info=system_info
        )
        
        audit_log.add_file_path("/test/path.pdf")
        audit_log.add_warning("Test warning")
        audit_log.set_processing_metrics(3.5, 128.0)
        
        # Test to_dict
        log_dict = audit_log.to_dict()
        assert log_dict['operation'] == 'document_redaction'
        assert log_dict['level'] == 'info'
        assert log_dict['document_id'] == 'doc_123'
        assert log_dict['system_info']['hostname'] == 'test-host'
        assert len(log_dict['file_paths']) == 1
        assert len(log_dict['warning_messages']) == 1
        
        # Test from_dict
        restored = AuditLog.from_dict(log_dict)
        assert restored.operation == audit_log.operation
        assert restored.level == audit_log.level
        assert restored.document_id == audit_log.document_id
        assert restored.system_info.hostname == audit_log.system_info.hostname
        
        # Test JSON serialization
        json_str = audit_log.to_json()
        restored_from_json = AuditLog.from_json(json_str)
        assert restored_from_json.id == audit_log.id
    
    def test_csv_export(self):
        """Test CSV export functionality."""
        audit_log = AuditLog(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            timestamp=datetime.now(timezone.utc),
            document_id="doc_123",
            user_id="user_456"
        )
        
        # Test CSV headers
        headers = AuditLog.get_csv_headers()
        assert 'ID' in headers
        assert 'Operation' in headers
        assert 'Timestamp' in headers
        assert 'Document ID' in headers
        
        # Test CSV row
        row = audit_log.to_csv_row()
        assert len(row) == len(headers)
        assert row[0] == audit_log.id
        assert row[1] == 'document_upload'
        assert row[4] == 'doc_123'
        assert row[5] == 'user_456'


class TestAuditTrail:
    """Test AuditTrail class functionality."""
    
    def create_sample_logs(self, count: int = 3) -> List[AuditLog]:
        """Create sample audit logs."""
        logs = []
        base_time = datetime.now(timezone.utc)
        
        for i in range(count):
            log = AuditLog(
                operation=AuditOperation.DOCUMENT_UPLOAD,
                timestamp=base_time + timedelta(seconds=i),
                document_id=f"doc_{i}",
                user_id=f"user_{i % 2}"  # Alternate between 2 users
            )
            logs.append(log)
        
        return logs
    
    def test_audit_trail_creation(self):
        """Test audit trail creation."""
        logs = self.create_sample_logs(3)
        
        trail = AuditTrail(
            id="trail_123",
            name="Test Trail",
            logs=logs
        )
        
        assert trail.id == "trail_123"
        assert trail.name == "Test Trail"
        assert len(trail.logs) == 3
    
    def test_log_filtering(self):
        """Test audit log filtering methods."""
        logs = [
            AuditLog(
                operation=AuditOperation.DOCUMENT_UPLOAD,
                timestamp=datetime.now(timezone.utc),
                document_id="doc_1",
                user_id="user_1"
            ),
            AuditLog(
                operation=AuditOperation.PII_DETECTION,
                timestamp=datetime.now(timezone.utc),
                document_id="doc_1",
                user_id="user_1"
            ),
            AuditLog(
                operation=AuditOperation.ERROR_OCCURRED,
                timestamp=datetime.now(timezone.utc),
                level=AuditLevel.ERROR,
                document_id="doc_2",
                user_id="user_2",
                error_message="Test error"
            )
        ]
        
        trail = AuditTrail(id="trail_123", name="Test Trail", logs=logs)
        
        # Test filtering by operation
        upload_logs = trail.get_logs_by_operation(AuditOperation.DOCUMENT_UPLOAD)
        assert len(upload_logs) == 1
        assert upload_logs[0].operation == AuditOperation.DOCUMENT_UPLOAD
        
        # Test filtering by document
        doc1_logs = trail.get_logs_by_document("doc_1")
        assert len(doc1_logs) == 2
        
        # Test filtering by user
        user1_logs = trail.get_logs_by_user("user_1")
        assert len(user1_logs) == 2
        
        # Test filtering by level
        error_logs = trail.get_logs_by_level(AuditLevel.ERROR)
        assert len(error_logs) == 1
        
        # Test error and warning getters
        assert len(trail.get_error_logs()) == 1
        assert len(trail.get_warning_logs()) == 0
    
    def test_timeframe_filtering(self):
        """Test timeframe filtering."""
        base_time = datetime.now(timezone.utc)
        logs = [
            AuditLog(
                operation=AuditOperation.DOCUMENT_UPLOAD,
                timestamp=base_time,
                document_id="doc_1"
            ),
            AuditLog(
                operation=AuditOperation.PII_DETECTION,
                timestamp=base_time + timedelta(hours=1),
                document_id="doc_1"
            ),
            AuditLog(
                operation=AuditOperation.DOCUMENT_REDACTION,
                timestamp=base_time + timedelta(hours=2),
                document_id="doc_1"
            )
        ]
        
        trail = AuditTrail(id="trail_123", name="Test Trail", logs=logs)
        
        # Filter for middle hour
        start_time = base_time + timedelta(minutes=30)
        end_time = base_time + timedelta(hours=1, minutes=30)
        
        filtered_logs = trail.get_logs_in_timeframe(start_time, end_time)
        assert len(filtered_logs) == 1
        assert filtered_logs[0].operation == AuditOperation.PII_DETECTION
    
    def test_chain_operations(self):
        """Test chain-related operations."""
        # Create a processing chain
        chain_id = "chain_123"
        
        upload_log = AuditLog(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            timestamp=datetime.now(timezone.utc),
            document_id="doc_1",
            chain_id=chain_id
        )
        
        detection_log = AuditLog(
            operation=AuditOperation.PII_DETECTION,
            timestamp=datetime.now(timezone.utc),
            document_id="doc_1",
            chain_id=chain_id,
            parent_id=upload_log.id
        )
        
        redaction_log = AuditLog(
            operation=AuditOperation.DOCUMENT_REDACTION,
            timestamp=datetime.now(timezone.utc),
            document_id="doc_1",
            chain_id=chain_id,
            parent_id=detection_log.id
        )
        
        trail = AuditTrail(
            id="trail_123",
            name="Test Trail",
            logs=[upload_log, detection_log, redaction_log]
        )
        
        # Test chain filtering
        chain_logs = trail.get_chain_logs(chain_id)
        assert len(chain_logs) == 3
        
        # Test document processing chain
        doc_chain = trail.get_document_processing_chain("doc_1")
        assert len(doc_chain) == 3
        assert doc_chain[0].operation == AuditOperation.DOCUMENT_UPLOAD
        assert doc_chain[1].operation == AuditOperation.PII_DETECTION
        assert doc_chain[2].operation == AuditOperation.DOCUMENT_REDACTION
    
    def test_integrity_validation(self):
        """Test audit trail integrity validation."""
        # Create valid trail
        logs = self.create_sample_logs(3)
        trail = AuditTrail(id="trail_123", name="Test Trail", logs=logs)
        
        is_valid, issues = trail.validate_integrity()
        assert is_valid is True
        assert len(issues) == 0
        
        # Create trail with duplicate IDs
        logs_with_duplicates = self.create_sample_logs(2)
        logs_with_duplicates[1].id = logs_with_duplicates[0].id  # Duplicate ID
        
        invalid_trail = AuditTrail(id="trail_456", name="Invalid Trail", logs=logs_with_duplicates)
        
        is_valid, issues = invalid_trail.validate_integrity()
        assert is_valid is False
        assert any("Duplicate audit log IDs" in issue for issue in issues)
    
    def test_statistics(self):
        """Test audit trail statistics."""
        logs = [
            AuditLog(
                operation=AuditOperation.DOCUMENT_UPLOAD,
                timestamp=datetime.now(timezone.utc),
                level=AuditLevel.INFO,
                document_id="doc_1",
                user_id="user_1"
            ),
            AuditLog(
                operation=AuditOperation.PII_DETECTION,
                timestamp=datetime.now(timezone.utc),
                level=AuditLevel.INFO,
                document_id="doc_1",
                user_id="user_1"
            ),
            AuditLog(
                operation=AuditOperation.ERROR_OCCURRED,
                timestamp=datetime.now(timezone.utc),
                level=AuditLevel.ERROR,
                document_id="doc_2",
                user_id="user_2",
                signature="test_signature"
            )
        ]
        
        trail = AuditTrail(id="trail_123", name="Test Trail", logs=logs)
        
        stats = trail.get_statistics()
        
        assert stats['total_logs'] == 3
        assert stats['operations']['document_upload'] == 1
        assert stats['operations']['pii_detection'] == 1
        assert stats['operations']['error_occurred'] == 1
        assert stats['levels']['info'] == 2
        assert stats['levels']['error'] == 1
        assert stats['users']['user_1'] == 2
        assert stats['users']['user_2'] == 1
        assert stats['documents']['doc_1'] == 2
        assert stats['documents']['doc_2'] == 1
        assert stats['error_count'] == 1
        assert stats['warning_count'] == 0
        assert stats['signed_count'] == 1
        assert stats['timespan'] is not None
    
    def test_csv_export(self):
        """Test CSV export functionality."""
        logs = self.create_sample_logs(2)
        trail = AuditTrail(id="trail_123", name="Test Trail", logs=logs)
        
        # Test export (mock file operations)
        with patch('builtins.open', create=True) as mock_open:
            mock_file = mock_open.return_value.__enter__.return_value
            
            trail.export_to_csv(Path("test.csv"))
            
            # Verify file was opened for writing
            mock_open.assert_called_once_with(Path("test.csv"), 'w', newline='', encoding='utf-8')
            
            # Verify write calls were made
            assert mock_file.writerow.call_count >= 3  # Headers + 2 data rows
    
    def test_audit_trail_serialization(self):
        """Test audit trail serialization."""
        logs = self.create_sample_logs(2)
        trail = AuditTrail(
            id="trail_123",
            name="Test Trail",
            logs=logs,
            metadata={"source": "test"}
        )
        
        # Test to_dict
        trail_dict = trail.to_dict()
        assert trail_dict['id'] == "trail_123"
        assert trail_dict['name'] == "Test Trail"
        assert len(trail_dict['logs']) == 2
        assert trail_dict['metadata']['source'] == "test"
        assert 'statistics' in trail_dict
        
        # Test from_dict
        restored = AuditTrail.from_dict(trail_dict)
        assert restored.id == trail.id
        assert restored.name == trail.name
        assert len(restored.logs) == len(trail.logs)
        assert restored.metadata == trail.metadata
        
        # Test JSON serialization
        json_str = trail.to_json()
        restored_from_json = AuditTrail.from_json(json_str)
        assert restored_from_json.id == trail.id


class TestUtilityFunctions:
    """Test utility functions for audit operations."""
    
    def test_create_document_processing_audit_chain(self):
        """Test document processing audit chain creation."""
        chain_logs = create_document_processing_audit_chain(
            document_id="doc_123",
            user_id="user_456",
            profile_name="healthcare"
        )
        
        assert len(chain_logs) == 3
        
        # Check operations
        assert chain_logs[0].operation == AuditOperation.DOCUMENT_UPLOAD
        assert chain_logs[1].operation == AuditOperation.PII_DETECTION
        assert chain_logs[2].operation == AuditOperation.DOCUMENT_REDACTION
        
        # Check chain linking
        chain_id = chain_logs[0].chain_id
        assert all(log.chain_id == chain_id for log in chain_logs)
        assert chain_logs[1].parent_id == chain_logs[0].id
        assert chain_logs[2].parent_id == chain_logs[1].id
        
        # Check common attributes
        assert all(log.document_id == "doc_123" for log in chain_logs)
        assert all(log.user_id == "user_456" for log in chain_logs)
        assert chain_logs[1].profile_name == "healthcare"
        assert chain_logs[2].profile_name == "healthcare"
    
    def test_validate_audit_log_integrity(self):
        """Test audit log integrity validation."""
        # Valid log
        valid_log = AuditLog(
            operation=AuditOperation.DOCUMENT_UPLOAD,
            timestamp=datetime.now(timezone.utc),
            document_id="doc_123"
        )
        
        is_valid, issues = validate_audit_log_integrity(valid_log)
        assert is_valid is True
        assert len(issues) == 0
        
        # Invalid log - missing document ID for document operation
        invalid_log = AuditLog(
            operation=AuditOperation.PII_DETECTION,
            timestamp=datetime.now(timezone.utc)
            # Missing document_id
        )
        
        is_valid, issues = validate_audit_log_integrity(invalid_log)
        assert is_valid is False
        assert any("Document ID required" in issue for issue in issues)
        
        # Invalid log - error without error message
        error_log = AuditLog(
            operation=AuditOperation.ERROR_OCCURRED,
            timestamp=datetime.now(timezone.utc),
            level=AuditLevel.ERROR
            # Missing error_message
        )
        
        is_valid, issues = validate_audit_log_integrity(error_log)
        assert is_valid is False
        assert any("Error audit log missing error message" in issue for issue in issues)
    
    def test_merge_audit_trails(self):
        """Test audit trail merging."""
        # Create multiple trails
        trail1_logs = [
            AuditLog(
                operation=AuditOperation.DOCUMENT_UPLOAD,
                timestamp=datetime.now(timezone.utc),
                document_id="doc_1"
            )
        ]
        
        trail2_logs = [
            AuditLog(
                operation=AuditOperation.PII_DETECTION,
                timestamp=datetime.now(timezone.utc) + timedelta(seconds=1),
                document_id="doc_2"
            )
        ]
        
        trail1 = AuditTrail(id="trail_1", name="Trail 1", logs=trail1_logs)
        trail2 = AuditTrail(id="trail_2", name="Trail 2", logs=trail2_logs)
        
        # Merge trails
        merged_trail = merge_audit_trails([trail1, trail2])
        
        assert len(merged_trail.logs) == 2
        assert "Merged Trail" in merged_trail.name
        assert merged_trail.metadata['source_count'] == 2
        assert merged_trail.metadata['total_logs'] == 2
        assert trail1.id in merged_trail.metadata['source_trails']
        assert trail2.id in merged_trail.metadata['source_trails']
        
        # Test empty merge
        empty_trail = merge_audit_trails([])
        assert len(empty_trail.logs) == 0
        assert "Empty Merged Trail" in empty_trail.name
    
    def test_filter_audit_logs(self):
        """Test audit log filtering function."""
        base_time = datetime.now(timezone.utc)
        
        logs = [
            AuditLog(
                operation=AuditOperation.DOCUMENT_UPLOAD,
                timestamp=base_time,
                level=AuditLevel.INFO,
                document_id="doc_1",
                user_id="user_1"
            ),
            AuditLog(
                operation=AuditOperation.PII_DETECTION,
                timestamp=base_time + timedelta(seconds=1),
                level=AuditLevel.INFO,
                document_id="doc_1",
                user_id="user_1"
            ),
            AuditLog(
                operation=AuditOperation.ERROR_OCCURRED,
                timestamp=base_time + timedelta(seconds=2),
                level=AuditLevel.ERROR,
                document_id="doc_2",
                user_id="user_2"
            )
        ]
        
        # Filter by operation
        upload_logs = filter_audit_logs(logs, operation=AuditOperation.DOCUMENT_UPLOAD)
        assert len(upload_logs) == 1
        assert upload_logs[0].operation == AuditOperation.DOCUMENT_UPLOAD
        
        # Filter by level
        error_logs = filter_audit_logs(logs, level=AuditLevel.ERROR)
        assert len(error_logs) == 1
        assert error_logs[0].level == AuditLevel.ERROR
        
        # Filter by document
        doc1_logs = filter_audit_logs(logs, document_id="doc_1")
        assert len(doc1_logs) == 2
        
        # Filter by user
        user1_logs = filter_audit_logs(logs, user_id="user_1")
        assert len(user1_logs) == 2
        
        # Filter by time range
        start_time = base_time + timedelta(milliseconds=500)
        end_time = base_time + timedelta(seconds=1, milliseconds=500)
        
        time_filtered = filter_audit_logs(logs, start_time=start_time, end_time=end_time)
        assert len(time_filtered) == 1
        assert time_filtered[0].operation == AuditOperation.PII_DETECTION
        
        # Multiple filters
        combined_filtered = filter_audit_logs(
            logs,
            document_id="doc_1",
            user_id="user_1",
            level=AuditLevel.INFO
        )
        assert len(combined_filtered) == 2


if __name__ == "__main__":
    pytest.main([__file__])