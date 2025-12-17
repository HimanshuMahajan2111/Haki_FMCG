"""
Enhanced Inter-Agent Communication System
Comprehensive message passing, state management, error handling, and retry logic.
Supports both Redis and in-memory backends.
"""
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
import time
import asyncio
from abc import ABC, abstractmethod
import structlog

logger = structlog.get_logger()


# ============================================================================
# Enums and Data Classes
# ============================================================================

class MessageType(Enum):
    """Message types for inter-agent communication."""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    COMMAND = "command"
    NOTIFICATION = "notification"
    HEARTBEAT = "heartbeat"


class MessagePriority(Enum):
    """Message priority levels."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class MessageState(Enum):
    """Message lifecycle states."""
    QUEUED = "queued"
    DISPATCHED = "dispatched"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    DEAD_LETTER = "dead_letter"


class AgentState(Enum):
    """Agent operational states."""
    IDLE = "idle"
    BUSY = "busy"
    WAITING = "waiting"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class InterAgentMessage:
    """
    Inter-agent message with full metadata.
    """
    # Identity
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None  # For request-response tracking
    conversation_id: Optional[str] = None  # For multi-message conversations
    
    # Routing
    from_agent: str = ""
    to_agent: str = ""
    reply_to: Optional[str] = None  # Queue to send reply
    
    # Message details
    message_type: MessageType = MessageType.REQUEST
    priority: MessagePriority = MessagePriority.NORMAL
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # State tracking
    state: MessageState = MessageState.QUEUED
    retry_count: int = 0
    max_retries: int = 3
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    dispatched_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'message_id': self.message_id,
            'correlation_id': self.correlation_id,
            'conversation_id': self.conversation_id,
            'from_agent': self.from_agent,
            'to_agent': self.to_agent,
            'reply_to': self.reply_to,
            'message_type': self.message_type.value,
            'priority': self.priority.value,
            'payload': self.payload,
            'state': self.state.value,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at.isoformat(),
            'dispatched_at': self.dispatched_at.isoformat() if self.dispatched_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'metadata': self.metadata,
            'error_info': self.error_info
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InterAgentMessage':
        """Create message from dictionary."""
        msg = cls()
        msg.message_id = data.get('message_id', str(uuid.uuid4()))
        msg.correlation_id = data.get('correlation_id')
        msg.conversation_id = data.get('conversation_id')
        msg.from_agent = data.get('from_agent', '')
        msg.to_agent = data.get('to_agent', '')
        msg.reply_to = data.get('reply_to')
        msg.message_type = MessageType(data.get('message_type', 'request'))
        msg.priority = MessagePriority(data.get('priority', 3))
        msg.payload = data.get('payload', {})
        msg.state = MessageState(data.get('state', 'queued'))
        msg.retry_count = data.get('retry_count', 0)
        msg.max_retries = data.get('max_retries', 3)
        
        # Parse timestamps
        if data.get('created_at'):
            msg.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('dispatched_at'):
            msg.dispatched_at = datetime.fromisoformat(data['dispatched_at'])
        if data.get('completed_at'):
            msg.completed_at = datetime.fromisoformat(data['completed_at'])
        if data.get('expires_at'):
            msg.expires_at = datetime.fromisoformat(data['expires_at'])
            
        msg.metadata = data.get('metadata', {})
        msg.error_info = data.get('error_info')
        
        return msg


@dataclass
class AgentStateInfo:
    """Agent state information."""
    agent_id: str
    state: AgentState
    last_heartbeat: datetime
    message_count: int = 0
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Abstract Message Backend
# ============================================================================

class MessageBackend(ABC):
    """Abstract backend for message storage and retrieval."""
    
    @abstractmethod
    async def push_message(self, queue_name: str, message: InterAgentMessage) -> bool:
        """Push message to queue."""
        pass
    
    @abstractmethod
    async def pop_message(self, queue_name: str, timeout: Optional[float] = None) -> Optional[InterAgentMessage]:
        """Pop message from queue."""
        pass
    
    @abstractmethod
    async def peek_message(self, queue_name: str) -> Optional[InterAgentMessage]:
        """Peek at next message without removing."""
        pass
    
    @abstractmethod
    async def get_message(self, message_id: str) -> Optional[InterAgentMessage]:
        """Get specific message by ID."""
        pass
    
    @abstractmethod
    async def update_message_state(self, message_id: str, state: MessageState) -> bool:
        """Update message state."""
        pass
    
    @abstractmethod
    async def get_queue_size(self, queue_name: str) -> int:
        """Get queue size."""
        pass
    
    @abstractmethod
    async def set_agent_state(self, agent_id: str, state: AgentStateInfo) -> bool:
        """Set agent state."""
        pass
    
    @abstractmethod
    async def get_agent_state(self, agent_id: str) -> Optional[AgentStateInfo]:
        """Get agent state."""
        pass


# ============================================================================
# In-Memory Backend
# ============================================================================

class InMemoryBackend(MessageBackend):
    """In-memory message backend using asyncio queues."""
    
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        self.messages: Dict[str, InterAgentMessage] = {}  # message_id -> message
        self.agent_states: Dict[str, AgentStateInfo] = {}
        self.lock = asyncio.Lock()
        
        logger.info("Initialized in-memory message backend")
    
    def _get_queue(self, queue_name: str) -> asyncio.Queue:
        """Get or create queue."""
        if queue_name not in self.queues:
            self.queues[queue_name] = asyncio.Queue()
        return self.queues[queue_name]
    
    async def push_message(self, queue_name: str, message: InterAgentMessage) -> bool:
        """Push message to queue."""
        try:
            async with self.lock:
                # Store message
                self.messages[message.message_id] = message
                
                # Add to queue (priority sorted)
                queue = self._get_queue(queue_name)
                await queue.put((message.priority.value, message.message_id))
                
                logger.debug(
                    "Message pushed to queue",
                    queue=queue_name,
                    message_id=message.message_id,
                    priority=message.priority.value
                )
                return True
        except Exception as e:
            logger.error("Failed to push message", error=str(e))
            return False
    
    async def pop_message(self, queue_name: str, timeout: Optional[float] = None) -> Optional[InterAgentMessage]:
        """Pop message from queue."""
        try:
            queue = self._get_queue(queue_name)
            
            if timeout:
                priority, message_id = await asyncio.wait_for(queue.get(), timeout=timeout)
            else:
                priority, message_id = await queue.get()
            
            async with self.lock:
                message = self.messages.get(message_id)
                if message:
                    message.dispatched_at = datetime.now()
                    message.state = MessageState.DISPATCHED
                    logger.debug(
                        "Message popped from queue",
                        queue=queue_name,
                        message_id=message_id
                    )
                return message
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error("Failed to pop message", error=str(e))
            return None
    
    async def peek_message(self, queue_name: str) -> Optional[InterAgentMessage]:
        """Peek at next message without removing."""
        queue = self._get_queue(queue_name)
        if queue.empty():
            return None
        
        # Peek by getting and putting back
        priority, message_id = await queue.get()
        await queue.put((priority, message_id))
        
        return self.messages.get(message_id)
    
    async def get_message(self, message_id: str) -> Optional[InterAgentMessage]:
        """Get specific message by ID."""
        async with self.lock:
            return self.messages.get(message_id)
    
    async def update_message_state(self, message_id: str, state: MessageState) -> bool:
        """Update message state."""
        async with self.lock:
            if message_id in self.messages:
                self.messages[message_id].state = state
                if state == MessageState.COMPLETED:
                    self.messages[message_id].completed_at = datetime.now()
                logger.debug(
                    "Message state updated",
                    message_id=message_id,
                    state=state.value
                )
                return True
            return False
    
    async def get_queue_size(self, queue_name: str) -> int:
        """Get queue size."""
        queue = self._get_queue(queue_name)
        return queue.qsize()
    
    async def set_agent_state(self, agent_id: str, state: AgentStateInfo) -> bool:
        """Set agent state."""
        async with self.lock:
            self.agent_states[agent_id] = state
            return True
    
    async def get_agent_state(self, agent_id: str) -> Optional[AgentStateInfo]:
        """Get agent state."""
        async with self.lock:
            return self.agent_states.get(agent_id)


# ============================================================================
# Redis Backend
# ============================================================================

class RedisBackend(MessageBackend):
    """Redis-based message backend for distributed systems."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize Redis backend.
        
        Args:
            redis_url: Redis connection URL
        """
        try:
            import redis.asyncio as aioredis
            self.redis = aioredis.from_url(redis_url, decode_responses=False)
            self.redis_url = redis_url
            logger.info("Initialized Redis message backend", url=redis_url)
        except ImportError:
            logger.error("redis package not installed. Install with: pip install redis")
            raise
    
    def _queue_key(self, queue_name: str) -> str:
        """Get Redis key for queue."""
        return f"queue:{queue_name}"
    
    def _message_key(self, message_id: str) -> str:
        """Get Redis key for message."""
        return f"message:{message_id}"
    
    def _agent_state_key(self, agent_id: str) -> str:
        """Get Redis key for agent state."""
        return f"agent:{agent_id}:state"
    
    async def push_message(self, queue_name: str, message: InterAgentMessage) -> bool:
        """Push message to Redis queue."""
        try:
            # Store message
            message_key = self._message_key(message.message_id)
            message_data = json.dumps(message.to_dict())
            await self.redis.set(message_key, message_data)
            await self.redis.expire(message_key, 86400)  # 24 hour TTL
            
            # Add to priority queue (sorted set)
            queue_key = self._queue_key(queue_name)
            score = message.priority.value * 1000000 + time.time()  # Priority + timestamp
            await self.redis.zadd(queue_key, {message.message_id: score})
            
            logger.debug(
                "Message pushed to Redis",
                queue=queue_name,
                message_id=message.message_id
            )
            return True
        except Exception as e:
            logger.error("Failed to push message to Redis", error=str(e))
            return False
    
    async def pop_message(self, queue_name: str, timeout: Optional[float] = None) -> Optional[InterAgentMessage]:
        """Pop message from Redis queue."""
        try:
            queue_key = self._queue_key(queue_name)
            
            if timeout:
                # Blocking pop with timeout
                result = await self.redis.bzpopmin(queue_key, timeout=int(timeout))
                if not result:
                    return None
                _, message_id, _ = result
                message_id = message_id.decode('utf-8')
            else:
                # Non-blocking pop
                result = await self.redis.zpopmin(queue_key, count=1)
                if not result:
                    return None
                message_id, _ = result[0]
                message_id = message_id.decode('utf-8')
            
            # Get message data
            message_key = self._message_key(message_id)
            message_data = await self.redis.get(message_key)
            
            if message_data:
                message = InterAgentMessage.from_dict(json.loads(message_data))
                message.dispatched_at = datetime.now()
                message.state = MessageState.DISPATCHED
                
                # Update state in Redis
                await self.redis.set(message_key, json.dumps(message.to_dict()))
                
                logger.debug(
                    "Message popped from Redis",
                    queue=queue_name,
                    message_id=message_id
                )
                return message
            
            return None
        except Exception as e:
            logger.error("Failed to pop message from Redis", error=str(e))
            return None
    
    async def peek_message(self, queue_name: str) -> Optional[InterAgentMessage]:
        """Peek at next message without removing."""
        try:
            queue_key = self._queue_key(queue_name)
            result = await self.redis.zrange(queue_key, 0, 0, withscores=False)
            
            if not result:
                return None
            
            message_id = result[0].decode('utf-8')
            message_key = self._message_key(message_id)
            message_data = await self.redis.get(message_key)
            
            if message_data:
                return InterAgentMessage.from_dict(json.loads(message_data))
            
            return None
        except Exception as e:
            logger.error("Failed to peek message from Redis", error=str(e))
            return None
    
    async def get_message(self, message_id: str) -> Optional[InterAgentMessage]:
        """Get specific message by ID."""
        try:
            message_key = self._message_key(message_id)
            message_data = await self.redis.get(message_key)
            
            if message_data:
                return InterAgentMessage.from_dict(json.loads(message_data))
            
            return None
        except Exception as e:
            logger.error("Failed to get message from Redis", error=str(e))
            return None
    
    async def update_message_state(self, message_id: str, state: MessageState) -> bool:
        """Update message state."""
        try:
            message = await self.get_message(message_id)
            if not message:
                return False
            
            message.state = state
            if state == MessageState.COMPLETED:
                message.completed_at = datetime.now()
            
            message_key = self._message_key(message_id)
            await self.redis.set(message_key, json.dumps(message.to_dict()))
            
            logger.debug(
                "Message state updated in Redis",
                message_id=message_id,
                state=state.value
            )
            return True
        except Exception as e:
            logger.error("Failed to update message state in Redis", error=str(e))
            return False
    
    async def get_queue_size(self, queue_name: str) -> int:
        """Get queue size."""
        try:
            queue_key = self._queue_key(queue_name)
            return await self.redis.zcard(queue_key)
        except Exception as e:
            logger.error("Failed to get queue size from Redis", error=str(e))
            return 0
    
    async def set_agent_state(self, agent_id: str, state: AgentStateInfo) -> bool:
        """Set agent state."""
        try:
            state_key = self._agent_state_key(agent_id)
            state_data = {
                'agent_id': state.agent_id,
                'state': state.state.value,
                'last_heartbeat': state.last_heartbeat.isoformat(),
                'message_count': state.message_count,
                'error_count': state.error_count,
                'metadata': json.dumps(state.metadata)
            }
            await self.redis.hset(state_key, mapping=state_data)
            await self.redis.expire(state_key, 300)  # 5 minute TTL
            return True
        except Exception as e:
            logger.error("Failed to set agent state in Redis", error=str(e))
            return False
    
    async def get_agent_state(self, agent_id: str) -> Optional[AgentStateInfo]:
        """Get agent state."""
        try:
            state_key = self._agent_state_key(agent_id)
            state_data = await self.redis.hgetall(state_key)
            
            if not state_data:
                return None
            
            # Decode bytes to strings
            state_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in state_data.items()}
            
            return AgentStateInfo(
                agent_id=state_data['agent_id'],
                state=AgentState(state_data['state']),
                last_heartbeat=datetime.fromisoformat(state_data['last_heartbeat']),
                message_count=int(state_data['message_count']),
                error_count=int(state_data['error_count']),
                metadata=json.loads(state_data['metadata'])
            )
        except Exception as e:
            logger.error("Failed to get agent state from Redis", error=str(e))
            return None
    
    async def close(self):
        """Close Redis connection."""
        await self.redis.close()


# ============================================================================
# Communication Manager
# ============================================================================

class InterAgentCommunicationManager:
    """
    Main communication manager for inter-agent message passing.
    
    Features:
    - Multiple backend support (in-memory, Redis)
    - Message routing and delivery
    - State management
    - Error handling and retry logic
    - Dead letter queue
    - Request/Response patterns
    - Publish/Subscribe
    """
    
    def __init__(
        self,
        backend: Optional[MessageBackend] = None,
        enable_retry: bool = True,
        enable_dead_letter: bool = True,
        default_timeout: float = 30.0
    ):
        """Initialize communication manager.
        
        Args:
            backend: Message backend (in-memory or Redis)
            enable_retry: Enable automatic retry on failures
            enable_dead_letter: Move failed messages to dead letter queue
            default_timeout: Default message timeout in seconds
        """
        self.backend = backend or InMemoryBackend()
        self.enable_retry = enable_retry
        self.enable_dead_letter = enable_dead_letter
        self.default_timeout = default_timeout
        
        # Message handlers
        self.handlers: Dict[str, List[Callable]] = {}
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_delivered': 0,
            'messages_failed': 0,
            'messages_timeout': 0,
            'retry_attempts': 0
        }
        
        logger.info(
            "Inter-agent communication manager initialized",
            backend=type(self.backend).__name__,
            retry_enabled=enable_retry,
            dead_letter_enabled=enable_dead_letter
        )
    
    def _get_agent_queue_name(self, agent_id: str) -> str:
        """Get queue name for agent."""
        return f"agent:{agent_id}"
    
    async def send_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: Optional[str] = None,
        timeout_seconds: Optional[float] = None
    ) -> str:
        """
        Send message to another agent.
        
        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            message_type: Type of message
            payload: Message payload
            priority: Message priority
            correlation_id: Correlation ID for tracking
            timeout_seconds: Message timeout
            
        Returns:
            Message ID
        """
        # Create message
        message = InterAgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload,
            priority=priority,
            correlation_id=correlation_id or str(uuid.uuid4())
        )
        
        # Set expiration
        if timeout_seconds:
            message.expires_at = datetime.now() + timedelta(seconds=timeout_seconds)
        elif self.default_timeout:
            message.expires_at = datetime.now() + timedelta(seconds=self.default_timeout)
        
        # Push to agent's queue
        queue_name = self._get_agent_queue_name(to_agent)
        success = await self.backend.push_message(queue_name, message)
        
        if success:
            self.stats['messages_sent'] += 1
            logger.info(
                "Message sent",
                message_id=message.message_id,
                from_agent=from_agent,
                to_agent=to_agent,
                type=message_type.value
            )
        else:
            logger.error("Failed to send message", message_id=message.message_id)
        
        return message.message_id
    
    async def receive_message(
        self,
        agent_id: str,
        timeout: Optional[float] = None
    ) -> Optional[InterAgentMessage]:
        """
        Receive message for agent.
        
        Args:
            agent_id: Agent ID
            timeout: Timeout in seconds
            
        Returns:
            Message or None
        """
        queue_name = self._get_agent_queue_name(agent_id)
        message = await self.backend.pop_message(queue_name, timeout)
        
        if message:
            # Check expiration
            if message.expires_at and datetime.now() > message.expires_at:
                await self._handle_timeout(message)
                return None
            
            self.stats['messages_delivered'] += 1
            logger.info(
                "Message received",
                message_id=message.message_id,
                agent_id=agent_id,
                type=message.message_type.value
            )
        
        return message
    
    async def process_message(
        self,
        message: InterAgentMessage,
        handler: Callable[[InterAgentMessage], Any]
    ) -> bool:
        """
        Process message with error handling and retry logic.
        
        Args:
            message: Message to process
            handler: Handler function
            
        Returns:
            Success status
        """
        try:
            # Update state
            await self.backend.update_message_state(
                message.message_id,
                MessageState.PROCESSING
            )
            
            # Process message
            result = await handler(message)
            
            # Mark as completed
            await self.backend.update_message_state(
                message.message_id,
                MessageState.COMPLETED
            )
            
            logger.info(
                "Message processed successfully",
                message_id=message.message_id
            )
            return True
            
        except Exception as e:
            logger.error(
                "Error processing message",
                message_id=message.message_id,
                error=str(e)
            )
            
            # Handle retry
            if self.enable_retry and message.retry_count < message.max_retries:
                await self._retry_message(message)
            else:
                await self._handle_failure(message, str(e))
            
            return False
    
    async def _retry_message(self, message: InterAgentMessage):
        """Retry failed message."""
        message.retry_count += 1
        message.state = MessageState.QUEUED
        
        # Re-queue message
        queue_name = self._get_agent_queue_name(message.to_agent)
        await self.backend.push_message(queue_name, message)
        
        self.stats['retry_attempts'] += 1
        logger.warning(
            "Message retry scheduled",
            message_id=message.message_id,
            retry_count=message.retry_count,
            max_retries=message.max_retries
        )
    
    async def _handle_failure(self, message: InterAgentMessage, error: str):
        """Handle message failure."""
        message.state = MessageState.FAILED
        message.error_info = {
            'error': error,
            'failed_at': datetime.now().isoformat()
        }
        
        await self.backend.update_message_state(
            message.message_id,
            MessageState.FAILED
        )
        
        # Move to dead letter queue if enabled
        if self.enable_dead_letter:
            dlq_name = "dead_letter_queue"
            await self.backend.push_message(dlq_name, message)
            logger.info(
                "Message moved to dead letter queue",
                message_id=message.message_id
            )
        
        self.stats['messages_failed'] += 1
    
    async def _handle_timeout(self, message: InterAgentMessage):
        """Handle message timeout."""
        message.state = MessageState.TIMEOUT
        
        await self.backend.update_message_state(
            message.message_id,
            MessageState.TIMEOUT
        )
        
        self.stats['messages_timeout'] += 1
        logger.warning(
            "Message timeout",
            message_id=message.message_id,
            expires_at=message.expires_at
        )
    
    async def request_response(
        self,
        from_agent: str,
        to_agent: str,
        payload: Dict[str, Any],
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        Send request and wait for response.
        
        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            payload: Request payload
            timeout: Response timeout
            
        Returns:
            Response payload or None
        """
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        
        # Send request
        await self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.REQUEST,
            payload=payload,
            correlation_id=correlation_id,
            timeout_seconds=timeout
        )
        
        # Wait for response
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = await self.receive_message(from_agent, timeout=1.0)
            
            if response and response.correlation_id == correlation_id:
                if response.message_type == MessageType.RESPONSE:
                    return response.payload
            
            await asyncio.sleep(0.1)
        
        logger.warning(
            "Request-response timeout",
            from_agent=from_agent,
            to_agent=to_agent,
            correlation_id=correlation_id
        )
        return None
    
    async def publish_event(
        self,
        from_agent: str,
        event_type: str,
        payload: Dict[str, Any],
        targets: Optional[List[str]] = None
    ):
        """
        Publish event to multiple agents.
        
        Args:
            from_agent: Publisher agent ID
            event_type: Event type
            payload: Event payload
            targets: Target agent IDs (None for broadcast)
        """
        # If no targets, broadcast to all registered handlers
        if targets is None:
            targets = list(self.handlers.keys())
        
        # Send to all targets
        for target in targets:
            await self.send_message(
                from_agent=from_agent,
                to_agent=target,
                message_type=MessageType.EVENT,
                payload={
                    'event_type': event_type,
                    'data': payload
                },
                priority=MessagePriority.NORMAL
            )
        
        logger.info(
            "Event published",
            from_agent=from_agent,
            event_type=event_type,
            target_count=len(targets)
        )
    
    async def update_agent_state(
        self,
        agent_id: str,
        state: AgentState,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update agent state."""
        state_info = AgentStateInfo(
            agent_id=agent_id,
            state=state,
            last_heartbeat=datetime.now(),
            metadata=metadata or {}
        )
        
        await self.backend.set_agent_state(agent_id, state_info)
        
        logger.debug(
            "Agent state updated",
            agent_id=agent_id,
            state=state.value
        )
    
    async def get_agent_state(self, agent_id: str) -> Optional[AgentStateInfo]:
        """Get agent state."""
        return await self.backend.get_agent_state(agent_id)
    
    async def get_queue_size(self, agent_id: str) -> int:
        """Get queue size for agent."""
        queue_name = self._get_agent_queue_name(agent_id)
        return await self.backend.get_queue_size(queue_name)
    
    def get_stats(self) -> Dict[str, int]:
        """Get communication statistics."""
        return self.stats.copy()


# ============================================================================
# Helper Functions
# ============================================================================

def create_communication_manager(
    use_redis: bool = False,
    redis_url: str = "redis://localhost:6379/0",
    **kwargs
) -> InterAgentCommunicationManager:
    """
    Create communication manager with appropriate backend.
    
    Args:
        use_redis: Use Redis backend instead of in-memory
        redis_url: Redis connection URL
        **kwargs: Additional arguments for manager
        
    Returns:
        Communication manager instance
    """
    if use_redis:
        backend = RedisBackend(redis_url)
    else:
        backend = InMemoryBackend()
    
    return InterAgentCommunicationManager(backend=backend, **kwargs)


# Global instance
_global_comm_manager: Optional[InterAgentCommunicationManager] = None


def get_global_comm_manager() -> InterAgentCommunicationManager:
    """Get global communication manager instance."""
    global _global_comm_manager
    if _global_comm_manager is None:
        _global_comm_manager = create_communication_manager()
    return _global_comm_manager


def set_global_comm_manager(manager: InterAgentCommunicationManager):
    """Set global communication manager instance."""
    global _global_comm_manager
    _global_comm_manager = manager
