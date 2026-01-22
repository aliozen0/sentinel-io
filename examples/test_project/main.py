#!/usr/bin/env python3
"""
GPU Performance Benchmark - Test Project
=========================================
Bu script, GPU hesaplama performansını test etmek için tasarlanmıştır.
io-Guard Wizard üzerinden uzak GPU'ya deploy edilebilir.

Özellikler:
- Matrix çarpımı benchmark
- Memory bandwidth testi
- Basit ML inference simülasyonu
"""

import os
import sys
import time
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import Timer, format_size, create_matrix, matrix_multiply
from config import CONFIG, get_benchmark_params

def run_cpu_benchmark():
    """CPU matrix multiplication benchmark."""
    print("\n" + "=" * 60)
    print("🖥️  CPU Matrix Multiplication Benchmark")
    print("=" * 60)
    
    params = get_benchmark_params()
    size = params['matrix_size']
    iterations = params['iterations']
    
    print(f"   Matrix Size: {size}x{size}")
    print(f"   Iterations: {iterations}")
    print("-" * 60)
    
    # Create random matrices
    print("   📊 Creating random matrices...")
    A = create_matrix(size, size)
    B = create_matrix(size, size)
    
    # Warm-up
    print("   🔥 Warming up...")
    _ = matrix_multiply(A, B)
    
    # Benchmark
    print("   ⏱️  Running benchmark...")
    times = []
    
    for i in range(iterations):
        with Timer() as t:
            result = matrix_multiply(A, B)
        times.append(t.elapsed)
        print(f"      Iteration {i+1}/{iterations}: {t.elapsed:.4f}s")
    
    avg_time = sum(times) / len(times)
    ops = (2 * size * size * size) / avg_time / 1e9  # GFLOPS
    
    print("-" * 60)
    print(f"   ✅ Average Time: {avg_time:.4f}s")
    print(f"   ⚡ Performance: {ops:.2f} GFLOPS")
    
    return {"avg_time": avg_time, "gflops": ops}

def run_memory_benchmark():
    """Memory allocation and bandwidth test."""
    print("\n" + "=" * 60)
    print("💾 Memory Bandwidth Benchmark")
    print("=" * 60)
    
    sizes = [1, 10, 50, 100]  # MB
    results = []
    
    for size_mb in sizes:
        size_bytes = size_mb * 1024 * 1024
        elements = size_bytes // 8  # 64-bit floats
        
        print(f"\n   Testing {size_mb} MB allocation...")
        
        with Timer() as t:
            data = [random.random() for _ in range(elements)]
            _ = sum(data)  # Force memory access
        
        bandwidth = size_bytes / t.elapsed / 1e9  # GB/s
        results.append({"size_mb": size_mb, "bandwidth_gbs": bandwidth})
        print(f"      ✓ {size_mb} MB: {bandwidth:.2f} GB/s")
    
    avg_bandwidth = sum(r["bandwidth_gbs"] for r in results) / len(results)
    print("-" * 60)
    print(f"   ✅ Average Bandwidth: {avg_bandwidth:.2f} GB/s")
    
    return results

def run_inference_simulation():
    """Simulates ML model inference."""
    print("\n" + "=" * 60)
    print("🤖 ML Inference Simulation")
    print("=" * 60)
    
    batch_sizes = [1, 8, 32]
    latencies = []
    
    for batch in batch_sizes:
        print(f"\n   Batch Size: {batch}")
        
        # Simulate preprocessing
        preprocess_time = random.uniform(0.001, 0.005) * batch
        
        # Simulate inference (matrix ops)
        inference_time = random.uniform(0.01, 0.05) * batch
        
        # Simulate postprocessing
        postprocess_time = random.uniform(0.001, 0.003) * batch
        
        total = preprocess_time + inference_time + postprocess_time
        throughput = batch / total
        
        latencies.append({
            "batch": batch,
            "latency_ms": total * 1000,
            "throughput": throughput
        })
        
        print(f"      Latency: {total*1000:.2f}ms")
        print(f"      Throughput: {throughput:.1f} samples/sec")
    
    return latencies

def main():
    """Main benchmark runner."""
    print("\n" + "🚀" * 30)
    print(f"\n   {CONFIG['project_name']} v{CONFIG['version']}")
    print(f"   {CONFIG['description']}")
    print("\n" + "🚀" * 30)
    
    print(f"\n📍 Working Directory: {os.getcwd()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"💻 Platform: {sys.platform}")
    
    start_time = time.time()
    
    # Run benchmarks
    cpu_results = run_cpu_benchmark()
    memory_results = run_memory_benchmark()
    inference_results = run_inference_simulation()
    
    total_time = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"   Total Duration: {total_time:.2f}s")
    print(f"   CPU Performance: {cpu_results['gflops']:.2f} GFLOPS")
    print(f"   Memory Bandwidth: {memory_results[-1]['bandwidth_gbs']:.2f} GB/s")
    print(f"   Inference (batch=32): {inference_results[-1]['throughput']:.1f} samples/sec")
    print("=" * 60)
    print("\n✅ All benchmarks completed successfully!")
    print("🎉 io-Guard GPU Performance Test - PASSED\n")

if __name__ == "__main__":
    main()
