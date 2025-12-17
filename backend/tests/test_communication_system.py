"""Comprehensive tests for inter-agent communication system."""
import asyncio
import pytest
import time
import uuid

from agents.communication.message_broker import (
    Message, MessagePriority,
    InMemoryMessageBroker
)
from agents.communication.state_manager import (
    StateType, InMemoryStateManager
)
from agents.communication.retry_handler import (
    RetryHandler, RetryPolicy, RetryStrategy,
    CircuitBreaker, CircuitBreakerConfig, CircuitState
)


# ============================================================================
# Message Broker Tests
# ============================================================================

@pytest.mark.asyncio
async def test_in_memory_broker_basic():
    """Test basic in-memory broker functionality."""
    broker = InMemoryMessageBroker()
    
    # Create and publish message
    msg = Message(
        message_id=str(uuid.uuid4()),
        sender="agent1",
        recipient="agent2",
        message_type="request",
        payload={"test": "data"}
    )
    
    success = await broker.publish(msg)
    assert success
    
    # Get message
    received = await broker.get_message("agent2", timeout=1.0)
    assert received is not None
    assert received.sender == "agent1"
    assert received.payload["test"] == "data"


@pytest.mark.asyncio
async def test_subscription():
    """Test subscription pattern."""
    broker = InMemoryMessageBroker()
    
    received_messages = []
    
    async def handler(msg):
        received_messages.append(msg)
    
    # Subscribe
    await broker.subscribe("agent1", handler)
    
    # Publish message
    msg = Message(
        message_id=str(uuid.uuid4()),
        sender="agent2",
        recipient="agent1",
        message_type="notification",
        payload={"data": "test"}
    )
    await broker.publish(msg)
    
    # Wait for async processing
    await asyncio.sleep(0.2)
    
    # Check message was delivered
    assert len(received_messages) > 0
    assert received_messages[0].payload["data"] == "test"


@pytest.mark.asyncio
async def test_queue_size():
    """Test getting queue size."""
    broker = InMemoryMessageBroker()
    
    # Initial size should be 0
    size = await broker.get_queue_size("agent1")
    assert size == 0
    
    # Publish messages
    await broker.publish(Message(
        message_id=str(uuid.uuid4()),
        sender="a2",
        recipient="agent1",
        message_type="notification",
        payload={}
    ))
    await broker.publish(Message(
        message_id=str(uuid.uuid4()),
        sender="a3",
        recipient="agent1",
        message_type="notification",
        payload={}
    ))
    
    # Size should be 2
    size = await broker.get_queue_size("agent1")
    assert size == 2


# ============================================================================
# State Manager Tests
# ============================================================================

@pytest.mark.asyncio
async def test_state_manager_basic():
    """Test basic state management."""
    manager = InMemoryStateManager()
    
    # Set and get state
    await manager.set("agent1:status", "busy", StateType.AGENT)
    
    status = await manager.get("agent1:status")
    assert status == "busy"


@pytest.mark.asyncio
async def test_state_with_ttl():
    """Test state with TTL."""
    manager = InMemoryStateManager()
    
    # Set state with short TTL
    await manager.set("temp:key", "value", StateType.CACHE, ttl=1)
    
    # Should exist immediately
    value = await manager.get("temp:key")
    assert value == "value"
    
    # Wait for expiry
    await asyncio.sleep(1.2)
    
    # Should be gone
    value = await manager.get("temp:key")
    assert value is None


@pytest.mark.asyncio
async def test_state_delete():
    """Test deleting state."""
    manager = InMemoryStateManager()
    
    # Set state
    await manager.set("test:key", "value", StateType.AGENT)
    
    # Delete state
    success = await manager.delete("test:key")
    assert success
    
    # Should be gone
    value = await manager.get("test:key")
    assert value is None


@pytest.mark.asyncio
async def test_state_exists():
    """Test checking if state exists."""
    manager = InMemoryStateManager()
    
    # Should not exist
    exists = await manager.exists("test:key")
    assert not exists
    
    # Create state
    await manager.set("test:key", "value", StateType.AGENT)
    
    # Should exist
    exists = await manager.exists("test:key")
    assert exists


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
            initial_delay=0.05,
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
            max_attempts=2,
            initial_delay=0.05,
            strategy=RetryStrategy.IMMEDIATE
        )
    )
    
    async def always_fail():
        raise ValueError("Permanent failure")
    
    with pytest.raises(ValueError):
        await handler.execute(always_fail)


def test_exponential_backoff():
    """Test exponential backoff strategy."""
    policy = RetryPolicy(
        initial_delay=1.0,
        exponential_base=2.0,
        strategy=RetryStrategy.EXPONENTIAL,
        jitter=False
    )
    
    delays = [policy.calculate_delay(i) for i in range(1, 5)]
    
    assert delays[0] == 1.0
    assert delays[1] == 2.0
    assert delays[2] == 4.0
    assert delays[3] == 8.0


def test_linear_backoff():
    """Test linear backoff strategy."""
    policy = RetryPolicy(
        initial_delay=1.0,
        strategy=RetryStrategy.LINEAR,
        jitter=False
    )
    
    delays = [policy.calculate_delay(i) for i in range(1, 5)]
    
    assert delays[0] == 1.0
    assert delays[1] == 2.0
    assert delays[2] == 3.0
    assert delays[3] == 4.0


# ============================================================================
# Circuit Breaker Tests
# ============================================================================

def test_circuit_breaker_open_after_failures():
    """Test circuit breaker opens after threshold."""
    breaker = CircuitBreaker(CircuitBreakerConfig(failure_threshold=3))
    
    for _ in range(3):
        breaker.record_failure()
    
    assert breaker.state == CircuitState.OPEN
    assert breaker.is_open()


def test_circuit_breaker_half_open_after_timeout():
    """Test circuit breaker transitions to half-open."""
    breaker = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=2,
        timeout=0.1
    ))
    
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    
    time.sleep(0.2)
    
    is_open = breaker.is_open()
    assert not is_open
    assert breaker.state == CircuitState.HALF_OPEN


def test_circuit_breaker_close_after_successes():
    """Test circuit breaker closes after successes."""
    breaker = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=2,
        success_threshold=2,
        timeout=0.1
    ))
    
    breaker.record_failure()
    breaker.record_failure()
    
    time.sleep(0.2)
    breaker.is_open()
    
    breaker.record_success()
    breaker.record_success()
    
    assert breaker.state == CircuitState.CLOSED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
