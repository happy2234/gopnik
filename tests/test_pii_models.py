"""
Unit tests for PII detection data models.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch

from src.gopnik.models.pii import (
    PIIType, BoundingBox, PIIDetection, PIIDetectionCollection,
    validate_detection_confidence, validate_coordinates,
    merge_overlapping_detections, filter_detections_by_confidence,
    group_detections_by_type, calculate_detection_coverage
)


class TestPIIType:
    """Test PIIType enum functionality."""
    
    def test_visual_types(self):
        """Test visual PII types classification."""
        visual_types = PIIType.visual_types()
        expected = [PIIType.FACE, PIIType.SIGNATURE, PIIType.BARCODE, PIIType.QR_CODE]
        assert set(visual_types) == set(expected)
    
    def test_text_types(self):
        """Test text PII types classification."""
        text_types = PIIType.text_types()
        visual_types = PIIType.visual_types()
        
        # Ensure no overlap
        assert not set(text_types).intersection(set(visual_types))
        
        # Ensure all types are covered
        all_types = set(text_types + visual_types)
        assert all_types == set(PIIType)
    
    def test_sensitive_types(self):
        """Test sensitive PII types classification."""
        sensitive_types = PIIType.sensitive_types()
        expected = [
            PIIType.SSN, PIIType.CREDIT_CARD, PIIType.PASSPORT_NUMBER,
            PIIType.DRIVER_LICENSE, PIIType.MEDICAL_RECORD_NUMBER,
            PIIType.BANK_ACCOUNT
        ]
        assert set(sensitive_types) == set(expected)


class TestBoundingBox:
    """Test BoundingBox class functionality."""
    
    def test_valid_bounding_box(self):
        """Test creation of valid bounding box."""
        bbox = BoundingBox(10, 20, 100, 200)
        assert bbox.x1 == 10
        assert bbox.y1 == 20
        assert bbox.x2 == 100
        assert bbox.y2 == 200
    
    def test_invalid_coordinates(self):
        """Test validation of invalid coordinates."""
        # x1 >= x2
        with pytest.raises(ValueError, match="x1.*must be less than x2"):
            BoundingBox(100, 20, 100, 200)
        
        # y1 >= y2
        with pytest.raises(ValueError, match="y1.*must be less than y2"):
            BoundingBox(10, 200, 100, 200)
        
        # Negative coordinates
        with pytest.raises(ValueError, match="Coordinates cannot be negative"):
            BoundingBox(-10, 20, 100, 200)
    
    def test_properties(self):
        """Test bounding box properties."""
        bbox = BoundingBox(10, 20, 110, 120)
        assert bbox.width == 100
        assert bbox.height == 100
        assert bbox.area == 10000
        assert bbox.center == (60.0, 70.0)
    
    def test_to_tuple(self):
        """Test conversion to tuple."""
        bbox = BoundingBox(10, 20, 100, 200)
        assert bbox.to_tuple() == (10, 20, 100, 200)
    
    def test_from_tuple(self):
        """Test creation from tuple."""
        coords = (10, 20, 100, 200)
        bbox = BoundingBox.from_tuple(coords)
        assert bbox.to_tuple() == coords
    
    def test_overlaps_with(self):
        """Test overlap detection."""
        bbox1 = BoundingBox(0, 0, 100, 100)
        bbox2 = BoundingBox(50, 50, 150, 150)  # 50% overlap
        bbox3 = BoundingBox(200, 200, 300, 300)  # No overlap
        
        assert bbox1.overlaps_with(bbox2, threshold=0.0)
        assert bbox1.overlaps_with(bbox2, threshold=0.2)
        assert not bbox1.overlaps_with(bbox2, threshold=0.8)
        assert not bbox1.overlaps_with(bbox3, threshold=0.0)
    
    def test_intersection_over_union(self):
        """Test IoU calculation."""
        bbox1 = BoundingBox(0, 0, 100, 100)  # Area: 10000
        bbox2 = BoundingBox(50, 50, 150, 150)  # Area: 10000, Intersection: 2500
        bbox3 = BoundingBox(200, 200, 300, 300)  # No overlap
        
        iou = bbox1.intersection_over_union(bbox2)
        expected_iou = 2500 / (10000 + 10000 - 2500)  # 2500 / 17500
        assert abs(iou - expected_iou) < 0.001
        
        assert bbox1.intersection_over_union(bbox3) == 0.0
    
    def test_expand(self):
        """Test bounding box expansion."""
        bbox = BoundingBox(10, 10, 90, 90)
        expanded = bbox.expand(5)
        
        assert expanded.x1 == 5
        assert expanded.y1 == 5
        assert expanded.x2 == 95
        assert expanded.y2 == 95
        
        # Test expansion with clipping to zero
        small_bbox = BoundingBox(2, 2, 10, 10)
        expanded_small = small_bbox.expand(5)
        assert expanded_small.x1 == 0  # Clipped to 0
        assert expanded_small.y1 == 0  # Clipped to 0
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        bbox = BoundingBox(10, 20, 110, 120)
        bbox_dict = bbox.to_dict()
        
        expected = {
            'x1': 10, 'y1': 20, 'x2': 110, 'y2': 120,
            'width': 100, 'height': 100, 'area': 10000
        }
        assert bbox_dict == expected


class TestPIIDetection:
    """Test PIIDetection class functionality."""
    
    def test_valid_detection(self):
        """Test creation of valid PII detection."""
        bbox = BoundingBox(10, 20, 100, 200)
        detection = PIIDetection(
            type=PIIType.FACE,
            bounding_box=bbox,
            confidence=0.95
        )
        
        assert detection.type == PIIType.FACE
        assert detection.bounding_box == bbox
        assert detection.confidence == 0.95
        assert detection.page_number == 0
        assert detection.detection_method == "unknown"
        assert isinstance(detection.timestamp, datetime)
        assert len(detection.id) > 0
    
    def test_confidence_validation(self):
        """Test confidence score validation."""
        bbox = BoundingBox(10, 20, 100, 200)
        
        # Valid confidence
        PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=0.5)
        PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=0.0)
        PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=1.0)
        
        # Invalid confidence
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=1.5)
        
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=-0.1)
        
        with pytest.raises(TypeError, match="Confidence must be a number"):
            PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence="0.5")
    
    def test_page_number_validation(self):
        """Test page number validation."""
        bbox = BoundingBox(10, 20, 100, 200)
        
        # Valid page numbers
        PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=0.5, page_number=0)
        PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=0.5, page_number=10)
        
        # Invalid page numbers
        with pytest.raises(ValueError, match="Page number cannot be negative"):
            PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=0.5, page_number=-1)
        
        with pytest.raises(TypeError, match="Page number must be an integer"):
            PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=0.5, page_number="0")
    
    def test_detection_method_validation(self):
        """Test detection method validation."""
        bbox = BoundingBox(10, 20, 100, 200)
        
        # Valid methods
        valid_methods = ["cv", "nlp", "hybrid", "manual", "unknown"]
        for method in valid_methods:
            PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=0.5, detection_method=method)
        
        # Invalid method
        with pytest.raises(ValueError, match="Detection method must be one of"):
            PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=0.5, detection_method="invalid")
    
    def test_properties(self):
        """Test detection properties."""
        bbox = BoundingBox(10, 20, 110, 120)
        detection = PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=0.95)
        
        assert detection.width == 100
        assert detection.height == 100
        assert detection.area == 10000
        assert detection.center == (60.0, 70.0)
        assert detection.coordinates == (10, 20, 110, 120)
        
        assert detection.is_visual_pii
        assert not detection.is_text_pii
        assert not detection.is_sensitive
    
    def test_pii_type_properties(self):
        """Test PII type classification properties."""
        bbox = BoundingBox(10, 20, 100, 200)
        
        # Visual PII
        face_detection = PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=0.95)
        assert face_detection.is_visual_pii
        assert not face_detection.is_text_pii
        
        # Text PII
        email_detection = PIIDetection(type=PIIType.EMAIL, bounding_box=bbox, confidence=0.95)
        assert not email_detection.is_visual_pii
        assert email_detection.is_text_pii
        
        # Sensitive PII
        ssn_detection = PIIDetection(type=PIIType.SSN, bounding_box=bbox, confidence=0.95)
        assert ssn_detection.is_sensitive
    
    def test_overlaps_with(self):
        """Test overlap detection between detections."""
        bbox1 = BoundingBox(0, 0, 100, 100)
        bbox2 = BoundingBox(50, 50, 150, 150)
        
        detection1 = PIIDetection(type=PIIType.FACE, bounding_box=bbox1, confidence=0.95)
        detection2 = PIIDetection(type=PIIType.FACE, bounding_box=bbox2, confidence=0.85)
        
        assert detection1.overlaps_with(detection2, threshold=0.1)
        assert not detection1.overlaps_with(detection2, threshold=0.8)
    
    def test_is_duplicate_of(self):
        """Test duplicate detection."""
        bbox1 = BoundingBox(0, 0, 100, 100)
        bbox2 = BoundingBox(10, 10, 110, 110)  # High overlap
        bbox3 = BoundingBox(200, 200, 300, 300)  # No overlap
        
        detection1 = PIIDetection(type=PIIType.FACE, bounding_box=bbox1, confidence=0.95, page_number=0)
        detection2 = PIIDetection(type=PIIType.FACE, bounding_box=bbox2, confidence=0.85, page_number=0)
        detection3 = PIIDetection(type=PIIType.FACE, bounding_box=bbox3, confidence=0.90, page_number=0)
        detection4 = PIIDetection(type=PIIType.NAME, bounding_box=bbox1, confidence=0.95, page_number=0)  # Different type
        detection5 = PIIDetection(type=PIIType.FACE, bounding_box=bbox1, confidence=0.95, page_number=1)  # Different page
        
        assert detection1.is_duplicate_of(detection2, iou_threshold=0.5)
        assert not detection1.is_duplicate_of(detection3, iou_threshold=0.5)
        assert not detection1.is_duplicate_of(detection4, iou_threshold=0.5)  # Different type
        assert not detection1.is_duplicate_of(detection5, iou_threshold=0.5)  # Different page
    
    def test_merge_with(self):
        """Test merging detections."""
        bbox1 = BoundingBox(0, 0, 100, 100)
        bbox2 = BoundingBox(10, 10, 110, 110)
        
        detection1 = PIIDetection(
            type=PIIType.FACE, bounding_box=bbox1, confidence=0.95,
            text_content="face1", detection_method="cv"
        )
        detection2 = PIIDetection(
            type=PIIType.FACE, bounding_box=bbox2, confidence=0.85,
            text_content="face2", detection_method="nlp"
        )
        
        merged = detection1.merge_with(detection2)
        
        assert merged.type == PIIType.FACE
        assert merged.confidence == 0.95  # Higher confidence
        assert merged.text_content == "face1"  # From higher confidence detection
        assert merged.detection_method == "hybrid"  # Different methods
        assert merged.bounding_box.x1 == 0  # Union of bounding boxes
        assert merged.bounding_box.y1 == 0
        assert merged.bounding_box.x2 == 110
        assert merged.bounding_box.y2 == 110
        assert 'merged_from' in merged.metadata
    
    def test_to_dict_and_from_dict(self):
        """Test dictionary serialization and deserialization."""
        bbox = BoundingBox(10, 20, 100, 200)
        original = PIIDetection(
            type=PIIType.EMAIL,
            bounding_box=bbox,
            confidence=0.95,
            text_content="test@example.com",
            page_number=1,
            detection_method="nlp",
            metadata={"source": "test"}
        )
        
        # Convert to dict and back
        detection_dict = original.to_dict()
        restored = PIIDetection.from_dict(detection_dict)
        
        assert restored.type == original.type
        assert restored.bounding_box.to_tuple() == original.bounding_box.to_tuple()
        assert restored.confidence == original.confidence
        assert restored.text_content == original.text_content
        assert restored.page_number == original.page_number
        assert restored.detection_method == original.detection_method
        assert restored.metadata == original.metadata
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        bbox = BoundingBox(10, 20, 100, 200)
        original = PIIDetection(
            type=PIIType.PHONE,
            bounding_box=bbox,
            confidence=0.88,
            text_content="+1-555-123-4567"
        )
        
        # Convert to JSON and back
        json_str = original.to_json()
        restored = PIIDetection.from_json(json_str)
        
        assert restored.type == original.type
        assert restored.confidence == original.confidence
        assert restored.text_content == original.text_content
    
    def test_legacy_coordinates_compatibility(self):
        """Test backward compatibility with coordinate tuples."""
        # Test from_dict with legacy coordinates format
        legacy_data = {
            'type': 'face',
            'coordinates': (10, 20, 100, 200),
            'confidence': 0.95
        }
        
        detection = PIIDetection.from_dict(legacy_data)
        assert detection.coordinates == (10, 20, 100, 200)
        assert detection.bounding_box.to_tuple() == (10, 20, 100, 200)


class TestPIIDetectionCollection:
    """Test PIIDetectionCollection class functionality."""
    
    def create_sample_detections(self) -> List[PIIDetection]:
        """Create sample detections for testing."""
        return [
            PIIDetection(
                type=PIIType.FACE,
                bounding_box=BoundingBox(0, 0, 100, 100),
                confidence=0.95,
                page_number=0
            ),
            PIIDetection(
                type=PIIType.EMAIL,
                bounding_box=BoundingBox(200, 200, 300, 250),
                confidence=0.88,
                text_content="test@example.com",
                page_number=0
            ),
            PIIDetection(
                type=PIIType.SSN,
                bounding_box=BoundingBox(50, 300, 200, 350),
                confidence=0.92,
                text_content="123-45-6789",
                page_number=1
            )
        ]
    
    def test_collection_creation(self):
        """Test collection creation and basic operations."""
        detections = self.create_sample_detections()
        collection = PIIDetectionCollection(
            detections=detections,
            document_id="test_doc",
            total_pages=2
        )
        
        assert len(collection) == 3
        assert collection.document_id == "test_doc"
        assert collection.total_pages == 2
        
        # Test iteration
        for i, detection in enumerate(collection):
            assert detection == detections[i]
        
        # Test indexing
        assert collection[0] == detections[0]
    
    def test_add_remove_detection(self):
        """Test adding and removing detections."""
        collection = PIIDetectionCollection()
        detection = self.create_sample_detections()[0]
        
        # Add detection
        collection.add_detection(detection)
        assert len(collection) == 1
        assert collection[0] == detection
        
        # Remove detection
        removed = collection.remove_detection(detection.id)
        assert removed is True
        assert len(collection) == 0
        
        # Try to remove non-existent detection
        removed = collection.remove_detection("non_existent")
        assert removed is False
    
    def test_filtering_methods(self):
        """Test various filtering methods."""
        detections = self.create_sample_detections()
        collection = PIIDetectionCollection(detections=detections)
        
        # Filter by type
        face_detections = collection.get_by_type(PIIType.FACE)
        assert len(face_detections) == 1
        assert face_detections[0].type == PIIType.FACE
        
        # Filter by page
        page0_detections = collection.get_by_page(0)
        assert len(page0_detections) == 2
        
        page1_detections = collection.get_by_page(1)
        assert len(page1_detections) == 1
        
        # Filter by confidence
        high_conf_detections = collection.get_high_confidence(threshold=0.9)
        assert len(high_conf_detections) == 2  # Face (0.95) and SSN (0.92)
        
        # Filter by PII category
        visual_detections = collection.get_visual_detections()
        assert len(visual_detections) == 1
        assert visual_detections[0].type == PIIType.FACE
        
        text_detections = collection.get_text_detections()
        assert len(text_detections) == 2
        
        sensitive_detections = collection.get_sensitive_detections()
        assert len(sensitive_detections) == 1
        assert sensitive_detections[0].type == PIIType.SSN
    
    def test_remove_duplicates(self):
        """Test duplicate removal."""
        # Create overlapping detections
        bbox1 = BoundingBox(0, 0, 100, 100)
        bbox2 = BoundingBox(10, 10, 110, 110)  # High overlap
        
        detection1 = PIIDetection(type=PIIType.FACE, bounding_box=bbox1, confidence=0.95)
        detection2 = PIIDetection(type=PIIType.FACE, bounding_box=bbox2, confidence=0.85)
        detection3 = PIIDetection(type=PIIType.EMAIL, bounding_box=bbox1, confidence=0.90)  # Different type
        
        collection = PIIDetectionCollection(detections=[detection1, detection2, detection3])
        
        removed_count = collection.remove_duplicates(iou_threshold=0.5)
        
        assert removed_count == 1  # One duplicate removed
        assert len(collection) == 2  # Two detections remain
        
        # The merged detection should have the higher confidence
        face_detections = collection.get_by_type(PIIType.FACE)
        assert len(face_detections) == 1
        assert face_detections[0].confidence == 0.95
    
    def test_sorting_methods(self):
        """Test sorting methods."""
        detections = self.create_sample_detections()
        collection = PIIDetectionCollection(detections=detections)
        
        # Sort by confidence (descending)
        collection.sort_by_confidence(descending=True)
        confidences = [d.confidence for d in collection.detections]
        assert confidences == sorted(confidences, reverse=True)
        
        # Sort by confidence (ascending)
        collection.sort_by_confidence(descending=False)
        confidences = [d.confidence for d in collection.detections]
        assert confidences == sorted(confidences)
        
        # Sort by area
        collection.sort_by_area(descending=True)
        areas = [d.area for d in collection.detections]
        assert areas == sorted(areas, reverse=True)
    
    def test_filter_by_confidence(self):
        """Test confidence filtering."""
        detections = self.create_sample_detections()
        collection = PIIDetectionCollection(detections=detections)
        
        original_count = len(collection)
        collection.filter_by_confidence(0.9)
        
        # Should keep detections with confidence >= 0.9
        assert len(collection) < original_count
        for detection in collection:
            assert detection.confidence >= 0.9
    
    def test_statistics(self):
        """Test statistics generation."""
        detections = self.create_sample_detections()
        collection = PIIDetectionCollection(detections=detections)
        
        stats = collection.get_statistics()
        
        assert stats['total_detections'] == 3
        assert stats['by_type']['face'] == 1
        assert stats['by_type']['email'] == 1
        assert stats['by_type']['ssn'] == 1
        assert stats['by_page'][0] == 2
        assert stats['by_page'][1] == 1
        assert stats['visual_count'] == 1
        assert stats['text_count'] == 2
        assert stats['sensitive_count'] == 1
        
        # Check confidence stats
        conf_stats = stats['confidence_stats']
        assert conf_stats['min'] == 0.88
        assert conf_stats['max'] == 0.95
        assert conf_stats['high_confidence_count'] >= 0
    
    def test_json_serialization(self):
        """Test JSON serialization of collection."""
        detections = self.create_sample_detections()
        collection = PIIDetectionCollection(
            detections=detections,
            document_id="test_doc",
            total_pages=2,
            processing_metadata={"version": "1.0"}
        )
        
        # Convert to JSON and back
        json_str = collection.to_json()
        restored = PIIDetectionCollection.from_json(json_str)
        
        assert len(restored) == len(collection)
        assert restored.document_id == collection.document_id
        assert restored.total_pages == collection.total_pages
        assert restored.processing_metadata == collection.processing_metadata


class TestUtilityFunctions:
    """Test utility functions for PII detection."""
    
    def test_validate_detection_confidence(self):
        """Test confidence validation function."""
        assert validate_detection_confidence(0.5) is True
        assert validate_detection_confidence(0.0) is True
        assert validate_detection_confidence(1.0) is True
        assert validate_detection_confidence(1.5) is False
        assert validate_detection_confidence(-0.1) is False
        assert validate_detection_confidence("0.5") is False
    
    def test_validate_coordinates(self):
        """Test coordinate validation function."""
        # Valid tuple coordinates
        assert validate_coordinates((10, 20, 100, 200)) is True
        
        # Valid BoundingBox
        bbox = BoundingBox(10, 20, 100, 200)
        assert validate_coordinates(bbox) is True
        
        # Invalid coordinates
        assert validate_coordinates((100, 20, 10, 200)) is False  # x1 >= x2
        assert validate_coordinates((-10, 20, 100, 200)) is False  # Negative
        assert validate_coordinates("invalid") is False  # Wrong type
    
    def test_merge_overlapping_detections(self):
        """Test merging overlapping detections function."""
        bbox1 = BoundingBox(0, 0, 100, 100)
        bbox2 = BoundingBox(10, 10, 110, 110)  # High overlap
        bbox3 = BoundingBox(200, 200, 300, 300)  # No overlap
        
        detections = [
            PIIDetection(type=PIIType.FACE, bounding_box=bbox1, confidence=0.95),
            PIIDetection(type=PIIType.FACE, bounding_box=bbox2, confidence=0.85),
            PIIDetection(type=PIIType.FACE, bounding_box=bbox3, confidence=0.90)
        ]
        
        merged = merge_overlapping_detections(detections, iou_threshold=0.5)
        
        assert len(merged) == 2  # Two groups: merged overlapping + separate
    
    def test_filter_detections_by_confidence(self):
        """Test confidence filtering function."""
        bbox = BoundingBox(10, 20, 100, 200)
        detections = [
            PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=0.95),
            PIIDetection(type=PIIType.EMAIL, bounding_box=bbox, confidence=0.75),
            PIIDetection(type=PIIType.SSN, bounding_box=bbox, confidence=0.85)
        ]
        
        filtered = filter_detections_by_confidence(detections, min_confidence=0.8)
        
        assert len(filtered) == 2  # Only 0.95 and 0.85 pass
        for detection in filtered:
            assert detection.confidence >= 0.8
    
    def test_group_detections_by_type(self):
        """Test grouping detections by type."""
        bbox = BoundingBox(10, 20, 100, 200)
        detections = [
            PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=0.95),
            PIIDetection(type=PIIType.FACE, bounding_box=bbox, confidence=0.85),
            PIIDetection(type=PIIType.EMAIL, bounding_box=bbox, confidence=0.90)
        ]
        
        groups = group_detections_by_type(detections)
        
        assert len(groups) == 2
        assert len(groups[PIIType.FACE]) == 2
        assert len(groups[PIIType.EMAIL]) == 1
    
    def test_calculate_detection_coverage(self):
        """Test detection coverage calculation."""
        bbox1 = BoundingBox(0, 0, 100, 100)  # Area: 10000
        bbox2 = BoundingBox(200, 200, 300, 250)  # Area: 5000
        
        detections = [
            PIIDetection(type=PIIType.FACE, bounding_box=bbox1, confidence=0.95),
            PIIDetection(type=PIIType.EMAIL, bounding_box=bbox2, confidence=0.85)
        ]
        
        document_area = 50000  # Total area
        coverage = calculate_detection_coverage(detections, document_area)
        
        expected_coverage = (10000 + 5000) / 50000  # 0.3
        assert abs(coverage - expected_coverage) < 0.001
        
        # Test edge cases
        assert calculate_detection_coverage([], 1000) == 0.0
        assert calculate_detection_coverage(detections, 0) == 0.0
        
        # Test coverage > 1.0 (should be capped at 1.0)
        small_document_area = 5000
        coverage = calculate_detection_coverage(detections, small_document_area)
        assert coverage == 1.0


if __name__ == "__main__":
    pytest.main([__file__])