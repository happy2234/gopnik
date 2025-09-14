"""
Error response and exception data models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid


@dataclass
class ErrorResponse:
    """
    Standardized error response format.
    
    Attributes:
        error_code: Unique error code identifier
        message: Human-readable error message
        details: Additional error details
        timestamp: When error occurred
        request_id: Unique request identifier
        suggestions: List of suggested solutions
        context: Additional context information
    """
    error_code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    suggestions: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error response to dictionary format.
        
        Returns:
            Dictionary representation of error
        """
        return {
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'request_id': self.request_id,
            'suggestions': self.suggestions,
            'context': self.context
        }


class GopnikException(Exception):
    """Base exception class for Gopnik-specific errors."""
    
    def __init__(self, message: str, error_code: str = "GOPNIK_ERROR", 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now()
    
    def to_error_response(self) -> ErrorResponse:
        """Convert exception to ErrorResponse object."""
        return ErrorResponse(
            error_code=self.error_code,
            message=self.message,
            details=self.details,
            timestamp=self.timestamp
        )


class DocumentProcessingError(GopnikException):
    """Exception raised during document processing operations."""
    
    def __init__(self, message: str, document_path: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DOCUMENT_PROCESSING_ERROR", details)
        if document_path:
            self.details['document_path'] = document_path


class AIEngineError(GopnikException):
    """Exception raised by AI engine components."""
    
    def __init__(self, message: str, engine_type: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AI_ENGINE_ERROR", details)
        if engine_type:
            self.details['engine_type'] = engine_type


class ProfileValidationError(GopnikException):
    """Exception raised during profile validation."""
    
    def __init__(self, message: str, profile_name: Optional[str] = None,
                 validation_errors: Optional[List[str]] = None):
        details = {}
        if profile_name:
            details['profile_name'] = profile_name
        if validation_errors:
            details['validation_errors'] = validation_errors
        
        super().__init__(message, "PROFILE_VALIDATION_ERROR", details)


class AuditError(GopnikException):
    """Exception raised during audit operations."""
    
    def __init__(self, message: str, audit_id: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUDIT_ERROR", details)
        if audit_id:
            self.details['audit_id'] = audit_id


class IntegrityValidationError(GopnikException):
    """Exception raised during document integrity validation."""
    
    def __init__(self, message: str, document_id: Optional[str] = None,
                 expected_hash: Optional[str] = None, actual_hash: Optional[str] = None):
        details = {}
        if document_id:
            details['document_id'] = document_id
        if expected_hash:
            details['expected_hash'] = expected_hash
        if actual_hash:
            details['actual_hash'] = actual_hash
        
        super().__init__(message, "INTEGRITY_VALIDATION_ERROR", details)