"""
Unit tests for CLI validate command.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import argparse

from src.gopnik.interfaces.cli.commands.validate_command import ValidateCommand
from src.gopnik.config import GopnikConfig


class TestValidateCommand:
    """Test cases for ValidateCommand class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=GopnikConfig)
        self.command = ValidateCommand(self.config)
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test files
        self.test_document = self.temp_dir / "test_document.pdf"
        self.test_document.write_text("Test document content")
        
        self.test_audit_log = self.temp_dir / "audit.json"
        self.test_audit_log.write_text(json.dumps({
            "document_hash": "abc123",
            "operation": "redaction",
            "timestamp": "2024-01-01T12:00:00Z",
            "signature": "signature_data"
        }))
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_add_arguments(self):
        """Test argument parser setup."""
        parser = argparse.ArgumentParser()
        ValidateCommand.add_arguments(parser)
        
        # Test required arguments
        args = parser.parse_args(['document.pdf'])
        assert args.document == Path('document.pdf')
        assert args.audit_log is None
        
        # Test with audit log
        args = parser.parse_args(['document.pdf', 'audit.json'])
        assert args.document == Path('document.pdf')
        assert args.audit_log == Path('audit.json')
        
        # Test optional arguments
        args = parser.parse_args([
            'document.pdf',
            '--audit-dir', '/audit/logs',
            '--strict',
            '--verify-signatures',
            '--format', 'json',
            '--verbose'
        ])
        assert args.audit_dir == Path('/audit/logs')
        assert args.strict is True
        assert args.verify_signatures is True
        assert args.format == 'json'
        assert args.verbose is True
    
    @patch('src.gopnik.interfaces.cli.commands.validate_command.IntegrityValidator')
    def test_execute_validation_success(self, mock_validator_class):
        """Test successful document validation."""
        # Mock validator
        mock_validator = Mock()
        mock_validator.validate_document_integrity.return_value = True
        mock_validator.generate_document_hash.return_value = "abc123"
        mock_validator_class.return_value = mock_validator
        
        # Create arguments
        args = argparse.Namespace(
            document=self.test_document,
            audit_log=self.test_audit_log,
            audit_dir=None,
            strict=False,
            verify_signatures=False,
            format='text',
            verbose=False
        )
        
        # Execute command
        result = self.command.execute(args)
        
        # Verify success
        assert result == 0
        mock_validator.validate_document_integrity.assert_called_once_with(
            self.test_document, self.test_audit_log
        )
    
    @patch('src.gopnik.interfaces.cli.commands.validate_command.IntegrityValidator')
    def test_execute_validation_failure(self, mock_validator_class):
        """Test failed document validation."""
        # Mock validator
        mock_validator = Mock()
        mock_validator.validate_document_integrity.return_value = False
        mock_validator.generate_document_hash.return_value = "different_hash"
        mock_validator_class.return_value = mock_validator
        
        # Create arguments
        args = argparse.Namespace(
            document=self.test_document,
            audit_log=self.test_audit_log,
            audit_dir=None,
            strict=False,
            verify_signatures=False,
            format='text',
            verbose=False
        )
        
        # Execute command
        result = self.command.execute(args)
        
        # Verify failure
        assert result == 1
        mock_validator.validate_document_integrity.assert_called_once_with(
            self.test_document, self.test_audit_log
        )
    
    @patch('src.gopnik.interfaces.cli.commands.validate_command.IntegrityValidator')
    def test_execute_validation_json_output(self, mock_validator_class):
        """Test validation with JSON output format."""
        # Mock validator
        mock_validator = Mock()
        mock_validator.validate_document_integrity.return_value = True
        mock_validator.generate_document_hash.return_value = "abc123"
        mock_validator_class.return_value = mock_validator
        
        # Create arguments
        args = argparse.Namespace(
            document=self.test_document,
            audit_log=self.test_audit_log,
            audit_dir=None,
            strict=False,
            verify_signatures=False,
            format='json',
            verbose=False
        )
        
        # Execute command
        with patch.object(self.command, 'print_json') as mock_print_json:
            result = self.command.execute(args)
        
        # Verify success and JSON output
        assert result == 0
        mock_print_json.assert_called_once()
        
        # Check JSON output structure
        json_output = mock_print_json.call_args[0][0]
        assert 'document' in json_output
        assert 'audit_log' in json_output
        assert 'valid' in json_output
        assert json_output['valid'] is True
    
    def test_find_audit_log_explicit(self):
        """Test finding audit log when explicitly provided."""
        args = argparse.Namespace(
            audit_log=self.test_audit_log,
            audit_dir=None
        )
        
        result = self.command._find_audit_log(args)
        assert result == self.test_audit_log
    
    def test_find_audit_log_search(self):
        """Test finding audit log by searching."""
        # Create audit log with expected name
        expected_audit = self.test_document.parent / f"{self.test_document.stem}_audit.json"
        expected_audit.write_text('{"test": "data"}')
        
        args = argparse.Namespace(
            document=self.test_document,
            audit_log=None,
            audit_dir=None
        )
        
        result = self.command._find_audit_log(args)
        assert result == expected_audit
    
    def test_find_audit_log_not_found(self):
        """Test audit log search when not found."""
        args = argparse.Namespace(
            document=self.test_document,
            audit_log=None,
            audit_dir=None
        )
        
        result = self.command._find_audit_log(args)
        assert result is None
    
    def test_find_audit_log_in_audit_dir(self):
        """Test finding audit log in specified audit directory."""
        # Create audit directory and log
        audit_dir = self.temp_dir / "audit_logs"
        audit_dir.mkdir()
        audit_log = audit_dir / f"{self.test_document.stem}_audit.json"
        audit_log.write_text('{"test": "data"}')
        
        args = argparse.Namespace(
            document=self.test_document,
            audit_log=None,
            audit_dir=audit_dir
        )
        
        result = self.command._find_audit_log(args)
        assert result == audit_log
    
    @patch('src.gopnik.interfaces.cli.commands.validate_command.IntegrityValidator')
    def test_get_validation_details(self, mock_validator_class):
        """Test getting detailed validation information."""
        # Mock validator
        mock_validator = Mock()
        mock_validator.generate_document_hash.return_value = "abc123"
        mock_validator_class.return_value = mock_validator
        
        args = argparse.Namespace(
            verify_signatures=False,
            verbose=False
        )
        
        details = self.command._get_validation_details(
            mock_validator, self.test_document, self.test_audit_log, args
        )
        
        # Verify details structure
        assert 'audit_log_loaded' in details
        assert 'current_document_hash' in details
        assert 'expected_document_hash' in details
        assert 'hash_match' in details
        assert details['audit_log_loaded'] is True
        assert details['current_document_hash'] == "abc123"
        assert details['expected_document_hash'] == "abc123"
        assert details['hash_match'] is True
    
    @patch('src.gopnik.interfaces.cli.commands.validate_command.IntegrityValidator')
    def test_get_validation_details_verbose(self, mock_validator_class):
        """Test getting detailed validation information in verbose mode."""
        # Mock validator
        mock_validator = Mock()
        mock_validator.generate_document_hash.return_value = "abc123"
        mock_validator_class.return_value = mock_validator
        
        args = argparse.Namespace(
            verify_signatures=False,
            verbose=True
        )
        
        details = self.command._get_validation_details(
            mock_validator, self.test_document, self.test_audit_log, args
        )
        
        # Verify verbose details
        assert 'document_size' in details
        assert 'document_modified' in details
        assert 'audit_log_size' in details
        assert 'audit_log_modified' in details
    
    @patch('src.gopnik.interfaces.cli.commands.validate_command.AuditLogger')
    def test_verify_signatures(self, mock_audit_logger_class):
        """Test signature verification."""
        # Mock audit logger
        mock_audit_logger = Mock()
        mock_audit_logger_class.return_value = mock_audit_logger
        
        audit_data = {
            "signature": "valid_signature",
            "operation": "redaction"
        }
        
        signature_info = self.command._verify_signatures(audit_data)
        
        # Verify signature info structure
        assert 'signatures_found' in signature_info
        assert 'signatures_valid' in signature_info
        assert 'signatures_invalid' in signature_info
        assert signature_info['signatures_found'] == 1
        assert signature_info['signatures_valid'] == 1
        assert signature_info['signatures_invalid'] == 0
    
    def test_verify_signatures_list_format(self):
        """Test signature verification with list format audit data."""
        audit_data = [
            {"signature": "sig1", "operation": "op1"},
            {"signature": "sig2", "operation": "op2"},
            {"no_signature": "data"}
        ]
        
        signature_info = self.command._verify_signatures(audit_data)
        
        # Verify signature counts
        assert signature_info['signatures_found'] == 2
        assert signature_info['signatures_valid'] == 2
        assert signature_info['signatures_invalid'] == 0
    
    def test_print_text_results_valid(self):
        """Test printing validation results in text format for valid document."""
        details = {
            'hash_match': True,
            'current_document_hash': 'abc123',
            'expected_document_hash': 'abc123',
            'signature_verification': {
                'signatures_found': 1,
                'signatures_valid': 1
            }
        }
        
        args = argparse.Namespace(verbose=False)
        
        # Capture output
        with patch('builtins.print') as mock_print:
            self.command._print_text_results(True, details, args)
        
        # Verify output contains validation result
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("✓ VALID" in call for call in print_calls)
        assert any("✓ Match" in call for call in print_calls)
    
    def test_print_text_results_invalid(self):
        """Test printing validation results in text format for invalid document."""
        details = {
            'hash_match': False,
            'current_document_hash': 'abc123',
            'expected_document_hash': 'def456'
        }
        
        args = argparse.Namespace(verbose=False)
        
        # Capture output
        with patch('builtins.print') as mock_print:
            self.command._print_text_results(False, details, args)
        
        # Verify output contains validation result
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("✗ INVALID" in call for call in print_calls)
        assert any("✗ Mismatch" in call for call in print_calls)
        assert any("Recommendations:" in call for call in print_calls)
    
    def test_execute_document_not_found(self):
        """Test validation with non-existent document."""
        args = argparse.Namespace(
            document=Path("nonexistent.pdf"),
            audit_log=None,
            audit_dir=None,
            strict=False,
            verify_signatures=False,
            format='text',
            verbose=False
        )
        
        result = self.command.execute(args)
        assert result == 1
    
    @patch('src.gopnik.interfaces.cli.commands.validate_command.IntegrityValidator')
    def test_execute_validation_exception(self, mock_validator_class):
        """Test validation with exception during processing."""
        # Mock validator to raise exception
        mock_validator = Mock()
        mock_validator.validate_document_integrity.side_effect = Exception("Validation error")
        mock_validator_class.return_value = mock_validator
        
        args = argparse.Namespace(
            document=self.test_document,
            audit_log=self.test_audit_log,
            audit_dir=None,
            strict=False,
            verify_signatures=False,
            format='text',
            verbose=False
        )
        
        result = self.command.execute(args)
        assert result == 1


class TestValidateCommandIntegration:
    """Integration tests for validate command."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=GopnikConfig)
        self.command = ValidateCommand(self.config)
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_full_validation_workflow(self):
        """Test complete validation workflow."""
        # Create test document and audit log
        document = self.temp_dir / "document.pdf"
        document.write_text("Test document content")
        
        audit_log = self.temp_dir / "document_audit.json"
        audit_data = {
            "document_hash": "test_hash",
            "operation": "redaction",
            "timestamp": "2024-01-01T12:00:00Z",
            "signature": "test_signature"
        }
        audit_log.write_text(json.dumps(audit_data))
        
        # Mock the validator to return consistent results
        with patch('src.gopnik.interfaces.cli.commands.validate_command.IntegrityValidator') as mock_validator_class:
            mock_validator = Mock()
            mock_validator.validate_document_integrity.return_value = True
            mock_validator.generate_document_hash.return_value = "test_hash"
            mock_validator_class.return_value = mock_validator
            
            args = argparse.Namespace(
                document=document,
                audit_log=None,  # Should find it automatically
                audit_dir=None,
                strict=False,
                verify_signatures=True,
                format='json',
                verbose=True
            )
            
            # Execute validation
            with patch.object(self.command, 'print_json') as mock_print_json:
                result = self.command.execute(args)
            
            # Verify success
            assert result == 0
            mock_print_json.assert_called_once()
            
            # Verify JSON output structure
            json_output = mock_print_json.call_args[0][0]
            assert json_output['valid'] is True
            assert 'details' in json_output
            assert 'signature_verification' in json_output['details']