"""
Utility for handling timeouts in operations.
"""
import signal
from contextlib import contextmanager
from typing import Optional, Callable, Any


class TimeoutError(Exception):
    """Exception raised when an operation times out."""
    pass


@contextmanager
def timeout(seconds: int, on_timeout: Optional[Callable[[], Any]] = None):
    """
    Context manager for timing out operations.
    
    Args:
        seconds: Number of seconds before timing out.
        on_timeout: Optional callback to execute when timeout occurs.
    
    Raises:
        TimeoutError: If the operation times out.
    
    Example:
        ```python
        try:
            with timeout(5):
                # Operation that might take too long
                result = slow_operation()
        except TimeoutError:
            print("Operation timed out")
        ```
    """
    def handle_timeout(signum, frame):
        if on_timeout:
            on_timeout()
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    # Set the timeout handler
    original_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, handle_timeout)
    
    try:
        # Set the alarm
        signal.alarm(seconds)
        yield
    finally:
        # Cancel the alarm and restore the original handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)
