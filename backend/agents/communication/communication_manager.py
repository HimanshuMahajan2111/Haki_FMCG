"""Communication Manager - High-level API for inter-agent communication."""
import asyncio
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import structlog

from .message_broker import (
    MessageBroker, InMemoryMessageBroker, RedisMessageBroker,
    Message, MessagePriority
)
from .state_manager import StateManager, InMemoryStateManager, RedisStateManager, StateType
from .retry_handler import RetryHandler, RetryPolicy, CircuitBreaker
from .monitoring import MessageTracer, QueueMonitor, PerformanceMetrics

logger = structlog.get_logger()


class AgentMessageType(Enum):
    """Standard message types for agents."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    COMMAND = "command"
    EVENT = "event"
    ERROR = "error"


@dataclass
class AgentMessage:
    """High-level agent message."""
    sender: str
    recipient: str
    message_type: AgentMessageType
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    timeout: Optional[float] = None
    
    def to_broker_message(self) -> Message:
        """Convert to broker message."""
        return Message(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            recipient=self.recipient,
            message_type=self.message_type.value,
            payload=self.payload,
            priority=self.priority,
            correlation_id=self.correlation_id,
            reply_to=self.reply_to,
            expiry=time.time() + self.timeout if self.timeout else None
        )
    
    @classmethod
    def from_broker_message(cls, msg: Message) -> 'AgentMessage':
        """Create from broker message."""
        return cls(
            sender=msg.sender,
            recipient=msg.recipient,
            message_type=AgentMessageType(msg.message_type),
            payload=msg.payload,
            priority=msg.priority,
            correlation_id=msg.correlation_id,
            reply_to=msg.reply_to
        )


class CommunicationManager:
    """High-level API for inter-agent communication."""
    
    def __init__(self,
                 use_redis: bool = False,
                 redis_url: str = "redis://localhost:6379/0"):
        """Initialize communication manager.
        
        Args:
            use_redis: Whether to use Redis or in-memory storage
            redis_url: Redis connection URL
        """
        # Initialize message broker
        if use_redis:
            self.message_broker = RedisMessageBroker(redis_url)
        else:
            self.message_broker = InMemoryMessageBroker()
        
        # Initialize state manager
        if use_redis:
            self.state_manager = RedisStateManager(redis_url)
        else:
            self.state_manager = InMemoryStateManager()
        
        # Initialize retry handler
        self.retry_handler = RetryHandler()
        
        # Initialize monitoring components
        self.tracer = MessageTracer()
        self.queue_monitor = QueueMonitor()
        self.performance_metrics = PerformanceMetrics()
        
        # Track registered agents
        self.agents: Dict[str, Dict[str, Any]] = {}
        
        # Message handlers
        self.handlers: Dict[str, Dict[str, Callable]] = {}
        
        # Pending requests (for request-response pattern)
        self.pending_requests: Dict[str, asyncio.Future] = {}
        
        logger.info("Initialized CommunicationManager", use_redis=use_redis)
    
    async def connect(self):
        """Connect to backend services."""
        if isinstance(self.message_broker, RedisMessageBroker):
            await self.message_broker.connect()
        if isinstance(self.state_manager, RedisStateManager):
            await self.state_manager.connect()
        
        if isinstance(self.state_manager, InMemoryStateManager):
            await self.state_manager.start_cleanup_task()
        
        logger.info("Connected to communication backend")
    
    async def disconnect(self):
        """Disconnect from backend services."""
        if isinstance(self.message_broker, RedisMessageBroker):
            await self.message_broker.disconnect()
        if isinstance(self.state_manager, RedisStateManager):
            await self.state_manager.disconnect()
        
        if isinstance(self.state_manager, InMemoryStateManager):
            await self.state_manager.stop_cleanup_task()
        
        logger.info("Disconnected from communication backend")
    
    async def register_agent(self,
                            agent_id: str,
                            agent_type: str,
                            capabilities: List[str] = None):
        """Register an agent."""
        self.agents[agent_id] = {
            'agent_type': agent_type,
            'capabilities': capabilities or [],
            'registered_at': datetime.utcnow().isoformat(),
            'status': 'active'
        }
        
        # Subscribe to messages
        await self.message_broker.subscribe(agent_id, self._handle_message)
        
        # Store agent info in state
        await self.state_manager.set(
            f"agent:{agent_id}:info",
            self.agents[agent_id],
            StateType.AGENT
        )
        
        logger.info("Registered agent",
                   agent_id=agent_id,
                   agent_type=agent_type)
    
    async def unregister_agent(self, agent_id: str):
        """Unregister an agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            await self.state_manager.delete(f"agent:{agent_id}:info")
            logger.info("Unregistered agent", agent_id=agent_id)
    
    async def send_message(self, message: AgentMessage) -> bool:
        """Send a message to another agent."""
        start_time = time.time()
        try:
            broker_msg = message.to_broker_message()
            
            # Start tracing
            await self.tracer.start_trace(
                broker_msg.message_id,
                message.sender,
                message.recipient,
                message.message_type.value,
                message.correlation_id
            )
            
            # Record queue activity
            self.queue_monitor.record_enqueue(message.recipient)
            
            # Use retry handler
            success = await self.retry_handler.execute(
                self.message_broker.publish,
                broker_msg
            )
            
            # Record metrics
            latency = time.time() - start_time
            self.performance_metrics.record_latency(latency)
            
            if success:
                await self.tracer.mark_delivered(broker_msg.message_id)
                logger.debug("Message sent",
                           sender=message.sender,
                           recipient=message.recipient,
                           type=message.message_type.value)
            else:
                await self.tracer.mark_failed(broker_msg.message_id, "Publish failed")
                self.performance_metrics.record_error()
            
            return success
            
        except Exception as e:
            self.performance_metrics.record_error()
            logger.error("Failed to send message", error=str(e))
            return False
    
    async def send_request(self,
                          sender: str,
                          recipient: str,
                          payload: Dict[str, Any],
                          timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """Send a request and wait for response."""
        correlation_id = str(uuid.uuid4())
        future = asyncio.Future()
        self.pending_requests[correlation_id] = future
        
        try:
            message = AgentMessage(
                sender=sender,
                recipient=recipient,
                message_type=AgentMessageType.REQUEST,
                payload=payload,
                correlation_id=correlation_id,
                reply_to=sender,
                timeout=timeout
            )
            
            success = await self.send_message(message)
            if not success:
                return None
            
            # Wait for response
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
            
        except asyncio.TimeoutError:
            logger.error("Request timeout", correlation_id=correlation_id)
            return None
        except Exception as e:
            logger.error("Request failed", error=str(e))
            return None
        finally:
            if correlation_id in self.pending_requests:
                del self.pending_requests[correlation_id]
    
    async def send_response(self,
                          request_msg: Message,
                          response_payload: Dict[str, Any]):
        """Send a response to a request."""
        if not request_msg.reply_to or not request_msg.correlation_id:
            logger.warning("Cannot send response - missing reply_to or correlation_id")
            return
        
        message = AgentMessage(
            sender=request_msg.recipient,
            recipient=request_msg.reply_to,
            message_type=AgentMessageType.RESPONSE,
            payload=response_payload,
            correlation_id=request_msg.correlation_id
        )
        
        await self.send_message(message)
    
    async def register_handler(self,
                              agent_id: str,
                              message_type: str,
                              handler: Callable):
        """Register a message handler."""
        if agent_id not in self.handlers:
            self.handlers[agent_id] = {}
        
        self.handlers[agent_id][message_type] = handler
        logger.info("Registered handler",
                   agent_id=agent_id,
                   message_type=message_type)
    
    async def _handle_message(self, message: Message):
        """Internal message handler."""
        try:
            # Check if this is a response to a pending request
            if (message.message_type == AgentMessageType.RESPONSE.value and
                message.correlation_id in self.pending_requests):
                future = self.pending_requests[message.correlation_id]
                if not future.done():
                    future.set_result(message.payload)
                return
            
            # Call registered handler if exists
            if message.recipient in self.handlers:
                handler = self.handlers[message.recipient].get(message.message_type)
                if handler:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                else:
                    logger.warning("No handler for message type",
                                 agent=message.recipient,
                                 type=message.message_type)
        
        except Exception as e:
            logger.error("Error handling message", error=str(e))
    
    async def set_agent_state(self,
                             agent_id: str,
                             key: str,
                             value: Any,
                             ttl: Optional[int] = None):
        """Set agent state."""
        state_key = f"agent:{agent_id}:{key}"
        await self.state_manager.set(state_key, value, StateType.AGENT, ttl)
    
    async def get_agent_state(self, agent_id: str, key: str) -> Optional[Any]:
        """Get agent state."""
        state_key = f"agent:{agent_id}:{key}"
        return await self.state_manager.get(state_key)
    
    async def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information."""
        return await self.state_manager.get(f"agent:{agent_id}:info")
    
    async def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered agents."""
        return await self.state_manager.get_all("agent:*:info")
    
    async def get_queue_size(self, agent_id: str) -> int:
        """Get number of pending messages for agent."""
        return await self.message_broker.get_queue_size(agent_id)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self.performance_metrics.get_summary()
    
    def get_message_analytics(self) -> Dict[str, Any]:
        """Get message analytics."""
        analytics = self.tracer.get_analytics()
        return {
            'total_messages': analytics.total_messages,
            'delivered': analytics.total_delivered,
            'failed': analytics.total_failed,
            'acknowledged': analytics.total_acknowledged,
            'success_rate': analytics.get_success_rate(),
            'failure_rate': analytics.get_failure_rate(),
            'avg_processing_time_ms': analytics.avg_processing_time * 1000,
            'max_processing_time_ms': analytics.max_processing_time * 1000,
            'messages_by_type': dict(analytics.messages_by_type),
            'messages_by_sender': dict(analytics.messages_by_sender)
        }
    
    def get_queue_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get queue statistics for an agent."""
        return self.queue_monitor.get_queue_stats(agent_id)
    
    def get_all_queue_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all queues."""
        return self.queue_monitor.get_all_queue_stats()
    
    def get_message_trace(self, message_id: str):
        """Get trace information for a message."""
        return self.tracer.get_trace(message_id)
    
    def get_failed_messages(self, limit: int = 100):
        """Get recent failed messages."""
        return self.tracer.get_failed_traces(limit)
    
    async def broadcast(self,
                       sender: str,
                       payload: Dict[str, Any],
                       agent_type: Optional[str] = None):
        """Broadcast message to all agents or specific type."""
        agents = await self.get_all_agents()
        
        for agent_id, info in agents.items():
            # Skip sender
            if agent_id == sender:
                continue
            
            # Filter by type if specified
            if agent_type and info.get('agent_type') != agent_type:
                continue
            
            message = AgentMessage(
                sender=sender,
                recipient=agent_id,
                message_type=AgentMessageType.NOTIFICATION,
                payload=payload
            )
            
            await self.send_message(message)
        
        logger.info("Broadcast sent",
                   sender=sender,
                   agent_type=agent_type,
                   recipients=len(agents))
