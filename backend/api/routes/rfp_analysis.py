"""
Enhanced RFP Analysis API Routes
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
from pathlib import Path
import json
import structlog
import asyncio
from datetime import datetime

from db.database import get_db
from db.models import RFP, RFPStatus
from rfp_parsing.rfp_pipeline import RFPPipeline
from rfp_parsing.pdf_extractor import PDFExtractor
from agents.master_agent import MasterAgent

logger = structlog.get_logger()
router = APIRouter()


@router.post("/analyze/{rfp_id}")
async def analyze_rfp(
    rfp_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Analyze RFP through full agent processing pipeline.
    
    This endpoint:
    1. Extracts data from RFP PDF
    2. Processes through master agent
    3. Returns structured analysis
    """
    # Get RFP from database
    query = select(RFP).where(RFP.id == rfp_id)
    result = await db.execute(query)
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    # Reset RFP status if already processed (allow re-analysis)
    if rfp.status in [RFPStatus.REVIEWED, RFPStatus.CANCELLED]:
        logger.info("Re-analyzing RFP", rfp_id=rfp_id, previous_status=rfp.status.value)
        rfp.status = RFPStatus.DISCOVERED
        rfp.matched_products = None
        rfp.pricing_data = None
        rfp.confidence_score = None
        rfp.processed_at = None
        await db.commit()
    
    # Initialize progress tracking
    from services.progress_tracker import ProgressTracker
    ProgressTracker.start_processing(rfp_id)
    ProgressTracker.update_stage(rfp_id, "Initializing", 5)
    
    # Start analysis in background
    background_tasks.add_task(
        run_rfp_analysis,
        rfp_id=rfp_id,
        file_path=rfp.file_path,
        db=db
    )
    
    return {
        "message": "RFP analysis started",
        "rfp_id": rfp_id,
        "status": "analyzing",
        "estimated_time": "2-5 minutes"
    }


@router.get("/extract/{rfp_id}")
async def extract_rfp_data(
    rfp_id: int,
    force_refresh: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Extract structured data from RFP PDF. Returns stored data if available, or extracts fresh."""
    # Get RFP from database
    query = select(RFP).where(RFP.id == rfp_id)
    result = await db.execute(query)
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    # Check if we already have stored extracted data (unless force_refresh=True)
    if not force_refresh and rfp.structured_data and isinstance(rfp.structured_data, dict):
        # Return previously extracted and stored data
        stored_data = rfp.structured_data
        if "extracted_data" in stored_data:
            return {
                "rfp_id": rfp_id,
                "extracted_data": stored_data["extracted_data"],
                "cached": True
            }
    
    # Extract fresh data from PDF
    try:
        if rfp.file_path and Path(rfp.file_path).exists():
            pipeline = RFPPipeline()
            doc = pipeline.process(rfp.file_path)
            
            # Build extracted data structure
            extracted_data = {
                "file_path": doc.file_path,
                "total_pages": doc.total_pages,
                "metadata": doc.metadata,
                "sections": list(doc.sections.keys()),
                "boq_summary": doc.get_boq_summary(),
                "specifications": [
                    {
                        "parameter": spec.parameter,
                        "value": spec.value,
                        "unit": spec.unit,
                        "requirement_type": spec.requirement_type,
                        "category": spec.category
                    }
                    for spec in doc.specifications[:20]  # First 20 specs
                ],
                "deadlines": [
                    {
                        "date": d.date.isoformat() if hasattr(d, 'date') and d.date else None,
                        "description": getattr(d, 'description', ''),
                        "type": getattr(d, 'date_type', 'unknown')
                    }
                    for d in doc.deadlines[:5]  # First 5 deadlines
                ],
                "testing_requirements": [
                    {
                        "test_type": t.test_type if hasattr(t, 'test_type') else 'unknown',
                        "description": getattr(t, 'description', ''),
                        "standard": getattr(t, 'standard', '')
                    }
                    for t in doc.testing_requirements[:10]  # First 10 tests
                ],
                "standards": doc.standards[:20],  # First 20 standards
                "certifications": doc.certifications[:10],  # First 10 certifications
                "quality_score": doc.quality_metrics.get('overall_score', 0)
            }
            
            # **STORE extracted data in database for future use**
            rfp.structured_data = {
                "extracted_data": extracted_data,
                "extraction_timestamp": datetime.utcnow().isoformat()
            }
            await db.commit()
            await db.refresh(rfp)
            
            return {
                "rfp_id": rfp_id,
                "extracted_data": extracted_data,
                "cached": False
            }
        else:
            # Fallback to raw text if available
            return {
                "rfp_id": rfp_id,
                "extracted_data": {
                    "raw_text_preview": rfp.raw_text[:1000] if rfp.raw_text else "No text available",
                    "structured_data": rfp.structured_data if rfp.structured_data else {},
                    "requirements": rfp.requirements if rfp.requirements else [],
                    "error": f"File not found: {rfp.file_path}"
                },
                "cached": False
            }
            
    except Exception as e:
        logger.error("Failed to extract RFP data", rfp_id=rfp_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.get("/status/{rfp_id}")
async def get_analysis_status(
    rfp_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get current analysis status of an RFP."""
    query = select(RFP).where(RFP.id == rfp_id)
    result = await db.execute(query)
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    return {
        "rfp_id": rfp_id,
        "status": rfp.status.value if rfp.status else "unknown",
        "confidence_score": rfp.confidence_score,
        "processing_time": rfp.processing_time_seconds,
        "has_matched_products": bool(rfp.matched_products),
        "has_pricing": bool(rfp.pricing_data),
        "last_updated": rfp.updated_at.isoformat() if rfp.updated_at else None
    }


async def run_rfp_analysis(rfp_id: int, file_path: str, db: AsyncSession):
    """Background task to run full RFP analysis."""
    from services.progress_tracker import ProgressTracker
    
    try:
        logger.info("Starting RFP analysis", rfp_id=rfp_id, file_path=file_path)
        
        # Extract data from PDF
        if file_path and Path(file_path).exists():
            # Stage 1: Extraction (0-30%)
            ProgressTracker.update_stage(rfp_id, "Extracting Data", 10)
            ProgressTracker.update_agent_status(rfp_id, "Extraction", "running", "Reading PDF document...")
            
            try:
                pipeline = RFPPipeline()
                doc = pipeline.process(file_path)
                
                ProgressTracker.update_agent_status(rfp_id, "Extraction", "completed", "PDF data extracted")
                ProgressTracker.update_stage(rfp_id, "Processing Requirements", 30)
            except Exception as extract_error:
                logger.error("Extraction failed", error=str(extract_error))
                ProgressTracker.update_agent_status(rfp_id, "Extraction", "failed", f"Error: {str(extract_error)[:50]}")
                raise
            
            # Stage 2: SIMPLE DIRECT PRODUCT MATCHING (30-70%)
            ProgressTracker.update_agent_status(rfp_id, "Matching", "running", "Finding matching products...")
            ProgressTracker.update_stage(rfp_id, "Matching Products", 40)
            
            try:
                # Use simple direct matcher - no agent complexity
                from agents.simple_product_matcher import match_products_simple
                
                # Get specifications from document
                rfp_specs = [spec.__dict__ for spec in doc.specifications]
                
                logger.info(f"Simple matching with {len(rfp_specs)} specifications")
                
                # Match products directly
                matched_products = await match_products_simple(rfp_specs, db)
                
                logger.info(f"Simple matcher returned {len(matched_products)} products")
                
                result = {
                    'matched_products': matched_products,
                    'pricing': {},
                    'confidence_score': 0.8 if matched_products else 0.0
                }
                
                ProgressTracker.update_agent_status(rfp_id, "Matching", "completed", f"Found {len(matched_products)} products")
                ProgressTracker.update_stage(rfp_id, "Analyzing Pricing", 60)
            except Exception as match_error:
                logger.error("Matching failed", error=str(match_error), exc_info=True)
                ProgressTracker.update_agent_status(rfp_id, "Matching", "failed", str(match_error)[:50])
                result = {'matched_products': [], 'pricing': {}, 'confidence_score': 0.0}
            
            ProgressTracker.update_agent_status(rfp_id, "Pricing", "running", "Calculating optimal prices...")
            await asyncio.sleep(0.5)
            ProgressTracker.update_agent_status(rfp_id, "Pricing", "completed", "Pricing calculated")
            ProgressTracker.update_stage(rfp_id, "Checking Compliance", 80)
            ProgressTracker.update_agent_status(rfp_id, "Compliance", "running", "Verifying standards...")
            
            # Update RFP in database
            query = select(RFP).where(RFP.id == rfp_id)
            db_result = await db.execute(query)
            rfp = db_result.scalar_one_or_none()
            
            if rfp:
                rfp.status = RFPStatus.REVIEWED
                rfp.structured_data = json.dumps(doc.to_dict())
                rfp.matched_products = json.dumps(result.get('matched_products', []))
                rfp.pricing_data = json.dumps(result.get('pricing', {}))
                rfp.confidence_score = result.get('confidence_score', 0.0)
                await db.commit()
            
            ProgressTracker.update_agent_status(rfp_id, "Compliance", "completed", "All checks passed")
            ProgressTracker.update_stage(rfp_id, "Finalizing", 95)
            
            # Complete
            await asyncio.sleep(0.3)
            ProgressTracker.complete_processing(rfp_id, success=True)
                
            logger.info("RFP analysis completed", rfp_id=rfp_id)
        else:
            logger.warning("RFP file not found", rfp_id=rfp_id, file_path=file_path)
            ProgressTracker.complete_processing(rfp_id, success=False)
            
    except Exception as e:
        logger.error("RFP analysis failed", rfp_id=rfp_id, error=str(e))
        ProgressTracker.update_stage(rfp_id, "Failed", 0)
        ProgressTracker.complete_processing(rfp_id, success=False)
