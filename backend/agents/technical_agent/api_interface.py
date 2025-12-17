"""
API Interface and Webhook Support for Technical Agent.
"""
from typing import Dict, Any, List, Optional, Callable
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog
import asyncio
import aiohttp
from datetime import datetime
import uuid

logger = structlog.get_logger()


# Pydantic models for API
class RFPRequest(BaseModel):
    """RFP processing request."""
    rfp_id: Optional[str] = Field(None, description="RFP identifier")
    title: str = Field(..., description="RFP title")
    description: str = Field(..., description="RFP description")
    organization: Optional[str] = Field(None, description="Organization name")
    estimated_value: Optional[float] = Field(None, description="Estimated value")
    technical_requirements: List[str] = Field(default_factory=list, description="Technical requirements")
    callback_url: Optional[str] = Field(None, description="Webhook callback URL")
    
    class Config:
        schema_extra = {
            "example": {
                "rfp_id": "RFP-2024-001",
                "title": "Supply of Electrical Cables",
                "description": "Tender for electrical cables and wires",
                "organization": "Indian Railways",
                "estimated_value": 5000000.0,
                "technical_requirements": [
                    "PVC insulated 4-core cable, 2.5 sq.mm, 1.1kV"
                ],
                "callback_url": "https://example.com/webhook"
            }
        }


class ProcessingResponse(BaseModel):
    """RFP processing response."""
    request_id: str
    status: str
    message: str
    estimated_completion_time: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class WebhookPayload(BaseModel):
    """Webhook callback payload."""
    request_id: str
    rfp_id: str
    status: str
    result: Dict[str, Any]
    completed_at: str
    processing_time_seconds: float


class TechnicalAgentAPI:
    """FastAPI interface for Technical Agent."""
    
    def __init__(self, technical_agent):
        """Initialize API.
        
        Args:
            technical_agent: TechnicalAgent instance
        """
        self.logger = logger.bind(component="TechnicalAgentAPI")
        self.agent = technical_agent
        self.app = FastAPI(
            title="Technical Agent API",
            description="API for RFP analysis and product matching",
            version="1.0.0"
        )
        
        # Request tracking
        self.active_requests = {}
        
        # Setup routes
        self._setup_routes()
        
        self.logger.info("API initialized")
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "service": "Technical Agent API",
                "version": "1.0.0",
                "status": "running"
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "active_requests": len(self.active_requests),
                "agent_statistics": self.agent.get_statistics()
            }
        
        @self.app.post("/api/v1/process", response_model=ProcessingResponse)
        async def process_rfp(request: RFPRequest, background_tasks: BackgroundTasks):
            """Process RFP (synchronous)."""
            request_id = str(uuid.uuid4())
            
            try:
                self.logger.info("Processing RFP", request_id=request_id, rfp_id=request.rfp_id)
                
                # Convert to dict
                rfp_data = request.dict()
                if not rfp_data.get('rfp_id'):
                    rfp_data['rfp_id'] = request_id
                
                # Process
                result = self.agent.process_rfp(rfp_data)
                
                # Send webhook if provided
                if request.callback_url:
                    background_tasks.add_task(
                        self._send_webhook,
                        request.callback_url,
                        request_id,
                        request.rfp_id or request_id,
                        "completed",
                        result
                    )
                
                return ProcessingResponse(
                    request_id=request_id,
                    status="completed",
                    message="RFP processed successfully",
                    result=result
                )
            
            except Exception as e:
                self.logger.error(f"Processing failed: {e}", request_id=request_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/process-async", response_model=ProcessingResponse)
        async def process_rfp_async(request: RFPRequest, background_tasks: BackgroundTasks):
            """Process RFP (asynchronous)."""
            request_id = str(uuid.uuid4())
            
            try:
                self.logger.info("Starting async RFP processing", request_id=request_id)
                
                # Track request
                self.active_requests[request_id] = {
                    'status': 'processing',
                    'started_at': datetime.now().isoformat(),
                    'rfp_id': request.rfp_id or request_id
                }
                
                # Process in background
                background_tasks.add_task(
                    self._process_async,
                    request_id,
                    request.dict(),
                    request.callback_url
                )
                
                return ProcessingResponse(
                    request_id=request_id,
                    status="processing",
                    message="RFP processing started",
                    estimated_completion_time="2-5 minutes"
                )
            
            except Exception as e:
                self.logger.error(f"Failed to start processing: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/status/{request_id}")
        async def get_status(request_id: str):
            """Get processing status."""
            if request_id not in self.active_requests:
                raise HTTPException(status_code=404, detail="Request not found")
            
            return self.active_requests[request_id]
        
        @self.app.get("/api/v1/statistics")
        async def get_statistics():
            """Get agent statistics."""
            return self.agent.get_statistics()
        
        @self.app.post("/api/v1/batch-process")
        async def batch_process(requests: List[RFPRequest], background_tasks: BackgroundTasks):
            """Process multiple RFPs in batch."""
            batch_id = str(uuid.uuid4())
            
            self.logger.info(f"Starting batch processing", batch_id=batch_id, count=len(requests))
            
            request_ids = []
            for req in requests:
                request_id = str(uuid.uuid4())
                request_ids.append(request_id)
                
                background_tasks.add_task(
                    self._process_async,
                    request_id,
                    req.dict(),
                    req.callback_url
                )
            
            return {
                "batch_id": batch_id,
                "request_ids": request_ids,
                "status": "processing",
                "count": len(requests)
            }
    
    async def _process_async(self, request_id: str, rfp_data: Dict[str, Any], callback_url: Optional[str]):
        """Process RFP asynchronously."""
        start_time = datetime.now()
        
        try:
            # Set RFP ID
            if not rfp_data.get('rfp_id'):
                rfp_data['rfp_id'] = request_id
            
            # Process
            result = self.agent.process_rfp(rfp_data)
            
            # Update status
            self.active_requests[request_id] = {
                'status': 'completed',
                'started_at': self.active_requests[request_id]['started_at'],
                'completed_at': datetime.now().isoformat(),
                'processing_time_seconds': (datetime.now() - start_time).total_seconds(),
                'result': result
            }
            
            # Send webhook
            if callback_url:
                await self._send_webhook(
                    callback_url,
                    request_id,
                    rfp_data['rfp_id'],
                    "completed",
                    result
                )
            
            self.logger.info("Async processing completed", request_id=request_id)
        
        except Exception as e:
            self.logger.error(f"Async processing failed: {e}", request_id=request_id)
            self.active_requests[request_id] = {
                'status': 'failed',
                'started_at': self.active_requests[request_id]['started_at'],
                'completed_at': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def _send_webhook(
        self,
        url: str,
        request_id: str,
        rfp_id: str,
        status: str,
        result: Dict[str, Any]
    ):
        """Send webhook callback.
        
        Args:
            url: Webhook URL
            request_id: Request ID
            rfp_id: RFP ID
            status: Processing status
            result: Processing result
        """
        try:
            payload = WebhookPayload(
                request_id=request_id,
                rfp_id=rfp_id,
                status=status,
                result=result,
                completed_at=datetime.now().isoformat(),
                processing_time_seconds=0  # TODO: Calculate
            )
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload.dict(),
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        self.logger.info("Webhook sent successfully", url=url)
                    else:
                        self.logger.warning(f"Webhook failed: {response.status}", url=url)
        
        except Exception as e:
            self.logger.error(f"Webhook error: {e}", url=url)
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run API server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)


class WebhookManager:
    """Manage webhook subscriptions and deliveries."""
    
    def __init__(self):
        """Initialize webhook manager."""
        self.logger = logger.bind(component="WebhookManager")
        self.subscriptions = {}
        self.delivery_queue = asyncio.Queue()
        self.retry_policy = {
            'max_retries': 3,
            'retry_delay': [1, 5, 15]  # seconds
        }
    
    def subscribe(self, event_type: str, callback_url: str, headers: Optional[Dict[str, str]] = None):
        """Subscribe to webhook events.
        
        Args:
            event_type: Event type (rfp.completed, rfp.failed, etc.)
            callback_url: Callback URL
            headers: Optional headers to include
        """
        subscription_id = str(uuid.uuid4())
        
        self.subscriptions[subscription_id] = {
            'event_type': event_type,
            'callback_url': callback_url,
            'headers': headers or {},
            'created_at': datetime.now().isoformat(),
            'active': True
        }
        
        self.logger.info(f"Webhook subscribed", subscription_id=subscription_id, event=event_type)
        return subscription_id
    
    def unsubscribe(self, subscription_id: str):
        """Unsubscribe from webhooks.
        
        Args:
            subscription_id: Subscription ID
        """
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id]['active'] = False
            self.logger.info(f"Webhook unsubscribed", subscription_id=subscription_id)
    
    async def trigger_event(self, event_type: str, payload: Dict[str, Any]):
        """Trigger webhook event.
        
        Args:
            event_type: Event type
            payload: Event payload
        """
        self.logger.info(f"Triggering webhook event", event=event_type)
        
        # Find matching subscriptions
        for sub_id, sub in self.subscriptions.items():
            if sub['event_type'] == event_type and sub['active']:
                await self.delivery_queue.put({
                    'subscription_id': sub_id,
                    'callback_url': sub['callback_url'],
                    'headers': sub['headers'],
                    'payload': payload,
                    'retry_count': 0
                })
    
    async def process_deliveries(self):
        """Process webhook delivery queue."""
        while True:
            try:
                delivery = await self.delivery_queue.get()
                await self._deliver_webhook(delivery)
            except Exception as e:
                self.logger.error(f"Delivery processing error: {e}")
    
    async def _deliver_webhook(self, delivery: Dict[str, Any]):
        """Deliver webhook with retries.
        
        Args:
            delivery: Delivery details
        """
        url = delivery['callback_url']
        headers = delivery['headers']
        payload = delivery['payload']
        retry_count = delivery['retry_count']
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        self.logger.info("Webhook delivered", url=url)
                        return
                    else:
                        raise Exception(f"HTTP {response.status}")
        
        except Exception as e:
            self.logger.warning(f"Webhook delivery failed: {e}", url=url, retry=retry_count)
            
            # Retry logic
            if retry_count < self.retry_policy['max_retries']:
                await asyncio.sleep(self.retry_policy['retry_delay'][retry_count])
                delivery['retry_count'] += 1
                await self.delivery_queue.put(delivery)
            else:
                self.logger.error(f"Webhook delivery abandoned after {retry_count} retries", url=url)
