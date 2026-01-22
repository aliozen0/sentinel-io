import ast
import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
try:
    from backend.ai_client import ask_io_intelligence_async
except ImportError:
    # Fallback for local testing or if path issues
    from ai_client import ask_io_intelligence_async

logger = logging.getLogger(__name__)

class AuditReport(BaseModel):
    vram_min_gb: int = Field(..., description="Minimum VRAM required in GB")
    framework: str = Field(..., description="pytorch, tensorflow, or jax")
    health_score: int = Field(..., description="Code health score 0-100")
    critical_issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)

class Auditor:
    """
    Module 1: THE AUDITOR (Code Audit Engine)
    Analyzes user code using LLM (Llama-3-70B) or fallback AST.
    """
    
    SYSTEM_PROMPT = """
    You are a Senior AI Engineer & Code Auditor. 
    Analyze the provided Python training code. The input may contain multiple files concatenated with headers like '# === FILE: name ==='.
    
    Return ONLY a valid JSON object matching this schema:
    {
        "vram_min_gb": int, 
        "framework": "pytorch" | "tensorflow" | "jax",
        "health_score": int (0-100),
        "critical_issues": ["issue1", "issue2"],
        "suggestions": ["suggestion1"]
    }
    
    Guidelines:
    - If code uses 'cpu', estimate VRAM as if it were running on a standard GPU (e.g., batch size * model size).
    - Do NOT hallucinate 'missing imports' for files that are present in the context (check the FILE headers).
    - If the code is extremely broken or malicious, set health_score to 0.
    
    Do NOT return markdown formatting like ```json ... ```. Just the raw JSON string.
    """

    @staticmethod
    async def analyze_code(code: str, model: str = None) -> AuditReport:
        """
        Main entry point for code analysis.
        Tries LLM first, falls back to AST if LLM fails.
        """
        try:
            # 1. Try LLM with specified model
            logger.info(f"Sending code to LLM ({model or 'default'}) for audit...")
            llm_response = await ask_io_intelligence_async(
                system_prompt=Auditor.SYSTEM_PROMPT,
                user_prompt=f"CODE PROJECT CONTEXT:\n{code[:32000]}",  # Increased limit for projects
                model=model
            )
            
            # 2. Parse JSON
            cleaned_response = llm_response.strip().replace("```json", "").replace("```", "")
            data = json.loads(cleaned_response)
            return AuditReport(**data)
            
        except Exception as e:
            logger.warning(f"LLM Audit failed: {e}. Falling back to AST analysis.")
            return Auditor._fallback_ast_analysis(code)

    @staticmethod
    def _fallback_ast_analysis(code: str) -> AuditReport:
        """
        Simple static analysis using Python's ast module.
        """
        issues = []
        framework = "pytorch" # Default assumption
        vram = 8 # Safe default
        
        try:
            tree = ast.parse(code)
            
            # Check imports
            imports = [node.name for node in ast.walk(tree) if isinstance(node, ast.Import)]
            img_from_imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            all_imports = set(imports + [i for i in img_from_imports if i])
            
            if "tensorflow" in all_imports:
                framework = "tensorflow"
            elif "jax" in all_imports:
                framework = "jax"
            
            # Check for cuda device usage
            source_lower = code.lower()
            if "cuda" not in source_lower and "to(device)" not in source_lower:
                issues.append("No explicit CUDA device usage found. Ensure you are moving tensors to GPU.")
            
            return AuditReport(
                vram_min_gb=vram,
                framework=framework,
                health_score=60 if issues else 85,
                critical_issues=issues,
                suggestions=["Automated fallback analysis used. LLM unavailable."]
            )
            
        except SyntaxError as e:
            return AuditReport(
                vram_min_gb=0,
                framework="unknown",
                health_score=0,
                critical_issues=[f"Syntax Error: {str(e)}"],
                suggestions=["Fix syntax errors before submitting."]
            )
        except Exception as e:
             return AuditReport(
                vram_min_gb=0,
                framework="unknown",
                health_score=0,
                critical_issues=[f"Analysis Error: {str(e)}"],
                suggestions=[]
            )
