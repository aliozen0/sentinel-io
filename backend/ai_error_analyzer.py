"""
AI-powered error analysis helper for Step 6.
"""

async def analyze_deployment_error(error_log: str, script_content: str = "") -> dict:
    """
    Uses AI to deeply analyze deployment errors and suggest fixes.
    
    Args:
        error_log: Recent error log lines (last 10-20 lines)
        script_content: Optional script content for context
    
    Returns: {
        "root_cause": str,
        "suggested_fix": str,
        "confidence": int (0-100),
        "auto_fixable": bool
    }
    """
    from ai_client import ask_io_intelligence_async
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    prompt = f"""You are a DevOps debugging expert. Analyze this deployment error:

ERROR LOG:
{error_log}

SCRIPT (if available):
{script_content[:1000] if script_content else "N/A"}

Provide a JSON response with:
1. "root_cause": Brief explanation (1-2 sentences)
2. "suggested_fix": Specific command or code change
3. "confidence": 0-100% how sure you are
4. "auto_fixable": true if can be fixed via shell command

Format as valid JSON only, no markdown."""
    
    try:
        response = await ask_io_intelligence_async(prompt)
        
        # Parse JSON response
        # Remove markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
        
        return json.loads(cleaned)
    except Exception as e:
        logger.error(f"AI error analysis failed: {e}")
        return {
            "root_cause": "AI analysis unavailable",
            "suggested_fix": "Manual debugging required",
            "confidence": 0,
            "auto_fixable": False
        }
