"""
Base interfaces and abstract classes for core system components.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from ..models import PIIDetection, ProcessingResult, RedactionProfile, AuditLog


class DocumentProcessorInterface(ABC):
    """Abstract interface for document processing operations."""
    
    @abstractmethod
    def process_document(self, input_path: Path, profile: RedactionProfile) -> ProcessingResult:
        """Process a single document with the given redaction profile."""
        pass
    
    @abstractmethod
    def validate_document(self, document_path: Path, audit_path: Path) -> bool:
        """Validate document integrity using audit trail."""
        pass
    
    @abstractmethod
    def batch_process(self, input_dir: Path, profile: RedactionProfile) -> List[ProcessingResult]:
        """Process multiple documents in a directory."""
        pass


class AIEngineInterface(ABC):
    """Abstract interface for AI-powered PII detection engines."""
    
    @abstractmethod
    def detect_pii(self, document_data: Any) -> List[PIIDetection]:
        """Detect PII in document data and return detection results."""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """Return list of PII types this engine can detect."""
        pass
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the AI engine with given parameters."""
        pass


class AuditSystemInterface(ABC):
    """Abstract interface for audit logging and integrity validation."""
    
    @abstractmethod
    def create_audit_log(self, operation: str, details: Dict[str, Any]) -> AuditLog:
        """Create a new audit log entry."""
        pass
    
    @abstractmethod
    def sign_audit_log(self, audit_log: AuditLog) -> str:
        """Generate cryptographic signature for audit log."""
        pass
    
    @abstractmethod
    def verify_signature(self, audit_log: AuditLog, signature: str) -> bool:
        """Verify the cryptographic signature of an audit log."""
        pass
    
    @abstractmethod
    def generate_document_hash(self, document_path: Path) -> str:
        """Generate cryptographic hash for document integrity."""
        pass


class RedactionEngineInterface(ABC):
    """Abstract interface for document redaction operations."""
    
    @abstractmethod
    def apply_redactions(self, document_path: Path, detections: List[PIIDetection], 
                        profile: RedactionProfile) -> Path:
        """Apply redactions to document based on detections and profile."""
        pass
    
    @abstractmethod
    def preserve_layout(self) -> bool:
        """Return whether this engine preserves document layout."""
        pass


class ProfileManagerInterface(ABC):
    """Abstract interface for redaction profile management."""
    
    @abstractmethod
    def load_profile(self, profile_name: str) -> RedactionProfile:
        """Load a redaction profile by name."""
        pass
    
    @abstractmethod
    def save_profile(self, profile: RedactionProfile) -> None:
        """Save a redaction profile."""
        pass
    
    @abstractmethod
    def list_profiles(self) -> List[str]:
        """List all available profile names."""
        pass
    
    @abstractmethod
    def validate_profile(self, profile: RedactionProfile) -> Tuple[bool, List[str]]:
        """Validate profile configuration and return errors if any."""
        pass