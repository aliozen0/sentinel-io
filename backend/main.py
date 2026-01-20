from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
from state_manager import state
from ai_client import ask_io_intelligence
from services.orchestrator import AgentOrchestrator
from models import AnalysisContext
from logger import get_logger, LOG_FILE
import os

logger = get_logger("API")

app = FastAPI(title="io-Guard Orchestrator v2.0")

# Singleton Orchestrator (Dependency Injection pattern could be used here)
orchestrator = AgentOrchestrator()

class Telemetry(BaseModel):
    worker_id: str
    latency: float
    temperature: float
    gpu_util: float

@app.post("/telemetry")
async def receive_telemetry(data: Telemetry):
    """
    Receives telemetry data from workers.
    """
    state.update_worker_status(data.worker_id, data.dict())
    return {"status": "received"}

@app.get("/status")
async def get_system_status():
    """
    Returns the current status of all workers.
    """
    return state.get_all_workers()

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
