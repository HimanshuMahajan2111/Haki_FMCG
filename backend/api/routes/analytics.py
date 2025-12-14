"""Analytics API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from db.database import get_db
from db.models import RFP, Product, AgentLog, RFPStatus

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_analytics(
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard analytics.
    
    Args:
        db: Database session
        
    Returns:
        Dashboard statistics
    """
    # Total products
    product_count_query = select(func.count(Product.id))
    product_result = await db.execute(product_count_query)
    total_products = product_result.scalar()
    
    # Total RFPs
    rfp_count_query = select(func.count(RFP.id))
    rfp_result = await db.execute(rfp_count_query)
    total_rfps = rfp_result.scalar()
    
    # Processed RFPs
    processed_query = select(func.count(RFP.id)).where(
        RFP.status.in_([RFPStatus.REVIEWED, RFPStatus.APPROVED, RFPStatus.SUBMITTED])
    )
    processed_result = await db.execute(processed_query)
    processed_rfps = processed_result.scalar()
    
    # Processing rate
    processing_rate = (processed_rfps / total_rfps * 100) if total_rfps > 0 else 0
    
    # Average processing time
    avg_time_query = select(func.avg(RFP.processing_time_seconds)).where(
        RFP.processing_time_seconds.isnot(None)
    )
    avg_time_result = await db.execute(avg_time_query)
    avg_processing_time = avg_time_result.scalar() or 0
    
    return {
        "total_products": total_products,
        "total_rfps": total_rfps,
        "processed_rfps": processed_rfps,
        "processing_rate": round(processing_rate, 2),
        "avg_processing_time_seconds": round(avg_processing_time, 2),
    }


@router.get("/trends")
async def get_trends(
    db: AsyncSession = Depends(get_db)
):
    """Get processing trends.
    
    Args:
        db: Database session
        
    Returns:
        Trend data
    """
    # This would typically include time-series data
    # For now, return basic statistics
    
    return {
        "message": "Trends endpoint - implement time-series queries",
        "data": {}
    }
