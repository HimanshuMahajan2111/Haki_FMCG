"""
Workflow API - Trigger multi-agent RFP processing workflow.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from datetime import datetime
import structlog

from db.database import get_db
from db.models import RFP
from agents.master_agent import MasterAgent
from agents.sales_agent_worker import SalesAgentWorker
from agents.technical_agent_worker import TechnicalAgentWorker
from agents.pricing_agent_worker import PricingAgentWorker
from agents.product_repository import ProductRepository

router = APIRouter(prefix="/api/workflow", tags=["workflow"])
logger = structlog.get_logger()

# Initialize agents
product_repo = ProductRepository()
sales_agent = SalesAgentWorker()
technical_agent = TechnicalAgentWorker(product_repository=product_repo)
pricing_agent = PricingAgentWorker()
master_agent = MasterAgent(
    technical_agent=technical_agent,
    pricing_agent=pricing_agent
)


@router.post("/process-rfp")
async def process_rfp_workflow(
    rfp_id: int = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Trigger complete multi-agent RFP processing workflow.
    
    Flow:
    1. Sales Agent selects RFP (if rfp_id not provided)
    2. Master Agent starts workflow
    3. Technical Agent recommends top 3 products per item
    4. Pricing Agent calculates material + test costs
    5. Master Agent consolidates final response
    
    Args:
        rfp_id: Optional RFP ID to process. If not provided, Sales Agent selects one.
        db: Database session
        
    Returns:
        Consolidated response with OEM SKUs, prices, and test costs
    """
    logger.info("🚀 Starting multi-agent RFP processing workflow")
    
    try:
        # Step 1: Select RFP (Sales Agent or by ID)
        if rfp_id is None:
            logger.info("📋 Step 1: Sales Agent selecting RFP from database")
            
            # Sales Agent identifies RFPs for next 3 months
            identified_rfps = await sales_agent.identify_rfps_for_next_3_months(db)
            
            if not identified_rfps:
                raise HTTPException(
                    status_code=404,
                    detail="No RFPs found due in next 3 months"
                )
            
            # Sales Agent selects one RFP based on priority
            selected_rfp_data = await sales_agent.select_one_rfp_for_processing(
                identified_rfps
            )
            
            rfp_id = selected_rfp_data['id']
            
            logger.info(
                f"✅ Sales Agent selected RFP: {selected_rfp_data['title']}",
                rfp_id=rfp_id,
                priority_score=selected_rfp_data['priority_score']
            )
        else:
            logger.info(f"📋 Step 1: Using provided RFP ID: {rfp_id}")
        
        # Get RFP from database
        result = await db.execute(
            select(RFP).where(RFP.id == rfp_id)
        )
        rfp = result.scalar_one_or_none()
        
        if not rfp:
            raise HTTPException(
                status_code=404,
                detail=f"RFP with ID {rfp_id} not found"
            )
        
        # Convert RFP to dict for processing
        rfp_data = {
            'rfp_id': rfp.id,
            'rfp_title': rfp.title,
            'organization': rfp.buyer_organization,
            'rfp_number': rfp.rfp_number,
            'due_date': rfp.due_date.isoformat() if rfp.due_date else None,
            'status': rfp.status,
            'raw_text': rfp.raw_text or '',
            'file_path': rfp.file_path,
            'specifications': rfp.structured_data or {},
            'structured_data': rfp.structured_data or {}
        }
        
        logger.info(
            f"🎯 Processing RFP: {rfp.title}",
            organization=rfp.buyer_organization,
            rfp_number=rfp.rfp_number
        )
        
        # Step 2: Master Agent starts workflow
        logger.info("🧠 Step 2: Master Agent starting workflow")
        
        result = await master_agent.start_workflow(rfp_data)
        
        logger.info(
            "🎉 Workflow completed successfully",
            rfp_id=rfp_id,
            products_recommended=len(result.get('recommended_products', [])),
            grand_total=result.get('total_costs', {}).get('grand_total', 0)
        )
        
        # Update RFP status
        rfp.status = 'processed'
        rfp.processed_at = datetime.now()
        await db.commit()
        
        return {
            'success': True,
            'rfp_id': rfp_id,
            'rfp_title': rfp.title,
            'organization': rfp.buyer_organization,
            'workflow_result': result,
            'processed_at': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Workflow processing failed: {str(e)}"
        )


@router.post("/process-next-rfp")
async def process_next_rfp(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process next RFP automatically selected by Sales Agent.
    
    This endpoint lets Sales Agent select the highest priority RFP
    from those due in next 3 months.
    """
    return await process_rfp_workflow(rfp_id=None, db=db)


@router.get("/pending-rfps")
async def get_pending_rfps(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get list of RFPs pending processing (due in next 3 months).
    
    Returns list identified by Sales Agent with priority scores.
    """
    logger.info("📊 Fetching pending RFPs for next 3 months")
    
    try:
        sales_worker = SalesAgentWorker()
        identified_rfps = await sales_worker.identify_rfps_for_next_3_months(db)
        
        return {
            'success': True,
            'count': len(identified_rfps),
            'rfps': identified_rfps,
            'retrieved_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching pending RFPs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch pending RFPs: {str(e)}"
        )


@router.get("/workflow-status")
async def get_workflow_status() -> Dict[str, Any]:
    """Get status of all agents in the workflow."""
    return {
        'success': True,
        'agents': {
            'master_agent': {
                'status': 'ready',
                'total_processed': master_agent.total_processed,
                'total_value_processed': master_agent.total_value_processed,
                'avg_processing_time': master_agent.avg_processing_time
            },
            'sales_agent': {
                'status': 'ready',
                'monitored_websites': sales_agent.monitored_websites
            },
            'technical_agent': {
                'status': 'ready',
                'product_count': len(product_repo.get_all_products()),
                'manufacturers': product_repo.get_manufacturers()
            },
            'pricing_agent': {
                'status': 'ready',
                'pricing_table': 'loaded'
            }
        },
        'workflow_ready': True,
        'timestamp': datetime.now().isoformat()
    }
