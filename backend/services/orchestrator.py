"""
io-Guard v1.0 Agent Orchestrator

Unified pipeline for code analysis workflow:
Auditor (LLM Analysis) -> Architect (Environment Planning) -> Sniper (Market Arbitrage)
"""

import time
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from state_manager import state
from agents.auditor import Auditor, AuditReport
from agents.architect import Architect, EnvironmentConfig
from agents.sniper import Sniper, GPUNode

logger = logging.getLogger("Orchestrator")


class AnalysisResult(BaseModel):
    """Complete result from the analysis pipeline."""
    audit: Dict[str, Any]
    environment: Dict[str, Any]
    market_recommendations: List[Dict[str, Any]]
    summary: Dict[str, str]
    pipeline_trace: Dict[str, Any]


class AgentOrchestrator:
    """
    v1.0 Code Analysis Orchestrator
    
    Orchestrates the agent pipeline:
    1. Auditor - LLM-powered code analysis
    2. Architect - Environment and dependency planning  
    3. Sniper - Market price optimization
    """
    
    async def run_analysis(
        self, 
        code: str, 
        budget: float = 10.0,
        model: Optional[str] = None
    ) -> AnalysisResult:
        """
        Executes the full v1.0 analysis pipeline.
        
        Args:
            code: Python code to analyze
            budget: Hourly budget for GPU rental
            model: Optional LLM model override
            
        Returns:
            AnalysisResult with audit, environment, and market data
        """
        import os
        
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
                "model": model or os.getenv("IO_MODEL_NAME", "deepseek-ai/DeepSeek-V3.2"),
                "api": api_base.replace("https://", "").replace("/api/v1/", ""),
                "code_length": len(code)
            }
        })
        
        audit_report = await Auditor.analyze_code(code, model=model)
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
            code=code,
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
                "budget": f"${budget}/hr"
            }
        })
        
        best_nodes = await Sniper.get_best_nodes(
            budget_hourly=budget, 
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
        
        result = AnalysisResult(
            audit=audit_report.dict(),
            environment=env_config.dict(),
            market_recommendations=[node.dict() for node in best_nodes],
            summary={
                "framework": audit_report.framework,
                "vram_required": f"{audit_report.vram_min_gb} GB",
                "recommended_gpu": gpu_model,
                "estimated_setup": f"{env_config.estimated_setup_time_min} min",
                "health_score": str(audit_report.health_score)
            },
            pipeline_trace={
                "total_duration_sec": total_time,
                "steps": pipeline_trace
            }
        )
        
        # Store in state for Chat Agent context
        state.last_analysis = result.dict()
        
        return result
