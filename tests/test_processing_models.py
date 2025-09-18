"""
Unit tests for processing result and document data models.
"""

import pytest
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from unittest.mock import patch, MagicMock

from src.gopnik.models.processing import (
    Document, PageInfo, ProcessingResult, ProcessingMetrics,
    BatchProcessingResult, ProcessingStatus, DocumentFormat,
    validate_processing_result, merge_processing_results,
    create_processing_summary_report
)
from src.gopnik.models.pii import PIIDetection, PIIType, BoundingBox, PIIDetectionCollection
from src.gopnik.models.audit import AuditLog, AuditOperation


class TestDocumentFormat:
    """Test DocumentFormat enum functionality."""
    
    def test_from_path(self):
        """Test format detection from file path."""
        assert DocumentFormat.from_path("test.pdf") == DocumentFormat.PDF
        assert DocumentFormat.from_path("test.PNG") == DocumentFormat.PNG
        assert DocumentFormat.from_path("test.jpeg") == DocumentFormat.JPEG
        assert DocumentFormat.from_path("test.jpg") == DocumentFormat.JPG
        assert DocumentFormat.from_path("test.tiff") == DocumentFormat.TIFF
        assert DocumentFormat.from_path("test.tif") == DocumentFormat.TIFF
        assert DocumentFormat.from_path("test.bmp") == DocumentFormat.BMP
        assert DocumentFormat.from_path("test.unknown") == DocumentFormat.UNKNOWN
    
    def test_from_mime_type(self):
        """Test format detection from MIME type."""
        assert DocumentFormat.from_mime_type("application/pdf") == DocumentFormat.PDF
        assert DocumentFormat.from_mime_type("image/png") == DocumentFormat.PNG
        assert DocumentFormat.from_mime_type("image/jpeg") == DocumentFormat.JPEG
        assert DocumentFormat.from_mime_type("image/tiff") == DocumentFormat.TIFF
        assert DocumentFormat.from_mime_type("image/bmp") == DocumentFormat.BMP
        assert DocumentFormat.from_mime_type("unknown/type") == DocumentFormat.UNKNOWN


class TestPageInfo:
    """Test PageInfo class functionality."""
    
    def test_valid_page_info(self):
        """Test creation of valid page info."""
        page = PageInfo(
            page_number=0,
            width=800,
            height=600,
            dpi=150.0,
            rotation=90
        )
        
        assert page.page_number == 0
        assert page.width == 800
        assert page.height == 600
        assert page.dpi == 150.0
        assert page.rotation == 90
    
    def test_invalid_page_info(self):
        """Test validation of invalid page info."""
        # Negative page number
        with pytest.raises(ValueError, match="Page number cannot be negative"):
            PageInfo(page_number=-1, width=800, height=600)
        
        # Invalid dimensions
        with pytest.raises(ValueError, match="Page dimensions must be positive"):
            PageInfo(page_number=0, width=0, height=600)
        
        with pytest.raises(ValueError, match="Page dimensions must be positive"):
            PageInfo(page_number=0, width=800, height=-100)
        
        # Invalid DPI
        with pytest.raises(ValueError, match="DPI must be positive"):
            PageInfo(page_number=0, width=800, height=600, dpi=-72.0)
        
        # Invalid rotation
        with pytest.raises(ValueError, match="Rotation must be 0, 90, 180, or 270"):
            PageInfo(page_number=0, width=800, height=600, rotation=45)
    
    def test_properties(self):
        """Test page info properties."""
        page = PageInfo(page_number=0, width=800, height=600)
        
        assert page.aspect_ratio == 800 / 600
        assert page.area == 800 * 600
    
    def test_serialization(self):
        """Test page info serialization."""
        page = PageInfo(
            page_number=1,
            width=1200,
            height=800,
            dpi=300.0,
            text_content="Sample text"
        )
        
        # Test to_dict
        page_dict = page.to_dict()
        assert page_dict['page_number'] == 1
        assert page_dict['width'] == 1200
        assert page_dict['height'] == 800
        assert page_dict['aspect_ratio'] == 1.5
        assert page_dict['area'] == 960000
        
        # Test from_dict
        restored = PageInfo.from_dict(page_dict)
        assert restored.page_number == page.page_number
        assert restored.width == page.width
        assert restored.height == page.height
        assert restored.text_content == page.text_content


class TestDocument:
    """Test Document class functionality."""
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    @patch('src.gopnik.models.processing.Document._calculate_file_hash')
    def test_document_creation(self, mock_hash, mock_stat, mock_exists):
        """Test document creation."""
        mock_exists.return_value = True
        mock_stat.return_value = MagicMock(st_size=1024, st_ctime=1234567890, st_mtime=1234567890)
        mock_hash.return_value = "test_hash_123"
        
        doc = Document(
            path=Path("test.pdf"),
            format=DocumentFormat.PDF
        )
        
        assert doc.path == Path("test.pdf")
        assert doc.format == DocumentFormat.PDF
        assert len(doc.id) > 0
        assert doc.file_hash == "test_hash_123"
    
    def test_document_format_auto_detection(self):
        """Test automatic format detection."""
        with patch('pathlib.Path.exists', return_value=False):
            doc = Document(
                path=Path("test.png"),
                format="png"  # String format should be converted
            )
            
            assert doc.format == DocumentFormat.PNG
    
    def test_page_management(self):
        """Test page addition and retrieval."""
        with patch('pathlib.Path.exists', return_value=False):
            doc = Document(path=Path("test.pdf"), format=DocumentFormat.PDF)
            
            # Add pages
            page1 = PageInfo(page_number=0, width=800, height=600)
            page2 = PageInfo(page_number=1, width=800, height=600)
            
            doc.add_page(page1)
            doc.add_page(page2)
            
            assert doc.page_count == 2
            assert doc.is_multi_page is True
            assert doc.get_page(0) == page1
            assert doc.get_page(1) == page2
            assert doc.get_page(2) is None
    
    def test_page_number_validation(self):
        """Test page number validation."""
        with patch('pathlib.Path.exists', return_value=False):
            doc = Document(path=Path("test.pdf"), format=DocumentFormat.PDF)
            
            # Try to add page with wrong number
            page = PageInfo(page_number=1, width=800, height=600)  # Should be 0
            
            with pytest.raises(ValueError, match="Page number 1 doesn't match expected 0"):
                doc.add_page(page)
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    @patch('src.gopnik.models.processing.Document._calculate_file_hash')
    def test_integrity_validation(self, mock_hash, mock_stat, mock_exists):
        """Test document integrity validation."""
        mock_exists.return_value = True
        mock_stat.return_value = MagicMock(st_size=1024)
        
        # Mock initial hash calculation
        mock_hash.return_value = "original_hash_123"
        
        doc = Document(path=Path("test.pdf"), format=DocumentFormat.PDF)
        original_hash = doc.file_hash
        
        # Test validation with same hash
        mock_hash.return_value = "original_hash_123"
        assert doc.validate_integrity() is True
        
        # Test validation with different hash
        mock_hash.return_value = "different_hash_456"
        assert doc.validate_integrity() is False
    
    def test_document_serialization(self):
        """Test document serialization."""
        with patch('pathlib.Path.exists', return_value=False):
            doc = Document(
                path=Path("test.pdf"),
                format=DocumentFormat.PDF
            )
            
            # Add a page
            page = PageInfo(page_number=0, width=800, height=600)
            doc.add_page(page)
            
            # Test to_dict
            doc_dict = doc.to_dict()
            assert doc_dict['path'] == str(doc.path)
            assert doc_dict['format'] == 'pdf'
            assert doc_dict['page_count'] == 1
            assert len(doc_dict['pages']) == 1
            
            # Test from_dict
            restored = Document.from_dict(doc_dict)
            assert restored.path == doc.path
            assert restored.format == doc.format
            assert restored.page_count == doc.page_count
            
            # Test JSON serialization
            json_str = doc.to_json()
            restored_from_json = Document.from_json(json_str)
            assert restored_from_json.id == doc.id


class TestProcessingMetrics:
    """Test ProcessingMetrics class functionality."""
    
    def test_valid_metrics(self):
        """Test creation of valid metrics."""
        metrics = ProcessingMetrics(
            total_time=10.5,
            detection_time=3.2,
            redaction_time=5.1,
            pages_processed=5,
            detections_found=12
        )
        
        assert metrics.total_time == 10.5
        assert metrics.pages_processed == 5
        assert metrics.detections_found == 12
    
    def test_invalid_metrics(self):
        """Test validation of invalid metrics."""
        # Negative total time
        with pytest.raises(ValueError, match="Total time cannot be negative"):
            ProcessingMetrics(total_time=-1.0)
        
        # Negative individual times
        with pytest.raises(ValueError, match="Individual times cannot be negative"):
            ProcessingMetrics(total_time=10.0, detection_time=-1.0)
        
        # Negative pages
        with pytest.raises(ValueError, match="Pages processed cannot be negative"):
            ProcessingMetrics(total_time=10.0, pages_processed=-1)
        
        # Negative detections
        with pytest.raises(ValueError, match="Detections found cannot be negative"):
            ProcessingMetrics(total_time=10.0, detections_found=-1)
    
    def test_calculated_properties(self):
        """Test calculated properties."""
        metrics = ProcessingMetrics(
            total_time=10.0,
            pages_processed=5,
            detections_found=15
        )
        
        assert metrics.pages_per_second == 0.5
        assert metrics.detections_per_page == 3.0
        
        # Test edge cases
        zero_time_metrics = ProcessingMetrics(total_time=0.0, pages_processed=5)
        assert zero_time_metrics.pages_per_second == 0.0
        
        zero_pages_metrics = ProcessingMetrics(total_time=10.0, pages_processed=0, detections_found=5)
        assert zero_pages_metrics.detections_per_page == 0.0


class TestProcessingResult:
    """Test ProcessingResult class functionality."""
    
    @patch('src.gopnik.models.processing.Document._calculate_file_hash')
    def create_sample_document(self, mock_hash) -> Document:
        """Create a sample document for testing."""
        mock_hash.return_value = "sample_hash_123"
        with patch('pathlib.Path.exists', return_value=False):
            doc = Document(path=Path("test.pdf"), format=DocumentFormat.PDF)
            page = PageInfo(page_number=0, width=800, height=600)
            doc.add_page(page)
            return doc
    
    def create_sample_detections(self) -> PIIDetectionCollection:
        """Create sample detections for testing."""
        detection = PIIDetection(
            type=PIIType.FACE,
            bounding_box=BoundingBox(0, 0, 100, 100),
            confidence=0.95
        )
        return PIIDetectionCollection(detections=[detection])
    
    def create_sample_audit_log(self, document_id: str) -> AuditLog:
        """Create sample audit log for testing."""
        return AuditLog(
            operation=AuditOperation.DOCUMENT_REDACTION,
            timestamp=datetime.now(timezone.utc),
            document_id=document_id
        )
    
    def test_processing_result_creation(self):
        """Test processing result creation."""
        doc = self.create_sample_document()
        detections = self.create_sample_detections()
        audit_log = self.create_sample_audit_log(doc.id)
        
        result = ProcessingResult(
            document_id=doc.id,
            input_document=doc,
            detections=detections,
            audit_log=audit_log,
            status=ProcessingStatus.COMPLETED
        )
        
        assert result.document_id == doc.id
        assert result.input_document == doc
        assert result.status == ProcessingStatus.COMPLETED
        assert len(result.id) > 0
    
    def test_document_id_consistency(self):
        """Test document ID consistency enforcement."""
        doc = self.create_sample_document()
        detections = self.create_sample_detections()
        audit_log = self.create_sample_audit_log(doc.id)
        
        # Create result with different document_id
        result = ProcessingResult(
            document_id="different_id",
            input_document=doc,
            detections=detections,
            audit_log=audit_log,
            status=ProcessingStatus.COMPLETED
        )
        
        # Should be corrected to match input document
        assert result.document_id == doc.id
        assert result.detections.document_id == doc.id
    
    def test_processing_completion(self):
        """Test processing completion marking."""
        doc = self.create_sample_document()
        detections = self.create_sample_detections()
        audit_log = self.create_sample_audit_log(doc.id)
        
        result = ProcessingResult(
            document_id=doc.id,
            input_document=doc,
            detections=detections,
            audit_log=audit_log,
            status=ProcessingStatus.IN_PROGRESS
        )
        
        # Mark as completed
        result.mark_completed(success=True)
        
        assert result.status == ProcessingStatus.COMPLETED
        assert result.success is True
        assert result.completed_at is not None
        assert result.metrics is not None
    
    def test_processing_failure(self):
        """Test processing failure marking."""
        doc = self.create_sample_document()
        detections = self.create_sample_detections()
        audit_log = self.create_sample_audit_log(doc.id)
        
        result = ProcessingResult(
            document_id=doc.id,
            input_document=doc,
            detections=detections,
            audit_log=audit_log,
            status=ProcessingStatus.IN_PROGRESS
        )
        
        # Mark as failed
        error_msg = "Processing failed due to invalid input"
        result.mark_failed(error_msg)
        
        assert result.status == ProcessingStatus.FAILED
        assert result.success is False
        assert error_msg in result.errors
        assert result.completed_at is not None
    
    def test_detection_methods(self):
        """Test detection retrieval methods."""
        doc = self.create_sample_document()
        
        # Create multiple detections
        face_detection = PIIDetection(
            type=PIIType.FACE,
            bounding_box=BoundingBox(0, 0, 100, 100),
            confidence=0.95,
            page_number=0
        )
        email_detection = PIIDetection(
            type=PIIType.EMAIL,
            bounding_box=BoundingBox(200, 200, 300, 250),
            confidence=0.85,
            page_number=0
        )
        
        detections = PIIDetectionCollection(detections=[face_detection, email_detection])
        audit_log = self.create_sample_audit_log(doc.id)
        
        result = ProcessingResult(
            document_id=doc.id,
            input_document=doc,
            detections=detections,
            audit_log=audit_log,
            status=ProcessingStatus.COMPLETED
        )
        
        # Test detection retrieval
        assert result.detection_count == 2
        assert set(result.detection_types) == {'face', 'email'}
        
        face_detections = result.get_detections_by_type('face')
        assert len(face_detections) == 1
        assert face_detections[0].type == PIIType.FACE
        
        high_conf_detections = result.get_high_confidence_detections(threshold=0.9)
        assert len(high_conf_detections) == 1
        assert high_conf_detections[0].type == PIIType.FACE
        
        page_detections = result.get_detections_by_page(0)
        assert len(page_detections) == 2
    
    def test_processing_result_serialization(self):
        """Test processing result serialization."""
        doc = self.create_sample_document()
        detections = self.create_sample_detections()
        audit_log = self.create_sample_audit_log(doc.id)
        
        result = ProcessingResult(
            document_id=doc.id,
            input_document=doc,
            detections=detections,
            audit_log=audit_log,
            status=ProcessingStatus.COMPLETED,
            profile_name="test_profile"
        )
        
        # Test to_dict
        result_dict = result.to_dict()
        assert result_dict['document_id'] == doc.id
        assert result_dict['status'] == 'completed'
        assert result_dict['profile_name'] == 'test_profile'
        assert 'summary' in result_dict
        
        # Test from_dict
        restored = ProcessingResult.from_dict(result_dict)
        assert restored.document_id == result.document_id
        assert restored.status == result.status
        assert restored.profile_name == result.profile_name
        
        # Test JSON serialization
        json_str = result.to_json()
        restored_from_json = ProcessingResult.from_json(json_str)
        assert restored_from_json.id == result.id


class TestBatchProcessingResult:
    """Test BatchProcessingResult class functionality."""
    
    def create_sample_results(self, count: int = 3) -> List[ProcessingResult]:
        """Create sample processing results."""
        results = []
        
        for i in range(count):
            with patch('pathlib.Path.exists', return_value=False):
                doc = Document(path=Path(f"test_{i}.pdf"), format=DocumentFormat.PDF)
                page = PageInfo(page_number=0, width=800, height=600)
                doc.add_page(page)
            
            detections = PIIDetectionCollection()
            audit_log = AuditLog(
                operation=AuditOperation.DOCUMENT_REDACTION,
                timestamp=datetime.now(timezone.utc),
                document_id=doc.id
            )
            
            # Make some results fail
            status = ProcessingStatus.FAILED if i == count - 1 else ProcessingStatus.COMPLETED
            
            result = ProcessingResult(
                document_id=doc.id,
                input_document=doc,
                detections=detections,
                audit_log=audit_log,
                status=status
            )
            
            if status == ProcessingStatus.FAILED:
                result.add_error("Sample error")
            
            results.append(result)
        
        return results
    
    def test_batch_result_creation(self):
        """Test batch processing result creation."""
        results = self.create_sample_results(3)
        
        batch_result = BatchProcessingResult(
            id="batch_123",
            input_directory=Path("/input"),
            output_directory=Path("/output"),
            results=results,
            started_at=datetime.now(timezone.utc),
            total_documents=3
        )
        
        assert batch_result.id == "batch_123"
        assert batch_result.total_documents == 3
        assert batch_result.processed_documents == 2  # 2 successful
        assert batch_result.failed_documents == 1     # 1 failed
    
    def test_batch_statistics(self):
        """Test batch processing statistics."""
        results = self.create_sample_results(4)
        
        batch_result = BatchProcessingResult(
            id="batch_123",
            input_directory=Path("/input"),
            output_directory=Path("/output"),
            results=results,
            started_at=datetime.now(timezone.utc),
            total_documents=4
        )
        
        # Test success rate
        assert batch_result.success_rate == 75.0  # 3 out of 4 successful
        
        # Test result filtering
        failed_results = batch_result.get_failed_results()
        assert len(failed_results) == 1
        
        successful_results = batch_result.get_successful_results()
        assert len(successful_results) == 3
        
        # Test statistics
        stats = batch_result.get_statistics()
        assert stats['total_documents'] == 4
        assert stats['processed_documents'] == 3
        assert stats['failed_documents'] == 1
        assert stats['success_rate'] == 75.0
    
    def test_batch_completion(self):
        """Test batch completion marking."""
        results = self.create_sample_results(2)
        
        batch_result = BatchProcessingResult(
            id="batch_123",
            input_directory=Path("/input"),
            output_directory=Path("/output"),
            results=results,
            started_at=datetime.now(timezone.utc),
            total_documents=2
        )
        
        assert batch_result.is_completed is False
        
        batch_result.mark_completed()
        
        assert batch_result.is_completed is True
        assert batch_result.completed_at is not None
    
    def test_batch_serialization(self):
        """Test batch result serialization."""
        results = self.create_sample_results(2)
        
        batch_result = BatchProcessingResult(
            id="batch_123",
            input_directory=Path("/input"),
            output_directory=Path("/output"),
            results=results,
            started_at=datetime.now(timezone.utc),
            total_documents=2,
            profile_name="test_profile"
        )
        
        # Test to_dict
        batch_dict = batch_result.to_dict()
        assert batch_dict['id'] == "batch_123"
        assert batch_dict['total_documents'] == 2
        assert len(batch_dict['results']) == 2
        assert 'statistics' in batch_dict
        
        # Test from_dict
        restored = BatchProcessingResult.from_dict(batch_dict)
        assert restored.id == batch_result.id
        assert restored.total_documents == batch_result.total_documents
        assert len(restored.results) == len(batch_result.results)
        
        # Test JSON serialization
        json_str = batch_result.to_json()
        restored_from_json = BatchProcessingResult.from_json(json_str)
        assert restored_from_json.id == batch_result.id


class TestUtilityFunctions:
    """Test utility functions for processing results."""
    
    def create_sample_result(self, success: bool = True) -> ProcessingResult:
        """Create a sample processing result."""
        with patch('pathlib.Path.exists', return_value=False):
            doc = Document(path=Path("test.pdf"), format=DocumentFormat.PDF)
            page = PageInfo(page_number=0, width=800, height=600)
            doc.add_page(page)
        
        detections = PIIDetectionCollection()
        audit_log = AuditLog(
            operation=AuditOperation.DOCUMENT_REDACTION,
            timestamp=datetime.now(timezone.utc),
            document_id=doc.id
        )
        
        status = ProcessingStatus.COMPLETED if success else ProcessingStatus.FAILED
        result = ProcessingResult(
            document_id=doc.id,
            input_document=doc,
            detections=detections,
            audit_log=audit_log,
            status=status
        )
        
        if not success:
            result.add_error("Test error")
        
        return result
    
    def test_validate_processing_result(self):
        """Test processing result validation."""
        # Valid result
        valid_result = self.create_sample_result(success=True)
        valid_result.mark_completed()
        
        is_valid, errors = validate_processing_result(valid_result)
        assert is_valid is True
        assert len(errors) == 0
        
        # Invalid result - missing completion timestamp
        invalid_result = self.create_sample_result(success=True)
        invalid_result.status = ProcessingStatus.COMPLETED
        # Don't call mark_completed() to leave completed_at as None
        
        is_valid, errors = validate_processing_result(invalid_result)
        assert is_valid is False
        assert any("Completed status but no completion timestamp" in error for error in errors)
    
    def test_merge_processing_results(self):
        """Test merging multiple processing results."""
        results = [
            self.create_sample_result(success=True),
            self.create_sample_result(success=True),
            self.create_sample_result(success=False)
        ]
        
        # Set processing times
        for i, result in enumerate(results):
            result.mark_completed()
            if result.metrics:
                result.metrics.total_time = float(i + 1)
        
        merged_stats = merge_processing_results(results)
        
        assert merged_stats['total_results'] == 3
        assert merged_stats['successful_results'] == 2
        assert merged_stats['failed_results'] == 1
        assert merged_stats['success_rate'] == (2/3) * 100
        assert merged_stats['total_processing_time'] > 0
    
    def test_create_processing_summary_report(self):
        """Test processing summary report creation."""
        results = [
            self.create_sample_result(success=True),
            self.create_sample_result(success=False)
        ]
        
        for result in results:
            result.mark_completed()
        
        report = create_processing_summary_report(results)
        
        assert "Processing Summary Report" in report
        assert "Total Documents: 2" in report
        assert "Successful: 1" in report
        assert "Failed: 1" in report
        
        # Test empty results
        empty_report = create_processing_summary_report([])
        assert "No processing results to summarize" in empty_report


if __name__ == "__main__":
    pytest.main([__file__])