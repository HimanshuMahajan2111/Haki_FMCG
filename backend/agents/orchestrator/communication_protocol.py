"""
Agent Communication Protocol
Standardized protocol for agent-to-agent communication.
"""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import structlog

from agents.orchestrator.message_queue import (
    AgentMessageQueue,
    Message,
    MessagePriority,
    get_global_message_queue
)

logger = structlog.get_logger()


class ProtocolMessageType(Enum):
    """Standard protocol message types."""
    # Request types
    REQUEST_ANALYSIS = "request_analysis"
    REQUEST_PROCESSING = "request_processing"
    REQUEST_DATA = "request_data"
    REQUEST_STATUS = "request_status"
    
    # Response types
    RESPONSE_SUCCESS = "response_success"
    RESPONSE_ERROR = "response_error"
    RESPONSE_DATA = "response_data"
    RESPONSE_STATUS = "response_status"
    
    # Command types
    COMMAND_START = "command_start"
    COMMAND_STOP = "command_stop"
    COMMAND_PAUSE = "command_pause"
    COMMAND_RESUME = "command_resume"
    
    # Event types
    EVENT_STARTED = "event_started"
    EVENT_COMPLETED = "event_completed"
    EVENT_FAILED = "event_failed"
    EVENT_PROGRESS = "event_progress"
    
    # Coordination types
    COORD_HANDOFF = "coord_handoff"
    COORD_SYNC = "coord_sync"
    COORD_BROADCAST = "coord_broadcast"


@dataclass
class ProtocolMessage:
    """Standardized protocol message."""
    message_type: ProtocolMessageType
    sender: str
    receiver: str
    payload: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentCommunicationProtocol:
    """
    Agent Communication Protocol
    
    Features:
    - Standardized message formats
    - Request/Response patterns
    - Event publishing
    - Context propagation
    - Message routing
    - Protocol validation
    """
    
    def __init__(self, message_queue: Optional[AgentMessageQueue] = None):
        """Initialize communication protocol.
        
        Args:
            message_queue: Message queue instance (uses global if None)
        """
        self.logger = logger.bind(component="CommunicationProtocol")
        self.message_queue = message_queue or get_global_message_queue()
        
        # Message handlers
        self._handlers: Dict[str, Dict[ProtocolMessageType, Callable]] = {}
        
        # Pending requests (for request/response tracking)
        self._pending_requests: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("Communication Protocol initialized")
    
    def register_handler(
        self,
        agent_id: str,
        message_type: ProtocolMessageType,
        handler: Callable
    ):
        """Register message handler for an agent.
        
        Args:
            agent_id: Agent ID
            message_type: Message type to handle
            handler: Handler function
        """
        if agent_id not in self._handlers:
            self._handlers[agent_id] = {}
        
        self._handlers[agent_id][message_type] = handler
        
        self.logger.info(
            "Handler registered",
            agent_id=agent_id,
            message_type=message_type.value
        )
    
    def send_request(
        self,
        from_agent: str,
        to_agent: str,
        request_type: ProtocolMessageType,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> str:
        """Send a request to another agent.
        
        Args:
            from_agent: Source agent ID
            to_agent: Destination agent ID
            request_type: Type of request
            payload: Request payload
            context: Optional context
            priority: Message priority
            
        Returns:
            Correlation ID for tracking response
        """
        protocol_message = ProtocolMessage(
            message_type=request_type,
            sender=from_agent,
            receiver=to_agent,
            payload=payload,
            context=context or {}
        )
        
        correlation_id = self.message_queue.send_request(
            from_agent=from_agent,
            to_agent=to_agent,
            request_type=request_type.value,
            payload={
                'protocol_message': {
                    'message_type': protocol_message.message_type.value,
                    'sender': protocol_message.sender,
                    'receiver': protocol_message.receiver,
                    'payload': protocol_message.payload,
                    'context': protocol_message.context,
                    'timestamp': protocol_message.timestamp
                }
            },
            priority=priority
        )
        
        # Track pending request
        self._pending_requests[correlation_id] = {
            'from_agent': from_agent,
            'to_agent': to_agent,
            'request_type': request_type.value,
            'sent_at': datetime.now().isoformat()
        }
        
        self.logger.info(
            "Request sent",
            from_agent=from_agent,
            to_agent=to_agent,
            request_type=request_type.value,
            correlation_id=correlation_id
        )
        
        return correlation_id
    
    def send_response(
        self,
        from_agent: str,
        to_agent: str,
        correlation_id: str,
        response_type: ProtocolMessageType,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> str:
        """Send a response to a request.
        
        Args:
            from_agent: Source agent ID
            to_agent: Destination agent ID
            correlation_id: Correlation ID from request
            response_type: Type of response
            payload: Response payload
            context: Optional context
            priority: Message priority
            
        Returns:
            Message ID
        """
        protocol_message = ProtocolMessage(
            message_type=response_type,
            sender=from_agent,
            receiver=to_agent,
            payload=payload,
            context=context or {}
        )
        
        message_id = self.message_queue.send_response(
            from_agent=from_agent,
            to_agent=to_agent,
            correlation_id=correlation_id,
            response_type=response_type.value,
            payload={
                'protocol_message': {
                    'message_type': protocol_message.message_type.value,
                    'sender': protocol_message.sender,
                    'receiver': protocol_message.receiver,
                    'payload': protocol_message.payload,
                    'context': protocol_message.context,
                    'timestamp': protocol_message.timestamp
                }
            },
            priority=priority
        )
        
        # Clear pending request if exists
        if correlation_id in self._pending_requests:
            del self._pending_requests[correlation_id]
        
        self.logger.info(
            "Response sent",
            from_agent=from_agent,
            to_agent=to_agent,
            response_type=response_type.value,
            correlation_id=correlation_id
        )
        
        return message_id
    
    def send_event(
        self,
        from_agent: str,
        event_type: ProtocolMessageType,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        topic: Optional[str] = None
    ) -> List[str]:
        """Publish an event.
        
        Args:
            from_agent: Source agent ID
            event_type: Type of event
            payload: Event payload
            context: Optional context
            topic: Optional topic (publishes to all if None)
            
        Returns:
            List of message IDs
        """
        protocol_message = ProtocolMessage(
            message_type=event_type,
            sender=from_agent,
            receiver="*",  # Broadcast
            payload=payload,
            context=context or {}
        )
        
        if topic:
            # Publish to specific topic
            message_ids = self.message_queue.publish(
                from_agent=from_agent,
                topic=topic,
                message_type=event_type.value,
                payload={
                    'protocol_message': {
                        'message_type': protocol_message.message_type.value,
                        'sender': protocol_message.sender,
                        'receiver': protocol_message.receiver,
                        'payload': protocol_message.payload,
                        'context': protocol_message.context,
                        'timestamp': protocol_message.timestamp
                    }
                }
            )
        else:
            # Broadcast to all (would need implementation)
            message_ids = []
        
        self.logger.info(
            "Event published",
            from_agent=from_agent,
            event_type=event_type.value,
            topic=topic
        )
        
        return message_ids
    
    def send_command(
        self,
        from_agent: str,
        to_agent: str,
        command_type: ProtocolMessageType,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.HIGH
    ) -> str:
        """Send a command to another agent.
        
        Args:
            from_agent: Source agent ID
            to_agent: Destination agent ID
            command_type: Type of command
            payload: Command payload
            context: Optional context
            priority: Message priority
            
        Returns:
            Message ID
        """
        protocol_message = ProtocolMessage(
            message_type=command_type,
            sender=from_agent,
            receiver=to_agent,
            payload=payload,
            context=context or {}
        )
        
        message_id = self.message_queue.send_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=command_type.value,
            payload={
                'protocol_message': {
                    'message_type': protocol_message.message_type.value,
                    'sender': protocol_message.sender,
                    'receiver': protocol_message.receiver,
                    'payload': protocol_message.payload,
                    'context': protocol_message.context,
                    'timestamp': protocol_message.timestamp
                }
            },
            priority=priority
        )
        
        self.logger.info(
            "Command sent",
            from_agent=from_agent,
            to_agent=to_agent,
            command_type=command_type.value
        )
        
        return message_id
    
    def handoff(
        self,
        from_agent: str,
        to_agent: str,
        workflow_state: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Handoff workflow to another agent.
        
        Args:
            from_agent: Source agent ID
            to_agent: Destination agent ID
            workflow_state: Current workflow state
            context: Workflow context
            
        Returns:
            Correlation ID
        """
        return self.send_request(
            from_agent=from_agent,
            to_agent=to_agent,
            request_type=ProtocolMessageType.COORD_HANDOFF,
            payload=workflow_state,
            context=context,
            priority=MessagePriority.HIGH
        )
    
    def process_message(
        self,
        agent_id: str,
        message: Message
    ) -> Optional[Any]:
        """Process incoming message for an agent.
        
        Args:
            agent_id: Agent ID
            message: Incoming message
            
        Returns:
            Handler result or None
        """
        try:
            # Extract protocol message
            protocol_data = message.payload.get('protocol_message', {})
            message_type_str = protocol_data.get('message_type')
            
            if not message_type_str:
                self.logger.warning(
                    "Invalid protocol message",
                    agent_id=agent_id,
                    message_id=message.message_id
                )
                return None
            
            message_type = ProtocolMessageType(message_type_str)
            
            # Find handler
            if agent_id in self._handlers and message_type in self._handlers[agent_id]:
                handler = self._handlers[agent_id][message_type]
                
                # Call handler
                result = handler(protocol_data)
                
                self.logger.info(
                    "Message processed",
                    agent_id=agent_id,
                    message_type=message_type.value,
                    message_id=message.message_id
                )
                
                return result
            else:
                self.logger.warning(
                    "No handler found",
                    agent_id=agent_id,
                    message_type=message_type.value
                )
                return None
                
        except Exception as e:
            self.logger.error(
                "Message processing failed",
                agent_id=agent_id,
                message_id=message.message_id,
                error=str(e)
            )
            return None
    
    def get_pending_requests(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pending requests.
        
        Args:
            agent_id: Optional agent ID filter
            
        Returns:
            List of pending requests
        """
        if agent_id:
            return [
                {'correlation_id': corr_id, **req_data}
                for corr_id, req_data in self._pending_requests.items()
                if req_data['from_agent'] == agent_id
            ]
        else:
            return [
                {'correlation_id': corr_id, **req_data}
                for corr_id, req_data in self._pending_requests.items()
            ]


# Global protocol instance
_global_protocol = None


def get_global_protocol() -> AgentCommunicationProtocol:
    """Get global communication protocol instance.
    
    Returns:
        Global AgentCommunicationProtocol instance
    """
    global _global_protocol
    if _global_protocol is None:
        _global_protocol = AgentCommunicationProtocol()
    return _global_protocol
