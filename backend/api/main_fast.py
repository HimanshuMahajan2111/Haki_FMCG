"""Fast-loading API without heavy authentication imports."""
import asyncio
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Path, status, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import structlog

from agents.communication import CommunicationManager
from workflows.rfp_workflow import (
    RFPWorkflowOrchestrator, 
    WorkflowStatus as WFStatus,
    WorkflowStage
)
from workflows.mock_agents import (
    MockRFPParserAgent, MockSalesAgent, MockTechnicalAgent,
    MockPricingAgent, MockResponseGeneratorAgent
)
from api.models import (
    RFPSubmission, WorkflowResponse, WorkflowStatus, WorkflowResult,
    TemplateInfo, TimeEstimatesResponse, TimeEstimate, ApprovalInfo,
    ApprovalAction, AnalyticsResponse, HealthResponse, ErrorResponse,
    ConfigUpdate, VisualizationResponse
)

# Import production services
from config.logging_config import setup_production_logging, get_api_logger, get_performance_logger
from services.monitoring_service import get_performance_monitor, monitor_async_performance
from services.cache_service import get_cache_service
from services.error_tracking import get_error_tracker, capture_exception
from db.optimization import create_performance_indexes
from db.database import get_db

logger = structlog.get_logger()

# Global state
comm_manager: Optional[CommunicationManager] = None
orchestrator: Optional[RFPWorkflowOrchestrator] = None
workflow_results: Dict[str, Any] = {}
background_tasks_storage: Dict[str, asyncio.Task] = {}

# Production services
api_logger = None
perf_logger = None
performance_monitor = None
cache_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    global comm_manager, orchestrator, api_logger, perf_logger, performance_monitor, cache_service
    
    logger.info("Starting RFP Workflow API (Production Mode)")
    
    # Setup production logging
    try:
        setup_production_logging(
            log_dir="logs",
            log_level="INFO",
            enable_json=True,
            enable_console=True,
            enable_file=True
        )
        api_logger = get_api_logger()
        perf_logger = get_performance_logger()
        api_logger.info("Production logging initialized")
    except Exception as e:
        logger.warning(f"Failed to setup production logging: {e}")
    
    # Initialize monitoring
    performance_monitor = get_performance_monitor()
    
    # Initialize caching
    cache_service = get_cache_service(max_size=1000, enable_redis=False)
    
    # Create database indexes for optimization
    try:
        # Database indexes will be created on first request
        logger.info("Database optimization ready")
    except Exception as e:
        logger.warning(f"Failed to setup database optimization: {e}")
    
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
    
    logger.info("All agents initialized successfully")
    
    # Initialize orchestrator
    orchestrator = RFPWorkflowOrchestrator(
        comm_manager,
        enable_approvals=True,
        enable_visualization=False
    )
    await orchestrator.initialize()
    
    # Record system startup metric
    if performance_monitor:
        performance_monitor.increment_counter("system_startup")
        performance_monitor.record_system_metrics()
    
    logger.info("RFP Workflow API ready - Production mode with analytics & monitoring")
    if api_logger:
        api_logger.info("System startup complete", extra={
            'version': '1.0.0',
            'environment': 'production',
            'caching_enabled': cache_service is not None,
            'monitoring_enabled': performance_monitor is not None
        })
    
    yield
    
    # Cleanup
    logger.info("Shutting down RFP Workflow API")
    if api_logger:
        api_logger.info("System shutdown initiated")
    
    for task_id, task in background_tasks_storage.items():
        if not task.done():
            task.cancel()
    
    comm_manager = None
    orchestrator = None


# Create FastAPI app
app = FastAPI(
    title="RFP Workflow Management API (Production)",
    description="RESTful API for managing end-to-end RFP processing workflows",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Performance monitoring middleware
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    """Monitor API request performance"""
    if performance_monitor:
        timer_id = performance_monitor.start_timer("api_request")
        performance_monitor.increment_counter("api_requests_total")
    
    try:
        response = await call_next(request)
        
        if performance_monitor:
            duration = performance_monitor.stop_timer(timer_id, "api_request_duration")
            performance_monitor.record_metric("api_response_time", duration)
            performance_monitor.increment_counter(f"api_status_{response.status_code}")
        
        # Add security headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response
    except Exception as e:
        if performance_monitor:
            performance_monitor.increment_counter("api_errors_total")
        
        # Track error
        error_tracker = get_error_tracker()
        error_id = error_tracker.capture_exception(
            e,
            context={'path': request.url.path, 'method': request.method},
            severity='error'
        )
        
        raise

# Include all routers
from api.analytics import router as analytics_router
from api.routes.rfp import router as rfp_router
from api.routes.products import router as products_router
from api.routes.agents import router as agents_router
from api.routes.challenge import router as challenge_router

app.include_router(analytics_router)
app.include_router(rfp_router, prefix="/api/rfp", tags=["RFP Legacy"])
app.include_router(products_router, prefix="/api/products", tags=["Products"])
app.include_router(agents_router, prefix="/api/agents", tags=["Agents"])
app.include_router(challenge_router)

# Check if React build exists, otherwise use static dashboard
import os
REACT_BUILD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend_build")
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

if os.path.exists(REACT_BUILD_DIR):
    # Serve React production build
    logger.info(f"Serving React app from {REACT_BUILD_DIR}")
    app.mount("/assets", StaticFiles(directory=os.path.join(REACT_BUILD_DIR, "assets")), name="assets")
    
    @app.get("/", response_class=HTMLResponse)
    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_react_app(full_path: str = ""):
        """Serve React SPA - fallback to index.html for client-side routing"""
        # Don't intercept API calls
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404)
        
        index_path = os.path.join(REACT_BUILD_DIR, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return f.read()
        raise HTTPException(status_code=404, detail="React app not found")
else:
    # Fallback to static dashboard
    logger.info(f"Serving static dashboard from {STATIC_DIR}")
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Serve the analytics dashboard"""
        with open(os.path.join(STATIC_DIR, "index.html"), "r") as f:
            return f.read()

# WebSocket endpoint for real-time updates
@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time system updates"""
    await websocket.accept()
    try:
        while True:
            # Send periodic updates (every 5 seconds)
            await asyncio.sleep(5)
            
            # Get real-time metrics
            try:
                from services.analytics_service import get_analytics_service
                analytics = get_analytics_service()
                realtime_data = await analytics.get_realtime_metrics()
                
                await websocket.send_json({
                    "type": "metrics_update",
                    "data": realtime_data,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error sending WebSocket update: {e}")
    except Exception as e:
        logger.info(f"WebSocket connection closed: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass


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


# RFP Submission Endpoints
@app.post("/api/v1/rfp/submit", response_model=WorkflowResponse, status_code=status.HTTP_202_ACCEPTED, tags=["RFP"])
async def submit_rfp(rfp: RFPSubmission, background_tasks: BackgroundTasks):
    """Submit a new RFP for processing."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    # Get template
    template = orchestrator.template_manager.get_template(rfp.template_id or "standard_rfp")
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {rfp.template_id}")
    
    # Create workflow configuration
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
    
    # Store the workflow ID that will be created by process_rfp
    workflow_id_holder = {"id": None}
    
    # Start workflow in background
    async def run_workflow():
        try:
            result = await orchestrator.process_rfp(workflow_config, template_id=template.template_id)
            # Extract the workflow_id from the result
            actual_workflow_id = result['workflow_info']['workflow_id']
            workflow_id_holder["id"] = actual_workflow_id
            workflow_results[actual_workflow_id] = result
            logger.info("Workflow completed", workflow_id=actual_workflow_id)
        except Exception as e:
            logger.error("Workflow execution error", error=str(e))
    
    # Start the task and wait a moment for workflow_id to be created
    task = asyncio.create_task(run_workflow())
    await asyncio.sleep(0.1)  # Give it a moment to start and create workflow_id
    
    # Get the workflow_id from active_workflows
    workflow_id = None
    for wf_id in orchestrator.active_workflows.keys():
        if orchestrator.active_workflows[wf_id].rfp_id == rfp.rfp_id:
            workflow_id = wf_id
            break
    
    if not workflow_id:
        # Fallback to temporary ID
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
    
    background_tasks_storage[workflow_id] = task
    
    logger.info("RFP submitted", workflow_id=workflow_id, rfp_id=rfp.rfp_id)
    
    return WorkflowResponse(
        workflow_id=workflow_id,
        rfp_id=rfp.rfp_id,
        customer_id=rfp.customer_id,
        status="submitted",
        template_id=template.template_id,
        template_name=template.name,
        estimated_duration=template.estimated_duration,
        message="RFP submitted successfully, processing in background"
    )


@app.get("/api/v1/rfp/status/{workflow_id}", response_model=WorkflowStatus, tags=["RFP"])
async def get_workflow_status(workflow_id: str = Path(..., description="Workflow ID")):
    """Get the status of a workflow."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    if workflow_id not in orchestrator.active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = orchestrator.active_workflows[workflow_id]
    
    # Calculate duration
    duration = None
    if workflow.end_time:
        duration = (workflow.end_time - workflow.start_time).total_seconds()
    elif workflow.status != WFStatus.PENDING:
        duration = (datetime.utcnow() - workflow.start_time).total_seconds()
    
    # Get template info from metadata
    template_id = workflow.metadata.get('template_id')
    template_name = workflow.metadata.get('template_name')
    estimated_duration = workflow.metadata.get('estimated_duration')
    
    return WorkflowStatus(
        workflow_id=workflow_id,
        rfp_id=workflow.rfp_id,
        customer_id=workflow.customer_id,
        status=workflow.status.value,
        current_stage=workflow.current_stage.value if isinstance(workflow.current_stage, WorkflowStage) else str(workflow.current_stage),
        template_id=template_id,
        template_name=template_name,
        stages_completed=[stage.value for stage in workflow.stage_results.keys()] if workflow.stage_results else [],
        start_time=workflow.start_time.isoformat() if workflow.start_time else datetime.utcnow().isoformat(),
        end_time=workflow.end_time.isoformat() if workflow.end_time else None,
        duration_seconds=duration,
        estimated_duration=estimated_duration,
        errors=list(workflow.errors)
    )


@app.get("/api/v1/rfp/result/{workflow_id}", response_model=WorkflowResult, tags=["RFP"])
async def get_workflow_result(workflow_id: str = Path(..., description="Workflow ID")):
    """Get the results of a completed workflow."""
    if workflow_id not in workflow_results:
        raise HTTPException(status_code=404, detail="Workflow results not found")
    
    result = workflow_results[workflow_id]
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=f"Workflow failed: {result['error']}")
    
    return WorkflowResult(
        workflow_info=result.get("workflow_info", {}),
        quote=result.get("quote", {}),
        compliance=result.get("compliance", {}),
        timeline=result.get("timeline", {}),
        response_document=result.get("response_document"),
        executive_summary=result.get("executive_summary"),
        metadata=result.get("metadata")
    )


@app.get("/api/v1/rfp/workflows", response_model=List[WorkflowStatus], tags=["RFP"])
async def list_workflows(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of workflows to return")
):
    """List all workflows with optional filtering."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    workflows = orchestrator.get_all_active_workflows()
    
    result = []
    for wf_id in list(workflows.keys())[:limit]:
        workflow = workflows[wf_id]
        if status_filter and workflow.status.value != status_filter:
            continue
        
        result.append(WorkflowStatus(
            workflow_id=wf_id,
            rfp_id=workflow.config.get("rfp_id", ""),
            customer_id=workflow.config.get("customer_id", ""),
            status=workflow.status.value,
            current_stage=workflow.current_stage or "not_started",
            template_id=workflow.template.template_id if workflow.template else None,
            template_name=workflow.template.name if workflow.template else None,
            stages_completed=list(workflow.completed_stages),
            start_time=workflow.start_time,
            end_time=workflow.end_time,
            duration_seconds=workflow.get_duration(),
            errors=list(workflow.errors)
        ))
    
    return result


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """API root endpoint with basic information."""
    return {
        "name": "RFP Workflow Management API",
        "version": "1.0.0",
        "status": "operational",
        "mode": "fast",
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "note": "For full features with auth/webhooks, use api.main:app_full"
    }
