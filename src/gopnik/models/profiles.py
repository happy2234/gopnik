"""
Redaction profile and style data models.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import yaml
import json
from pathlib import Path


class RedactionStyle(Enum):
    """Redaction style options."""
    SOLID_BLACK = "solid_black"
    SOLID_WHITE = "solid_white"
    PIXELATED = "pixelated"
    BLURRED = "blurred"
    PATTERN = "pattern"


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
    """
    name: str
    description: str
    visual_rules: Dict[str, bool] = field(default_factory=dict)
    text_rules: Dict[str, bool] = field(default_factory=dict)
    redaction_style: RedactionStyle = RedactionStyle.SOLID_BLACK
    multilingual_support: List[str] = field(default_factory=list)
    confidence_threshold: float = 0.7
    custom_rules: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate profile configuration."""
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError(f"Confidence threshold must be between 0.0 and 1.0, got {self.confidence_threshold}")
        
        if not self.name:
            raise ValueError("Profile name cannot be empty")
    
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
            custom_rules=data.get('custom_rules', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert profile to dictionary format.
        
        Returns:
            Dictionary representation of profile
        """
        return {
            'name': self.name,
            'description': self.description,
            'visual_rules': self.visual_rules,
            'text_rules': self.text_rules,
            'redaction_style': self.redaction_style.value,
            'multilingual_support': self.multilingual_support,
            'confidence_threshold': self.confidence_threshold,
            'custom_rules': self.custom_rules
        }
    
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