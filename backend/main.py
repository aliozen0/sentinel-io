from fastapi import FastAPI, HTTPException, WebSocket, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import re
from datetime import datetime
from typing import List, Dict, Optional
import hmac
import hashlib
import os
import logging
import asyncio
import uuid


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
    
    # Demo Routes
    from routes import demo
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

# Register Demo Routes
app.include_router(demo.router, prefix="/v1/connections", tags=["Demo"])

# Ensure uploads directory exists
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Mount static files for serving uploads
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# ==========================================
# 🚀 io-Guard v1.0 API ENDPOINTS (THE NEW CORE)
# ==========================================

# Available io.net models
IO_NET_MODELS = [
    {"id": "deepseek-ai/DeepSeek-V3.2", "name": "DeepSeek V3.2", "type": "chat", "recommended": True},
    {"id": "deepseek-ai/DeepSeek-R1-0528", "name": "DeepSeek R1 (Reasoning)", "type": "reasoning"},
    {"id": "meta-llama/Llama-3.3-70B-Instruct", "name": "Llama 3.3 70B", "type": "chat"},
    {"id": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8", "name": "Llama 4 Maverick", "type": "chat"},
    {"id": "Qwen/Qwen3-235B-A22B-Thinking-2507", "name": "Qwen3 235B Thinking", "type": "reasoning"},
    {"id": "Qwen/Qwen2.5-VL-32B-Instruct", "name": "Qwen2.5 VL 32B (Vision)", "type": "vision"},
    {"id": "moonshotai/Kimi-K2-Thinking", "name": "Kimi K2 Thinking", "type": "reasoning"},
    {"id": "moonshotai/Kimi-K2-Instruct-0905", "name": "Kimi K2 Instruct", "type": "chat"},
    {"id": "mistralai/Mistral-Large-Instruct-2411", "name": "Mistral Large", "type": "chat"},
    {"id": "mistralai/Mistral-Nemo-Instruct-2407", "name": "Mistral Nemo", "type": "chat"},
    {"id": "mistralai/Devstral-Small-2505", "name": "Devstral Small (Code)", "type": "code"},
    {"id": "openai/gpt-oss-120b", "name": "GPT OSS 120B", "type": "chat"},
    {"id": "zai-org/GLM-4.7", "name": "GLM 4.7", "type": "chat"},
]

# --- Models ---
class AnalyzeRequest(BaseModel):
    code: str
    budget: float = 10.0
    model: Optional[str] = None  # Custom model override

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]

class DeploySimulateRequest(BaseModel):
    job_config: Dict

# --- Model Selection Endpoint ---

@app.get("/v1/models")
async def get_available_models():
    """Returns available io.net AI models for analysis."""
    default_model = os.getenv("IO_MODEL_NAME", "deepseek-ai/DeepSeek-V3.2")
    return {
        "default_model": default_model,
        "models": IO_NET_MODELS
    }

# --- Endpoints ---

@app.post("/v1/analyze")
async def analyze_code(request: AnalyzeRequest):
    """
    [v1.0] Analyzes code and recommends GPU nodes.
    Uses: Auditor (LLM) → Architect (Environment) → Sniper (Market)
    Returns pipeline trace for transparency.
    """
    import time
    import os
    
    # Get model - use request model or fall back to env default
    default_model = os.getenv("IO_MODEL_NAME", "deepseek-ai/DeepSeek-V3.2")
    model_name = request.model if request.model else default_model
    api_base = os.getenv("IO_BASE_URL", "api.intelligence.io.solutions")
    
    pipeline_trace = []
    
    # === STEP 1: Auditor (LLM Analysis) ===
    step1_start = time.time()
    pipeline_trace.append({
        "step": 1,
        "agent": "Auditor",
        "status": "running",
        "action": "Sending code to LLM for analysis...",
        "details": {
            "model": model_name,
            "api": api_base.replace("https://", "").replace("/api/v1/", ""),
            "code_length": len(request.code)
        }
    })
    
    audit_report = await Auditor.analyze_code(request.code, model=model_name)
    step1_time = round(time.time() - step1_start, 2)
    
    pipeline_trace[0]["status"] = "completed"
    pipeline_trace[0]["duration_sec"] = step1_time
    pipeline_trace[0]["result"] = {
        "framework": audit_report.framework,
        "vram": f"{audit_report.vram_min_gb} GB",
        "health_score": audit_report.health_score,
        "issues_found": len(audit_report.critical_issues)
    }
    
    # === STEP 2: Architect (Environment Planning) ===
    step2_start = time.time()
    pipeline_trace.append({
        "step": 2,
        "agent": "Architect",
        "status": "running",
        "action": "Analyzing imports and planning environment...",
        "details": {
            "framework": audit_report.framework,
            "vram_required": audit_report.vram_min_gb
        }
    })
    
    env_config = await Architect.plan_environment(
        framework=audit_report.framework,
        code=request.code,
        vram_gb=audit_report.vram_min_gb
    )
    step2_time = round(time.time() - step2_start, 2)
    
    pipeline_trace[1]["status"] = "completed"
    pipeline_trace[1]["duration_sec"] = step2_time
    pipeline_trace[1]["result"] = {
        "base_image": env_config.base_image,
        "packages_detected": len(env_config.python_packages),
        "cuda_version": env_config.cuda_version
    }
    
    # === STEP 3: Sniper (Market Analysis) ===
    step3_start = time.time()
    gpu_model = "RTX 4090" if audit_report.vram_min_gb > 20 else "RTX 3090"
    
    pipeline_trace.append({
        "step": 3,
        "agent": "Sniper",
        "status": "running",
        "action": "Fetching live GPU prices from io.net...",
        "details": {
            "api": "api.io.solutions/v1/io-explorer/network/market-snapshot",
            "target_gpu": gpu_model,
            "budget": f"${request.budget}/hr"
        }
    })
    
    best_nodes = await Sniper.get_best_nodes(
        budget_hourly=request.budget, 
        gpu_model=gpu_model
    )
    step3_time = round(time.time() - step3_start, 2)
    
    pipeline_trace[2]["status"] = "completed"
    pipeline_trace[2]["duration_sec"] = step3_time
    pipeline_trace[2]["result"] = {
        "nodes_found": len(best_nodes),
        "best_price": f"${best_nodes[0].price_hourly}/hr" if best_nodes else "N/A"
    }
    
    total_time = round(step1_time + step2_time + step3_time, 2)
    
    analysis_result = {
        "audit": audit_report.dict(),
        "environment": env_config.dict(),
        "market_recommendations": [node.dict() for node in best_nodes],
        "summary": {
            "framework": audit_report.framework,
            "vram_required": f"{audit_report.vram_min_gb} GB",
            "recommended_gpu": gpu_model,
            "estimated_setup": f"{env_config.estimated_setup_time_min} min",
            "health_score": audit_report.health_score
        },
        "pipeline_trace": {
            "total_duration_sec": total_time,
            "steps": pipeline_trace
        }
    }
    
    # Store in state for Chat Agent context
    state.last_analysis = analysis_result
    
    return analysis_result

# ...
try:
    from db.client import get_db
except ImportError:
    get_db = lambda: None

# ... (inside chat_agent)

@app.post("/v1/chat")
async def chat_agent(request: ChatRequest):
    """
    [v1.0] Project-Aware AI Chatbot.
    Uses ChatAgent to provide context-aware responses (Analysis, Deployment, etc.)
    """
    from agents.chat import ChatAgent
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # 1. Persist User Message (Real DB)
    supabase = get_db()
    if supabase:
        try:
             supabase.table("io_chat_history").insert({
                "role": "user",
                "content": request.messages[-1]["content"]
            }).execute()
        except: pass

    # 2. Get Response from ChatAgent (Context Aware)
    # We can pass model preference if needed, for now use default
    response_content = await ChatAgent.chat(request.messages)
    
    # 3. Persist AI Response
    if supabase:
        try:
             supabase.table("io_chat_history").insert({
                "role": "assistant",
                "content": response_content
            }).execute()
        except: pass

    return {"role": "assistant", "content": response_content}

@app.get("/v1/market/status")
async def market_status():
    """
    [v1.0] Returns cached market data or status.
    """
    data = Sniper._get_market_data()
    return {"source": "live/cache", "node_count": len(data), "sample": data[:10]}

# --- Terminal WebSocket ---
from agents.terminal import terminal_manager
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json

@app.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket):
    await websocket.accept()
    session_id = id(websocket) 
    
    try:
        # Wait for init message
        data = await websocket.receive_text()
        msg = json.loads(data)
        
        if msg.get("type") == "connect":
            config = msg.get("config")
            try:
                terminal_manager.create_session(session_id, config)
                await websocket.send_json({"type": "status", "data": "connected"})
            except Exception as e:
                await websocket.send_json({"type": "error", "data": str(e)})
                return
        
        # Main Loop
        session = terminal_manager.get_session(session_id)
        if not session:
            return

        # Background task to read from SSH
        async def read_ssh():
            while True:
                output = session.recv()
                if output:
                    await websocket.send_json({"type": "output", "data": output})
                else:
                    await asyncio.sleep(0.1)

        reader_task = asyncio.create_task(read_ssh())
        
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg.get("type") == "input":
                session.send(msg.get("data"))
            elif msg.get("type") == "resize":
                # Handle resize if needed
                pass

    except WebSocketDisconnect:
        terminal_manager.close_session(session_id)
    except Exception as e:
        logger.error(f"WS Error: {e}")
        terminal_manager.close_session(session_id)

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

class SSHConnectionRequest(BaseModel):
    hostname: str
    username: str
    port: int = 22
    auth_type: str = "key"  # "key" or "password"
    private_key: Optional[str] = None
    password: Optional[str] = None
    passphrase: Optional[str] = None  # For encrypted keys

@app.post("/v1/connection/test")
async def test_ssh_connection(request: SSHConnectionRequest):
    """
    [v1.0] Tests SSH connection to a remote node.
    Supports: Private Key, Password, and Passphrase-protected keys.
    """
    try:
        from services.ssh_manager import SSHManager
        success, message = await SSHManager.test_connection(
            hostname=request.hostname, 
            username=request.username, 
            port=request.port,
            auth_type=request.auth_type,
            private_key=request.private_key,
            password=request.password,
            passphrase=request.passphrase
        )
        return {"success": success, "message": message}
    except ImportError:
        return {"success": False, "message": "SSH Module (Paramiko) missing. Please rebuild backend."}
    except Exception as e:
        logger.error(f"SSH Test Error: {e}")
        return {"success": False, "message": f"Server Error: {str(e)}"}

# --- File Upload ---

ALLOWED_EXTENSIONS = {'.py', '.txt', '.yaml', '.yml', '.json', '.zip'}

def get_file_type(filename: str) -> str:
    """Determine file type from extension."""
    if filename.endswith('.py'):
        return 'script'
    elif filename.endswith('.txt'):
        return 'requirements'
    elif filename.endswith(('.yaml', '.yml')):
        return 'config'
    elif filename.endswith('.json'):
        return 'config'
    elif filename.endswith('.zip'):
        return 'archive'
    return 'other'

def find_entry_point(directory: str) -> Optional[str]:
    """Find the main Python script in a directory."""
    # Priority: main.py > train.py > run.py > first .py file
    priority_names = ['main.py', 'train.py', 'run.py', 'app.py', 'script.py']
    
    for name in priority_names:
        path = os.path.join(directory, name)
        if os.path.exists(path):
            return name
    
    # Fallback to first .py file
    for f in os.listdir(directory):
        if f.endswith('.py'):
            return f
    
    return None

@app.post("/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    [v1.0] Uploads a single file for remote execution.
    Accepts: .py, .txt, .yaml, .yml, .json, .zip
    """
    # Security: Check allowed extensions
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())[:8]
    safe_filename = f"{file_id}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOADS_DIR, safe_filename)
    
    try:
        # Save file
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        file_url = f"http://localhost:8000/uploads/{safe_filename}"
        
        logger.info(f"File uploaded: {safe_filename} ({len(contents)} bytes)")
        
        return {
            "success": True,
            "filename": safe_filename,
            "original_name": file.filename,
            "size": len(contents),
            "url": file_url,
            "local_path": file_path,
            "type": get_file_type(file.filename)
        }
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/v1/upload/project")
async def upload_project(files: List[UploadFile] = File(...)):
    """
    [v1.0] Uploads multiple files or a ZIP archive as a project.
    Creates a project directory and extracts files.
    Returns project metadata including entry point.
    """
    import zipfile
    import io as io_module
    
    project_id = str(uuid.uuid4())[:8]
    project_dir = os.path.join(UPLOADS_DIR, f"project_{project_id}")
    os.makedirs(project_dir, exist_ok=True)
    
    uploaded_files = []
    
    try:
        for file in files:
            ext = os.path.splitext(file.filename)[1].lower()
            
            if ext == '.zip':
                # Extract ZIP archive
                contents = await file.read()
                try:
                    with zipfile.ZipFile(io_module.BytesIO(contents), 'r') as zip_ref:
                        # Security: Check for path traversal
                        for member in zip_ref.namelist():
                            if member.startswith('..') or member.startswith('/'):
                                raise HTTPException(status_code=400, detail="Invalid ZIP: path traversal detected")
                        
                        zip_ref.extractall(project_dir)
                        
                        # List extracted files
                        for root, dirs, files_list in os.walk(project_dir):
                            for f in files_list:
                                rel_path = os.path.relpath(os.path.join(root, f), project_dir)
                                full_path = os.path.join(root, f)
                                uploaded_files.append({
                                    "filename": rel_path,
                                    "size": os.path.getsize(full_path),
                                    "type": get_file_type(f),
                                    "source": "zip"
                                })
                        
                        logger.info(f"ZIP extracted: {file.filename} -> {len(uploaded_files)} files")
                except zipfile.BadZipFile:
                    raise HTTPException(status_code=400, detail="Invalid ZIP file")
            
            elif ext in ALLOWED_EXTENSIONS:
                # Regular file
                safe_filename = file.filename.replace(' ', '_')
                file_path = os.path.join(project_dir, safe_filename)
                
                contents = await file.read()
                with open(file_path, "wb") as f:
                    f.write(contents)
                
                uploaded_files.append({
                    "filename": safe_filename,
                    "size": len(contents),
                    "type": get_file_type(file.filename),
                    "source": "upload"
                })
                
                logger.info(f"File added to project: {safe_filename}")
            else:
                logger.warning(f"Skipped unsupported file: {file.filename}")
        
        # Find entry point
        entry_point = find_entry_point(project_dir)
        
        # Count files by type
        script_count = sum(1 for f in uploaded_files if f['type'] == 'script')
        
        return {
            "success": True,
            "project_id": project_id,
            "project_dir": project_dir,
            "files": uploaded_files,
            "file_count": len(uploaded_files),
            "script_count": script_count,
            "entry_point": entry_point,
            "has_requirements": any(f['type'] == 'requirements' for f in uploaded_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Project upload error: {e}")
        # Cleanup on error
        import shutil
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/v1/uploads")
async def list_uploads():
    """
    [v1.0] Lists all uploaded files and projects.
    """
    try:
        files = []
        projects = []
        
        for item in os.listdir(UPLOADS_DIR):
            item_path = os.path.join(UPLOADS_DIR, item)
            
            if os.path.isdir(item_path) and item.startswith('project_'):
                # It's a project directory
                project_files = []
                for root, dirs, files_list in os.walk(item_path):
                    for f in files_list:
                        rel_path = os.path.relpath(os.path.join(root, f), item_path)
                        project_files.append(rel_path)
                
                projects.append({
                    "project_id": item.replace('project_', ''),
                    "path": item_path,
                    "file_count": len(project_files),
                    "entry_point": find_entry_point(item_path)
                })
            else:
                # Regular file
                ext = os.path.splitext(item)[1].lower()
                if ext in ALLOWED_EXTENSIONS:
                    files.append({
                        "filename": item,
                        "size": os.path.getsize(item_path),
                        "url": f"http://localhost:8000/uploads/{item}",
                        "type": get_file_type(item)
                    })
        
        return {"files": files, "projects": projects}
    except Exception as e:
        return {"files": [], "projects": [], "error": str(e)}


# --- Remote Execution ---

class ExecuteRequest(BaseModel):
    hostname: str
    username: str
    port: int = 22
    auth_type: str = "key"  # "key" or "password"
    private_key: Optional[str] = None
    password: Optional[str] = None
    passphrase: Optional[str] = None
    script_path: str  # Local path to the uploaded script


@app.post("/v1/deploy/execute")
async def deploy_execute(request: ExecuteRequest):
    """
    [v1.0] Uploads script to remote server and executes it.
    Supports: Private Key, Password, and Passphrase-protected keys.
    """
    if not os.path.exists(request.script_path):
        raise HTTPException(status_code=404, detail="Script file not found")
    
    job_id = f"exec_{str(uuid.uuid4())[:8]}"
    
    if not hasattr(app, 'job_configs'):
        app.job_configs = {}
    
    app.job_configs[job_id] = {
        "hostname": request.hostname,
        "username": request.username,
        "port": request.port,
        "auth_type": request.auth_type,
        "private_key": request.private_key,
        "password": request.password,
        "passphrase": request.passphrase,
        "script_path": request.script_path,
        "status": "pending"
    }
    
    logger.info(f"Execution job created: {job_id}")
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Connect to WebSocket /ws/execute/{job_id} for logs"
    }


@app.websocket("/ws/execute/{job_id}")
async def websocket_execute(websocket: WebSocket, job_id: str):
    """
    [v1.0] Real-time execution logs via WebSocket.
    Uploads file to remote server and executes it.
    """
    await websocket.accept()
    
    try:
        if not hasattr(app, 'job_configs') or job_id not in app.job_configs:
            await websocket.send_text("❌ Job not found")
            await websocket.close()
            return
        
        config = app.job_configs[job_id]
        config["status"] = "running"
        
        await websocket.send_text(f"🚀 Starting job: {job_id}")
        
        from services.ssh_manager import SSHManager
        
        async for line in SSHManager.upload_and_execute(
            hostname=config["hostname"],
            username=config["username"],
            local_path=config["script_path"],
            port=config["port"],
            auth_type=config["auth_type"],
            private_key=config.get("private_key"),
            password=config.get("password"),
            passphrase=config.get("passphrase")
        ):
            await websocket.send_text(line)
        
        config["status"] = "completed"
        await websocket.send_text(f"✅ Job {job_id} completed")
        
    except Exception as e:
        logger.error(f"Execution error: {e}")
        await websocket.send_text(f"❌ Error: {str(e)}")
    finally:
        try:
            await websocket.close()
        except:
            pass


# --- Project Execution ---

class ExecuteProjectRequest(BaseModel):
    hostname: str
    username: str
    port: int = 22
    auth_type: str = "key"
    private_key: Optional[str] = None
    password: Optional[str] = None
    passphrase: Optional[str] = None
    project_dir: str  # Local path to the project directory
    entry_point: str  # Main script to execute (e.g., "main.py")
    install_requirements: bool = True


@app.post("/v1/deploy/project")
async def deploy_project(request: ExecuteProjectRequest):
    """
    [v1.0] Uploads a project to remote server and executes it.
    Supports: Multiple files, requirements.txt installation, entry point execution.
    """
    if not os.path.exists(request.project_dir):
        raise HTTPException(status_code=404, detail="Project directory not found")
    
    entry_path = os.path.join(request.project_dir, request.entry_point)
    if not os.path.exists(entry_path):
        raise HTTPException(status_code=404, detail=f"Entry point '{request.entry_point}' not found in project")
    
    job_id = f"proj_{str(uuid.uuid4())[:8]}"
    
    if not hasattr(app, 'job_configs'):
        app.job_configs = {}
    
    app.job_configs[job_id] = {
        "type": "project",
        "hostname": request.hostname,
        "username": request.username,
        "port": request.port,
        "auth_type": request.auth_type,
        "private_key": request.private_key,
        "password": request.password,
        "passphrase": request.passphrase,
        "project_dir": request.project_dir,
        "entry_point": request.entry_point,
        "install_requirements": request.install_requirements,
        "status": "pending"
    }
    
    logger.info(f"Project execution job created: {job_id}")
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Connect to WebSocket /ws/execute-project/{job_id} for logs"
    }


@app.websocket("/ws/execute-project/{job_id}")
async def websocket_execute_project(websocket: WebSocket, job_id: str):
    """
    [v1.0] Real-time project execution logs via WebSocket.
    Uploads entire project, installs requirements, and executes entry point.
    """
    await websocket.accept()
    
    try:
        if not hasattr(app, 'job_configs') or job_id not in app.job_configs:
            await websocket.send_text("❌ Job not found")
            await websocket.close()
            return
        
        config = app.job_configs[job_id]
        
        if config.get("type") != "project":
            await websocket.send_text("❌ Invalid job type for this endpoint")
            await websocket.close()
            return
        
        config["status"] = "running"
        
        await websocket.send_text(f"🚀 Starting project job: {job_id}")
        
        from services.ssh_manager import SSHManager
        
        async for line in SSHManager.upload_project_and_execute(
            hostname=config["hostname"],
            username=config["username"],
            project_dir=config["project_dir"],
            entry_point=config["entry_point"],
            port=config["port"],
            auth_type=config["auth_type"],
            private_key=config.get("private_key"),
            password=config.get("password"),
            passphrase=config.get("passphrase"),
            install_requirements=config.get("install_requirements", True)
        ):
            await websocket.send_text(line)
        
        config["status"] = "completed"
        await websocket.send_text(f"✅ Project job {job_id} completed")
        
    except Exception as e:
        logger.error(f"Project execution error: {e}")
        await websocket.send_text(f"❌ Error: {str(e)}")
    finally:
        try:
            await websocket.close()
        except:
            pass

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
