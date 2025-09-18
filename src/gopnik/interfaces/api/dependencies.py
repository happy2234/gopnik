"""
FastAPI dependency injection functions.
"""

from fastapi import Depends, HTTPException, Request
from typing import Optional
import logging

from ...core.processor import DocumentProcessor
from ...models.profiles import ProfileManager
from ...config import GopnikConfig
from .job_manager import job_manager


logger = logging.getLogger(__name__)


def get_config(request: Request) -> GopnikConfig:
    """
    Get application configuration.
    
    Args:
        request: FastAPI request object
        
    Returns:
        GopnikConfig instance
    """
    return request.app.state.config


def get_document_processor(request: Request) -> DocumentProcessor:
    """
    Get document processor instance.
    
    Args:
        request: FastAPI request object
        
    Returns:
        DocumentProcessor instance
    """
    return request.app.state.document_processor


def get_profile_manager(request: Request) -> ProfileManager:
    """
    Get profile manager instance.
    
    Args:
        request: FastAPI request object
        
    Returns:
        ProfileManager instance
    """
    return request.app.state.profile_manager


def validate_profile_exists(
    profile_name: str,
    profile_manager: ProfileManager = Depends(get_profile_manager)
) -> str:
    """
    Validate that a profile exists.
    
    Args:
        profile_name: Name of the profile to validate
        profile_manager: ProfileManager instance
        
    Returns:
        Validated profile name
        
    Raises:
        HTTPException: If profile doesn't exist
    """
    try:
        available_profiles = profile_manager.list_profiles()
        if profile_name not in available_profiles:
            raise HTTPException(
                status_code=404,
                detail=f"Profile '{profile_name}' not found. Available profiles: {available_profiles}"
            )
        return profile_name
    except Exception as e:
        logger.error(f"Error validating profile '{profile_name}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error validating profile: {str(e)}"
        )


def get_validated_profile(
    profile_name: str,
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """
    Get a validated profile instance.
    
    Args:
        profile_name: Name of the profile to load
        profile_manager: ProfileManager instance
        
    Returns:
        RedactionProfile instance
        
    Raises:
        HTTPException: If profile doesn't exist or is invalid
    """
    try:
        profile = profile_manager.load_profile(profile_name)
        return profile
    except FileNotFoundError:
        available_profiles = profile_manager.list_profiles()
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{profile_name}' not found. Available profiles: {available_profiles}"
        )
    except Exception as e:
        logger.error(f"Error loading profile '{profile_name}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error loading profile: {str(e)}"
        )


def check_system_health(
    processor: DocumentProcessor = Depends(get_document_processor)
) -> dict:
    """
    Check system health status.
    
    Args:
        processor: DocumentProcessor instance
        
    Returns:
        Health status dictionary
    """
    try:
        return processor.health_check()
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'components': {},
            'supported_formats': [],
            'statistics': {}
        }


def get_job_manager():
    """
    Get job manager instance.
    
    Returns:
        JobManager instance
    """
    return job_manager