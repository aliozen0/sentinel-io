import json
from .base import BaseAgent
from models import AnalysisContext, VramAnalysisContext
from ai_client import ask_io_intelligence, ask_io_intelligence_async
from state_manager import state
from logger import get_logger

logger = get_logger("Agents")

class WatchdogAgent(BaseAgent):
    """
    Step 1: Monitors telemetry for PHYSICS VIOLATIONS.
    e.g. Temp > 90C OR (Fan > 90% AND Temp increasing) OR (Latency > 0.5s AND Low Load)
    """
    async def _process(self, ctx: AnalysisContext) -> tuple[dict, str]:
        # 1. Get Telemetry Snapshot
        active_workers = {k: v.dict() for k, v in ctx.telemetry_snapshot.items()}
        
        # 2. Prepare Data for AI (Flattened)
        worker_list = []
        for wid, data in active_workers.items():
            worker_list.append({
                "id": wid,
                "lat": round(data.get("latency", 0), 3),
                "temp": round(data.get("temperature", 0), 1),
                "fan": round(data.get("fan_speed", 0), 1),
                "clock": round(data.get("clock_speed", 100), 1),
                "load": round(data.get("gpu_util", 0), 1)
            })
            
        if not worker_list:
            return {}, "No workers to analyze."

        system_prompt = (
            "You are a Physics Engine Watchdog. Analyze worker telemetry for anomalies. "
            "PHYSICS RULES:"
            "1. High Temp (>90C) is CRITICAL."
            "2. High Fan (>90%) with High Temp (>85C) means Cooling Failure."
            "3. Low Clock (<90%) means Thermal Throttling."
            "4. Latency > 1.0s is High."
            "Return ONLY JSON: {\"anomalies\": [{\"node_id\": \"...\", \"reason\": \"Thermal Throttling (Clock 50%)\"}]}. "
        )
        user_prompt = f"Telemetry: {json.dumps(worker_list)}"
        
        logger.info(f"Watchdog: Scanning {len(worker_list)} nodes for physics violations...")
        response_text = await ask_io_intelligence_async(system_prompt, user_prompt)
        
        # 3. Parse Response
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
                
            data = json.loads(response_text)
            anomalies = data.get("anomalies", [])
            
            ctx.anomalies_detected = anomalies
            
            if anomalies:
                return {"anomalies": anomalies}, f"Watchdog detected {len(anomalies)} physics violations."
            else:
                return {"anomalies": []}, "All systems within physics tolerances."
                
        except Exception as e:
            return {}, f"Watchdog failed: {e}"

class DiagnosticianAgent(BaseAgent):
    """
    Step 2: Diagnoses COMPONENT FAILURE based on Physics Data.
    """
    async def _process(self, ctx: AnalysisContext) -> tuple[dict, str]:
        if not ctx.anomalies_detected:
            return {}, "No anomalies to diagnose."

        diagnoses = []
        
        for anomaly in ctx.anomalies_detected:
            node_id = anomaly.get("node_id")
            reason = anomaly.get("reason")
            
            # Fetch full telemetry for this node
            tdata = ctx.telemetry_snapshot.get(node_id)
            if not tdata: continue
            
            metrics = f"Temp: {tdata.temperature}C, Fan: {tdata.fan_speed}%, Clock: {tdata.clock_speed}%, Latency: {tdata.latency}s"
            
            system_prompt = (
                "You are a Hardware Engineer. Diagnose the Root Cause. "
                "scenarios:"
                "- Temp High + Fan High + Clock Low = 'Active Cooling Failure' (Fan working but not cooling -> Dust/Paste issue?)"
                "- Temp High + Fan Low = 'Fan Motor Failure' (Fan not spinning)."
                "- Latency High + Temp Normal = 'Network Congestion'."
                "Output ONLY the Root Cause Name from: [Fan Motor Failure, Thermal Paste Degraded, Network Congestion, Unknown]."
            )
            
            cause = await ask_io_intelligence_async(system_prompt, f"Node: {node_id}, Issue: {reason}. Metrics: {metrics}")
            diagnoses.append({"node_id": node_id, "classification": cause})
        
        ctx.diagnosis = diagnoses[0]["classification"] if diagnoses else "Unknown"
        return {"diagnoses": diagnoses}, f"Diagnosed: {[d['classification'] for d in diagnoses]}"

class AccountantAgent(BaseAgent):
    """
    Step 3: Calculates THERMAL WASTE ($).
    If Clock Speed is < 100%, we are paying 100% price for partial performance.
    """
    async def _process(self, ctx: AnalysisContext) -> tuple[dict, str]:
        if not ctx.anomalies_detected:
            return {}, "No waste."

        HOURLY_COST_GPU = 2.50
        waste_report = []
        total_waste = 0.0
        
        for anomaly in ctx.anomalies_detected:
            node_id = anomaly.get("node_id")
            tdata = ctx.telemetry_snapshot.get(node_id)
            if not tdata: continue
            
            # Throttling Calculation
            # 100% clock = 0 waste
            # 50% clock = 50% waste
            efficiency = tdata.clock_speed / 100.0
            waste_ratio = 1.0 - efficiency
            waste_usd = HOURLY_COST_GPU * waste_ratio
            
            if waste_usd > 0.01:
                waste_report.append({
                    "node_id": node_id,
                    "clock_speed": tdata.clock_speed,
                    "hourly_waste_usd": waste_usd
                })
                total_waste += waste_usd
            
        ctx.financial_report = {
            "total_waste_hourly": total_waste,
            "details": waste_report,
            "story": f"Thermal throttling is costing ${total_waste:.2f}/hr in lost compute."
        }
        
        return ctx.financial_report, ctx.financial_report["story"]

class EnforcerAgent(BaseAgent):
    """
    Step 4: DIGITAL REPAIR. 
    Tries to repair components via API first. If that fails (or logic dictates), then maybe escalate (not impl here).
    """
    async def _process(self, ctx: AnalysisContext) -> tuple[dict, str]:
        if not ctx.anomalies_detected:
            return {}, "No actions needed."
            
        actions = []
        # Use httpx for async requests
        import httpx
        BACKEND_URL = "http://localhost:8000" # Internal reference
        
        # Iterate over diagnoses
        # Ensure we have diagnoses in context, if not, use anomalies
        targets = ctx.anomalies_detected
        
        async with httpx.AsyncClient() as client:
            for tgt in targets:
                node_id = tgt.get("node_id")
                # Try to infer repair action from diagnosis if available
                # For this demo, we assume "Fan Motor Failure" -> Repair
                
                # Send REPAIR command
                try:
                    # We use the generic repair endpoint which acts like a "Technician Visit"
                    await client.post(f"{BACKEND_URL}/chaos/repair/{node_id}", timeout=2.0)
                    actions.append(f"DISPATCHED TECHNICIAN (Repair) to {node_id}")
                except Exception as e:
                    actions.append(f"FAILED to contact repair dispatch for {node_id}: {e}")

        ctx.actions_taken = actions
        return {"actions": actions}, ", ".join(actions) if actions else "No actions needed."

# --- v3.0 Agentic VRAM Oracle Agents ---

class CodeParserAgent(BaseAgent):
    async def _process(self, ctx: VramAnalysisContext) -> tuple[dict, str]:
        logger.info("CodeParser: Analyzing python script...")
        system_prompt = (
            "You are a Deep Learning Code Expert. Analyze the script. "
            "Extract: Model Architecture (e.g. Llama-3, ResNet), "
            "Precision (fp16/fp32/bf16), Batch Size, Optimizer Type (Adam/SGD), Sequence Length. "
            "Return ONLY JSON keys: model, precision, batch_size, optimizer, seq_len."
        )
        user_prompt = f"Code: {ctx.code_snippet[:1500]}..."
        
        response = await ask_io_intelligence_async(system_prompt, user_prompt)
        
        try:
             # Extract JSON logic
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response
            
            metadata = json.loads(json_str)
            ctx.parsed_metadata = metadata
            return metadata, f"Extracted metadata: {metadata.get('model', 'Unknown')}"
        except Exception as e:
            logger.error("CodeParser JSON Error")
            return {}, f"Failed to parse code metadata: {str(e)}"

class VRAMCalculatorAgent(BaseAgent):
    async def _process(self, ctx: VramAnalysisContext) -> tuple[dict, str]:
        if not ctx.parsed_metadata:
            return {}, "Missing metadata."
            
        logger.info("VRAMCalculator: Computing memory requirements...")
        system_prompt = (
            "You are a Hardware Engineer. Calculate total VRAM usage in GB. "
            "Rules: Model Weights ~2 bytes/param fp16. Optimizer ~8 bytes/param. "
            "Gradients ~2 bytes. Activations depends on batch/seq_len. "
            "Output ONLY JSON: {\"breakdown\": {\"weights\": float, \"optimizer\": float, \"activations\": float}, \"total_gb\": float}"
        )
        user_prompt = f"Metadata: {json.dumps(ctx.parsed_metadata)}"
        
        response = await ask_io_intelligence_async(system_prompt, user_prompt)
        
        try:
            # Extract JSON logic
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response
                
            vram_data = json.loads(json_str)
            ctx.vram_usage = vram_data
            return vram_data, f"Estimated VRAM: {vram_data.get('total_gb')} GB"
        except Exception:
            return {}, "Failed to calculate VRAM."

class OptimizationAdvisorAgent(BaseAgent):
    async def _process(self, ctx: VramAnalysisContext) -> tuple[dict, str]:
        if not ctx.vram_usage:
            return {}, "No VRAM data."
            
        total_gb = ctx.vram_usage.get("total_gb", 0)
        target = 24.0 # RTX 4090 standard
        
        logger.info(f"Advisor: Checking if {total_gb}GB fits on {target}GB card...")
        
        if total_gb <= target:
            msg = "Fits perfectly on 24GB card."
            ctx.optimization_story = msg
            return {}, msg
        else:
            system_prompt = (
                f"User needs {total_gb}GB but has {target}GB. "
                "Suggest 3 technical optimizations (e.g. Gradient Accumulation, LoRA, QLoRA, CPU Offload). Be specific."
            )
            user_prompt = "Provide advice."
            
            advice = await ask_io_intelligence_async(system_prompt, user_prompt)
            ctx.optimization_story = advice
            return {"advice": advice}, "Optimization needed."
