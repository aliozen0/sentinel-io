import time
import random
import requests
import os
import sys

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
WORKER_ID = os.getenv("WORKER_ID", f"worker-{random.randint(1000, 9999)}")

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

class DigitalTwin:
    def __init__(self):
        # Component Health (0.0 - 1.0)
        self.health_cooling = 1.0 
        self.health_network = 1.0
        self.health_power = 1.0

        # Physical State
        self.temp = 45.0
        self.clock_speed = 100.0 # Percentage 0-100
        self.fan_rpm = 0.0 # Percentage 0-100
        
        # Physics Constants
        self.throttle_temp = 95.0
        self.heat_gen_base = 1.5 # degrees per tick
        self.cooling_power_max = 4.0 # degrees per tick max cooling
        
    def update_physics(self, load_percent: float):
        """
        Runs the Thermodynamic Loop.
        DeltaTemp = HeatGen - Dissipation
        """
        # 1. Calculate Heat Generation
        # Base heat from load + Leakage from poor power health
        heat_gen = (load_percent / 100.0) * self.heat_gen_base
        heat_gen += (1.0 - self.health_power) * 2.0 # Power inefficiency generates heat
        
        # 2. Calculate Cooling (Dissipation)
        # Fan curve: Ramp up as temp exceeds 50C
        target_fan = min(100.0, max(0.0, (self.temp - 50.0) * 2.5))
        self.fan_rpm = target_fan 
        
        # Effective Cooling depends on Fan RPM and Fan Health
        # If fan wire is cut (health=0), cooling is 0 even if RPM is 100
        cooling_effective = (self.fan_rpm / 100.0) * self.health_cooling * self.cooling_power_max
        
        # 3. Apply Temperature Change
        self.temp += heat_gen - cooling_effective
        self.temp = max(25.0, self.temp) # Ambient floor
        
        # 4. Throttling Logic
        if self.temp > self.throttle_temp:
            # Throttle down to reduce heat (simulated by reducing clock)
            self.clock_speed = max(10.0, self.clock_speed - 10.0)
            if random.random() < 0.1: # Don't spam logs
                remote_log("warning", f"🔥 THERMAL THROTTLING! Temp: {self.temp:.1f}C, Clock: {self.clock_speed}%")
        else:
            # Recover slowly
            self.clock_speed = min(100.0, self.clock_speed + 2.0)

    def get_latency(self, base_latency=0.1):
        """
        Calculate latency based on Clock Speed and Network Health.
        """
        # Clock factor: 50% clock = 2x latency
        clock_factor = 100.0 / max(5.0, self.clock_speed)
        
        # Network factor: 50% health = 2x latency + jitter
        net_factor = 1.0 / max(0.1, self.health_network)
        
        jitter = random.uniform(0, 0.05 * (1.0 - self.health_network))
        
        final_latency = (base_latency * clock_factor * net_factor) + jitter
        return final_latency

def work_loop():
    twin = DigitalTwin()
    remote_log("info", f"Worker {WORKER_ID} initialized with DeepSim Digital Twin.")
    
    while True:
        try:
            # 1. Poll for Commands (Heartbeat & Chaos Injection)
            try:
                cmd_res = requests.get(f"{BACKEND_URL}/command/{WORKER_ID}", timeout=2)
                if cmd_res.status_code == 200:
                    cmd_data = cmd_res.json()
                    
                    # Applying Chaos/Sabotage commands directly to the Twin
                    if "sabotage" in cmd_data:
                        sabotage = cmd_data["sabotage"] # e.g., {"component": "COOLING", "health": 0.0}
                        component = sabotage.get("component")
                        val = sabotage.get("health", 1.0)
                        
                        if component == "COOLING": twin.health_cooling = val
                        elif component == "NETWORK": twin.health_network = val
                        elif component == "POWER": twin.health_power = val
                        elif component == "ALL_RESTORE": 
                            twin.health_cooling = 1.0
                            twin.health_network = 1.0
                            twin.health_power = 1.0
                            
            except Exception:
                pass # Backend offline?

            # 2. Physics Simulation Step
            # Simulate a variable load (random work)
            current_load = random.uniform(20.0, 80.0)
            twin.update_physics(current_load)
            
            # 3. Send Telemetry with Extended Physics Data
            current_latency = twin.get_latency()
            
            data = {
                "worker_id": WORKER_ID,
                "latency": current_latency,
                "temperature": twin.temp,
                "gpu_util": current_load,
                "fan_speed": twin.fan_rpm,
                "clock_speed": twin.clock_speed,
                "health": {
                    "cooling": twin.health_cooling,
                    "network": twin.health_network
                }
            }

            try:
                requests.post(f"{BACKEND_URL}/telemetry", json=data, timeout=2)
            except Exception as e:
                # Only log error occasionally/locally to avoid spamming self if network is dead
                pass

            time.sleep(0.5) # 2Hz Physics Loop
                
        except Exception as e:
            remote_log("error", f"Crash in work loop: {e}")
            time.sleep(1)

if __name__ == "__main__":
    work_loop()
