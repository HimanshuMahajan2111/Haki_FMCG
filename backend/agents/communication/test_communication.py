"""Tests for inter-agent communication system."""
import asyncio
import pytest
from datetime import datetime

from .message_broker import (
    Message, MessagePriority,
    InMemoryMessageBroker, RedisMessageBroker
)
from .state_manager import (
    StateType, InMemoryStateManager, RedisStateManager
)
from .retry_handler import (
    RetryHandler, RetryPolicy, RetryStrategy,
    CircuitBreaker, CircuitBreakerConfig, CircuitState
)
from .communication_manager import (
    CommunicationManager, AgentMessage, AgentMessageType
)


# ============================================================================
# Message Broker Tests
# ============================================================================

@pytest.mark.asyncio
async def test_in_memory_broker_basic():
    """Test basic in-memory broker functionality."""
    broker = InMemoryMessageBroker()
    await broker.connect()
    
    # Send and receive message
    msg = Message(
        sender="agent1",
        recipient="agent2",
        message_type="request",
        payload={"test": "data"}
    )
    
    success = await broker.publish(msg)
    assert success
    
    # Consume message
    received_messages = []
    
    async def handler(msg):
        received_messages.append(msg)
    
    await broker.consume("agent2", handler)
    
    # Give time for processing
    await asyncio.sleep(0.1)
    
    assert len(received_messages) > 0
    assert received_messages[0].sender == "agent1"
    
    await broker.disconnect()


@pytest.mark.asyncio
async def test_in_memory_broker_priority():
    """Test priority queuing."""
    broker = InMemoryMessageBroker()
    await broker.connect()
    
    # Send messages with different priorities
    await broker.publish(Message(
        sender="a1", recipient="a2",
        message_type="event",
        priority=MessagePriority.LOW,
        payload={"msg": "low"}
    ))
    
    await broker.publish(Message(
        sender="a1", recipient="a2",
        message_type="event",
        priority=MessagePriority.HIGH,
        payload={"msg": "high"}
    ))
    
    # High priority should come first
    received_messages = []
    
    async def handler(msg):
        received_messages.append(msg)
    
    await broker.consume("a2", handler)
    await asyncio.sleep(0.1)
    
    assert len(received_messages) == 2
    # Priority queue should deliver high priority first
    assert received_messages[0].priority == MessagePriority.HIGH
    
    await broker.disconnect()


@pytest.mark.asyncio
async def test_pubsub_pattern():
    """Test pub/sub pattern."""
    broker = InMemoryMessageBroker()
    await broker.connect()
    
    received_messages = []
    
    async def handler(msg):
        received_messages.append(msg)
    
    # Subscribe to topic
    await broker.subscribe("events.user", handler)
    
    # Publish messages
    msg1 = Message(sender="sys", recipient="*", message_type="event",
                   topic="events.user", payload={"event": "login"})
    msg2 = Message(sender="sys", recipient="*", message_type="event",
                   topic="events.user", payload={"event": "logout"})
    
    await broker.publish(msg1)
    await broker.publish(msg2)
    
    # Give time for async processing
    await asyncio.sleep(0.2)
    
    assert len(received_messages) >= 1
    
    await broker.disconnect()


@pytest.mark.asyncio  
async def test_basic_messaging():
    """Test basic message publishing and consuming."""
    broker = InMemoryMessageBroker()
    await broker.connect()
    
    received_messages = []
    
    async def handler(msg):
        received_messages.append(msg)
    
    # Start consumer
    await broker.consume("agent1", handler)
    
    # Publish message
    msg = Message(
        sender="agent2",
        recipient="agent1",
        message_type="notification",
        payload={"data": "test"}
    )
    await broker.publish(msg)
    
    # Wait for processing
    await asyncio.sleep(0.1)
    
    assert len(received_messages) > 0
    assert received_messages[0].payload["data"] == "test"
    
    await broker.disconnect()


# ============================================================================
# State Manager Tests
# ============================================================================

@pytest.mark.asyncio
async def test_state_manager_basic():
    """Test basic state management."""
    manager = InMemoryStateManager()
    await manager.connect()
    
    # Set and get state
    await manager.set("agent1:status", "busy", StateType.AGENT)
    
    status = await manager.get("agent1:status")
    assert status == "busy"
    
    await manager.disconnect()


@pytest.mark.asyncio
async def test_state_with_ttl():
    """Test state with TTL."""
    manager = InMemoryStateManager()
    await manager.connect()
    
    # Set state with short TTL
    await manager.set("temp:key", "value", StateType.TEMPORARY, ttl=1)
    
    # Should exist immediately
    value = await manager.get("temp:key")
    assert value == "value"
    
    # Wait for expiry
    await asyncio.sleep(1.5)
    
    # Should be gone
    value = await manager.get("temp:key")
    assert value is None
    
    await manager.disconnect()


@pytest.mark.asyncio
async def test_get_all_states():
    """Test getting all keys with pattern."""
    manager = InMemoryStateManager()
    await manager.connect()
    
    await manager.set("agent1:status", "busy", StateType.AGENT)
    await manager.set("agent2:status", "idle", StateType.AGENT)
    await manager.set("other:key", "value", StateType.AGENT)
    
    # Get all agent statuses
    all_statuses = await manager.get_all("agent*:status")
    
    assert len(all_statuses) >= 2
    
    await manager.disconnect()


# ============================================================================
# Retry Handler Tests
# ============================================================================

@pytest.mark.asyncio
async def test_retry_success_first_attempt():
    """Test successful operation on first attempt."""
    handler = RetryHandler()
    
    async def succeed():
        return "success"
    
    result = await handler.execute(succeed)
    assert result == "success"


@pytest.mark.asyncio
async def test_retry_success_after_failures():
    """Test successful operation after failures."""
    handler = RetryHandler(
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay=0.1,
            strategy=RetryStrategy.IMMEDIATE
        )
    )
    
    attempts = [0]
    
    async def fail_twice():
        attempts[0] += 1
        if attempts[0] < 3:
            raise ValueError("Temporary failure")
        return "success"
    
    result = await handler.execute(fail_twice)
    assert result == "success"
    assert attempts[0] == 3


@pytest.mark.asyncio
async def test_retry_all_attempts_fail():
    """Test all retry attempts fail."""
    handler = RetryHandler(
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay=0.1,
            strategy=RetryStrategy.IMMEDIATE
        )
    )
    
    async def always_fail():
        raise ValueError("Permanent failure")
    
    with pytest.raises(ValueError):
        await handler.execute(always_fail)


@pytest.mark.asyncio
async def test_exponential_backoff():
    """Test exponential backoff strategy."""
    policy = RetryPolicy(
        initial_delay=1.0,
        exponential_base=2.0,
        strategy=RetryStrategy.EXPONENTIAL,
        jitter=False
    )
    
    delays = [policy.calculate_delay(i) for i in range(1, 5)]
    
    # Should be: 1, 2, 4, 8
    assert delays[0] == 1.0
    assert delays[1] == 2.0
    assert delays[2] == 4.0
    assert delays[3] == 8.0


def test_circuit_breaker_open_after_failures():
    """Test circuit breaker opens after threshold."""
    breaker = CircuitBreaker(CircuitBreakerConfig(failure_threshold=3))
    
    # Record failures
    for _ in range(3):
        breaker.record_failure()
    
    assert breaker.state == CircuitState.OPEN
    assert breaker.is_open()


def test_circuit_breaker_half_open_after_timeout():
    """Test circuit breaker transitions to half-open."""
    import time
    
    breaker = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=2,
        timeout=0.1
    ))
    
    # Open the circuit
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    
    # Wait for timeout
    time.sleep(0.2)
    
    # Check state (should transition to half-open)
    breaker.is_open()  # This triggers state check
    assert breaker.state == CircuitState.HALF_OPEN


def test_circuit_breaker_close_after_successes():
    """Test circuit breaker closes after successes."""
    import time
    
    breaker = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=2,
        success_threshold=2,
        timeout=0.1
    ))
    
    # Open the circuit
    breaker.record_failure()
    breaker.record_failure()
    
    # Wait and transition to half-open
    time.sleep(0.2)
    breaker.is_open()
    
    # Record successes
    breaker.record_success()
    breaker.record_success()
    
    assert breaker.state == CircuitState.CLOSED


# ============================================================================
# Communication Manager Tests
# ============================================================================

@pytest.mark.asyncio
async def test_communication_manager_registration():
    """Test agent registration."""
    manager = CommunicationManager()
    await manager.connect()
    
    await manager.register_agent(
        "agent1",
        "sales",
        capabilities=["pricing", "negotiation"]
    )
    
    info = await manager.get_agent_info("agent1")
    assert info is not None
    assert info['agent_type'] == "sales"
    assert "pricing" in info['capabilities']
    
    await manager.disconnect()


@pytest.mark.asyncio
async def test_communication_manager_messaging():
    """Test message sending."""
    manager = CommunicationManager()
    await manager.connect()
    
    await manager.register_agent("agent1", "type1")
    await manager.register_agent("agent2", "type2")
    
    received_messages = []
    
    async def handler(msg):
        received_messages.append(msg)
    
    await manager.register_handler("agent2", "notification", handler)
    
    # Send message
    message = AgentMessage(
        sender="agent1",
        recipient="agent2",
        message_type=AgentMessageType.NOTIFICATION,
        payload={"info": "test"}
    )
    
    success = await manager.send_message(message)
    assert success
    
    # Give time for processing
    await asyncio.sleep(0.2)
    
    assert len(received_messages) > 0
    
    await manager.disconnect()


@pytest.mark.asyncio
async def test_communication_manager_request_response():
    """Test request-response pattern."""
    manager = CommunicationManager()
    await manager.connect()
    
    await manager.register_agent("requester", "type1")
    await manager.register_agent("responder", "type2")
    
    # Register handler to respond
    async def request_handler(msg):
        await manager.send_response(msg, {"result": "processed"})
    
    await manager.register_handler("responder", "request", request_handler)
    
    # Send request
    response = await manager.send_request(
        sender="requester",
        recipient="responder",
        payload={"query": "test"},
        timeout=5.0
    )
    
    assert response is not None
    assert response["result"] == "processed"
    
    await manager.disconnect()


@pytest.mark.asyncio
async def test_communication_manager_broadcast():
    """Test broadcast messaging."""
    manager = CommunicationManager()
    await manager.connect()
    
    await manager.register_agent("sender", "controller")
    await manager.register_agent("agent1", "worker")
    await manager.register_agent("agent2", "worker")
    
    # Broadcast to all workers
    await manager.broadcast(
        sender="sender",
        payload={"command": "start"},
        agent_type="worker"
    )
    
    # Give time for processing
    await asyncio.sleep(0.2)
    
    # Check messages were sent
    queue_size_1 = await manager.get_queue_size("agent1")
    queue_size_2 = await manager.get_queue_size("agent2")
    
    assert queue_size_1 > 0 or queue_size_2 > 0
    
    await manager.disconnect()


@pytest.mark.asyncio
async def test_communication_manager_state():
    """Test agent state management."""
    manager = CommunicationManager()
    await manager.connect()
    
    await manager.register_agent("agent1", "type1")
    
    # Set state
    await manager.set_agent_state("agent1", "status", "processing")
    
    # Get state
    status = await manager.get_agent_state("agent1", "status")
    assert status == "processing"
    
    await manager.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
