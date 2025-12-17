"""Error handling decorators and utilities."""
import functools
import time
from typing import Any, Callable, Optional, Type, Union, Tuple
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = structlog.get_logger()


def handle_errors(
    default_return: Any = None,
    log_error: bool = True,
    raise_error: bool = False,
    error_message: Optional[str] = None
):
    """Decorator to handle errors in functions.
    
    Args:
        default_return: Value to return on error
        log_error: Whether to log the error
        raise_error: Whether to re-raise the error after handling
        error_message: Custom error message
        
    Example:
        @handle_errors(default_return=[], log_error=True)
        def get_products():
            # Function code
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    log = logger.bind(
                        function=func.__name__,
                        error_type=type(e).__name__,
                        error=str(e)
                    )
                    msg = error_message or f"Error in {func.__name__}"
                    log.error(msg)
                
                if raise_error:
                    raise
                
                return default_return
        return wrapper
    return decorator


def handle_async_errors(
    default_return: Any = None,
    log_error: bool = True,
    raise_error: bool = False,
    error_message: Optional[str] = None
):
    """Decorator to handle errors in async functions.
    
    Args:
        default_return: Value to return on error
        log_error: Whether to log the error
        raise_error: Whether to re-raise the error
        error_message: Custom error message
        
    Example:
        @handle_async_errors(default_return=[], log_error=True)
        async def get_products():
            # Async function code
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    log = logger.bind(
                        function=func.__name__,
                        error_type=type(e).__name__,
                        error=str(e)
                    )
                    msg = error_message or f"Error in {func.__name__}"
                    log.error(msg)
                
                if raise_error:
                    raise
                
                return default_return
        return wrapper
    return decorator


def retry_on_error(
    max_attempts: int = 3,
    wait_seconds: float = 1.0,
    exponential_backoff: bool = True,
    retry_on: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
):
    """Decorator to retry function on error.
    
    Args:
        max_attempts: Maximum number of retry attempts
        wait_seconds: Base wait time between retries
        exponential_backoff: Use exponential backoff for wait time
        retry_on: Exception type(s) to retry on
        
    Example:
        @retry_on_error(max_attempts=3, wait_seconds=2)
        def fetch_data():
            # Function code
            pass
    """
    def decorator(func: Callable) -> Callable:
        if exponential_backoff:
            retry_decorator = retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=wait_seconds, min=wait_seconds, max=wait_seconds * 10),
                retry=retry_if_exception_type(retry_on),
                reraise=True
            )
        else:
            from tenacity import wait_fixed
            retry_decorator = retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_fixed(wait_seconds),
                retry=retry_if_exception_type(retry_on),
                reraise=True
            )
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log = logger.bind(function=func.__name__)
            try:
                return retry_decorator(func)(*args, **kwargs)
            except Exception as e:
                log.error(
                    "Function failed after retries",
                    max_attempts=max_attempts,
                    error=str(e)
                )
                raise
        
        return wrapper
    return decorator


def measure_time(log_result: bool = True):
    """Decorator to measure function execution time.
    
    Args:
        log_result: Whether to log the execution time
        
    Example:
        @measure_time(log_result=True)
        def process_data():
            # Function code
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            if log_result:
                logger.info(
                    f"{func.__name__} completed",
                    function=func.__name__,
                    execution_time_seconds=round(execution_time, 3)
                )
            
            return result
        return wrapper
    return decorator


def measure_async_time(log_result: bool = True):
    """Decorator to measure async function execution time.
    
    Args:
        log_result: Whether to log the execution time
        
    Example:
        @measure_async_time(log_result=True)
        async def process_data():
            # Async function code
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            if log_result:
                logger.info(
                    f"{func.__name__} completed",
                    function=func.__name__,
                    execution_time_seconds=round(execution_time, 3)
                )
            
            return result
        return wrapper
    return decorator


def validate_args(**validators):
    """Decorator to validate function arguments.
    
    Args:
        **validators: Keyword arguments mapping parameter names to validator functions
        
    Example:
        @validate_args(
            price=lambda x: x > 0,
            quantity=lambda x: isinstance(x, int) and x > 0
        )
        def calculate_total(price, quantity):
            return price * quantity
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each argument
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValueError(
                            f"Validation failed for parameter '{param_name}' "
                            f"with value: {value}"
                        )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def cache_result(ttl_seconds: Optional[int] = None):
    """Decorator to cache function results.
    
    Args:
        ttl_seconds: Time to live for cache in seconds (None = forever)
        
    Example:
        @cache_result(ttl_seconds=300)  # 5 minute cache
        def expensive_operation(param):
            # Function code
            pass
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_times = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            cache_key = str(args) + str(sorted(kwargs.items()))
            
            # Check if cached and not expired
            if cache_key in cache:
                if ttl_seconds is None:
                    return cache[cache_key]
                
                cache_time = cache_times.get(cache_key, 0)
                if time.time() - cache_time < ttl_seconds:
                    logger.debug(
                        f"Cache hit for {func.__name__}",
                        function=func.__name__
                    )
                    return cache[cache_key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = result
            cache_times[cache_key] = time.time()
            
            logger.debug(
                f"Cached result for {func.__name__}",
                function=func.__name__
            )
            
            return result
        
        # Add cache clearing function
        wrapper.clear_cache = lambda: (cache.clear(), cache_times.clear())
        
        return wrapper
    return decorator


def require_auth(role: Optional[str] = None):
    """Decorator to require authentication (placeholder for actual auth).
    
    Args:
        role: Required role (None = any authenticated user)
        
    Example:
        @require_auth(role='admin')
        def admin_function():
            # Function code
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # This is a placeholder - implement actual auth logic
            # For now, just log the requirement
            logger.debug(
                f"Auth required for {func.__name__}",
                function=func.__name__,
                required_role=role
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def deprecation_warning(message: str, removal_version: Optional[str] = None):
    """Decorator to mark function as deprecated.
    
    Args:
        message: Deprecation message
        removal_version: Version when function will be removed
        
    Example:
        @deprecation_warning("Use new_function instead", removal_version="2.0")
        def old_function():
            # Function code
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import warnings
            
            warning_msg = f"{func.__name__} is deprecated. {message}"
            if removal_version:
                warning_msg += f" Will be removed in version {removal_version}."
            
            warnings.warn(warning_msg, DeprecationWarning, stacklevel=2)
            logger.warning(
                "Deprecated function called",
                function=func.__name__,
                message=message,
                removal_version=removal_version
            )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class ErrorContext:
    """Context manager for error handling with automatic logging.
    
    Example:
        with ErrorContext("Processing products", default_return=[]):
            # Code that might raise errors
            products = load_products()
    """
    
    def __init__(
        self,
        operation_name: str,
        default_return: Any = None,
        log_error: bool = True,
        raise_error: bool = False
    ):
        """Initialize error context.
        
        Args:
            operation_name: Name of the operation
            default_return: Default value to return on error
            log_error: Whether to log errors
            raise_error: Whether to re-raise errors
        """
        self.operation_name = operation_name
        self.default_return = default_return
        self.log_error = log_error
        self.raise_error = raise_error
        self.result = default_return
    
    def __enter__(self):
        """Enter context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context with error handling."""
        if exc_type is not None:
            if self.log_error:
                logger.error(
                    f"Error in {self.operation_name}",
                    operation=self.operation_name,
                    error_type=exc_type.__name__,
                    error=str(exc_val)
                )
            
            if self.raise_error:
                return False  # Re-raise the exception
            
            return True  # Suppress the exception
        
        return True


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default on division by zero.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
        
    Returns:
        Division result or default
    """
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ValueError):
        return default


def safe_get(
    dictionary: dict,
    key: str,
    default: Any = None,
    required_type: Optional[Type] = None
) -> Any:
    """Safely get value from dictionary with type checking.
    
    Args:
        dictionary: Dictionary to get value from
        key: Key to retrieve
        default: Default value if key not found
        required_type: Required type for value
        
    Returns:
        Value from dictionary or default
    """
    value = dictionary.get(key, default)
    
    if value is None:
        return default
    
    if required_type and not isinstance(value, required_type):
        logger.warning(
            f"Type mismatch for key '{key}'",
            expected_type=required_type.__name__,
            actual_type=type(value).__name__
        )
        return default
    
    return value


def batch_process_with_errors(
    items: list,
    processor: Callable,
    log_errors: bool = True,
    continue_on_error: bool = True
) -> Tuple[list, list]:
    """Process items in batch with error handling.
    
    Args:
        items: List of items to process
        processor: Function to process each item
        log_errors: Whether to log errors
        continue_on_error: Whether to continue processing on error
        
    Returns:
        Tuple of (successful_results, failed_items)
    """
    results = []
    failures = []
    
    for item in items:
        try:
            result = processor(item)
            results.append(result)
        except Exception as e:
            if log_errors:
                logger.error(
                    "Error processing item",
                    item=str(item)[:100],
                    error=str(e)
                )
            
            failures.append({
                'item': item,
                'error': str(e),
                'error_type': type(e).__name__
            })
            
            if not continue_on_error:
                break
    
    return results, failures
