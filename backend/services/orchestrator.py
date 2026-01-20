from agents.base import BaseAgent
from agents.implementations import WatchdogAgent, DiagnosticianAgent, AccountantAgent, EnforcerAgent
from models import AnalysisContext, TelemetryData
from state_manager import state
import uuid

class AgentOrchestrator:
    """
    Service to assemble and execute the agent pipeline (Chain of Responsibility).
    """
    def __init__(self):
        # Initialize Agents
        self.pipeline: list[BaseAgent] = [
            WatchdogAgent("watchdog"),
            DiagnosticianAgent("diagnostician"),
            AccountantAgent("accountant"),
            EnforcerAgent("enforcer")
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
                    gpu_util=data.get('gpu_util', 0)
                )

        ctx = AnalysisContext(
            session_id=str(uuid.uuid4()),
            telemetry_snapshot=snapshot
        )

        # 2. Execute Pipeline
        print(f"--- Starting Agentic Scan {ctx.session_id} ---")
        for agent in self.pipeline:
            ctx = await agent.execute(ctx)
            
            # Optimization: Break if Watchdog found nothing?
            # For this demo, we let it flow, but Diagnostician handles "no anomaly" check
            if agent.agent_id == "watchdog" and not ctx.anomalies_detected:
                print("Watchdog found no anomalies. Aborting chain.")
                break

        print(f"--- Scan Complete. Actions: {ctx.actions_taken} ---")
        return ctx
