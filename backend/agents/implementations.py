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
        from ai_client import ask_io_intelligence_async
        import json
        
        if not ctx.anomalies_detected:
            return {}, "No financial waste detected."

        # Prepare Data for the CFO Agent
        anomalies_context = []
        for anomaly in ctx.anomalies_detected:
            node_id = anomaly.get("node_id")
            tdata = ctx.telemetry_snapshot.get(node_id)
            if tdata:
                anomalies_context.append({
                    "id": node_id,
                    "issue": anomaly.get("reason"),
                    "telemetry": {
                        "temp": tdata.temperature,
                        "clock": tdata.clock_speed,
                        "fan": tdata.fan_speed,
                        "gpu_load": tdata.gpu_util
                    }
                })

        # IMPROVED: Agentic Financial prompting
        system_prompt = (
            "You are the CFO AI (Chief Financial Officer). "
            "Analyze the technical anomalies below and calculate financial impact. "
            "COST MODEL:\n"
            "- COMPUTE_LOSS: $2.50/hr per node if Clock < 100%.\n"
            "- POWER_WASTE: $0.50/hr per node if Fan > 90% (Inefficient).\n"
            "- RISK_PREMIUM: $15.00/hr per node if Temp > 90C (Meltdown Risk).\n\n"
            "INSTRUCTIONS:\n"
            "1. Calculate total waste for each node based on the model.\n"
            "2. Sum up to 'total_waste_hourly'.\n"
            "3. Write a SHORT, punchy executive summary (1 sentence).\n"
            "OUTPUT ONLY JSON: {\"total_waste_hourly\": float, \"details\": list, \"story\": string}"
        )
        
        user_prompt = f"Anomalies Detected:\n{json.dumps(anomalies_context, indent=2)}"
        
        try:
            response_text = await ask_io_intelligence_async(system_prompt, user_prompt)
            
            # JSON Parsing Logic
            json_str = response_text
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
                
            report = json.loads(json_str)
            ctx.financial_report = report
            return report, report.get("story", "Financial Analysis Complete.")
            
        except Exception as e:
            return {}, f"CFO Analysis Failed: {e}"

class EnforcerAgent(BaseAgent):
    """
    Step 4: SITE RELIABILITY MANAGER (The Boss).
    Decides on the Final Action based on:
    1. Diagnosis (Hardware Engineer)
    2. Financial Impact (CFO)
    """
    async def _process(self, ctx: AnalysisContext) -> tuple[dict, str]:
        from ai_client import ask_io_intelligence_async
        import httpx
        import json
        
        if not ctx.anomalies_detected:
            return {}, "System Healthy. No intervention required."
            
        # Gather Intelligence
        intelligence_brief = {
            "diagnoses": ctx.diagnosis, # List or string
            "financial_report": ctx.financial_report, # Dict from CFO
            "anomalies": ctx.anomalies_detected
        }
        
        # SRE Manager Prompt
        system_prompt = (
            "You are the SRE Manager (Site Reliability Engineering). "
            "make a FINAL DECISION based on the technical and financial reports. "
            "AVAILABLE ACTIONS:\n"
            "- REPAIR: Dispatch technician (Cost: $50 fixed). Use for 'Fan Failure', 'Thermal Paste' if Waste < $500.\n"
            "- RESTART: Remote reboot (Cost: $0, Downtime: 10s). Use for 'Software Glitch', 'Unknown', or low-cost throttling.\n"
            "- ISOLATE: Kill the node (Cost: $0, Capacity Loss). Use if Waste > $500/hr (Bleeding cash) OR Critical Meltdown Risk.\n"
            "- IGNORE: Do nothing. Use if waste is negligible (< $1.00).\n\n"
            "OUTPUT JSON: {\"node_id\": \"...\", \"action\": \"REPAIR\"|\"RESTART\"|\"ISOLATE\"|\"IGNORE\", \"reasoning\": \"...\"}"
        )
        
        user_prompt = f"Intelligence Brief:\n{json.dumps(intelligence_brief, indent=2)}"
        
        try:
            response_text = await ask_io_intelligence_async(system_prompt, user_prompt)
            
            # JSON Parsing
            json_str = response_text
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
                
            decision = json.loads(json_str)
            action = decision.get("action", "IGNORE").upper()
            target_node = decision.get("node_id", intelligence_brief["anomalies"][0]["node_id"])
            reason = decision.get("reasoning", "No reason provided.")
            
            # Execute Action
            BACKEND_URL = "http://localhost:8000"
            exec_log = f"DECISION: {action} on {target_node}. Reason: {reason}"
            
            async with httpx.AsyncClient() as client:
                if action == "REPAIR":
                    await client.post(f"{BACKEND_URL}/chaos/repair/{target_node}")
                elif action == "ISOLATE":
                    # In a real app this might stop the container. For now, maybe just log?
                    # Or we implement a 'kill' endpoint. Let's assume repair for now effectively 'resets' state
                    # But ideally we'd have a /stop endpoint.
                    await client.post(f"{BACKEND_URL}/chaos/repair/{target_node}") # Placeholder for Kill
                elif action == "RESTART":
                    # Restart logic (simulate by repair for demo simplicity, or add specific endpoint)
                    await client.post(f"{BACKEND_URL}/chaos/repair/{target_node}") 
            
            ctx.actions_taken.append(exec_log)
            return {"decision": decision}, exec_log
            
        except Exception as e:
            return {}, f"SRE Manager Panic: {e}"

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
