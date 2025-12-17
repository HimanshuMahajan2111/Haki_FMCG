"""
Monitoring, Logging, and Performance Tracking.
"""
from typing import Dict, Any, List, Optional
import structlog
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
from pathlib import Path
import threading

logger = structlog.get_logger()


class PerformanceTracker:
    """Track performance metrics for Technical Agent."""
    
    def __init__(self):
        """Initialize performance tracker."""
        self.logger = logger.bind(component="PerformanceTracker")
        
        # Metrics
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_processing_time': 0.0,
            'avg_processing_time': 0.0,
            'min_processing_time': float('inf'),
            'max_processing_time': 0.0,
            'requests_per_hour': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Latency tracking
        self.latency_buckets = {
            '0-1s': 0,
            '1-5s': 0,
            '5-10s': 0,
            '10-30s': 0,
            '30s+': 0
        }
        
        # Component timing
        self.component_timings = defaultdict(list)
        
        # Recent requests for rate calculation
        self.recent_requests = deque(maxlen=1000)
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        self.logger.info("Performance tracker initialized")
    
    def record_request(self, processing_time: float, success: bool, component_timings: Optional[Dict[str, float]] = None):
        """Record request metrics.
        
        Args:
            processing_time: Total processing time in seconds
            success: Whether request succeeded
            component_timings: Optional breakdown by component
        """
        with self.lock:
            self.metrics['total_requests'] += 1
            
            if success:
                self.metrics['successful_requests'] += 1
            else:
                self.metrics['failed_requests'] += 1
            
            # Timing metrics
            self.metrics['total_processing_time'] += processing_time
            self.metrics['avg_processing_time'] = (
                self.metrics['total_processing_time'] / self.metrics['total_requests']
            )
            self.metrics['min_processing_time'] = min(
                self.metrics['min_processing_time'],
                processing_time
            )
            self.metrics['max_processing_time'] = max(
                self.metrics['max_processing_time'],
                processing_time
            )
            
            # Latency buckets
            if processing_time < 1:
                self.latency_buckets['0-1s'] += 1
            elif processing_time < 5:
                self.latency_buckets['1-5s'] += 1
            elif processing_time < 10:
                self.latency_buckets['5-10s'] += 1
            elif processing_time < 30:
                self.latency_buckets['10-30s'] += 1
            else:
                self.latency_buckets['30s+'] += 1
            
            # Component timings
            if component_timings:
                for component, timing in component_timings.items():
                    self.component_timings[component].append(timing)
            
            # Track for rate calculation
            self.recent_requests.append({
                'timestamp': datetime.now(),
                'processing_time': processing_time,
                'success': success
            })
            
            # Calculate requests per hour
            self._calculate_rate()
    
    def record_cache_access(self, hit: bool):
        """Record cache access.
        
        Args:
            hit: Whether cache hit occurred
        """
        with self.lock:
            if hit:
                self.metrics['cache_hits'] += 1
            else:
                self.metrics['cache_misses'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics.
        
        Returns:
            Metrics dictionary
        """
        with self.lock:
            cache_total = self.metrics['cache_hits'] + self.metrics['cache_misses']
            cache_hit_rate = (
                self.metrics['cache_hits'] / cache_total * 100
                if cache_total > 0 else 0
            )
            
            return {
                **self.metrics,
                'cache_hit_rate': round(cache_hit_rate, 2),
                'success_rate': round(
                    self.metrics['successful_requests'] / self.metrics['total_requests'] * 100
                    if self.metrics['total_requests'] > 0 else 0,
                    2
                ),
                'latency_distribution': self.latency_buckets.copy(),
                'component_avg_timings': {
                    component: sum(timings) / len(timings)
                    for component, timings in self.component_timings.items()
                }
            }
    
    def get_component_timings(self) -> Dict[str, Dict[str, float]]:
        """Get detailed component timing statistics.
        
        Returns:
            Component timing stats
        """
        with self.lock:
            stats = {}
            for component, timings in self.component_timings.items():
                if timings:
                    stats[component] = {
                        'avg': sum(timings) / len(timings),
                        'min': min(timings),
                        'max': max(timings),
                        'total': sum(timings),
                        'count': len(timings)
                    }
            return stats
    
    def _calculate_rate(self):
        """Calculate requests per hour from recent requests."""
        if not self.recent_requests:
            return
        
        # Count requests in last hour
        cutoff = datetime.now() - timedelta(hours=1)
        recent_count = sum(
            1 for req in self.recent_requests
            if req['timestamp'] > cutoff
        )
        
        self.metrics['requests_per_hour'] = recent_count
    
    def reset_metrics(self):
        """Reset all metrics."""
        with self.lock:
            self.metrics = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'total_processing_time': 0.0,
                'avg_processing_time': 0.0,
                'min_processing_time': float('inf'),
                'max_processing_time': 0.0,
                'requests_per_hour': 0,
                'cache_hits': 0,
                'cache_misses': 0
            }
            self.latency_buckets = {
                '0-1s': 0,
                '1-5s': 0,
                '5-10s': 0,
                '10-30s': 0,
                '30s+': 0
            }
            self.component_timings.clear()
            self.recent_requests.clear()
            
            self.logger.info("Metrics reset")


class QualityAssurance:
    """Quality assurance checks for Technical Agent outputs."""
    
    def __init__(self):
        """Initialize QA system."""
        self.logger = logger.bind(component="QualityAssurance")
        
        # QA thresholds
        self.thresholds = {
            'min_confidence_score': 0.6,
            'min_match_score': 0.5,
            'max_missing_specs': 3,
            'min_certifications_matched': 0.7
        }
        
        # QA history
        self.qa_history = deque(maxlen=1000)
    
    def validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate processing result.
        
        Args:
            result: Processing result to validate
            
        Returns:
            Validation report
        """
        self.logger.info("Running QA validation")
        
        issues = []
        warnings = []
        
        # Check if processing was successful
        if not result.get('success'):
            issues.append({
                'severity': 'critical',
                'category': 'processing',
                'message': 'Processing failed',
                'details': result.get('error', 'Unknown error')
            })
            return self._create_report(issues, warnings)
        
        # Validate comparisons
        comparisons = result.get('comparisons', [])
        if not comparisons:
            issues.append({
                'severity': 'high',
                'category': 'matching',
                'message': 'No product matches found',
                'details': 'No comparisons generated'
            })
        
        for idx, comp in enumerate(comparisons):
            comp_issues, comp_warnings = self._validate_comparison(comp, idx)
            issues.extend(comp_issues)
            warnings.extend(comp_warnings)
        
        # Check overall confidence
        avg_confidence = result.get('summary', {}).get('average_confidence', 0)
        if avg_confidence < self.thresholds['min_confidence_score']:
            warnings.append({
                'severity': 'medium',
                'category': 'confidence',
                'message': f'Low average confidence: {avg_confidence*100:.1f}%',
                'details': f'Below threshold of {self.thresholds["min_confidence_score"]*100:.1f}%'
            })
        
        # Check match rate
        match_rate = result.get('summary', {}).get('match_rate', 0)
        if match_rate < 80:
            warnings.append({
                'severity': 'medium',
                'category': 'coverage',
                'message': f'Low match rate: {match_rate}%',
                'details': 'Many requirements have no matches'
            })
        
        report = self._create_report(issues, warnings)
        self.qa_history.append(report)
        
        return report
    
    def _validate_comparison(
        self,
        comparison: Dict[str, Any],
        index: int
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Validate individual comparison.
        
        Args:
            comparison: Comparison to validate
            index: Comparison index
            
        Returns:
            Tuple of (issues, warnings)
        """
        issues = []
        warnings = []
        
        products = comparison.get('products', [])
        
        # Check if products exist
        if not products:
            issues.append({
                'severity': 'high',
                'category': 'matching',
                'message': f'Comparison {index+1}: No products matched',
                'details': f"Requirement: {comparison.get('requirement', {}).get('item_name', 'Unknown')}"
            })
            return issues, warnings
        
        # Validate top product
        top_product = products[0]
        
        # Check match score
        if top_product.get('overall_score', 0) < self.thresholds['min_match_score']:
            warnings.append({
                'severity': 'medium',
                'category': 'score',
                'message': f'Comparison {index+1}: Low match score',
                'details': f"Score: {top_product.get('overall_score', 0)*100:.1f}%"
            })
        
        # Check missing specifications
        missing_specs = top_product.get('missing_specs', [])
        if len(missing_specs) > self.thresholds['max_missing_specs']:
            warnings.append({
                'severity': 'medium',
                'category': 'specifications',
                'message': f'Comparison {index+1}: Many missing specs',
                'details': f"Missing {len(missing_specs)} specifications"
            })
        
        # Check certifications
        matched_certs = top_product.get('matched_certifications', [])
        missing_certs = top_product.get('missing_certifications', [])
        if matched_certs or missing_certs:
            cert_match_rate = len(matched_certs) / (len(matched_certs) + len(missing_certs))
            if cert_match_rate < self.thresholds['min_certifications_matched']:
                warnings.append({
                    'severity': 'medium',
                    'category': 'certifications',
                    'message': f'Comparison {index+1}: Low certification match',
                    'details': f"Only {cert_match_rate*100:.1f}% certifications matched"
                })
        
        # Check confidence
        confidence = comparison.get('confidence_score', 0)
        if confidence < self.thresholds['min_confidence_score']:
            warnings.append({
                'severity': 'low',
                'category': 'confidence',
                'message': f'Comparison {index+1}: Low confidence',
                'details': f"Confidence: {confidence*100:.1f}%"
            })
        
        return issues, warnings
    
    def _create_report(
        self,
        issues: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create QA report.
        
        Args:
            issues: List of issues
            warnings: List of warnings
            
        Returns:
            QA report
        """
        # Determine overall quality
        if any(i['severity'] == 'critical' for i in issues):
            quality = 'failed'
        elif len(issues) > 0:
            quality = 'poor'
        elif len(warnings) > 3:
            quality = 'fair'
        elif len(warnings) > 0:
            quality = 'good'
        else:
            quality = 'excellent'
        
        return {
            'timestamp': datetime.now().isoformat(),
            'quality': quality,
            'passed': len(issues) == 0,
            'issue_count': len(issues),
            'warning_count': len(warnings),
            'issues': issues,
            'warnings': warnings,
            'recommendations': self._generate_recommendations(issues, warnings)
        }
    
    def _generate_recommendations(
        self,
        issues: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on issues/warnings.
        
        Args:
            issues: List of issues
            warnings: List of warnings
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if any(i['category'] == 'matching' for i in issues + warnings):
            recommendations.append("Expand product catalog or relax matching criteria")
        
        if any(i['category'] == 'specifications' for i in warnings):
            recommendations.append("Review specification requirements for flexibility")
        
        if any(i['category'] == 'certifications' for i in warnings):
            recommendations.append("Consider alternative certifications or work with manufacturers")
        
        if any(i['category'] == 'confidence' for i in warnings):
            recommendations.append("Improve requirement clarity or add more context")
        
        if not recommendations:
            recommendations.append("Results meet all quality thresholds")
        
        return recommendations
    
    def get_qa_statistics(self) -> Dict[str, Any]:
        """Get QA statistics.
        
        Returns:
            QA statistics
        """
        if not self.qa_history:
            return {
                'total_validations': 0,
                'quality_distribution': {},
                'avg_issue_count': 0,
                'avg_warning_count': 0
            }
        
        quality_counts = defaultdict(int)
        total_issues = 0
        total_warnings = 0
        
        for report in self.qa_history:
            quality_counts[report['quality']] += 1
            total_issues += report['issue_count']
            total_warnings += report['warning_count']
        
        return {
            'total_validations': len(self.qa_history),
            'quality_distribution': dict(quality_counts),
            'avg_issue_count': total_issues / len(self.qa_history),
            'avg_warning_count': total_warnings / len(self.qa_history),
            'pass_rate': sum(1 for r in self.qa_history if r['passed']) / len(self.qa_history) * 100
        }


class MetricsCollector:
    """Collect and export metrics for monitoring."""
    
    def __init__(self, export_dir: str = "./metrics"):
        """Initialize metrics collector.
        
        Args:
            export_dir: Directory to export metrics
        """
        self.logger = logger.bind(component="MetricsCollector")
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics = {}
        self.lock = threading.Lock()
    
    def record_metric(self, name: str, value: Any, tags: Optional[Dict[str, str]] = None):
        """Record a metric value.
        
        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags
        """
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = []
            
            self.metrics[name].append({
                'timestamp': datetime.now().isoformat(),
                'value': value,
                'tags': tags or {}
            })
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics to file.
        
        Args:
            format: Export format (json, csv)
            
        Returns:
            Path to exported file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'json':
            filepath = self.export_dir / f"metrics_{timestamp}.json"
            with open(filepath, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        
        self.logger.info(f"Metrics exported to {filepath}")
        return str(filepath)
    
    def get_metric_summary(self, name: str) -> Dict[str, Any]:
        """Get summary for a specific metric.
        
        Args:
            name: Metric name
            
        Returns:
            Metric summary
        """
        if name not in self.metrics:
            return {}
        
        values = [m['value'] for m in self.metrics[name] if isinstance(m['value'], (int, float))]
        
        if not values:
            return {'count': len(self.metrics[name])}
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'total': sum(values)
        }
