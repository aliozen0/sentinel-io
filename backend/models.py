from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class TelemetryData(BaseModel):
    worker_id: str
    latency: float
    temperature: float
    gpu_util: float
    fan_speed: float = 0.0
    clock_speed: float = 100.0
    integrity: str = "UNKNOWN" # VERIFIED / SPOOFED
    timestamp: datetime = Field(default_factory=datetime.now)

class SecureHeader(BaseModel):
    worker_id: str
    timestamp: int
    signature: str

class SecureTelemetryPayload(BaseModel):
    header: SecureHeader
    body: TelemetryData

class AgentResponse(BaseModel):
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any]
    message: str

class AnalysisContext(BaseModel):
    """
    Context object passed along the Chain of Responsibility (FinOps Scan).
    """
    session_id: str
    telemetry_snapshot: Dict[str, TelemetryData]
    secure_verification_failed: bool = False
    anomalies_detected: List[Dict[str, Any]] = []
    diagnosis: Optional[str] = None
    financial_report: Optional[Dict[str, Any]] = None
    actions_taken: List[str] = []
    
    # Trace of agent executions
    agent_logs: List[AgentResponse] = []

    def log_agent_response(self, response: AgentResponse):
        self.agent_logs.append(response)

class VramAnalysisContext(BaseModel):
    """
    Context object for the VRAM Analysis Pipeline.
    """
    session_id: str
    code_snippet: str
    parsed_metadata: Optional[Dict[str, Any]] = None
    vram_usage: Optional[Dict[str, Any]] = None
    optimization_story: Optional[str] = None
    
    agent_logs: List[AgentResponse] = []

    def log_agent_response(self, response: AgentResponse):
        self.agent_logs.append(response)
