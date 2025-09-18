"""
Profile management endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
import logging

from ....models.profiles import ProfileManager, RedactionProfile, ProfileValidationError
from ..models import (
    ProfileResponse, ProfileCreateRequest, ProfileUpdateRequest, ErrorResponse
)
from ..dependencies import get_profile_manager


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/profiles", response_model=List[ProfileResponse])
async def list_profiles(
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """
    List all available redaction profiles.
    
    Returns:
        List of available profiles with their configurations
    """
    try:
        profile_names = profile_manager.list_profiles()
        profiles = []
        
        for name in profile_names:
            try:
                profile = profile_manager.load_profile(name)
                profiles.append(_profile_to_response(profile))
            except Exception as e:
                logger.warning(f"Failed to load profile '{name}': {str(e)}")
                continue
        
        logger.info(f"Listed {len(profiles)} profiles")
        return profiles
        
    except Exception as e:
        logger.error(f"Failed to list profiles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list profiles: {str(e)}"
        )


@router.get("/profiles/{profile_name}", response_model=ProfileResponse)
async def get_profile(
    profile_name: str,
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """
    Get a specific redaction profile by name.
    
    Args:
        profile_name: Name of the profile to retrieve
        
    Returns:
        Profile configuration details
    """
    try:
        profile = profile_manager.load_profile(profile_name)
        logger.info(f"Retrieved profile '{profile_name}'")
        return _profile_to_response(profile)
        
    except FileNotFoundError:
        available_profiles = profile_manager.list_profiles()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_name}' not found. Available profiles: {available_profiles}"
        )
    except Exception as e:
        logger.error(f"Failed to get profile '{profile_name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}"
        )


@router.post("/profiles", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_request: ProfileCreateRequest,
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """
    Create a new redaction profile.
    
    Args:
        profile_request: Profile configuration to create
        
    Returns:
        Created profile details
    """
    try:
        # Check if profile already exists
        existing_profiles = profile_manager.list_profiles()
        if profile_request.name in existing_profiles:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Profile '{profile_request.name}' already exists"
            )
        
        # Create profile from request
        profile = _request_to_profile(profile_request)
        
        # Validate profile
        validation_errors = profile_manager.validate_profile(profile)
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Profile validation failed: {'; '.join(validation_errors)}"
            )
        
        # Save profile
        profile_manager.save_profile(profile)
        
        logger.info(f"Created profile '{profile_request.name}'")
        return _profile_to_response(profile)
        
    except HTTPException:
        raise
    except ProfileValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to create profile '{profile_request.name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(e)}"
        )


@router.put("/profiles/{profile_name}", response_model=ProfileResponse)
async def update_profile(
    profile_name: str,
    profile_request: ProfileUpdateRequest,
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """
    Update an existing redaction profile.
    
    Args:
        profile_name: Name of the profile to update
        profile_request: Profile updates to apply
        
    Returns:
        Updated profile details
    """
    try:
        # Load existing profile
        try:
            existing_profile = profile_manager.load_profile(profile_name)
        except FileNotFoundError:
            available_profiles = profile_manager.list_profiles()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_name}' not found. Available profiles: {available_profiles}"
            )
        
        # Apply updates
        updated_profile = _apply_profile_updates(existing_profile, profile_request)
        
        # Validate updated profile
        validation_errors = profile_manager.validate_profile(updated_profile)
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Profile validation failed: {'; '.join(validation_errors)}"
            )
        
        # Save updated profile
        profile_manager.save_profile(updated_profile)
        
        logger.info(f"Updated profile '{profile_name}'")
        return _profile_to_response(updated_profile)
        
    except HTTPException:
        raise
    except ProfileValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to update profile '{profile_name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.delete("/profiles/{profile_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_name: str,
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """
    Delete a redaction profile.
    
    Args:
        profile_name: Name of the profile to delete
    """
    try:
        # Check if profile exists
        existing_profiles = profile_manager.list_profiles()
        if profile_name not in existing_profiles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_name}' not found. Available profiles: {existing_profiles}"
            )
        
        # Prevent deletion of default profile
        if profile_name == "default":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the default profile"
            )
        
        # Find and delete profile file
        for directory in profile_manager.profile_directories:
            for extension in ['.yaml', '.yml', '.json']:
                profile_path = directory / f"{profile_name}{extension}"
                if profile_path.exists():
                    profile_path.unlink()
                    logger.info(f"Deleted profile '{profile_name}' from {profile_path}")
                    
                    # Clear cache
                    profile_manager.clear_cache()
                    return
        
        # If we get here, profile was listed but file not found
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile '{profile_name}' file not found for deletion"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile '{profile_name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}"
        )


# Helper functions

def _profile_to_response(profile: RedactionProfile) -> ProfileResponse:
    """Convert RedactionProfile to API response model."""
    return ProfileResponse(
        name=profile.name,
        description=profile.description,
        visual_rules=profile.visual_rules,
        text_rules=profile.text_rules,
        redaction_style=profile.redaction_style.value,
        confidence_threshold=profile.confidence_threshold,
        multilingual_support=profile.multilingual_support,
        version=profile.version
    )


def _request_to_profile(request: ProfileCreateRequest) -> RedactionProfile:
    """Convert API request to RedactionProfile."""
    from ....models.profiles import RedactionStyle
    
    # Convert redaction style string to enum
    redaction_style = RedactionStyle(request.redaction_style)
    
    return RedactionProfile(
        name=request.name,
        description=request.description,
        visual_rules=request.visual_rules,
        text_rules=request.text_rules,
        redaction_style=redaction_style,
        confidence_threshold=request.confidence_threshold,
        multilingual_support=request.multilingual_support
    )


def _apply_profile_updates(
    existing_profile: RedactionProfile, 
    updates: ProfileUpdateRequest
) -> RedactionProfile:
    """Apply updates to an existing profile."""
    from ....models.profiles import RedactionStyle
    
    # Create updated profile data
    updated_data = existing_profile.to_dict()
    
    # Apply non-None updates
    if updates.description is not None:
        updated_data['description'] = updates.description
    
    if updates.visual_rules is not None:
        updated_data['visual_rules'] = updates.visual_rules
    
    if updates.text_rules is not None:
        updated_data['text_rules'] = updates.text_rules
    
    if updates.redaction_style is not None:
        updated_data['redaction_style'] = updates.redaction_style
    
    if updates.confidence_threshold is not None:
        updated_data['confidence_threshold'] = updates.confidence_threshold
    
    if updates.multilingual_support is not None:
        updated_data['multilingual_support'] = updates.multilingual_support
    
    # Create new profile from updated data
    return RedactionProfile._from_dict(updated_data)