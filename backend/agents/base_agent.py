"""Base agent class for all specialized agents."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings


logger = structlog.get_logger()


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(
        self,
        agent_name: str,
        agent_type: str,
        model: Optional[str] = None,
    ):
        """Initialize agent.
        
        Args:
            agent_name: Unique name for the agent
            agent_type: Type of agent (technical, pricing, etc.)
            model: LLM model to use (optional)
        """
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.model = model or settings.default_llm_model
        self.logger = logger.bind(agent=agent_name, type=agent_type)
        
        self.execution_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results.
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Processed results
        """
        pass
    
    @retry(
        stop=stop_after_attempt(settings.max_agent_retries),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def execute(
        self,
        rfp_id: int,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent with retry logic and logging.
        
        Args:
            rfp_id: RFP ID being processed
            input_data: Input data for processing
            
        Returns:
            Execution results with metadata
        """
        start_time = datetime.utcnow()
        self.execution_count += 1
        
        self.logger.info(
            "Agent execution started",
            rfp_id=rfp_id,
            execution_number=self.execution_count
        )
        
        try:
            # Process the input
            result = await self.process(input_data)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Prepare execution metadata
            execution_result = {
                "status": "success",
                "agent_name": self.agent_name,
                "agent_type": self.agent_type,
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration_seconds": duration,
                "result": result,
                "metadata": {
                    "model": self.model,
                    "execution_count": self.execution_count,
                }
            }
            
            self.logger.info(
                "Agent execution completed",
                rfp_id=rfp_id,
                duration=duration,
                status="success"
            )
            
            return execution_result
            
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.error(
                "Agent execution failed",
                rfp_id=rfp_id,
                error=str(e),
                duration=duration
            )
            
            return {
                "status": "failed",
                "agent_name": self.agent_name,
                "agent_type": self.agent_type,
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration_seconds": duration,
                "error": str(e),
                "metadata": {
                    "model": self.model,
                    "execution_count": self.execution_count,
                }
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent execution statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "execution_count": self.execution_count,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost,
        }
