from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import re
from datetime import datetime
from typing import List, Dict, Optional
import hmac
import hashlib
import os
import logging
import asyncio

# --- io-Guard v1.0 Core Imports ---
try:
    from ai_client import ask_io_intelligence, ask_io_intelligence_async
    from state_manager import state
    from services.orchestrator import AgentOrchestrator
    from models import AnalysisContext, VramAnalysisContext, SecureTelemetryPayload
    from logger import get_logger, LOG_FILE
    
    # New Agents
    from agents.auditor import Auditor, AuditReport
    from agents.sniper import Sniper, GPUNode
    from agents.architect import Architect, EnvironmentConfig
    from agents.executor import Executor
except ImportError:
    # Fallback for local dev if paths are tricky
    pass

logger = logging.getLogger("io-guard-core") # Updated logger name for v1.0

app = FastAPI(title="io-Guard Core (v1.0 + Legacy v2.0)")

# Singleton Orchestrator
orchestrator = AgentOrchestrator()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 🚀 io-Guard v1.0 API ENDPOINTS (THE NEW CORE)
# ==========================================

# --- Models ---
class AnalyzeRequest(BaseModel):
    code: str
    budget: float = 10.0

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

class DeploySimulateRequest(BaseModel):
    job_config: Dict

# --- Endpoints ---

@app.post("/v1/analyze")
async def analyze_code(request: AnalyzeRequest):
    """
    [v1.0] Analyzes code and recommends GPU nodes.
    """
    logger.info("Received analysis request (v1.0)")
    
    # 1. Audit Code
    audit_report = await Auditor.analyze_code(request.code)
    
    # 2. Architect Environment
    env_config = Architect.plan_environment(audit_report.framework)
    
    # 3. Find Nodes (Sniper)
    best_nodes = await Sniper.get_best_nodes(
        budget_hourly=request.budget, 
        gpu_model="RTX 4090" if audit_report.vram_min_gb > 20 else "RTX 3090"
    )
    
    return {
        "audit": audit_report.dict(),
        "environment": env_config.dict(),
        "market_recommendations": [node.dict() for node in best_nodes]
    }

@app.post("/v1/chat")
async def chat_agent(request: ChatRequest):
    """
    [v1.0] General Purpose AI Chatbot.
    Supports technical queries + general conversation.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    last_msg = request.messages[-1]
    user_content = last_msg['content']
    
    # 1. (Mock) Persist User Message
    # In prod: supabase.table('chat_messages').insert({role: 'user', content: user_content})
    logger.info(f"Chat User: {user_content}")
    
    # 2. Updated System Prompt for General + Tech capabilities
    system_prompt = (
        "You are io-Guard, an intelligent AI Assistant. "
        "Your primary expertise is Distributed Training and GPU Orchestration, "
        "but you are also a friendly, general-purpose chatbot. "
        "You can answer general questions, help with coding, or just chat casually. "
        "Be concise, professional, yet warm."
    )
    
    response = await ask_io_intelligence_async(
        system_prompt=system_prompt,
        user_prompt=user_content
    )
    
    # 3. (Mock) Persist AI Response
    logger.info(f"Chat AI: {response}")
    
    return {"role": "assistant", "content": response}

@app.get("/v1/market/status")
async def market_status():
    """
    [v1.0] Returns cached market data or status.
    """
    data = Sniper._get_market_data()
    return {"source": "live/cache", "node_count": len(data), "sample": data[:2]}

@app.post("/v1/deploy/simulate")
async def deploy_simulate(request: DeploySimulateRequest):
    """
    [v1.0] Starts a simulation job.
    """
    import uuid
    job_id = f"sim_{str(uuid.uuid4())[:8]}"
    return {"job_id": job_id, "status": "simulation_started"}

@app.post("/v1/deploy/live")
async def deploy_live(payload: dict):
    """
    [v1.0] Mock for Live Deployment.
    """
    return {"job_id": "live_999", "status": "pending_ssh_connection"}

@app.websocket("/ws/logs/{job_id}")
async def websocket_logs(websocket: WebSocket, job_id: str):
    """
    [v1.0] Real-time logs for jobs (Simulation/Live).
    """
    await websocket.accept()
    try:
        async for line in Executor.run_simulation({"job_id": job_id}):
             await websocket.send_text(line)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

# ==========================================
# 🛑 LEGACY v2.0 ENDPOINTS (Keep for gradual migration)
# ==========================================

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
    service: str
    level: str
    message: str

@app.get("/")
def read_root():
    return {"status": "io-Guard Core v1.0 Active (Legacy v2.0 Supported)", "version": "1.0.0"}

@app.post("/telemetry")
async def receive_telemetry(data: Telemetry):
    state.update_worker_status(data.worker_id, data.dict())
    if data.worker_id not in chaos_state_db:
        chaos_state_db[data.worker_id] = False
    if data.temperature > 90.0:
        logger.warning(f"⚠️ KERNEL ALERT: {data.worker_id} overhead")
    return {"status": "received"}

@app.post("/telemetry/secure")
async def receive_secure_telemetry(payload: SecureTelemetryPayload):
    body = payload.body
    header = payload.header
    canonical_string = f"{header.worker_id}:{header.timestamp}:{body.latency}:{body.temperature}"
    SECRET_KEY = f"simulated_sk_{header.worker_id}".encode()
    expected_sign = hmac.new(SECRET_KEY, canonical_string.encode(), hashlib.sha256).hexdigest()
    
    integrity_status = "VERIFIED"
    if hmac.compare_digest(expected_sign, header.signature) == False:
        integrity_status = "SPOOFED"
    
    data_dict = body.dict()
    data_dict["integrity"] = integrity_status
    state.update_worker_status(header.worker_id, data_dict)
    
    if integrity_status == "SPOOFED":
         raise HTTPException(status_code=401, detail="Signature Verification Failed")
    return {"status": "secure_received", "integrity": integrity_status}

@app.post("/chaos/inject/{worker_id}")
async def inject_chaos(worker_id: str, payload: dict):
    health_val = 0.0
    if "health" in payload:
        health_val = payload["health"]
    elif "severity" in payload:
        health_val = max(0.0, 1.0 - payload["severity"])
    component = payload.get("component", "COOLING").upper()
    chaos_state_db[worker_id] = {"sabotage": {"component": component, "health": health_val}}
    return {"status": "sabotage_sent"}

@app.post("/chaos/repair/{worker_id}")
async def repair_node(worker_id: str):
    chaos_state_db[worker_id] = {"sabotage": {"component": "ALL_RESTORE", "health": 1.0}}
    state.transition_node(worker_id, "ACTIVE")
    return {"status": "repaired"}

@app.post("/provision")
async def provision_node():
    import random
    new_id = f"worker-{random.randint(10000, 99999)}"
    state.add_simulated_worker(new_id)
    return {"status": "provisioned", "worker_id": new_id}

@app.get("/command/{worker_id}")
async def get_worker_command(worker_id: str):
    return chaos_state_db.get(worker_id, {})

@app.post("/simulation/attack")
async def simulation_attack(payload: dict):
    return {"status": "attack_sent"}

@app.post("/log-event")
async def receive_log_event(event: LogEvent):
    msg = f"[{event.service.upper()}] {event.message}"
    logger.info(msg)
    return {"status": "logged"}

@app.get("/status")
async def get_system_status():
    return state.get_all_workers()

@app.get("/cluster/status")
async def get_cluster_status():
    return {"status": "legacy_cluster_status"} # Simplified for rewrite

@app.get("/economy/ledger")
async def get_economy_ledger():
    return state.get_ledger()

@app.post("/analyze/vram-prediction")
async def predict_vram(file_content: str):
    # Reuse old pre-flight logic or point to new one? 
    # For now keeping as is.
    model_match = re.search(r'model_name\s*=\s*["\']([^"\']+)["\']', file_content)
    extracted_info = f"Model: {model_match.group(1) if model_match else 'Unknown'}"
    system_prompt = "You are an expert AI hardware engineer. Estimate VRAM usage."
    user_prompt = f"Analyze: {extracted_info}. Code: {file_content[:500]}..."
    response = ask_io_intelligence(system_prompt, user_prompt)
    return {"ai_response": response}

@app.post("/analyze/vram-agentic")
async def analyze_vram_agentic(file_content: str):
    try:
        ctx: VramAnalysisContext = await orchestrator.run_vram_analysis(file_content)
        return {"session_id": ctx.session_id, "vram": ctx.vram_usage}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/agentic-scan")
async def run_agentic_scan():
    try:
        ctx: AnalysisContext = await orchestrator.run_scan()
        return {"session_id": ctx.session_id, "actions": ctx.actions_taken}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze/logs")
async def get_agent_logs(limit: int = 50):
    return {"logs": state.get_agent_logs(limit)}

@app.get("/logs")
async def get_system_logs(lines: int = 50):
    if not os.path.exists(LOG_FILE):
        return {"logs": []}
    with open(LOG_FILE, "r") as f:
        return {"logs": f.readlines()[-lines:]}
