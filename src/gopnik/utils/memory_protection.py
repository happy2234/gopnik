"""
Memory protection and cleanup utilities for sensitive data handling.
"""

import gc
import mmap
import os
import sys
import threading
import weakref
from typing import Any, Dict, List, Optional, Set, Union, Callable
import logging
import ctypes
from ctypes import c_void_p, c_size_t
import psutil
import tracemalloc

from .crypto import CryptographicUtils


class SecureMemoryManager:
    """
    Secure memory manager for handling sensitive data in memory.
    
    Features:
    - Secure memory allocation and deallocation
    - Automatic sensitive data clearing
    - Memory leak detection and prevention
    - Garbage collection optimization
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for memory manager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize secure memory manager."""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.logger = logging.getLogger(__name__)
        self._sensitive_objects: Set[int] = set()
        self._secure_allocations: Dict[int, int] = {}  # object_id -> size
        self._cleanup_callbacks: Dict[int, Callable] = {}
        self._memory_stats = {
            'allocations': 0,
            'deallocations': 0,
            'peak_memory': 0,
            'current_memory': 0
        }
        
        # Enable tracemalloc for memory tracking
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        # Get system page size for memory alignment
        self._page_size = os.sysconf(os.sysconf_names['SC_PAGE_SIZE'])
        
        # Initialize crypto utils for secure random data
        self._crypto_utils = CryptographicUtils()
        
        self.logger.info("SecureMemoryManager initialized")
    
    def allocate_secure_memory(self, size: int, zero_on_free: bool = True) -> memoryview:
        """
        Allocate secure memory region.
        
        Args:
            size: Size in bytes to allocate
            zero_on_free: Whether to zero memory on deallocation
            
        Returns:
            Memory view of allocated secure memory
        """
        try:
            # Align size to page boundary for better security
            aligned_size = ((size + self._page_size - 1) // self._page_size) * self._page_size
            
            # Allocate memory using mmap for better control
            memory_map = mmap.mmap(-1, aligned_size, mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS)
            
            # Lock memory to prevent swapping (if supported)
            try:
                memory_map.mlock()
            except (OSError, AttributeError):
                self.logger.warning("Memory locking not supported on this system")
            
            # Create memory view
            memory_view = memoryview(memory_map)
            
            # Track allocation
            obj_id = id(memory_view)
            self._secure_allocations[obj_id] = aligned_size
            self._memory_stats['allocations'] += 1
            self._memory_stats['current_memory'] += aligned_size
            self._memory_stats['peak_memory'] = max(
                self._memory_stats['peak_memory'],
                self._memory_stats['current_memory']
            )
            
            # Register cleanup callback
            if zero_on_free:
                def cleanup_callback():
                    try:
                        self._secure_zero_memory(memory_map, aligned_size)
                        memory_map.close()
                    except Exception as e:
                        self.logger.error(f"Error in memory cleanup: {e}")
                
                self._cleanup_callbacks[obj_id] = cleanup_callback
                try:
                    weakref.finalize(memory_view, self._cleanup_secure_allocation, obj_id)
                except TypeError:
                    # If weak reference fails, we'll rely on manual cleanup
                    pass
            
            self.logger.debug(f"Allocated {aligned_size} bytes of secure memory")
            return memory_view
            
        except Exception as e:
            self.logger.error(f"Failed to allocate secure memory: {e}")
            raise RuntimeError(f"Secure memory allocation failed: {e}")
    
    def register_sensitive_object(self, obj: Any, cleanup_callback: Optional[Callable] = None) -> None:
        """
        Register an object as containing sensitive data.
        
        Args:
            obj: Object containing sensitive data
            cleanup_callback: Optional cleanup function to call when object is destroyed
        """
        obj_id = id(obj)
        self._sensitive_objects.add(obj_id)
        
        if cleanup_callback:
            self._cleanup_callbacks[obj_id] = cleanup_callback
        
        # Register finalizer for automatic cleanup (only for objects that support weak references)
        try:
            weakref.finalize(obj, self._cleanup_sensitive_object, obj_id)
        except TypeError:
            # Some objects (str, int, bytearray) don't support weak references
            # We'll rely on manual cleanup for these
            self.logger.debug(f"Object {obj_id} doesn't support weak references, manual cleanup required")
        
        self.logger.debug(f"Registered sensitive object {obj_id}")
    
    def clear_sensitive_data(self, obj: Any) -> bool:
        """
        Clear sensitive data from an object.
        
        Args:
            obj: Object to clear
            
        Returns:
            True if clearing was successful
        """
        try:
            obj_id = id(obj)
            
            # Handle different object types
            if isinstance(obj, (str, bytes)):
                # For immutable types, we can't clear in place
                # But we can overwrite the reference
                self._overwrite_immutable_reference(obj)
                
            elif isinstance(obj, bytearray):
                # Clear mutable byte array
                self._secure_zero_bytes(obj)
                
            elif isinstance(obj, memoryview):
                # Clear memory view
                if not obj.readonly:
                    self._secure_zero_bytes(obj)
                
            elif isinstance(obj, list):
                # Clear list contents
                for i in range(len(obj)):
                    if isinstance(obj[i], (str, bytes, bytearray)):
                        self.clear_sensitive_data(obj[i])
                obj.clear()
                
            elif isinstance(obj, dict):
                # Clear dictionary contents
                for key, value in list(obj.items()):
                    if isinstance(value, (str, bytes, bytearray)):
                        self.clear_sensitive_data(value)
                obj.clear()
                
            elif hasattr(obj, '__dict__'):
                # Clear object attributes
                for attr_name, attr_value in list(obj.__dict__.items()):
                    if isinstance(attr_value, (str, bytes, bytearray)):
                        self.clear_sensitive_data(attr_value)
                        setattr(obj, attr_name, None)
            
            # Remove from sensitive objects tracking
            if obj_id in self._sensitive_objects:
                self._sensitive_objects.remove(obj_id)
            
            self.logger.debug(f"Cleared sensitive data from object {obj_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear sensitive data: {e}")
            return False
    
    def force_garbage_collection(self, generations: Optional[List[int]] = None) -> Dict[str, int]:
        """
        Force garbage collection with optional generation specification.
        
        Args:
            generations: List of generations to collect (default: all)
            
        Returns:
            Dictionary with collection statistics
        """
        stats = {
            'collected': 0,
            'uncollectable': 0,
            'generation_0': 0,
            'generation_1': 0,
            'generation_2': 0
        }
        
        try:
            if generations is None:
                # Collect all generations
                for gen in range(3):
                    collected = gc.collect(gen)
                    stats[f'generation_{gen}'] = collected
                    stats['collected'] += collected
            else:
                # Collect specified generations
                for gen in generations:
                    if 0 <= gen <= 2:
                        collected = gc.collect(gen)
                        stats[f'generation_{gen}'] = collected
                        stats['collected'] += collected
            
            # Get uncollectable objects count
            stats['uncollectable'] = len(gc.garbage)
            
            self.logger.debug(f"Garbage collection completed: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Garbage collection failed: {e}")
            return stats
    
    def optimize_memory_for_large_documents(self) -> None:
        """
        Optimize memory settings for processing large documents.
        """
        try:
            # Get current thresholds
            current_thresholds = gc.get_threshold()
            
            # Adjust garbage collection thresholds for large document processing
            # Reduce frequency of generation 0 collections, increase for others
            new_threshold_0 = max(2000, current_thresholds[0] * 2)  # Ensure it's actually increased
            gc.set_threshold(new_threshold_0, 20, 20)
            
            # Force immediate collection to start with clean slate
            self.force_garbage_collection()
            
            self.logger.info("Memory optimized for large document processing")
            
        except Exception as e:
            self.logger.error(f"Memory optimization failed: {e}")
    
    def get_memory_usage(self) -> Dict[str, Union[int, float]]:
        """
        Get current memory usage statistics.
        
        Returns:
            Dictionary with memory usage information
        """
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            stats = {
                'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
                'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
                'percent': process.memory_percent(),
                'secure_allocations': len(self._secure_allocations),
                'sensitive_objects': len(self._sensitive_objects),
                'peak_memory_mb': self._memory_stats['peak_memory'] / 1024 / 1024,
                'current_secure_mb': self._memory_stats['current_memory'] / 1024 / 1024
            }
            
            # Add tracemalloc statistics if available
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                stats['traced_current_mb'] = current / 1024 / 1024
                stats['traced_peak_mb'] = peak / 1024 / 1024
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get memory usage: {e}")
            return {}
    
    def detect_memory_leaks(self, threshold_mb: float = 100.0) -> List[Dict[str, Any]]:
        """
        Detect potential memory leaks.
        
        Args:
            threshold_mb: Memory threshold in MB to consider as potential leak
            
        Returns:
            List of potential memory leak information
        """
        leaks = []
        
        try:
            if not tracemalloc.is_tracing():
                self.logger.warning("Tracemalloc not enabled, cannot detect leaks")
                return leaks
            
            # Get top memory allocations
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            for stat in top_stats[:10]:  # Top 10 allocations
                size_mb = stat.size / 1024 / 1024
                if size_mb > threshold_mb:
                    leaks.append({
                        'filename': stat.traceback.format()[0] if stat.traceback else 'unknown',
                        'size_mb': size_mb,
                        'count': stat.count,
                        'traceback': stat.traceback.format() if stat.traceback else []
                    })
            
            if leaks:
                self.logger.warning(f"Detected {len(leaks)} potential memory leaks")
            
            return leaks
            
        except Exception as e:
            self.logger.error(f"Memory leak detection failed: {e}")
            return leaks
    
    def cleanup_all_sensitive_data(self) -> int:
        """
        Clean up all registered sensitive data.
        
        Returns:
            Number of objects cleaned up
        """
        cleaned_count = 0
        
        try:
            # Copy the set to avoid modification during iteration
            sensitive_objects = self._sensitive_objects.copy()
            
            for obj_id in sensitive_objects:
                if obj_id in self._cleanup_callbacks:
                    try:
                        self._cleanup_callbacks[obj_id]()
                        cleaned_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to cleanup object {obj_id}: {e}")
            
            # Clear tracking sets
            self._sensitive_objects.clear()
            self._cleanup_callbacks.clear()
            
            # Force garbage collection
            self.force_garbage_collection()
            
            self.logger.info(f"Cleaned up {cleaned_count} sensitive objects")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup sensitive data: {e}")
            return cleaned_count
    
    def _secure_zero_memory(self, memory_map: mmap.mmap, size: int) -> None:
        """Securely zero memory region."""
        try:
            # Multiple pass zeroing for security
            for _ in range(3):
                memory_map.seek(0)
                memory_map.write(b'\x00' * size)
                memory_map.flush()
        except Exception as e:
            self.logger.error(f"Failed to zero memory: {e}")
    
    def _secure_zero_bytes(self, data: Union[bytearray, memoryview]) -> None:
        """Securely zero byte data."""
        try:
            # Check if data is writable
            is_readonly = False
            if hasattr(data, 'readonly'):
                is_readonly = data.readonly
            
            if isinstance(data, (bytearray, memoryview)) and not is_readonly:
                # Overwrite with random data first, then zeros
                random_data = self._crypto_utils.generate_secure_bytes(len(data))
                data[:] = random_data
                data[:] = b'\x00' * len(data)
            elif isinstance(data, bytearray):
                # For bytearray, we can always overwrite
                random_data = self._crypto_utils.generate_secure_bytes(len(data))
                data[:] = random_data
                data[:] = b'\x00' * len(data)
        except Exception as e:
            self.logger.error(f"Failed to zero bytes: {e}")
    
    def _overwrite_immutable_reference(self, obj: Union[str, bytes]) -> None:
        """Attempt to overwrite immutable object reference."""
        # For immutable objects, we can't clear the data in place
        # This is a limitation of Python's memory model
        # The best we can do is ensure the reference is cleared
        # and rely on garbage collection
        pass
    
    def _cleanup_secure_allocation(self, obj_id: int) -> None:
        """Clean up secure memory allocation."""
        try:
            if obj_id in self._cleanup_callbacks:
                self._cleanup_callbacks[obj_id]()
                del self._cleanup_callbacks[obj_id]
            
            if obj_id in self._secure_allocations:
                size = self._secure_allocations[obj_id]
                self._memory_stats['deallocations'] += 1
                self._memory_stats['current_memory'] -= size
                del self._secure_allocations[obj_id]
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup secure allocation {obj_id}: {e}")
    
    def _cleanup_sensitive_object(self, obj_id: int) -> None:
        """Clean up sensitive object."""
        try:
            if obj_id in self._cleanup_callbacks:
                self._cleanup_callbacks[obj_id]()
                del self._cleanup_callbacks[obj_id]
            
            if obj_id in self._sensitive_objects:
                self._sensitive_objects.remove(obj_id)
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup sensitive object {obj_id}: {e}")


class SecureString:
    """
    Secure string wrapper that automatically clears sensitive data.
    """
    
    def __init__(self, data: Union[str, bytes]):
        """
        Initialize secure string.
        
        Args:
            data: String or bytes data to protect
        """
        if isinstance(data, str):
            self._data = bytearray(data.encode('utf-8'))
        elif isinstance(data, bytes):
            self._data = bytearray(data)
        else:
            raise ValueError("Data must be string or bytes")
        
        self._memory_manager = SecureMemoryManager()
        # Register self instead of _data since bytearray doesn't support weak references
        self._memory_manager.register_sensitive_object(
            self, 
            lambda: self._secure_clear()
        )
    
    def get_data(self) -> str:
        """
        Get string data.
        
        Returns:
            String representation of data
        """
        return self._data.decode('utf-8')
    
    def get_bytes(self) -> bytes:
        """
        Get bytes data.
        
        Returns:
            Bytes representation of data
        """
        return bytes(self._data)
    
    def clear(self) -> None:
        """Clear the sensitive data."""
        self._secure_clear()
    
    def _secure_clear(self) -> None:
        """Securely clear the data."""
        if self._data:
            # Overwrite with random data first
            crypto_utils = CryptographicUtils()
            random_data = crypto_utils.generate_secure_bytes(len(self._data))
            self._data[:] = random_data
            
            # Then overwrite with zeros
            self._data[:] = b'\x00' * len(self._data)
            
            # Clear the bytearray
            self._data.clear()
    
    def __str__(self) -> str:
        """String representation."""
        return self.get_data()
    
    def __bytes__(self) -> bytes:
        """Bytes representation."""
        return self.get_bytes()
    
    def __len__(self) -> int:
        """Length of data."""
        return len(self._data)
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            if hasattr(self, '_data'):
                self._secure_clear()
        except Exception:
            pass  # Ignore errors during destruction


class MemoryProfiler:
    """
    Memory profiler for performance monitoring and leak detection.
    """
    
    def __init__(self, name: str = "MemoryProfiler"):
        """
        Initialize memory profiler.
        
        Args:
            name: Name for this profiler instance
        """
        self.name = name
        self.logger = logging.getLogger(__name__)
        self._memory_manager = SecureMemoryManager()
        self._start_memory = None
        self._snapshots = []
    
    def start_profiling(self) -> None:
        """Start memory profiling."""
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        self._start_memory = self._memory_manager.get_memory_usage()
        self.logger.info(f"Started memory profiling: {self.name}")
    
    def take_snapshot(self, label: str = "") -> Dict[str, Any]:
        """
        Take a memory snapshot.
        
        Args:
            label: Optional label for the snapshot
            
        Returns:
            Snapshot information
        """
        if not tracemalloc.is_tracing():
            self.logger.warning("Tracemalloc not enabled")
            return {}
        
        snapshot = {
            'label': label,
            'timestamp': tracemalloc.get_traced_memory(),
            'memory_usage': self._memory_manager.get_memory_usage(),
            'tracemalloc_snapshot': tracemalloc.take_snapshot()
        }
        
        self._snapshots.append(snapshot)
        self.logger.debug(f"Memory snapshot taken: {label}")
        return snapshot
    
    def stop_profiling(self) -> Dict[str, Any]:
        """
        Stop memory profiling and return summary.
        
        Returns:
            Profiling summary
        """
        end_memory = self._memory_manager.get_memory_usage()
        
        summary = {
            'name': self.name,
            'start_memory': self._start_memory,
            'end_memory': end_memory,
            'snapshots': len(self._snapshots),
            'memory_delta_mb': 0,
            'potential_leaks': []
        }
        
        if self._start_memory and end_memory:
            summary['memory_delta_mb'] = (
                end_memory.get('rss_mb', 0) - self._start_memory.get('rss_mb', 0)
            )
        
        # Check for potential leaks
        summary['potential_leaks'] = self._memory_manager.detect_memory_leaks()
        
        self.logger.info(f"Memory profiling completed: {self.name}")
        return summary
    
    def generate_report(self) -> str:
        """
        Generate memory profiling report.
        
        Returns:
            Formatted report string
        """
        summary = self.stop_profiling()
        
        report = f"""
Memory Profiling Report: {summary['name']}
{'=' * 50}

Memory Usage:
- Start RSS: {summary['start_memory'].get('rss_mb', 0):.2f} MB
- End RSS: {summary['end_memory'].get('rss_mb', 0):.2f} MB
- Delta: {summary['memory_delta_mb']:.2f} MB

Snapshots Taken: {summary['snapshots']}

Potential Leaks: {len(summary['potential_leaks'])}
"""
        
        for i, leak in enumerate(summary['potential_leaks'][:5]):  # Top 5 leaks
            report += f"\nLeak {i+1}:\n"
            report += f"  Size: {leak['size_mb']:.2f} MB\n"
            report += f"  Count: {leak['count']}\n"
            report += f"  Location: {leak['filename']}\n"
        
        return report