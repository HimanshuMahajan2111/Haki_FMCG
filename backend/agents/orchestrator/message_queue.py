"""
Message Queue System for Agent Communication
Implements a robust message passing system between agents.
"""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from queue import Queue, PriorityQueue, Empty
from threading import Lock, Event
import uuid
import structlog

logger = structlog.get_logger()


class MessagePriority(Enum):
    """Message priority levels."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class MessageStatus(Enum):
    """Message delivery status."""
    PENDING = "pending"
    DELIVERED = "delivered"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class Message:
    """Message object for agent communication."""
    message_id: str
    from_agent: str
    to_agent: str
    message_type: str
    payload: Dict[str, Any]
    priority: MessagePriority
    created_at: str
    expires_at: Optional[str] = None
    status: MessageStatus = MessageStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    correlation_id: Optional[str] = None  # For request-response tracking
    reply_to: Optional[str] = None  # For response routing
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        return data


@dataclass
class MessageQueueStats:
    """Statistics for message queue."""
    total_messages_sent: int = 0
    total_messages_delivered: int = 0
    total_messages_failed: int = 0
    total_messages_timeout: int = 0
    pending_messages: int = 0
    average_delivery_time: float = 0.0


class AgentMessageQueue:
    """
    Message Queue System for Agent Communication
    
    Features:
    - Priority-based message delivery
    - Message acknowledgment
    - Retry mechanism
    - Dead letter queue
    - Message expiration
    - Pub/Sub pattern support
    - Request/Response correlation
    """
    
    def __init__(
        self,
        max_queue_size: int = 1000,
        enable_persistence: bool = False
    ):
        """Initialize message queue.
        
        Args:
            max_queue_size: Maximum queue size
            enable_persistence: Enable message persistence
        """
        self.logger = logger.bind(component="MessageQueue")
        
        # Message queues per agent
        self._agent_queues: Dict[str, PriorityQueue] = {}
        self._agent_locks: Dict[str, Lock] = {}
        
        # Message storage
        self._messages: Dict[str, Message] = {}
        self._message_lock = Lock()
        
        # Dead letter queue
        self._dead_letter_queue: List[Message] = []
        
        # Subscribers for pub/sub
        self._subscribers: Dict[str, List[str]] = {}  # topic -> [agent_ids]
        
        # Statistics
        self.stats = MessageQueueStats()
        
        # Configuration
        self.max_queue_size = max_queue_size
        self.enable_persistence = enable_persistence
        
        self.logger.info("Message Queue initialized")
    
    def register_agent_queue(self, agent_id: str):
        """Register a message queue for an agent.
        
        Args:
            agent_id: Agent ID
        """
        if agent_id not in self._agent_queues:
            self._agent_queues[agent_id] = PriorityQueue(maxsize=self.max_queue_size)
            self._agent_locks[agent_id] = Lock()
            self.logger.info("Agent queue registered", agent_id=agent_id)
    
    def send_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: Optional[str] = None,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Send a message to an agent.
        
        Args:
            from_agent: Source agent ID
            to_agent: Destination agent ID
            message_type: Type of message
            payload: Message payload
            priority: Message priority
            correlation_id: Optional correlation ID
            reply_to: Optional reply-to address
            metadata: Optional metadata
            
        Returns:
            Message ID
        """
        # Ensure destination queue exists
        if to_agent not in self._agent_queues:
            self.register_agent_queue(to_agent)
        
        # Create message
        message_id = str(uuid.uuid4())
        message = Message(
            message_id=message_id,
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload,
            priority=priority,
            created_at=datetime.now().isoformat(),
            correlation_id=correlation_id,
            reply_to=reply_to,
            metadata=metadata or {}
        )
        
        # Store message
        with self._message_lock:
            self._messages[message_id] = message
        
        # Enqueue message (priority, timestamp, message)
        try:
            self._agent_queues[to_agent].put(
                (priority.value, datetime.now().timestamp(), message),
                block=False
            )
            
            self.stats.total_messages_sent += 1
            self.stats.pending_messages += 1
            
            self.logger.info(
                "Message sent",
                message_id=message_id,
                from_agent=from_agent,
                to_agent=to_agent,
                message_type=message_type,
                priority=priority.value
            )
            
            return message_id
            
        except Exception as e:
            self.logger.error(
                "Failed to send message",
                message_id=message_id,
                error=str(e)
            )
            message.status = MessageStatus.FAILED
            self.stats.total_messages_failed += 1
            raise
    
    def receive_message(
        self,
        agent_id: str,
        timeout: float = 1.0
    ) -> Optional[Message]:
        """Receive a message for an agent.
        
        Args:
            agent_id: Agent ID
            timeout: Timeout in seconds
            
        Returns:
            Message or None
        """
        if agent_id not in self._agent_queues:
            return None
        
        try:
            # Get message from queue
            _, _, message = self._agent_queues[agent_id].get(timeout=timeout)
            
            # Update status
            message.status = MessageStatus.DELIVERED
            self.stats.total_messages_delivered += 1
            self.stats.pending_messages -= 1
            
            self.logger.info(
                "Message received",
                message_id=message.message_id,
                agent_id=agent_id,
                message_type=message.message_type
            )
            
            return message
            
        except Empty:
            return None
        except Exception as e:
            self.logger.error(
                "Failed to receive message",
                agent_id=agent_id,
                error=str(e)
            )
            return None
    
    def acknowledge_message(self, message_id: str, success: bool = True):
        """Acknowledge message processing.
        
        Args:
            message_id: Message ID
            success: Whether processing was successful
        """
        with self._message_lock:
            if message_id not in self._messages:
                return
            
            message = self._messages[message_id]
            
            if success:
                message.status = MessageStatus.COMPLETED
                self.logger.info(
                    "Message acknowledged",
                    message_id=message_id
                )
            else:
                # Retry logic
                message.retry_count += 1
                
                if message.retry_count < message.max_retries:
                    # Requeue message
                    message.status = MessageStatus.PENDING
                    try:
                        self._agent_queues[message.to_agent].put(
                            (message.priority.value, datetime.now().timestamp(), message),
                            block=False
                        )
                        self.logger.warning(
                            "Message retry",
                            message_id=message_id,
                            retry_count=message.retry_count
                        )
                    except:
                        message.status = MessageStatus.FAILED
                        self._dead_letter_queue.append(message)
                        self.stats.total_messages_failed += 1
                else:
                    # Max retries exceeded - move to dead letter queue
                    message.status = MessageStatus.FAILED
                    self._dead_letter_queue.append(message)
                    self.stats.total_messages_failed += 1
                    
                    self.logger.error(
                        "Message failed after max retries",
                        message_id=message_id,
                        retry_count=message.retry_count
                    )
    
    def send_request(
        self,
        from_agent: str,
        to_agent: str,
        request_type: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> str:
        """Send a request and get correlation ID for tracking response.
        
        Args:
            from_agent: Source agent ID
            to_agent: Destination agent ID
            request_type: Type of request
            payload: Request payload
            priority: Message priority
            
        Returns:
            Correlation ID
        """
        correlation_id = str(uuid.uuid4())
        
        self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=request_type,
            payload=payload,
            priority=priority,
            correlation_id=correlation_id,
            reply_to=from_agent
        )
        
        return correlation_id
    
    def send_response(
        self,
        from_agent: str,
        to_agent: str,
        correlation_id: str,
        response_type: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> str:
        """Send a response to a previous request.
        
        Args:
            from_agent: Source agent ID
            to_agent: Destination agent ID
            correlation_id: Correlation ID from request
            response_type: Type of response
            payload: Response payload
            priority: Message priority
            
        Returns:
            Message ID
        """
        return self.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=response_type,
            payload=payload,
            priority=priority,
            correlation_id=correlation_id
        )
    
    def subscribe(self, agent_id: str, topic: str):
        """Subscribe agent to a topic.
        
        Args:
            agent_id: Agent ID
            topic: Topic to subscribe to
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        
        if agent_id not in self._subscribers[topic]:
            self._subscribers[topic].append(agent_id)
            
            self.logger.info(
                "Agent subscribed to topic",
                agent_id=agent_id,
                topic=topic
            )
    
    def unsubscribe(self, agent_id: str, topic: str):
        """Unsubscribe agent from a topic.
        
        Args:
            agent_id: Agent ID
            topic: Topic to unsubscribe from
        """
        if topic in self._subscribers and agent_id in self._subscribers[topic]:
            self._subscribers[topic].remove(agent_id)
            
            self.logger.info(
                "Agent unsubscribed from topic",
                agent_id=agent_id,
                topic=topic
            )
    
    def publish(
        self,
        from_agent: str,
        topic: str,
        message_type: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> List[str]:
        """Publish message to all subscribers of a topic.
        
        Args:
            from_agent: Source agent ID
            topic: Topic to publish to
            message_type: Type of message
            payload: Message payload
            priority: Message priority
            
        Returns:
            List of message IDs
        """
        message_ids = []
        
        subscribers = self._subscribers.get(topic, [])
        
        for subscriber_id in subscribers:
            message_id = self.send_message(
                from_agent=from_agent,
                to_agent=subscriber_id,
                message_type=message_type,
                payload=payload,
                priority=priority,
                metadata={'topic': topic}
            )
            message_ids.append(message_id)
        
        self.logger.info(
            "Message published",
            from_agent=from_agent,
            topic=topic,
            subscribers_count=len(subscribers)
        )
        
        return message_ids
    
    def get_queue_size(self, agent_id: str) -> int:
        """Get queue size for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Queue size
        """
        if agent_id not in self._agent_queues:
            return 0
        return self._agent_queues[agent_id].qsize()
    
    def get_dead_letter_queue(self) -> List[Message]:
        """Get messages in dead letter queue.
        
        Returns:
            List of failed messages
        """
        return self._dead_letter_queue.copy()
    
    def clear_dead_letter_queue(self):
        """Clear dead letter queue."""
        self._dead_letter_queue.clear()
        self.logger.info("Dead letter queue cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'total_messages_sent': self.stats.total_messages_sent,
            'total_messages_delivered': self.stats.total_messages_delivered,
            'total_messages_failed': self.stats.total_messages_failed,
            'total_messages_timeout': self.stats.total_messages_timeout,
            'pending_messages': self.stats.pending_messages,
            'dead_letter_queue_size': len(self._dead_letter_queue),
            'registered_agents': len(self._agent_queues),
            'active_topics': len(self._subscribers)
        }


# Global message queue instance
_global_message_queue = None


def get_global_message_queue() -> AgentMessageQueue:
    """Get global message queue instance.
    
    Returns:
        Global AgentMessageQueue instance
    """
    global _global_message_queue
    if _global_message_queue is None:
        _global_message_queue = AgentMessageQueue()
    return _global_message_queue
