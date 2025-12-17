"""RFP-related API endpoints."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import structlog

from db.database import get_db
from db.models import RFP, RFPStatus
from api.schemas import RFPResponse, RFPProcessRequest, RFPScanRequest
from services.rfp_scanner import RFPScanner
from services.rfp_processor import RFPProcessor

logger = structlog.get_logger()
router = APIRouter()


@router.post("/scan")
async def scan_rfps(
    request: RFPScanRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Scan RFP directory for new documents.
    
    Args:
        request: Scan request with force_rescan flag
        background_tasks: Background task handler
        db: Database session
        
    Returns:
        Scan results
    """
    scanner = RFPScanner(db)
    
    # Run scan in background
    background_tasks.add_task(
        scanner.scan_directory,
        force_rescan=request.force_rescan
    )
    
    return {
        "message": "RFP scan initiated",
        "force_rescan": request.force_rescan
    }


@router.get("/latest")
async def get_latest_rfps(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get latest RFPs with enriched data.
    
    Args:
        limit: Maximum number of RFPs to return
        db: Database session
        
    Returns:
        List of latest RFPs with calculated fields
    """
    query = select(RFP).order_by(desc(RFP.created_at)).limit(limit)
    result = await db.execute(query)
    rfps = result.scalars().all()
    
    enriched_rfps = []
    for rfp in rfps:
        # Calculate days remaining
        days_remaining = None
        if rfp.due_date:
            delta = rfp.due_date - datetime.utcnow()
            days_remaining = delta.days
        
        # Extract structured data fields
        import json
        structured = rfp.structured_data
        if isinstance(structured, str):
            try:
                structured = json.loads(structured)
            except:
                structured = {}
        structured = structured or {}
        buyer = structured.get('buyer', 'Unknown Buyer')
        category = structured.get('category', 'Electrical')
        quantity = structured.get('quantity', '')
        
        # Calculate estimated value (mock for now based on category)
        estimated_value = 5000000  # Default 50L
        if 'solar' in category.lower():
            estimated_value = 15000000
        elif 'signaling' in category.lower():
            estimated_value = 8000000
        elif 'power' in category.lower():
            estimated_value = 12000000
        
        enriched_rfps.append({
            "id": rfp.id,
            "title": rfp.title,
            "source": rfp.source,
            "due_date": rfp.due_date.isoformat() if rfp.due_date else None,
            "status": rfp.status.value,
            "days_remaining": days_remaining,
            "created_at": rfp.created_at.isoformat(),
            "customer": buyer,
            "buyer": buyer,
            "category": category,
            "quantity": quantity,
            "estimated_value": estimated_value,
            "confidence_score": rfp.confidence_score or 0.75,
            "processing_time_seconds": rfp.processing_time_seconds,
            "file_path": rfp.file_path,
            "raw_text": rfp.raw_text[:500] if rfp.raw_text else "",  # First 500 chars
        })
    
    return {
        "success": True,
        "data": {
            "rfps": enriched_rfps
        }
    }


@router.get("/history")
async def get_rfp_history(
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get RFP processing history with enriched data.
    
    Args:
        limit: Maximum number of records
        db: Database session
        
    Returns:
        RFP history with full details
    """
    # Get all RFPs, not just processed ones, ordered by creation date
    query = select(RFP).order_by(desc(RFP.created_at)).limit(limit)
    result = await db.execute(query)
    rfps = result.scalars().all()
    
    history_records = []
    for rfp in rfps:
        structured = rfp.structured_data or {}
        buyer = structured.get('buyer', 'Unknown Buyer')
        category = structured.get('category', 'Electrical')
        
        history_records.append({
            "id": rfp.id,
            "title": rfp.title,
            "buyer": buyer,
            "category": category,
            "status": rfp.status.value,
            "processed_at": rfp.processed_at.isoformat() if rfp.processed_at else rfp.created_at.isoformat(),
            "created_at": rfp.created_at.isoformat(),
            "processing_time": rfp.processing_time_seconds or 0,
            "confidence_score": rfp.confidence_score or 0.0,
            "source": rfp.source,
            "file_path": rfp.file_path,
        })
    
    return {
        "success": True,
        "data": {
            "history": history_records
        }
    }


@router.post("/process")
async def process_rfp(
    request: RFPProcessRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Process an RFP through the agent system.
    
    Args:
        request: RFP processing request
        background_tasks: Background task handler
        db: Database session
        
    Returns:
        Processing status
    """
    # Get RFP from database
    query = select(RFP).where(RFP.id == request.rfp_id)
    result = await db.execute(query)
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    # Start processing in background
    processor = RFPProcessor(db)
    background_tasks.add_task(
        processor.process,
        rfp_id=request.rfp_id,
        rfp_data=request.rfp_data
    )
    
    return {
        "message": "RFP processing initiated",
        "rfp_id": request.rfp_id,
        "status": "processing"
    }


@router.get("/{rfp_id}")
async def get_rfp(
    rfp_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get RFP details by ID.
    
    Args:
        rfp_id: RFP ID
        db: Database session
        
    Returns:
        RFP details
    """
    query = select(RFP).where(RFP.id == rfp_id)
    result = await db.execute(query)
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    return {
        "data": {
            "id": rfp.id,
            "title": rfp.title,
            "source": rfp.source,
            "due_date": rfp.due_date.isoformat() if rfp.due_date else None,
            "status": rfp.status.value,
            "requirements": rfp.requirements,
            "structured_data": rfp.structured_data,
            "matched_products": rfp.matched_products,
            "pricing_data": rfp.pricing_data,
            "confidence_score": rfp.confidence_score,
            "processing_time_seconds": rfp.processing_time_seconds,
        }
    }
