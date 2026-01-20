from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import json
from state_manager import state
from ai_client import ask_io_intelligence

app = FastAPI(title="io-Guard Orchestrator")

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

@app.post("/analyze/stragglers")
async def detect_stragglers():
    """
    In-Flight Straggler Detection: Identifies slow nodes.
    """
    workers = state.get_all_workers()
    active_workers_data = []
    
    for wid, wdata in workers.items():
        if wdata["status"] == "Active":
            # Get average latency from history
            history = state.get_worker_history(wid)
            if history:
                avg_latency = sum(h["latency"] for h in history) / len(history)
                active_workers_data.append(f"{wid}: {avg_latency:.4f}s avg latency")
    
    if not active_workers_data:
        return {"result": "No active workers to analyze"}

    system_prompt = "You are a distributed systems expert. Detect performance anomalies."
    user_prompt = f"Here are the average latencies of active nodes: {', '.join(active_workers_data)}. Is there a statistically significant straggler? If yes, return the Worker ID. If no, return 'None'."
    
    response = ask_io_intelligence(system_prompt, user_prompt)
    
    # Simple parsing logic - in a real app, we'd want structured JSON response
    # The prompt asks for Worker ID or None.
    
    for wid in workers.keys():
        if wid in response and "None" not in response:
             state.kill_worker(wid)
             return {"result": f"Straggler detected and killed: {wid}", "ai_raw": response}
             
    return {"result": "No stragglers detected", "ai_raw": response}
