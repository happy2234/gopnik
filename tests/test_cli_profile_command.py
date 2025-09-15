"""
Unit tests for CLI profile command.
"""

import pytest
import tempfile
import shutil
import yaml
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import argparse

from src.gopnik.interfaces.cli.commands.profile_command import ProfileCommand
from src.gopnik.config import GopnikConfig
from src.gopnik.models.profiles import RedactionProfile, RedactionStyle
from src.gopnik.models.pii import PIIType


class TestProfileCommand:
    """Test cases for ProfileCommand class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=GopnikConfig)
        self.command = ProfileCommand(self.config)
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create profiles directory
        self.profiles_dir = self.temp_dir / "profiles"
        self.profiles_dir.mkdir()
        
        # Create test profile
        self.test_profile_data = {
            'name': 'test_profile',
            'description': 'Test profile for unit tests',
            'visual_rules': {'face': True, 'signature': False},
            'text_rules': {'name': True, 'email': True, 'phone': False},
            'redaction_style': 'solid_black',
            'confidence_threshold': 0.8,
            'multilingual_support': ['en', 'es']
        }
        
        self.test_profile_file = self.profiles_dir / "test_profile.yaml"
        with open(self.test_profile_file, 'w') as f:
            yaml.dump(self.test_profile_data, f)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_add_arguments(self):
        """Test argument parser setup."""
        parser = argparse.ArgumentParser()
        ProfileCommand.add_arguments(parser)
        
        # Test list subcommand
        args = parser.parse_args(['list'])
        assert args.profile_action == 'list'
        
        # Test list with options
        args = parser.parse_args(['list', '--format', 'json', '--verbose'])
        assert args.format == 'json'
        assert args.verbose is True
        
        # Test show subcommand
        args = parser.parse_args(['show', 'test_profile'])
        assert args.profile_action == 'show'
        assert args.name == 'test_profile'
        
        # Test create subcommand
        args = parser.parse_args([
            'create',
            '--name', 'new_profile',
            '--description', 'New profile',
            '--pii-types', 'name', 'email',
            '--redaction-style', 'solid'
        ])
        assert args.profile_action == 'create'
        assert args.name == 'new_profile'
        assert args.description == 'New profile'
        assert args.pii_types == ['name', 'email']
        assert args.redaction_style == 'solid'
        
        # Test edit subcommand
        args = parser.parse_args([
            'edit', 'test_profile',
            '--add-pii-types', 'phone',
            '--remove-pii-types', 'email'
        ])
        assert args.profile_action == 'edit'
        assert args.name == 'test_profile'
        assert args.add_pii_types == ['phone']
        assert args.remove_pii_types == ['email']
        
        # Test validate subcommand
        args = parser.parse_args(['validate', 'test_profile'])
        assert args.profile_action == 'validate'
        assert args.profile == 'test_profile'
        
        # Test delete subcommand
        args = parser.parse_args(['delete', 'test_profile', '--force'])
        assert args.profile_action == 'delete'
        assert args.name == 'test_profile'
        assert args.force is True
    
    @patch('src.gopnik.interfaces.cli.commands.profile_command.ProfileManager')
    def test_list_profiles_text_format(self, mock_profile_manager_class):
        """Test listing profiles in text format."""
        # Mock ProfileManager
        mock_manager = Mock()
        mock_manager.list_profiles.return_value = ['test_profile', 'healthcare']
        mock_profile_manager_class.return_value = mock_manager
        
        # Mock profile loading
        test_profile = RedactionProfile(
            name='test_profile',
            description='Test profile',
            visual_rules={'face': True},
            text_rules={'name': True, 'email': True}
        )
        
        with patch.object(self.command, '_find_profile_path', return_value=self.test_profile_file):
            mock_manager.load_profile.return_value = test_profile
            
            args = argparse.Namespace(
                profile_action='list',
                format='text',
                verbose=False
            )
            
            with patch('builtins.print') as mock_print:
                result = self.command.execute(args)
            
            assert result == 0
            # Verify output contains profile information
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any('test_profile' in call for call in print_calls)
    
    @patch('src.gopnik.interfaces.cli.commands.profile_command.ProfileManager')
    def test_list_profiles_json_format(self, mock_profile_manager_class):
        """Test listing profiles in JSON format."""
        # Mock ProfileManager
        mock_manager = Mock()
        mock_manager.list_profiles.return_value = ['test_profile']
        mock_profile_manager_class.return_value = mock_manager
        
        # Mock profile loading
        test_profile = RedactionProfile(
            name='test_profile',
            description='Test profile',
            visual_rules={'face': True},
            text_rules={'name': True, 'email': True}
        )
        
        with patch.object(self.command, '_find_profile_path', return_value=self.test_profile_file):
            mock_manager.load_profile.return_value = test_profile
            
            args = argparse.Namespace(
                profile_action='list',
                format='json',
                verbose=True
            )
            
            with patch.object(self.command, 'print_json') as mock_print_json:
                result = self.command.execute(args)
            
            assert result == 0
            mock_print_json.assert_called_once()
            
            # Verify JSON structure
            json_output = mock_print_json.call_args[0][0]
            assert isinstance(json_output, list)
            assert len(json_output) == 1
            assert json_output[0]['name'] == 'test_profile'
    
    @patch('src.gopnik.interfaces.cli.commands.profile_command.ProfileManager')
    def test_show_profile(self, mock_profile_manager_class):
        """Test showing profile details."""
        # Mock ProfileManager
        mock_manager = Mock()
        test_profile = RedactionProfile(
            name='test_profile',
            description='Test profile',
            visual_rules={'face': True},
            text_rules={'name': True, 'email': True},
            confidence_threshold=0.8,
            multilingual_support=['en']
        )
        mock_manager.load_profile.return_value = test_profile
        mock_profile_manager_class.return_value = mock_manager
        
        args = argparse.Namespace(
            profile_action='show',
            name='test_profile',
            format='text'
        )
        
        with patch('builtins.print') as mock_print:
            result = self.command.execute(args)
        
        assert result == 0
        mock_manager.load_profile.assert_called_once_with('test_profile')
        
        # Verify output contains profile details
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any('Profile: test_profile' in call for call in print_calls)
        assert any('Test profile' in call for call in print_calls)
    
    @patch('src.gopnik.interfaces.cli.commands.profile_command.ProfileManager')
    def test_show_profile_json(self, mock_profile_manager_class):
        """Test showing profile details in JSON format."""
        # Mock ProfileManager
        mock_manager = Mock()
        test_profile = RedactionProfile(
            name='test_profile',
            description='Test profile',
            visual_rules={'face': True},
            text_rules={'name': True, 'email': True},
            confidence_threshold=0.8,
            multilingual_support=['en']
        )
        mock_manager.load_profile.return_value = test_profile
        mock_profile_manager_class.return_value = mock_manager
        
        args = argparse.Namespace(
            profile_action='show',
            name='test_profile',
            format='json'
        )
        
        with patch.object(self.command, 'print_json') as mock_print_json:
            result = self.command.execute(args)
        
        assert result == 0
        mock_print_json.assert_called_once()
        
        # Verify JSON structure
        json_output = mock_print_json.call_args[0][0]
        assert json_output['name'] == 'test_profile'
        assert json_output['description'] == 'Test profile'
        assert 'pii_types' in json_output
        assert 'visual_rules' in json_output
        assert 'text_rules' in json_output
    
    def test_create_profile_new(self):
        """Test creating a new profile."""
        args = argparse.Namespace(
            profile_action='create',
            name='new_profile',
            description='New test profile',
            based_on=None,
            pii_types=['name', 'email'],
            redaction_style='solid',
            output=None
        )
        
        with patch.object(self.command, 'confirm_action', return_value=True):
            with patch('pathlib.Path.mkdir'):
                with patch('src.gopnik.models.profiles.RedactionProfile.save_yaml') as mock_save:
                    result = self.command.execute(args)
        
        assert result == 0
        mock_save.assert_called_once()
    
    @patch('src.gopnik.interfaces.cli.commands.profile_command.ProfileManager')
    def test_create_profile_based_on_existing(self, mock_profile_manager_class):
        """Test creating a profile based on existing one."""
        # Mock ProfileManager and base profile
        mock_manager = Mock()
        base_profile = RedactionProfile(
            name='base_profile',
            description='Base profile',
            visual_rules={'face': True},
            text_rules={'name': True},
            redaction_style=RedactionStyle.SOLID_BLACK,
            confidence_threshold=0.7,
            multilingual_support=['en']
        )
        mock_manager.load_profile.return_value = base_profile
        mock_profile_manager_class.return_value = mock_manager
        
        args = argparse.Namespace(
            profile_action='create',
            name='derived_profile',
            description='Derived profile',
            based_on='base_profile',
            pii_types=None,
            redaction_style=None,
            output=None
        )
        
        with patch.object(self.command, 'confirm_action', return_value=True):
            with patch('pathlib.Path.mkdir'):
                with patch('src.gopnik.models.profiles.RedactionProfile.save_yaml') as mock_save:
                    result = self.command.execute(args)
        
        assert result == 0
        mock_save.assert_called_once()
        mock_manager.load_profile.assert_called_once_with('base_profile')
    
    @patch('src.gopnik.interfaces.cli.commands.profile_command.ProfileManager')
    def test_edit_profile(self, mock_profile_manager_class):
        """Test editing an existing profile."""
        # Mock ProfileManager and existing profile
        mock_manager = Mock()
        existing_profile = RedactionProfile(
            name='test_profile',
            description='Original description',
            visual_rules={'face': True},
            text_rules={'name': True, 'email': False},
            redaction_style=RedactionStyle.SOLID_BLACK
        )
        mock_manager.load_profile.return_value = existing_profile
        mock_manager.save_profile.return_value = Path('profiles/test_profile.yaml')
        mock_profile_manager_class.return_value = mock_manager
        
        args = argparse.Namespace(
            profile_action='edit',
            name='test_profile',
            description='Updated description',
            add_pii_types=['phone'],
            remove_pii_types=['email'],
            redaction_style='blur'
        )
        
        result = self.command.execute(args)
        
        assert result == 0
        mock_manager.load_profile.assert_called_once_with('test_profile')
        mock_manager.save_profile.assert_called_once()
        
        # Verify profile was modified
        saved_profile = mock_manager.save_profile.call_args[0][0]
        assert saved_profile.description == 'Updated description'
        assert saved_profile.text_rules['phone'] is True
        assert saved_profile.text_rules['email'] is False
    
    @patch('src.gopnik.interfaces.cli.commands.profile_command.ProfileManager')
    def test_validate_profile_valid(self, mock_profile_manager_class):
        """Test validating a valid profile."""
        # Mock ProfileManager
        mock_manager = Mock()
        test_profile = RedactionProfile(
            name='test_profile',
            description='Test profile',
            visual_rules={'face': True},
            text_rules={'name': True}
        )
        mock_manager.load_profile.return_value = test_profile
        mock_manager.validate_profile.return_value = []  # No errors
        mock_profile_manager_class.return_value = mock_manager
        
        args = argparse.Namespace(
            profile_action='validate',
            profile='test_profile',
            format='text'
        )
        
        with patch('builtins.print') as mock_print:
            result = self.command.execute(args)
        
        assert result == 0
        mock_manager.validate_profile.assert_called_once_with(test_profile)
        
        # Verify output shows valid
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any('✓ VALID' in call for call in print_calls)
    
    @patch('src.gopnik.interfaces.cli.commands.profile_command.ProfileManager')
    def test_validate_profile_invalid(self, mock_profile_manager_class):
        """Test validating an invalid profile."""
        # Mock ProfileManager
        mock_manager = Mock()
        test_profile = RedactionProfile(
            name='test_profile',
            description='Test profile',
            visual_rules={'face': True},
            text_rules={'name': True}
        )
        mock_manager.load_profile.return_value = test_profile
        mock_manager.validate_profile.return_value = ['Invalid configuration', 'Missing required field']
        mock_profile_manager_class.return_value = mock_manager
        
        args = argparse.Namespace(
            profile_action='validate',
            profile='test_profile',
            format='text'
        )
        
        with patch('builtins.print') as mock_print:
            result = self.command.execute(args)
        
        assert result == 1
        
        # Verify output shows invalid and errors
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any('✗ INVALID' in call for call in print_calls)
        assert any('Invalid configuration' in call for call in print_calls)
    
    @patch('src.gopnik.interfaces.cli.commands.profile_command.ProfileManager')
    def test_delete_profile(self, mock_profile_manager_class):
        """Test deleting a profile."""
        # Mock ProfileManager
        mock_manager = Mock()
        mock_manager.list_profiles.return_value = ['test_profile', 'other_profile']
        mock_profile_manager_class.return_value = mock_manager
        
        # Create test profile file
        test_profile_path = self.profiles_dir / "test_profile.yaml"
        test_profile_path.write_text("test profile content")
        
        with patch.object(self.command, '_find_profile_path', return_value=test_profile_path):
            args = argparse.Namespace(
                profile_action='delete',
                name='test_profile',
                force=True
            )
            
            with patch('pathlib.Path.unlink') as mock_unlink:
                result = self.command.execute(args)
        
        assert result == 0
        mock_unlink.assert_called_once()
    
    @patch('src.gopnik.interfaces.cli.commands.profile_command.ProfileManager')
    def test_delete_profile_with_confirmation(self, mock_profile_manager_class):
        """Test deleting a profile with user confirmation."""
        # Mock ProfileManager
        mock_manager = Mock()
        mock_manager.list_profiles.return_value = ['test_profile']
        mock_profile_manager_class.return_value = mock_manager
        
        # Create test profile file
        test_profile_path = self.profiles_dir / "test_profile.yaml"
        test_profile_path.write_text("test profile content")
        
        with patch.object(self.command, '_find_profile_path', return_value=test_profile_path):
            with patch.object(self.command, 'confirm_action', return_value=True):
                args = argparse.Namespace(
                    profile_action='delete',
                    name='test_profile',
                    force=False
                )
                
                with patch('pathlib.Path.unlink') as mock_unlink:
                    result = self.command.execute(args)
        
        assert result == 0
        mock_unlink.assert_called_once()
    
    @patch('src.gopnik.interfaces.cli.commands.profile_command.ProfileManager')
    def test_delete_profile_cancelled(self, mock_profile_manager_class):
        """Test deleting a profile when user cancels."""
        # Mock ProfileManager
        mock_manager = Mock()
        mock_manager.list_profiles.return_value = ['test_profile']
        mock_profile_manager_class.return_value = mock_manager
        
        # Create test profile file
        test_profile_path = self.profiles_dir / "test_profile.yaml"
        test_profile_path.write_text("test profile content")
        
        with patch.object(self.command, '_find_profile_path', return_value=test_profile_path):
            with patch.object(self.command, 'confirm_action', return_value=False):
                args = argparse.Namespace(
                    profile_action='delete',
                    name='test_profile',
                    force=False
                )
                
                with patch('pathlib.Path.unlink') as mock_unlink:
                    result = self.command.execute(args)
        
        assert result == 0  # Success but no deletion
        mock_unlink.assert_not_called()
    
    def test_find_profile_path(self):
        """Test finding profile file path."""
        # Test existing profile
        result = self.command._find_profile_path('test_profile')
        assert result == self.test_profile_file
        
        # Test non-existent profile
        result = self.command._find_profile_path('nonexistent')
        assert result is None
    
    def test_execute_no_action(self):
        """Test executing command without specifying action."""
        args = argparse.Namespace(profile_action=None)
        
        result = self.command.execute(args)
        assert result == 1
    
    def test_execute_unknown_action(self):
        """Test executing command with unknown action."""
        args = argparse.Namespace(profile_action='unknown')
        
        result = self.command.execute(args)
        assert result == 1
    
    @patch('src.gopnik.interfaces.cli.commands.profile_command.ProfileManager')
    def test_execute_exception_handling(self, mock_profile_manager_class):
        """Test exception handling during command execution."""
        # Mock ProfileManager to raise exception
        mock_manager = Mock()
        mock_manager.list_profiles.side_effect = Exception("Test error")
        mock_profile_manager_class.return_value = mock_manager
        
        args = argparse.Namespace(
            profile_action='list',
            format='text',
            verbose=False
        )
        
        result = self.command.execute(args)
        assert result == 1


class TestProfileCommandIntegration:
    """Integration tests for profile command."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=GopnikConfig)
        self.command = ProfileCommand(self.config)
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create profiles directory
        self.profiles_dir = self.temp_dir / "profiles"
        self.profiles_dir.mkdir()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_full_profile_lifecycle(self):
        """Test complete profile lifecycle: create, edit, validate, delete."""
        # Change to temp directory for profile operations
        original_cwd = Path.cwd()
        
        try:
            import os
            os.chdir(self.temp_dir)
            
            # 1. Create profile
            create_args = argparse.Namespace(
                profile_action='create',
                name='lifecycle_test',
                description='Lifecycle test profile',
                based_on=None,
                pii_types=['name', 'email'],
                redaction_style='solid',
                output=None
            )
            
            with patch.object(self.command, 'confirm_action', return_value=True):
                result = self.command.execute(create_args)
            assert result == 0
            
            # Verify profile was created
            profile_file = self.profiles_dir / "lifecycle_test.yaml"
            assert profile_file.exists()
            
            # 2. Edit profile
            edit_args = argparse.Namespace(
                profile_action='edit',
                name='lifecycle_test',
                description='Updated lifecycle test profile',
                add_pii_types=['phone'],
                remove_pii_types=None,
                redaction_style=None
            )
            
            result = self.command.execute(edit_args)
            assert result == 0
            
            # 3. Validate profile
            validate_args = argparse.Namespace(
                profile_action='validate',
                profile='lifecycle_test',
                format='text'
            )
            
            with patch('builtins.print'):
                result = self.command.execute(validate_args)
            assert result == 0
            
            # 4. Delete profile
            delete_args = argparse.Namespace(
                profile_action='delete',
                name='lifecycle_test',
                force=True
            )
            
            result = self.command.execute(delete_args)
            assert result == 0
            
            # Verify profile was deleted
            assert not profile_file.exists()
            
        finally:
            os.chdir(original_cwd)