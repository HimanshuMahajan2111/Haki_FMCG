"""Message Broker for inter-agent communication."""
import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import structlog

logger = structlog.get_logger()


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Message:
    """Message structure for inter-agent communication."""
    message_id: str
    sender: str
    recipient: str
    message_type: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    timestamp: float = None
    expiry: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary (serialization)."""
        data = asdict(self)
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary (deserialization)."""
        if isinstance(data['priority'], int):
            data['priority'] = MessagePriority(data['priority'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize message to JSON string."""
        import json
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Deserialize message from JSON string."""
        import json
        return cls.from_dict(json.loads(json_str))
    
    def is_expired(self) -> bool:
        """Check if message has expired."""
        if self.expiry is None:
            return False
        return time.time() > self.expiry


class MessageBroker(ABC):
    """Abstract base class for message brokers."""
    
    @abstractmethod
    async def publish(self, message: Message) -> bool:
        """Publish a message."""
        pass
    
    @abstractmethod
    async def subscribe(self, agent_id: str, callback: Callable) -> None:
        """Subscribe to messages for an agent."""
        pass
    
    @abstractmethod
    async def get_message(self, agent_id: str, timeout: float = None) -> Optional[Message]:
        """Get next message for an agent."""
        pass
    
    @abstractmethod
    async def acknowledge(self, message_id: str) -> bool:
        """Acknowledge message receipt."""
        pass
    
    @abstractmethod
    async def get_queue_size(self, agent_id: str) -> int:
        """Get number of pending messages."""
        pass


class InMemoryMessageBroker(MessageBroker):
    """In-memory message broker for testing and development."""
    
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.pending_acks: Dict[str, Message] = {}
        self.dead_letter: List[Message] = []
        self._lock = asyncio.Lock()
        logger.info("Initialized InMemoryMessageBroker")
    
    def _get_queue(self, agent_id: str) -> asyncio.Queue:
        """Get or create queue for agent."""
        if agent_id not in self.queues:
            self.queues[agent_id] = asyncio.Queue()
        return self.queues[agent_id]
    
    async def publish(self, message: Message) -> bool:
        """Publish message to recipient's queue."""
        try:
            if message.is_expired():
                logger.warning("Message expired", message_id=message.message_id)
                self.dead_letter.append(message)
                return False
            
            queue = self._get_queue(message.recipient)
            await queue.put(message)
            
            # Notify subscribers
            if message.recipient in self.subscribers:
                for callback in self.subscribers[message.recipient]:
                    try:
                        await callback(message)
                    except Exception as e:
                        logger.error("Subscriber callback failed", 
                                   error=str(e), agent=message.recipient)
            
            logger.debug("Published message",
                        message_id=message.message_id,
                        sender=message.sender,
                        recipient=message.recipient)
            return True
            
        except Exception as e:
            logger.error("Failed to publish message", error=str(e))
            return False
    
    async def subscribe(self, agent_id: str, callback: Callable) -> None:
        """Subscribe to messages."""
        async with self._lock:
            if agent_id not in self.subscribers:
                self.subscribers[agent_id] = []
            self.subscribers[agent_id].append(callback)
        logger.info("Agent subscribed", agent_id=agent_id)
    
    async def get_message(self, agent_id: str, timeout: float = None) -> Optional[Message]:
        """Get next message from queue."""
        try:
            queue = self._get_queue(agent_id)
            if timeout:
                message = await asyncio.wait_for(queue.get(), timeout=timeout)
            else:
                message = await queue.get()
            
            # Store for acknowledgment
            self.pending_acks[message.message_id] = message
            
            return message
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error("Failed to get message", error=str(e), agent=agent_id)
            return None
    
    async def acknowledge(self, message_id: str) -> bool:
        """Acknowledge message processing."""
        if message_id in self.pending_acks:
            del self.pending_acks[message_id]
            logger.debug("Message acknowledged", message_id=message_id)
            return True
        return False
    
    async def get_queue_size(self, agent_id: str) -> int:
        """Get queue size."""
        queue = self._get_queue(agent_id)
        return queue.qsize()


class RedisMessageBroker(MessageBroker):
    """Redis-based message broker for production use."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis = None
        self.pubsub = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self._subscriber_tasks: Dict[str, asyncio.Task] = {}
        logger.info("Initialized RedisMessageBroker", redis_url=redis_url)
    
    async def connect(self):
        """Connect to Redis."""
        try:
            import redis.asyncio as aioredis
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Connected to Redis")
        except ImportError:
            logger.error("redis package not installed. Run: pip install redis")
            raise
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
    
    def _queue_key(self, agent_id: str) -> str:
        """Get Redis key for agent queue."""
        return f"agent:queue:{agent_id}"
    
    def _pending_key(self, agent_id: str) -> str:
        """Get Redis key for pending messages."""
        return f"agent:pending:{agent_id}"
    
    async def publish(self, message: Message) -> bool:
        """Publish message to Redis queue."""
        try:
            if not self.redis:
                await self.connect()
            
            if message.is_expired():
                logger.warning("Message expired", message_id=message.message_id)
                await self.redis.lpush("dead_letter", json.dumps(message.to_dict()))
                return False
            
            # Add to recipient's queue with priority
            queue_key = self._queue_key(message.recipient)
            message_json = json.dumps(message.to_dict())
            
            # Use sorted set for priority queue
            score = message.priority.value * 1000000 - message.timestamp
            await self.redis.zadd(queue_key, {message_json: score})
            
            # Publish to pub/sub for real-time notifications
            await self.redis.publish(f"agent:channel:{message.recipient}", message_json)
            
            logger.debug("Published message to Redis",
                        message_id=message.message_id,
                        recipient=message.recipient)
            return True
            
        except Exception as e:
            logger.error("Failed to publish to Redis", error=str(e))
            return False
    
    async def subscribe(self, agent_id: str, callback: Callable) -> None:
        """Subscribe to messages via Redis pub/sub."""
        try:
            if not self.redis:
                await self.connect()
            
            if agent_id not in self.subscribers:
                self.subscribers[agent_id] = []
            self.subscribers[agent_id].append(callback)
            
            # Start subscriber task if not already running
            if agent_id not in self._subscriber_tasks:
                task = asyncio.create_task(self._subscriber_loop(agent_id))
                self._subscriber_tasks[agent_id] = task
            
            logger.info("Agent subscribed to Redis", agent_id=agent_id)
            
        except Exception as e:
            logger.error("Failed to subscribe", error=str(e), agent=agent_id)
    
    async def _subscriber_loop(self, agent_id: str):
        """Background loop for Redis pub/sub."""
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(f"agent:channel:{agent_id}")
            
            async for msg in pubsub.listen():
                if msg['type'] == 'message':
                    try:
                        message_data = json.loads(msg['data'])
                        message = Message.from_dict(message_data)
                        
                        # Notify all subscribers
                        for callback in self.subscribers.get(agent_id, []):
                            try:
                                await callback(message)
                            except Exception as e:
                                logger.error("Subscriber callback failed",
                                           error=str(e), agent=agent_id)
                    except Exception as e:
                        logger.error("Failed to process pub/sub message", error=str(e))
        except Exception as e:
            logger.error("Subscriber loop error", error=str(e), agent=agent_id)
    
    async def get_message(self, agent_id: str, timeout: float = None) -> Optional[Message]:
        """Get highest priority message from Redis queue."""
        try:
            if not self.redis:
                await self.connect()
            
            queue_key = self._queue_key(agent_id)
            
            # Get highest priority message (highest score)
            if timeout:
                # Blocking pop with timeout
                result = await self.redis.bzpopmax(queue_key, timeout=timeout)
                if not result:
                    return None
                _, message_json, _ = result
            else:
                # Non-blocking pop
                results = await self.redis.zpopmax(queue_key, count=1)
                if not results:
                    return None
                message_json, _ = results[0]
            
            message_data = json.loads(message_json)
            message = Message.from_dict(message_data)
            
            # Move to pending list
            pending_key = self._pending_key(agent_id)
            await self.redis.hset(pending_key, message.message_id, message_json)
            
            return message
            
        except Exception as e:
            logger.error("Failed to get message from Redis", error=str(e))
            return None
    
    async def acknowledge(self, message_id: str) -> bool:
        """Acknowledge message processing."""
        try:
            if not self.redis:
                await self.connect()
            
            # Remove from all pending lists
            for key in await self.redis.keys("agent:pending:*"):
                await self.redis.hdel(key, message_id)
            
            logger.debug("Message acknowledged in Redis", message_id=message_id)
            return True
            
        except Exception as e:
            logger.error("Failed to acknowledge in Redis", error=str(e))
            return False
    
    async def get_queue_size(self, agent_id: str) -> int:
        """Get queue size from Redis."""
        try:
            if not self.redis:
                await self.connect()
            
            queue_key = self._queue_key(agent_id)
            return await self.redis.zcard(queue_key)
            
        except Exception as e:
            logger.error("Failed to get queue size", error=str(e))
            return 0
