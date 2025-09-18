"""
REST API interface for Gopnik deidentification system.

Provides FastAPI-based endpoints for system integration.
"""

from .app import app, create_app, run_server
from .models import (
    HealthResponse, ProcessingResponse, ProfileResponse,
    ValidationResponse, ErrorResponse, ProcessingRequest,
    BatchProcessingRequest, ProfileCreateRequest, ProfileUpdateRequest
)

__all__ = [
    "app",
    "create_app", 
    "run_server",
    "HealthResponse",
    "ProcessingResponse",
    "ProfileResponse", 
    "ValidationResponse",
    "ErrorResponse",
    "ProcessingRequest",
    "BatchProcessingRequest",
    "ProfileCreateRequest",
    "ProfileUpdateRequest"
]