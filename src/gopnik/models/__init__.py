"""
Data models and structures for the Gopnik deidentification system.
"""

from .pii import (
    PIIDetection, PIIType, BoundingBox, PIIDetectionCollection,
    validate_detection_confidence, validate_coordinates,
    merge_overlapping_detections, filter_detections_by_confidence,
    group_detections_by_type, calculate_detection_coverage
)
from .processing import ProcessingResult, Document
from .profiles import RedactionProfile, RedactionStyle
from .audit import AuditLog
from .errors import ErrorResponse

__all__ = [
    "PIIDetection",
    "PIIType",
    "BoundingBox", 
    "PIIDetectionCollection",
    "ProcessingResult",
    "Document",
    "RedactionProfile",
    "RedactionStyle",
    "AuditLog",
    "ErrorResponse",
    "validate_detection_confidence",
    "validate_coordinates",
    "merge_overlapping_detections",
    "filter_detections_by_confidence",
    "group_detections_by_type",
    "calculate_detection_coverage"
]