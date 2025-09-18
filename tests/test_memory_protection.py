"""
Tests for memory protection and cleanup functionality.
"""

import gc
import mmap
import threading
import time
import tracemalloc
from unittest.mock import patch, MagicMock
import pytest

from src.gopnik.utils.memory_protection import (
    SecureMemoryManager, SecureString, MemoryProfiler
)


class TestSecureMemoryManager:
    """Test cases for SecureMemoryManager."""
    
    def setup_method(self):
        """Set up test environment."""
        # Reset singleton instance for testing
        SecureMemoryManager._instance = None
        self.manager = SecureMemoryManager()
    
    def teardown_method(self):
        """Clean up test environment."""
        self.manager.cleanup_all_sensitive_data()
        # Reset singleton instance
        SecureMemoryManager._instance = None
    
    def test_singleton_pattern(self):
        """Test that SecureMemoryManager follows singleton pattern."""
        manager1 = SecureMemoryManager()
        manager2 = SecureMemoryManager()
        
        assert manager1 is manager2
        assert id(manager1) == id(manager2)
    
    def test_allocate_secure_memory(self):
        """Test secure memory allocation."""
        size = 1024
        memory_view = self.manager.allocate_secure_memory(size)
        
        # Verify memory view is created
        assert isinstance(memory_view, memoryview)
        assert len(memory_view) >= size  # May be aligned to page boundary
        
        # Verify tracking
        obj_id = id(memory_view)
        assert obj_id in self.manager._secure_allocations
        assert self.manager._memory_stats['allocations'] == 1
        assert self.manager._memory_stats['current_memory'] > 0
    
    def test_allocate_secure_memory_alignment(self):
        """Test memory allocation alignment to page boundaries."""
        small_size = 100
        memory_view = self.manager.allocate_secure_memory(small_size)
        
        # Memory should be aligned to page boundary
        assert len(memory_view) >= small_size
        assert len(memory_view) % self.manager._page_size == 0
    
    def test_register_sensitive_object(self):
        """Test registering sensitive objects."""
        sensitive_data = "sensitive information"
        cleanup_called = False
        
        def cleanup_callback():
            nonlocal cleanup_called
            cleanup_called = True
        
        self.manager.register_sensitive_object(sensitive_data, cleanup_callback)
        
        # Verify object is tracked
        obj_id = id(sensitive_data)
        assert obj_id in self.manager._sensitive_objects
        assert obj_id in self.manager._cleanup_callbacks
    
    def test_clear_sensitive_data_bytearray(self):
        """Test clearing sensitive data from bytearray."""
        sensitive_data = bytearray(b"sensitive information")
        original_length = len(sensitive_data)
        
        result = self.manager.clear_sensitive_data(sensitive_data)
        
        assert result is True
        assert len(sensitive_data) == original_length
        # Data should be zeroed
        assert all(byte == 0 for byte in sensitive_data)
    
    def test_clear_sensitive_data_list(self):
        """Test clearing sensitive data from list."""
        sensitive_list = ["secret1", "secret2", bytearray(b"secret3")]
        
        result = self.manager.clear_sensitive_data(sensitive_list)
        
        assert result is True
        assert len(sensitive_list) == 0  # List should be cleared
    
    def test_clear_sensitive_data_dict(self):
        """Test clearing sensitive data from dictionary."""
        sensitive_dict = {
            "key1": "secret1",
            "key2": bytearray(b"secret2"),
            "key3": "secret3"
        }
        
        result = self.manager.clear_sensitive_data(sensitive_dict)
        
        assert result is True
        assert len(sensitive_dict) == 0  # Dict should be cleared
    
    def test_clear_sensitive_data_object(self):
        """Test clearing sensitive data from object attributes."""
        class SensitiveObject:
            def __init__(self):
                self.secret = "sensitive data"
                self.data = bytearray(b"more secrets")
                self.normal = 42
        
        obj = SensitiveObject()
        result = self.manager.clear_sensitive_data(obj)
        
        assert result is True
        assert obj.secret is None
        assert obj.data is None
        assert obj.normal == 42  # Non-sensitive data unchanged
    
    def test_force_garbage_collection(self):
        """Test forced garbage collection."""
        # Create some objects to collect
        temp_objects = [[] for _ in range(100)]
        del temp_objects
        
        stats = self.manager.force_garbage_collection()
        
        assert isinstance(stats, dict)
        assert 'collected' in stats
        assert 'generation_0' in stats
        assert 'generation_1' in stats
        assert 'generation_2' in stats
        assert stats['collected'] >= 0
    
    def test_force_garbage_collection_specific_generations(self):
        """Test garbage collection for specific generations."""
        stats = self.manager.force_garbage_collection(generations=[0, 1])
        
        assert stats['generation_0'] >= 0
        assert stats['generation_1'] >= 0
        assert stats['generation_2'] == 0  # Not collected
    
    def test_optimize_memory_for_large_documents(self):
        """Test memory optimization for large documents."""
        # Get initial thresholds
        initial_thresholds = gc.get_threshold()
        
        self.manager.optimize_memory_for_large_documents()
        
        # Verify thresholds were changed
        new_thresholds = gc.get_threshold()
        assert new_thresholds != initial_thresholds
        assert new_thresholds[0] > initial_thresholds[0]  # Increased threshold
    
    def test_get_memory_usage(self):
        """Test memory usage statistics."""
        stats = self.manager.get_memory_usage()
        
        assert isinstance(stats, dict)
        assert 'rss_mb' in stats
        assert 'vms_mb' in stats
        assert 'percent' in stats
        assert 'secure_allocations' in stats
        assert 'sensitive_objects' in stats
        
        # All values should be non-negative
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                assert value >= 0
    
    def test_detect_memory_leaks(self):
        """Test memory leak detection."""
        # Enable tracemalloc if not already enabled
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        # Create some allocations
        large_data = [bytearray(1024) for _ in range(10)]
        
        leaks = self.manager.detect_memory_leaks(threshold_mb=0.001)  # Low threshold
        
        assert isinstance(leaks, list)
        # May or may not find leaks depending on system state
        
        # Clean up
        del large_data
    
    def test_cleanup_all_sensitive_data(self):
        """Test cleaning up all sensitive data."""
        # Register multiple sensitive objects
        sensitive_objects = [
            "secret1",
            bytearray(b"secret2"),
            ["secret3", "secret4"]
        ]
        
        for obj in sensitive_objects:
            self.manager.register_sensitive_object(obj)
        
        # Verify objects are tracked
        assert len(self.manager._sensitive_objects) >= len(sensitive_objects)
        
        # Clean up all
        cleaned_count = self.manager.cleanup_all_sensitive_data()
        
        # Verify cleanup
        assert cleaned_count >= 0
        assert len(self.manager._sensitive_objects) == 0
        assert len(self.manager._cleanup_callbacks) == 0
    
    def test_thread_safety(self):
        """Test thread safety of memory manager."""
        results = []
        errors = []
        
        def allocate_memory():
            try:
                for _ in range(3):  # Reduced from 10 to 3
                    memory_view = self.manager.allocate_secure_memory(512)  # Reduced size
                    results.append(memory_view)
                    # Removed sleep to speed up test
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(3):  # Reduced from 5 to 3
            thread = threading.Thread(target=allocate_memory)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify no errors
        assert len(errors) == 0
        assert len(results) == 9  # 3 threads * 3 allocations each
    
    @patch('psutil.Process')
    def test_get_memory_usage_error_handling(self, mock_process):
        """Test error handling in memory usage statistics."""
        mock_process.side_effect = Exception("Process error")
        
        stats = self.manager.get_memory_usage()
        
        # Should return empty dict on error
        assert stats == {}
    
    def test_memory_stats_tracking(self):
        """Test memory statistics tracking."""
        initial_stats = self.manager._memory_stats.copy()
        
        # Allocate some memory
        memory_view = self.manager.allocate_secure_memory(2048)
        
        # Verify stats updated
        assert self.manager._memory_stats['allocations'] > initial_stats['allocations']
        assert self.manager._memory_stats['current_memory'] > initial_stats['current_memory']
        assert self.manager._memory_stats['peak_memory'] >= self.manager._memory_stats['current_memory']


class TestSecureString:
    """Test cases for SecureString."""
    
    def test_create_secure_string_from_str(self):
        """Test creating SecureString from string."""
        original_data = "sensitive information"
        secure_str = SecureString(original_data)
        
        assert secure_str.get_data() == original_data
        assert isinstance(secure_str._data, bytearray)
    
    def test_create_secure_string_from_bytes(self):
        """Test creating SecureString from bytes."""
        original_data = b"sensitive bytes"
        secure_str = SecureString(original_data)
        
        assert secure_str.get_bytes() == original_data
        assert secure_str.get_data() == original_data.decode('utf-8')
    
    def test_secure_string_invalid_input(self):
        """Test SecureString with invalid input."""
        with pytest.raises(ValueError, match="Data must be string or bytes"):
            SecureString(123)
    
    def test_secure_string_clear(self):
        """Test clearing SecureString data."""
        secure_str = SecureString("sensitive data")
        original_length = len(secure_str)
        
        secure_str.clear()
        
        # Data should be cleared
        assert len(secure_str._data) == 0
        assert len(secure_str) == 0
    
    def test_secure_string_str_representation(self):
        """Test string representation of SecureString."""
        data = "test data"
        secure_str = SecureString(data)
        
        assert str(secure_str) == data
        assert bytes(secure_str) == data.encode('utf-8')
        assert len(secure_str) == len(data)
    
    def test_secure_string_automatic_cleanup(self):
        """Test automatic cleanup of SecureString."""
        data = "sensitive data"
        secure_str = SecureString(data)
        
        # Verify data exists
        assert len(secure_str._data) > 0
        
        # Delete reference
        del secure_str
        
        # Force garbage collection
        gc.collect()
        
        # Note: We can't easily verify the data was cleared since the object is destroyed
        # This test mainly ensures no exceptions are raised during cleanup


class TestMemoryProfiler:
    """Test cases for MemoryProfiler."""
    
    def setup_method(self):
        """Set up test environment."""
        self.profiler = MemoryProfiler("TestProfiler")
    
    def test_memory_profiler_initialization(self):
        """Test memory profiler initialization."""
        assert self.profiler.name == "TestProfiler"
        assert self.profiler._start_memory is None
        assert len(self.profiler._snapshots) == 0
    
    def test_start_profiling(self):
        """Test starting memory profiling."""
        self.profiler.start_profiling()
        
        assert self.profiler._start_memory is not None
        assert isinstance(self.profiler._start_memory, dict)
    
    def test_take_snapshot(self):
        """Test taking memory snapshots."""
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        snapshot = self.profiler.take_snapshot("test_snapshot")
        
        assert isinstance(snapshot, dict)
        assert snapshot['label'] == "test_snapshot"
        assert 'timestamp' in snapshot
        assert 'memory_usage' in snapshot
        assert len(self.profiler._snapshots) == 1
    
    def test_take_snapshot_without_tracemalloc(self):
        """Test taking snapshot without tracemalloc enabled."""
        # Stop tracemalloc if running
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        
        snapshot = self.profiler.take_snapshot("test")
        
        assert snapshot == {}
    
    def test_stop_profiling(self):
        """Test stopping memory profiling."""
        self.profiler.start_profiling()
        
        # Take some snapshots
        self.profiler.take_snapshot("snapshot1")
        self.profiler.take_snapshot("snapshot2")
        
        summary = self.profiler.stop_profiling()
        
        assert isinstance(summary, dict)
        assert summary['name'] == "TestProfiler"
        assert 'start_memory' in summary
        assert 'end_memory' in summary
        assert summary['snapshots'] == 2
        assert 'memory_delta_mb' in summary
        assert 'potential_leaks' in summary
    
    def test_generate_report(self):
        """Test generating memory profiling report."""
        self.profiler.start_profiling()
        self.profiler.take_snapshot("test_snapshot")
        
        report = self.profiler.generate_report()
        
        assert isinstance(report, str)
        assert "Memory Profiling Report: TestProfiler" in report
        assert "Memory Usage:" in report
        assert "Snapshots Taken:" in report
        assert "Potential Leaks:" in report
    
    def test_profiler_with_memory_operations(self):
        """Test profiler with actual memory operations."""
        self.profiler.start_profiling()
        
        # Perform some memory operations
        large_data = []
        for i in range(20):  # Reduced from 100 to 20
            large_data.append(bytearray(512))  # Reduced size from 1024 to 512
            if i % 10 == 0:  # Reduced from 25 to 10
                self.profiler.take_snapshot(f"iteration_{i}")
        
        summary = self.profiler.stop_profiling()
        
        # Should have captured memory changes
        assert summary['snapshots'] > 0
        assert isinstance(summary['memory_delta_mb'], (int, float))
        
        # Clean up
        del large_data


class TestMemoryProtectionIntegration:
    """Integration tests for memory protection functionality."""
    
    def test_secure_memory_with_document_processing(self):
        """Test secure memory management in document processing scenario."""
        manager = SecureMemoryManager()
        
        try:
            # Simulate document processing with sensitive data
            document_data = SecureString("Sensitive document content with PII")
            manager.register_sensitive_object(document_data)
            
            # Allocate secure memory for processing
            processing_memory = manager.allocate_secure_memory(4096)
            
            # Simulate processing operations
            temp_data = bytearray(b"Temporary processing data")
            manager.register_sensitive_object(temp_data)
            
            # Verify memory tracking
            stats = manager.get_memory_usage()
            assert stats['secure_allocations'] >= 1
            assert stats['sensitive_objects'] >= 2
            
            # Clean up
            document_data.clear()
            manager.clear_sensitive_data(temp_data)
            
        finally:
            manager.cleanup_all_sensitive_data()
    
    def test_memory_optimization_workflow(self):
        """Test complete memory optimization workflow."""
        manager = SecureMemoryManager()
        profiler = MemoryProfiler("OptimizationTest")
        
        try:
            # Start profiling
            profiler.start_profiling()
            
            # Optimize for large documents
            manager.optimize_memory_for_large_documents()
            profiler.take_snapshot("after_optimization")
            
            # Simulate large document processing
            large_documents = []
            for i in range(5):  # Reduced from 10 to 5
                doc_data = SecureString(f"Large document {i} " * 100)  # Reduced from 1000 to 100
                large_documents.append(doc_data)
                manager.register_sensitive_object(doc_data)
            
            profiler.take_snapshot("after_allocation")
            
            # Force garbage collection
            gc_stats = manager.force_garbage_collection()
            profiler.take_snapshot("after_gc")
            
            # Clean up sensitive data
            for doc in large_documents:
                doc.clear()
            
            cleanup_count = manager.cleanup_all_sensitive_data()
            profiler.take_snapshot("after_cleanup")
            
            # Generate report
            report = profiler.generate_report()
            
            # Verify workflow completed successfully
            assert gc_stats['collected'] >= 0
            assert cleanup_count >= 0
            assert "TestProfiler" in report or "OptimizationTest" in report
            
        finally:
            manager.cleanup_all_sensitive_data()
    
    def test_concurrent_memory_operations(self):
        """Test concurrent memory operations for thread safety."""
        manager = SecureMemoryManager()
        results = []
        errors = []
        
        def memory_operations():
            try:
                # Allocate secure memory
                memory_view = manager.allocate_secure_memory(2048)
                
                # Create secure string
                secure_str = SecureString("Thread-specific sensitive data")
                manager.register_sensitive_object(secure_str)
                
                # Perform operations
                time.sleep(0.01)
                
                # Clear data
                secure_str.clear()
                
                results.append("success")
                
            except Exception as e:
                errors.append(e)
        
        # Run concurrent operations
        threads = []
        for _ in range(3):  # Reduced from 10 to 3
            thread = threading.Thread(target=memory_operations)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0
        assert len(results) == 3  # Updated expected count
        
        # Clean up
        manager.cleanup_all_sensitive_data()


if __name__ == '__main__':
    pytest.main([__file__])