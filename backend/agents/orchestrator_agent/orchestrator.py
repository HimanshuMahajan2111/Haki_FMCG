"""Agent Orchestrator - Coordinates parallel agent execution."""
import asyncio
from datetime import datetime
from typing import Any, Dict, List
import structlog

from agents.technical_agent import TechnicalAgent
from agents.pricing_agent import PricingAgent
from config.settings import settings

logger = structlog.get_logger()


class AgentOrchestrator:
    """Orchestrates parallel execution of multiple agents."""
    
    def __init__(self):
        """Initialize orchestrator with agents."""
        self.technical_agent = TechnicalAgent(
            model=settings.technical_agent_model
        )
        self.pricing_agent = PricingAgent(
            model=settings.pricing_agent_model
        )
        
        self.parallel_execution = settings.parallel_execution
    
    async def process_rfp(
        self,
        rfp_id: int,
        rfp_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process RFP through all agents.
        
        Args:
            rfp_id: RFP database ID
            rfp_data: Extracted RFP data containing requirements
            
        Returns:
            Combined results from all agents
        """
        start_time = datetime.utcnow()
        
        logger.info(
            "Starting RFP processing",
            rfp_id=rfp_id,
            parallel=self.parallel_execution
        )
        
        try:
            if self.parallel_execution:
                # Execute agents in parallel
                results = await self._execute_parallel(rfp_id, rfp_data)
            else:
                # Execute agents sequentially
                results = await self._execute_sequential(rfp_id, rfp_data)
            
            end_time = datetime.utcnow()
            total_duration = (end_time - start_time).total_seconds()
            
            # Combine results
            combined_result = {
                "rfp_id": rfp_id,
                "processing_start": start_time.isoformat(),
                "processing_end": end_time.isoformat(),
                "total_duration_seconds": total_duration,
                "technical_result": results.get("technical"),
                "pricing_result": results.get("pricing"),
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            logger.info(
                "RFP processing completed",
                rfp_id=rfp_id,
                duration=total_duration,
                status="success"
            )
            
            return combined_result
            
        except Exception as e:
            logger.error(
                "RFP processing failed",
                rfp_id=rfp_id,
                error=str(e)
            )
            
            return {
                "rfp_id": rfp_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def _execute_parallel(
        self,
        rfp_id: int,
        rfp_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agents in parallel.
        
        Args:
            rfp_id: RFP ID
            rfp_data: RFP data
            
        Returns:
            Results from all agents
        """
        logger.info("Executing agents in parallel", rfp_id=rfp_id)
        
        # Prepare input for technical agent
        technical_input = {
            "rfp_requirements": rfp_data.get("requirements", []),
            "rfp_text": rfp_data.get("raw_text", ""),
            "compliance_standards": rfp_data.get("standards", []),
        }
        
        # Execute technical and pricing agents in parallel
        # Note: Pricing agent needs technical results, so we do this in two stages
        
        # Stage 1: Technical agent
        technical_result = await self.technical_agent.execute(
            rfp_id=rfp_id,
            input_data=technical_input
        )
        
        # Stage 2: Pricing agent (can run after technical completes)
        pricing_input = {
            "matched_products": technical_result["result"].get("matched_products", []),
            "quantities": rfp_data.get("quantities", {}),
            "pricing_strategy": rfp_data.get("pricing_strategy", "competitive"),
        }
        
        pricing_result = await self.pricing_agent.execute(
            rfp_id=rfp_id,
            input_data=pricing_input
        )
        
        return {
            "technical": technical_result,
            "pricing": pricing_result,
        }
    
    async def _execute_sequential(
        self,
        rfp_id: int,
        rfp_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agents sequentially.
        
        Args:
            rfp_id: RFP ID
            rfp_data: RFP data
            
        Returns:
            Results from all agents
        """
        logger.info("Executing agents sequentially", rfp_id=rfp_id)
        
        # Execute technical agent first
        technical_input = {
            "rfp_requirements": rfp_data.get("requirements", []),
            "rfp_text": rfp_data.get("raw_text", ""),
            "compliance_standards": rfp_data.get("standards", []),
        }
        
        technical_result = await self.technical_agent.execute(
            rfp_id=rfp_id,
            input_data=technical_input
        )
        
        # Then execute pricing agent with technical results
        pricing_input = {
            "matched_products": technical_result["result"].get("matched_products", []),
            "quantities": rfp_data.get("quantities", {}),
            "pricing_strategy": rfp_data.get("pricing_strategy", "competitive"),
        }
        
        pricing_result = await self.pricing_agent.execute(
            rfp_id=rfp_id,
            input_data=pricing_input
        )
        
        return {
            "technical": technical_result,
            "pricing": pricing_result,
        }
    
    def get_all_statistics(self) -> Dict[str, Any]:
        """Get statistics from all agents.
        
        Returns:
            Combined statistics
        """
        return {
            "technical_agent": self.technical_agent.get_statistics(),
            "pricing_agent": self.pricing_agent.get_statistics(),
        }
