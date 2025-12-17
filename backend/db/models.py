"""Database models."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Float, Integer, DateTime, JSON, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from db.database import Base


class RFPStatus(enum.Enum):
    """RFP processing status."""
    DISCOVERED = "discovered"
    PROCESSING = "processing"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class AgentType(enum.Enum):
    """Agent types."""
    TECHNICAL = "technical"
    PRICING = "pricing"
    COMPLIANCE = "compliance"


class RFP(Base):
    """RFP document model."""
    __tablename__ = "rfps"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(200))
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[RFPStatus] = mapped_column(Enum(RFPStatus), default=RFPStatus.DISCOVERED)
    
    # Extracted content
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    structured_data: Mapped[Optional[dict]] = mapped_column(JSON)
    requirements: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Processing results
    matched_products: Mapped[Optional[dict]] = mapped_column(JSON)
    pricing_data: Mapped[Optional[dict]] = mapped_column(JSON)
    response_document_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Metrics
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Product(Base):
    """Product catalog model."""
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    brand: Mapped[str] = mapped_column(String(100), index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    sub_category: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Product details
    product_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    product_name: Mapped[str] = mapped_column(String(500))
    model_name: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Technical specifications
    specifications: Mapped[dict] = mapped_column(JSON)
    
    # Pricing
    mrp: Mapped[Optional[float]] = mapped_column(Float)
    selling_price: Mapped[Optional[float]] = mapped_column(Float)
    dealer_price: Mapped[Optional[float]] = mapped_column(Float)
    
    # Compliance
    certifications: Mapped[Optional[str]] = mapped_column(String(500))
    bis_registration: Mapped[Optional[str]] = mapped_column(String(200))
    standard: Mapped[Optional[str]] = mapped_column(String(100))
    hsn_code: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Additional info
    warranty_years: Mapped[Optional[int]] = mapped_column(Integer)
    country_of_origin: Mapped[Optional[str]] = mapped_column(String(100))
    image_url: Mapped[Optional[str]] = mapped_column(String(1000))
    datasheet_url: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # Vector embedding ID for semantic search
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkflowRun(Base):
    """Workflow execution tracking."""
    __tablename__ = "workflow_runs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    rfp_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    customer_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Execution status
    status: Mapped[str] = mapped_column(String(50), index=True, default="pending")  # pending, in_progress, completed, failed
    current_stage: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    
    # Results
    stage_results: Mapped[Optional[dict]] = mapped_column(JSON)  # Stage-wise results
    final_output: Mapped[Optional[dict]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metrics
    total_cost_usd: Mapped[Optional[float]] = mapped_column(Float)
    quote_value_usd: Mapped[Optional[float]] = mapped_column(Float)
    match_score: Mapped[Optional[float]] = mapped_column(Float)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    
    # Outcome
    won: Mapped[Optional[bool]] = mapped_column(Boolean)  # Whether deal was won
    feedback: Mapped[Optional[str]] = mapped_column(Text)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentLog(Base):
    """Agent execution logs."""
    __tablename__ = "agent_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    rfp_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    agent_type: Mapped[Optional[AgentType]] = mapped_column(Enum(AgentType))
    agent_name: Mapped[str] = mapped_column(String(100), index=True)
    
    # Execution details
    started_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    
    # Results
    status: Mapped[str] = mapped_column(String(50), index=True)
    action: Mapped[Optional[str]] = mapped_column(String(200), index=True)
    input_data: Mapped[Optional[dict]] = mapped_column(JSON)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metrics
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Standard(Base):
    """Standards reference data."""
    __tablename__ = "standards"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    standard_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    standard_type: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    issuing_body: Mapped[str] = mapped_column(String(200))
    geographical_scope: Mapped[str] = mapped_column(String(100))
    mandatory_in_region: Mapped[bool] = mapped_column(Boolean, default=False)
    certification_required: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
