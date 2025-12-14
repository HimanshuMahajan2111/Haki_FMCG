"""RFP Processor service - orchestrates RFP processing."""
from datetime import datetime
from typing import Dict, Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models import RFP, RFPStatus
from agents.orchestrator import AgentOrchestrator

logger = structlog.get_logger()


class RFPProcessor:
    """Process RFPs through agent system."""
    
    def __init__(self, db: AsyncSession):
        """Initialize RFP processor.
        
        Args:
            db: Database session
        """
        self.db = db
        self.orchestrator = AgentOrchestrator()
        self.logger = logger.bind(component="RFPProcessor")
    
    async def process(
        self,
        rfp_id: int,
        rfp_data: Dict[str, Any]
    ):
        """Process an RFP.
        
        Args:
            rfp_id: RFP database ID
            rfp_data: Extracted RFP data
        """
        self.logger.info("Starting RFP processing", rfp_id=rfp_id)
        
        # Get RFP from database
        query = select(RFP).where(RFP.id == rfp_id)
        result = await self.db.execute(query)
        rfp = result.scalar_one()
        
        # Update status
        rfp.status = RFPStatus.PROCESSING
        await self.db.commit()
        
        try:
            # Process through agent orchestrator
            start_time = datetime.utcnow()
            
            result = await self.orchestrator.process_rfp(
                rfp_id=rfp_id,
                rfp_data=rfp_data
            )
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Extract results
            technical_result = result.get("technical_result", {}).get("result", {})
            pricing_result = result.get("pricing_result", {}).get("result", {})
            
            # Update RFP with results
            rfp.matched_products = technical_result.get("matched_products", [])
            rfp.pricing_data = pricing_result
            rfp.confidence_score = technical_result.get("average_confidence", 0)
            rfp.processing_time_seconds = duration
            rfp.processed_at = datetime.utcnow()
            rfp.status = RFPStatus.REVIEWED
            
            await self.db.commit()
            
            self.logger.info(
                "RFP processing completed",
                rfp_id=rfp_id,
                duration=duration,
                status="success"
            )
            
        except Exception as e:
            self.logger.error(
                "RFP processing failed",
                rfp_id=rfp_id,
                error=str(e)
            )
            
            rfp.status = RFPStatus.DISCOVERED
            await self.db.commit()
            
            raise
