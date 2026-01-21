from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import re
from datetime import datetime
from state_manager import state
from ai_client import ask_io_intelligence
from services.orchestrator import AgentOrchestrator
from models import AnalysisContext, VramAnalysisContext, SecureTelemetryPayload
from logger import get_logger, LOG_FILE
import hmac
import hashlib
import os

logger = get_logger("API")

app = FastAPI(title="io-Guard Orchestrator v2.0")

# Singleton Orchestrator (Dependency Injection pattern could be used here)
orchestrator = AgentOrchestrator()

# --- v3.0 Dynamic Chaos Engine ---
# In-Memory Database for Chaos State
chaos_state_db = {} 

class Telemetry(BaseModel):
    worker_id: str
    latency: float
    temperature: float
    gpu_util: float
    fan_speed: float = 0.0
    clock_speed: float = 100.0
    health: dict = {}
    timestamp: datetime = Field(default_factory=datetime.now)

class LogEvent(BaseModel):
    """
    Schema for remote logging from workers.
    """
    service: str
    level: str
    message: str

@app.post("/telemetry")
async def receive_telemetry(data: Telemetry):
    """
    Receives telemetry data from workers.
    """
    state.update_worker_status(data.worker_id, data.dict())
    
    # Ensure worker is in chaos db (default False if new)
    if data.worker_id not in chaos_state_db:
        chaos_state_db[data.worker_id] = False
        
    # Critical Physics Check (Kernel Level)
    if data.temperature > 90.0:
        logger.warning(f"⚠️ KERNEL ALERT: {data.worker_id} overhead (Temp: {data.temperature:.1f}C). Advise Agent Scan.")
        
    return {"status": "received"}

    return {"status": "received"}

@app.post("/telemetry/secure")
async def receive_secure_telemetry(payload: SecureTelemetryPayload):
    """
    v4.0 Secure Telemetry Ingestion (PoC Protocol)
    """
    body = payload.body
    header = payload.header
    
    # 1. Reconstruct Canonical String
    # MUST MATCH worker.py: f"{worker_id}:{timestamp}:{latency}:{temp}"
    canonical_string = f"{header.worker_id}:{header.timestamp}:{body.latency}:{body.temperature}"
    
    # 2. Verify Signature
    # In prod, fetch key from Secrets Manager based on worker_id
    SECRET_KEY = f"simulated_sk_{header.worker_id}".encode()
    
    expected_sign = hmac.new(SECRET_KEY, canonical_string.encode(), hashlib.sha256).hexdigest()
    
    integrity_status = "VERIFIED"
    if hmac.compare_digest(expected_sign, header.signature) == False:
        logger.error(f"🚨 SECURITY ALERT: Invalid Signature from {header.worker_id}")
        integrity_status = "SPOOFED"
    
    # 3. Update State with Integrity Flag
    data_dict = body.dict()
    data_dict["integrity"] = integrity_status
    
    state.update_worker_status(header.worker_id, data_dict)
    
    if integrity_status == "SPOOFED":
         raise HTTPException(status_code=401, detail="Signature Verification Failed")
         
    return {"status": "secure_received", "integrity": integrity_status}

# --- v3.0 Chaos Endpoints ---
@app.post("/chaos/inject/{worker_id}")
async def inject_chaos(worker_id: str, payload: dict):
    """
    Activates Component-Level Sabotage.
    Payload: {"component": "COOLING", "severity": 0.8} (Sets health to 1.0 - severity)
             OR {"component": "COOLING", "health": 0.0} (Direct health set)
    """
    health_val = 0.0
    if "health" in payload:
        health_val = payload["health"]
    elif "severity" in payload:
        health_val = max(0.0, 1.0 - payload["severity"])
        
    component = payload.get("component", "COOLING").upper()
    
    # Store command in DB for worker to pick up
    chaos_state_db[worker_id] = {
        "sabotage": {
            "component": component,
            "health": health_val
        }
    }
    
    logger.warning(f"🔥 SABOTAGE! {component} on {worker_id} set to health {health_val}")
    return {"status": "sabotage_sent", "worker_id": worker_id, "component": component}

@app.post("/chaos/repair/{worker_id}")
async def repair_node(worker_id: str):
    """
    Simulates a physical repair (Reset to 1.0 health).
    """
    chaos_state_db[worker_id] = {
        "sabotage": {
            "component": "ALL_RESTORE",
            "health": 1.0
        }
    }
    # Reset State to ACTIVE
    state.transition_node(worker_id, "ACTIVE")
    return {"status": "repaired", "target": worker_id}

@app.post("/provision")
async def provision_node():
    """
    Spins up a new simulated standby node.
    """
    import random
    new_id = f"worker-{random.randint(10000, 99999)}"
    state.add_simulated_worker(new_id)
    return {"status": "provisioned", "worker_id": new_id}

@app.get("/command/{worker_id}")
async def get_worker_command(worker_id: str):
    """
    Worker polls this endpoint to receive sabotage/repair commands.
    Once consumed, we clear the command or keep it persistent?
    For persistent state (like 'Cut Wire'), we keep sending it until Repaired.
    """
    command = chaos_state_db.get(worker_id, {})
    return command

@app.post("/simulation/attack")
async def simulation_attack(payload: dict):
    """
    Simulates Security Attacks (e.g., Spoofing).
    """
    target_id = payload.get("worker_id", "worker-1") # Default target
    attack_type = payload.get("type", "SIGNATURE_SPOOF")
    
    if attack_type == "SIGNATURE_SPOOF":
         chaos_state_db[target_id] = {
             "sabotage": {
                 "component": "SIGNATURE_SPOOF",
                 "health": 0.0 # Irrelevant for spoof
             }
         }
         logger.warning(f"🎭 ATTACK SIMULATION: Spoofing triggered on {target_id}")
         return {"status": "attack_sent", "type": attack_type}
    
    return {"status": "unknown_attack"}

@app.post("/log-event")
async def receive_log_event(event: LogEvent):
    """
    Centralized logging endpoint. Workers send logs here.
    """
    msg = f"[{event.service.upper()}] {event.message}"
    
    if event.level.lower() == "error":
        logger.error(msg)
    elif event.level.lower() == "warning":
        logger.warning(msg)
    else:
        logger.info(msg)
        
    return {"status": "logged"}

# ----------------------------

@app.get("/status")
async def get_system_status():
    """
    Returns the current status of all workers.
    """
    return state.get_all_workers()

@app.get("/cluster/status")
async def get_cluster_status():
    """
    Ray-Lite Cluster Manager View
    """
    workers = state.get_all_workers()
    
    # Group by Lifecycle State
    cluster_view = {
        "active": [],
        "idle": [],
        "cordoned": [],
        "draining": [],
        "offline": []
    }
    
    for wid, info in workers.items():
        ls = info.get("lifecycle_state", "ACTIVE").lower()
        if ls in cluster_view:
            cluster_view[ls].append(wid)
        else:
            cluster_view["active"].append(wid) # Fallback
            
    return cluster_view

@app.get("/economy/ledger")
async def get_economy_ledger():
    """
    Returns Tokenomics State
    """
    return state.get_ledger()

@app.post("/analyze/vram-prediction")
async def predict_vram(file_content: str):
    """
    Pre-Flight Oracle: Predicts VRAM usage based on code content.
    """
    # Extract potential parameters using RegEx for context
    model_match = re.search(r'model_name\s*=\s*["\']([^"\']+)["\']', file_content)
    batch_match = re.search(r'batch_size\s*=\s*(\d+)', file_content)
    
    extracted_info = f"Model: {model_match.group(1) if model_match else 'Unknown'}, Batch: {batch_match.group(1) if batch_match else 'Unknown'}"
    
    system_prompt = "You are an expert AI hardware engineer. Estimate VRAM usage."
    user_prompt = f"Analyze this code parameters: {extracted_info}. Code snippet: {file_content[:500]}... Calculate required VRAM. Return ONLY a JSON with keys: 'vram_gb' (float), 'status' ('Approved'|'Denied'), 'reason' (string)."
    
    response = ask_io_intelligence(system_prompt, user_prompt)
    return {"ai_response": response}

@app.post("/analyze/vram-agentic")
async def analyze_vram_agentic(file_content: str):
    """
    v3.0 Agentic VRAM Oracle: 3-Stage Pipeline (Parser -> Calculator -> Advisor).
    """
    try:
        ctx: VramAnalysisContext = await orchestrator.run_vram_analysis(file_content)
        
        return {
            "session_id": ctx.session_id,
            "metadata": ctx.parsed_metadata,
            "vram": ctx.vram_usage,
            "advice": ctx.optimization_story,
            "logs": ctx.agent_logs
        }
    except Exception as e:
        logger.error(f"VRAM Analysis Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/agentic-scan")
async def run_agentic_scan():
    """
    Triggers the v2.0 Agentic Workflow (Watchdog -> Diagnostician -> Accountant -> Enforcer).
    """
    try:
        ctx: AnalysisContext = await orchestrator.run_scan()
        
        # Convert internal context to a frontend-friendly response
        return {
            "session_id": ctx.session_id,
            "anomaly_detected": bool(ctx.anomalies_detected),
            "logs": ctx.agent_logs,
            "actions": ctx.actions_taken,
            "financial_report": ctx.financial_report
        }
    except Exception as e:
        logger.error(f"Agentic scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze/logs")
async def get_agent_logs(limit: int = 50):
    """
    Returns the global agent event log (Neural Stream).
    """
    return {"logs": state.get_agent_logs(limit)}

@app.get("/logs")
async def get_system_logs(lines: int = 50):
    """
    Returns the last N lines of the system log.
    """
    if not os.path.exists(LOG_FILE):
        return {"logs": ["Log file not initialized yet."]}
        
    try:
        with open(LOG_FILE, "r") as f:
            # Simple simulation of "tail" - reading all might be heavy for production but fine for MVP
            all_lines = f.readlines()
            return {"logs": all_lines[-lines:]}
    except Exception as e:
        return {"logs": [f"Error reading logs: {str(e)}"]}
