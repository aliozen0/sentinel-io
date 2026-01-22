"""
Utility Module - GPU Benchmark Tools
=====================================
Yardımcı fonksiyonlar ve sınıflar.
"""

import time
from typing import List, Tuple, Any
from contextlib import contextmanager


class Timer:
    """Context manager for timing code execution."""
    
    def __init__(self):
        self.elapsed = 0.0
        self._start = None
    
    def __enter__(self):
        self._start = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self._start


def format_size(bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} PB"


def format_time(seconds: float) -> str:
    """Format seconds to human-readable time."""
    if seconds < 0.001:
        return f"{seconds*1000000:.2f} µs"
    elif seconds < 1:
        return f"{seconds*1000:.2f} ms"
    elif seconds < 60:
        return f"{seconds:.2f} s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.1f}s"


def create_matrix(rows: int, cols: int, fill: float = None) -> List[List[float]]:
    """
    Creates a matrix with given dimensions.
    
    Args:
        rows: Number of rows
        cols: Number of columns
        fill: Optional fill value (random if None)
    
    Returns:
        2D list representing the matrix
    """
    import random
    
    if fill is not None:
        return [[fill for _ in range(cols)] for _ in range(rows)]
    else:
        return [[random.random() for _ in range(cols)] for _ in range(rows)]


def matrix_multiply(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    """
    Performs matrix multiplication A × B.
    
    This is a naive O(n³) implementation for demonstration.
    In production, use NumPy or similar optimized libraries.
    
    Args:
        A: First matrix (m × n)
        B: Second matrix (n × p)
    
    Returns:
        Result matrix (m × p)
    """
    m = len(A)
    n = len(A[0])
    p = len(B[0])
    
    # Initialize result matrix with zeros
    C = [[0.0 for _ in range(p)] for _ in range(m)]
    
    # Perform multiplication
    for i in range(m):
        for j in range(p):
            total = 0.0
            for k in range(n):
                total += A[i][k] * B[k][j]
            C[i][j] = total
    
    return C


def calculate_statistics(data: List[float]) -> dict:
    """
    Calculate basic statistics for a list of numbers.
    
    Args:
        data: List of numeric values
    
    Returns:
        Dictionary with min, max, mean, std
    """
    if not data:
        return {"min": 0, "max": 0, "mean": 0, "std": 0}
    
    n = len(data)
    mean = sum(data) / n
    variance = sum((x - mean) ** 2 for x in data) / n
    std = variance ** 0.5
    
    return {
        "min": min(data),
        "max": max(data),
        "mean": mean,
        "std": std,
        "count": n
    }


class ProgressBar:
    """Simple console progress bar."""
    
    def __init__(self, total: int, width: int = 40, prefix: str = "Progress"):
        self.total = total
        self.width = width
        self.prefix = prefix
        self.current = 0
    
    def update(self, current: int = None):
        """Update progress bar."""
        if current is not None:
            self.current = current
        else:
            self.current += 1
        
        percent = self.current / self.total
        filled = int(self.width * percent)
        bar = "█" * filled + "░" * (self.width - filled)
        
        print(f"\r{self.prefix}: [{bar}] {percent*100:.1f}%", end="", flush=True)
        
        if self.current >= self.total:
            print()  # New line when complete
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        if self.current < self.total:
            self.update(self.total)
