"""
Production Monitoring Service
Tracks performance metrics, bottlenecks, and system health
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import time
import threading
import psutil
import functools


class PerformanceMonitor:
    """Monitor and track performance metrics"""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.metrics = defaultdict(lambda: deque(maxlen=window_size))
        self.counters = defaultdict(int)
        self.timers = {}
        self.lock = threading.Lock()
        
        # System monitoring
        self.system_metrics = deque(maxlen=60)  # Last 60 measurements
        self.start_time = time.time()
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict] = None):
        """Record a metric value"""
        with self.lock:
            timestamp = time.time()
            self.metrics[name].append({
                'value': value,
                'timestamp': timestamp,
                'tags': tags or {}
            })
    
    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter"""
        with self.lock:
            self.counters[name] += value
    
    def start_timer(self, name: str) -> str:
        """Start a timer and return timer ID"""
        timer_id = f"{name}_{time.time()}"
        self.timers[timer_id] = time.time()
        return timer_id
    
    def stop_timer(self, timer_id: str, metric_name: Optional[str] = None):
        """Stop a timer and record duration"""
        if timer_id in self.timers:
            duration = time.time() - self.timers[timer_id]
            del self.timers[timer_id]
            
            if metric_name:
                self.record_metric(metric_name, duration)
            
            return duration
        return None
    
    def get_metric_stats(self, name: str, duration_seconds: int = 60) -> Dict[str, Any]:
        """Get statistics for a metric"""
        with self.lock:
            if name not in self.metrics:
                return {}
            
            cutoff_time = time.time() - duration_seconds
            recent_values = [
                m['value'] for m in self.metrics[name]
                if m['timestamp'] >= cutoff_time
            ]
            
            if not recent_values:
                return {}
            
            return {
                'count': len(recent_values),
                'min': min(recent_values),
                'max': max(recent_values),
                'avg': sum(recent_values) / len(recent_values),
                'sum': sum(recent_values),
                'last': recent_values[-1] if recent_values else None
            }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics summary"""
        with self.lock:
            metrics_summary = {}
            
            for name in self.metrics.keys():
                stats = self.get_metric_stats(name, duration_seconds=300)  # Last 5 minutes
                if stats:
                    metrics_summary[name] = stats
            
            return {
                'metrics': metrics_summary,
                'counters': dict(self.counters),
                'active_timers': len(self.timers),
                'uptime_seconds': time.time() - self.start_time
            }
    
    def record_system_metrics(self):
        """Record current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                'timestamp': time.time(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / (1024**3),
                'disk_percent': disk.percent,
                'disk_used_gb': disk.used / (1024**3)
            }
            
            with self.lock:
                self.system_metrics.append(metrics)
            
            return metrics
        except Exception as e:
            return {'error': str(e)}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics summary"""
        with self.lock:
            if not self.system_metrics:
                return {}
            
            latest = self.system_metrics[-1]
            
            # Calculate averages
            cpu_values = [m['cpu_percent'] for m in self.system_metrics if 'cpu_percent' in m]
            mem_values = [m['memory_percent'] for m in self.system_metrics if 'memory_percent' in m]
            
            return {
                'current': latest,
                'avg_cpu_percent': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'avg_memory_percent': sum(mem_values) / len(mem_values) if mem_values else 0,
                'samples': len(self.system_metrics)
            }


class BottleneckDetector:
    """Detect and track performance bottlenecks"""
    
    def __init__(self):
        self.slow_operations = deque(maxlen=100)
        self.thresholds = {
            'api_request': 2.0,      # 2 seconds
            'database_query': 1.0,   # 1 second
            'product_match': 3.0,    # 3 seconds
            'rfp_parsing': 5.0,      # 5 seconds
            'agent_action': 4.0      # 4 seconds
        }
    
    def check_operation(self, operation_type: str, duration: float, context: Dict = None):
        """Check if operation is a bottleneck"""
        threshold = self.thresholds.get(operation_type, 5.0)
        
        if duration > threshold:
            bottleneck = {
                'type': operation_type,
                'duration': duration,
                'threshold': threshold,
                'timestamp': datetime.utcnow().isoformat(),
                'context': context or {}
            }
            self.slow_operations.append(bottleneck)
            return True
        
        return False
    
    def get_bottlenecks(self, minutes: int = 60) -> List[Dict]:
        """Get recent bottlenecks"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        
        return [
            b for b in self.slow_operations
            if datetime.fromisoformat(b['timestamp']) >= cutoff
        ]
    
    def get_bottleneck_summary(self) -> Dict[str, Any]:
        """Get bottleneck summary"""
        bottlenecks_by_type = defaultdict(list)
        
        for b in self.slow_operations:
            bottlenecks_by_type[b['type']].append(b['duration'])
        
        summary = {}
        for op_type, durations in bottlenecks_by_type.items():
            summary[op_type] = {
                'count': len(durations),
                'avg_duration': sum(durations) / len(durations),
                'max_duration': max(durations),
                'threshold': self.thresholds.get(op_type, 5.0)
            }
        
        return summary


# Global monitor instance
_performance_monitor = None
_bottleneck_detector = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

def get_bottleneck_detector() -> BottleneckDetector:
    """Get global bottleneck detector"""
    global _bottleneck_detector
    if _bottleneck_detector is None:
        _bottleneck_detector = BottleneckDetector()
    return _bottleneck_detector


# Decorator for monitoring function performance
def monitor_performance(operation_type: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            detector = get_bottleneck_detector()
            
            # Start timer
            timer_id = monitor.start_timer(operation_type)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record metrics
                monitor.record_metric(f"{operation_type}_duration", duration)
                monitor.increment_counter(f"{operation_type}_success")
                
                # Check for bottleneck
                detector.check_operation(operation_type, duration, {
                    'function': func.__name__,
                    'success': True
                })
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                monitor.increment_counter(f"{operation_type}_error")
                
                detector.check_operation(operation_type, duration, {
                    'function': func.__name__,
                    'success': False,
                    'error': str(e)
                })
                
                raise
            
            finally:
                monitor.stop_timer(timer_id)
        
        return wrapper
    return decorator


# Async version
def monitor_async_performance(operation_type: str):
    """Decorator to monitor async function performance"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            detector = get_bottleneck_detector()
            
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                monitor.record_metric(f"{operation_type}_duration", duration)
                monitor.increment_counter(f"{operation_type}_success")
                
                detector.check_operation(operation_type, duration, {
                    'function': func.__name__,
                    'success': True
                })
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                monitor.increment_counter(f"{operation_type}_error")
                
                detector.check_operation(operation_type, duration, {
                    'function': func.__name__,
                    'success': False,
                    'error': str(e)
                })
                
                raise
        
        return wrapper
    return decorator
