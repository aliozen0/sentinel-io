import time
import random
import requests
import os
import sys

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
WORKER_ID = os.getenv("WORKER_ID", f"worker-{random.randint(1000, 9999)}")
CHAOS_MODE = os.getenv("CHAOS_MODE", "False").lower() == "true"

print(f"Starting Worker {WORKER_ID} | Chaos Mode: {CHAOS_MODE} | Backend: {BACKEND_URL}")

def work_loop():
    while True:
        try:
            # Simulate work
            # Normal latency: 0.08 - 0.12s
            latency = random.uniform(0.08, 0.12)
            
            # Chaos Mode (Straggler)
            if CHAOS_MODE:
                latency = random.uniform(2.0, 3.0) # 20x-30x slower
                
            time.sleep(latency)
            
            # Telemetry Data
            data = {
                "worker_id": WORKER_ID,
                "latency": latency,
                "temperature": random.uniform(65.0, 80.0), # Fake GPU Temp
                "gpu_util": random.uniform(80.0, 99.0)     # Fake GPU Util
            }
            
            # Send to Backend
            try:
                requests.post(f"{BACKEND_URL}/telemetry", json=data, timeout=1)
            except requests.exceptions.RequestException as e:
                print(f"Failed to send telemetry: {e}")
                
        except Exception as e:
            print(f"Worker Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    work_loop()
