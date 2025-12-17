"""Retry Handler with exponential backoff and circuit breaker."""
import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional
import structlog

logger = structlog.get_logger()


class RetryStrategy(Enum):
    """Retry strategies."""
    IMMEDIATE = "immediate"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"


@dataclass
class RetryPolicy:
    """Retry policy configuration."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt."""
        if self.strategy == RetryStrategy.IMMEDIATE:
            delay = 0
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay * attempt
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.initial_delay * (self.exponential_base ** (attempt - 1))
        elif self.strategy == RetryStrategy.FIBONACCI:
            delay = self._fibonacci(attempt) * self.initial_delay
        else:
            delay = self.initial_delay
        
        # Apply max delay
        delay = min(delay, self.max_delay)
        
        # Add jitter
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())
        
        return delay
    
    @staticmethod
    def _fibonacci(n: int) -> int:
        """Calculate nth Fibonacci number."""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failures exceeded, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 60.0
    half_open_timeout: float = 30.0


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, config: CircuitBreakerConfig = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.opened_at: Optional[float] = None
        logger.info("Initialized CircuitBreaker")
    
    def is_open(self) -> bool:
        """Check if circuit is open."""
        if self.state == CircuitState.CLOSED:
            return False
        
        if self.state == CircuitState.OPEN:
            # Check if timeout expired
            if time.time() - self.opened_at >= self.config.timeout:
                self._transition_to_half_open()
                return False
            return True
        
        # HALF_OPEN state
        return False
    
    def record_success(self):
        """Record successful execution."""
        self.failure_count = 0
        self.last_failure_time = None
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        
        logger.debug("Recorded success", state=self.state.value)
    
    def record_failure(self):
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()
        elif self.failure_count >= self.config.failure_threshold:
            self._transition_to_open()
        
        logger.debug("Recorded failure",
                    count=self.failure_count,
                    state=self.state.value)
    
    def _transition_to_open(self):
        """Transition to OPEN state."""
        self.state = CircuitState.OPEN
        self.opened_at = time.time()
        logger.warning("Circuit breaker opened",
                      failure_count=self.failure_count)
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.failure_count = 0
        self.success_count = 0
        logger.info("Circuit breaker half-opened")
    
    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info("Circuit breaker closed")


class RetryHandler:
    """Handler for retrying operations with backoff and circuit breaker."""
    
    def __init__(self,
                 retry_policy: RetryPolicy = None,
                 circuit_breaker: CircuitBreaker = None):
        self.retry_policy = retry_policy or RetryPolicy()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        logger.info("Initialized RetryHandler")
    
    async def execute(self,
                     func: Callable,
                     *args,
                     **kwargs) -> Any:
        """Execute function with retry logic."""
        attempt = 0
        last_exception = None
        
        while attempt < self.retry_policy.max_attempts:
            attempt += 1
            
            # Check circuit breaker
            if self.circuit_breaker.is_open():
                logger.warning("Circuit breaker open, rejecting request")
                raise Exception("Circuit breaker is open")
            
            try:
                result = await self._execute_once(func, *args, **kwargs)
                self.circuit_breaker.record_success()
                
                if attempt > 1:
                    logger.info("Operation succeeded after retry", attempt=attempt)
                
                return result
                
            except Exception as e:
                last_exception = e
                self.circuit_breaker.record_failure()
                
                logger.warning("Operation failed",
                             attempt=attempt,
                             max_attempts=self.retry_policy.max_attempts,
                             error=str(e))
                
                # Don't wait after last attempt
                if attempt < self.retry_policy.max_attempts:
                    delay = self.retry_policy.calculate_delay(attempt)
                    logger.debug("Waiting before retry", delay=delay)
                    await asyncio.sleep(delay)
        
        # All attempts failed
        logger.error("Operation failed after all retries",
                    attempts=attempt,
                    error=str(last_exception))
        raise last_exception
    
    async def _execute_once(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function once."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    def reset(self):
        """Reset retry handler state."""
        self.circuit_breaker._transition_to_closed()
        logger.info("Reset retry handler")
