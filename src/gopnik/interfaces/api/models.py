"""
Pydantic models for API request/response serialization.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from enum import Enum
import uuid

from ...models.processing import ProcessingStatus, DocumentFormat
from ...models.pii import PIIType


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    components: Dict[str, str] = Field(..., description="Component status details")
    supported_formats: List[str] = Field(..., description="Supported document formats")
    statistics: Dict[str, Any] = Field(..., description="Processing statistics")
    warnings: Optional[List[str]] = Field(None, description="System warnings")


class PIIDetectionResponse(BaseModel):
    """PII detection response model."""
    id: str = Field(..., description="Detection ID")
    type: str = Field(..., description="PII type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    bounding_box: Dict[str, int] = Field(..., description="Bounding box coordinates")
    text_content: Optional[str] = Field(None, description="Detected text content")
    page_number: int = Field(..., ge=0, description="Page number (0-indexed)")
    detection_method: str = Field(..., description="Detection method used")


class ProcessingMetricsResponse(BaseModel):
    """Processing metrics response model."""
    total_time: float = Field(..., ge=0, description="Total processing time in seconds")
    detection_time: float = Field(..., ge=0, description="PII detection time")
    redaction_time: float = Field(..., ge=0, description="Redaction time")
    io_time: float = Field(..., ge=0, description="I/O time")
    pages_processed: int = Field(..., ge=0, description="Number of pages processed")
    detections_found: int = Field(..., ge=0, description="Number of detections found")
    pages_per_second: float = Field(..., ge=0, description="Processing rate")


class ProcessingResponse(BaseModel):
    """Document processing response model."""
    id: str = Field(..., description="Processing result ID")
    document_id: str = Field(..., description="Document ID")
    status: str = Field(..., description="Processing status")
    success: bool = Field(..., description="Whether processing was successful")
    detections: List[PIIDetectionResponse] = Field(..., description="PII detections found")
    metrics: Optional[ProcessingMetricsResponse] = Field(None, description="Processing metrics")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    profile_name: Optional[str] = Field(None, description="Redaction profile used")
    started_at: datetime = Field(..., description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    output_available: bool = Field(..., description="Whether processed output is available")


class BatchProcessingResponse(BaseModel):
    """Batch processing response model."""
    id: str = Field(..., description="Batch processing ID")
    total_documents: int = Field(..., ge=0, description="Total documents to process")
    processed_documents: int = Field(..., ge=0, description="Successfully processed documents")
    failed_documents: int = Field(..., ge=0, description="Failed documents")
    success_rate: float = Field(..., ge=0, le=100, description="Success rate percentage")
    results: List[ProcessingResponse] = Field(..., description="Individual processing results")
    started_at: datetime = Field(..., description="Batch processing start time")
    completed_at: Optional[datetime] = Field(None, description="Batch processing completion time")
    is_completed: bool = Field(..., description="Whether batch processing is completed")


class ProfileResponse(BaseModel):
    """Redaction profile response model."""
    name: str = Field(..., description="Profile name")
    description: str = Field(..., description="Profile description")
    visual_rules: Dict[str, bool] = Field(..., description="Visual PII redaction rules")
    text_rules: Dict[str, bool] = Field(..., description="Text PII redaction rules")
    redaction_style: str = Field(..., description="Redaction style")
    confidence_threshold: float = Field(..., ge=0.0, le=1.0, description="Confidence threshold")
    multilingual_support: List[str] = Field(..., description="Supported languages")
    version: str = Field(..., description="Profile version")


class ValidationResponse(BaseModel):
    """Document validation response model."""
    document_id: str = Field(..., description="Document ID")
    is_valid: bool = Field(..., description="Whether document is valid")
    validation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    integrity_check: bool = Field(..., description="File integrity check result")
    audit_trail_valid: bool = Field(..., description="Audit trail validation result")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


# Request models

class ProcessingRequest(BaseModel):
    """Document processing request model."""
    profile_name: Optional[str] = Field("default", description="Redaction profile to use")
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Override confidence threshold")
    output_format: Optional[str] = Field(None, description="Desired output format")
    
    @field_validator('profile_name')
    @classmethod
    def validate_profile_name(cls, v):
        if v and not v.strip():
            raise ValueError("Profile name cannot be empty")
        return v


class BatchProcessingRequest(BaseModel):
    """Batch processing request model."""
    profile_name: Optional[str] = Field("default", description="Redaction profile to use")
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Override confidence threshold")
    output_format: Optional[str] = Field(None, description="Desired output format")
    recursive: bool = Field(True, description="Process subdirectories recursively")
    
    @field_validator('profile_name')
    @classmethod
    def validate_profile_name(cls, v):
        if v and not v.strip():
            raise ValueError("Profile name cannot be empty")
        return v


class ProfileCreateRequest(BaseModel):
    """Profile creation request model."""
    name: str = Field(..., description="Profile name")
    description: str = Field(..., description="Profile description")
    visual_rules: Dict[str, bool] = Field(default_factory=dict, description="Visual PII redaction rules")
    text_rules: Dict[str, bool] = Field(default_factory=dict, description="Text PII redaction rules")
    redaction_style: str = Field("solid_black", description="Redaction style")
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Confidence threshold")
    multilingual_support: List[str] = Field(default_factory=list, description="Supported languages")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Profile name cannot be empty")
        if len(v) > 100:
            raise ValueError("Profile name too long (max 100 characters)")
        return v.strip()
    
    @field_validator('redaction_style')
    @classmethod
    def validate_redaction_style(cls, v):
        valid_styles = ["solid_black", "solid_white", "pixelated", "blurred", "pattern"]
        if v not in valid_styles:
            raise ValueError(f"Invalid redaction style. Must be one of: {valid_styles}")
        return v


class ProfileUpdateRequest(BaseModel):
    """Profile update request model."""
    description: Optional[str] = Field(None, description="Profile description")
    visual_rules: Optional[Dict[str, bool]] = Field(None, description="Visual PII redaction rules")
    text_rules: Optional[Dict[str, bool]] = Field(None, description="Text PII redaction rules")
    redaction_style: Optional[str] = Field(None, description="Redaction style")
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence threshold")
    multilingual_support: Optional[List[str]] = Field(None, description="Supported languages")
    
    @field_validator('redaction_style')
    @classmethod
    def validate_redaction_style(cls, v):
        if v is not None:
            valid_styles = ["solid_black", "solid_white", "pixelated", "blurred", "pattern"]
            if v not in valid_styles:
                raise ValueError(f"Invalid redaction style. Must be one of: {valid_styles}")
        return v


# Job tracking models for async processing

class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobResponse(BaseModel):
    """Async job response model."""
    job_id: str = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Job status")
    created_at: datetime = Field(..., description="Job creation time")
    started_at: Optional[datetime] = Field(None, description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Job progress percentage")
    result: Optional[Union[ProcessingResponse, BatchProcessingResponse]] = Field(None, description="Job result")
    error: Optional[str] = Field(None, description="Error message if job failed")


class JobListResponse(BaseModel):
    """Job list response model."""
    jobs: List[JobResponse] = Field(..., description="List of jobs")
    total: int = Field(..., ge=0, description="Total number of jobs")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Page size")