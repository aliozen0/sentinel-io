import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv() 

BASE_URL = os.getenv("IO_BASE_URL", "https://api.intelligence.io.solutions/api/v1/")
API_KEY = os.getenv("IO_API_KEY")
MODEL_NAME = os.getenv("IO_MODEL_NAME", "meta-llama/Llama-3.3-70B-Instruct")

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

import asyncio

def ask_io_intelligence(system_prompt: str, user_prompt: str):
    """
    Sends a request to the io.net Intelligence API (Sync Wrapper).
    Warning: This blocks! Prefer strict usage in async wrappers or threads.
    """
    if not API_KEY or "sk-io-" in API_KEY and len(API_KEY) < 20: 
         return "Error: IO_API_KEY is not set or is invalid in .env"

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        content = response.choices[0].message.content
        
        # LOGGING (Brain Trace)
        try:
            from state_manager import state
            state.add_agent_log({
                "agent": "Brain (LLM)",
                "message": f"Thinking...\nPrompt: {system_prompt[:50]}...\nResponse: {content[:100]}...",
                "details": {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "response": content
                }
            })
        except ImportError:
            pass # Avoid circular import if any
            
        return content
    except Exception as e:
        return f"AI Error: {str(e)}"

async def ask_io_intelligence_async(system_prompt: str, user_prompt: str):
    """
    Async wrapper to prevent blocking the FastAPI Event Loop.
    """
    return await asyncio.to_thread(ask_io_intelligence, system_prompt, user_prompt)
