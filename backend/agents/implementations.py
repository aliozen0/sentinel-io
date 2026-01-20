import json
from .base import BaseAgent
from models import AnalysisContext
from .base import BaseAgent
from models import AnalysisContext
from ai_client import ask_io_intelligence
from state_manager import state
from logger import get_logger

logger = get_logger("Agents")

class WatchdogAgent(BaseAgent):
    """
    Role: Monitoring
    Goal: Detect anomalies in telemetry data.
    """
    async def _process(self, ctx: AnalysisContext) -> tuple[dict, str]:
        # 1. Prepare Data for AI
        active_workers = {k: v.dict() for k, v in ctx.telemetry_snapshot.items()}
        if not active_workers:
            return {}, "No active workers to monitor."

        # 2. AI Analysis
        system_prompt = (
            "You are a Monitoring Expert. Analyze the input logs. "
            "Look for latency > 0.5s or temperature > 80C. "
            "If found, output \"ANOMALY_DETECTED\" and the Node ID. "
            "Return ONLY JSON: {\"anomalies\": [{\"node_id\": \"...\", \"reason\": \"...\"}]}"
        )
        user_prompt = f"Telemetry: {json.dumps(active_workers, default=str)}"
        
        logger.info(f"Watchdog: Sending telemetry sample size={len(active_workers)} to IO Intelligence...")
        response_text = ask_io_intelligence(system_prompt, user_prompt)
        logger.debug(f"Watchdog: AI Raw Response: {response_text[:100]}...")
        
        # 3. Parse Response
        try:
            # Cleanup markdown if present
            clean_json = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            anomalies = data.get("anomalies", [])
            
            ctx.anomalies_detected = anomalies
            
            if anomalies:
                msg = f"Watchdog detected {len(anomalies)} anomalies."
            else:
                msg = "System healthy. No anomalies."
                
            return data, msg
            
        except Exception as e:
            return {"raw": response_text}, f"Watchdog parse error: {e}"


class DiagnosticianAgent(BaseAgent):
    """
    Role: Root Cause Analysis
    Goal: Classify the error type for detected anomalies.
    """
    async def _process(self, ctx: AnalysisContext) -> tuple[dict, str]:
        if not ctx.anomalies_detected:
            return {}, "Skipping diagnosis (No anomalies)."

        diagnoses = []
        for anomaly in ctx.anomalies_detected:
            node_id = anomaly.get("node_id")
            reason = anomaly.get("reason")
            
            # Retrieve worker history for deeper context
            history = state.get_worker_history(node_id)
            avg_lat = sum(h["latency"] for h in history) / len(history) if history else 0
            
            system_prompt = "You are a Hardware Engineer. Receive the anomaly report."
            user_prompt = (
                f"Node: {node_id}, Issue: {reason}. "
                f"Avg Latency (30s): {avg_lat:.4f}s. "
                "Classify the error type into: [Network Congestion, Thermal Throttling, Memory Leak]. "
                "Output the Classification Label."
            )
            
            cause = ask_io_intelligence(system_prompt, user_prompt)
            logger.info(f"Diagnostician: Node {node_id} issue '{reason}' diagnosed as '{cause}'")
            diagnoses.append({"node_id": node_id, "classification": cause})
        
        # Store simplistic single diagnosis for context, or full list in data
        ctx.diagnosis = diagnoses[0]["classification"] if diagnoses else "Unknown"
        
        return {"diagnoses": diagnoses}, f"Diagnosed issues: {[d['classification'] for d in diagnoses]}"


class AccountantAgent(BaseAgent):
    """
    Role: FinOps
    Goal: Calculate financial waste.
    """
    async def _process(self, ctx: AnalysisContext) -> tuple[dict, str]:
        if not ctx.anomalies_detected:
            return {}, "Skipping accounting (No anomalies)."

        GPU_HOURLY_RATE = 2.50 # Mock cost for A100
        waste_report = []
        total_waste = 0.0

        for anomaly in ctx.anomalies_detected:
            node_id = anomaly.get("node_id")
            # Heuristic: If detecting anomaly, assume efficiency dropped to 10%
            # Real world would compare actual vs expected TFLOPS
            
            inefficiency_factor = 0.9 # 90% wasted
            hourly_waste = GPU_HOURLY_RATE * inefficiency_factor
            total_waste += hourly_waste
            
            waste_report.append({
                "node_id": node_id,
                "hourly_waste_usd": hourly_waste,
                "reason": ctx.diagnosis
            })

        # AI Storytelling
        system_prompt = "You are a FinOps Auditor. The hourly cost of a GPU is $2.50. Calculate the wasted money based on inefficiency. Formula: Cost * (Current_Latency / Ideal_Latency). Report the dollar amount."
        user_prompt = f"Waste Report: {json.dumps(waste_report)}. Write a punchy financial impact statement."
        
        story = ask_io_intelligence(system_prompt, user_prompt)
        
        logger.warning(f"Accountant: Total waste calculated: ${total_waste}/hr. Story generated.")
        
        ctx.financial_report = {
            "total_waste_hourly": total_waste,
            "details": waste_report,
            "story": story
        }
        
        return ctx.financial_report, story


class EnforcerAgent(BaseAgent):
    """
    Role: System Admin
    Goal: Take action based on financial thresholds.
    """
    async def _process(self, ctx: AnalysisContext) -> tuple[dict, str]:
        if not ctx.financial_report:
            return {}, "No financial report to act on."

        THRESHOLD_USD = 0.50 # Updated from 1.0 to 0.50 per blueprint
        actions = []
        
        details = ctx.financial_report.get("details", [])
        for item in details:
            if item["hourly_waste_usd"] > THRESHOLD_USD:
                node_id = item["node_id"]
                logger.warning(f"Enforcer: EXECUTION ORDER. Killing {node_id} due to financial waste ${item['hourly_waste_usd']}/hr")
                state.kill_worker(node_id) # Execute Kill
                actions.append(f"KILLED {node_id} (Wasting ${item['hourly_waste_usd']:.2f}/hr)")
            else:
                logger.info(f"Enforcer: Monitoring {item['node_id']} (Waste acceptable)")
                actions.append(f"BSERVED {item['node_id']} (Waste below threshold)")

        ctx.actions_taken = actions
        
        if not actions:
             return {}, "No actions taken."
             
        msg = " | ".join(actions)
        return {"actions": actions}, msg
