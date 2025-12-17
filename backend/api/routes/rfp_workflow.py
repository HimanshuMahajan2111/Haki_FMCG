"""
RFP Processing Workflow API Routes
Handles progress tracking, product matching, response generation, and exports
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import structlog
from datetime import datetime
import io
import csv

from db.database import get_db
from db.models import RFP, Product, RFPStatus
from rfp_parsing.rfp_pipeline import RFPPipeline
from matching.spec_matcher import SpecificationMatcher
from services.pdf_generator import PDFResponseGenerator
from services.progress_tracker import ProgressTracker

logger = structlog.get_logger()
router = APIRouter()

# In-memory progress tracking (in production, use Redis or database)
processing_progress = {}


@router.get("/progress/{rfp_id}")
async def get_processing_progress(rfp_id: int):
    """Get real-time processing progress for an RFP."""
    progress = processing_progress.get(rfp_id, {
        "status": "not_started",
        "progress": 0,
        "current_stage": "Initializing",
        "agents_status": {},
        "estimated_time_remaining": None
    })
    return progress


@router.post("/match-products/{rfp_id}")
async def match_products(
    rfp_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Match top 3 OEM products based on RFP specifications."""
    try:
        # Get RFP
        query = select(RFP).where(RFP.id == rfp_id)
        result = await db.execute(query)
        rfp = result.scalar_one_or_none()
        
        if not rfp:
            raise HTTPException(status_code=404, detail="RFP not found")
        
        # Get extracted specifications - parse JSON if string
        import json
        structured = rfp.structured_data
        if isinstance(structured, str):
            try:
                structured = json.loads(structured)
            except:
                structured = {}
        
        if structured and isinstance(structured, dict):
            extracted = structured.get("extracted_data", {})
            specifications = extracted.get("specifications", [])
            standards = extracted.get("standards", [])
            certifications = extracted.get("certifications", [])
        else:
            raise HTTPException(status_code=400, detail="RFP not yet processed. Please extract data first.")
        
        # Initialize spec matcher
        matcher = SpecificationMatcher()
        
        # Get all products
        products_query = select(Product).limit(100)  # Get top 100 products
        products_result = await db.execute(products_query)
        all_products = products_result.scalars().all()
        
        # Match products
        matched_products = []
        for product in all_products:
            score = matcher.calculate_match_score(
                specifications,
                product.specifications,
                standards,
                getattr(product, 'certifications', '').split(',') if hasattr(product, 'certifications') else []
            )
            
            if score > 0.3:  # Minimum 30% match
                matched_products.append({
                    "product_id": product.id,
                    "product_code": product.product_code,
                    "product_name": product.product_name,
                    "brand": product.brand,
                    "category": product.category,
                    "match_score": round(score * 100, 2),
                    "specifications": product.specifications,
                    "mrp": product.mrp,
                    "selling_price": product.selling_price,
                    "certifications": getattr(product, 'certifications', ''),
                    "standard": getattr(product, 'standard', ''),
                    "image_url": product.image_url
                })
        
        # Sort by match score and get top 3
        matched_products.sort(key=lambda x: x["match_score"], reverse=True)
        top_3_matches = matched_products[:3]
        
        # Store matches in RFP
        rfp.matched_products = {"top_matches": top_3_matches, "all_matches": matched_products[:10]}
        await db.commit()
        
        return {
            "rfp_id": rfp_id,
            "top_matches": top_3_matches,
            "total_matches": len(matched_products),
            "match_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Product matching failed", rfp_id=rfp_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")


@router.get("/spec-comparison/{rfp_id}")
async def get_spec_comparison_table(
    rfp_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Generate specification comparison table for matched products."""
    try:
        query = select(RFP).where(RFP.id == rfp_id)
        result = await db.execute(query)
        rfp = result.scalar_one_or_none()
        
        if not rfp:
            raise HTTPException(status_code=404, detail="RFP not found")
        
        if not rfp.matched_products:
            raise HTTPException(status_code=400, detail="No matched products found. Run matching first.")
        
        # Get RFP requirements - parse JSON if string
        import json
        structured = rfp.structured_data
        if isinstance(structured, str):
            try:
                structured = json.loads(structured)
            except:
                structured = {}
        structured = structured or {}
        
        extracted = structured.get("extracted_data", {})
        rfp_specs = {spec["parameter"]: spec for spec in extracted.get("specifications", [])}
        
        # Get matched products - parse JSON if string
        matched = rfp.matched_products
        if isinstance(matched, str):
            try:
                matched = json.loads(matched)
            except:
                matched = {}
        matched = matched or {}
        
        top_matches = matched.get("top_matches", [])
        
        # Build comparison table
        comparison_table = []
        all_parameters = set(rfp_specs.keys())
        
        # Add product spec parameters
        for match in top_matches:
            if match.get("specifications"):
                all_parameters.update(match["specifications"].keys())
        
        # Build rows
        for param in sorted(all_parameters):
            row = {
                "parameter": param,
                "rfp_requirement": rfp_specs.get(param, {}).get("value", "N/A"),
                "rfp_unit": rfp_specs.get(param, {}).get("unit", ""),
                "required": rfp_specs.get(param, {}).get("requirement_type") == "mandatory",
                "products": []
            }
            
            for match in top_matches:
                product_value = match.get("specifications", {}).get(param, "N/A")
                row["products"].append({
                    "product_name": match["product_name"],
                    "value": product_value,
                    "matches": str(product_value).lower() == str(row["rfp_requirement"]).lower()
                })
            
            comparison_table.append(row)
        
        return {
            "rfp_id": rfp_id,
            "comparison_table": comparison_table,
            "matched_products": top_matches
        }
        
    except Exception as e:
        logger.error("Spec comparison failed", rfp_id=rfp_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-response/{rfp_id}")
async def generate_response_document(
    rfp_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Generate PDF response document for RFP."""
    try:
        query = select(RFP).where(RFP.id == rfp_id)
        result = await db.execute(query)
        rfp = result.scalar_one_or_none()
        
        if not rfp:
            raise HTTPException(status_code=404, detail="RFP not found")
        
        if not rfp.matched_products:
            raise HTTPException(status_code=400, detail="No matched products. Run matching first.")
        
        # Generate PDF in background
        output_dir = Path("outputs/rfp_responses")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"RFP_{rfp_id}_Response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Get all data for response - parse JSON if string
        import json
        structured = rfp.structured_data
        if isinstance(structured, str):
            try:
                structured = json.loads(structured)
            except:
                structured = {}
        structured = structured or {}
        extracted = structured.get("extracted_data", {})
        
        matched = rfp.matched_products
        if isinstance(matched, str):
            try:
                matched = json.loads(matched)
            except:
                matched = {}
        matched = matched or {}
        top_matches = matched.get("top_matches", [])
        
        # Generate PDF
        generator = PDFResponseGenerator()
        pdf_path = generator.generate_response(
            rfp_data={
                "id": rfp.id,
                "title": rfp.title,
                "source": rfp.source,
                "due_date": rfp.due_date.isoformat() if rfp.due_date else None,
                "boq_summary": extracted.get("boq_summary", {}),
                "specifications": extracted.get("specifications", []),
                "standards": extracted.get("standards", []),
                "certifications": extracted.get("certifications", [])
            },
            matched_products=top_matches,
            output_path=str(output_path)
        )
        
        # Update RFP with response path
        rfp.response_document_path = str(pdf_path)
        await db.commit()
        
        return {
            "rfp_id": rfp_id,
            "response_generated": True,
            "file_path": str(pdf_path),
            "download_url": f"/api/rfp-workflow/download-response/{rfp_id}",
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Response generation failed", rfp_id=rfp_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-response/{rfp_id}")
async def download_response_document(
    rfp_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Download generated RFP response PDF."""
    query = select(RFP).where(RFP.id == rfp_id)
    result = await db.execute(query)
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    if not rfp.response_document_path or not Path(rfp.response_document_path).exists():
        raise HTTPException(status_code=404, detail="Response document not found")
    
    return FileResponse(
        path=rfp.response_document_path,
        media_type="application/pdf",
        filename=f"RFP_{rfp_id}_Response.pdf"
    )


@router.get("/export-details/{rfp_id}")
async def export_rfp_details_csv(
    rfp_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Export RFP details and matched products as CSV."""
    query = select(RFP).where(RFP.id == rfp_id)
    result = await db.execute(query)
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write RFP details
    writer.writerow(["RFP Details"])
    writer.writerow(["ID", "Title", "Source", "Status", "Due Date", "Confidence Score"])
    writer.writerow([
        rfp.id,
        rfp.title,
        rfp.source,
        rfp.status.value if rfp.status else "",
        rfp.due_date.isoformat() if rfp.due_date else "",
        rfp.confidence_score or ""
    ])
    writer.writerow([])
    
    # Write extracted data summary - parse JSON if string
    import json
    if rfp.structured_data:
        structured = rfp.structured_data
        if isinstance(structured, str):
            try:
                structured = json.loads(structured)
            except:
                structured = {}
        structured = structured or {}
        extracted = structured.get("extracted_data", {})
        boq = extracted.get("boq_summary", {})
        
        writer.writerow(["BOQ Summary"])
        writer.writerow(["Total Items", "Total Quantity", "Total Amount"])
        writer.writerow([
            boq.get("total_items", ""),
            boq.get("total_quantity", ""),
            boq.get("total_amount", "")
        ])
        writer.writerow([])
        
        # Write specifications
        specs = extracted.get("specifications", [])
        if specs:
            writer.writerow(["Technical Specifications"])
            writer.writerow(["Parameter", "Value", "Unit", "Requirement Type", "Category"])
            for spec in specs:
                writer.writerow([
                    spec.get("parameter", ""),
                    spec.get("value", ""),
                    spec.get("unit", ""),
                    spec.get("requirement_type", ""),
                    spec.get("category", "")
                ])
            writer.writerow([])
    
    # Write matched products - parse JSON if string
    if rfp.matched_products:
        matched = rfp.matched_products
        if isinstance(matched, str):
            try:
                matched = json.loads(matched)
            except:
                matched = {}
        matched = matched or {}
        top_matches = matched.get("top_matches", [])
        if top_matches:
            writer.writerow(["Matched Products"])
            writer.writerow(["Rank", "Product Code", "Product Name", "Brand", "Match Score %", "MRP", "Selling Price"])
            for idx, match in enumerate(top_matches, 1):
                writer.writerow([
                    idx,
                    match.get("product_code", ""),
                    match.get("product_name", ""),
                    match.get("brand", ""),
                    match.get("match_score", ""),
                    match.get("mrp", ""),
                    match.get("selling_price", "")
                ])
    
    # Return CSV as download
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=RFP_{rfp_id}_Details.csv"}
    )


@router.get("/export-all-rfps")
async def export_all_rfps_csv(db: AsyncSession = Depends(get_db)):
    """Export all RFPs summary as CSV."""
    query = select(RFP).order_by(RFP.created_at.desc()).limit(100)
    result = await db.execute(query)
    rfps = result.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "ID", "Title", "Source", "Status", "Created At", "Due Date",
        "Confidence Score", "Processing Time (s)", "Has Matched Products",
        "Has Response Document", "File Path"
    ])
    
    for rfp in rfps:
        writer.writerow([
            rfp.id,
            rfp.title,
            rfp.source,
            rfp.status.value if rfp.status else "",
            rfp.created_at.isoformat() if rfp.created_at else "",
            rfp.due_date.isoformat() if rfp.due_date else "",
            rfp.confidence_score or "",
            rfp.processing_time_seconds or "",
            "Yes" if rfp.matched_products else "No",
            "Yes" if rfp.response_document_path else "No",
            rfp.file_path or ""
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=All_RFPs_Summary.csv"}
    )


@router.post("/send-response/{rfp_id}")
async def send_response(
    rfp_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Mark RFP response as sent (placeholder for actual submission logic)."""
    query = select(RFP).where(RFP.id == rfp_id)
    result = await db.execute(query)
    rfp = result.scalar_one_or_none()
    
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    if not rfp.response_document_path:
        raise HTTPException(status_code=400, detail="No response document generated")
    
    # Update status to submitted
    rfp.status = RFPStatus.SUBMITTED
    await db.commit()
    
    logger.info("RFP response sent", rfp_id=rfp_id)
    
    return {
        "rfp_id": rfp_id,
        "status": "submitted",
        "message": "Response marked as sent successfully",
        "sent_at": datetime.utcnow().isoformat()
    }

@router.post("/cancel/{rfp_id}")
async def cancel_processing(
    rfp_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Cancel RFP processing."""
    from services.progress_tracker import ProgressTracker
    
    # Clear progress tracking
    ProgressTracker.clear_progress(rfp_id)
    
    # Update RFP status
    query = select(RFP).where(RFP.id == rfp_id)
    result = await db.execute(query)
    rfp = result.scalar_one_or_none()
    
    if rfp:
        rfp.status = RFPStatus.CANCELLED
        await db.commit()
    
    logger.info("RFP processing cancelled", rfp_id=rfp_id)
    
    return {
        "message": "Processing cancelled successfully",
        "rfp_id": rfp_id,
        "status": "cancelled"
    }
