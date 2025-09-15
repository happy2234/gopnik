"""
Data models and structures for the Gopnik deidentification system.
"""

from .pii import (
    PIIDetection, PIIType, BoundingBox, PIIDetectionCollection,
    validate_detection_confidence, validate_coordinates,
    merge_overlapping_detections, filter_detections_by_confidence,
    group_detections_by_type, calculate_detection_coverage
)
from .processing import (
    ProcessingResult, Document, PageInfo, ProcessingMetrics,
    BatchProcessingResult, ProcessingStatus, DocumentFormat,
    validate_processing_result, merge_processing_results,
    create_processing_summary_report
)
from .profiles import (
    RedactionProfile, RedactionStyle, ProfileManager,
    ProfileValidationError, ProfileConflictError
)
from .audit import (
    AuditLog, AuditTrail, SystemInfo, AuditOperation, AuditLevel,
    create_document_processing_audit_chain, validate_audit_log_integrity,
    merge_audit_trails, filter_audit_logs
)
from .errors import ErrorResponse

__all__ = [
    # PII Detection Models
    "PIIDetection",
    "PIIType",
    "BoundingBox", 
    "PIIDetectionCollection",
    "validate_detection_confidence",
    "validate_coordinates",
    "merge_overlapping_detections",
    "filter_detections_by_confidence",
    "group_detections_by_type",
    "calculate_detection_coverage",
    
    # Processing Models
    "ProcessingResult",
    "Document",
    "PageInfo",
    "ProcessingMetrics",
    "BatchProcessingResult",
    "ProcessingStatus",
    "DocumentFormat",
    "validate_processing_result",
    "merge_processing_results",
    "create_processing_summary_report",
    
    # Audit Models
    "AuditLog",
    "AuditTrail",
    "SystemInfo",
    "AuditOperation",
    "AuditLevel",
    "create_document_processing_audit_chain",
    "validate_audit_log_integrity",
    "merge_audit_trails",
    "filter_audit_logs",
    
    # Profile and Error Models
    "RedactionProfile",
    "RedactionStyle",
    "ProfileManager",
    "ProfileValidationError",
    "ProfileConflictError",
    "ErrorResponse"
]