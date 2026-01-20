from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class TelemetryData(BaseModel):
    worker_id: str
    latency: float
    temperature: float
    gpu_util: float
    timestamp: datetime = Field(default_factory=datetime.now)

class AgentResponse(BaseModel):
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any]
    message: str

class AnalysisContext(BaseModel):
    """
    Context object passed along the Chain of Responsibility.
    """
    session_id: str
    telemetry_snapshot: Dict[str, TelemetryData]
    anomalies_detected: List[Dict[str, Any]] = []
    diagnosis: Optional[str] = None
    financial_report: Optional[Dict[str, Any]] = None
    actions_taken: List[str] = []
    
    # Trace of agent executions
    agent_logs: List[AgentResponse] = []

    def log_agent_response(self, response: AgentResponse):
        self.agent_logs.append(response)
