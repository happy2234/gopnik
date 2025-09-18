"""
Tests for CLI API command.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from io import StringIO

from src.gopnik.interfaces.cli.main import GopnikCLI


def test_api_command_help():
    """Test that API command help is available."""
    cli = GopnikCLI()
    parser = cli.create_parser()
    
    # Capture help output
    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['api', '--help'])
        
        # Should exit with code 0 for help
        assert exc_info.value.code == 0
        
        help_output = mock_stdout.getvalue()
        assert 'Gopnik REST API server' in help_output
        assert '--host' in help_output
        assert '--port' in help_output
        assert '--reload' in help_output


def test_api_command_parsing():
    """Test API command argument parsing."""
    cli = GopnikCLI()
    parser = cli.create_parser()
    
    # Test default arguments
    args = parser.parse_args(['api'])
    assert args.command == 'api'
    assert args.host == '127.0.0.1'
    assert args.port == 8000
    assert args.reload is False
    
    # Test custom arguments
    args = parser.parse_args(['api', '--host', '0.0.0.0', '--port', '8080', '--reload'])
    assert args.command == 'api'
    assert args.host == '0.0.0.0'
    assert args.port == 8080
    assert args.reload is True


@patch('src.gopnik.interfaces.api.app.run_server')
def test_api_command_execution(mock_run_server):
    """Test API command execution."""
    cli = GopnikCLI()
    
    # Mock the run_server function
    mock_run_server.return_value = None
    
    # Test execution
    result = cli.run(['api', '--host', '0.0.0.0', '--port', '8080'])
    
    # Should succeed
    assert result == 0
    
    # Should call run_server with correct arguments
    mock_run_server.assert_called_once_with(
        host='0.0.0.0',
        port=8080,
        reload=False
    )


@patch('src.gopnik.interfaces.api.app.run_server')
def test_api_command_with_reload(mock_run_server):
    """Test API command with reload option."""
    cli = GopnikCLI()
    
    # Mock the run_server function
    mock_run_server.return_value = None
    
    # Test execution with reload
    result = cli.run(['api', '--reload'])
    
    # Should succeed
    assert result == 0
    
    # Should call run_server with reload=True
    mock_run_server.assert_called_once_with(
        host='127.0.0.1',
        port=8000,
        reload=True
    )


def test_api_command_import_error():
    """Test API command when FastAPI is not installed."""
    cli = GopnikCLI()
    
    # Mock import error by patching the import itself
    with patch('builtins.__import__', side_effect=ImportError("No module named 'fastapi'")):
        result = cli.run(['api'])
        
        # Should fail with import error
        assert result == 1


@patch('src.gopnik.interfaces.api.app.run_server')
def test_api_command_keyboard_interrupt(mock_run_server):
    """Test API command handling keyboard interrupt."""
    cli = GopnikCLI()
    
    # Mock keyboard interrupt
    mock_run_server.side_effect = KeyboardInterrupt()
    
    result = cli.run(['api'])
    
    # Should handle interrupt gracefully
    assert result == 0


@patch('src.gopnik.interfaces.api.app.run_server')
def test_api_command_server_error(mock_run_server):
    """Test API command handling server errors."""
    cli = GopnikCLI()
    
    # Mock server error
    mock_run_server.side_effect = Exception("Server failed to start")
    
    result = cli.run(['api'])
    
    # Should handle error and return error code
    assert result == 1