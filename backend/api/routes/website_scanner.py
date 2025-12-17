"""
API Routes for Website Scanning and RFP Discovery

Provides endpoints for scanning procurement websites and managing discovered RFPs.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from agents.website_scanner import WebsiteScanner, scan_and_process_rfps

router = APIRouter()
scanner = WebsiteScanner()


class RFPResponse(BaseModel):
    """RFP response model."""
    rfp_id: str
    title: str
    buyer: str
    category: str
    description: str
    estimated_value: float
    quantity: str
    publish_date: str
    submission_deadline: str
    location: str
    website: str
    bid_type: str
    specifications: dict


class ScanResultResponse(BaseModel):
    """Scan result response model."""
    timestamp: str
    rfps_found: int
    rfps: List[RFPResponse]
    category_filter: Optional[str] = None


class ScanStatisticsResponse(BaseModel):
    """Scan statistics response model."""
    total_scans: int
    total_rfps_found: int
    avg_rfps_per_scan: float
    last_scan: Optional[str]
    last_scan_rfps: int


@router.get("/scan", response_model=ScanResultResponse)
async def scan_all_websites(
    category: Optional[str] = Query(None, description="Filter by category (e.g., 'Power Cables', 'Solar')"),
):
    """
    Scan all procurement websites for RFPs.
    
    - **category**: Optional filter by category
    """
    try:
        rfps = await scanner.scan_all_websites(category=category)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "rfps_found": len(rfps),
            "rfps": rfps,
            "category_filter": category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/scan/{website_name}", response_model=ScanResultResponse)
async def scan_single_website(
    website_name: str,
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """
    Scan a specific procurement website.
    
    - **website_name**: Name of website (eProcure, GEM, TCS iON, L&T eProcure)
    - **category**: Optional filter by category
    """
    valid_websites = ["eProcure", "GEM", "TCS iON", "L&T eProcure"]
    if website_name not in valid_websites:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid website name. Valid options: {', '.join(valid_websites)}"
        )
    
    try:
        rfps = await scanner.scan_single_website(website_name, category=category)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "rfps_found": len(rfps),
            "rfps": rfps,
            "category_filter": category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/rfp/{rfp_id}", response_model=RFPResponse)
async def get_rfp_by_id(rfp_id: str):
    """
    Get a specific RFP by ID.
    
    - **rfp_id**: RFP identifier (e.g., "EPRO-2025-001")
    """
    rfp = scanner.get_rfp_by_id(rfp_id)
    if not rfp:
        raise HTTPException(status_code=404, detail=f"RFP {rfp_id} not found")
    
    return rfp


@router.get("/rfps/new", response_model=ScanResultResponse)
async def get_new_rfps(
    since_days: int = Query(7, description="Get RFPs from last N days", ge=1, le=90),
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """
    Get new RFPs published in the last N days.
    
    - **since_days**: Number of days to look back (1-90)
    - **category**: Optional filter by category
    """
    since_date = datetime.now()
    from datetime import timedelta
    since_date = since_date - timedelta(days=since_days)
    
    try:
        rfps = await scanner.get_new_rfps(since_date=since_date)
        
        # Apply category filter if provided
        if category:
            rfps = [rfp for rfp in rfps if category.lower() in rfp['category'].lower()]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "rfps_found": len(rfps),
            "rfps": rfps,
            "category_filter": category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get new RFPs: {str(e)}")


@router.get("/statistics", response_model=ScanStatisticsResponse)
async def get_scan_statistics():
    """Get scanning statistics."""
    try:
        stats = scanner.get_scan_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/websites")
async def list_websites():
    """List all available procurement websites."""
    websites = []
    for website in scanner.websites:
        websites.append({
            "name": website.name,
            "base_url": website.base_url,
            "rfp_count": len(website.rfps)
        })
    
    return {
        "total_websites": len(websites),
        "websites": websites
    }


@router.post("/process-rfps")
async def process_scanned_rfps(
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """
    Scan websites and prepare RFPs for agent processing.
    
    This endpoint scans all websites and returns RFPs in a format
    ready for the multi-agent system to process.
    
    - **category**: Optional filter by category
    """
    try:
        processed_rfps = await scan_and_process_rfps(scanner, category=category)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "rfps_ready_for_processing": len(processed_rfps),
            "rfps": processed_rfps,
            "message": "RFPs are ready to be submitted to the multi-agent system"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process RFPs: {str(e)}")
