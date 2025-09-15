"""
Unit tests for CLI base command functionality.
"""

import pytest
import argparse
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from io import StringIO
import json

from src.gopnik.interfaces.cli.base_command import BaseCommand
from src.gopnik.config import GopnikConfig


class TestBaseCommand:
    """Test cases for BaseCommand class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a concrete implementation for testing
        class TestCommand(BaseCommand):
            @staticmethod
            def add_arguments(parser):
                parser.add_argument('test_arg')
            
            def execute(self, args):
                return 0
        
        self.config = Mock(spec=GopnikConfig)
        self.command = TestCommand(self.config)
    
    def test_init(self):
        """Test command initialization."""
        assert self.command.config == self.config
        assert hasattr(self.command, 'logger')
    
    def test_validate_file_path_exists(self):
        """Test file path validation for existing file."""
        test_path = Path('test_file.txt')
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_file', return_value=True):
            
            result = self.command.validate_file_path(test_path, must_exist=True)
            assert result is True
    
    def test_validate_file_path_not_exists(self):
        """Test file path validation for non-existent file."""
        test_path = Path('nonexistent.txt')
        
        with patch('pathlib.Path.exists', return_value=False):
            result = self.command.validate_file_path(test_path, must_exist=True)
            assert result is False
    
    def test_validate_file_path_not_file(self):
        """Test file path validation for directory instead of file."""
        test_path = Path('test_dir')
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_file', return_value=False):
            
            result = self.command.validate_file_path(test_path, must_exist=True)
            assert result is False
    
    def test_validate_file_path_create_parent(self):
        """Test file path validation with parent directory creation."""
        test_path = Path('new_dir/test_file.txt')
        
        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('pathlib.Path.is_dir', return_value=True):
            
            result = self.command.validate_file_path(test_path, must_exist=False)
            assert result is True
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    def test_validate_directory_path_exists(self):
        """Test directory path validation for existing directory."""
        test_path = Path('test_dir')
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True):
            
            result = self.command.validate_directory_path(test_path, must_exist=True)
            assert result is True
    
    def test_validate_directory_path_create(self):
        """Test directory path validation with creation."""
        test_path = Path('new_dir')
        
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            result = self.command.validate_directory_path(test_path, must_exist=False)
            assert result is True
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    def test_validate_directory_path_create_error(self):
        """Test directory path validation with creation error."""
        test_path = Path('invalid_dir')
        
        with patch('pathlib.Path.mkdir', side_effect=OSError("Permission denied")):
            result = self.command.validate_directory_path(test_path, must_exist=False)
            assert result is False
    
    def test_format_error_simple(self):
        """Test error message formatting without details."""
        message = "Something went wrong"
        result = self.command.format_error(message)
        assert result == "Error: Something went wrong"
    
    def test_format_error_with_details(self):
        """Test error message formatting with details."""
        message = "Processing failed"
        details = {'file': 'test.pdf', 'code': 500}
        result = self.command.format_error(message, details)
        assert result == "Error: Processing failed (file=test.pdf, code=500)"
    
    def test_format_success_simple(self):
        """Test success message formatting without details."""
        message = "Operation completed"
        result = self.command.format_success(message)
        assert result == "Success: Operation completed"
    
    def test_format_success_with_details(self):
        """Test success message formatting with details."""
        message = "File processed"
        details = {'output': 'result.pdf', 'time': '2.5s'}
        result = self.command.format_success(message, details)
        assert result == "Success: File processed (output=result.pdf, time=2.5s)"
    
    def test_print_json(self):
        """Test JSON printing functionality."""
        test_data = {'key': 'value', 'number': 42}
        
        with patch('builtins.print') as mock_print:
            self.command.print_json(test_data)
            
            # Verify print was called with formatted JSON
            mock_print.assert_called_once()
            printed_text = mock_print.call_args[0][0]
            parsed_data = json.loads(printed_text)
            assert parsed_data == test_data
    
    def test_print_json_with_path_objects(self):
        """Test JSON printing with Path objects."""
        test_data = {'path': Path('/test/path'), 'name': 'test'}
        
        with patch('builtins.print') as mock_print:
            self.command.print_json(test_data)
            
            # Verify print was called and Path was converted to string
            mock_print.assert_called_once()
            printed_text = mock_print.call_args[0][0]
            parsed_data = json.loads(printed_text)
            assert parsed_data['path'] == '/test/path'
            assert parsed_data['name'] == 'test'
    
    @patch('builtins.input', return_value='y')
    def test_confirm_action_yes(self, mock_input):
        """Test user confirmation with yes response."""
        result = self.command.confirm_action("Continue?")
        assert result is True
        mock_input.assert_called_once_with("Continue? [y/N]: ")
    
    @patch('builtins.input', return_value='n')
    def test_confirm_action_no(self, mock_input):
        """Test user confirmation with no response."""
        result = self.command.confirm_action("Continue?")
        assert result is False
    
    @patch('builtins.input', return_value='')
    def test_confirm_action_default_false(self, mock_input):
        """Test user confirmation with empty response and default False."""
        result = self.command.confirm_action("Continue?", default=False)
        assert result is False
    
    @patch('builtins.input', return_value='')
    def test_confirm_action_default_true(self, mock_input):
        """Test user confirmation with empty response and default True."""
        result = self.command.confirm_action("Continue?", default=True)
        assert result is True
        mock_input.assert_called_once_with("Continue? [Y/n]: ")
    
    @patch('builtins.input', return_value='yes')
    def test_confirm_action_yes_variants(self, mock_input):
        """Test user confirmation with various yes responses."""
        for response in ['yes', 'YES', 'Y', 'true', '1']:
            mock_input.return_value = response
            result = self.command.confirm_action("Continue?")
            assert result is True
    
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    def test_confirm_action_keyboard_interrupt(self, mock_input):
        """Test user confirmation with keyboard interrupt."""
        result = self.command.confirm_action("Continue?")
        assert result is False
    
    @patch('builtins.input', side_effect=EOFError())
    def test_confirm_action_eof_error(self, mock_input):
        """Test user confirmation with EOF error."""
        result = self.command.confirm_action("Continue?")
        assert result is False


class TestBaseCommandAbstractMethods:
    """Test abstract method requirements."""
    
    def test_abstract_methods_required(self):
        """Test that abstract methods must be implemented."""
        
        # This should raise TypeError because abstract methods are not implemented
        with pytest.raises(TypeError):
            BaseCommand(Mock())
    
    def test_concrete_implementation_works(self):
        """Test that concrete implementation with all methods works."""
        
        class ConcreteCommand(BaseCommand):
            @staticmethod
            def add_arguments(parser):
                pass
            
            def execute(self, args):
                return 0
        
        # This should work without errors
        config = Mock(spec=GopnikConfig)
        command = ConcreteCommand(config)
        assert isinstance(command, BaseCommand)
        assert command.config == config


class TestBaseCommandIntegration:
    """Integration tests for BaseCommand functionality."""
    
    def test_command_with_real_parser(self):
        """Test command integration with real argument parser."""
        
        class TestCommand(BaseCommand):
            @staticmethod
            def add_arguments(parser):
                parser.add_argument('--test-flag', action='store_true')
                parser.add_argument('input_file', type=Path)
            
            def execute(self, args):
                if args.test_flag:
                    return 0
                return 1
        
        # Create parser and add arguments
        parser = argparse.ArgumentParser()
        TestCommand.add_arguments(parser)
        
        # Parse test arguments
        args = parser.parse_args(['--test-flag', 'test.txt'])
        
        # Create and execute command
        config = Mock(spec=GopnikConfig)
        command = TestCommand(config)
        result = command.execute(args)
        
        assert result == 0
        assert args.test_flag is True
        assert args.input_file == Path('test.txt')