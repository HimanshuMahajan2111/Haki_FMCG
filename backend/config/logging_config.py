"""
Production Logging Configuration
Structured logging with rotation, filtering, and cloud export support
"""
import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import traceback


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add custom fields
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'workflow_id'):
            log_data['workflow_id'] = record.workflow_id
        
        return json.dumps(log_data)


class ContextFilter(logging.Filter):
    """Add contextual information to log records"""
    
    def __init__(self):
        super().__init__()
        self.request_id = None
        self.user_id = None
        self.workflow_id = None
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Add context to record
        if self.request_id:
            record.request_id = self.request_id
        if self.user_id:
            record.user_id = self.user_id
        if self.workflow_id:
            record.workflow_id = self.workflow_id
        
        return True


def setup_production_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    enable_json: bool = True,
    enable_console: bool = True,
    enable_file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 10
):
    """
    Setup production logging configuration
    
    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json: Use JSON formatting
        enable_console: Log to console
        enable_file: Log to rotating files
        max_bytes: Max size per log file
        backup_count: Number of backup files to keep
    """
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Formatters
    if enable_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Rotating file handlers
    if enable_file:
        # Main application log
        app_handler = logging.handlers.RotatingFileHandler(
            log_path / 'app.log',
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        app_handler.setLevel(logging.DEBUG)
        app_handler.setFormatter(formatter)
        root_logger.addHandler(app_handler)
        
        # Error log (errors only)
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / 'error.log',
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
        
        # Performance log
        perf_handler = logging.handlers.RotatingFileHandler(
            log_path / 'performance.log',
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(formatter)
        
        perf_logger = logging.getLogger('performance')
        perf_logger.addHandler(perf_handler)
        perf_logger.propagate = False
        
        # Access log
        access_handler = logging.handlers.RotatingFileHandler(
            log_path / 'access.log',
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        access_handler.setFormatter(formatter)
        
        access_logger = logging.getLogger('access')
        access_logger.addHandler(access_handler)
        access_logger.propagate = False
    
    # Add context filter
    context_filter = ContextFilter()
    root_logger.addFilter(context_filter)
    
    # Suppress noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    return context_filter


def log_with_context(logger: logging.Logger, level: str, message: str, **context):
    """Log message with additional context"""
    extra_data = context
    
    log_func = getattr(logger, level.lower())
    log_func(message, extra={'extra_data': extra_data})


def create_logger(name: str) -> logging.Logger:
    """Create a logger with the given name"""
    return logging.getLogger(name)


# Pre-configured loggers
def get_app_logger() -> logging.Logger:
    """Get application logger"""
    return logging.getLogger('app')


def get_api_logger() -> logging.Logger:
    """Get API logger"""
    return logging.getLogger('api')


def get_performance_logger() -> logging.Logger:
    """Get performance logger"""
    return logging.getLogger('performance')


def get_access_logger() -> logging.Logger:
    """Get access logger"""
    return logging.getLogger('access')


def get_security_logger() -> logging.Logger:
    """Get security logger"""
    return logging.getLogger('security')
