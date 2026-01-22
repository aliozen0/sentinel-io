import logging
import json
from typing import List, Dict, Any
from state_manager import state
from ai_client import ask_io_intelligence_async

logger = logging.getLogger("ChatAgent")

class ChatAgent:
    """
    Project-Aware Chat Assistant.
    Has access to:
    - Last analysis results (Auditor/Sniper)
    - Deployment status
    - Project context
    """
    
    SYSTEM_PROMPT = """You are the io-Guard Intelligent Assistant.
You are a Senior ML Engineer and DevOps Specialist.
Your goal is to help the user with:
1. Understanding code analysis results (Auditor reports).
2. Choosing the right GPU hardware (Sniper recommendations).
3. Debugging deployment issues.
4. Optimizing ML training code.

CONTEXT AWARENESS:
You have access to the "Current Project State" in the system message. 
ALWAYS use this data to answer questions.
If the user asks "Why did you recommend X?", check the analysis results.

TONE:
Professional, technical, but helpful. Be concise.
"""

    @staticmethod
    async def chat(messages: List[Dict[str, str]], model: str = None) -> str:
        """
        Processes chat messages with context injection.
        """
        # 1. Build Context
        context_str = "CURRENT PROJECT STATE:\n"
        
        # Add Last Analysis
        if state.last_analysis:
            analysis = state.last_analysis
            context_str += f"""
[LAST ANALYSIS RESULT]
- Framework: {analysis.get('summary', {}).get('framework', 'Unknown')}
- VRAM Required: {analysis.get('summary', {}).get('vram_required', 'Unknown')}
- Health Score: {analysis.get('summary', {}).get('health_score', 'N/A')}
- Recommended GPU: {analysis.get('summary', {}).get('recommended_gpu', 'N/A')}
- Critical Issues: {len(analysis.get('audit', {}).get('critical_issues', []))} found
"""
            # Add top recommendation details
            if analysis.get('market_recommendations'):
                top = analysis['market_recommendations'][0]
                context_str += f"- Top Match: {top.get('gpu_model')} (${top.get('price_hourly')}/hr, Score: {top.get('score'):.2f})\n"
        else:
            context_str += "[No analysis run yet]\n"
            
        # Add Recent Logs (Last 5)
        recent_logs = state.get_agent_logs(limit=5)
        if recent_logs:
            context_str += "\n[RECENT SYSTEM ACTIVITY]\n"
            for log in recent_logs:
                context_str += f"- {log.get('agent', 'System')}: {log.get('action') or log.get('message')}\n"

        # 2. Prepare Prompt
        # We inject context into the latest system message or prepend it
        full_system_prompt = f"{ChatAgent.SYSTEM_PROMPT}\n\n{context_str}"
        
        # Convert messages to format expected by AI client if needed
        # But here we just take the user's last message and append history context if possible
        # For simplicity in this v1, we'll send the full history to the LLM if the API supports it,
        # otherwise we just send the last message + context.
        
        # Since our `ask_io_intelligence` takes (system, user), we'll format history into user prompt
        # or just assume the frontend handles history display and we only answer the last query.
        
        last_user_msg = messages[-1]['content']
        
        # Include a summary of previous turns if short
        history_context = ""
        if len(messages) > 1:
            history_context = "\nCHAT HISTORY:\n"
            for m in messages[:-1]:
                history_context += f"{m['role'].upper()}: {m['content']}\n"
        
        final_user_prompt = f"{history_context}\nUSER: {last_user_msg}"

        logger.info("Chat Agent thinking with context...")
        
        # 3. Call LLM
        response = await ask_io_intelligence_async(
            system_prompt=full_system_prompt,
            user_prompt=final_user_prompt,
            model=model
        )
        
        return response
