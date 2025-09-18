"""
Test utilities and fixtures for comprehensive testing.
"""

import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator
from unittest.mock import Mock, MagicMock, patch
import pytest
import json
import yaml
from PIL import Image
import numpy as np

from src.gopnik.models.pii import PIIDetection, PIIType, BoundingBox
from src.gopnik.models.processing import ProcessingResult, ProcessingStatus
from src.gopnik.models.profiles import RedactionProfile
from src.gopnik.models.audit import AuditLog, AuditOperation, AuditLevel


class TestDataGenerator:
    """Generate synthetic test data for various scenarios."""
    
    @staticmethod
    def create_test_image(width: int = 800, height: int = 600, 
                         format: str = "RGB") -> Image.Image:
        """Create a test image with random content."""
        # Create random image data
        if format == "RGB":
            data = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        else:
            data = np.random.randint(0, 256, (height, width), dtype=np.uint8)
        
        return Image.fromarray(data, format)
    
    @staticmethod
    def create_test_document_with_pii(temp_dir: Path) -> Path:
        """Create a test document containing synthetic PII."""
        doc_path = temp_dir / "test_document.txt"
        
        content = """
        John Doe
        Email: john.doe@example.com
        Phone: (555) 123-4567
        SSN: 123-45-6789
        Address: 123 Main St, Anytown, ST 12345
        Credit Card: 4532-1234-5678-9012
        """
        
        doc_path.write_text(content)
        return doc_path
    
    @staticmethod
    def create_test_pii_detections() -> List[PIIDetection]:
        """Create a list of test PII detections."""
        return [
            PIIDetection(
                pii_type=PIIType.PERSON_NAME,
                text="John Doe",
                confidence=0.95,
                bounding_box=BoundingBox(x=10, y=20, width=100, height=25),
                page_number=1
            ),
            PIIDetection(
                pii_type=PIIType.EMAIL,
                text="john.doe@example.com",
                confidence=0.98,
                bounding_box=BoundingBox(x=10, y=50, width=200, height=25),
                page_number=1
            ),
            PIIDetection(
                pii_type=PIIType.PHONE_NUMBER,
                text="(555) 123-4567",
                confidence=0.92,
                bounding_box=BoundingBox(x=10, y=80, width=150, height=25),
                page_number=1
            )
        ]
    
    @staticmethod
    def create_test_processing_result() -> ProcessingResult:
        """Create a test processing result."""
        return ProcessingResult(
            document_id="test-doc-123",
            original_filename="test.pdf",
            status=ProcessingStatus.COMPLETED,
            detections=TestDataGenerator.create_test_pii_detections(),
            processing_time=1.5,
            redacted_file_path=Path("/tmp/redacted_test.pdf"),
            audit_log_path=Path("/tmp/audit_test.json")
        )
    
    @staticmethod
    def create_test_redaction_profile() -> RedactionProfile:
        """Create a test redaction profile."""
        return RedactionProfile(
            name="test_profile",
            description="Test redaction profile",
            pii_types=[PIIType.PERSON_NAME, PIIType.EMAIL, PIIType.PHONE_NUMBER],
            redaction_style="solid_black",
            confidence_threshold=0.8,
            preserve_layout=True
        )
    
    @staticmethod
    def create_test_audit_log() -> AuditLog:
        """Create a test audit log."""
        return AuditLog(
            operation=AuditOperation.DOCUMENT_REDACTION,
            level=AuditLevel.INFO,
            message="Test document processing completed",
            details={"filename": "test.pdf", "duration": 1.5}
        )


class MockAIEngine:
    """Mock AI engine for testing."""
    
    def __init__(self, detections: Optional[List[PIIDetection]] = None):
        self.detections = detections or TestDataGenerator.create_test_pii_detections()
    
    async def detect_pii(self, document_path: Path) -> List[PIIDetection]:
        """Mock PII detection."""
        return self.detections
    
    def is_available(self) -> bool:
        """Mock availability check."""
        return True


class MockDocumentProcessor:
    """Mock document processor for testing."""
    
    def __init__(self, result: Optional[ProcessingResult] = None):
        self.result = result or TestDataGenerator.create_test_processing_result()
    
    async def process_document(self, document_path: Path, 
                             profile: RedactionProfile) -> ProcessingResult:
        """Mock document processing."""
        return self.result


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_data_generator() -> TestDataGenerator:
    """Provide test data generator."""
    return TestDataGenerator()


@pytest.fixture
def mock_ai_engine() -> MockAIEngine:
    """Provide mock AI engine."""
    return MockAIEngine()


@pytest.fixture
def mock_document_processor() -> MockDocumentProcessor:
    """Provide mock document processor."""
    return MockDocumentProcessor()


@pytest.fixture
def test_pii_detections() -> List[PIIDetection]:
    """Provide test PII detections."""
    return TestDataGenerator.create_test_pii_detections()


@pytest.fixture
def test_processing_result() -> ProcessingResult:
    """Provide test processing result."""
    return TestDataGenerator.create_test_processing_result()


@pytest.fixture
def test_redaction_profile() -> RedactionProfile:
    """Provide test redaction profile."""
    return TestDataGenerator.create_test_redaction_profile()


@pytest.fixture
def test_audit_log() -> AuditLog:
    """Provide test audit log."""
    return TestDataGenerator.create_test_audit_log()


class TestAssertions:
    """Custom assertions for testing."""
    
    @staticmethod
    def assert_pii_detection_valid(detection: PIIDetection) -> None:
        """Assert that a PII detection is valid."""
        assert detection.pii_type is not None
        assert detection.confidence >= 0.0 and detection.confidence <= 1.0
        assert detection.bounding_box is not None
        assert detection.bounding_box.width > 0
        assert detection.bounding_box.height > 0
        assert detection.page_number >= 1
    
    @staticmethod
    def assert_processing_result_valid(result: ProcessingResult) -> None:
        """Assert that a processing result is valid."""
        assert result.document_id is not None
        assert result.original_filename is not None
        assert result.status is not None
        assert result.processing_time >= 0
        
        if result.detections:
            for detection in result.detections:
                TestAssertions.assert_pii_detection_valid(detection)
    
    @staticmethod
    def assert_audit_log_valid(audit_log: AuditLog) -> None:
        """Assert that an audit log is valid."""
        assert audit_log.document_id is not None
        assert audit_log.events is not None
        assert len(audit_log.events) > 0
        
        for event in audit_log.events:
            assert event.event_type is not None
            assert event.timestamp is not None


def create_mock_response(status_code: int = 200, json_data: Optional[Dict] = None,
                        text: Optional[str] = None) -> Mock:
    """Create a mock HTTP response."""
    mock_response = Mock()
    mock_response.status_code = status_code
    
    if json_data:
        mock_response.json.return_value = json_data
    
    if text:
        mock_response.text = text
        mock_response.content = text.encode()
    
    return mock_response


def patch_ai_models():
    """Decorator to patch AI model dependencies."""
    def decorator(func):
        @patch('src.gopnik.ai.cv_engine.YOLO')
        @patch('src.gopnik.ai.nlp_engine.pipeline')
        @patch('src.gopnik.ai.hybrid_engine.HybridAIEngine')
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def patch_file_operations():
    """Decorator to patch file system operations."""
    def decorator(func):
        @patch('pathlib.Path.exists')
        @patch('pathlib.Path.mkdir')
        @patch('pathlib.Path.unlink')
        @patch('shutil.copy2')
        @patch('shutil.move')
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


class PerformanceTimer:
    """Context manager for measuring test performance."""
    
    def __init__(self, max_duration: float = 5.0):
        self.max_duration = max_duration
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        if duration > self.max_duration:
            pytest.fail(f"Test took too long: {duration:.2f}s > {self.max_duration}s")
    
    @property
    def duration(self) -> float:
        """Get the measured duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0


def skip_if_no_ai_models():
    """Skip test if AI models are not available."""
    try:
        import torch
        import transformers
        return False
    except ImportError:
        return True


# Performance test markers
performance_test = pytest.mark.performance
slow_test = pytest.mark.slow
security_test = pytest.mark.security
integration_test = pytest.mark.integration
unit_test = pytest.mark.unit