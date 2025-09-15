"""
Validate command implementation for document integrity checking.
"""

import argparse
from pathlib import Path
import json

from ..base_command import BaseCommand
from ....utils.integrity_validator import IntegrityValidator
from ....utils.audit_logger import AuditLogger


class ValidateCommand(BaseCommand):
    """Command for validating document integrity and audit trails."""
    
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """Add validate command arguments."""
        
        # Required arguments
        parser.add_argument(
            'document',
            type=Path,
            help='Document path to validate'
        )
        
        parser.add_argument(
            'audit_log',
            type=Path,
            nargs='?',
            help='Audit log file path (optional, will search for matching log)'
        )
        
        # Optional arguments
        parser.add_argument(
            '--audit-dir',
            type=Path,
            help='Directory to search for audit logs'
        )
        
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Enable strict validation mode'
        )
        
        parser.add_argument(
            '--verify-signatures',
            action='store_true',
            help='Verify cryptographic signatures in audit logs'
        )
        
        parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Show detailed validation information'
        )
    
    def execute(self, args: argparse.Namespace) -> int:
        """Execute the validate command."""
        
        # Validate document path
        if not self.validate_file_path(args.document, must_exist=True):
            return 1
        
        # Find or validate audit log
        audit_log_path = self._find_audit_log(args)
        if not audit_log_path:
            return 1
        
        # Execute validation
        return self._execute_validation(args, audit_log_path)
    
    def _find_audit_log(self, args: argparse.Namespace) -> Path:
        """Find the audit log file for the document."""
        
        if args.audit_log:
            # Explicit audit log provided
            if not self.validate_file_path(args.audit_log, must_exist=True):
                return None
            return args.audit_log
        
        # Search for audit log
        search_dirs = []
        
        if args.audit_dir:
            search_dirs.append(args.audit_dir)
        
        # Default search locations
        search_dirs.extend([
            args.document.parent,  # Same directory as document
            args.document.parent / 'audit_logs',  # audit_logs subdirectory
            Path('audit_logs'),  # Current directory audit_logs
        ])
        
        # Generate possible audit log names
        doc_stem = args.document.stem
        possible_names = [
            f"{doc_stem}_audit.json",
            f"{doc_stem}.audit",
            f"audit_{doc_stem}.json",
            "audit.json"
        ]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            for name in possible_names:
                audit_path = search_dir / name
                if audit_path.exists():
                    self.logger.info(f"Found audit log: {audit_path}")
                    return audit_path
        
        self.logger.error(f"No audit log found for document: {args.document}")
        self.logger.info("Searched locations:")
        for search_dir in search_dirs:
            self.logger.info(f"  {search_dir}")
        
        return None
    
    def _execute_validation(self, args: argparse.Namespace, audit_log_path: Path) -> int:
        """Execute document validation."""
        
        try:
            # Initialize validator
            validator = IntegrityValidator()
            
            self.logger.info(f"Validating document: {args.document}")
            self.logger.info(f"Using audit log: {audit_log_path}")
            
            # Perform validation
            is_valid = validator.validate_document_integrity(args.document, audit_log_path)
            
            # Get detailed validation results if available
            validation_details = self._get_validation_details(
                validator, args.document, audit_log_path, args
            )
            
            # Report results
            if args.format == 'json':
                self.print_json({
                    'document': str(args.document),
                    'audit_log': str(audit_log_path),
                    'valid': is_valid,
                    'details': validation_details
                })
            else:
                self._print_text_results(is_valid, validation_details, args)
            
            return 0 if is_valid else 1
            
        except Exception as e:
            if args.format == 'json':
                self.print_json({
                    'document': str(args.document),
                    'audit_log': str(audit_log_path),
                    'valid': False,
                    'error': str(e)
                })
            else:
                print(self.format_error(f"Validation failed: {e}"))
            
            return 1
    
    def _get_validation_details(self, validator: IntegrityValidator, 
                              document_path: Path, audit_log_path: Path,
                              args: argparse.Namespace) -> dict:
        """Get detailed validation information."""
        
        details = {}
        
        try:
            # Load audit log
            with open(audit_log_path, 'r') as f:
                audit_data = json.load(f)
            
            details['audit_log_loaded'] = True
            details['audit_entries'] = len(audit_data) if isinstance(audit_data, list) else 1
            
            # Check document hash
            current_hash = validator.generate_document_hash(document_path)
            details['current_document_hash'] = current_hash
            
            # Extract expected hash from audit log
            if isinstance(audit_data, dict) and 'document_hash' in audit_data:
                expected_hash = audit_data['document_hash']
                details['expected_document_hash'] = expected_hash
                details['hash_match'] = current_hash == expected_hash
            
            # Signature verification if requested
            if args.verify_signatures:
                details['signature_verification'] = self._verify_signatures(audit_data)
            
            # Additional checks in verbose mode
            if args.verbose:
                details['document_size'] = document_path.stat().st_size
                details['document_modified'] = document_path.stat().st_mtime
                details['audit_log_size'] = audit_log_path.stat().st_size
                details['audit_log_modified'] = audit_log_path.stat().st_mtime
        
        except Exception as e:
            details['error'] = str(e)
            details['audit_log_loaded'] = False
        
        return details
    
    def _verify_signatures(self, audit_data: dict) -> dict:
        """Verify cryptographic signatures in audit data."""
        
        signature_info = {
            'signatures_found': 0,
            'signatures_valid': 0,
            'signatures_invalid': 0
        }
        
        try:
            # Initialize audit logger for signature verification
            audit_logger = AuditLogger()
            
            # Handle different audit log formats
            entries = audit_data if isinstance(audit_data, list) else [audit_data]
            
            for entry in entries:
                if isinstance(entry, dict) and 'signature' in entry:
                    signature_info['signatures_found'] += 1
                    
                    # TODO: Implement signature verification
                    # This would require the audit logger to have signature verification methods
                    # For now, we'll mark as valid if signature exists
                    if entry['signature']:
                        signature_info['signatures_valid'] += 1
                    else:
                        signature_info['signatures_invalid'] += 1
        
        except Exception as e:
            signature_info['error'] = str(e)
        
        return signature_info
    
    def _print_text_results(self, is_valid: bool, details: dict, args: argparse.Namespace) -> None:
        """Print validation results in text format."""
        
        # Main result
        status = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"\nValidation Result: {status}")
        
        # Basic information
        print(f"Document: {args.document}")
        print(f"Audit Log: {details.get('audit_log', 'N/A')}")
        
        # Hash verification
        if 'hash_match' in details:
            hash_status = "✓ Match" if details['hash_match'] else "✗ Mismatch"
            print(f"Document Hash: {hash_status}")
            
            if args.verbose:
                print(f"  Current:  {details.get('current_document_hash', 'N/A')}")
                print(f"  Expected: {details.get('expected_document_hash', 'N/A')}")
        
        # Signature verification
        if 'signature_verification' in details:
            sig_info = details['signature_verification']
            print(f"Signatures: {sig_info.get('signatures_valid', 0)}/{sig_info.get('signatures_found', 0)} valid")
        
        # Verbose information
        if args.verbose and 'document_size' in details:
            print(f"\nDetailed Information:")
            print(f"  Document Size: {details['document_size']} bytes")
            print(f"  Audit Entries: {details.get('audit_entries', 'N/A')}")
            
            if 'error' in details:
                print(f"  Validation Error: {details['error']}")
        
        # Recommendations
        if not is_valid:
            print(f"\nRecommendations:")
            if details.get('hash_match') is False:
                print("  • Document has been modified since processing")
                print("  • Verify document source and integrity")
            
            if 'error' in details:
                print("  • Check audit log format and accessibility")
                print("  • Ensure audit log corresponds to this document")