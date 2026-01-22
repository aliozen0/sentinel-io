"""
Configuration Module - GPU Benchmark Settings
==============================================
Proje ayarları ve konfigürasyon parametreleri.
"""

import os

# Project metadata
CONFIG = {
    "project_name": "GPU Performance Benchmark",
    "version": "1.0.0",
    "description": "io-Guard test project for GPU performance testing",
    "author": "io-Guard Team",
}

# Benchmark parameters - can be overridden by environment variables
BENCHMARK_CONFIG = {
    # Matrix multiplication settings
    "matrix_size": int(os.getenv("BENCH_MATRIX_SIZE", "100")),
    "iterations": int(os.getenv("BENCH_ITERATIONS", "5")),
    
    # Memory benchmark settings
    "memory_sizes_mb": [1, 10, 50, 100],
    
    # Inference simulation settings
    "batch_sizes": [1, 8, 32, 64],
    "model_layers": 12,
    "hidden_dim": 768,
}

# Logging configuration
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "file": os.getenv("LOG_FILE", None),
}

# GPU detection settings (mock for CPU-only test)
GPU_CONFIG = {
    "prefer_gpu": True,
    "fallback_cpu": True,
    "mixed_precision": False,
}


def get_benchmark_params() -> dict:
    """Returns current benchmark parameters."""
    return {
        "matrix_size": BENCHMARK_CONFIG["matrix_size"],
        "iterations": BENCHMARK_CONFIG["iterations"],
        "memory_sizes": BENCHMARK_CONFIG["memory_sizes_mb"],
        "batch_sizes": BENCHMARK_CONFIG["batch_sizes"],
    }


def get_config_summary() -> str:
    """Returns a formatted summary of current configuration."""
    lines = [
        f"Project: {CONFIG['project_name']} v{CONFIG['version']}",
        f"Matrix Size: {BENCHMARK_CONFIG['matrix_size']}x{BENCHMARK_CONFIG['matrix_size']}",
        f"Iterations: {BENCHMARK_CONFIG['iterations']}",
        f"Log Level: {LOGGING_CONFIG['level']}",
    ]
    return "\n".join(lines)


# Exported configuration
__all__ = [
    "CONFIG",
    "BENCHMARK_CONFIG", 
    "LOGGING_CONFIG",
    "GPU_CONFIG",
    "get_benchmark_params",
    "get_config_summary",
]
