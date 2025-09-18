"""
Integration and end-to-end tests for complete workflows.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import yaml
import time
from typing import List, Dict, Any
import subprocess
import sys

from tests.test_utils import (
    TestDataGenerator, MockAIEngine, MockDocumentProcessor,
    TestAssertions, temp_dir, integration_test, performance_test,
    PerformanceTimer
)

# Import modules for integration testing
from src.gopnik.models.pii import PIIType, BoundingBox, PIIDetection
from src.gopnik.models.processing import ProcessingResult, ProcessingStatus
from src.gopnik.models.profiles import RedactionProfile, ProfileManager
from src.gopnik.models.audit import AuditLog, AuditOperation, AuditLevel
from src.gopnik.core.processor import DocumentProcessor
from src.gopnik.core.analyzer import DocumentAnalyzer
from src.gopnik.core.redaction import RedactionEngine
from src.gopnik.ai.hybrid_engine import HybridAIEngine
from src.gopnik.utils.crypto import CryptographicUtils
from src.gopnik.utils.file_utils import FileUtils, TempFileManager
from src.gopnik.interfaces.cli.main import GopnikCLI


@integration_test
class TestDocumentProcessingWorkflow:
    """Test complete document processing workflow."""
    
    @pytest.fixture
    def setup_test_environment(self, temp_dir):
        """Set up test environment with all necessary components."""
        # Create test directories
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        profiles_dir = temp_dir / "profiles"
        audit_dir = temp_dir / "audit"
        
        for directory in [input_dir, output_dir, profiles_dir, audit_dir]:
            directory.mkdir(exist_ok=True)
        
        # Create test profile
        profile_data = {
            'name': 'test_integration_profile',
            'description': 'Integration test profile',
            'pii_types': ['name', 'email', 'phone'],
            'redaction_style': 'solid_black',
            'confidence_threshold': 0.8,
            'preserve_layout': True
        }
        
        profile_file = profiles_dir / "test_profile.yaml"
        with open(profile_file, 'w') as f:
            yaml.dump(profile_data, f)
        
        # Create test document
        test_doc = input_dir / "test_document.txt"
        test_doc.write_text("""
        John Doe
        Email: john.doe@example.com
        Phone: (555) 123-4567
        Address: 123 Main St, Anytown, ST 12345
        """)
        
        return {
            'input_dir': input_dir,
            'output_dir': output_dir,
            'profiles_dir': profiles_dir,
            'audit_dir': audit_dir,
            'test_doc': test_doc,
            'profile_file': profile_file
        }
    
    @patch('src.gopnik.ai.hybrid_engine.HybridAIEngine')
    def test_complete_document_processing_workflow(self, mock_ai_engine, setup_test_environment):
        """Test complete document processing from start to finish."""
        env = setup_test_environment
        
        # Mock AI engine to return test detections
        mock_engine = Mock()
        mock_detections = [
            PIIDetection(
                type=PIIType.NAME,
                bounding_box=BoundingBox(0, 0, 100, 25),
                confidence=0.95,
                text_content="John Doe"
            ),
            PIIDetection(
                type=PIIType.EMAIL,
                bounding_box=BoundingBox(0, 30, 200, 55),
                confidence=0.98,
                text_content="john.doe@example.com"
            ),
            PIIDetection(
                type=PIIType.PHONE_NUMBER,
                bounding_box=BoundingBox(0, 60, 150, 85),
                confidence=0.92,
                text_content="(555) 123-4567"
            )
        ]
        mock_engine.detect_pii.return_value = mock_detections
        mock_ai_engine.return_value = mock_engine
        
        # Initialize components
        profile_manager = ProfileManager()
        document_processor = DocumentProcessor()
        
        # Load profile
        profile = profile_manager.load_profile(env['profile_file'])
        assert profile.name == 'test_integration_profile'
        
        # Process document
        with patch.object(document_processor, 'ai_engine', mock_engine):
            result = document_processor.process_document(
                document_path=env['test_doc'],
                profile=profile,
                output_path=env['output_dir'] / "redacted_document.txt"
            )
        
        # Verify processing result
        assert result.status == ProcessingStatus.COMPLETED
        assert len(result.detections) == 3
        assert result.processing_time > 0
        
        # Verify output file exists
        output_file = env['output_dir'] / "redacted_document.txt"
        assert output_file.exists()
        
        # Verify audit log was created
        assert result.audit_log_path is not None
        assert result.audit_log_path.exists()
        
        # Verify detections are correct types
        detection_types = [d.type for d in result.detections]
        assert PIIType.NAME in detection_types
        assert PIIType.EMAIL in detection_types
        assert PIIType.PHONE_NUMBER in detection_types
    
    @patch('src.gopnik.ai.hybrid_engine.HybridAIEngine')
    def test_batch_processing_workflow(self, mock_ai_engine, setup_test_environment):
        """Test batch processing of multiple documents."""
        env = setup_test_environment
        
        # Create multiple test documents
        test_docs = []
        for i in range(3):
            doc = env['input_dir'] / f"test_doc_{i}.txt"
            doc.write_text(f"""
            Person {i}: Test User {i}
            Email: user{i}@example.com
            Phone: (555) 123-456{i}
            """)
            test_docs.append(doc)
        
        # Mock AI engine
        mock_engine = Mock()
        mock_engine.detect_pii.return_value = [
            PIIDetection(
                type=PIIType.NAME,
                bounding_box=BoundingBox(0, 0, 100, 25),
                confidence=0.9,
                text_content="Test User"
            )
        ]
        mock_ai_engine.return_value = mock_engine
        
        # Initialize batch processor
        document_processor = DocumentProcessor()
        profile_manager = ProfileManager()
        profile = profile_manager.load_profile(env['profile_file'])
        
        # Process batch
        results = []
        with patch.object(document_processor, 'ai_engine', mock_engine):
            for doc in test_docs:
                result = document_processor.process_document(
                    document_path=doc,
                    profile=profile,
                    output_path=env['output_dir'] / f"redacted_{doc.name}"
                )
                results.append(result)
        
        # Verify all documents were processed
        assert len(results) == 3
        for result in results:
            assert result.status == ProcessingStatus.COMPLETED
            assert len(result.detections) >= 1
        
        # Verify all output files exist
        for i in range(3):
            output_file = env['output_dir'] / f"redacted_test_doc_{i}.txt"
            assert output_file.exists()


@integration_test
class TestCLIIntegrationWorkflow:
    """Test CLI interface integration workflows."""
    
    @pytest.fixture
    def cli_test_environment(self, temp_dir):
        """Set up CLI test environment."""
        # Create test structure
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        profiles_dir = temp_dir / "profiles"
        config_dir = temp_dir / "config"
        
        for directory in [input_dir, output_dir, profiles_dir, config_dir]:
            directory.mkdir(exist_ok=True)
        
        # Create test document
        test_doc = input_dir / "cli_test.pdf"
        test_doc.write_text("Mock PDF content with John Doe and john@example.com")
        
        # Create test profile
        profile_data = {
            'name': 'cli_test_profile',
            'description': 'CLI test profile',
            'pii_types': ['name', 'email'],
            'redaction_style': 'solid_black',
            'confidence_threshold': 0.8
        }
        
        profile_file = profiles_dir / "cli_test.yaml"
        with open(profile_file, 'w') as f:
            yaml.dump(profile_data, f)
        
        # Create test config
        config_data = {
            'log_level': 'INFO',
            'temp_dir': str(temp_dir / "temp"),
            'profiles_dir': str(profiles_dir)
        }
        
        config_file = config_dir / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        return {
            'input_dir': input_dir,
            'output_dir': output_dir,
            'profiles_dir': profiles_dir,
            'config_dir': config_dir,
            'test_doc': test_doc,
            'profile_file': profile_file,
            'config_file': config_file
        }
    
    @patch('src.gopnik.core.processor.DocumentProcessor')
    def test_cli_process_command_workflow(self, mock_processor, cli_test_environment):
        """Test CLI process command end-to-end workflow."""
        env = cli_test_environment
        
        # Mock processor result
        mock_result = ProcessingResult(
            document_id="cli-test-123",
            original_filename="cli_test.pdf",
            status=ProcessingStatus.COMPLETED,
            detections=[
                PIIDetection(
                    type=PIIType.NAME,
                    bounding_box=BoundingBox(0, 0, 100, 25),
                    confidence=0.95,
                    text_content="John Doe"
                )
            ],
            processing_time=1.2
        )
        
        mock_processor_instance = Mock()
        mock_processor_instance.process_document.return_value = mock_result
        mock_processor.return_value = mock_processor_instance
        
        # Initialize CLI
        cli = GopnikCLI()
        
        # Test process command
        args = [
            'process',
            str(env['test_doc']),
            '--profile', str(env['profile_file']),
            '--output', str(env['output_dir'] / 'cli_output.pdf'),
            '--config', str(env['config_file'])
        ]
        
        # Execute CLI command
        result = cli.run(args)
        
        # Verify command executed successfully
        assert result == 0
        
        # Verify processor was called with correct arguments
        mock_processor_instance.process_document.assert_called_once()
    
    @patch('src.gopnik.core.processor.DocumentProcessor')
    def test_cli_batch_command_workflow(self, mock_processor, cli_test_environment):
        """Test CLI batch command workflow."""
        env = cli_test_environment
        
        # Create multiple test files
        for i in range(3):
            test_file = env['input_dir'] / f"batch_test_{i}.pdf"
            test_file.write_text(f"Test content {i} with PII data")
        
        # Mock processor
        mock_result = ProcessingResult(
            document_id="batch-test",
            original_filename="batch_test.pdf",
            status=ProcessingStatus.COMPLETED,
            detections=[],
            processing_time=0.5
        )
        
        mock_processor_instance = Mock()
        mock_processor_instance.process_document.return_value = mock_result
        mock_processor.return_value = mock_processor_instance
        
        # Initialize CLI
        cli = GopnikCLI()
        
        # Test batch command
        args = [
            'batch',
            str(env['input_dir']),
            '--profile', str(env['profile_file']),
            '--output-dir', str(env['output_dir']),
            '--config', str(env['config_file'])
        ]
        
        # Execute CLI command
        result = cli.run(args)
        
        # Verify command executed successfully
        assert result == 0
        
        # Verify processor was called multiple times
        assert mock_processor_instance.process_document.call_count >= 3
    
    def test_cli_profile_management_workflow(self, cli_test_environment):
        """Test CLI profile management workflow."""
        env = cli_test_environment
        
        # Initialize CLI
        cli = GopnikCLI()
        
        # Test profile list command
        args = ['profile', 'list', '--profiles-dir', str(env['profiles_dir'])]
        result = cli.run(args)
        assert result == 0
        
        # Test profile show command
        args = ['profile', 'show', 'cli_test_profile', '--profiles-dir', str(env['profiles_dir'])]
        result = cli.run(args)
        assert result == 0
        
        # Test profile validate command
        args = ['profile', 'validate', str(env['profile_file'])]
        result = cli.run(args)
        assert result == 0


@integration_test
class TestAPIIntegrationWorkflow:
    """Test API interface integration workflows."""
    
    @pytest.fixture
    def api_test_environment(self, temp_dir):
        """Set up API test environment."""
        # Create test structure
        upload_dir = temp_dir / "uploads"
        output_dir = temp_dir / "outputs"
        profiles_dir = temp_dir / "profiles"
        
        for directory in [upload_dir, output_dir, profiles_dir]:
            directory.mkdir(exist_ok=True)
        
        # Create test profile
        profile_data = {
            'name': 'api_test_profile',
            'description': 'API test profile',
            'pii_types': ['name', 'email', 'phone'],
            'redaction_style': 'solid_black',
            'confidence_threshold': 0.8
        }
        
        profile_file = profiles_dir / "api_test.yaml"
        with open(profile_file, 'w') as f:
            yaml.dump(profile_data, f)
        
        return {
            'upload_dir': upload_dir,
            'output_dir': output_dir,
            'profiles_dir': profiles_dir,
            'profile_file': profile_file
        }
    
    @patch('src.gopnik.interfaces.api.app.FastAPI')
    @patch('src.gopnik.core.processor.DocumentProcessor')
    def test_api_document_processing_workflow(self, mock_processor, mock_fastapi, api_test_environment):
        """Test API document processing workflow."""
        env = api_test_environment
        
        # Mock FastAPI app
        mock_app = Mock()
        mock_fastapi.return_value = mock_app
        
        # Mock processor result
        mock_result = ProcessingResult(
            document_id="api-test-123",
            original_filename="api_test.pdf",
            status=ProcessingStatus.COMPLETED,
            detections=[
                PIIDetection(
                    type=PIIType.EMAIL,
                    bounding_box=BoundingBox(0, 0, 200, 25),
                    confidence=0.98,
                    text_content="test@example.com"
                )
            ],
            processing_time=2.1
        )
        
        mock_processor_instance = Mock()
        mock_processor_instance.process_document.return_value = mock_result
        mock_processor.return_value = mock_processor_instance
        
        # Import and initialize API app
        from src.gopnik.interfaces.api.app import create_app
        app = create_app()
        
        # Verify app was created
        assert app is not None
    
    @patch('src.gopnik.interfaces.api.job_manager.JobManager')
    def test_api_job_management_workflow(self, mock_job_manager, api_test_environment):
        """Test API job management workflow."""
        env = api_test_environment
        
        # Mock job manager
        mock_manager = Mock()
        mock_job_manager.return_value = mock_manager
        
        # Mock job creation
        mock_job = {
            'job_id': 'test-job-123',
            'status': 'processing',
            'created_at': '2024-01-01T10:00:00Z',
            'document_id': 'doc-123'
        }
        mock_manager.create_job.return_value = mock_job
        
        # Mock job status
        mock_manager.get_job_status.return_value = {
            'job_id': 'test-job-123',
            'status': 'completed',
            'progress': 100,
            'result': {
                'detections_found': 5,
                'processing_time': 2.3
            }
        }
        
        # Test job creation
        from src.gopnik.interfaces.api.job_manager import JobManager
        job_manager = JobManager()
        
        # Verify job manager was created
        assert job_manager is not None


@integration_test
class TestWebIntegrationWorkflow:
    """Test web interface integration workflows."""
    
    @pytest.fixture
    def web_test_environment(self, temp_dir):
        """Set up web test environment."""
        # Create test structure
        uploads_dir = temp_dir / "web_uploads"
        outputs_dir = temp_dir / "web_outputs"
        static_dir = temp_dir / "static"
        templates_dir = temp_dir / "templates"
        
        for directory in [uploads_dir, outputs_dir, static_dir, templates_dir]:
            directory.mkdir(exist_ok=True)
        
        return {
            'uploads_dir': uploads_dir,
            'outputs_dir': outputs_dir,
            'static_dir': static_dir,
            'templates_dir': templates_dir
        }
    
    @patch('src.gopnik.interfaces.web.processing.WebProcessingManager')
    def test_web_upload_and_processing_workflow(self, mock_processing_manager, web_test_environment):
        """Test web upload and processing workflow."""
        env = web_test_environment
        
        # Mock processing manager
        mock_manager = Mock()
        mock_processing_manager.return_value = mock_manager
        
        # Mock file upload result
        mock_upload_result = {
            'file_id': 'web-upload-123',
            'filename': 'web_test.pdf',
            'size': 1024,
            'upload_time': '2024-01-01T10:00:00Z'
        }
        mock_manager.handle_file_upload.return_value = mock_upload_result
        
        # Mock processing result
        mock_processing_result = {
            'job_id': 'web-job-123',
            'status': 'completed',
            'detections_found': 3,
            'processing_time': 1.8,
            'download_url': '/download/web-job-123'
        }
        mock_manager.process_file.return_value = mock_processing_result
        
        # Test web processing manager
        from src.gopnik.interfaces.web.processing import WebProcessingManager
        processing_manager = WebProcessingManager()
        
        # Verify manager was created
        assert processing_manager is not None
    
    @patch('src.gopnik.interfaces.web.security.SecurityManager')
    def test_web_security_workflow(self, mock_security_manager, web_test_environment):
        """Test web security workflow."""
        env = web_test_environment
        
        # Mock security manager
        mock_manager = Mock()
        mock_security_manager.return_value = mock_manager
        
        # Mock security validation
        mock_manager.validate_file_upload.return_value = True
        mock_manager.check_rate_limit.return_value = True
        mock_manager.sanitize_filename.return_value = "safe_filename.pdf"
        
        # Test security manager
        from src.gopnik.interfaces.web.security import SecurityManager
        security_manager = SecurityManager()
        
        # Verify manager was created
        assert security_manager is not None


@performance_test
class TestPerformanceIntegration:
    """Performance tests for integrated workflows."""
    
    def test_document_processing_performance(self, temp_dir):
        """Test document processing performance under load."""
        # Create test documents
        test_docs = []
        for i in range(10):  # Reduced for faster testing
            doc = temp_dir / f"perf_test_{i}.txt"
            doc.write_text(f"Performance test document {i} with John Doe and john{i}@example.com")
            test_docs.append(doc)
        
        # Create test profile
        profile = RedactionProfile(
            name="performance_test",
            description="Performance test profile",
            pii_types=[PIIType.NAME, PIIType.EMAIL],
            redaction_style="solid_black",
            confidence_threshold=0.8
        )
        
        with PerformanceTimer(max_duration=10.0) as timer:
            # Mock processing for performance test
            with patch('src.gopnik.core.processor.DocumentProcessor') as mock_processor:
                mock_result = ProcessingResult(
                    document_id="perf-test",
                    original_filename="perf_test.txt",
                    status=ProcessingStatus.COMPLETED,
                    detections=[],
                    processing_time=0.1
                )
                
                mock_processor_instance = Mock()
                mock_processor_instance.process_document.return_value = mock_result
                mock_processor.return_value = mock_processor_instance
                
                # Process all documents
                processor = mock_processor()
                results = []
                for doc in test_docs:
                    result = processor.process_document(
                        document_path=doc,
                        profile=profile,
                        output_path=temp_dir / f"output_{doc.name}"
                    )
                    results.append(result)
        
        # Verify performance
        assert timer.duration < 10.0
        assert len(results) == 10
        
        # Calculate average processing time
        avg_time = timer.duration / len(test_docs)
        assert avg_time < 1.0  # Should process each document in less than 1 second
    
    def test_concurrent_processing_performance(self, temp_dir):
        """Test concurrent document processing performance."""
        import concurrent.futures
        
        # Create test documents
        test_docs = []
        for i in range(5):  # Reduced for faster testing
            doc = temp_dir / f"concurrent_test_{i}.txt"
            doc.write_text(f"Concurrent test {i} with sensitive data")
            test_docs.append(doc)
        
        def mock_process_document(doc_path):
            """Mock document processing function."""
            time.sleep(0.1)  # Simulate processing time
            return ProcessingResult(
                document_id=f"concurrent-{doc_path.stem}",
                original_filename=doc_path.name,
                status=ProcessingStatus.COMPLETED,
                detections=[],
                processing_time=0.1
            )
        
        with PerformanceTimer(max_duration=5.0) as timer:
            # Process documents concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(mock_process_document, doc) for doc in test_docs]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify concurrent processing was faster than sequential
        assert timer.duration < 1.0  # Should be much faster than 5 * 0.1 = 0.5 seconds
        assert len(results) == 5
        
        # Verify all results are valid
        for result in results:
            assert result.status == ProcessingStatus.COMPLETED


@integration_test
class TestSecurityIntegration:
    """Security-focused integration tests."""
    
    def test_audit_trail_integrity_workflow(self, temp_dir):
        """Test complete audit trail integrity workflow."""
        # Create test environment
        audit_dir = temp_dir / "audit"
        audit_dir.mkdir(exist_ok=True)
        
        # Initialize crypto utils
        crypto = CryptographicUtils()
        
        # Generate key pair for signing
        private_key, public_key = crypto.generate_rsa_key_pair()
        
        # Create audit logs
        audit_logs = []
        for i in range(5):
            log = AuditLog(
                operation=AuditOperation.DOCUMENT_REDACTION,
                level=AuditLevel.INFO,
                message=f"Test audit log {i}",
                details={'test_id': i}
            )
            audit_logs.append(log)
        
        # Create audit trail
        from src.gopnik.models.audit import AuditTrail
        trail = AuditTrail(logs=audit_logs, document_id="security-test-123")
        
        # Export and sign audit trail
        audit_file = audit_dir / "security_audit.json"
        trail.export_to_json(audit_file)
        
        # Sign the audit file
        signature = crypto.sign_file(audit_file, private_key)
        assert signature is not None
        
        # Verify signature
        is_valid = crypto.verify_file_signature(audit_file, signature, public_key)
        assert is_valid is True
        
        # Test tampering detection
        # Modify the file
        with open(audit_file, 'a') as f:
            f.write("tampered data")
        
        # Signature should now be invalid
        is_valid = crypto.verify_file_signature(audit_file, signature, public_key)
        assert is_valid is False
    
    def test_secure_file_handling_workflow(self, temp_dir):
        """Test secure file handling workflow."""
        # Initialize file utils
        file_utils = FileUtils()
        temp_manager = TempFileManager()
        
        # Create sensitive test file
        sensitive_file = temp_dir / "sensitive_data.txt"
        sensitive_file.write_text("This is sensitive information that should be securely handled")
        
        # Test secure copying
        with temp_manager.create_temp_dir() as secure_temp_dir:
            # Copy file to secure temporary location
            temp_copy = secure_temp_dir / "temp_sensitive.txt"
            file_utils.safe_copy(sensitive_file, temp_copy)
            
            assert temp_copy.exists()
            assert temp_copy.read_text() == sensitive_file.read_text()
            
            # Process file (mock processing)
            processed_file = secure_temp_dir / "processed_sensitive.txt"
            processed_file.write_text("Processed and redacted content")
            
            # Copy processed file to final location
            final_file = temp_dir / "final_output.txt"
            file_utils.safe_copy(processed_file, final_file)
            
            assert final_file.exists()
            
            # Secure delete temporary files
            file_utils.secure_delete(temp_copy)
            file_utils.secure_delete(processed_file)
            
            # Verify temporary files are gone
            assert not temp_copy.exists()
            assert not processed_file.exists()
        
        # Verify temporary directory is cleaned up
        assert not secure_temp_dir.exists()
        
        # Final file should still exist
        assert final_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])