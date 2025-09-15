"""
Progress bar utilities for CLI operations.
"""

import sys
import time
from typing import Optional


class ProgressBar:
    """
    Simple progress bar for CLI operations.
    """
    
    def __init__(self, total: int, description: str = "", width: int = 50):
        self.total = total
        self.current = 0
        self.description = description
        self.width = width
        self.start_time = time.time()
        self.last_update = 0
        
    def update(self, increment: int = 1, description: Optional[str] = None) -> None:
        """Update progress bar."""
        self.current += increment
        
        if description:
            self.description = description
        
        # Only update display if enough time has passed (avoid flickering)
        current_time = time.time()
        if current_time - self.last_update < 0.1 and self.current < self.total:
            return
        
        self.last_update = current_time
        self._display()
    
    def _display(self) -> None:
        """Display the progress bar."""
        if self.total == 0:
            return
        
        percent = min(100, (self.current / self.total) * 100)
        filled_width = int(self.width * self.current / self.total)
        bar = '█' * filled_width + '░' * (self.width - filled_width)
        
        # Calculate elapsed and estimated time
        elapsed = time.time() - self.start_time
        if self.current > 0:
            rate = self.current / elapsed
            eta = (self.total - self.current) / rate if rate > 0 else 0
            eta_str = f"ETA: {self._format_time(eta)}"
        else:
            eta_str = "ETA: --:--"
        
        # Format the progress line
        progress_line = f"\r{self.description} [{bar}] {percent:5.1f}% ({self.current}/{self.total}) {eta_str}"
        
        # Write to stderr to avoid interfering with output
        sys.stderr.write(progress_line)
        sys.stderr.flush()
        
        # Add newline when complete
        if self.current >= self.total:
            sys.stderr.write('\n')
    
    def _format_time(self, seconds: float) -> str:
        """Format time in MM:SS format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def finish(self) -> None:
        """Mark progress as complete."""
        self.current = self.total
        self._display()


class SpinnerProgress:
    """
    Simple spinner for indeterminate progress.
    """
    
    def __init__(self, description: str = "Processing..."):
        self.description = description
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current_char = 0
        self.start_time = time.time()
        self.last_update = 0
        self.active = False
    
    def start(self) -> None:
        """Start the spinner."""
        self.active = True
        self._display()
    
    def update(self, description: Optional[str] = None) -> None:
        """Update spinner with optional new description."""
        if not self.active:
            return
        
        if description:
            self.description = description
        
        current_time = time.time()
        if current_time - self.last_update < 0.1:
            return
        
        self.last_update = current_time
        self.current_char = (self.current_char + 1) % len(self.spinner_chars)
        self._display()
    
    def _display(self) -> None:
        """Display the spinner."""
        elapsed = time.time() - self.start_time
        elapsed_str = self._format_time(elapsed)
        
        spinner_line = f"\r{self.spinner_chars[self.current_char]} {self.description} ({elapsed_str})"
        
        sys.stderr.write(spinner_line)
        sys.stderr.flush()
    
    def _format_time(self, seconds: float) -> str:
        """Format time in MM:SS format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def stop(self) -> None:
        """Stop the spinner."""
        if self.active:
            self.active = False
            sys.stderr.write('\r' + ' ' * 80 + '\r')  # Clear the line
            sys.stderr.flush()


def create_progress_bar(total: int, description: str = "", show_progress: bool = True) -> Optional[ProgressBar]:
    """
    Create a progress bar if progress display is enabled.
    
    Args:
        total: Total number of items
        description: Description to show
        show_progress: Whether to show progress
        
    Returns:
        ProgressBar instance or None if progress disabled
    """
    if show_progress and total > 0:
        return ProgressBar(total, description)
    return None


def create_spinner(description: str = "Processing...", show_progress: bool = True) -> Optional[SpinnerProgress]:
    """
    Create a spinner if progress display is enabled.
    
    Args:
        description: Description to show
        show_progress: Whether to show progress
        
    Returns:
        SpinnerProgress instance or None if progress disabled
    """
    if show_progress:
        return SpinnerProgress(description)
    return None