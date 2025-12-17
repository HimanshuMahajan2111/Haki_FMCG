"""Enhanced database models with proper relationships."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Float, Integer, DateTime, JSON, Boolean, Enum, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base
import enum

# Use separate Base to avoid conflicts with basic models
Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class RFPStatus(enum.Enum):
    """RFP processing status."""
    DISCOVERED = "discovered"
    PROCESSING = "processing"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    REJECTED = "rejected"


class AgentType(enum.Enum):
    """Agent types."""
    TECHNICAL = "technical"
    PRICING = "pricing"
    COMPLIANCE = "compliance"
    ORCHESTRATOR = "orchestrator"


class MatchStatus(enum.Enum):
    """Product match status."""
    CANDIDATE = "candidate"
    RECOMMENDED = "recommended"
    SELECTED = "selected"
    REJECTED = "rejected"


class InteractionStatus(enum.Enum):
    """Agent interaction status."""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


# ============================================================================
# CORE ENTITIES
# ============================================================================

class RFP(Base):
    """RFP document model with enhanced tracking."""
    __tablename__ = "rfps"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(200), index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    status: Mapped[RFPStatus] = mapped_column(Enum(RFPStatus), default=RFPStatus.DISCOVERED, index=True)
    
    # Extracted content
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    structured_data: Mapped[Optional[dict]] = mapped_column(JSON)
    requirements: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Response generation
    response_document_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Metrics
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    total_estimated_cost: Mapped[Optional[float]] = mapped_column(Float)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    product_matches: Mapped[List["ProductMatch"]] = relationship("ProductMatch", back_populates="rfp", cascade="all, delete-orphan")
    agent_interactions: Mapped[List["AgentInteraction"]] = relationship("AgentInteraction", back_populates="rfp", cascade="all, delete-orphan")
    requirement_items: Mapped[List["RequirementItem"]] = relationship("RequirementItem", back_populates="rfp", cascade="all, delete-orphan")


class Product(Base):
    """Product catalog model with enhanced specifications."""
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    brand: Mapped[str] = mapped_column(String(100), index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    sub_category: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Product details (product_code is unique but nullable - empty codes converted to NULL)
    product_code: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    product_name: Mapped[str] = mapped_column(String(500), index=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Technical specifications
    specifications: Mapped[dict] = mapped_column(JSON)
    
    # Current pricing
    mrp: Mapped[Optional[float]] = mapped_column(Float, index=True)
    selling_price: Mapped[Optional[float]] = mapped_column(Float, index=True)
    dealer_price: Mapped[Optional[float]] = mapped_column(Float, index=True)
    
    # Compliance
    certifications: Mapped[Optional[str]] = mapped_column(String(500))
    bis_registration: Mapped[Optional[str]] = mapped_column(String(200))
    standard: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    hsn_code: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    
    # Additional info
    warranty_years: Mapped[Optional[int]] = mapped_column(Integer)
    country_of_origin: Mapped[Optional[str]] = mapped_column(String(100))
    image_url: Mapped[Optional[str]] = mapped_column(String(1000))
    datasheet_url: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # Vector embedding ID for semantic search
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Inventory
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    stock_available: Mapped[Optional[int]] = mapped_column(Integer)
    lead_time_days: Mapped[Optional[int]] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product_matches: Mapped[List["ProductMatch"]] = relationship("ProductMatch", back_populates="product")
    pricing_history: Mapped[List["PricingHistory"]] = relationship("PricingHistory", back_populates="product", cascade="all, delete-orphan")
    standard_compliances: Mapped[List["StandardCompliance"]] = relationship("StandardCompliance", back_populates="product", cascade="all, delete-orphan")
    test_results: Mapped[List["TestResult"]] = relationship("TestResult", back_populates="product", cascade="all, delete-orphan")


# ============================================================================
# RFP REQUIREMENT TRACKING
# ============================================================================

class RequirementItem(Base):
    """Individual requirement items extracted from RFP."""
    __tablename__ = "requirement_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rfp_id: Mapped[int] = mapped_column(Integer, ForeignKey("rfps.id", ondelete="CASCADE"), index=True)
    
    # Requirement details
    item_number: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    quantity: Mapped[Optional[int]] = mapped_column(Integer)
    unit: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Technical specifications
    required_specifications: Mapped[Optional[dict]] = mapped_column(JSON)
    required_standards: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    # Budget constraints
    budget_min: Mapped[Optional[float]] = mapped_column(Float)
    budget_max: Mapped[Optional[float]] = mapped_column(Float)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rfp: Mapped["RFP"] = relationship("RFP", back_populates="requirement_items")


# ============================================================================
# PRODUCT MATCHING
# ============================================================================

class ProductMatch(Base):
    """Product matches for RFP requirements with detailed scoring."""
    __tablename__ = "product_matches"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rfp_id: Mapped[int] = mapped_column(Integer, ForeignKey("rfps.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), index=True)
    
    # Match quality
    match_status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus), default=MatchStatus.CANDIDATE, index=True)
    similarity_score: Mapped[float] = mapped_column(Float, index=True)
    technical_score: Mapped[Optional[float]] = mapped_column(Float)
    compliance_score: Mapped[Optional[float]] = mapped_column(Float)
    pricing_score: Mapped[Optional[float]] = mapped_column(Float)
    overall_score: Mapped[float] = mapped_column(Float, index=True)
    
    # Match details
    matched_specifications: Mapped[Optional[dict]] = mapped_column(JSON)
    missing_specifications: Mapped[Optional[dict]] = mapped_column(JSON)
    compliance_details: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Pricing for this match
    quoted_quantity: Mapped[Optional[int]] = mapped_column(Integer)
    unit_price: Mapped[Optional[float]] = mapped_column(Float)
    total_price: Mapped[Optional[float]] = mapped_column(Float)
    discount_percentage: Mapped[Optional[float]] = mapped_column(Float)
    
    # Metadata
    match_reason: Mapped[Optional[str]] = mapped_column(Text)
    agent_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Ranking
    rank_in_rfp: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rfp: Mapped["RFP"] = relationship("RFP", back_populates="product_matches")
    product: Mapped["Product"] = relationship("Product", back_populates="product_matches")
    
    __table_args__ = (
        Index('ix_match_rfp_score', 'rfp_id', 'overall_score'),
        Index('ix_match_product_score', 'product_id', 'overall_score'),
    )


# ============================================================================
# AGENT INTERACTIONS
# ============================================================================

class AgentInteraction(Base):
    """Detailed agent interaction tracking for workflow analysis."""
    __tablename__ = "agent_interactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rfp_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("rfps.id", ondelete="CASCADE"), index=True)
    parent_interaction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("agent_interactions.id"), index=True)
    
    # Agent details
    agent_type: Mapped[AgentType] = mapped_column(Enum(AgentType), index=True)
    agent_name: Mapped[str] = mapped_column(String(100))
    agent_version: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Execution tracking
    status: Mapped[InteractionStatus] = mapped_column(Enum(InteractionStatus), default=InteractionStatus.STARTED, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    
    # Input/Output
    input_data: Mapped[Optional[dict]] = mapped_column(JSON)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_traceback: Mapped[Optional[str]] = mapped_column(Text)
    
    # LLM Metrics
    model_name: Mapped[Optional[str]] = mapped_column(String(100))
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float)
    
    # Performance metrics
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rfp: Mapped[Optional["RFP"]] = relationship("RFP", back_populates="agent_interactions")
    parent_interaction: Mapped[Optional["AgentInteraction"]] = relationship("AgentInteraction", remote_side=[id], back_populates="child_interactions")
    child_interactions: Mapped[List["AgentInteraction"]] = relationship("AgentInteraction", back_populates="parent_interaction")
    
    __table_args__ = (
        Index('ix_agent_rfp_started', 'rfp_id', 'started_at'),
        Index('ix_agent_type_status', 'agent_type', 'status'),
    )


# ============================================================================
# PRICING HISTORY
# ============================================================================

class PricingHistory(Base):
    """Track pricing changes over time for products."""
    __tablename__ = "pricing_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), index=True)
    
    # Pricing snapshot
    mrp: Mapped[Optional[float]] = mapped_column(Float)
    selling_price: Mapped[Optional[float]] = mapped_column(Float)
    dealer_price: Mapped[Optional[float]] = mapped_column(Float)
    
    # Change tracking
    change_reason: Mapped[Optional[str]] = mapped_column(String(200))
    changed_by: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Validity period
    effective_from: Mapped[datetime] = mapped_column(DateTime, index=True)
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="pricing_history")
    
    __table_args__ = (
        Index('ix_pricing_product_current', 'product_id', 'is_current'),
        Index('ix_pricing_effective', 'effective_from', 'effective_to'),
    )


# ============================================================================
# STANDARDS & COMPLIANCE
# ============================================================================

class Standard(Base):
    """Standards reference data."""
    __tablename__ = "standards"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    standard_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    standard_type: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    
    # Issuing authority
    issuing_body: Mapped[str] = mapped_column(String(200))
    geographical_scope: Mapped[str] = mapped_column(String(100))
    
    # Requirements
    mandatory_in_region: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    certification_required: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Equivalencies
    equivalent_standards: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    # Version tracking
    version: Mapped[Optional[str]] = mapped_column(String(50))
    published_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    revision_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    compliances: Mapped[List["StandardCompliance"]] = relationship("StandardCompliance", back_populates="standard")


class StandardCompliance(Base):
    """Product compliance with specific standards."""
    __tablename__ = "standard_compliances"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), index=True)
    standard_id: Mapped[int] = mapped_column(Integer, ForeignKey("standards.id", ondelete="CASCADE"), index=True)
    
    # Compliance details
    is_compliant: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    certification_number: Mapped[Optional[str]] = mapped_column(String(200))
    certification_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    
    # Testing
    test_report_number: Mapped[Optional[str]] = mapped_column(String(200))
    testing_laboratory: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Additional details
    compliance_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="standard_compliances")
    standard: Mapped["Standard"] = relationship("Standard", back_populates="compliances")
    
    __table_args__ = (
        Index('ix_compliance_product_standard', 'product_id', 'standard_id', unique=True),
    )


# ============================================================================
# TESTING & QUALITY
# ============================================================================

class TestResult(Base):
    """Product testing results and quality data."""
    __tablename__ = "test_results"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), index=True)
    
    # Test details
    test_type: Mapped[str] = mapped_column(String(100), index=True)  # routine, type, special, certification
    test_name: Mapped[str] = mapped_column(String(200))
    test_standard: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Testing information
    test_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    testing_laboratory: Mapped[str] = mapped_column(String(200))
    lab_accreditation: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Results
    test_passed: Mapped[bool] = mapped_column(Boolean, index=True)
    test_results: Mapped[dict] = mapped_column(JSON)  # Detailed test parameters and results
    report_number: Mapped[Optional[str]] = mapped_column(String(200))
    report_url: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # Validity
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="test_results")
    
    __table_args__ = (
        Index('ix_test_product_type', 'product_id', 'test_type'),
    )


# ============================================================================
# SYSTEM MONITORING
# ============================================================================

class SystemMetric(Base):
    """System performance and health metrics."""
    __tablename__ = "system_metrics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Metric details
    metric_type: Mapped[str] = mapped_column(String(100), index=True)  # api_latency, db_query, vector_search, etc.
    metric_name: Mapped[str] = mapped_column(String(200))
    
    # Values
    metric_value: Mapped[float] = mapped_column(Float)
    metric_unit: Mapped[str] = mapped_column(String(50))
    
    # Context
    component: Mapped[str] = mapped_column(String(100), index=True)
    endpoint: Mapped[Optional[str]] = mapped_column(String(200))
    metric_metadata: Mapped[Optional[dict]] = mapped_column(JSON)  # Renamed from 'metadata' (reserved)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('ix_metrics_component_type', 'component', 'metric_type', 'timestamp'),
    )
