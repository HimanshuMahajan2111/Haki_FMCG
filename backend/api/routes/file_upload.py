"""
File Upload API - Upload RFP PDFs and Product CSVs

Endpoints:
- POST /api/upload/rfp-pdf         - Upload RFP PDF and start processing
- POST /api/upload/product-csv     - Upload product CSV for bulk import
- POST /api/upload/multiple-pdfs   - Upload multiple RFP PDFs
- GET  /api/upload/history         - Get upload history
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
import aiofiles
import os
from pathlib import Path
from datetime import datetime
import structlog
import hashlib

from db.database import get_db
from db.models import RFP, Product
from rfp_parsing.pdf_extractor import PDFExtractor
from rfp_parsing.boq_extractor import BOQExtractor
from api.routes.agent_logs import emit_agent_log
from agents.master_agent import MasterAgent
from agents.technical_agent_worker import TechnicalAgentWorker
from agents.pricing_agent_worker import PricingAgentWorker
from agents.product_repository import ProductRepository

router = APIRouter(prefix="/api/upload", tags=["upload"])
logger = structlog.get_logger()

# Upload directories
UPLOAD_DIR = Path("uploads")
RFP_UPLOAD_DIR = UPLOAD_DIR / "rfps"
PRODUCT_UPLOAD_DIR = UPLOAD_DIR / "products"

# Create directories if they don't exist
for directory in [UPLOAD_DIR, RFP_UPLOAD_DIR, PRODUCT_UPLOAD_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


async def save_upload_file(upload_file: UploadFile, destination: Path) -> Path:
    """Save uploaded file to destination."""
    async with aiofiles.open(destination, 'wb') as out_file:
        content = await upload_file.read()
        await out_file.write(content)
    return destination


def get_file_hash(file_path: Path) -> str:
    """Get SHA-256 hash of file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


@router.post("/rfp-pdf")
async def upload_rfp_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    process_immediately: bool = True,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload RFP PDF and optionally start processing.
    
    Args:
        file: PDF file
        process_immediately: If True, start agent processing immediately
        db: Database session
        
    Returns:
        Upload status and RFP ID
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted"
        )
    
    logger.info("Receiving RFP PDF upload", filename=file.filename)
    
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = file.filename.replace(" ", "_")
        file_path = RFP_UPLOAD_DIR / f"{timestamp}_{safe_filename}"
        
        # Save file
        saved_path = await save_upload_file(file, file_path)
        file_hash = get_file_hash(saved_path)
        
        logger.info("PDF saved", path=str(saved_path), hash=file_hash)
        
        # Extract PDF content
        pdf_extractor = PDFExtractor()
        extracted_data = await pdf_extractor.extract_from_file(str(saved_path))
        
        # Extract BOQ if present
        boq_extractor = BOQExtractor()
        boq_items = []
        
        if extracted_data.get('tables'):
            for table in extracted_data['tables']:
                items = boq_extractor.extract_from_dataframe(table)
                boq_items.extend([item.to_dict() for item in items])
        
        # Create RFP record in database
        rfp = RFP(
            title=extracted_data.get('title', file.filename),
            source='file_upload',
            status='uploaded',
            file_path=str(saved_path),
            file_hash=file_hash,
            raw_text=extracted_data.get('text', ''),
            structured_data={
                'filename': file.filename,
                'pages': extracted_data.get('pages', 0),
                'tables_found': len(extracted_data.get('tables', [])),
                'boq_items': boq_items,
                'metadata': extracted_data.get('metadata', {})
            }
        )
        
        db.add(rfp)
        await db.commit()
        await db.refresh(rfp)
        
        logger.info("RFP created in database", rfp_id=rfp.id)
        
        response = {
            "success": True,
            "message": "RFP PDF uploaded successfully",
            "data": {
                "rfp_id": rfp.id,
                "filename": file.filename,
                "file_path": str(saved_path),
                "pages": extracted_data.get('pages', 0),
                "tables_found": len(extracted_data.get('tables', [])),
                "boq_items_found": len(boq_items),
                "status": "uploaded"
            }
        }
        
        # Start processing if requested
        if process_immediately:
            workflow_id = f"wf_{rfp.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Emit initial log
            await emit_agent_log(
                workflow_id=workflow_id,
                agent="file_upload",
                message=f"RFP PDF uploaded: {file.filename}",
                level="info",
                data={
                    "rfp_id": rfp.id,
                    "filename": file.filename,
                    "pages": extracted_data.get('pages', 0)
                }
            )
            
            # Start background processing
            if background_tasks:
                background_tasks.add_task(
                    process_rfp_workflow,
                    rfp_id=rfp.id,
                    workflow_id=workflow_id,
                    db=db
                )
            
            response["data"]["workflow_id"] = workflow_id
            response["data"]["status"] = "processing"
            response["message"] = "RFP uploaded and processing started"
        
        return response
        
    except Exception as e:
        logger.error("Error uploading RFP PDF", error=str(e), filename=file.filename)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload RFP PDF: {str(e)}"
        )


async def process_rfp_workflow(rfp_id: int, workflow_id: str, db: AsyncSession):
    """
    Background task to process RFP through agent workflow.
    
    Args:
        rfp_id: RFP database ID
        workflow_id: Unique workflow ID
        db: Database session
    """
    try:
        await emit_agent_log(
            workflow_id=workflow_id,
            agent="workflow",
            message="Starting RFP processing workflow",
            level="info"
        )
        
        # Initialize agents
        product_repo = ProductRepository(use_database=True)
        technical_agent = TechnicalAgentWorker(product_repository=product_repo)
        pricing_agent = PricingAgentWorker()
        master_agent = MasterAgent(
            technical_agent=technical_agent,
            pricing_agent=pricing_agent
        )
        
        # Get RFP from database
        from sqlalchemy import select
        result = await db.execute(select(RFP).where(RFP.id == rfp_id))
        rfp = result.scalar_one_or_none()
        
        if not rfp:
            await emit_agent_log(
                workflow_id=workflow_id,
                agent="workflow",
                message=f"RFP {rfp_id} not found",
                level="error"
            )
            return
        
        # Update status
        rfp.status = 'processing'
        await db.commit()
        
        await emit_agent_log(
            workflow_id=workflow_id,
            agent="technical_agent",
            message="Analyzing RFP requirements",
            level="info"
        )
        
        # Prepare RFP data - parse JSON if string
        import json
        structured = rfp.structured_data
        if isinstance(structured, str):
            try:
                structured = json.loads(structured)
            except:
                structured = {}
        structured = structured or {}
        
        rfp_data = {
            'rfp_id': rfp.id,
            'title': rfp.title,
            'raw_text': rfp.raw_text,
            'boq_items': structured.get('boq_items', []),
            'requirements': structured.get('requirements', [])
        }
        
        # Process through master agent
        result = await master_agent.start_workflow(rfp_data)
        
        # Update RFP with results
        rfp.status = 'completed'
        rfp.processed_at = datetime.now()
        rfp.processing_time_seconds = result.processing_time_seconds
        rfp.confidence_score = result.confidence_score
        rfp.result_data = result.to_dict()
        
        await db.commit()
        
        await emit_agent_log(
            workflow_id=workflow_id,
            agent="workflow",
            message="RFP processing completed successfully",
            level="success",
            data={
                "rfp_id": rfp_id,
                "products_recommended": len(result.recommended_products),
                "processing_time": result.processing_time_seconds
            }
        )
        
    except Exception as e:
        logger.error("Error in workflow processing", error=str(e), rfp_id=rfp_id)
        
        await emit_agent_log(
            workflow_id=workflow_id,
            agent="workflow",
            message=f"Workflow failed: {str(e)}",
            level="error"
        )
        
        # Update RFP status
        result = await db.execute(select(RFP).where(RFP.id == rfp_id))
        rfp = result.scalar_one_or_none()
        if rfp:
            rfp.status = 'failed'
            await db.commit()


@router.post("/multiple-pdfs")
async def upload_multiple_rfp_pdfs(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload multiple RFP PDFs at once.
    
    Args:
        files: List of PDF files
        db: Database session
        
    Returns:
        Upload status for all files
    """
    results = []
    
    for file in files:
        try:
            result = await upload_rfp_pdf(file=file, process_immediately=False, db=db)
            results.append({
                "filename": file.filename,
                "status": "success",
                "data": result["data"]
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })
    
    successful = len([r for r in results if r["status"] == "success"])
    failed = len([r for r in results if r["status"] == "failed"])
    
    return {
        "success": True,
        "message": f"Uploaded {successful} files successfully, {failed} failed",
        "data": {
            "total": len(files),
            "successful": successful,
            "failed": failed,
            "results": results
        }
    }


@router.post("/product-csv")
async def upload_product_csv(
    file: UploadFile = File(...),
    manufacturer: str = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload product CSV for bulk import.
    
    Args:
        file: CSV file
        manufacturer: Manufacturer name (if known)
        db: Database session
        
    Returns:
        Import status
    """
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are accepted"
        )
    
    logger.info("Receiving product CSV upload", filename=file.filename)
    
    try:
        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = file.filename.replace(" ", "_")
        file_path = PRODUCT_UPLOAD_DIR / f"{timestamp}_{safe_filename}"
        
        await save_upload_file(file, file_path)
        
        # Import products (use existing CSV loading logic)
        import pandas as pd
        df = pd.read_csv(file_path)
        
        added_count = 0
        skipped_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                # Create product from row
                product_id = f"{manufacturer[:3].upper() if manufacturer else 'UNK'}_{row.get('product_code', idx)}_{timestamp}"
                
                product = Product(
                    id=product_id,
                    manufacturer=manufacturer or row.get('manufacturer', 'Unknown'),
                    product_code=row.get('product_code', f'PROD_{idx}'),
                    product_name=row.get('product_name', ''),
                    category=row.get('category', 'General'),
                    # Add other fields...
                )
                
                db.add(product)
                added_count += 1
                
            except Exception as e:
                skipped_count += 1
                errors.append(f"Row {idx}: {str(e)}")
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"Imported {added_count} products",
            "data": {
                "filename": file.filename,
                "total_rows": len(df),
                "added": added_count,
                "skipped": skipped_count,
                "errors": errors[:10]  # First 10 errors only
            }
        }
        
    except Exception as e:
        logger.error("Error uploading product CSV", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload product CSV: {str(e)}"
        )


@router.get("/history")
async def get_upload_history(
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get upload history.
    
    Args:
        limit: Maximum number of records
        
    Returns:
        Upload history
    """
    rfp_files = sorted(RFP_UPLOAD_DIR.glob("*.pdf"), key=os.path.getmtime, reverse=True)[:limit]
    product_files = sorted(PRODUCT_UPLOAD_DIR.glob("*.csv"), key=os.path.getmtime, reverse=True)[:limit]
    
    history = []
    
    for file_path in rfp_files:
        stat = file_path.stat()
        history.append({
            "type": "rfp_pdf",
            "filename": file_path.name,
            "size_bytes": stat.st_size,
            "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "path": str(file_path)
        })
    
    for file_path in product_files:
        stat = file_path.stat()
        history.append({
            "type": "product_csv",
            "filename": file_path.name,
            "size_bytes": stat.st_size,
            "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "path": str(file_path)
        })
    
    # Sort by upload time
    history.sort(key=lambda x: x['uploaded_at'], reverse=True)
    
    return {
        "success": True,
        "data": {
            "history": history[:limit],
            "total_files": len(history)
        }
    }
