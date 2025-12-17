"""Message tracing and analytics for communication system."""
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set
from collections import defaultdict
import structlog

logger = structlog.get_logger()


@dataclass
class MessageTrace:
    """Trace information for a single message."""
    message_id: str
    correlation_id: Optional[str]
    sender: str
    recipient: str
    message_type: str
    timestamp: float
    route: List[str] = field(default_factory=list)
    processing_times: Dict[str, float] = field(default_factory=dict)
    status: str = "in_flight"  # in_flight, delivered, acknowledged, failed
    error: Optional[str] = None
    
    def add_hop(self, hop: str):
        """Add a hop to the message route."""
        self.route.append(hop)
    
    def set_processing_time(self, stage: str, duration: float):
        """Record processing time for a stage."""
        self.processing_times[stage] = duration
    
    def mark_delivered(self):
        """Mark message as delivered."""
        self.status = "delivered"
    
    def mark_acknowledged(self):
        """Mark message as acknowledged."""
        self.status = "acknowledged"
    
    def mark_failed(self, error: str):
        """Mark message as failed."""
        self.status = "failed"
        self.error = error
    
    def get_total_time(self) -> float:
        """Get total processing time."""
        return sum(self.processing_times.values())


@dataclass
class MessageAnalytics:
    """Analytics for message patterns."""
    total_messages: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    total_acknowledged: int = 0
    messages_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    messages_by_sender: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    messages_by_recipient: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    avg_processing_time: float = 0.0
    max_processing_time: float = 0.0
    min_processing_time: float = float('inf')
    
    def update(self, trace: MessageTrace):
        """Update analytics from a trace."""
        self.total_messages += 1
        
        if trace.status == "delivered":
            self.total_delivered += 1
        elif trace.status == "failed":
            self.total_failed += 1
        elif trace.status == "acknowledged":
            self.total_acknowledged += 1
        
        self.messages_by_type[trace.message_type] += 1
        self.messages_by_sender[trace.sender] += 1
        self.messages_by_recipient[trace.recipient] += 1
        
        # Update processing times
        total_time = trace.get_total_time()
        if total_time > 0:
            self.max_processing_time = max(self.max_processing_time, total_time)
            self.min_processing_time = min(self.min_processing_time, total_time)
            
            # Update average (running average)
            if self.avg_processing_time == 0:
                self.avg_processing_time = total_time
            else:
                self.avg_processing_time = (
                    (self.avg_processing_time * (self.total_messages - 1) + total_time) 
                    / self.total_messages
                )
    
    def get_success_rate(self) -> float:
        """Get message success rate."""
        if self.total_messages == 0:
            return 0.0
        return (self.total_delivered + self.total_acknowledged) / self.total_messages
    
    def get_failure_rate(self) -> float:
        """Get message failure rate."""
        if self.total_messages == 0:
            return 0.0
        return self.total_failed / self.total_messages


class MessageTracer:
    """Tracks and traces messages through the system."""
    
    def __init__(self, max_traces: int = 10000):
        self.max_traces = max_traces
        self.traces: Dict[str, MessageTrace] = {}
        self.analytics = MessageAnalytics()
        self._lock = None
        logger.info("Initialized MessageTracer", max_traces=max_traces)
    
    async def start_trace(self, message_id: str, sender: str, recipient: str, 
                         message_type: str, correlation_id: Optional[str] = None) -> MessageTrace:
        """Start tracing a message."""
        trace = MessageTrace(
            message_id=message_id,
            correlation_id=correlation_id,
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            timestamp=time.time()
        )
        
        # Limit number of traces
        if len(self.traces) >= self.max_traces:
            # Remove oldest traces
            oldest_keys = sorted(self.traces.keys(), 
                               key=lambda k: self.traces[k].timestamp)[:100]
            for key in oldest_keys:
                del self.traces[key]
        
        self.traces[message_id] = trace
        trace.add_hop(f"created_by_{sender}")
        
        logger.debug("Started message trace", message_id=message_id)
        return trace
    
    async def record_hop(self, message_id: str, hop: str):
        """Record a hop in the message journey."""
        if message_id in self.traces:
            self.traces[message_id].add_hop(hop)
            logger.debug("Recorded hop", message_id=message_id, hop=hop)
    
    async def record_processing_time(self, message_id: str, stage: str, duration: float):
        """Record processing time for a stage."""
        if message_id in self.traces:
            self.traces[message_id].set_processing_time(stage, duration)
    
    async def mark_delivered(self, message_id: str):
        """Mark message as delivered."""
        if message_id in self.traces:
            self.traces[message_id].mark_delivered()
            self.analytics.update(self.traces[message_id])
            logger.debug("Marked delivered", message_id=message_id)
    
    async def mark_acknowledged(self, message_id: str):
        """Mark message as acknowledged."""
        if message_id in self.traces:
            self.traces[message_id].mark_acknowledged()
            self.analytics.update(self.traces[message_id])
            logger.debug("Marked acknowledged", message_id=message_id)
    
    async def mark_failed(self, message_id: str, error: str):
        """Mark message as failed."""
        if message_id in self.traces:
            self.traces[message_id].mark_failed(error)
            self.analytics.update(self.traces[message_id])
            logger.warning("Marked failed", message_id=message_id, error=error)
    
    def get_trace(self, message_id: str) -> Optional[MessageTrace]:
        """Get trace for a message."""
        return self.traces.get(message_id)
    
    def get_traces_by_correlation(self, correlation_id: str) -> List[MessageTrace]:
        """Get all traces with the same correlation ID."""
        return [
            trace for trace in self.traces.values()
            if trace.correlation_id == correlation_id
        ]
    
    def get_analytics(self) -> MessageAnalytics:
        """Get current analytics."""
        return self.analytics
    
    def get_recent_traces(self, limit: int = 100) -> List[MessageTrace]:
        """Get most recent traces."""
        sorted_traces = sorted(
            self.traces.values(),
            key=lambda t: t.timestamp,
            reverse=True
        )
        return sorted_traces[:limit]
    
    def get_failed_traces(self, limit: int = 100) -> List[MessageTrace]:
        """Get recent failed traces."""
        failed = [t for t in self.traces.values() if t.status == "failed"]
        return sorted(failed, key=lambda t: t.timestamp, reverse=True)[:limit]
    
    def clear_old_traces(self, max_age_seconds: float = 3600):
        """Clear traces older than max_age_seconds."""
        current_time = time.time()
        to_remove = [
            msg_id for msg_id, trace in self.traces.items()
            if current_time - trace.timestamp > max_age_seconds
        ]
        
        for msg_id in to_remove:
            del self.traces[msg_id]
        
        if to_remove:
            logger.info("Cleared old traces", count=len(to_remove))
        
        return len(to_remove)


class QueueMonitor:
    """Monitors queue performance and health."""
    
    def __init__(self):
        self.queue_sizes: Dict[str, int] = defaultdict(int)
        self.queue_high_water_marks: Dict[str, int] = defaultdict(int)
        self.enqueue_counts: Dict[str, int] = defaultdict(int)
        self.dequeue_counts: Dict[str, int] = defaultdict(int)
        self.last_activity: Dict[str, float] = {}
        logger.info("Initialized QueueMonitor")
    
    def record_enqueue(self, queue_id: str):
        """Record a message enqueued."""
        self.enqueue_counts[queue_id] += 1
        self.queue_sizes[queue_id] += 1
        self.queue_high_water_marks[queue_id] = max(
            self.queue_high_water_marks[queue_id],
            self.queue_sizes[queue_id]
        )
        self.last_activity[queue_id] = time.time()
    
    def record_dequeue(self, queue_id: str):
        """Record a message dequeued."""
        self.dequeue_counts[queue_id] += 1
        self.queue_sizes[queue_id] = max(0, self.queue_sizes[queue_id] - 1)
        self.last_activity[queue_id] = time.time()
    
    def get_queue_size(self, queue_id: str) -> int:
        """Get current queue size."""
        return self.queue_sizes[queue_id]
    
    def get_queue_stats(self, queue_id: str) -> Dict[str, any]:
        """Get statistics for a queue."""
        return {
            'current_size': self.queue_sizes[queue_id],
            'high_water_mark': self.queue_high_water_marks[queue_id],
            'total_enqueued': self.enqueue_counts[queue_id],
            'total_dequeued': self.dequeue_counts[queue_id],
            'last_activity': self.last_activity.get(queue_id, 0),
            'idle_time': time.time() - self.last_activity.get(queue_id, time.time())
        }
    
    def get_all_queue_stats(self) -> Dict[str, Dict[str, any]]:
        """Get statistics for all queues."""
        return {
            queue_id: self.get_queue_stats(queue_id)
            for queue_id in self.queue_sizes.keys()
        }
    
    def get_total_throughput(self) -> int:
        """Get total messages processed."""
        return sum(self.dequeue_counts.values())
    
    def get_queue_health(self, queue_id: str) -> str:
        """Get health status of a queue."""
        size = self.queue_sizes[queue_id]
        high_water = self.queue_high_water_marks[queue_id]
        
        if size == 0:
            return "idle"
        elif size < high_water * 0.5:
            return "healthy"
        elif size < high_water * 0.8:
            return "warning"
        else:
            return "critical"


class PerformanceMetrics:
    """Tracks performance metrics for the communication system."""
    
    def __init__(self):
        self.start_time = time.time()
        self.message_latencies: List[float] = []
        self.processing_times: List[float] = []
        self.error_count = 0
        self.timeout_count = 0
        self.retry_count = 0
        self.circuit_breaker_trips = 0
        logger.info("Initialized PerformanceMetrics")
    
    def record_latency(self, latency: float):
        """Record message latency."""
        self.message_latencies.append(latency)
        # Keep only last 1000 measurements
        if len(self.message_latencies) > 1000:
            self.message_latencies.pop(0)
    
    def record_processing_time(self, duration: float):
        """Record processing time."""
        self.processing_times.append(duration)
        if len(self.processing_times) > 1000:
            self.processing_times.pop(0)
    
    def record_error(self):
        """Record an error."""
        self.error_count += 1
    
    def record_timeout(self):
        """Record a timeout."""
        self.timeout_count += 1
    
    def record_retry(self):
        """Record a retry attempt."""
        self.retry_count += 1
    
    def record_circuit_breaker_trip(self):
        """Record circuit breaker opening."""
        self.circuit_breaker_trips += 1
    
    def get_avg_latency(self) -> float:
        """Get average message latency."""
        if not self.message_latencies:
            return 0.0
        return sum(self.message_latencies) / len(self.message_latencies)
    
    def get_p95_latency(self) -> float:
        """Get 95th percentile latency."""
        if not self.message_latencies:
            return 0.0
        sorted_latencies = sorted(self.message_latencies)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[index]
    
    def get_p99_latency(self) -> float:
        """Get 99th percentile latency."""
        if not self.message_latencies:
            return 0.0
        sorted_latencies = sorted(self.message_latencies)
        index = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[index]
    
    def get_avg_processing_time(self) -> float:
        """Get average processing time."""
        if not self.processing_times:
            return 0.0
        return sum(self.processing_times) / len(self.processing_times)
    
    def get_uptime(self) -> float:
        """Get system uptime in seconds."""
        return time.time() - self.start_time
    
    def get_error_rate(self) -> float:
        """Get error rate (errors per minute)."""
        uptime_minutes = self.get_uptime() / 60
        if uptime_minutes == 0:
            return 0.0
        return self.error_count / uptime_minutes
    
    def get_summary(self) -> Dict[str, any]:
        """Get performance summary."""
        return {
            'uptime_seconds': self.get_uptime(),
            'avg_latency_ms': self.get_avg_latency() * 1000,
            'p95_latency_ms': self.get_p95_latency() * 1000,
            'p99_latency_ms': self.get_p99_latency() * 1000,
            'avg_processing_time_ms': self.get_avg_processing_time() * 1000,
            'error_count': self.error_count,
            'timeout_count': self.timeout_count,
            'retry_count': self.retry_count,
            'circuit_breaker_trips': self.circuit_breaker_trips,
            'error_rate_per_minute': self.get_error_rate()
        }
