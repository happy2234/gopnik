"""
Unit tests for redaction profile models and parsing.
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from src.gopnik.models.profiles import (
    RedactionProfile, 
    RedactionStyle, 
    ProfileManager,
    ProfileValidationError,
    ProfileConflictError
)


class TestRedactionProfile:
    """Test cases for RedactionProfile class."""
    
    def test_profile_creation_with_defaults(self):
        """Test creating a profile with default values."""
        profile = RedactionProfile(
            name="test_profile",
            description="Test profile"
        )
        
        assert profile.name == "test_profile"
        assert profile.description == "Test profile"
        assert profile.visual_rules == {}
        assert profile.text_rules == {}
        assert profile.redaction_style == RedactionStyle.SOLID_BLACK
        assert profile.multilingual_support == []
        assert profile.confidence_threshold == 0.7
        assert profile.custom_rules == {}
        assert profile.inherits_from == []
        assert profile.version == "1.0"
        assert profile.metadata == {}
    
    def test_profile_creation_with_custom_values(self):
        """Test creating a profile with custom values."""
        profile = RedactionProfile(
            name="custom_profile",
            description="Custom test profile",
            visual_rules={"face": True, "signature": False},
            text_rules={"email": True, "phone": False},
            redaction_style=RedactionStyle.BLURRED,
            multilingual_support=["en", "es"],
            confidence_threshold=0.8,
            custom_rules={"medical_id": True},
            inherits_from=["base_profile"],
            version="2.0",
            metadata={"author": "test"}
        )
        
        assert profile.name == "custom_profile"
        assert profile.visual_rules == {"face": True, "signature": False}
        assert profile.text_rules == {"email": True, "phone": False}
        assert profile.redaction_style == RedactionStyle.BLURRED
        assert profile.multilingual_support == ["en", "es"]
        assert profile.confidence_threshold == 0.8
        assert profile.custom_rules == {"medical_id": True}
        assert profile.inherits_from == ["base_profile"]
        assert profile.version == "2.0"
        assert profile.metadata == {"author": "test"}
    
    def test_profile_validation_success(self):
        """Test successful profile validation."""
        profile = RedactionProfile(
            name="valid_profile",
            description="Valid profile",
            visual_rules={"face": True},
            text_rules={"email": False},
            confidence_threshold=0.5
        )
        
        # Should not raise any exception
        profile.validate()
    
    def test_profile_validation_empty_name(self):
        """Test validation failure with empty name."""
        with pytest.raises(ProfileValidationError) as exc_info:
            RedactionProfile(name="", description="Test")
        
        assert "Profile name must be a non-empty string" in str(exc_info.value)
    
    def test_profile_validation_invalid_confidence_threshold(self):
        """Test validation failure with invalid confidence threshold."""
        with pytest.raises(ProfileValidationError) as exc_info:
            RedactionProfile(
                name="test",
                description="Test",
                confidence_threshold=1.5
            )
        
        assert "Confidence threshold must be between 0.0 and 1.0" in str(exc_info.value)
    
    def test_profile_validation_invalid_rules(self):
        """Test validation failure with invalid rules."""
        with pytest.raises(ProfileValidationError) as exc_info:
            RedactionProfile(
                name="test",
                description="Test",
                visual_rules={"face": "yes"}  # Should be boolean
            )
        
        assert "Visual rule value for 'face' must be boolean" in str(exc_info.value)
    
    def test_profile_validation_circular_inheritance(self):
        """Test validation failure with circular inheritance."""
        with pytest.raises(ProfileValidationError) as exc_info:
            RedactionProfile(
                name="test",
                description="Test",
                inherits_from=["test"]  # Circular reference
            )
        
        assert "Profile cannot inherit from itself" in str(exc_info.value)
    
    def test_is_pii_type_enabled(self):
        """Test PII type checking."""
        profile = RedactionProfile(
            name="test",
            description="Test",
            visual_rules={"face": True, "signature": False},
            text_rules={"email": True, "phone": False}
        )
        
        assert profile.is_pii_type_enabled("face") is True
        assert profile.is_pii_type_enabled("signature") is False
        assert profile.is_pii_type_enabled("email") is True
        assert profile.is_pii_type_enabled("phone") is False
        assert profile.is_pii_type_enabled("unknown") is False
    
    def test_to_dict(self):
        """Test converting profile to dictionary."""
        profile = RedactionProfile(
            name="test",
            description="Test profile",
            visual_rules={"face": True},
            text_rules={"email": False},
            redaction_style=RedactionStyle.PIXELATED,
            confidence_threshold=0.8,
            inherits_from=["parent"],
            version="1.5",
            metadata={"key": "value"}
        )
        
        result = profile.to_dict()
        
        assert result["name"] == "test"
        assert result["description"] == "Test profile"
        assert result["visual_rules"] == {"face": True}
        assert result["text_rules"] == {"email": False}
        assert result["redaction_style"] == "pixelated"
        assert result["confidence_threshold"] == 0.8
        assert result["inherits_from"] == ["parent"]
        assert result["version"] == "1.5"
        assert result["metadata"] == {"key": "value"}
    
    def test_to_dict_no_inheritance(self):
        """Test to_dict excludes empty inherits_from."""
        profile = RedactionProfile(name="test", description="Test")
        result = profile.to_dict()
        
        assert "inherits_from" not in result
    
    def test_from_dict(self):
        """Test creating profile from dictionary."""
        data = {
            "name": "test",
            "description": "Test profile",
            "visual_rules": {"face": True},
            "text_rules": {"email": False},
            "redaction_style": "blurred",
            "confidence_threshold": 0.9,
            "inherits_from": ["parent"],
            "version": "2.0",
            "metadata": {"author": "test"}
        }
        
        profile = RedactionProfile._from_dict(data)
        
        assert profile.name == "test"
        assert profile.description == "Test profile"
        assert profile.visual_rules == {"face": True}
        assert profile.text_rules == {"email": False}
        assert profile.redaction_style == RedactionStyle.BLURRED
        assert profile.confidence_threshold == 0.9
        assert profile.inherits_from == ["parent"]
        assert profile.version == "2.0"
        assert profile.metadata == {"author": "test"}
    
    def test_from_dict_invalid_redaction_style(self):
        """Test from_dict with invalid redaction style falls back to default."""
        data = {
            "name": "test",
            "description": "Test",
            "redaction_style": "invalid_style"
        }
        
        profile = RedactionProfile._from_dict(data)
        assert profile.redaction_style == RedactionStyle.SOLID_BLACK
    
    def test_yaml_serialization(self):
        """Test YAML serialization and deserialization."""
        profile = RedactionProfile(
            name="yaml_test",
            description="YAML test profile",
            visual_rules={"face": True, "signature": False},
            text_rules={"email": True},
            redaction_style=RedactionStyle.PATTERN,
            confidence_threshold=0.85
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            profile.save_yaml(Path(f.name))
            yaml_path = Path(f.name)
        
        try:
            loaded_profile = RedactionProfile.from_yaml(yaml_path)
            
            assert loaded_profile.name == profile.name
            assert loaded_profile.description == profile.description
            assert loaded_profile.visual_rules == profile.visual_rules
            assert loaded_profile.text_rules == profile.text_rules
            assert loaded_profile.redaction_style == profile.redaction_style
            assert loaded_profile.confidence_threshold == profile.confidence_threshold
        finally:
            yaml_path.unlink()
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        profile = RedactionProfile(
            name="json_test",
            description="JSON test profile",
            visual_rules={"face": False, "barcode": True},
            text_rules={"phone": True},
            redaction_style=RedactionStyle.SOLID_WHITE,
            confidence_threshold=0.6
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            profile.save_json(Path(f.name))
            json_path = Path(f.name)
        
        try:
            loaded_profile = RedactionProfile.from_json(json_path)
            
            assert loaded_profile.name == profile.name
            assert loaded_profile.description == profile.description
            assert loaded_profile.visual_rules == profile.visual_rules
            assert loaded_profile.text_rules == profile.text_rules
            assert loaded_profile.redaction_style == profile.redaction_style
            assert loaded_profile.confidence_threshold == profile.confidence_threshold
        finally:
            json_path.unlink()
    
    def test_merge_with_parent(self):
        """Test merging profile with parent."""
        parent = RedactionProfile(
            name="parent",
            description="Parent profile",
            visual_rules={"face": True, "signature": False},
            text_rules={"email": True, "phone": False},
            multilingual_support=["en", "es"],
            confidence_threshold=0.7,
            custom_rules={"parent_rule": True},
            metadata={"parent_key": "parent_value"}
        )
        
        child = RedactionProfile(
            name="child",
            description="Child profile",
            visual_rules={"signature": True, "barcode": True},  # Override signature
            text_rules={"phone": True, "address": True},  # Override phone, add address
            multilingual_support=["fr"],  # Additional language
            confidence_threshold=0.8,  # Override threshold
            custom_rules={"child_rule": True},  # Additional rule
            metadata={"child_key": "child_value"}  # Additional metadata
        )
        
        merged = child.merge_with_parent(parent)
        
        # Check merged visual rules
        assert merged.visual_rules["face"] is True  # From parent
        assert merged.visual_rules["signature"] is True  # Overridden by child
        assert merged.visual_rules["barcode"] is True  # From child
        
        # Check merged text rules
        assert merged.text_rules["email"] is True  # From parent
        assert merged.text_rules["phone"] is True  # Overridden by child
        assert merged.text_rules["address"] is True  # From child
        
        # Check merged multilingual support
        assert set(merged.multilingual_support) == {"en", "es", "fr"}
        
        # Check overridden values
        assert merged.confidence_threshold == 0.8  # Child value
        assert merged.name == "child"  # Child value
        assert merged.description == "Child profile"  # Child value
        
        # Check merged custom rules and metadata
        assert merged.custom_rules["parent_rule"] is True
        assert merged.custom_rules["child_rule"] is True
        assert merged.metadata["parent_key"] == "parent_value"
        assert merged.metadata["child_key"] == "child_value"
        
        # Check inheritance is cleared
        assert merged.inherits_from == []
    
    def test_detect_conflicts(self):
        """Test conflict detection between profiles."""
        profile1 = RedactionProfile(
            name="profile1",
            description="Profile 1",
            visual_rules={"face": True, "signature": False},
            text_rules={"email": True, "phone": False},
            redaction_style=RedactionStyle.SOLID_BLACK,
            confidence_threshold=0.7
        )
        
        profile2 = RedactionProfile(
            name="profile2",
            description="Profile 2",
            visual_rules={"face": False, "barcode": True},  # face conflicts
            text_rules={"email": True, "phone": True},  # phone conflicts
            redaction_style=RedactionStyle.BLURRED,  # style conflicts
            confidence_threshold=0.9  # threshold conflicts (significant difference)
        )
        
        conflicts = profile1.detect_conflicts(profile2)
        
        assert len(conflicts) == 4
        assert any("Visual rule 'face'" in conflict for conflict in conflicts)
        assert any("Text rule 'phone'" in conflict for conflict in conflicts)
        assert any("Redaction style" in conflict for conflict in conflicts)
        assert any("Confidence threshold" in conflict for conflict in conflicts)
    
    def test_detect_no_conflicts(self):
        """Test no conflicts detected when profiles are compatible."""
        profile1 = RedactionProfile(
            name="profile1",
            description="Profile 1",
            visual_rules={"face": True},
            text_rules={"email": True},
            confidence_threshold=0.7
        )
        
        profile2 = RedactionProfile(
            name="profile2",
            description="Profile 2",
            visual_rules={"signature": True},  # Different keys
            text_rules={"phone": True},  # Different keys
            confidence_threshold=0.75  # Small difference
        )
        
        conflicts = profile1.detect_conflicts(profile2)
        assert len(conflicts) == 0
    
    def test_resolve_conflicts_strict_mode_fails(self):
        """Test strict conflict resolution fails with conflicts."""
        profile1 = RedactionProfile(
            name="profile1",
            description="Profile 1",
            visual_rules={"face": True}
        )
        
        profile2 = RedactionProfile(
            name="profile2",
            description="Profile 2",
            visual_rules={"face": False}  # Conflict
        )
        
        with pytest.raises(ProfileConflictError) as exc_info:
            profile1.resolve_conflicts(profile2, strategy='strict')
        
        assert "Cannot resolve conflicts in strict mode" in str(exc_info.value)
    
    def test_resolve_conflicts_permissive_mode(self):
        """Test permissive conflict resolution."""
        profile1 = RedactionProfile(
            name="profile1",
            description="Profile 1",
            visual_rules={"face": True, "signature": False},
            text_rules={"email": True, "phone": False},
            confidence_threshold=0.8
        )
        
        profile2 = RedactionProfile(
            name="profile2",
            description="Profile 2",
            visual_rules={"face": False, "signature": True},
            text_rules={"email": False, "phone": True},
            confidence_threshold=0.6
        )
        
        merged = profile1.resolve_conflicts(profile2, strategy='permissive')
        
        # In permissive mode, all PII types should be enabled
        assert merged.visual_rules["face"] is True  # True OR False = True
        assert merged.visual_rules["signature"] is True  # False OR True = True
        assert merged.text_rules["email"] is True  # True OR False = True
        assert merged.text_rules["phone"] is True  # False OR True = True
        
        # Should use lower confidence threshold
        assert merged.confidence_threshold == 0.6
        
        # Name should reflect merge
        assert "merged" in merged.name
    
    def test_resolve_conflicts_conservative_mode(self):
        """Test conservative conflict resolution."""
        profile1 = RedactionProfile(
            name="profile1",
            description="Profile 1",
            visual_rules={"face": True, "signature": False},
            text_rules={"email": True, "phone": False},
            confidence_threshold=0.6
        )
        
        profile2 = RedactionProfile(
            name="profile2",
            description="Profile 2",
            visual_rules={"face": False, "signature": True},
            text_rules={"email": False, "phone": True},
            confidence_threshold=0.8
        )
        
        merged = profile1.resolve_conflicts(profile2, strategy='conservative')
        
        # In conservative mode, only common enabled types should remain
        assert merged.visual_rules["face"] is False  # True AND False = False
        assert merged.visual_rules["signature"] is False  # False AND True = False
        assert merged.text_rules["email"] is False  # True AND False = False
        assert merged.text_rules["phone"] is False  # False AND True = False
        
        # Should use higher confidence threshold
        assert merged.confidence_threshold == 0.8


class TestProfileManager:
    """Test cases for ProfileManager class."""
    
    def test_profile_manager_initialization(self):
        """Test ProfileManager initialization."""
        manager = ProfileManager()
        assert manager.profile_directories == [Path("profiles")]
        
        custom_dirs = [Path("custom1"), Path("custom2")]
        manager = ProfileManager(custom_dirs)
        assert manager.profile_directories == custom_dirs
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_profile_yaml(self, mock_file, mock_exists):
        """Test loading profile from YAML file."""
        mock_exists.return_value = True
        
        yaml_content = """
name: test_profile
description: Test profile
visual_rules:
  face: true
text_rules:
  email: false
confidence_threshold: 0.8
"""
        mock_file.return_value.read.return_value = yaml_content
        
        with patch('yaml.safe_load') as mock_yaml_load:
            mock_yaml_load.return_value = {
                'name': 'test_profile',
                'description': 'Test profile',
                'visual_rules': {'face': True},
                'text_rules': {'email': False},
                'confidence_threshold': 0.8
            }
            
            manager = ProfileManager([Path("test_profiles")])
            profile = manager.load_profile("test_profile")
            
            assert profile.name == "test_profile"
            assert profile.visual_rules == {"face": True}
            assert profile.text_rules == {"email": False}
            assert profile.confidence_threshold == 0.8
    
    def test_load_profile_not_found(self):
        """Test loading non-existent profile."""
        manager = ProfileManager([Path("nonexistent")])
        
        with pytest.raises(FileNotFoundError) as exc_info:
            manager.load_profile("nonexistent_profile")
        
        assert "Profile 'nonexistent_profile' not found" in str(exc_info.value)
    
    def test_load_profile_unsupported_format(self):
        """Test loading profile with unsupported format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            profile_path = temp_path / "test.txt"
            profile_path.write_text("invalid format")
            
            manager = ProfileManager([temp_path])
            
            # The manager should find the .txt file but reject it due to unsupported format
            # We need to patch _find_profile_file to return the .txt file
            with patch.object(manager, '_find_profile_file', return_value=profile_path):
                with pytest.raises(ValueError) as exc_info:
                    manager.load_profile("test")
                
                assert "Unsupported profile file format" in str(exc_info.value)
    
    def test_profile_caching(self):
        """Test profile caching functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test profile
            profile_data = {
                'name': 'cached_profile',
                'description': 'Cached test profile',
                'visual_rules': {'face': True}
            }
            
            profile_path = temp_path / "cached_profile.yaml"
            with open(profile_path, 'w') as f:
                yaml.dump(profile_data, f)
            
            manager = ProfileManager([temp_path])
            
            # Load profile twice
            profile1 = manager.load_profile("cached_profile")
            profile2 = manager.load_profile("cached_profile")
            
            # Should be the same object (cached)
            assert profile1 is profile2
    
    def test_list_profiles(self):
        """Test listing available profiles."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test profile files
            (temp_path / "profile1.yaml").touch()
            (temp_path / "profile2.json").touch()
            (temp_path / "profile3.yml").touch()
            (temp_path / "not_profile.txt").touch()  # Should be ignored
            
            manager = ProfileManager([temp_path])
            profiles = manager.list_profiles()
            
            assert sorted(profiles) == ["profile1", "profile2", "profile3"]
    
    def test_validate_profile_success(self):
        """Test successful profile validation."""
        profile = RedactionProfile(
            name="valid_profile",
            description="Valid profile"
        )
        
        manager = ProfileManager()
        errors = manager.validate_profile(profile)
        
        assert errors == []
    
    def test_validate_profile_failure(self):
        """Test profile validation failure."""
        # Create a profile with invalid data by bypassing validation
        profile = object.__new__(RedactionProfile)
        profile.name = ""  # Invalid empty name
        profile.description = "Invalid profile"
        profile.visual_rules = {}
        profile.text_rules = {}
        profile.redaction_style = RedactionStyle.SOLID_BLACK
        profile.multilingual_support = []
        profile.confidence_threshold = 0.7
        profile.custom_rules = {}
        profile.inherits_from = []
        profile.version = "1.0"
        profile.metadata = {}
        
        manager = ProfileManager()
        errors = manager.validate_profile(profile)
        
        assert len(errors) > 0
        assert any("Profile name must be a non-empty string" in error for error in errors)
    
    def test_create_composite_profile(self):
        """Test creating composite profile."""
        profile1 = RedactionProfile(
            name="profile1",
            description="Profile 1",
            visual_rules={"face": True},
            text_rules={"email": True}
        )
        
        profile2 = RedactionProfile(
            name="profile2",
            description="Profile 2",
            visual_rules={"signature": True},
            text_rules={"phone": True}
        )
        
        manager = ProfileManager()
        composite = manager.create_composite_profile(
            [profile1, profile2],
            "composite_profile"
        )
        
        assert composite.name == "composite_profile"
        assert "Composite profile from: profile1, profile2" in composite.description
        assert composite.visual_rules["face"] is True
        assert composite.visual_rules["signature"] is True
        assert composite.text_rules["email"] is True
        assert composite.text_rules["phone"] is True
    
    def test_create_composite_profile_empty_list(self):
        """Test creating composite profile with empty list."""
        manager = ProfileManager()
        
        with pytest.raises(ValueError) as exc_info:
            manager.create_composite_profile([], "empty_composite")
        
        assert "At least one profile must be provided" in str(exc_info.value)
    
    def test_save_profile_yaml(self):
        """Test saving profile as YAML."""
        profile = RedactionProfile(
            name="save_test",
            description="Save test profile",
            visual_rules={"face": True}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            manager = ProfileManager([temp_path])
            
            saved_path = manager.save_profile(profile, temp_path, 'yaml')
            
            assert saved_path.exists()
            assert saved_path.name == "save_test.yaml"
            
            # Verify content
            loaded_profile = RedactionProfile.from_yaml(saved_path)
            assert loaded_profile.name == profile.name
            assert loaded_profile.visual_rules == profile.visual_rules
    
    def test_save_profile_json(self):
        """Test saving profile as JSON."""
        profile = RedactionProfile(
            name="save_test_json",
            description="Save test profile JSON",
            text_rules={"email": False}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            manager = ProfileManager([temp_path])
            
            saved_path = manager.save_profile(profile, temp_path, 'json')
            
            assert saved_path.exists()
            assert saved_path.name == "save_test_json.json"
            
            # Verify content
            loaded_profile = RedactionProfile.from_json(saved_path)
            assert loaded_profile.name == profile.name
            assert loaded_profile.text_rules == profile.text_rules
    
    def test_save_profile_unsupported_format(self):
        """Test saving profile with unsupported format."""
        profile = RedactionProfile(name="test", description="Test")
        manager = ProfileManager()
        
        with pytest.raises(ValueError) as exc_info:
            manager.save_profile(profile, format='xml')
        
        assert "Unsupported format: xml" in str(exc_info.value)
    
    def test_clear_cache(self):
        """Test clearing profile cache."""
        manager = ProfileManager()
        
        # Add something to cache
        manager._profile_cache["test"] = RedactionProfile(name="test", description="Test")
        assert len(manager._profile_cache) > 0
        
        manager.clear_cache()
        assert len(manager._profile_cache) == 0


class TestProfileInheritance:
    """Test cases for profile inheritance functionality."""
    
    def test_inheritance_resolution(self):
        """Test resolving profile inheritance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create base profile
            base_profile_data = {
                'name': 'base',
                'description': 'Base profile',
                'visual_rules': {'face': True, 'signature': False},
                'text_rules': {'email': True, 'phone': False},
                'confidence_threshold': 0.7
            }
            
            base_path = temp_path / "base.yaml"
            with open(base_path, 'w') as f:
                yaml.dump(base_profile_data, f)
            
            # Create child profile that inherits from base
            child_profile_data = {
                'name': 'child',
                'description': 'Child profile',
                'inherits_from': ['base'],
                'visual_rules': {'signature': True, 'barcode': True},  # Override signature, add barcode
                'text_rules': {'phone': True},  # Override phone
                'confidence_threshold': 0.8  # Override threshold
            }
            
            child_path = temp_path / "child.yaml"
            with open(child_path, 'w') as f:
                yaml.dump(child_profile_data, f)
            
            manager = ProfileManager([temp_path])
            resolved_profile = manager.load_profile("child", resolve_inheritance=True)
            
            # Check inherited and overridden values
            assert resolved_profile.visual_rules['face'] is True  # Inherited
            assert resolved_profile.visual_rules['signature'] is True  # Overridden
            assert resolved_profile.visual_rules['barcode'] is True  # Added
            assert resolved_profile.text_rules['email'] is True  # Inherited
            assert resolved_profile.text_rules['phone'] is True  # Overridden
            assert resolved_profile.confidence_threshold == 0.8  # Overridden
    
    def test_circular_inheritance_detection(self):
        """Test detection of circular inheritance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create profiles with circular inheritance
            profile_a_data = {
                'name': 'profile_a',
                'description': 'Profile A',
                'inherits_from': ['profile_b']
            }
            
            profile_b_data = {
                'name': 'profile_b',
                'description': 'Profile B',
                'inherits_from': ['profile_a']  # Circular reference
            }
            
            with open(temp_path / "profile_a.yaml", 'w') as f:
                yaml.dump(profile_a_data, f)
            
            with open(temp_path / "profile_b.yaml", 'w') as f:
                yaml.dump(profile_b_data, f)
            
            manager = ProfileManager([temp_path])
            
            with pytest.raises(ProfileValidationError) as exc_info:
                manager.load_profile("profile_a", resolve_inheritance=True)
            
            assert "Circular inheritance detected" in str(exc_info.value)
    
    def test_multiple_inheritance(self):
        """Test profile with multiple parents."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create parent profiles
            parent1_data = {
                'name': 'parent1',
                'description': 'Parent 1',
                'visual_rules': {'face': True},
                'text_rules': {'email': True},
                'multilingual_support': ['en']
            }
            
            parent2_data = {
                'name': 'parent2',
                'description': 'Parent 2',
                'visual_rules': {'signature': True},
                'text_rules': {'phone': True},
                'multilingual_support': ['es']
            }
            
            # Create child that inherits from both
            child_data = {
                'name': 'multi_child',
                'description': 'Multi-inheritance child',
                'inherits_from': ['parent1', 'parent2'],
                'visual_rules': {'barcode': True}
            }
            
            for name, data in [('parent1', parent1_data), ('parent2', parent2_data), ('multi_child', child_data)]:
                with open(temp_path / f"{name}.yaml", 'w') as f:
                    yaml.dump(data, f)
            
            manager = ProfileManager([temp_path])
            resolved_profile = manager.load_profile("multi_child", resolve_inheritance=True)
            
            # Should have rules from both parents plus child's own rules
            assert resolved_profile.visual_rules['face'] is True  # From parent1
            assert resolved_profile.visual_rules['signature'] is True  # From parent2
            assert resolved_profile.visual_rules['barcode'] is True  # From child
            assert resolved_profile.text_rules['email'] is True  # From parent1
            assert resolved_profile.text_rules['phone'] is True  # From parent2
            
            # Languages should be combined
            assert set(resolved_profile.multilingual_support) == {'en', 'es'}