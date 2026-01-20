import json
from .base import BaseAgent
from models import AnalysisContext, VramAnalysisContext
from ai_client import ask_io_intelligence
from state_manager import state
from logger import get_logger

logger = get_logger("Agents")

class WatchdogAgent(BaseAgent):
    """
    Step 1: Monitors telemetry for hardcoded thresholds (Latency > 0.5s, Temp > 85C).
    """
    async def _process(self, ctx: AnalysisContext) -> tuple[dict, str]:
        # 1. Get Telemetry Snapshot
        # Convert Pydantic models to dicts for clear JSON serialization
        active_workers = {k: v.dict() for k, v in ctx.telemetry_snapshot.items()}
        
        # 2. AI Analysis
        # Flatten data for easier AI parsing
        worker_list = []
        for wid, data in active_workers.items():
            worker_list.append({
                "id": wid,
                "lat": round(data.get("latency", 0), 2),
                "temp": round(data.get("temperature", 0), 1)
            })
            
        system_prompt = (
            "You are a Critical System Monitor. Review the list of worker metrics. "
            "Rules:"
            "1. IF lat > 0.5 OR temp > 80.0 -> ANOMALY."
            "2. IF lat > 3.0 -> CRITICAL ANOMALY."
            "Return ONLY JSON: {\"anomalies\": [{\"node_id\": \"...\", \"reason\": \"High Latency (X.Xs)\"}]}. "
            "If no anomalies, return {\"anomalies\": []}."
        )
        user_prompt = f"Metrics: {json.dumps(worker_list)}"
        
        logger.info(f"Watchdog: Analyzing {len(worker_list)} workers. Data: {user_prompt}")
        response_text = ask_io_intelligence(system_prompt, user_prompt)
        logger.debug(f"Watchdog: AI Raw Response: {response_text[:100]}...")
        
        # 3. Parse Response
        try:
            # Extract JSON from potential markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
                
            data = json.loads(response_text)
            anomalies = data.get("anomalies", [])
            
            ctx.anomalies_detected = anomalies
            
            if anomalies:
                return {"anomalies": anomalies}, f"Watchdog detected {len(anomalies)} anomalies."
            else:
                return {"anomalies": []}, "System healthy. No anomalies."
                
        except Exception as e:
            return {}, f"Watchdog AI parsing failed: {e}. Raw: {response_text}"

class DiagnosticianAgent(BaseAgent):
    """
    Step 2: Diagnoses the ROOT CAUSE of the anomaly (e.g., Thermal Throttling, Network).
    """
    async def _process(self, ctx: AnalysisContext) -> tuple[dict, str]:
        if not ctx.anomalies_detected:
            return {}, "No anomalies to diagnose."

        diagnoses = []
        
        for anomaly in ctx.anomalies_detected:
            node_id = anomaly.get("node_id")
            reason = anomaly.get("reason")
            
            # Fetch historical context from State Manager for better diagnosis
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
    Step 3: Calculates FINANCIAL WASTE ($) based on inefficiency.
    """
    async def _process(self, ctx: AnalysisContext) -> tuple[dict, str]:
        if not ctx.anomalies_detected:
            return {}, "No ineffiency to audit."

        HOURLY_COST_GPU = 2.50 # $2.50/hr for an A100 equivalent
        IDEAL_LATENCY = 0.10   # 100ms
        
        waste_report = []
        total_waste = 0.0
        
        for anomaly in ctx.anomalies_detected:
            node_id = anomaly.get("node_id")
            # Get current latency from snapshot
            current_lat = ctx.telemetry_snapshot[node_id].get("latency", 0.1)
            
            # Calculate Inefficiency Ratio
            # If latency represents processing time per token/request
            if current_lat > IDEAL_LATENCY:
                inefficiency = (current_lat - IDEAL_LATENCY) / current_lat
                waste_usd = HOURLY_COST_GPU * inefficiency
            else:
                waste_usd = 0
            
            total_waste += waste_usd
            waste_report.append({
                "node_id": node_id,
                "current_latency": current_lat,
                "hourly_waste_usd": waste_usd
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
    Step 4: Takes ACTION (Kill Node) if waste exceeds threshold.
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
        
        response = ask_io_intelligence(system_prompt, user_prompt)
        
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
        
        response = ask_io_intelligence(system_prompt, user_prompt)
        
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
            
            advice = ask_io_intelligence(system_prompt, user_prompt)
            ctx.optimization_story = advice
            return {"advice": advice}, "Optimization needed."
