import json
import logging
import asyncio
from typing import List, Dict, Any
from .base import BaseAgent
from models import AnalysisContext
from ai_client import ask_io_intelligence_async
from state_manager import state

logger = logging.getLogger("OracleAgent")

class OracleAgent(BaseAgent):
    """
    The Oracle: Senior Reliability Engineer Agent.
    Performs Multivariate Time-Series Analysis to predict failures BEFORE they happen.
    """
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.last_run_time = 0
        self.run_interval = 10  # Seconds (Don't spam LLM)

    async def _process(self, ctx: AnalysisContext) -> tuple[dict, str]:
        import time
        now = time.time()
        
        # 1. Rate Limiting (Oracle is expensive)
        # Only run if forced (e.g. by Watchdog trigger) OR interval passed
        is_emergency = len(ctx.anomalies_detected) > 0
        if not is_emergency and (now - self.last_run_time < self.run_interval):
            return {}, "Oracle skipped (Standing by)."
            
        self.last_run_time = now
        
        # 2. Gather Time-Series Data
        predictions = []
        workers = state.get_all_workers()
        
        target_workers = []
        if is_emergency:
            # Focus on anomalies first
            target_ids = [a["node_id"] for a in ctx.anomalies_detected]
            target_workers = [(wid, workers[wid]) for wid in target_ids if wid in workers]
        else:
            # Routine scan of random active worker (to save costs/latency)
            active_workers = [(wid, w) for wid, w in workers.items() if w["status"] == "Active"]
            if active_workers:
                import random
                target_workers = [random.choice(active_workers)] # Pick 1 for routine check
                
        if not target_workers:
            return {}, "No active targets for prediction."

        for wid, wdata in target_workers:
            history = state.get_worker_history(wid)
            if len(history) < 10:
                continue # Need minimum data for trend calculation

            # 3. Pre-Calculate Derivatives (Multivariate Features)
            # We construct a CSV-like string for the LLM
            csv_data = "TimeDelta,Temp,Fan,Load,CoolingEff\n"
            
            # Use last 10 ticks inverted (Oldest -> Newest)
            recent_history = history[-15:] 
            start_time = float(0)
            
            for i, point in enumerate(recent_history):
                # Calculate Cooling Efficiency: Heat Removal per Fan %
                # Simple proxy: if Fan is high and Temp is rising fast, Eff is low.
                temp = point.get("temperature", 0)
                fan = point.get("fan_speed", 0)
                load = point.get("gpu_util", 0)
                
                # Cooling Eff = 100 if Fan=0 (Undefined but safe)
                # If Fan > 0: Eff = 1 / (Temp / Fan) ... logic needs to be intuitive for LLM
                # Better: Just give raw data, let LLM correlate.
                # But we add a calculated field "Eff": Fan / Temp (Higher is better cooling per degree)
                # Actually, standard is Rth (Thermal Resistance). 
                # Let's stick to raw inputs + basic ratio.
                
                eff = round(fan / max(1, temp), 2)
                
                csv_data += f"T-{len(recent_history)-i},{temp:.1f},{fan:.1f},{load:.1f},{eff}\n"

            # 4. Enterprise Prompt Engineering
            system_prompt = (
                "You are an Oracle AI (Senior SRE). Predict Hardware Failure. "
                "Analyze the Time-Series CSV below. "
                "Columns: TimeDelta (T-0 is now), Temp(C), Fan(%), Load(%), CoolingEff.\n"
                "Physics Rules:\n"
                "1. DRIFT: If Temp rises but Load is constant -> Thermal Paste/Dust issue.\n"
                "2. SATURATION: If Fan=100% and Temp > 85C -> Cooling Failure Imminent.\n"
                "3. OSCILLATION: If Fan seesaws up/down rapidly -> Controller Failure.\n\n"
                "TASK:\n"
                "1. Extrapolate Temp for T+10 (Future).\n"
                "2. Calculate Probability of Failure (0-100%).\n\n"
                "OUTPUT ONLY JSON: {\"node_id\": \"...\", \"predicted_temp_t10\": float, \"fail_prob\": int, \"root_cause\": \"...\", \"advice\": \"...\"}"
            )
            
            user_prompt = f"Node: {wid}\nData:\n{csv_data}"
            
            try:
                logger.info(f"Oracle: Gazing into the future of {wid}...")
                response = await ask_io_intelligence_async(system_prompt, user_prompt)
                
                # Robust JSON parsing
                json_str = response
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0].strip()
                    
                pred_data = json.loads(json_str)
                pred_data["node_id"] = wid # Ensure ID is set
                pred_data["evidence"] = csv_data # <--- PROOF: Show the data we analyzed
                predictions.append(pred_data)
                
            except Exception as e:
                logger.error(f"Oracle Vision Failed: {e}")
                
        # 5. Inject Predictions into Context
        ctx.agent_logs.append({
            "agent_id": "oracle",
            "data": {"predictions": predictions},
            "message": f"Oracle generated {len(predictions)} prophecies."
        })
        
        # If High Failure Prob, Upgrade to Anomaly automatically
        for pred in predictions:
            if pred.get("fail_prob", 0) > 70:
                ctx.anomalies_detected.append({
                    "node_id": pred["node_id"],
                    "reason": f"ORACLE PREDICTION: {pred.get('root_cause')} (Prob: {pred.get('fail_prob')}%)"
                })

        return {"predictions": predictions}, "Oracle Analysis Complete."
