"""
Comprehensive unit tests to achieve high test coverage.
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

# Import all modules to test
from src.gopnik.models.pii import (
    PIIType, BoundingBox, PIIDetection, PIIDetectionCollection,
    validate_detection_confidence, validate_coordinates,
    merge_overlapping_detections, filter_detections_by_confidence,
    group_detections_by_type, calculate_detection_coverage
)
from src.gopnik.models.processing import (
    ProcessingResult, ProcessingStatus, ProcessingMetrics,
    validate_processing_result, create_processing_summary_report
)
from src.gopnik.models.profiles import (
    RedactionProfile, ProfileValidationError, ProfileManager
)
from src.gopnik.models.audit import (
    AuditLog, AuditOperation, AuditLevel, AuditTrail
)
from src.gopnik.utils.crypto import CryptographicUtils
from src.gopnik.utils.file_utils import FileUtils, TempFileManager
from src.gopnik.config.settings import GopnikSettings
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
    
    def test_validate_coordinates(self):
        """Test coordinate validation."""
        # Valid coordinates
        assert validate_coordinates(0, 0, 100, 100) is True
        assert validate_coordinates(10, 20, 110, 120) is True
        
        # Invalid coordinates
        assert validate_coordinates(-1, 0, 100, 100) is False  # Negative
        assert validate_coordinates(100, 0, 100, 100) is False  # x1 >= x2
        assert validate_coordinates(0, 100, 100, 100) is False  # y1 >= y2
        assert validate_coordinates(0, 0, -1, 100) is False  # Negative x2
    
    def test_merge_overlapping_detections(self, test_pii_detections):
        """Test merging overlapping detections."""
        # Create overlapping detections
        bbox1 = BoundingBox(0, 0, 100, 100)
        bbox2 = BoundingBox(10, 10, 110, 110)  # High overlap
        bbox3 = BoundingBox(200, 200, 300, 300)  # No overlap
        
        detections = [
            PIIDetection(type=PIIType.NAME, bounding_box=bbox1, confidence=0.9),
            PIIDetection(type=PIIType.NAME, bounding_box=bbox2, confidence=0.8),
            PIIDetection(type=PIIType.EMAIL, bounding_box=bbox3, confidence=0.95)
        ]
        
        merged = merge_overlapping_detections(detections, iou_threshold=0.5)
        
        # Should merge the two overlapping NAME detections
        assert len(merged) == 2
        name_detections = [d for d in merged if d.type == PIIType.NAME]
        assert len(name_detections) == 1
        assert name_detections[0].confidence == 0.9  # Higher confidence preserved
    
    def test_filter_detections_by_confidence(self, test_pii_detections):
        """Test filtering detections by confidence threshold."""
        detections = [
            PIIDetection(type=PIIType.NAME, bounding_box=BoundingBox(0, 0, 100, 100), confidence=0.9),
            PIIDetection(type=PIIType.EMAIL, bounding_box=BoundingBox(0, 0, 100, 100), confidence=0.7),
            PIIDetection(type=PIIType.PHONE_NUMBER, bounding_box=BoundingBox(0, 0, 100, 100), confidence=0.6)
        ]
        
        # Filter with threshold 0.8
        filtered = filter_detections_by_confidence(detections, threshold=0.8)
        assert len(filtered) == 1
        assert filtered[0].type == PIIType.NAME
        
        # Filter with threshold 0.5
        filtered = filter_detections_by_confidence(detections, threshold=0.5)
        assert len(filtered) == 3
    
    def test_group_detections_by_type(self, test_pii_detections):
        """Test grouping detections by PII type."""
        detections = [
            PIIDetection(type=PIIType.NAME, bounding_box=BoundingBox(0, 0, 100, 100), confidence=0.9),
            PIIDetection(type=PIIType.NAME, bounding_box=BoundingBox(0, 0, 100, 100), confidence=0.8),
            PIIDetection(type=PIIType.EMAIL, bounding_box=BoundingBox(0, 0, 100, 100), confidence=0.95)
        ]
        
        grouped = group_detections_by_type(detections)
        
        assert len(grouped) == 2
        assert PIIType.NAME in grouped
        assert PIIType.EMAIL in grouped
        assert len(grouped[PIIType.NAME]) == 2
        assert len(grouped[PIIType.EMAIL]) == 1
    
    def test_calculate_detection_coverage(self):
        """Test detection coverage calculation."""
        detections = [
            PIIDetection(type=PIIType.NAME, bounding_box=BoundingBox(0, 0, 100, 100), confidence=0.9),
            PIIDetection(type=PIIType.EMAIL, bounding_box=BoundingBox(100, 100, 200, 200), confidence=0.95)
        ]
        
        # Document size 1000x1000
        coverage = calculate_detection_coverage(detections, document_width=1000, document_height=1000)
        
        # Two 100x100 boxes = 20000 pixels out of 1000000 = 2%
        expected_coverage = 20000 / 1000000
        assert abs(coverage - expected_coverage) < 0.001


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
        assert validate_processing_result(test_processing_result) is True
        
        # Invalid result - missing required fields
        invalid_result = ProcessingResult(
            document_id="",  # Empty ID
            original_filename="test.pdf",
            status=ProcessingStatus.COMPLETED,
            detections=[],
            processing_time=1.0
        )
        assert validate_processing_result(invalid_result) is False
        
        # Invalid result - negative processing time
        invalid_result.document_id = "valid-id"
        invalid_result.processing_time = -1.0
        assert validate_processing_result(invalid_result) is False
    
    def test_create_processing_summary(self, test_processing_result):
        """Test processing summary creation."""
        summary = create_processing_summary(test_processing_result)
        
        assert 'document_id' in summary
        assert 'status' in summary
        assert 'detection_count' in summary
        assert 'processing_time' in summary
        assert 'pii_types_found' in summary
        
        assert summary['document_id'] == test_processing_result.document_id
        assert summary['detection_count'] == len(test_processing_result.detections)


@unit_test
class TestProfileUtilities:
    """Test profile utility functions."""
    
    def test_load_profile_from_file(self, temp_dir):
        """Test loading profile from file."""
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
        
        profile = load_profile_from_file(yaml_path)
        assert profile.name == 'test_profile'
        assert len(profile.pii_types) == 2
        
        # Test JSON format
        json_path = temp_dir / "test_profile.json"
        with open(json_path, 'w') as f:
            json.dump(profile_data, f)
        
        profile = load_profile_from_file(json_path)
        assert profile.name == 'test_profile'
        
        # Test invalid file
        with pytest.raises(FileNotFoundError):
            load_profile_from_file(temp_dir / "nonexistent.yaml")
    
    def test_validate_profile_config(self):
        """Test profile configuration validation."""
        # Valid config
        valid_config = {
            'name': 'test_profile',
            'description': 'Test profile',
            'pii_types': ['name', 'email'],
            'redaction_style': 'solid_black',
            'confidence_threshold': 0.8
        }
        assert validate_profile_config(valid_config) is True
        
        # Invalid config - missing required fields
        invalid_config = {
            'name': 'test_profile'
            # Missing other required fields
        }
        assert validate_profile_config(invalid_config) is False
        
        # Invalid config - invalid PII types
        invalid_config = {
            'name': 'test_profile',
            'description': 'Test profile',
            'pii_types': ['invalid_type'],
            'redaction_style': 'solid_black',
            'confidence_threshold': 0.8
        }
        assert validate_profile_config(invalid_config) is False


@unit_test
class TestAuditUtilities:
    """Test audit utility functions."""
    
    def test_create_audit_event(self):
        """Test audit event creation."""
        event = create_audit_event(
            event_type="test_event",
            details={"key": "value"}
        )
        
        assert event.event_type == "test_event"
        assert event.details["key"] == "value"
        assert event.timestamp is not None
        assert event.event_id is not None
    
    def test_validate_audit_log(self, test_audit_log):
        """Test audit log validation."""
        # Valid audit log
        assert validate_audit_log(test_audit_log) is True
        
        # Invalid audit log - no events
        invalid_log = AuditLog(document_id="test", events=[])
        assert validate_audit_log(invalid_log) is False
        
        # Invalid audit log - missing document ID
        invalid_log = AuditLog(document_id="", events=test_audit_log.events)
        assert validate_audit_log(invalid_log) is False


@unit_test
class TestCryptoUtilities:
    """Test cryptographic utility functions."""
    
    def test_generate_and_verify_hash(self):
        """Test hash generation and verification."""
        data = b"test data for hashing"
        
        # Generate hash
        hash_value = generate_hash(data)
        assert hash_value is not None
        assert len(hash_value) > 0
        
        # Verify hash
        assert verify_hash(data, hash_value) is True
        assert verify_hash(b"different data", hash_value) is False
    
    def test_generate_random_key(self):
        """Test random key generation."""
        key1 = generate_random_key(32)
        key2 = generate_random_key(32)
        
        assert len(key1) == 32
        assert len(key2) == 32
        assert key1 != key2  # Should be different
    
    @patch('src.gopnik.utils.crypto.RSA')
    def test_generate_and_verify_signature(self, mock_rsa):
        """Test signature generation and verification."""
        # Mock RSA key generation
        mock_key = Mock()
        mock_rsa.generate.return_value = mock_key
        
        data = b"test data for signing"
        
        # Test signature generation
        signature = generate_signature(data, mock_key)
        assert signature is not None
        
        # Test signature verification
        with patch('src.gopnik.utils.crypto.pkcs1_15') as mock_pkcs:
            mock_pkcs.new.return_value.verify.return_value = None
            assert verify_signature(data, signature, mock_key) is True
            
            # Test invalid signature
            mock_pkcs.new.return_value.verify.side_effect = ValueError("Invalid signature")
            assert verify_signature(data, b"invalid", mock_key) is False
    
    @patch('src.gopnik.utils.crypto.AES')
    def test_encrypt_decrypt_data(self, mock_aes):
        """Test data encryption and decryption."""
        data = b"sensitive data to encrypt"
        key = b"32-byte-key-for-aes-encryption!!"
        
        # Mock AES encryption
        mock_cipher = Mock()
        mock_aes.new.return_value = mock_cipher
        mock_cipher.encrypt.return_value = b"encrypted_data"
        mock_cipher.decrypt.return_value = data
        
        # Test encryption
        encrypted = encrypt_data(data, key)
        assert encrypted is not None
        
        # Test decryption
        decrypted = decrypt_data(encrypted, key)
        assert decrypted == data


@unit_test
class TestFileUtilities:
    """Test file utility functions."""
    
    def test_ensure_directory_exists(self, temp_dir):
        """Test directory creation."""
        test_dir = temp_dir / "new_directory"
        assert not test_dir.exists()
        
        ensure_directory_exists(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()
        
        # Should not raise error if directory already exists
        ensure_directory_exists(test_dir)
        assert test_dir.exists()
    
    def test_safe_file_copy(self, temp_dir):
        """Test safe file copying."""
        # Create source file
        source = temp_dir / "source.txt"
        source.write_text("test content")
        
        # Copy file
        dest = temp_dir / "destination.txt"
        safe_file_copy(source, dest)
        
        assert dest.exists()
        assert dest.read_text() == "test content"
        
        # Test overwrite protection
        dest.write_text("different content")
        with pytest.raises(FileExistsError):
            safe_file_copy(source, dest, overwrite=False)
    
    def test_secure_file_delete(self, temp_dir):
        """Test secure file deletion."""
        # Create test file
        test_file = temp_dir / "to_delete.txt"
        test_file.write_text("sensitive content")
        assert test_file.exists()
        
        # Delete file securely
        secure_file_delete(test_file)
        assert not test_file.exists()
        
        # Should not raise error for non-existent file
        secure_file_delete(test_file)
    
    def test_get_file_hash(self, temp_dir):
        """Test file hash calculation."""
        # Create test file
        test_file = temp_dir / "test_hash.txt"
        test_file.write_text("content for hashing")
        
        # Calculate hash
        hash_value = get_file_hash(test_file)
        assert hash_value is not None
        assert len(hash_value) > 0
        
        # Same content should produce same hash
        hash_value2 = get_file_hash(test_file)
        assert hash_value == hash_value2
        
        # Different content should produce different hash
        test_file.write_text("different content")
        hash_value3 = get_file_hash(test_file)
        assert hash_value != hash_value3
    
    def test_validate_file_path(self, temp_dir):
        """Test file path validation."""
        # Valid existing file
        test_file = temp_dir / "valid.txt"
        test_file.write_text("content")
        assert validate_file_path(test_file) is True
        
        # Non-existent file
        assert validate_file_path(temp_dir / "nonexistent.txt") is False
        
        # Directory instead of file
        assert validate_file_path(temp_dir) is False
        
        # Invalid path
        assert validate_file_path(None) is False
    
    def test_create_temp_file(self):
        """Test temporary file creation."""
        with create_temp_file(suffix=".txt") as temp_file:
            assert temp_file.exists()
            assert temp_file.suffix == ".txt"
            
            # Write to temp file
            temp_file.write_text("temporary content")
            assert temp_file.read_text() == "temporary content"
        
        # File should be cleaned up after context
        assert not temp_file.exists()


@unit_test
class TestConfigurationClasses:
    """Test configuration classes."""
    
    def test_gopnik_settings_creation(self):
        """Test GopnikSettings creation and validation."""
        settings = GopnikSettings()
        
        # Should have default values
        assert settings.log_level is not None
        assert settings.temp_dir is not None
        assert settings.max_file_size > 0
        assert settings.supported_formats is not None
    
    def test_gopnik_config_creation(self):
        """Test GopnikConfig creation and loading."""
        config = GopnikConfig()
        
        # Should have default configuration
        assert config.settings is not None
        assert hasattr(config, 'ai_config')
        assert hasattr(config, 'security_config')
    
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
        assert config.settings.log_level == 'DEBUG'
        assert str(config.settings.temp_dir) == str(temp_dir)


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
            # Test filtering performance
            filtered = filter_detections_by_confidence(detections, threshold=0.85)
            
            # Test grouping performance
            grouped = group_detections_by_type(detections)
            
            # Test merging performance (with some overlaps)
            merged = merge_overlapping_detections(detections[:100], iou_threshold=0.5)
        
        assert timer.duration < 2.0
        assert len(filtered) > 0
        assert len(grouped) > 0
        assert len(merged) <= 100
    
    def test_file_operations_performance(self, temp_dir):
        """Test file operation performance."""
        from tests.test_utils import PerformanceTimer
        
        # Create test files
        test_files = []
        for i in range(100):
            test_file = temp_dir / f"test_{i}.txt"
            test_file.write_text(f"Test content {i}" * 100)  # ~1.5KB each
            test_files.append(test_file)
        
        with PerformanceTimer(max_duration=3.0) as timer:
            # Test hash calculation performance
            hashes = []
            for test_file in test_files:
                hash_value = get_file_hash(test_file)
                hashes.append(hash_value)
            
            # Test file copying performance
            for i, test_file in enumerate(test_files[:10]):  # Copy subset
                dest = temp_dir / f"copy_{i}.txt"
                safe_file_copy(test_file, dest)
        
        assert timer.duration < 3.0
        assert len(hashes) == 100
        assert all(h is not None for h in hashes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])