"""
Unit tests for document processor functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import time

from src.gopnik.core.processor import DocumentProcessor
from src.gopnik.core.interfaces import AIEngineInterface, AuditSystemInterface
from src.gopnik.models.pii import PIIDetection, PIIType, BoundingBox, PIIDetectionCollection
from src.gopnik.models.profiles import RedactionProfile, RedactionStyle
from src.gopnik.models.processing import ProcessingResult, ProcessingStatus, Document, DocumentFormat
from src.gopnik.models.errors import DocumentProcessingError
from src.gopnik.config import GopnikConfig


class MockAIEngine(AIEngineInterface):
    """Mock AI engine for testing."""
    
    def __init__(self, detections=None):
        self.detections = detections or []
    
    def detect_pii(self, document_data):
        return self.detections
    
    def get_supported_types(self):
        return [PIIType.NAME.value, PIIType.EMAIL.value]
    
    def configure(self, config):
        pass


class TestDocumentProcessor:
    """Test cases for DocumentProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DocumentProcessor()
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test profile
        self.test_profile = RedactionProfile(
            name="test_profile",
            description="Test profile",
            text_rules={PIIType.NAME.value: True},
            redaction_style=RedactionStyle.SOLID_BLACK,
            confidence_threshold=0.8
        )
        
        # Create test detection
        self.test_detection = PIIDetection(
            type=PIIType.NAME,
            bounding_box=BoundingBox(100, 100, 200, 150),
            confidence=0.9,
            text_content="John Doe",
            page_number=0
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temp files
        for file in self.temp_dir.glob('*'):
            if file.is_file():
                file.unlink()
        for dir in self.temp_dir.glob('*'):
            if dir.is_dir():
                for subfile in dir.rglob('*'):
                    if subfile.is_file():
                        subfile.unlink()
                dir.rmdir()
        self.temp_dir.rmdir()
    
    def test_init(self):
        """Test processor initialization."""
        assert self.processor.document_analyzer is not None
        assert self.processor.redaction_engine is not None
        assert self.processor.audit_logger is not None
        assert self.processor.integrity_validator is not None
        assert self.processor._ai_engine is None
        assert self.processor._audit_system is None
    
    def test_set_ai_engine(self):
        """Test setting AI engine."""
        mock_engine = MockAIEngine()
        self.processor.set_ai_engine(mock_engine)
        
        assert self.processor._ai_engine == mock_engine
    
    def test_set_audit_system(self):
        """Test setting audit system."""
        mock_audit = Mock(spec=AuditSystemInterface)
        self.processor.set_audit_system(mock_audit)
        
        assert self.processor._audit_system == mock_audit
    
    def test_get_supported_formats(self):
        """Test getting supported formats."""
        formats = self.processor.get_supported_formats()
        
        assert isinstance(formats, list)
        assert '.pdf' in formats
        assert '.png' in formats
    
    def test_get_processing_statistics_empty(self):
        """Test getting statistics when no processing has occurred."""
        stats = self.processor.get_processing_statistics()
        
        assert stats['total_processed'] == 0
        assert stats['successful_processed'] == 0
        assert stats['failed_processed'] == 0
        assert stats['success_rate'] == 0.0
        assert stats['average_processing_time'] == 0.0
    
    def test_reset_statistics(self):
        """Test resetting statistics."""
        # Manually set some stats
        self.processor._processing_stats['total_processed'] = 5
        
        self.processor.reset_statistics()
        
        stats = self.processor.get_processing_statistics()
        assert stats['total_processed'] == 0
    
    def test_health_check_no_ai_engine(self):
        """Test health check without AI engine."""
        health = self.processor.health_check()
        
        assert health['status'] == 'degraded'
        assert health['components']['ai_engine'] == 'not_configured'
        assert 'warnings' in health
    
    def test_health_check_with_ai_engine(self):
        """Test health check with AI engine."""
        mock_engine = MockAIEngine()
        self.processor.set_ai_engine(mock_engine)
        
        health = self.processor.health_check()
        
        assert health['status'] == 'healthy'
        assert health['components']['ai_engine'] == 'available'
    
    @patch('src.gopnik.core.processor.DocumentAnalyzer')
    @patch('src.gopnik.core.processor.RedactionEngine')
    def test_process_document_nonexistent_file(self, mock_redaction, mock_analyzer):
        """Test processing non-existent file."""
        nonexistent_file = self.temp_dir / 'nonexistent.pdf'
        
        result = self.processor.process_document(nonexistent_file, self.test_profile)
        
        assert result.status == ProcessingStatus.FAILED
        assert "not found" in result.errors[0]
    
    @patch('src.gopnik.core.processor.DocumentAnalyzer')
    def test_process_document_unsupported_format(self, mock_analyzer):
        """Test processing unsupported file format."""
        # Create test file
        test_file = self.temp_dir / 'test.txt'
        test_file.write_text('test content')
        
        # Mock analyzer to return False for supported format
        mock_analyzer_instance = Mock()
        mock_analyzer_instance.is_supported_format.return_value = False
        mock_analyzer.return_value = mock_analyzer_instance
        
        result = self.processor.process_document(test_file, self.test_profile)
        
        assert result.status == ProcessingStatus.FAILED
        assert "Unsupported document format" in result.errors[0]
    
    @patch('src.gopnik.core.processor.DocumentAnalyzer')
    @patch('src.gopnik.core.processor.RedactionEngine')
    def test_process_document_success_no_ai_engine(self, mock_redaction_class, mock_analyzer_class):
        """Test successful processing without AI engine."""
        # Create test file
        test_file = self.temp_dir / 'test.pdf'
        test_file.write_bytes(b'fake pdf content')
        
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.is_supported_format.return_value = True
        mock_document = Mock()
        mock_document.id = 'test_doc_id'
        mock_document.format = DocumentFormat.PDF
        mock_document.page_count = 1
        mock_analyzer.analyze_document.return_value = mock_document
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock redaction engine
        mock_redaction = Mock()
        mock_redaction._create_copy.return_value = test_file
        mock_redaction_class.return_value = mock_redaction
        
        # Set up processor
        self.processor.document_analyzer = mock_analyzer
        self.processor.redaction_engine = mock_redaction
        
        result = self.processor.process_document(test_file, self.test_profile)
        
        assert result.status == ProcessingStatus.COMPLETED
        assert result.success == True
        assert result.document_id == 'test_doc_id'
        assert result.detection_count == 0  # No AI engine, no detections
    
    @patch('src.gopnik.core.processor.DocumentAnalyzer')
    @patch('src.gopnik.core.processor.RedactionEngine')
    def test_process_document_success_with_ai_engine(self, mock_redaction_class, mock_analyzer_class):
        """Test successful processing with AI engine."""
        # Create test file
        test_file = self.temp_dir / 'test.pdf'
        test_file.write_bytes(b'fake pdf content')
        
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.is_supported_format.return_value = True
        mock_document = Mock()
        mock_document.id = 'test_doc_id'
        mock_document.format = DocumentFormat.PDF
        mock_document.page_count = 1
        mock_analyzer.analyze_document.return_value = mock_document
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock redaction engine
        mock_redaction = Mock()
        output_path = self.temp_dir / 'redacted_test.pdf'
        output_path.write_bytes(b'redacted content')
        mock_redaction.apply_redactions.return_value = output_path
        mock_redaction_class.return_value = mock_redaction
        
        # Set up AI engine
        mock_ai_engine = MockAIEngine([self.test_detection])
        self.processor.set_ai_engine(mock_ai_engine)
        
        # Set up processor
        self.processor.document_analyzer = mock_analyzer
        self.processor.redaction_engine = mock_redaction
        
        result = self.processor.process_document(test_file, self.test_profile)
        
        assert result.status == ProcessingStatus.COMPLETED
        assert result.success == True
        assert result.detection_count == 1
        assert result.output_path == output_path
    
    def test_validate_document_success(self):
        """Test successful document validation."""
        # Create test files
        doc_path = self.temp_dir / 'test.pdf'
        audit_path = self.temp_dir / 'audit.json'
        doc_path.write_bytes(b'test content')
        audit_path.write_text('{}')
        
        # Mock integrity validator
        with patch.object(self.processor.integrity_validator, 'validate_document_integrity', return_value=True):
            result = self.processor.validate_document(doc_path, audit_path)
            
            assert result == True
    
    def test_validate_document_failure(self):
        """Test document validation failure."""
        # Create test files
        doc_path = self.temp_dir / 'test.pdf'
        audit_path = self.temp_dir / 'audit.json'
        doc_path.write_bytes(b'test content')
        audit_path.write_text('{}')
        
        # Mock integrity validator
        with patch.object(self.processor.integrity_validator, 'validate_document_integrity', return_value=False):
            result = self.processor.validate_document(doc_path, audit_path)
            
            assert result == False
    
    def test_validate_document_error(self):
        """Test document validation with error."""
        # Create test files
        doc_path = self.temp_dir / 'test.pdf'
        audit_path = self.temp_dir / 'audit.json'
        doc_path.write_bytes(b'test content')
        audit_path.write_text('{}')
        
        # Mock integrity validator to raise exception
        with patch.object(self.processor.integrity_validator, 'validate_document_integrity', side_effect=Exception("Validation error")):
            result = self.processor.validate_document(doc_path, audit_path)
            
            assert result == False
    
    def test_batch_process_nonexistent_directory(self):
        """Test batch processing with non-existent directory."""
        nonexistent_dir = self.temp_dir / 'nonexistent'
        
        with pytest.raises(DocumentProcessingError, match="Input directory not found"):
            self.processor.batch_process(nonexistent_dir, self.test_profile)
    
    def test_batch_process_not_directory(self):
        """Test batch processing with file instead of directory."""
        test_file = self.temp_dir / 'test.txt'
        test_file.write_text('test')
        
        with pytest.raises(DocumentProcessingError, match="Input path is not a directory"):
            self.processor.batch_process(test_file, self.test_profile)
    
    @patch('src.gopnik.core.processor.DocumentAnalyzer')
    @patch('src.gopnik.core.processor.RedactionEngine')
    def test_batch_process_empty_directory(self, mock_redaction_class, mock_analyzer_class):
        """Test batch processing with empty directory."""
        empty_dir = self.temp_dir / 'empty'
        empty_dir.mkdir()
        
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.is_supported_format.return_value = False  # No supported files
        mock_analyzer_class.return_value = mock_analyzer
        
        self.processor.document_analyzer = mock_analyzer
        
        result = self.processor.batch_process(empty_dir, self.test_profile)
        
        assert result.total_documents == 0
        assert result.processed_documents == 0
        assert len(result.results) == 0
    
    @patch('src.gopnik.core.processor.DocumentAnalyzer')
    @patch('src.gopnik.core.processor.RedactionEngine')
    def test_batch_process_success(self, mock_redaction_class, mock_analyzer_class):
        """Test successful batch processing."""
        # Create test directory with files
        batch_dir = self.temp_dir / 'batch'
        batch_dir.mkdir()
        
        test_file1 = batch_dir / 'test1.pdf'
        test_file2 = batch_dir / 'test2.png'
        test_file1.write_bytes(b'pdf content')
        test_file2.write_bytes(b'png content')
        
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.is_supported_format.return_value = True
        mock_document = Mock()
        mock_document.id = 'test_doc_id'
        mock_document.format = DocumentFormat.PDF
        mock_document.page_count = 1
        mock_analyzer.analyze_document.return_value = mock_document
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock redaction engine
        mock_redaction = Mock()
        # Create output files for redaction
        output_file1 = self.temp_dir / 'redacted_test1.pdf'
        output_file2 = self.temp_dir / 'redacted_test2.png'
        output_file1.write_bytes(b'redacted pdf')
        output_file2.write_bytes(b'redacted png')
        mock_redaction._create_copy.side_effect = [output_file1, output_file2]
        mock_redaction_class.return_value = mock_redaction
        
        # Set up processor
        self.processor.document_analyzer = mock_analyzer
        self.processor.redaction_engine = mock_redaction
        
        result = self.processor.batch_process(batch_dir, self.test_profile)
        
        assert result.total_documents == 2
        assert result.processed_documents == 2
        assert len(result.results) == 2
        assert result.is_completed == True
    
    def test_detect_pii_no_ai_engine(self):
        """Test PII detection without AI engine."""
        mock_document = Mock()
        mock_document.id = 'test_id'
        mock_document.page_count = 1
        
        result = self.processor._detect_pii(mock_document)
        
        assert isinstance(result, PIIDetectionCollection)
        assert len(result) == 0
        assert result.document_id == 'test_id'
    
    def test_detect_pii_with_ai_engine(self):
        """Test PII detection with AI engine."""
        mock_document = Mock()
        mock_document.id = 'test_id'
        mock_document.page_count = 1
        
        # Set up AI engine
        mock_ai_engine = MockAIEngine([self.test_detection])
        self.processor.set_ai_engine(mock_ai_engine)
        
        result = self.processor._detect_pii(mock_document)
        
        assert isinstance(result, PIIDetectionCollection)
        assert len(result) == 1
        assert result.document_id == 'test_id'
    
    def test_detect_pii_ai_engine_error(self):
        """Test PII detection when AI engine raises error."""
        mock_document = Mock()
        mock_document.id = 'test_id'
        mock_document.page_count = 1
        
        # Set up AI engine that raises error
        mock_ai_engine = Mock()
        mock_ai_engine.detect_pii.side_effect = Exception("AI engine error")
        self.processor.set_ai_engine(mock_ai_engine)
        
        result = self.processor._detect_pii(mock_document)
        
        assert isinstance(result, PIIDetectionCollection)
        assert len(result) == 0  # Should return empty collection on error
    
    def test_update_processing_stats(self):
        """Test updating processing statistics."""
        # Test successful processing
        self.processor._update_processing_stats(success=True, processing_time=1.5)
        
        stats = self.processor.get_processing_statistics()
        assert stats['total_processed'] == 1
        assert stats['successful_processed'] == 1
        assert stats['failed_processed'] == 0
        assert stats['success_rate'] == 100.0
        assert stats['average_processing_time'] == 1.5
        
        # Test failed processing
        self.processor._update_processing_stats(success=False, processing_time=0.5)
        
        stats = self.processor.get_processing_statistics()
        assert stats['total_processed'] == 2
        assert stats['successful_processed'] == 1
        assert stats['failed_processed'] == 1
        assert stats['success_rate'] == 50.0
        assert stats['average_processing_time'] == 1.0


if __name__ == '__main__':
    pytest.main([__file__])