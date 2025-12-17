"""Webhook management for API."""
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import asyncio
import uuid

from pydantic import BaseModel, HttpUrl, Field
import httpx
import structlog

logger = structlog.get_logger()


class WebhookEvent(str, Enum):
    """Webhook event types."""
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_STAGE_COMPLETED = "workflow.stage.completed"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_COMPLETED = "approval.completed"
    QUOTE_GENERATED = "quote.generated"


class WebhookStatus(str, Enum):
    """Webhook delivery status."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class Webhook(BaseModel):
    """Webhook subscription model."""
    webhook_id: str = Field(default_factory=lambda: f"wh_{uuid.uuid4().hex[:12]}")
    url: HttpUrl = Field(..., description="URL to send webhook to")
    events: List[WebhookEvent] = Field(..., description="Events to subscribe to")
    secret: Optional[str] = Field(None, description="Secret for signature verification")
    active: bool = Field(default=True, description="Whether webhook is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WebhookDelivery(BaseModel):
    """Webhook delivery attempt."""
    delivery_id: str = Field(default_factory=lambda: f"del_{uuid.uuid4().hex[:12]}")
    webhook_id: str
    event: WebhookEvent
    payload: Dict[str, Any]
    status: WebhookStatus = WebhookStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None


class WebhookPayload(BaseModel):
    """Webhook payload structure."""
    event: WebhookEvent
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]
    webhook_id: str


class WebhookManager:
    """Manager for webhook subscriptions and deliveries."""
    
    def __init__(self):
        self.webhooks: Dict[str, Webhook] = {}
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.client = httpx.AsyncClient(timeout=10.0)
    
    def register_webhook(self, webhook: Webhook) -> Webhook:
        """Register a new webhook subscription."""
        self.webhooks[webhook.webhook_id] = webhook
        logger.info(
            "Webhook registered",
            webhook_id=webhook.webhook_id,
            url=str(webhook.url),
            events=[e.value for e in webhook.events]
        )
        return webhook
    
    def unregister_webhook(self, webhook_id: str) -> bool:
        """Unregister a webhook subscription."""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            logger.info("Webhook unregistered", webhook_id=webhook_id)
            return True
        return False
    
    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get webhook by ID."""
        return self.webhooks.get(webhook_id)
    
    def list_webhooks(self, active_only: bool = True) -> List[Webhook]:
        """List all webhooks."""
        webhooks = list(self.webhooks.values())
        if active_only:
            webhooks = [wh for wh in webhooks if wh.active]
        return webhooks
    
    def update_webhook(self, webhook_id: str, updates: Dict[str, Any]) -> Optional[Webhook]:
        """Update webhook configuration."""
        if webhook_id not in self.webhooks:
            return None
        
        webhook = self.webhooks[webhook_id]
        for key, value in updates.items():
            if hasattr(webhook, key):
                setattr(webhook, key, value)
        
        logger.info("Webhook updated", webhook_id=webhook_id, updates=updates)
        return webhook
    
    async def trigger_event(
        self,
        event: WebhookEvent,
        data: Dict[str, Any]
    ) -> List[WebhookDelivery]:
        """Trigger webhook event to all subscribed webhooks."""
        deliveries = []
        
        for webhook in self.webhooks.values():
            if not webhook.active:
                continue
            
            if event not in webhook.events:
                continue
            
            # Create delivery
            delivery = WebhookDelivery(
                webhook_id=webhook.webhook_id,
                event=event,
                payload=data
            )
            self.deliveries[delivery.delivery_id] = delivery
            deliveries.append(delivery)
            
            # Send webhook asynchronously
            asyncio.create_task(self._deliver_webhook(webhook, delivery))
        
        logger.info(
            "Webhook event triggered",
            event=event.value,
            webhooks_notified=len(deliveries)
        )
        
        return deliveries
    
    async def _deliver_webhook(
        self,
        webhook: Webhook,
        delivery: WebhookDelivery
    ):
        """Deliver webhook with retries."""
        payload = WebhookPayload(
            event=delivery.event,
            data=delivery.payload,
            webhook_id=webhook.webhook_id
        )
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": delivery.event.value,
            "X-Webhook-ID": webhook.webhook_id,
            "X-Delivery-ID": delivery.delivery_id
        }
        
        # Add signature if secret is provided
        if webhook.secret:
            import hmac
            import hashlib
            signature = hmac.new(
                webhook.secret.encode(),
                payload.json().encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"
        
        for attempt in range(1, delivery.max_attempts + 1):
            delivery.attempts = attempt
            delivery.status = WebhookStatus.RETRYING if attempt > 1 else WebhookStatus.PENDING
            
            try:
                response = await self.client.post(
                    str(webhook.url),
                    json=payload.dict(),
                    headers=headers
                )
                
                delivery.response_status = response.status_code
                delivery.response_body = response.text[:1000]  # Limit stored response
                
                if response.status_code < 300:
                    delivery.status = WebhookStatus.DELIVERED
                    delivery.delivered_at = datetime.utcnow()
                    logger.info(
                        "Webhook delivered",
                        webhook_id=webhook.webhook_id,
                        delivery_id=delivery.delivery_id,
                        status_code=response.status_code,
                        attempt=attempt
                    )
                    break
                else:
                    delivery.error = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.warning(
                        "Webhook delivery failed",
                        webhook_id=webhook.webhook_id,
                        delivery_id=delivery.delivery_id,
                        status_code=response.status_code,
                        attempt=attempt
                    )
            
            except Exception as e:
                delivery.error = str(e)
                logger.error(
                    "Webhook delivery error",
                    webhook_id=webhook.webhook_id,
                    delivery_id=delivery.delivery_id,
                    error=str(e),
                    attempt=attempt
                )
            
            # Wait before retry (exponential backoff)
            if attempt < delivery.max_attempts:
                await asyncio.sleep(2 ** attempt)
        
        # Mark as failed if all attempts exhausted
        if delivery.status != WebhookStatus.DELIVERED:
            delivery.status = WebhookStatus.FAILED
    
    def get_delivery(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get delivery by ID."""
        return self.deliveries.get(delivery_id)
    
    def list_deliveries(
        self,
        webhook_id: Optional[str] = None,
        limit: int = 100
    ) -> List[WebhookDelivery]:
        """List webhook deliveries."""
        deliveries = list(self.deliveries.values())
        
        if webhook_id:
            deliveries = [d for d in deliveries if d.webhook_id == webhook_id]
        
        # Sort by created_at descending
        deliveries.sort(key=lambda d: d.created_at, reverse=True)
        
        return deliveries[:limit]
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
