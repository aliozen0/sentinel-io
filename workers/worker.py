import time
import random
import requests
import os
import sys

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
WORKER_ID = os.getenv("WORKER_ID", f"worker-{random.randint(1000, 9999)}")
CHAOS_MODE = os.getenv("CHAOS_MODE", "False").lower() == "true"

def remote_log(level: str, message: str):
    """
    Sends log to the Backend Central Logger.
    """
    print(f"[{level.upper()}] {message}") # Keep local stdout for Docker
    try:
        payload = {
            "service": WORKER_ID,
            "level": level,
            "message": message
        }
        requests.post(f"{BACKEND_URL}/log-event", json=payload, timeout=1)
    except:
        pass # Fire and forget

def work_loop():
    global CHAOS_MODE 
    remote_log("info", f"Worker {WORKER_ID} started. Backend: {BACKEND_URL}")
    
    while True:
        try:
            # Simulate work
            try:
                # 1. Poll for Commands (Heartbeat & Config)
                cmd_res = requests.get(f"{BACKEND_URL}/command/{WORKER_ID}", timeout=2)
                if cmd_res.status_code == 200:
                    cmd_data = cmd_res.json()
                    new_chaos = cmd_data.get("chaos", False)
                    
                    if new_chaos != CHAOS_MODE:
                        CHAOS_MODE = new_chaos
                        status_str = "ACTIVATED" if CHAOS_MODE else "DEACTIVATED"
                        remote_log("warning", f"Chaos Mode {status_str} by remote command.")
                        
            except Exception:
                pass

            # 2. Simulate Workload based on Dynamic State
            if CHAOS_MODE:
                # Simulate High Latency (Straggler)
                latency = random.uniform(2.0, 5.0) 
                temperature = random.uniform(85.0, 98.0)
                remote_log("warning", f"🔥 UNDER ATTACK! Latency spiked to {latency:.2f}s")
            else:
                # Normal Operation
                latency = random.uniform(0.08, 0.12)
                temperature = random.uniform(60.0, 75.0)

            # 3. Send Telemetry
            data = {
                "worker_id": WORKER_ID,
                "latency": latency,
                "temperature": temperature,
                "gpu_util": random.uniform(80, 100) if CHAOS_MODE else random.uniform(40, 60)
            }

            try:
                requests.post(f"{BACKEND_URL}/telemetry", json=data, timeout=2)
            except Exception as e:
                remote_log("error", f"Telemetry connection failed: {e}")

            time.sleep(latency)
                
        except Exception as e:
            remote_log("error", f"Crash in work loop: {e}")
            time.sleep(1)

if __name__ == "__main__":
    work_loop()
