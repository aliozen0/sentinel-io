from abc import ABC, abstractmethod
from models import AnalysisContext, VramAnalysisContext, AgentResponse
from typing import Optional, Union
from logger import get_logger

logger = get_logger("BaseAgent")

class BaseAgent(ABC):
    """
    Abstract Base Agent defining the interface and common behavior (Template Method).
    """
    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    async def execute(self, ctx: Union[AnalysisContext, VramAnalysisContext]) -> Union[AnalysisContext, VramAnalysisContext]:
        """
        Template method that executes the agent's logic and logs the result.
        """
        logger.info(f"⚡ [{self.agent_id.upper()}] Activation started. Context ID: {ctx.session_id}")
        print(f"[{self.agent_id}] specific processing started...")
        try:
            # Delegate specific logic to concrete classes
            result_data, message = await self._process(ctx)
            
            logger.debug(f"[{self.agent_id.upper()}] Process complete. Msg: {message}")
            
            response = AgentResponse(
                agent_id=self.agent_id,
                data=result_data,
                message=message
            )
            ctx.log_agent_response(response)
            
        except Exception as e:
            logger.error(f"[{self.agent_id.upper()}] CRITICAL FAILURE: {str(e)}", exc_info=True)
            error_response = AgentResponse(
                agent_id=self.agent_id,
                data={"error": str(e)},
                message=f"Agent failed: {str(e)}"
            )
            ctx.log_agent_response(error_response)
            print(f"[{self.agent_id}] Error: {e}")
            
        return ctx

    @abstractmethod
    async def _process(self, ctx: Union[AnalysisContext, VramAnalysisContext]) -> tuple[dict, str]:
        """
        Abstract method to be implemented by concrete agents.
        Returns: (data_dict, human_readable_message)
        """
        pass
