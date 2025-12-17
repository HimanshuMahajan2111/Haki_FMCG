"""FastAPI application for RFP Workflow Management System."""
import asyncio
import uuid
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Path, status, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
import structlog

from agents.communication import CommunicationManager
from workflows.rfp_workflow import RFPWorkflowOrchestrator, WorkflowStatus as WFStatus
from workflows.mock_agents import (
    MockRFPParserAgent, MockSalesAgent, MockTechnicalAgent,
    MockPricingAgent, MockResponseGeneratorAgent
)
from api.models import (
    RFPSubmission, WorkflowResponse, WorkflowStatus, WorkflowResult,
    TemplateInfo, TimeEstimatesResponse, TimeEstimate, ApprovalInfo,
    ApprovalAction, AnalyticsResponse, HealthResponse, ErrorResponse,
    ConfigUpdate, VisualizationResponse, ProductSearchQuery, ProductSearchResponse,
    Product, BatchRFPSubmission, BatchRFPResponse, FileUploadResponse,
    WebhookSubscription
)
# Import auth models even if we don't use the full auth system (needed for type hints)
try:
    from api.auth import (
        Token, LoginRequest, UserCreate, get_current_user, RoleChecker, UserRole, User,
        authenticate_user, create_access_token, create_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES
    )
    # Create role checkers
    require_manager = RoleChecker([UserRole.ADMIN, UserRole.MANAGER])
except ImportError:
    # Create dummy classes if auth module isn't available
    Token = Dict[str, Any]
    LoginRequest = Dict[str, Any]
    UserCreate = Dict[str, Any]
    User = Dict[str, Any]
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    def get_current_user(): pass
    def authenticate_user(*args, **kwargs): return None
    def create_access_token(*args, **kwargs): return ""
    def create_refresh_token(*args, **kwargs): return ""
    def RoleChecker(*args): pass
    def require_manager(): pass
    class UserRole:
        ADMIN = "admin"

# Import webhook models
try:
    from api.webhooks import WebhookManager, Webhook, WebhookEvent
except ImportError:
    WebhookManager = None
    Webhook = Dict[str, Any]
    class WebhookEvent:
        RFP_SUBMITTED = "rfp.submitted"
        
# Lazy imports for faster startup
# These will be imported when needed
# from api.rate_limit import RateLimitMiddleware

logger = structlog.get_logger()

# Global state
comm_manager: Optional[CommunicationManager] = None
orchestrator: Optional[RFPWorkflowOrchestrator] = None
workflow_results: Dict[str, Any] = {}  # Store completed workflow results
background_tasks_storage: Dict[str, asyncio.Task] = {}  # Track background tasks
uploaded_files: Dict[str, Dict[str, Any]] = {}  # Store uploaded file metadata
active_streams: Dict[str, bool] = {}  # Track active SSE streams

# Lazy-loaded managers (imported when needed)
_webhook_manager = None
_auth_module = None
_rate_limit_module = None

def get_webhook_manager():
    """Get or create webhook manager."""
    global _webhook_manager
    if _webhook_manager is None and WebhookManager is not None:
        _webhook_manager = WebhookManager()
    return _webhook_manager

# Create a global reference that endpoints can use
webhook_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    global comm_manager, orchestrator, _webhook_manager
    
    logger.info("Starting RFP Workflow API (fast mode)")
    
    # Initialize communication system
    comm_manager = CommunicationManager()
    
    # Initialize mock agents
    parser = MockRFPParserAgent(comm_manager)
    sales = MockSalesAgent(comm_manager)
    technical = MockTechnicalAgent(comm_manager)
    pricing = MockPricingAgent(comm_manager)
    response_gen = MockResponseGeneratorAgent(comm_manager)
    
    await parser.initialize()
    await sales.initialize()
    await technical.initialize()
    await pricing.initialize()
    await response_gen.initialize()
    
    # Initialize orchestrator
    orchestrator = RFPWorkflowOrchestrator(
        comm_manager,
        enable_approvals=True,
        enable_visualization=False  # Disable for API
    )
    await orchestrator.initialize()
    
    logger.info("RFP Workflow API ready (webhook/auth available on-demand)")
    
    yield
    
    # Cleanup
    logger.info("Shutting down RFP Workflow API")
    # Cancel background tasks
    for task_id, task in background_tasks_storage.items():
        if not task.done():
            task.cancel()
    
    # Close webhook manager if initialized
    if _webhook_manager:
        await _webhook_manager.close()
    
    comm_manager = None
    orchestrator = None
    _webhook_manager = None


# Create FastAPI app
app = FastAPI(
    title="RFP Workflow Management API",
    description="RESTful API for managing end-to-end RFP processing workflows with authentication, webhooks, and batch processing",
    version="1.0.0",
    lifespan=lifespan
)

# Rate limiting can be enabled by uncommenting below (slows startup)
# from api.rate_limit import RateLimitMiddleware
# app.add_middleware(RateLimitMiddleware, calls=100, period=60, identifier="ip")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=str(exc),
            timestamp=datetime.utcnow()
        ).model_dump(mode='json')
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error("Unexpected error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            timestamp=datetime.utcnow()
        ).model_dump(mode='json')
    )


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check API health and system status."""
    if not orchestrator or not comm_manager:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    active = len(orchestrator.get_all_active_workflows())
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        active_workflows=active,
        communication_system="operational",
        features={
            "approvals": orchestrator.approval_manager is not None,
            "visualization": orchestrator.enable_visualization,
            "time_estimation": True,
            "templates": True,
            "conditional_branching": True
        }
    )


# Authentication Endpoints
@app.post("/api/v1/auth/login", response_model=Token, tags=["Authentication"])
async def login(login_data: LoginRequest):
    """Authenticate user and return JWT tokens."""
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "roles": [r.value for r in user.roles]},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username}
    )
    
    logger.info("User logged in", username=user.username)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles
        )
    )


@app.post("/api/v1/auth/register", response_model=Token, tags=["Authentication"])
async def register(register_data: RegisterRequest, _user: User = Depends(require_admin)):
    """Register a new user (admin only)."""
    if register_data.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(register_data.password)
    new_user = UserInDB(
        username=register_data.username,
        email=register_data.email,
        full_name=register_data.full_name,
        hashed_password=hashed_password,
        roles=register_data.roles,
        disabled=False
    )
    
    fake_users_db[register_data.username] = new_user.model_dump()
    
    # Generate tokens for new user
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.username, "roles": [r.value for r in new_user.roles]},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": new_user.username}
    )
    
    logger.info("New user registered", username=new_user.username)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=User(
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            roles=new_user.roles
        )
    )


@app.get("/api/v1/auth/me", response_model=User, tags=["Authentication"])
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


# RFP Submission Endpoints
@app.post("/api/v1/rfp/submit", response_model=WorkflowResponse, status_code=status.HTTP_202_ACCEPTED, tags=["RFP"])
async def submit_rfp(
    rfp: RFPSubmission,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_sales)
):
    """Submit a new RFP for processing.
    
    The workflow will be processed asynchronously. Use the returned workflow_id
    to check status and retrieve results.
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    logger.info("RFP submission received", rfp_id=rfp.rfp_id)
    
    # Prepare RFP data
    rfp_data = rfp.model_dump()
    
    # Start workflow in background
    async def process_workflow():
        try:
            result = await orchestrator.process_rfp(rfp_data, template_id=rfp.template_id)
            # Store result for later retrieval
            workflow_id = result['workflow_info']['workflow_id']
            workflow_results[workflow_id] = result
            logger.info("Workflow completed", workflow_id=workflow_id)
        except Exception as e:
            logger.error("Workflow failed", error=str(e))
    
    # Create background task
    task = asyncio.create_task(process_workflow())
    
    # Get template info for response
    template_id = rfp.template_id or orchestrator.template_manager.select_template(rfp_data)
    template = orchestrator.template_manager.get_template(template_id)
    
    # Generate temporary workflow ID (will be replaced when workflow actually starts)
    import uuid
    temp_workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
    background_tasks_storage[temp_workflow_id] = task
    
    return WorkflowResponse(
        workflow_id=temp_workflow_id,
        rfp_id=rfp.rfp_id,
        customer_id=rfp.customer_id,
        status="submitted",
        template_id=template_id,
        template_name=template.name,
        estimated_duration=template.estimated_duration,
        message="RFP submitted successfully, processing in background"
    )


@app.get("/api/v1/rfp/status/{workflow_id}", response_model=WorkflowStatus, tags=["RFP"])
async def get_workflow_status(
    workflow_id: str = Path(..., description="Workflow ID to check")
):
    """Get current status of a workflow."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    status_data = orchestrator.get_workflow_status(workflow_id)
    
    if not status_data:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    # Convert datetime objects to ISO strings
    if 'start_time' in status_data and status_data['start_time']:
        if isinstance(status_data['start_time'], datetime):
            status_data['start_time'] = status_data['start_time'].isoformat()
    if 'end_time' in status_data and status_data['end_time']:
        if isinstance(status_data['end_time'], datetime):
            status_data['end_time'] = status_data['end_time'].isoformat()
    
    return WorkflowStatus(**status_data)


@app.get("/api/v1/rfp/result/{workflow_id}", response_model=WorkflowResult, tags=["RFP"])
async def get_workflow_result(
    workflow_id: str = Path(..., description="Workflow ID to retrieve results for")
):
    """Get results of a completed workflow."""
    if workflow_id not in workflow_results:
        # Check if workflow is still active
        if orchestrator:
            status_data = orchestrator.get_workflow_status(workflow_id)
            if status_data:
                if status_data['status'] != 'completed':
                    raise HTTPException(
                        status_code=202,
                        detail=f"Workflow still in progress (status: {status_data['status']})"
                    )
        
        raise HTTPException(status_code=404, detail=f"Results for workflow {workflow_id} not found")
    
    return WorkflowResult(**workflow_results[workflow_id])


@app.get("/api/v1/rfp/workflows", response_model=List[WorkflowStatus], tags=["RFP"])
async def list_workflows(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of workflows to return")
):
    """List all workflows with optional filtering."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    workflows = orchestrator.get_all_active_workflows()
    
    # Apply status filter
    if status_filter:
        workflows = [w for w in workflows if w['status'] == status_filter]
    
    # Apply limit
    workflows = workflows[:limit]
    
    return [WorkflowStatus(**w) for w in workflows]


# Template Management Endpoints
@app.get("/api/v1/templates", response_model=List[TemplateInfo], tags=["Templates"])
async def list_templates():
    """Get all available workflow templates."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    templates = orchestrator.get_available_templates()
    return [TemplateInfo(**t) for t in templates]


@app.get("/api/v1/templates/{template_id}", response_model=TemplateInfo, tags=["Templates"])
async def get_template(template_id: str = Path(..., description="Template ID")):
    """Get details of a specific template."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    template = orchestrator.template_manager.get_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    
    return TemplateInfo(
        template_id=template.template_id,
        name=template.name,
        description=template.description,
        stages=[s.stage_name for s in template.stages],
        estimated_duration=template.estimated_duration
    )


# Analytics Endpoints
@app.get("/api/v1/analytics/estimates", response_model=TimeEstimatesResponse, tags=["Analytics"])
async def get_time_estimates():
    """Get time estimates for workflow stages based on historical data."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    estimates = orchestrator.get_time_estimates()
    
    # Convert to response model
    stage_estimates = {}
    for stage, data in estimates.items():
        if stage != 'total_workflow':
            stage_estimates[stage] = TimeEstimate(
                stage_name=stage,
                estimated_time=data['estimated_time'],
                confidence=data['confidence'],
                sample_count=data['sample_count']
            )
    
    return TimeEstimatesResponse(
        stage_estimates=stage_estimates,
        total_workflow=estimates['total_workflow']
    )


@app.get("/api/v1/analytics/summary", response_model=AnalyticsResponse, tags=["Analytics"])
async def get_analytics_summary():
    """Get overall analytics and performance metrics."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    workflows = orchestrator.get_all_active_workflows()
    
    # Calculate metrics
    total = len(workflows) + len(workflow_results)
    active = len([w for w in workflows if w['status'] == 'in_progress'])
    completed = len(workflow_results)
    failed = len([w for w in workflows if w['status'] == 'failed'])
    
    # Average duration from completed workflows
    durations = [r['timeline']['total_duration_seconds'] for r in workflow_results.values()
                if 'timeline' in r and 'total_duration_seconds' in r['timeline']]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    # Success rate
    success_rate = (completed / (completed + failed) * 100) if (completed + failed) > 0 else 100
    
    # Workflows by template
    by_template = {}
    for result in workflow_results.values():
        template_id = result.get('workflow_info', {}).get('template_id', 'unknown')
        by_template[template_id] = by_template.get(template_id, 0) + 1
    
    # Stage performance
    estimates = orchestrator.get_time_estimates()
    stage_performance = {}
    for stage, data in estimates.items():
        if stage != 'total_workflow':
            stage_performance[stage] = {
                'avg_time': data['estimated_time'],
                'confidence': data['confidence'],
                'samples': data['sample_count']
            }
    
    return AnalyticsResponse(
        total_workflows=total,
        active_workflows=active,
        completed_workflows=completed,
        failed_workflows=failed,
        average_duration=avg_duration,
        success_rate=success_rate,
        workflows_by_template=by_template,
        stage_performance=stage_performance
    )


# Approval Management Endpoints
@app.get("/api/v1/approvals/pending", response_model=List[ApprovalInfo], tags=["Approvals"])
async def get_pending_approvals(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID")
):
    """Get all pending approval requests."""
    if not orchestrator or not orchestrator.approval_manager:
        raise HTTPException(status_code=503, detail="Approval system not enabled")
    
    approvals = orchestrator.approval_manager.get_pending_approvals(workflow_id)
    
    return [
        ApprovalInfo(
            approval_id=a.approval_id,
            workflow_id=a.workflow_id,
            stage_name=a.stage_name,
            status=a.status,
            requested_at=a.requested_at,
            required_roles=a.required_roles,
            context_data=a.context_data,
            approved_by=a.approved_by,
            approved_at=a.approved_at,
            rejection_reason=a.rejection_reason
        )
        for a in approvals
    ]


@app.post("/api/v1/approvals/{approval_id}/approve", tags=["Approvals"])
async def approve_request(
    approval_id: str = Path(..., description="Approval request ID"),
    action: ApprovalAction = None
):
    """Approve a pending approval request."""
    if not orchestrator or not orchestrator.approval_manager:
        raise HTTPException(status_code=503, detail="Approval system not enabled")
    
    success = orchestrator.approval_manager.approve(approval_id, action.approver)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")
    
    return {"message": "Approval granted", "approval_id": approval_id, "approver": action.approver}


@app.post("/api/v1/approvals/{approval_id}/reject", tags=["Approvals"])
async def reject_request(
    approval_id: str = Path(..., description="Approval request ID"),
    action: ApprovalAction = None
):
    """Reject a pending approval request."""
    if not orchestrator or not orchestrator.approval_manager:
        raise HTTPException(status_code=503, detail="Approval system not enabled")
    
    if not action.reason:
        raise HTTPException(status_code=400, detail="Reason required for rejection")
    
    success = orchestrator.approval_manager.reject(approval_id, action.approver, action.reason)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")
    
    return {
        "message": "Approval rejected",
        "approval_id": approval_id,
        "approver": action.approver,
        "reason": action.reason
    }


# Visualization Endpoints
@app.get("/api/v1/visualization/{workflow_id}", response_model=VisualizationResponse, tags=["Visualization"])
async def get_workflow_visualization(
    workflow_id: str = Path(..., description="Workflow ID"),
    format: str = Query("ascii", description="Format: 'ascii' or 'mermaid'")
):
    """Get visual representation of workflow progress."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    if format not in ["ascii", "mermaid"]:
        raise HTTPException(status_code=400, detail="Format must be 'ascii' or 'mermaid'")
    
    if format == "ascii":
        viz = orchestrator.visualize_workflow(workflow_id)
    else:
        viz = orchestrator.generate_mermaid_diagram(workflow_id)
    
    if "not found" in viz.lower():
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    return VisualizationResponse(
        workflow_id=workflow_id,
        format=format,
        visualization=viz
    )


# Configuration Endpoints
@app.get("/api/v1/config", tags=["Configuration"])
async def get_configuration():
    """Get current system configuration."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    return {
        "enable_approvals": orchestrator.approval_manager is not None,
        "enable_visualization": orchestrator.enable_visualization,
        "available_templates": len(orchestrator.template_manager.list_templates()),
        "active_workflows": len(orchestrator.get_all_active_workflows())
    }


@app.post("/api/v1/config/update", tags=["Configuration"])
async def update_configuration(config: ConfigUpdate):
    """Update system configuration.
    
    Note: Some changes may require system restart to take full effect.
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    changes = []
    
    if config.enable_visualization is not None:
        orchestrator.enable_visualization = config.enable_visualization
        changes.append(f"visualization={'enabled' if config.enable_visualization else 'disabled'}")
    
    return {
        "message": "Configuration updated",
        "changes": changes,
        "note": "Some changes may require restart"
    }


# Product Search Endpoints
@app.post("/api/v1/products/search", response_model=ProductSearchResponse, tags=["Products"])
async def search_products(
    search_query: ProductSearchQuery,
    current_user: User = Depends(get_current_active_user)
):
    """Search for products in catalog."""
    # Mock product data - replace with real database query
    mock_products = [
        Product(
            product_id="PROD001",
            name="XLPE Insulated Power Cable 1100V",
            description="High voltage XLPE insulated power cable",
            manufacturer="Havells",
            category="Power Cables",
            specifications={"voltage": "1100V", "conductor": "Copper", "insulation": "XLPE"},
            price=125.50,
            in_stock=True,
            relevance_score=0.95
        ),
        Product(
            product_id="PROD002",
            name="PVC Insulated Control Cable 1100V",
            description="Multi-core control cable with PVC insulation",
            manufacturer="Polycab",
            category="Control Cables",
            specifications={"voltage": "1100V", "cores": 4, "insulation": "PVC"},
            price=89.75,
            in_stock=True,
            relevance_score=0.82
        )
    ]
    
    # Filter products based on query
    results = [p for p in mock_products if search_query.query.lower() in p.name.lower()]
    
    # Apply additional filters
    for key, value in search_query.filters.items():
        results = [p for p in results if p.specifications.get(key) == value]
    
    # Pagination
    total = len(results)
    results = results[search_query.offset:search_query.offset + search_query.limit]
    
    logger.info(
        "Product search",
        query=search_query.query,
        total_results=total,
        returned=len(results),
        user=current_user.username
    )
    
    return ProductSearchResponse(
        query=search_query.query,
        total_results=total,
        results=results,
        filters_applied=search_query.filters,
        offset=search_query.offset,
        limit=search_query.limit
    )


# Batch Processing Endpoints
@app.post("/api/v1/rfp/batch", response_model=BatchRFPResponse, tags=["RFP"])
async def submit_batch_rfp(
    batch: BatchRFPSubmission,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_manager)
):
    """Submit multiple RFPs in batch."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    batch_id = f"batch_{uuid.uuid4().hex[:12]}"
    submitted_workflows = []
    failed_submissions = []
    
    for rfp in batch.rfps:
        try:
            workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
            
            # Get template
            template = orchestrator.template_manager.get_template(rfp.template_id or "standard_rfp")
            if not template:
                raise ValueError(f"Template not found: {rfp.template_id}")
            
            # Create workflow config
            workflow_config = {
                "rfp_id": rfp.rfp_id,
                "customer_id": rfp.customer_id,
                "document": rfp.document,
                "priority": rfp.priority,
                "estimated_value": rfp.estimated_value or 100000,
                "deadline": rfp.deadline,
                "is_standard_product": rfp.is_standard_product,
                "metadata": rfp.metadata
            }
            
            # Start workflow in background
            if batch.process_in_parallel:
                background_tasks.add_task(
                    orchestrator.execute_workflow,
                    workflow_id,
                    template,
                    workflow_config
                )
            else:
                # Sequential processing - await directly
                await orchestrator.execute_workflow(workflow_id, template, workflow_config)
            
            submitted_workflows.append(
                WorkflowResponse(
                    workflow_id=workflow_id,
                    rfp_id=rfp.rfp_id,
                    customer_id=rfp.customer_id,
                    status="submitted" if batch.process_in_parallel else "in_progress",
                    template_id=template.template_id,
                    template_name=template.name,
                    estimated_duration=template.estimated_duration,
                    message="RFP submitted successfully"
                )
            )
        
        except Exception as e:
            logger.error("Batch submission error", rfp_id=rfp.rfp_id, error=str(e))
            failed_submissions.append({
                "rfp_id": rfp.rfp_id,
                "error": str(e)
            })
    
    logger.info(
        "Batch RFP submission",
        batch_id=batch_id,
        total=len(batch.rfps),
        submitted=len(submitted_workflows),
        failed=len(failed_submissions),
        user=current_user.username
    )
    
    return BatchRFPResponse(
        batch_id=batch_id,
        total_rfps=len(batch.rfps),
        submitted_workflows=submitted_workflows,
        failed_submissions=failed_submissions,
        message=f"Batch processed: {len(submitted_workflows)} submitted, {len(failed_submissions)} failed"
    )


# File Upload Endpoints
@app.post("/api/v1/files/upload", response_model=FileUploadResponse, tags=["Files"])
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a file (RFP document, specifications, etc.)."""
    # Generate file ID
    file_id = f"file_{uuid.uuid4().hex[:12]}"
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # In production, save to cloud storage (S3, Azure Blob, etc.)
    # For now, store metadata only
    file_metadata = {
        "file_id": file_id,
        "filename": file.filename,
        "size": file_size,
        "content_type": file.content_type,
        "uploaded_by": current_user.username,
        "uploaded_at": datetime.utcnow(),
        "content": content  # In production, this would be a storage URL
    }
    
    uploaded_files[file_id] = file_metadata
    
    logger.info(
        "File uploaded",
        file_id=file_id,
        filename=file.filename,
        size=file_size,
        user=current_user.username
    )
    
    return FileUploadResponse(
        file_id=file_id,
        filename=file.filename,
        size=file_size,
        content_type=file.content_type,
        uploaded_at=file_metadata["uploaded_at"],
        url=f"/api/v1/files/{file_id}"
    )


@app.get("/api/v1/files/{file_id}", tags=["Files"])
async def get_file(
    file_id: str = Path(..., description="File ID"),
    current_user: User = Depends(get_current_active_user)
):
    """Download an uploaded file."""
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_data = uploaded_files[file_id]
    
    return StreamingResponse(
        iter([file_data["content"]]),
        media_type=file_data["content_type"],
        headers={"Content-Disposition": f'attachment; filename="{file_data["filename"]}"'}
    )


# Server-Sent Events (SSE) for Real-time Status Updates
@app.get("/api/v1/rfp/stream/{workflow_id}", tags=["RFP"])
async def stream_workflow_status(
    workflow_id: str = Path(..., description="Workflow ID"),
    current_user: User = Depends(get_current_active_user)
):
    """Stream real-time workflow status updates via Server-Sent Events."""
    async def event_generator():
        """Generate SSE events for workflow updates."""
        active_streams[workflow_id] = True
        last_stage = None
        
        try:
            while active_streams.get(workflow_id, False):
                # Get current workflow status
                if workflow_id in orchestrator.workflows:
                    workflow = orchestrator.workflows[workflow_id]
                    current_stage = workflow.current_stage
                    
                    # Send update if stage changed
                    if current_stage != last_stage:
                        status_data = {
                            "workflow_id": workflow_id,
                            "status": workflow.status.value,
                            "current_stage": current_stage,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        yield f"data: {status_data}\n\n"
                        last_stage = current_stage
                    
                    # Check if workflow is complete
                    if workflow.status in [WFStatus.COMPLETED, WFStatus.FAILED]:
                        yield f"data: {{'status': 'complete', 'final_status': '{workflow.status.value}'}}\n\n"
                        break
                
                await asyncio.sleep(1)  # Poll every second
        
        finally:
            active_streams[workflow_id] = False
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


# Webhook Management Endpoints
@app.post("/api/v1/webhooks", tags=["Webhooks"])
async def register_webhook(
    webhook_data: WebhookSubscription,
    current_user: User = Depends(require_manager)
):
    """Register a new webhook subscription."""
    if not webhook_manager:
        raise HTTPException(status_code=503, detail="Webhook manager not initialized")
    
    # Convert event strings to WebhookEvent enum
    try:
        events = [WebhookEvent(e) for e in webhook_data.events]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {e}")
    
    webhook = Webhook(
        url=webhook_data.url,
        events=events,
        secret=webhook_data.secret,
        metadata=webhook_data.metadata
    )
    
    registered = webhook_manager.register_webhook(webhook)
    
    logger.info(
        "Webhook registered",
        webhook_id=registered.webhook_id,
        url=str(registered.url),
        user=current_user.username
    )
    
    return registered


@app.get("/api/v1/webhooks", tags=["Webhooks"])
async def list_webhooks(
    active_only: bool = Query(True, description="Only return active webhooks"),
    current_user: User = Depends(require_manager)
):
    """List all webhook subscriptions."""
    if not webhook_manager:
        raise HTTPException(status_code=503, detail="Webhook manager not initialized")
    
    webhooks = webhook_manager.list_webhooks(active_only=active_only)
    return {"webhooks": webhooks, "total": len(webhooks)}


@app.get("/api/v1/webhooks/{webhook_id}", tags=["Webhooks"])
async def get_webhook(
    webhook_id: str = Path(..., description="Webhook ID"),
    current_user: User = Depends(require_manager)
):
    """Get webhook details."""
    if not webhook_manager:
        raise HTTPException(status_code=503, detail="Webhook manager not initialized")
    
    webhook = webhook_manager.get_webhook(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return webhook


@app.delete("/api/v1/webhooks/{webhook_id}", tags=["Webhooks"])
async def delete_webhook(
    webhook_id: str = Path(..., description="Webhook ID"),
    current_user: User = Depends(require_manager)
):
    """Delete a webhook subscription."""
    if not webhook_manager:
        raise HTTPException(status_code=503, detail="Webhook manager not initialized")
    
    success = webhook_manager.unregister_webhook(webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    logger.info("Webhook deleted", webhook_id=webhook_id, user=current_user.username)
    
    return {"message": "Webhook deleted successfully", "webhook_id": webhook_id}


@app.get("/api/v1/webhooks/{webhook_id}/deliveries", tags=["Webhooks"])
async def list_webhook_deliveries(
    webhook_id: str = Path(..., description="Webhook ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of deliveries to return"),
    current_user: User = Depends(require_manager)
):
    """List webhook delivery attempts."""
    if not webhook_manager:
        raise HTTPException(status_code=503, detail="Webhook manager not initialized")
    
    deliveries = webhook_manager.list_deliveries(webhook_id=webhook_id, limit=limit)
    return {"webhook_id": webhook_id, "deliveries": deliveries, "total": len(deliveries)}


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """API root endpoint with basic information."""
    return {
        "name": "RFP Workflow Management API",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "authentication",
            "authorization",
            "rate_limiting",
            "webhooks",
            "batch_processing",
            "file_upload",
            "streaming",
            "product_search"
        ],
        "documentation": "/docs",
        "openapi": "/openapi.json"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
