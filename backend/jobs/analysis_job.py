import asyncio
import logging
from typing import Dict, Any, Optional
import time
import os

from agents.auditor import Auditor
from agents.architect import Architect
from agents.sniper import Sniper
from db.client import get_db

logger = logging.getLogger("io-guard-core")

async def run_analysis_bg(job_id: str, code: str, user_id: str, budget: float, model_name: str):
    """
    Background task to run the full analysis pipeline.
    Updates job status and metadata in DB at each step.
    """
    print(f"DEBUG: run_analysis_bg CALLED for {job_id}", flush=True)
    try:
        db = get_db()
        
        # Initial Update
        pipeline_trace = []
        
        def update_job_progress(status: str, result: Optional[Dict] = None, trace: Optional[list] = None):
            """Helper to update job in DB"""
            try:
                # job = db.get_job(job_id) # Optimization: Update blindly or assume exists (it was created in main)
                # existing_meta = job.get("metadata", {}) if job else {}
                
                # We need to fetch current metadata to preserve other fields?
                # For simplicity/speed in MVP, we might overwrite specific fields or merge.
                # Here we assume we can just merge into what we have in memory (pipeline_trace)
                # But better to fetch to be safe in case of race? background task is single writer usually.
                
                # Fetching latest state
                job = db.get_job(job_id)
                existing_meta = job.get("metadata", {}) if job else {}

                new_meta = {
                    **existing_meta,
                    "pipeline_trace": trace if trace else existing_meta.get("pipeline_trace", []),
                    "final_result": result if result else existing_meta.get("final_result")
                }
                db.update_job(job_id, status=status, metadata=new_meta)
            except Exception as e:
                logger.error(f"Failed to update job {job_id}: {e}")

        logger.info(f"🚀 Starting Analysis Job {job_id} for user {user_id}")
        update_job_progress("RUNNING", trace=pipeline_trace)
        
        api_base = os.getenv("IO_BASE_URL", "api.intelligence.io.solutions")

        # === STEP 1: Auditor ===
        step1_start = time.time()
        pipeline_trace.append({
            "step": 1, 
            "agent": "Auditor", 
            "status": "running",
            "action": "Sending code to LLM for analysis...",
            "details": {
                "model": model_name,
                "api": api_base.replace("https://", "").replace("/api/v1/", ""),
                "code_length": len(code)
            }
        })
        update_job_progress("RUNNING", trace=pipeline_trace)

        audit_report = await Auditor.analyze_code(code, model=model_name)
        step1_time = round(time.time() - step1_start, 2)
        
        pipeline_trace[0]["status"] = "completed"
        pipeline_trace[0]["duration_sec"] = step1_time
        pipeline_trace[0]["result"] = {
            "framework": audit_report.framework,
            "vram": f"{audit_report.vram_min_gb} GB",
            "health_score": audit_report.health_score,
            "issues_found": len(audit_report.critical_issues)
        }
        update_job_progress("RUNNING", trace=pipeline_trace)

        # === STEP 2: Architect ===
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
        update_job_progress("RUNNING", trace=pipeline_trace)

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
        update_job_progress("RUNNING", trace=pipeline_trace)

        # === STEP 3: Sniper ===
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
        update_job_progress("RUNNING", trace=pipeline_trace)
        
        # Real Sniper Call
        best_nodes = await Sniper.get_best_nodes(
            budget_hourly=budget, 
            gpu_model=gpu_model
        )
        
        market_nodes = [node.dict() for node in best_nodes]
        
        step3_time = round(time.time() - step3_start, 2)
        pipeline_trace[2]["status"] = "completed"
        pipeline_trace[2]["duration_sec"] = step3_time
        pipeline_trace[2]["result"] = {
            "nodes_found": len(market_nodes),
            "best_price": f"${best_nodes[0].price_hourly}/hr" if best_nodes else "N/A"
        }

        # Final Result Construction
        total_time = round(step1_time + step2_time + step3_time, 2)

        final_result = {
            "summary": {
                "framework": audit_report.framework,
                "recommended_gpu": gpu_model,
                "vram_required": f"{audit_report.vram_min_gb} GB",
                "estimated_setup": f"~{int(audit_report.vram_min_gb * 0.5)} min",
                "health_score": audit_report.health_score
            },
            "audit": audit_report.dict(),
            "environment": env_config.dict(),
            "market_recommendations": market_nodes, # FIXED: Renamed from market_nodes to match frontend
            "pipeline_trace": pipeline_trace
        }

        update_job_progress("COMPLETED", result=final_result, trace=pipeline_trace)
        logger.info(f"✅ Job {job_id} Completed Successfully")
        print(f"DEBUG: Job {job_id} DONE", flush=True)

    except Exception as e:
        logger.error(f"❌ Job {job_id} Failed: {e}")
        print(f"DEBUG: Job {job_id} FAILED: {e}", flush=True)
        # Check if pipeline_trace is defined (in case error happened before init)
        if 'pipeline_trace' not in locals(): pipeline_trace = []
        
        pipeline_trace.append({
            "step": 99, "agent": "System", "status": "failed", "action": f"Error: {str(e)}"
        })
        try:
            # Try to update DB even if failed
            # Try to update DB even if failed
            if 'db' not in locals(): 
                # Fallback if db wasn't initialized, try to get it using global import
                try:
                    db = get_db()
                except:
                   pass
            
            if 'db' in locals() and db:
                job = db.get_job(job_id)
            existing_meta = job.get("metadata", {}) if job else {}
            new_meta = {
                **existing_meta,
                "pipeline_trace": pipeline_trace
            }
            db.update_job(job_id, status="FAILED", metadata=new_meta)
        except:
             pass
