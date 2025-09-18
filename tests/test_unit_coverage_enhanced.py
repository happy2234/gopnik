"""
Enhanced unit tests to improve test coverage.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
import json
import yaml
from datetime import datetime

from tests.test_utils import (
    TestDataGenerator, MockAIEngine, MockDocumentProcessor,
    TestAssertions, temp_dir, performance_test, unit_test
)

# Import available classes and functions
from src.gopnik.models.pii import (
    PIIType, BoundingBox, PIIDetection, PIIDetectionCollection,
    validate_detection_confidence, validate_coordinates
)
from src.gopnik.models.processing import (
    ProcessingResult, ProcessingStatus, ProcessingMetrics,
    validate_processing_result
)
from src.gopnik.models.profiles import (
    RedactionProfile, ProfileValidationError, ProfileManager
)
from src.gopnik.models.audit import (
    AuditLog, AuditOperation, AuditLevel, AuditTrail
)
from src.gopnik.utils.crypto import CryptographicUtils
from src.gopnik.utils.file_utils import FileUtils, TempFileManager
from src.gopnik.config.settings import WebSettings, CLISettings, APISettings, AIEngineSettings, SecuritySettings
from src.gopnik.config.config import GopnikConfig


@unit_test
class TestPIIUtilityFunctions:
    """Test PII utility functions for comprehensive coverage."""
    
    def test_validate_detection_confidence(self):
        """Test detection confidence validation."""
        # Valid confidence values
        assert validate_detection_confidence(0.0) is True
        assert validate_detection_confidence(0.5) is True
        assert validate_detection_confidence(1.0) is True
        
        # Invalid confidence values
        assert validate_detection_confidence(-0.1) is False
        assert validate_detection_confidence(1.1) is False
        assert validate_detection_confidence(None) is False
        assert validate_detection_confidence("0.5") is False
    
    def test_validate_coordinates_with_bbox(self):
        """Test coordinate validation with BoundingBox."""
        # Valid bounding box
        bbox = BoundingBox(0, 0, 100, 100)
        assert validate_coordinates(bbox) is True
        
        # Invalid bounding box (will raise exception during creation)
        with pytest.raises(ValueError):
            invalid_bbox = BoundingBox(-1, 0, 100, 100)
            validate_coordinates(invalid_bbox)
    
    def test_validate_coordinates_with_tuple(self):
        """Test coordinate validation with tuple."""
        # Valid coordinates
        assert validate_coordinates((0, 0, 100, 100)) is True
        assert validate_coordinates((10, 20, 110, 120)) is True
        
        # Invalid coordinates
        assert validate_coordinates((-1, 0, 100, 100)) is False  # Negative
        assert validate_coordinates((100, 0, 100, 100)) is False  # x1 >= x2
        assert validate_coordinates((0, 100, 100, 100)) is False  # y1 >= y2


@unit_test
class TestPIIDetectionCollection:
    """Test PIIDetectionCollection functionality."""
    
    def test_collection_creation(self, test_pii_detections):
        """Test creating a detection collection."""
        collection = PIIDetectionCollection(detections=test_pii_detections)
        
        assert len(collection.detections) == len(test_pii_detections)
        assert collection.document_id is not None
        assert isinstance(collection.created_at, datetime)
    
    def test_collection_filtering(self, test_pii_detections):
        """Test collection filtering methods."""
        collection = PIIDetectionCollection(detections=test_pii_detections)
        
        # Filter by type
        name_detections = collection.filter_by_type(PIIType.PERSON_NAME)
        assert all(d.type == PIIType.PERSON_NAME for d in name_detections.detections)
        
        # Filter by confidence
        high_conf = collection.filter_by_confidence(0.9)
        assert all(d.confidence >= 0.9 for d in high_conf.detections)
        
        # Filter by page
        page_1 = collection.filter_by_page(1)
        assert all(d.page_number == 1 for d in page_1.detections)
    
    def test_collection_statistics(self, test_pii_detections):
        """Test collection statistics methods."""
        collection = PIIDetectionCollection(detections=test_pii_detections)
        
        stats = collection.get_statistics()
        assert 'total_detections' in stats
        assert 'detection_types' in stats
        assert 'confidence_distribution' in stats
        assert 'page_distribution' in stats
        
        assert stats['total_detections'] == len(test_pii_detections)
    
    def test_collection_export(self, test_pii_detections, temp_dir):
        """Test collection export functionality."""
        collection = PIIDetectionCollection(detections=test_pii_detections)
        
        # Export to JSON
        json_path = temp_dir / "detections.json"
        collection.export_to_json(json_path)
        assert json_path.exists()
        
        # Verify JSON content
        with open(json_path) as f:
            data = json.load(f)
        assert 'detections' in data
        assert len(data['detections']) == len(test_pii_detections)
        
        # Export to CSV
        csv_path = temp_dir / "detections.csv"
        collection.export_to_csv(csv_path)
        assert csv_path.exists()


@unit_test
class TestProcessingUtilities:
    """Test processing utility functions."""
    
    def test_validate_processing_result(self, test_processing_result):
        """Test processing result validation."""
        # Valid result
        is_valid, errors = validate_processing_result(test_processing_result)
        assert is_valid is True
        assert len(errors) == 0
        
        # Invalid result - missing required fields
        invalid_result = ProcessingResult(
            document_id="",  # Empty ID
            original_filename="test.pdf",
            status=ProcessingStatus.COMPLETED,
            detections=[],
            processing_time=1.0
        )
        is_valid, errors = validate_processing_result(invalid_result)
        assert is_valid is False
        assert len(errors) > 0
        
        # Invalid result - negative processing time
        invalid_result.document_id = "valid-id"
        invalid_result.processing_time = -1.0
        is_valid, errors = validate_processing_result(invalid_result)
        assert is_valid is False
        assert len(errors) > 0


@unit_test
class TestProfileManager:
    """Test profile management functionality."""
    
    def test_profile_manager_creation(self):
        """Test ProfileManager creation."""
        manager = ProfileManager()
        assert manager is not None
        assert hasattr(manager, 'profiles')
    
    def test_load_profile(self, temp_dir):
        """Test loading profile from file."""
        manager = ProfileManager()
        
        # Create test profile file
        profile_data = {
            'name': 'test_profile',
            'description': 'Test profile',
            'pii_types': ['name', 'email'],
            'redaction_style': 'solid_black',
            'confidence_threshold': 0.8
        }
        
        # Test YAML format
        yaml_path = temp_dir / "test_profile.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(profile_data, f)
        
        profile = manager.load_profile(yaml_path)
        assert profile.name == 'test_profile'
        assert len(profile.pii_types) == 2
    
    def test_validate_profile(self, test_redaction_profile):
        """Test profile validation."""
        manager = ProfileManager()
        
        # Valid profile
        is_valid, errors = manager.validate_profile(test_redaction_profile)
        assert is_valid is True
        assert len(errors) == 0
        
        # Invalid profile
        invalid_profile = RedactionProfile(
            name="",  # Empty name
            description="Test",
            pii_types=[],  # No PII types
            redaction_style="solid_black",
            confidence_threshold=1.5  # Invalid threshold
        )
        is_valid, errors = manager.validate_profile(invalid_profile)
        assert is_valid is False
        assert len(errors) > 0


@unit_test
class TestAuditLog:
    """Test audit log functionality."""
    
    def test_audit_log_creation(self):
        """Test creating audit logs."""
        log = AuditLog(
            operation=AuditOperation.DOCUMENT_REDACTION,
            level=AuditLevel.INFO,
            message="Test operation completed",
            details={"duration": 1.5}
        )
        
        assert log.operation == AuditOperation.DOCUMENT_REDACTION
        assert log.level == AuditLevel.INFO
        assert log.message == "Test operation completed"
        assert log.details["duration"] == 1.5
        assert log.timestamp is not None
        assert log.audit_id is not None
    
    def test_audit_log_serialization(self):
        """Test audit log serialization."""
        log = AuditLog(
            operation=AuditOperation.PII_DETECTION,
            level=AuditLevel.INFO,
            message="PII detected",
            details={"count": 5}
        )
        
        # Test to_dict
        log_dict = log.to_dict()
        assert 'operation' in log_dict
        assert 'level' in log_dict
        assert 'message' in log_dict
        assert 'details' in log_dict
        assert 'timestamp' in log_dict
        assert 'audit_id' in log_dict
        
        # Test to_json
        json_str = log.to_json()
        assert isinstance(json_str, str)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed['operation'] == 'pii_detection'
        assert parsed['level'] == 'info'


@unit_test
class TestAuditTrail:
    """Test audit trail functionality."""
    
    def test_audit_trail_creation(self):
        """Test creating audit trails."""
        logs = [
            AuditLog(
                operation=AuditOperation.DOCUMENT_UPLOAD,
                level=AuditLevel.INFO,
                message="Document uploaded"
            ),
            AuditLog(
                operation=AuditOperation.PII_DETECTION,
                level=AuditLevel.INFO,
                message="PII detected"
            ),
            AuditLog(
                operation=AuditOperation.DOCUMENT_REDACTION,
                level=AuditLevel.INFO,
                message="Document redacted"
            )
        ]
        
        trail = AuditTrail(logs=logs, document_id="test-doc-123")
        
        assert len(trail.logs) == 3
        assert trail.document_id == "test-doc-123"
        assert trail.created_at is not None
    
    def test_audit_trail_export(self, temp_dir):
        """Test audit trail export functionality."""
        logs = [
            AuditLog(
                operation=AuditOperation.DOCUMENT_UPLOAD,
                level=AuditLevel.INFO,
                message="Document uploaded"
            )
        ]
        
        trail = AuditTrail(logs=logs, document_id="test-doc-123")
        
        # Export to JSON
        json_path = temp_dir / "audit_trail.json"
        trail.export_to_json(json_path)
        assert json_path.exists()
        
        # Export to CSV
        csv_path = temp_dir / "audit_trail.csv"
        trail.export_to_csv(csv_path)
        assert csv_path.exists()


@unit_test
class TestCryptographicUtils:
    """Test cryptographic utilities."""
    
    def test_crypto_utils_creation(self):
        """Test CryptographicUtils creation."""
        crypto = CryptographicUtils()
        assert crypto is not None
        assert hasattr(crypto, 'logger')
    
    def test_sha256_hash_generation(self, temp_dir):
        """Test SHA-256 hash generation."""
        crypto = CryptographicUtils()
        
        # Create test file
        test_file = temp_dir / "test_hash.txt"
        test_file.write_text("content for hashing")
        
        # Generate hash
        hash_value = crypto.generate_sha256_hash(test_file)
        assert hash_value is not None
        assert len(hash_value) == 64  # SHA-256 produces 64-character hex string
        
        # Same content should produce same hash
        hash_value2 = crypto.generate_sha256_hash(test_file)
        assert hash_value == hash_value2
        
        # Different content should produce different hash
        test_file.write_text("different content")
        hash_value3 = crypto.generate_sha256_hash(test_file)
        assert hash_value != hash_value3
    
    def test_rsa_key_generation(self):
        """Test RSA key generation."""
        crypto = CryptographicUtils()
        
        # Generate RSA key pair
        private_key, public_key = crypto.generate_rsa_key_pair()
        assert private_key is not None
        assert public_key is not None
        
        # Keys should be different objects
        assert private_key != public_key
    
    def test_signature_generation_and_verification(self, temp_dir):
        """Test digital signature generation and verification."""
        crypto = CryptographicUtils()
        
        # Create test file
        test_file = temp_dir / "test_sign.txt"
        test_file.write_text("data to sign")
        
        # Generate key pair
        private_key, public_key = crypto.generate_rsa_key_pair()
        
        # Generate signature
        signature = crypto.sign_file(test_file, private_key)
        assert signature is not None
        
        # Verify signature
        is_valid = crypto.verify_file_signature(test_file, signature, public_key)
        assert is_valid is True
        
        # Verify with wrong data should fail
        test_file.write_text("modified data")
        is_valid = crypto.verify_file_signature(test_file, signature, public_key)
        assert is_valid is False


@unit_test
class TestFileUtils:
    """Test file utility functions."""
    
    def test_file_utils_creation(self):
        """Test FileUtils creation."""
        file_utils = FileUtils()
        assert file_utils is not None
    
    def test_safe_file_operations(self, temp_dir):
        """Test safe file operations."""
        file_utils = FileUtils()
        
        # Create source file
        source = temp_dir / "source.txt"
        source.write_text("test content")
        
        # Copy file safely
        dest = temp_dir / "destination.txt"
        file_utils.safe_copy(source, dest)
        
        assert dest.exists()
        assert dest.read_text() == "test content"
        
        # Test file validation
        assert file_utils.validate_file_path(source) is True
        assert file_utils.validate_file_path(temp_dir / "nonexistent.txt") is False
    
    def test_secure_file_deletion(self, temp_dir):
        """Test secure file deletion."""
        file_utils = FileUtils()
        
        # Create test file
        test_file = temp_dir / "to_delete.txt"
        test_file.write_text("sensitive content")
        assert test_file.exists()
        
        # Delete file securely
        file_utils.secure_delete(test_file)
        assert not test_file.exists()


@unit_test
class TestTempFileManager:
    """Test temporary file manager."""
    
    def test_temp_file_manager_creation(self):
        """Test TempFileManager creation."""
        temp_manager = TempFileManager()
        assert temp_manager is not None
    
    def test_temp_file_creation_and_cleanup(self):
        """Test temporary file creation and cleanup."""
        temp_manager = TempFileManager()
        
        # Create temporary file
        with temp_manager.create_temp_file(suffix=".txt") as temp_file:
            assert temp_file.exists()
            assert temp_file.suffix == ".txt"
            
            # Write to temp file
            temp_file.write_text("temporary content")
            assert temp_file.read_text() == "temporary content"
        
        # File should be cleaned up after context
        assert not temp_file.exists()
    
    def test_temp_directory_creation(self):
        """Test temporary directory creation."""
        temp_manager = TempFileManager()
        
        with temp_manager.create_temp_dir() as temp_dir:
            assert temp_dir.exists()
            assert temp_dir.is_dir()
            
            # Create files in temp directory
            test_file = temp_dir / "test.txt"
            test_file.write_text("content")
            assert test_file.exists()
        
        # Directory should be cleaned up after context
        assert not temp_dir.exists()


@unit_test
class TestConfigurationClasses:
    """Test configuration classes."""
    
    def test_web_settings_creation(self):
        """Test WebSettings creation and validation."""
        settings = WebSettings()
        
        # Should have default values
        assert settings.host == "localhost"
        assert settings.port == 8000
        assert settings.max_file_size_mb > 0
        assert len(settings.allowed_file_types) > 0
    
    def test_cli_settings_creation(self):
        """Test CLISettings creation and validation."""
        settings = CLISettings()
        
        # Should have default values
        assert settings.default_profile is not None
        assert settings.log_level is not None
        assert settings.temp_dir is not None
    
    def test_api_settings_creation(self):
        """Test APISettings creation and validation."""
        settings = APISettings()
        
        # Should have default values
        assert settings.host == "localhost"
        assert settings.port == 8000
        assert settings.max_file_size_mb > 0
    
    def test_gopnik_config_creation(self):
        """Test GopnikConfig creation and loading."""
        config = GopnikConfig()
        
        # Should have default configuration
        assert config is not None
        assert hasattr(config, 'web_settings')
        assert hasattr(config, 'cli_settings')
        assert hasattr(config, 'api_settings')
    
    def test_config_file_loading(self, temp_dir):
        """Test loading configuration from file."""
        # Create test config file
        config_data = {
            'log_level': 'DEBUG',
            'temp_dir': str(temp_dir),
            'max_file_size': 50 * 1024 * 1024,
            'ai_config': {
                'cv_model': 'yolov8',
                'nlp_model': 'layoutlmv3'
            }
        }
        
        config_file = temp_dir / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Load configuration
        config = GopnikConfig(config_file=config_file)
        assert config.cli_settings.log_level == 'DEBUG'
        assert str(config.cli_settings.temp_dir) == str(temp_dir)


@performance_test
class TestPerformanceBenchmarks:
    """Performance benchmarks for critical operations."""
    
    def test_pii_detection_performance(self, test_data_generator):
        """Test PII detection performance with large datasets."""
        from tests.test_utils import PerformanceTimer
        
        # Generate large number of detections
        detections = []
        for i in range(1000):
            bbox = BoundingBox(i, i, i+100, i+100)
            detection = PIIDetection(
                type=PIIType.NAME,
                bounding_box=bbox,
                confidence=0.8 + (i % 20) / 100
            )
            detections.append(detection)
        
        with PerformanceTimer(max_duration=2.0) as timer:
            # Test collection creation performance
            collection = PIIDetectionCollection(detections=detections)
            
            # Test filtering performance
            high_conf = collection.filter_by_confidence(0.85)
            
            # Test statistics calculation
            stats = collection.get_statistics()
        
        assert timer.duration < 2.0
        assert len(high_conf.detections) > 0
        assert stats['total_detections'] == 1000
    
    def test_file_operations_performance(self, temp_dir):
        """Test file operation performance."""
        from tests.test_utils import PerformanceTimer
        
        file_utils = FileUtils()
        crypto = CryptographicUtils()
        
        # Create test files
        test_files = []
        for i in range(50):  # Reduced number for faster testing
            test_file = temp_dir / f"test_{i}.txt"
            test_file.write_text(f"Test content {i}" * 100)  # ~1.5KB each
            test_files.append(test_file)
        
        with PerformanceTimer(max_duration=3.0) as timer:
            # Test hash calculation performance
            hashes = []
            for test_file in test_files:
                hash_value = crypto.generate_sha256_hash(test_file)
                hashes.append(hash_value)
            
            # Test file copying performance
            for i, test_file in enumerate(test_files[:10]):  # Copy subset
                dest = temp_dir / f"copy_{i}.txt"
                file_utils.safe_copy(test_file, dest)
        
        assert timer.duration < 3.0
        assert len(hashes) == 50
        assert all(h is not None for h in hashes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])