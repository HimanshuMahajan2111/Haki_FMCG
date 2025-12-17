"""
Advanced Retry Handler with Exponential Backoff and Circuit Breaker
"""
from typing import Callable, Optional, Any, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import random
import structlog

logger = structlog.get_logger()


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class RetryConfig:
    """Retry configuration."""
    max_retries: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1  # 10% jitter
    timeout: Optional[float] = None


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5  # Open circuit after N failures
    success_threshold: int = 2  # Close circuit after N successes in half-open
    timeout: float = 60.0  # Time to wait before trying again (seconds)
    half_open_max_calls: int = 3  # Max calls to allow in half-open state


@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_state_change: datetime = field(default_factory=datetime.now)
    half_open_calls: int = 0


class RetryHandler:
    """
    Advanced retry handler with exponential backoff, jitter, and circuit breaker.
    
    Features:
    - Exponential backoff with configurable base
    - Random jitter to prevent thundering herd
    - Circuit breaker pattern for fault tolerance
    - Detailed failure tracking and metrics
    """
    
    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        enable_circuit_breaker: bool = True
    ):
        """Initialize retry handler.
        
        Args:
            retry_config: Retry configuration
            circuit_breaker_config: Circuit breaker configuration
            enable_circuit_breaker: Enable circuit breaker
        """
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        self.enable_circuit_breaker = enable_circuit_breaker
        
        # Circuit breaker state per operation
        self.circuit_states: Dict[str, CircuitBreakerState] = {}
        
        # Metrics
        self.metrics = {
            'total_attempts': 0,
            'successful_attempts': 0,
            'failed_attempts': 0,
            'retry_attempts': 0,
            'circuit_opens': 0,
            'circuit_closes': 0
        }
        
        logger.info(
            "Retry handler initialized",
            max_retries=self.retry_config.max_retries,
            circuit_breaker_enabled=enable_circuit_breaker
        )
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt with exponential backoff and jitter.
        
        Args:
            attempt: Retry attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = min(
            self.retry_config.initial_delay * (self.retry_config.exponential_base ** attempt),
            self.retry_config.max_delay
        )
        
        # Add jitter
        if self.retry_config.jitter:
            jitter_range = delay * self.retry_config.jitter_factor
            jitter = random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay + jitter)
        
        return delay
    
    def _get_circuit_state(self, operation_id: str) -> CircuitBreakerState:
        """Get or create circuit breaker state for operation.
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            Circuit breaker state
        """
        if operation_id not in self.circuit_states:
            self.circuit_states[operation_id] = CircuitBreakerState()
        return self.circuit_states[operation_id]
    
    def _should_allow_request(self, operation_id: str) -> bool:
        """Check if request should be allowed based on circuit breaker state.
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            True if request should be allowed
        """
        if not self.enable_circuit_breaker:
            return True
        
        state = self._get_circuit_state(operation_id)
        
        if state.state == CircuitState.CLOSED:
            return True
        
        elif state.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if state.last_failure_time:
                elapsed = (datetime.now() - state.last_failure_time).total_seconds()
                if elapsed >= self.circuit_breaker_config.timeout:
                    # Move to half-open state
                    state.state = CircuitState.HALF_OPEN
                    state.half_open_calls = 0
                    state.last_state_change = datetime.now()
                    logger.info(
                        "Circuit breaker moving to half-open",
                        operation_id=operation_id
                    )
                    return True
            return False
        
        elif state.state == CircuitState.HALF_OPEN:
            # Allow limited requests in half-open state
            if state.half_open_calls < self.circuit_breaker_config.half_open_max_calls:
                state.half_open_calls += 1
                return True
            return False
        
        return False
    
    def _record_success(self, operation_id: str):
        """Record successful operation.
        
        Args:
            operation_id: Operation identifier
        """
        if not self.enable_circuit_breaker:
            return
        
        state = self._get_circuit_state(operation_id)
        
        if state.state == CircuitState.HALF_OPEN:
            state.success_count += 1
            
            # Check if we should close the circuit
            if state.success_count >= self.circuit_breaker_config.success_threshold:
                state.state = CircuitState.CLOSED
                state.failure_count = 0
                state.success_count = 0
                state.last_state_change = datetime.now()
                
                self.metrics['circuit_closes'] += 1
                logger.info(
                    "Circuit breaker closed",
                    operation_id=operation_id
                )
        
        elif state.state == CircuitState.CLOSED:
            # Reset failure count on success
            state.failure_count = 0
    
    def _record_failure(self, operation_id: str):
        """Record failed operation.
        
        Args:
            operation_id: Operation identifier
        """
        if not self.enable_circuit_breaker:
            return
        
        state = self._get_circuit_state(operation_id)
        state.failure_count += 1
        state.last_failure_time = datetime.now()
        
        if state.state == CircuitState.HALF_OPEN:
            # Failure in half-open state, reopen circuit
            state.state = CircuitState.OPEN
            state.success_count = 0
            state.last_state_change = datetime.now()
            
            self.metrics['circuit_opens'] += 1
            logger.warning(
                "Circuit breaker reopened from half-open",
                operation_id=operation_id
            )
        
        elif state.state == CircuitState.CLOSED:
            # Check if we should open the circuit
            if state.failure_count >= self.circuit_breaker_config.failure_threshold:
                state.state = CircuitState.OPEN
                state.last_state_change = datetime.now()
                
                self.metrics['circuit_opens'] += 1
                logger.warning(
                    "Circuit breaker opened",
                    operation_id=operation_id,
                    failure_count=state.failure_count
                )
    
    async def execute_with_retry(
        self,
        operation: Callable[[], Any],
        operation_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute operation with retry logic and circuit breaker.
        
        Args:
            operation: Async operation to execute
            operation_id: Operation identifier for circuit breaker
            context: Additional context for logging
            
        Returns:
            Operation result
            
        Raises:
            Exception: If all retries failed or circuit is open
        """
        context = context or {}
        attempt = 0
        last_exception = None
        
        while attempt <= self.retry_config.max_retries:
            # Check circuit breaker
            if not self._should_allow_request(operation_id):
                self.metrics['failed_attempts'] += 1
                raise Exception(
                    f"Circuit breaker is OPEN for operation: {operation_id}"
                )
            
            try:
                self.metrics['total_attempts'] += 1
                
                # Execute operation with timeout
                if self.retry_config.timeout:
                    result = await asyncio.wait_for(
                        operation(),
                        timeout=self.retry_config.timeout
                    )
                else:
                    result = await operation()
                
                # Success
                self.metrics['successful_attempts'] += 1
                self._record_success(operation_id)
                
                if attempt > 0:
                    logger.info(
                        "Operation succeeded after retry",
                        operation_id=operation_id,
                        attempt=attempt,
                        **context
                    )
                
                return result
            
            except asyncio.TimeoutError as e:
                last_exception = e
                logger.warning(
                    "Operation timeout",
                    operation_id=operation_id,
                    attempt=attempt,
                    timeout=self.retry_config.timeout,
                    **context
                )
            
            except Exception as e:
                last_exception = e
                logger.warning(
                    "Operation failed",
                    operation_id=operation_id,
                    attempt=attempt,
                    error=str(e),
                    **context
                )
            
            # Record failure
            self._record_failure(operation_id)
            
            # Check if we should retry
            if attempt < self.retry_config.max_retries:
                delay = self._calculate_delay(attempt)
                
                self.metrics['retry_attempts'] += 1
                logger.info(
                    "Retrying operation",
                    operation_id=operation_id,
                    attempt=attempt + 1,
                    delay=delay,
                    **context
                )
                
                await asyncio.sleep(delay)
            
            attempt += 1
        
        # All retries exhausted
        self.metrics['failed_attempts'] += 1
        logger.error(
            "Operation failed after all retries",
            operation_id=operation_id,
            attempts=attempt,
            **context
        )
        
        raise last_exception
    
    def get_circuit_state(self, operation_id: str) -> Optional[CircuitBreakerState]:
        """Get circuit breaker state for operation.
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            Circuit breaker state or None
        """
        return self.circuit_states.get(operation_id)
    
    def reset_circuit(self, operation_id: str):
        """Manually reset circuit breaker for operation.
        
        Args:
            operation_id: Operation identifier
        """
        if operation_id in self.circuit_states:
            self.circuit_states[operation_id] = CircuitBreakerState()
            logger.info(
                "Circuit breaker manually reset",
                operation_id=operation_id
            )
    
    def get_metrics(self) -> Dict[str, int]:
        """Get retry metrics.
        
        Returns:
            Metrics dictionary
        """
        return self.metrics.copy()
    
    def get_all_circuit_states(self) -> Dict[str, Dict[str, Any]]:
        """Get all circuit breaker states.
        
        Returns:
            Dictionary of operation_id -> state info
        """
        return {
            op_id: {
                'state': state.state.value,
                'failure_count': state.failure_count,
                'success_count': state.success_count,
                'last_failure_time': state.last_failure_time.isoformat() if state.last_failure_time else None,
                'last_state_change': state.last_state_change.isoformat()
            }
            for op_id, state in self.circuit_states.items()
        }


class RetryPolicy:
    """Predefined retry policies."""
    
    @staticmethod
    def immediate() -> RetryConfig:
        """Immediate retry without delay."""
        return RetryConfig(
            max_retries=3,
            initial_delay=0.1,
            exponential_base=1.0,
            jitter=False
        )
    
    @staticmethod
    def standard() -> RetryConfig:
        """Standard retry with exponential backoff."""
        return RetryConfig(
            max_retries=3,
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=True
        )
    
    @staticmethod
    def aggressive() -> RetryConfig:
        """Aggressive retry for critical operations."""
        return RetryConfig(
            max_retries=5,
            initial_delay=0.5,
            exponential_base=1.5,
            jitter=True
        )
    
    @staticmethod
    def patient() -> RetryConfig:
        """Patient retry for non-critical operations."""
        return RetryConfig(
            max_retries=3,
            initial_delay=2.0,
            exponential_base=3.0,
            jitter=True,
            max_delay=120.0
        )


# Helper function
def create_retry_handler(
    policy: str = "standard",
    enable_circuit_breaker: bool = True,
    **kwargs
) -> RetryHandler:
    """
    Create retry handler with predefined policy.
    
    Args:
        policy: Policy name (immediate, standard, aggressive, patient)
        enable_circuit_breaker: Enable circuit breaker
        **kwargs: Override config parameters
        
    Returns:
        Retry handler instance
    """
    policies = {
        'immediate': RetryPolicy.immediate(),
        'standard': RetryPolicy.standard(),
        'aggressive': RetryPolicy.aggressive(),
        'patient': RetryPolicy.patient()
    }
    
    retry_config = policies.get(policy, RetryPolicy.standard())
    
    # Override with kwargs
    for key, value in kwargs.items():
        if hasattr(retry_config, key):
            setattr(retry_config, key, value)
    
    return RetryHandler(
        retry_config=retry_config,
        enable_circuit_breaker=enable_circuit_breaker
    )
