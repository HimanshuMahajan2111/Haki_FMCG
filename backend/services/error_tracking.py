"""
Error Tracking and Reporting Service
Captures, tracks, and reports application errors
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import traceback
import sys
import logging


class ErrorTracker:
    """Track and analyze application errors"""
    
    def __init__(self):
        self.errors = []
        self.error_counts = defaultdict(int)
        self.error_patterns = defaultdict(list)
        self.max_errors = 1000  # Keep last 1000 errors
        self.logger = logging.getLogger('error_tracker')
    
    def capture_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = 'error',
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> str:
        """
        Capture an exception with context
        
        Returns: Error ID
        """
        error_id = f"ERR_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        
        # Get exception details
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_type is None:
            exc_type = type(exception)
            exc_value = exception
            exc_traceback = exception.__traceback__
        
        error_data = {
            'error_id': error_id,
            'timestamp': datetime.utcnow().isoformat(),
            'type': exc_type.__name__ if exc_type else 'Unknown',
            'message': str(exc_value),
            'severity': severity,
            'traceback': traceback.format_exception(exc_type, exc_value, exc_traceback),
            'context': context or {},
            'user_id': user_id,
            'request_id': request_id
        }
        
        # Store error
        self.errors.append(error_data)
        if len(self.errors) > self.max_errors:
            self.errors.pop(0)
        
        # Update counts
        error_key = f"{exc_type.__name__}:{str(exc_value)[:100]}"
        self.error_counts[error_key] += 1
        
        # Track pattern
        self.error_patterns[exc_type.__name__].append({
            'timestamp': datetime.utcnow(),
            'message': str(exc_value)[:200],
            'context': context
        })
        
        # Log error
        self.logger.error(
            f"Error captured: {error_id}",
            extra={
                'error_id': error_id,
                'error_type': exc_type.__name__,
                'error_message': str(exc_value),
                'context': context
            },
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        return error_id
    
    def get_error(self, error_id: str) -> Optional[Dict[str, Any]]:
        """Get error by ID"""
        for error in self.errors:
            if error['error_id'] == error_id:
                return error
        return None
    
    def get_recent_errors(self, minutes: int = 60, severity: Optional[str] = None) -> List[Dict]:
        """Get recent errors"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        
        recent = [
            e for e in self.errors
            if datetime.fromisoformat(e['timestamp']) >= cutoff
        ]
        
        if severity:
            recent = [e for e in recent if e['severity'] == severity]
        
        return sorted(recent, key=lambda x: x['timestamp'], reverse=True)
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary statistics"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        recent_errors = [
            e for e in self.errors
            if datetime.fromisoformat(e['timestamp']) >= cutoff
        ]
        
        # Count by type
        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        
        for error in recent_errors:
            by_type[error['type']] += 1
            by_severity[error['severity']] += 1
        
        # Top errors
        top_errors = sorted(
            self.error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'total_errors': len(recent_errors),
            'unique_errors': len(set(e['type'] + ':' + e['message'] for e in recent_errors)),
            'by_type': dict(by_type),
            'by_severity': dict(by_severity),
            'top_errors': [
                {'error': error, 'count': count}
                for error, count in top_errors
            ],
            'period_hours': hours
        }
    
    def get_error_patterns(self, error_type: Optional[str] = None) -> Dict[str, Any]:
        """Analyze error patterns"""
        if error_type:
            patterns = self.error_patterns.get(error_type, [])
        else:
            patterns = []
            for type_patterns in self.error_patterns.values():
                patterns.extend(type_patterns)
        
        # Group by time windows
        hourly_counts = defaultdict(int)
        for pattern in patterns:
            hour_key = pattern['timestamp'].replace(minute=0, second=0, microsecond=0)
            hourly_counts[hour_key] += 1
        
        return {
            'error_type': error_type or 'all',
            'total_occurrences': len(patterns),
            'hourly_distribution': {
                k.isoformat(): v for k, v in sorted(hourly_counts.items())
            },
            'recent_examples': patterns[-5:] if patterns else []
        }
    
    def clear_old_errors(self, days: int = 7):
        """Clear errors older than specified days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        self.errors = [
            e for e in self.errors
            if datetime.fromisoformat(e['timestamp']) >= cutoff
        ]
        
        # Clear old patterns
        for error_type in list(self.error_patterns.keys()):
            self.error_patterns[error_type] = [
                p for p in self.error_patterns[error_type]
                if p['timestamp'] >= cutoff
            ]


# Global error tracker
_error_tracker = None

def get_error_tracker() -> ErrorTracker:
    """Get global error tracker instance"""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
    return _error_tracker


def capture_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    severity: str = 'error'
) -> str:
    """Convenience function to capture exception"""
    tracker = get_error_tracker()
    return tracker.capture_exception(exception, context, severity)


# Context manager for error tracking
class track_errors:
    """Context manager to automatically track errors"""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None, severity: str = 'error'):
        self.context = context
        self.severity = severity
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            capture_exception(exc_val, self.context, self.severity)
        return False  # Don't suppress exception
