"""
Unit tests for CLI main functionality and argument parsing.
"""

import pytest
import argparse
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from src.gopnik.interfaces.cli.main import GopnikCLI
from src.gopnik.config import GopnikConfig


class TestGopnikCLI:
    """Test cases for GopnikCLI class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cli = GopnikCLI()
    
    def test_create_parser(self):
        """Test parser creation with all subcommands."""
        parser = self.cli.create_parser()
        
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == 'gopnik'
        
        # Test global arguments
        with patch('sys.argv', ['gopnik', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                parser.parse_args(['--version'])
            assert exc_info.value.code == 0
    
    def test_parser_subcommands(self):
        """Test that all expected subcommands are available."""
        parser = self.cli.create_parser()
        
        # Test process command
        args = parser.parse_args(['process', 'test.pdf'])
        assert args.command == 'process'
        assert args.input == Path('test.pdf')
        
        # Test batch command
        args = parser.parse_args(['batch', '/path/to/docs'])
        assert args.command == 'batch'
        assert args.input_dir == Path('/path/to/docs')
        
        # Test validate command
        args = parser.parse_args(['validate', 'doc.pdf', 'audit.json'])
        assert args.command == 'validate'
        assert args.document == Path('doc.pdf')
        assert args.audit_log == Path('audit.json')
        
        # Test profile command
        args = parser.parse_args(['profile', 'list'])
        assert args.command == 'profile'
        assert args.profile_action == 'list'
    
    def test_global_arguments(self):
        """Test global argument parsing."""
        parser = self.cli.create_parser()
        
        # Test log level
        args = parser.parse_args(['--log-level', 'DEBUG', 'process', 'test.pdf'])
        assert args.log_level == 'DEBUG'
        
        # Test config file
        args = parser.parse_args(['--config', 'custom.yaml', 'process', 'test.pdf'])
        assert args.config == Path('custom.yaml')
        
        # Test quiet flag
        args = parser.parse_args(['--quiet', 'process', 'test.pdf'])
        assert args.quiet is True
        
        # Test verbose flag
        args = parser.parse_args(['--verbose', 'process', 'test.pdf'])
        assert args.verbose is True
    
    def test_process_command_arguments(self):
        """Test process command argument parsing."""
        parser = self.cli.create_parser()
        
        # Basic process command
        args = parser.parse_args(['process', 'input.pdf'])
        assert args.input == Path('input.pdf')
        assert args.profile == 'default'
        
        # Process with options
        args = parser.parse_args([
            'process', 'input.pdf',
            '--output', 'output.pdf',
            '--profile', 'healthcare',
            '--dry-run',
            '--force'
        ])
        assert args.output == Path('output.pdf')
        assert args.profile == 'healthcare'
        assert args.dry_run is True
        assert args.force is True
    
    def test_batch_command_arguments(self):
        """Test batch command argument parsing."""
        parser = self.cli.create_parser()
        
        # Basic batch command
        args = parser.parse_args(['batch', '/input/dir'])
        assert args.input_dir == Path('/input/dir')
        
        # Batch with options
        args = parser.parse_args([
            'batch', '/input/dir',
            '--output', '/output/dir',
            '--recursive',
            '--pattern', '*.pdf',
            '--max-files', '100'
        ])
        assert args.output == Path('/output/dir')
        assert args.recursive is True
        assert args.pattern == '*.pdf'
        assert args.max_files == 100
    
    def test_validate_command_arguments(self):
        """Test validate command argument parsing."""
        parser = self.cli.create_parser()
        
        # Validate with audit log
        args = parser.parse_args(['validate', 'doc.pdf', 'audit.json'])
        assert args.document == Path('doc.pdf')
        assert args.audit_log == Path('audit.json')
        
        # Validate with options
        args = parser.parse_args([
            'validate', 'doc.pdf',
            '--audit-dir', '/audit/logs',
            '--strict',
            '--verify-signatures'
        ])
        assert args.audit_dir == Path('/audit/logs')
        assert args.strict is True
        assert args.verify_signatures is True
    
    def test_profile_command_arguments(self):
        """Test profile command argument parsing."""
        parser = self.cli.create_parser()
        
        # Profile list
        args = parser.parse_args(['profile', 'list'])
        assert args.profile_action == 'list'
        
        # Profile show
        args = parser.parse_args(['profile', 'show', 'healthcare'])
        assert args.profile_action == 'show'
        assert args.name == 'healthcare'
        
        # Profile create
        args = parser.parse_args([
            'profile', 'create',
            '--name', 'custom',
            '--description', 'Custom profile',
            '--pii-types', 'name', 'email',
            '--redaction-style', 'solid'
        ])
        assert args.profile_action == 'create'
        assert args.name == 'custom'
        assert args.description == 'Custom profile'
        assert args.pii_types == ['name', 'email']
        assert args.redaction_style == 'solid'
    
    @patch('src.gopnik.interfaces.cli.main.setup_logging')
    def test_setup_logging_from_args(self, mock_setup_logging):
        """Test logging setup from arguments."""
        args = argparse.Namespace(
            log_level='INFO',
            log_file=None,
            quiet=False,
            verbose=False
        )
        
        self.cli.setup_logging_from_args(args)
        
        mock_setup_logging.assert_called_once_with(
            level='INFO',
            log_file=None
        )
    
    @patch('src.gopnik.interfaces.cli.main.setup_logging')
    def test_setup_logging_quiet_mode(self, mock_setup_logging):
        """Test logging setup in quiet mode."""
        args = argparse.Namespace(
            log_level='INFO',
            log_file=None,
            quiet=True,
            verbose=False
        )
        
        self.cli.setup_logging_from_args(args)
        
        mock_setup_logging.assert_called_once_with(
            level='ERROR',
            log_file=None
        )
    
    @patch('src.gopnik.interfaces.cli.main.setup_logging')
    def test_setup_logging_verbose_mode(self, mock_setup_logging):
        """Test logging setup in verbose mode."""
        args = argparse.Namespace(
            log_level='INFO',
            log_file=Path('test.log'),
            quiet=False,
            verbose=True
        )
        
        self.cli.setup_logging_from_args(args)
        
        mock_setup_logging.assert_called_once_with(
            level='DEBUG',
            log_file=Path('test.log')
        )
    
    @patch('src.gopnik.config.GopnikConfig.from_file')
    def test_load_config_from_args(self, mock_from_file):
        """Test configuration loading from arguments."""
        # Mock config file
        mock_config = Mock(spec=GopnikConfig)
        mock_from_file.return_value = mock_config
        
        # Test with config file
        config_path = Path('test_config.yaml')
        args = argparse.Namespace(config=config_path)
        
        with patch.object(config_path, 'exists', return_value=True):
            self.cli.setup_logging_from_args(argparse.Namespace(
                log_level='INFO', log_file=None, quiet=False, verbose=False
            ))
            self.cli.load_config_from_args(args)
        
        mock_from_file.assert_called_once_with(config_path)
        assert self.cli.config == mock_config
    
    def test_load_config_file_not_found(self):
        """Test configuration loading with non-existent file."""
        config_path = Path('nonexistent.yaml')
        args = argparse.Namespace(config=config_path)
        
        # Setup logging first
        self.cli.setup_logging_from_args(argparse.Namespace(
            log_level='INFO', log_file=None, quiet=False, verbose=False
        ))
        
        with patch.object(config_path, 'exists', return_value=False):
            with pytest.raises(SystemExit) as exc_info:
                self.cli.load_config_from_args(args)
            assert exc_info.value.code == 1
    
    def test_validate_arguments_no_command(self):
        """Test argument validation with no command."""
        args = argparse.Namespace(command=None)
        
        # Setup logging first
        self.cli.setup_logging_from_args(argparse.Namespace(
            log_level='INFO', log_file=None, quiet=False, verbose=False
        ))
        
        result = self.cli.validate_arguments(args)
        assert result is False
    
    def test_validate_arguments_with_command(self):
        """Test argument validation with valid command."""
        args = argparse.Namespace(command='process')
        
        # Setup logging first
        self.cli.setup_logging_from_args(argparse.Namespace(
            log_level='INFO', log_file=None, quiet=False, verbose=False
        ))
        
        result = self.cli.validate_arguments(args)
        assert result is True
    
    @patch('src.gopnik.interfaces.cli.commands.ProcessCommand')
    def test_execute_command_process(self, mock_process_command):
        """Test command execution for process command."""
        mock_command_instance = Mock()
        mock_command_instance.execute.return_value = 0
        mock_process_command.return_value = mock_command_instance
        
        args = argparse.Namespace(command='process')
        
        result = self.cli.execute_command(args)
        
        mock_process_command.assert_called_once_with(self.cli.config)
        mock_command_instance.execute.assert_called_once_with(args)
        assert result == 0
    
    def test_execute_command_unknown(self):
        """Test command execution with unknown command."""
        args = argparse.Namespace(command='unknown')
        
        # Setup logging first
        self.cli.setup_logging_from_args(argparse.Namespace(
            log_level='INFO', log_file=None, quiet=False, verbose=False
        ))
        
        result = self.cli.execute_command(args)
        assert result == 1
    
    def test_execute_command_keyboard_interrupt(self):
        """Test command execution with keyboard interrupt."""
        with patch('src.gopnik.interfaces.cli.commands.ProcessCommand') as mock_command:
            mock_command_instance = Mock()
            mock_command_instance.execute.side_effect = KeyboardInterrupt()
            mock_command.return_value = mock_command_instance
            
            args = argparse.Namespace(command='process')
            
            # Setup logging first
            self.cli.setup_logging_from_args(argparse.Namespace(
                log_level='INFO', log_file=None, quiet=False, verbose=False
            ))
            
            result = self.cli.execute_command(args)
            assert result == 130
    
    def test_run_no_arguments(self):
        """Test running CLI with no arguments."""
        with patch('sys.stdout', new_callable=StringIO):
            result = self.cli.run([])
            assert result == 0
    
    @patch('src.gopnik.interfaces.cli.main.GopnikCLI.execute_command')
    @patch('src.gopnik.interfaces.cli.main.GopnikCLI.validate_arguments')
    @patch('src.gopnik.interfaces.cli.main.GopnikCLI.load_config_from_args')
    @patch('src.gopnik.interfaces.cli.main.GopnikCLI.setup_logging_from_args')
    def test_run_full_workflow(self, mock_setup_logging, mock_load_config, 
                              mock_validate, mock_execute):
        """Test full CLI workflow."""
        mock_validate.return_value = True
        mock_execute.return_value = 0
        
        result = self.cli.run(['process', 'test.pdf'])
        
        assert result == 0
        mock_setup_logging.assert_called_once()
        mock_load_config.assert_called_once()
        mock_validate.assert_called_once()
        mock_execute.assert_called_once()
    
    def test_run_help_argument(self):
        """Test running CLI with help argument."""
        with patch('sys.stdout', new_callable=StringIO):
            result = self.cli.run(['--help'])
            assert result == 0


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    def test_main_function_import(self):
        """Test that main function can be imported."""
        from src.gopnik.interfaces.cli.main import main
        assert callable(main)
    
    @patch('src.gopnik.interfaces.cli.main.GopnikCLI.run')
    def test_main_function_execution(self, mock_run):
        """Test main function execution."""
        from src.gopnik.interfaces.cli.main import main
        
        mock_run.return_value = 0
        result = main()
        
        mock_run.assert_called_once()
        assert result == 0
    
    def test_cli_entry_point_import(self):
        """Test that CLI entry point can be imported."""
        from src.gopnik.cli import main
        assert callable(main)