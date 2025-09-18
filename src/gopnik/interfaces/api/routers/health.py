"""
Health check and status endpoints.
"""

from fastapi import APIRouter, Depends
from datetime import datetime, timezone
import logging

from ..models import HealthResponse
from ..dependencies import check_system_health


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(health_status: dict = Depends(check_system_health)):
    """
    Get system health status.
    
    Returns comprehensive health information including:
    - Overall system status
    - Component availability
    - Supported document formats
    - Processing statistics
    - System warnings (if any)
    """
    return HealthResponse(
        status=health_status.get('status', 'unknown'),
        timestamp=datetime.now(timezone.utc),
        components=health_status.get('components', {}),
        supported_formats=health_status.get('supported_formats', []),
        statistics=health_status.get('statistics', {}),
        warnings=health_status.get('warnings')
    )


@router.get("/status")
async def simple_status():
    """
    Simple status endpoint for basic health checks.
    
    Returns:
        Simple status response
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc),
        "service": "gopnik-api"
    }