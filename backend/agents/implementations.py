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
                "load": round(data.get("gpu_util", 0), 1),
                "integrity": data.get("integrity", "UNKNOWN")
            })

        # 2a. SECURITY CHECK (PoC)
        spoofed_nodes = [w for w in worker_list if w["integrity"] == "SPOOFED"]
        if spoofed_nodes:
             anomalies = []
             for w in spoofed_nodes:
                 anomalies.append({
                     "node_id": w["id"],
                     "reason": "CRITICAL: Signature Spoofing Detected (PoC Violation)"
                 })
             ctx.anomalies_detected = anomalies
             return {"anomalies": anomalies}, f"🚨 SECURITY BREACH: {len(spoofed_nodes)} nodes failed signature check!"
            
        if not worker_list:
            return {}, "No workers to analyze."

        # 2b. PRE-PROCESSING: Calculate Raw Efficiency Metrics
        # This gives the LLM quantitative data to reason about, rather than just "high/low"
        for w in worker_list:
            # Normalized metrics (0.0 - 1.0)
            temp_score = max(0, 1.0 - (w["temp"] / 100.0)) # 100C = 0.0
            clock_score = w["clock"] / 100.0 # 100% = 1.0
            latency_score = max(0, 1.0 - w["lat"]) # 1s latency = 0.0
            
            # Weighted Efficiency Index (WEI)
            # Performance (Clock) is king, but Stability (Temp/Lat) is queen.
            w["efficiency_index"] = round((clock_score * 0.4) + (temp_score * 0.3) + (latency_score * 0.3), 2)

        # HYBRID APPROACH: Data-Driven Prompts
        # We pass the Calculated Efficiency Index to the LLM.
        # This allows the Agent to decide "Is 0.65 efficiency critical in this context?"
        
        system_prompt = (
            "You are an Advanced Infrastructure Intelligence. Analyze worker telemetry. "
            "metrics include a computed 'efficiency_index' (0.0-1.0). "
            "GOAL: Ensure User Experience. "
            "Use the efficiency_index as a STRONG signal, but provide your own severity assessment. "
            "GUIDELINES: "
            "1. Efficiency < 0.7 usually implies 'Performance Degradation' (Medium Severity). "
            "2. Efficiency < 0.4 implies 'Functional Failure' (Critical Severity). "
            "3. Look for correlations: Low Efficiency + High Temp = Thermal Throttling. "
            "Return JSON with 'anomalies': [{'node_id': '...', 'reason': 'Efficiency dropped to 0.65 due to Throttling. Recommended Preemptive Failover.', 'severity': 'MEDIUM'|'CRITICAL'}]"
        )
        user_prompt = f"Telemetry with Efficiency Indexes: {json.dumps(worker_list)}"
        
        logger.info(f"Watchdog: asking AI to analyze efficiency for {len(worker_list)} nodes...")
        response_text = await ask_io_intelligence_async(system_prompt, user_prompt)
        
        # 3. Parse Response
        try:
            # Sanity Check for API Errors
            if response_text.startswith("AI Error") or "Error" in response_text[:20]:
                logger.error(f"Watchdog AI Failure: {response_text}")
                return {}, f"Result: System Healthy (AI Unreachable: {response_text[:50]}...)"

            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
                
            data = json.loads(response_text)
            anomalies = data.get("anomalies", [])
            
            # Add raw score context for downstream agents
            for a in anomalies:
                node = next((w for w in worker_list if w["id"] == a["node_id"]), None)
                if node:
                    a["efficiency"] = node.get("efficiency_index", 0.0)
            
            ctx.anomalies_detected = anomalies
            
            if anomalies:
                return {"anomalies": anomalies}, f"Watchdog AI flagged {len(anomalies)} anomalies."
            else:
                return {"anomalies": []}, "AI analysis indicates healthy cluster."
                
        except json.JSONDecodeError:
            logger.error(f"Watchdog Malformed JSON: {response_text}")
            return {}, "Result: System Healthy (AI Response Malformed)"
        except Exception as e:
            logger.error(f"Watchdog Logic Error: {e}")
            return {}, f"Watchdog Logic Error: {str(e)}"

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
        from state_manager import state
        
        # TOKENOMICS ENGINE (DETERMINISTIC)
        total_impact = 0.0
        details = []
        
        # 1. Calculate Rewards (Proof-of-Uptime)
        active_workers = state.get_all_workers()
        for wid, info in active_workers.items():
            if info.get("status") == "Active":
                 reward = 0.01
                 total_impact += reward
                 # details.append(f"{wid}: +{reward}") # Too noisy
        
        # 2. Calculate Slashing (Penalties)
        # We analyze the SNAPSHOT provided in context
        telemetry_map = ctx.telemetry_snapshot
        
        penalty_reasons = []
        
        for wid, tdata in telemetry_map.items():
            # Rule 1: Safety (Signatures) - handled by Watchdog but we penalize here too if flagged
            if tdata.integrity == "SPOOFED":
                slashed = -100.0
                total_impact += slashed
                penalty_reasons.append(f"{wid} SPOOF (-100 $IO)")
            
            # Rule 2: Performance (Latency)
            if tdata.latency > 0.5:
                slashed = -5.0
                total_impact += slashed
                penalty_reasons.append(f"{wid} LATENCY > 0.5s (-5 $IO)")
                
            # Rule 3: Hardware (Temp)
            if tdata.temperature > 95.0:
                slashed = -10.0
                total_impact += slashed
                penalty_reasons.append(f"{wid} OVERHEAT (-10 $IO)")
        
        # 3. Update Ledger
        if len(penalty_reasons) > 0:
            summary = ", ".join(penalty_reasons)
        else:
            summary = "Uptime Rewards"
            
        state.update_ledger(total_impact, summary)
        
        report = {
            "total_impact": total_impact,
            "period": "10s",
            "balance": state.ledger["balance"],
            "slashed": state.ledger["slashed"]
        }
        
        ctx.financial_report = report
        
        msg = f"Financial Impact: {total_impact:+.2f} $IO. "
        if penalty_reasons:
            msg += f"Penalties: {', '.join(penalty_reasons[:3])}..."
            
        return report, msg

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
        # SRE Manager Prompt
        # Holistic Decision Making
        system_prompt = (
            "You are the SRE Manager. Your goal is MAXIMAL USER EXPERIENCE (SLA 99.9%). "
            "Review the anomalies provided by the Watchdog AI (which include efficiency scores). "
            "DECISION MATRIX:"
            "1. If Severity 'CRITICAL' -> FAILOVER IMMEDIATELY (Safety First)."
            "2. If Severity 'MEDIUM' AND Standby Node Available -> FAILOVER (Proactive Optimization)."
            "3. If Severity 'MEDIUM' AND No Standby -> RESTART (Attempt to clear software locks)."
            "4. If 'Minor' -> REPAIR request."
            "REASONING: Explain WHY you chose the action. E.g., 'Efficiency is 0.65, risking user lag. Switching to fresh standby node.'"
            "OUTPUT JSON: {\"node_id\": \"...\", \"action\": \"FAILOVER\"|\"RESTART\"|\"REPAIR\", \"reasoning\": \"...\"}"
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
            target_node = decision.get("node_id", intelligence_brief["anomalies"][0].get("node_id"))
            reason = decision.get("reasoning", "No reason provided.")
            
            # Execute Action
            BACKEND_URL = "http://localhost:8000"
            exec_log = f"DECISION: {action} on {target_node}. Reason: {reason}"
            
            async with httpx.AsyncClient() as client:
                if action == "REPAIR":
                    await client.post(f"{BACKEND_URL}/chaos/repair/{target_node}")
                elif action == "RESTART":
                     # Simulating restart by a quick repair actually
                    await client.post(f"{BACKEND_URL}/chaos/repair/{target_node}") 
                elif action == "FAILOVER":
                    from state_manager import state
                    
                    # 1. Cordon the inefficient node
                    state.transition_node(target_node, "CORDONED")
                    
                    # 2. Find replacement
                    standby = state.get_idle_node()
                    
                    if standby:
                        state.transition_node(standby, "ACTIVE")
                        msg = f"🚀 PREEMPTIVE FAILOVER: Swapped {target_node} (Inefficient) with {standby} (Fresh). {reason}"
                        logger.warning(msg)
                        exec_log = msg
                    else:
                        msg = f"⚠️ FAILOVER BLOCKED: No Standby nodes! keeping {target_node} online despite degradation."
                        logger.error(msg)
                        exec_log = msg
            
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
