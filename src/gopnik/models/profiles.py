"""
Redaction profile and style data models.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import yaml
import json
from pathlib import Path
import copy
import logging

logger = logging.getLogger(__name__)


class RedactionStyle(Enum):
    """Redaction style options."""
    SOLID_BLACK = "solid_black"
    SOLID_WHITE = "solid_white"
    PIXELATED = "pixelated"
    BLURRED = "blurred"
    PATTERN = "pattern"


class ProfileValidationError(Exception):
    """Exception raised when profile validation fails."""
    pass


class ProfileConflictError(Exception):
    """Exception raised when profile conflicts cannot be resolved."""
    pass


@dataclass
class RedactionProfile:
    """
    Configuration profile for redaction operations.
    
    Attributes:
        name: Profile name
        description: Profile description
        visual_rules: Rules for visual PII types
        text_rules: Rules for text PII types
        redaction_style: Style to use for redactions
        multilingual_support: List of supported languages
        confidence_threshold: Minimum confidence for redaction
        custom_rules: Additional custom redaction rules
        inherits_from: List of parent profile names for inheritance
        version: Profile version for compatibility
        metadata: Additional metadata for the profile
    """
    name: str
    description: str
    visual_rules: Dict[str, bool] = field(default_factory=dict)
    text_rules: Dict[str, bool] = field(default_factory=dict)
    redaction_style: RedactionStyle = RedactionStyle.SOLID_BLACK
    multilingual_support: List[str] = field(default_factory=list)
    confidence_threshold: float = 0.7
    custom_rules: Dict[str, Any] = field(default_factory=dict)
    inherits_from: List[str] = field(default_factory=list)
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate profile configuration."""
        self.validate()
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'RedactionProfile':
        """
        Load redaction profile from YAML file.
        
        Args:
            yaml_path: Path to YAML configuration file
            
        Returns:
            RedactionProfile instance
        """
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return cls._from_dict(data)
    
    @classmethod
    def from_json(cls, json_path: Path) -> 'RedactionProfile':
        """
        Load redaction profile from JSON file.
        
        Args:
            json_path: Path to JSON configuration file
            
        Returns:
            RedactionProfile instance
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls._from_dict(data)
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'RedactionProfile':
        """Create profile from dictionary data."""
        # Convert redaction_style string to enum
        style_str = data.get('redaction_style', 'solid_black')
        try:
            redaction_style = RedactionStyle(style_str)
        except ValueError:
            redaction_style = RedactionStyle.SOLID_BLACK
        
        return cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            visual_rules=data.get('visual_rules', {}),
            text_rules=data.get('text_rules', {}),
            redaction_style=redaction_style,
            multilingual_support=data.get('multilingual_support', []),
            confidence_threshold=data.get('confidence_threshold', 0.7),
            custom_rules=data.get('custom_rules', {}),
            inherits_from=data.get('inherits_from', []),
            version=data.get('version', '1.0'),
            metadata=data.get('metadata', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert profile to dictionary format.
        
        Returns:
            Dictionary representation of profile
        """
        result = {
            'name': self.name,
            'description': self.description,
            'visual_rules': self.visual_rules,
            'text_rules': self.text_rules,
            'redaction_style': self.redaction_style.value,
            'multilingual_support': self.multilingual_support,
            'confidence_threshold': self.confidence_threshold,
            'custom_rules': self.custom_rules,
            'version': self.version,
            'metadata': self.metadata
        }
        
        # Only include inherits_from if it's not empty
        if self.inherits_from:
            result['inherits_from'] = self.inherits_from
            
        return result
    
    def save_yaml(self, output_path: Path) -> None:
        """
        Save profile to YAML file.
        
        Args:
            output_path: Path where to save the YAML file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)
    
    def save_json(self, output_path: Path) -> None:
        """
        Save profile to JSON file.
        
        Args:
            output_path: Path where to save the JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def is_pii_type_enabled(self, pii_type: str) -> bool:
        """
        Check if a PII type is enabled for redaction.
        
        Args:
            pii_type: PII type to check
            
        Returns:
            True if type should be redacted
        """
        # Check visual rules first
        if pii_type in self.visual_rules:
            return self.visual_rules[pii_type]
        
        # Check text rules
        if pii_type in self.text_rules:
            return self.text_rules[pii_type]
        
        # Default to False if not specified
        return False
    
    def validate(self) -> None:
        """
        Validate profile configuration.
        
        Raises:
            ProfileValidationError: If validation fails
        """
        errors = []
        
        # Validate name
        if not self.name or not isinstance(self.name, str):
            errors.append("Profile name must be a non-empty string")
        
        # Validate confidence threshold
        if not isinstance(self.confidence_threshold, (int, float)):
            errors.append("Confidence threshold must be a number")
        elif not 0.0 <= self.confidence_threshold <= 1.0:
            errors.append(f"Confidence threshold must be between 0.0 and 1.0, got {self.confidence_threshold}")
        
        # Validate visual rules
        if not isinstance(self.visual_rules, dict):
            errors.append("Visual rules must be a dictionary")
        else:
            for key, value in self.visual_rules.items():
                if not isinstance(key, str):
                    errors.append(f"Visual rule key must be string, got {type(key).__name__}")
                if not isinstance(value, bool):
                    errors.append(f"Visual rule value for '{key}' must be boolean, got {type(value).__name__}")
        
        # Validate text rules
        if not isinstance(self.text_rules, dict):
            errors.append("Text rules must be a dictionary")
        else:
            for key, value in self.text_rules.items():
                if not isinstance(key, str):
                    errors.append(f"Text rule key must be string, got {type(key).__name__}")
                if not isinstance(value, bool):
                    errors.append(f"Text rule value for '{key}' must be boolean, got {type(value).__name__}")
        
        # Validate redaction style
        if not isinstance(self.redaction_style, RedactionStyle):
            errors.append(f"Redaction style must be RedactionStyle enum, got {type(self.redaction_style).__name__}")
        
        # Validate multilingual support
        if not isinstance(self.multilingual_support, list):
            errors.append("Multilingual support must be a list")
        else:
            for lang in self.multilingual_support:
                if not isinstance(lang, str):
                    errors.append(f"Language code must be string, got {type(lang).__name__}")
        
        # Validate inherits_from
        if not isinstance(self.inherits_from, list):
            errors.append("Inherits_from must be a list")
        else:
            for parent in self.inherits_from:
                if not isinstance(parent, str):
                    errors.append(f"Parent profile name must be string, got {type(parent).__name__}")
        
        # Validate version
        if not isinstance(self.version, str):
            errors.append("Version must be a string")
        
        # Check for circular inheritance
        if self.name in self.inherits_from:
            errors.append("Profile cannot inherit from itself")
        
        if errors:
            raise ProfileValidationError(f"Profile validation failed: {'; '.join(errors)}")
    
    def merge_with_parent(self, parent: 'RedactionProfile') -> 'RedactionProfile':
        """
        Merge this profile with a parent profile.
        
        Args:
            parent: Parent profile to inherit from
            
        Returns:
            New merged profile
        """
        # Create a deep copy of the parent
        merged_data = copy.deepcopy(parent.to_dict())
        
        # Override with current profile's values
        current_data = self.to_dict()
        
        # Merge visual rules (child overrides parent)
        merged_data['visual_rules'].update(current_data['visual_rules'])
        
        # Merge text rules (child overrides parent)
        merged_data['text_rules'].update(current_data['text_rules'])
        
        # Merge custom rules (child overrides parent)
        merged_data['custom_rules'].update(current_data['custom_rules'])
        
        # Merge multilingual support (combine both)
        parent_langs = set(merged_data['multilingual_support'])
        child_langs = set(current_data['multilingual_support'])
        merged_data['multilingual_support'] = list(parent_langs.union(child_langs))
        
        # Merge metadata (child overrides parent)
        merged_data['metadata'].update(current_data['metadata'])
        
        # Override scalar values with child values
        for key in ['name', 'description', 'redaction_style', 'confidence_threshold', 'version']:
            if key in current_data:
                merged_data[key] = current_data[key]
        
        # Clear inheritance chain for the merged profile
        merged_data['inherits_from'] = []
        
        return RedactionProfile._from_dict(merged_data)
    
    def detect_conflicts(self, other: 'RedactionProfile') -> List[str]:
        """
        Detect conflicts between this profile and another.
        
        Args:
            other: Other profile to compare with
            
        Returns:
            List of conflict descriptions
        """
        conflicts = []
        
        # Check visual rules conflicts
        for key in set(self.visual_rules.keys()).intersection(other.visual_rules.keys()):
            if self.visual_rules[key] != other.visual_rules[key]:
                conflicts.append(f"Visual rule '{key}': {self.visual_rules[key]} vs {other.visual_rules[key]}")
        
        # Check text rules conflicts
        for key in set(self.text_rules.keys()).intersection(other.text_rules.keys()):
            if self.text_rules[key] != other.text_rules[key]:
                conflicts.append(f"Text rule '{key}': {self.text_rules[key]} vs {other.text_rules[key]}")
        
        # Check redaction style conflict
        if self.redaction_style != other.redaction_style:
            conflicts.append(f"Redaction style: {self.redaction_style.value} vs {other.redaction_style.value}")
        
        # Check confidence threshold conflict (significant difference)
        if abs(self.confidence_threshold - other.confidence_threshold) > 0.1:
            conflicts.append(f"Confidence threshold: {self.confidence_threshold} vs {other.confidence_threshold}")
        
        return conflicts
    
    def resolve_conflicts(self, other: 'RedactionProfile', strategy: str = 'strict') -> 'RedactionProfile':
        """
        Resolve conflicts between profiles using specified strategy.
        
        Args:
            other: Other profile to merge with
            strategy: Conflict resolution strategy ('strict', 'permissive', 'conservative')
            
        Returns:
            New profile with conflicts resolved
            
        Raises:
            ProfileConflictError: If conflicts cannot be resolved
        """
        conflicts = self.detect_conflicts(other)
        
        if not conflicts:
            # No conflicts, simple merge
            return self._merge_profiles(other)
        
        if strategy == 'strict':
            raise ProfileConflictError(f"Cannot resolve conflicts in strict mode: {'; '.join(conflicts)}")
        
        # Create merged profile based on strategy
        merged_data = copy.deepcopy(self.to_dict())
        other_data = other.to_dict()
        
        if strategy == 'permissive':
            # Enable all PII types from both profiles
            for key, value in other_data['visual_rules'].items():
                merged_data['visual_rules'][key] = merged_data['visual_rules'].get(key, False) or value
            
            for key, value in other_data['text_rules'].items():
                merged_data['text_rules'][key] = merged_data['text_rules'].get(key, False) or value
            
            # Use lower confidence threshold
            merged_data['confidence_threshold'] = min(
                merged_data['confidence_threshold'], 
                other_data['confidence_threshold']
            )
            
        elif strategy == 'conservative':
            # Only enable PII types that are enabled in both profiles
            for key in list(merged_data['visual_rules'].keys()):
                if key in other_data['visual_rules']:
                    merged_data['visual_rules'][key] = (
                        merged_data['visual_rules'][key] and other_data['visual_rules'][key]
                    )
            
            for key in list(merged_data['text_rules'].keys()):
                if key in other_data['text_rules']:
                    merged_data['text_rules'][key] = (
                        merged_data['text_rules'][key] and other_data['text_rules'][key]
                    )
            
            # Use higher confidence threshold
            merged_data['confidence_threshold'] = max(
                merged_data['confidence_threshold'], 
                other_data['confidence_threshold']
            )
        
        # Merge other non-conflicting attributes
        merged_data['multilingual_support'] = list(
            set(merged_data['multilingual_support']).union(set(other_data['multilingual_support']))
        )
        merged_data['custom_rules'].update(other_data['custom_rules'])
        merged_data['metadata'].update(other_data['metadata'])
        
        # Update name and description to reflect merge
        merged_data['name'] = f"{self.name}_merged_{other.name}"
        merged_data['description'] = f"Merged profile: {self.description} + {other.description}"
        
        return RedactionProfile._from_dict(merged_data)
    
    def _merge_profiles(self, other: 'RedactionProfile') -> 'RedactionProfile':
        """Simple merge without conflict resolution."""
        merged_data = copy.deepcopy(self.to_dict())
        other_data = other.to_dict()
        
        # Merge rules (other overrides self)
        merged_data['visual_rules'].update(other_data['visual_rules'])
        merged_data['text_rules'].update(other_data['text_rules'])
        merged_data['custom_rules'].update(other_data['custom_rules'])
        merged_data['metadata'].update(other_data['metadata'])
        
        # Combine multilingual support
        merged_data['multilingual_support'] = list(
            set(merged_data['multilingual_support']).union(set(other_data['multilingual_support']))
        )
        
        # Use other's scalar values
        for key in ['redaction_style', 'confidence_threshold']:
            merged_data[key] = other_data[key]
        
        merged_data['name'] = f"{self.name}_merged_{other.name}"
        merged_data['description'] = f"Merged profile: {self.description} + {other.description}"
        
        return RedactionProfile._from_dict(merged_data)


class ProfileManager:
    """
    Manager for redaction profiles with support for inheritance and composition.
    """
    
    def __init__(self, profile_directories: Optional[List[Path]] = None):
        """
        Initialize profile manager.
        
        Args:
            profile_directories: List of directories to search for profiles
        """
        self.profile_directories = profile_directories or [Path("profiles")]
        self._profile_cache: Dict[str, RedactionProfile] = {}
        self._inheritance_graph: Dict[str, List[str]] = {}
    
    def load_profile(self, name: str, resolve_inheritance: bool = True) -> RedactionProfile:
        """
        Load a profile by name with optional inheritance resolution.
        
        Args:
            name: Profile name to load
            resolve_inheritance: Whether to resolve inheritance chain
            
        Returns:
            Loaded and optionally resolved profile
            
        Raises:
            FileNotFoundError: If profile file not found
            ProfileValidationError: If profile validation fails
        """
        # Check cache first
        cache_key = f"{name}{'_resolved' if resolve_inheritance else '_raw'}"
        if cache_key in self._profile_cache:
            return self._profile_cache[cache_key]
        
        # Find and load profile file
        profile_path = self._find_profile_file(name)
        if not profile_path:
            raise FileNotFoundError(f"Profile '{name}' not found in directories: {self.profile_directories}")
        
        # Load profile based on file extension
        if profile_path.suffix.lower() == '.yaml' or profile_path.suffix.lower() == '.yml':
            profile = RedactionProfile.from_yaml(profile_path)
        elif profile_path.suffix.lower() == '.json':
            profile = RedactionProfile.from_json(profile_path)
        else:
            raise ValueError(f"Unsupported profile file format: {profile_path.suffix}")
        
        # Cache raw profile
        raw_cache_key = f"{name}_raw"
        self._profile_cache[raw_cache_key] = profile
        
        if resolve_inheritance and profile.inherits_from:
            profile = self._resolve_inheritance(profile)
        
        # Cache resolved profile
        self._profile_cache[cache_key] = profile
        return profile
    
    def _find_profile_file(self, name: str) -> Optional[Path]:
        """Find profile file in configured directories."""
        for directory in self.profile_directories:
            for extension in ['.yaml', '.yml', '.json']:
                profile_path = directory / f"{name}{extension}"
                if profile_path.exists():
                    return profile_path
        return None
    
    def _resolve_inheritance(self, profile: RedactionProfile) -> RedactionProfile:
        """
        Resolve inheritance chain for a profile.
        
        Args:
            profile: Profile to resolve inheritance for
            
        Returns:
            Profile with inheritance resolved
            
        Raises:
            ProfileValidationError: If circular inheritance detected
        """
        if not profile.inherits_from:
            return profile
        
        # Check for circular inheritance
        visited = set()
        self._check_circular_inheritance(profile.name, profile.inherits_from, visited)
        
        # Load and merge parent profiles
        resolved_profile = profile
        for parent_name in profile.inherits_from:
            parent_profile = self.load_profile(parent_name, resolve_inheritance=True)
            resolved_profile = resolved_profile.merge_with_parent(parent_profile)
        
        return resolved_profile
    
    def _check_circular_inheritance(self, current: str, parents: List[str], visited: set):
        """Check for circular inheritance in the profile chain."""
        if current in visited:
            raise ProfileValidationError(f"Circular inheritance detected involving profile '{current}'")
        
        visited.add(current)
        
        for parent_name in parents:
            try:
                parent_profile = self.load_profile(parent_name, resolve_inheritance=False)
                if parent_profile.inherits_from:
                    self._check_circular_inheritance(parent_name, parent_profile.inherits_from, visited.copy())
            except FileNotFoundError:
                logger.warning(f"Parent profile '{parent_name}' not found for '{current}'")
    
    def list_profiles(self) -> List[str]:
        """
        List all available profiles.
        
        Returns:
            List of profile names
        """
        profiles = set()
        
        for directory in self.profile_directories:
            if not directory.exists():
                continue
                
            for file_path in directory.iterdir():
                if file_path.suffix.lower() in ['.yaml', '.yml', '.json']:
                    profiles.add(file_path.stem)
        
        return sorted(list(profiles))
    
    def validate_profile(self, profile: Union[RedactionProfile, str]) -> List[str]:
        """
        Validate a profile and return any validation errors.
        
        Args:
            profile: Profile instance or name to validate
            
        Returns:
            List of validation error messages
        """
        if isinstance(profile, str):
            try:
                profile = self.load_profile(profile, resolve_inheritance=False)
            except Exception as e:
                return [f"Failed to load profile: {str(e)}"]
        
        try:
            profile.validate()
            return []
        except ProfileValidationError as e:
            return [str(e)]
    
    def create_composite_profile(
        self, 
        profiles: List[Union[str, RedactionProfile]], 
        name: str,
        conflict_strategy: str = 'permissive'
    ) -> RedactionProfile:
        """
        Create a composite profile from multiple profiles.
        
        Args:
            profiles: List of profile names or instances to compose
            name: Name for the composite profile
            conflict_strategy: Strategy for resolving conflicts
            
        Returns:
            Composite profile
            
        Raises:
            ProfileConflictError: If conflicts cannot be resolved
        """
        if not profiles:
            raise ValueError("At least one profile must be provided")
        
        # Load profiles if needed
        loaded_profiles = []
        for profile in profiles:
            if isinstance(profile, str):
                loaded_profiles.append(self.load_profile(profile))
            else:
                loaded_profiles.append(profile)
        
        # Start with first profile
        composite = loaded_profiles[0]
        
        # Merge with remaining profiles
        for other_profile in loaded_profiles[1:]:
            composite = composite.resolve_conflicts(other_profile, conflict_strategy)
        
        # Update name and description
        composite.name = name
        composite.description = f"Composite profile from: {', '.join([p.name for p in loaded_profiles])}"
        
        return composite
    
    def save_profile(self, profile: RedactionProfile, directory: Optional[Path] = None, format: str = 'yaml') -> Path:
        """
        Save a profile to disk.
        
        Args:
            profile: Profile to save
            directory: Directory to save in (uses first configured directory if None)
            format: File format ('yaml' or 'json')
            
        Returns:
            Path where profile was saved
        """
        if directory is None:
            directory = self.profile_directories[0]
        
        directory.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'yaml':
            file_path = directory / f"{profile.name}.yaml"
            profile.save_yaml(file_path)
        elif format.lower() == 'json':
            file_path = directory / f"{profile.name}.json"
            profile.save_json(file_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Clear cache for this profile
        cache_keys = [k for k in self._profile_cache.keys() if k.startswith(profile.name)]
        for key in cache_keys:
            del self._profile_cache[key]
        
        return file_path
    
    def clear_cache(self):
        """Clear the profile cache."""
        self._profile_cache.clear()