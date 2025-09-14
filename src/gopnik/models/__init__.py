"""
Data models and structures for the Gopnik deidentification system.
"""

from .pii import PIIDetection, PIIType
from .processing import ProcessingResult, Document
from .profiles import RedactionProfile, RedactionStyle
from .audit import AuditLog
from .errors import ErrorResponse

__all__ = [
    "PIIDetection",
    "PIIType", 
    "ProcessingResult",
    "Document",
    "RedactionProfile",
    "RedactionStyle",
    "AuditLog",
    "ErrorResponse"
]