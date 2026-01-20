from agents.base import BaseAgent
from agents.implementations import (
    WatchdogAgent, DiagnosticianAgent, AccountantAgent, EnforcerAgent,
    CodeParserAgent, VRAMCalculatorAgent, OptimizationAdvisorAgent
)
from models import AnalysisContext, TelemetryData, VramAnalysisContext
from state_manager import state
import uuid
import logging

logger = logging.getLogger("Orchestrator")

class AgentOrchestrator:
    """
    Service to assemble and execute the agent pipeline (Chain of Responsibility).
    """
    def __init__(self):
        # Initialize Agents
        # v2.0 FinOps Pipeline
        self.pipeline: list[BaseAgent] = [
            WatchdogAgent("watchdog"),
            DiagnosticianAgent("diagnostician"),
            AccountantAgent("accountant"),
            EnforcerAgent("enforcer")
        ]
        
        # v3.0 VRAM Oracle Pipeline
        self.vram_pipeline: list[BaseAgent] = [
            CodeParserAgent("code_parser"),
            VRAMCalculatorAgent("vram_calculator"),
            OptimizationAdvisorAgent("optimization_advisor")
        ]

    async def run_scan(self) -> AnalysisContext:
        """
        Runs the full agentic workflow.
        """
        # 1. Create Context from Current State
        workers = state.get_all_workers()
        snapshot = {}
        for wid, wdata in workers.items():
            if wdata['status'] == 'Active':
                data = wdata['data']
                snapshot[wid] = TelemetryData(
                    worker_id=wid,
                    latency=data.get('latency', 0),
                    temperature=data.get('temperature', 0),
                    gpu_util=data.get('gpu_util', 0),
                    fan_speed=data.get('fan_speed', 0),
                    clock_speed=data.get('clock_speed', 100)
                )

        ctx = AnalysisContext(
            session_id=str(uuid.uuid4()),
            telemetry_snapshot=snapshot
        )

        # 2. Execute Pipeline
        logger.info(f"Starting Agentic Scan Session: {ctx.session_id}")
        
        for agent in self.pipeline:
            # Pass the context through each agent
            ctx = await agent.execute(ctx)
            
        logger.info("Scan complete.")
        return ctx

    async def run_vram_analysis(self, code_snippet: str) -> VramAnalysisContext:
        """
        Executes the v3.0 VRAM Oracle Pipeline.
        """
        session_id = str(uuid.uuid4())
        ctx = VramAnalysisContext(
            session_id=session_id,
            code_snippet=code_snippet
        )
        
        logger.info(f"Starting VRAM Analysis Session: {session_id}")
        
        for agent in self.vram_pipeline:
            ctx = await agent.execute(ctx)
            
        return ctx
