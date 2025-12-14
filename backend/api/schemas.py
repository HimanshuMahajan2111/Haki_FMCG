"""Pydantic schemas for API requests and responses."""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# RFP Schemas
class RFPScanRequest(BaseModel):
    """Request to scan RFP directory."""
    force_rescan: bool = False


class RFPProcessRequest(BaseModel):
    """Request to process an RFP."""
    rfp_id: int
    rfp_data: Dict[str, Any]


class RFPResponse(BaseModel):
    """RFP response model."""
    id: int
    title: str
    source: Optional[str]
    status: str
    due_date: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Product Schemas
class ProductSearchRequest(BaseModel):
    """Product search request."""
    query: str = Field(..., min_length=1)
    limit: int = Field(10, ge=1, le=50)


class ProductResponse(BaseModel):
    """Product response model."""
    id: int
    brand: str
    category: str
    product_code: str
    product_name: str
    specifications: Dict[str, Any]
    
    class Config:
        from_attributes = True


# Agent Schemas
class AgentExecutionRequest(BaseModel):
    """Agent execution request."""
    rfp_id: int
    input_data: Dict[str, Any]


class AgentExecutionResponse(BaseModel):
    """Agent execution response."""
    agent_name: str
    agent_type: str
    status: str
    duration_seconds: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
