"""Pydantic models for API requests and responses."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class RFPSubmission(BaseModel):
    """Request model for submitting a new RFP."""
    rfp_id: str = Field(..., description="Unique RFP identifier")
    customer_id: str = Field(..., description="Customer identifier")
    document: str = Field(..., description="RFP document content or path")
    deadline: Optional[str] = Field(None, description="Response deadline (ISO format)")
    priority: str = Field("normal", description="Priority: normal, high, urgent")
    complexity: Optional[str] = Field(None, description="Complexity: simple, standard, complex")
    estimated_value: Optional[float] = Field(None, description="Estimated contract value")
    is_standard_product: Optional[bool] = Field(False, description="Whether product is standard")
    template_id: Optional[str] = Field(None, description="Workflow template to use")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        schema_extra = {
            "example": {
                "rfp_id": "RFP2024001",
                "customer_id": "CUST12345",
                "document": "Request for 500m cable supply with specifications...",
                "deadline": "2024-12-31T23:59:59",
                "priority": "high",
                "complexity": "standard",
                "estimated_value": 150000,
                "is_standard_product": False,
                "template_id": "standard_rfp"
            }
        }


class WorkflowResponse(BaseModel):
    """Response model for workflow submission."""
    workflow_id: str = Field(..., description="Unique workflow identifier")
    rfp_id: str
    customer_id: str
    status: str
    template_id: str
    template_name: str
    estimated_duration: float
    message: str

    class Config:
        schema_extra = {
            "example": {
                "workflow_id": "wf_123abc",
                "rfp_id": "RFP2024001",
                "customer_id": "CUST12345",
                "status": "in_progress",
                "template_id": "standard_rfp",
                "template_name": "Standard RFP Processing",
                "estimated_duration": 7.0,
                "message": "Workflow started successfully"
            }
        }


class WorkflowStatus(BaseModel):
    """Response model for workflow status."""
    workflow_id: str
    rfp_id: str
    customer_id: str
    status: str
    current_stage: str
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    stages_completed: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    estimated_duration: Optional[float] = None
    errors: List[str] = Field(default_factory=list)


class WorkflowResult(BaseModel):
    """Response model for completed workflow results."""
    workflow_info: Dict[str, Any]
    quote: Dict[str, Any]
    compliance: Dict[str, Any]
    timeline: Dict[str, Any]
    response_document: Optional[Dict[str, Any]] = None
    executive_summary: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TemplateInfo(BaseModel):
    """Response model for workflow template information."""
    template_id: str
    name: str
    description: str
    stages: List[str]
    estimated_duration: float


class TimeEstimate(BaseModel):
    """Response model for time estimates."""
    stage_name: str
    estimated_time: float
    confidence: float
    sample_count: int


class TimeEstimatesResponse(BaseModel):
    """Response model for all time estimates."""
    stage_estimates: Dict[str, TimeEstimate]
    total_workflow: Dict[str, Any]


class ApprovalInfo(BaseModel):
    """Response model for approval information."""
    approval_id: str
    workflow_id: str
    stage_name: str
    status: str
    requested_at: datetime
    required_roles: List[str]
    context_data: Dict[str, Any]
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


class ApprovalAction(BaseModel):
    """Request model for approval action."""
    approver: str = Field(..., description="Name/ID of approver")
    reason: Optional[str] = Field(None, description="Reason for rejection (if rejecting)")

    class Config:
        schema_extra = {
            "example": {
                "approver": "john_doe",
                "reason": "Pricing needs revision"
            }
        }


class AnalyticsResponse(BaseModel):
    """Response model for workflow analytics."""
    total_workflows: int
    active_workflows: int
    completed_workflows: int
    failed_workflows: int
    average_duration: float
    success_rate: float
    workflows_by_template: Dict[str, int]
    stage_performance: Dict[str, Dict[str, float]]


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: datetime
    version: str
    active_workflows: int
    communication_system: str
    features: Dict[str, bool]


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    detail: Optional[str] = None
    workflow_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "error": "Workflow not found",
                "detail": "No workflow with ID wf_123abc exists",
                "workflow_id": "wf_123abc",
                "timestamp": "2024-12-16T10:30:00"
            }
        }


class ConfigUpdate(BaseModel):
    """Request model for configuration updates."""
    enable_approvals: Optional[bool] = Field(None, description="Enable/disable approval workflows")
    enable_visualization: Optional[bool] = Field(None, description="Enable/disable visualization")
    default_template: Optional[str] = Field(None, description="Default template ID")

    class Config:
        schema_extra = {
            "example": {
                "enable_approvals": True,
                "enable_visualization": False,
                "default_template": "standard_rfp"
            }
        }


class VisualizationResponse(BaseModel):
    """Response model for workflow visualization."""
    workflow_id: str
    format: str  # 'ascii' or 'mermaid'
    visualization: str


class ProductSearchQuery(BaseModel):
    """Request model for product search."""
    query: str = Field(..., description="Search query text")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Search filters")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "1100V XLPE cable",
                "filters": {"voltage": "1100V", "manufacturer": "Havells"},
                "limit": 20,
                "offset": 0
            }
        }


class Product(BaseModel):
    """Product model."""
    product_id: str
    name: str
    description: str
    manufacturer: str
    category: str
    specifications: Dict[str, Any]
    price: Optional[float] = None
    in_stock: bool = True
    relevance_score: Optional[float] = None


class ProductSearchResponse(BaseModel):
    """Response model for product search."""
    query: str
    total_results: int
    results: List[Product]
    filters_applied: Dict[str, Any]
    offset: int
    limit: int


class BatchRFPSubmission(BaseModel):
    """Request model for batch RFP submission."""
    rfps: List[RFPSubmission] = Field(..., description="List of RFPs to submit")
    process_in_parallel: bool = Field(False, description="Whether to process RFPs in parallel")
    
    class Config:
        schema_extra = {
            "example": {
                "rfps": [
                    {
                        "rfp_id": "RFP2024001",
                        "customer_id": "CUST001",
                        "document": "Cable supply request 1"
                    },
                    {
                        "rfp_id": "RFP2024002",
                        "customer_id": "CUST002",
                        "document": "Cable supply request 2"
                    }
                ],
                "process_in_parallel": True
            }
        }


class BatchRFPResponse(BaseModel):
    """Response model for batch RFP submission."""
    batch_id: str
    total_rfps: int
    submitted_workflows: List[WorkflowResponse]
    failed_submissions: List[Dict[str, Any]] = Field(default_factory=list)
    message: str


class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    file_id: str
    filename: str
    size: int
    content_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    url: Optional[str] = None


class WebhookSubscription(BaseModel):
    """Request model for webhook subscription."""
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to subscribe to")
    secret: Optional[str] = Field(None, description="Secret for signature verification")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com/webhook",
                "events": ["workflow.completed", "quote.generated"],
                "secret": "your-webhook-secret"
            }
        }
