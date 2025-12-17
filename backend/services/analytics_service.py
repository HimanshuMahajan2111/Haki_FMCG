"""
Comprehensive Analytics Service
Tracks RFP processing, match accuracy, win rates, agent performance, and system health
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
import statistics
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from db.database import get_db, AsyncSessionLocal
from db.models import RFP, Product, AgentLog, WorkflowRun


class AnalyticsService:
    """Service for generating comprehensive analytics and dashboard data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== RFP Processing Analytics ====================
    
    def get_rfp_processing_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive RFP processing statistics from real RFP table"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total RFPs from RFP table
        total_rfps = self.db.query(RFP).filter(
            RFP.created_at >= start_date
        ).count()
        
        # If no recent RFPs, get all RFPs
        if total_rfps == 0:
            total_rfps = self.db.query(RFP).count()
            start_date = datetime.utcnow() - timedelta(days=365)  # Look back 1 year
        
        # RFPs by status
        status_counts = self.db.query(
            RFP.status,
            func.count(RFP.id)
        ).filter(
            RFP.created_at >= start_date
        ).group_by(RFP.status).all()
        
        # Count in progress (discovered + processing)
        in_progress = sum(c for s, c in status_counts if s.value in ['discovered', 'processing'])
        
        # Average processing time
        rfps_with_time = self.db.query(RFP).filter(
            and_(
                RFP.created_at >= start_date,
                RFP.processing_time_seconds.isnot(None)
            )
        ).all()
        
        avg_processing_time = statistics.mean([
            r.processing_time_seconds for r in rfps_with_time
        ]) if rfps_with_time else 0
        
        # Success rate (reviewed, approved, submitted)
        success_count = sum(c for s, c in status_counts if s.value in ['reviewed', 'approved', 'submitted'])
        success_rate = (success_count / total_rfps * 100) if total_rfps > 0 else 0
        
        return {
            'total_rfps': total_rfps,
            'in_progress': in_progress,
            'status_breakdown': {s.value: c for s, c in status_counts},
            'avg_processing_time_seconds': round(avg_processing_time, 2),
            'success_rate_percent': round(success_rate, 2),
            'period_days': days
        }
    
    def _calculate_stage_times(self, workflows: List[WorkflowRun]) -> Dict[str, float]:
        """Calculate average time spent in each stage"""
        stage_times = defaultdict(list)
        
        for workflow in workflows:
            if workflow.stage_results:
                for stage, result in workflow.stage_results.items():
                    if isinstance(result, dict) and 'duration' in result:
                        stage_times[stage].append(result['duration'])
        
        return {
            stage: round(statistics.mean(times), 2)
            for stage, times in stage_times.items()
            if times
        }
    
    def _get_daily_volume(self, start_date: datetime) -> List[Dict[str, Any]]:
        """Get daily RFP processing volume"""
        daily_data = self.db.query(
            func.date(WorkflowRun.created_at).label('date'),
            func.count(WorkflowRun.id).label('count')
        ).filter(
            WorkflowRun.created_at >= start_date
        ).group_by(
            func.date(WorkflowRun.created_at)
        ).order_by('date').all()
        
        return [
            {'date': str(date), 'count': count}
            for date, count in daily_data
        ]
    
    # ==================== Match Accuracy Analytics ====================
    
    def get_match_accuracy_stats(self, days: int = 30) -> Dict[str, Any]:
        """Calculate product matching accuracy metrics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get completed workflows with matching data
        workflows = self.db.query(WorkflowRun).filter(
            and_(
                WorkflowRun.status == 'completed',
                WorkflowRun.created_at >= start_date,
                WorkflowRun.stage_results.isnot(None)
            )
        ).all()
        
        match_scores = []
        confidence_scores = []
        match_types = defaultdict(int)
        
        for workflow in workflows:
            stage_results = workflow.stage_results or {}
            
            # Extract matching data
            if 'product_matching' in stage_results:
                matching_data = stage_results['product_matching']
                
                if isinstance(matching_data, dict):
                    # Match score
                    if 'match_score' in matching_data:
                        match_scores.append(matching_data['match_score'])
                    
                    # Confidence
                    if 'confidence' in matching_data:
                        confidence_scores.append(matching_data['confidence'])
                    
                    # Match type
                    if 'match_type' in matching_data:
                        match_types[matching_data['match_type']] += 1
        
        avg_match_score = statistics.mean(match_scores) if match_scores else 0
        avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0
        
        # Accuracy by category
        category_accuracy = self._calculate_category_accuracy(workflows)
        
        return {
            'avg_match_score': round(avg_match_score, 4),
            'avg_confidence': round(avg_confidence, 4),
            'match_type_distribution': dict(match_types),
            'total_matches': len(match_scores),
            'category_accuracy': category_accuracy,
            'high_confidence_matches': sum(1 for c in confidence_scores if c > 0.8),
            'low_confidence_matches': sum(1 for c in confidence_scores if c < 0.5),
            'period_days': days
        }
    
    def _calculate_category_accuracy(self, workflows: List[WorkflowRun]) -> Dict[str, float]:
        """Calculate matching accuracy by product category"""
        category_scores = defaultdict(list)
        
        for workflow in workflows:
            stage_results = workflow.stage_results or {}
            if 'product_matching' in stage_results:
                matching_data = stage_results['product_matching']
                if isinstance(matching_data, dict):
                    category = matching_data.get('category', 'unknown')
                    score = matching_data.get('match_score', 0)
                    category_scores[category].append(score)
        
        return {
            category: round(statistics.mean(scores), 4)
            for category, scores in category_scores.items()
            if scores
        }
    
    # ==================== Win Rate Analytics ====================
    
    def get_win_rate_stats(self, days: int = 90) -> Dict[str, Any]:
        """Calculate RFP win rate statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get completed RFPs
        completed_rfps = self.db.query(WorkflowRun).filter(
            and_(
                WorkflowRun.status == 'completed',
                WorkflowRun.created_at >= start_date
            )
        ).all()
        
        total_completed = len(completed_rfps)
        won_count = 0
        lost_count = 0
        pending_count = 0
        
        # Analyze win/loss data
        for workflow in completed_rfps:
            metadata = workflow.metadata or {}
            outcome = metadata.get('outcome', 'pending')
            
            if outcome == 'won':
                won_count += 1
            elif outcome == 'lost':
                lost_count += 1
            else:
                pending_count += 1
        
        win_rate = (won_count / total_completed * 100) if total_completed > 0 else 0
        
        # Win rate by customer
        customer_win_rates = self._calculate_customer_win_rates(completed_rfps)
        
        # Win rate by value range
        value_win_rates = self._calculate_value_win_rates(completed_rfps)
        
        # Average quote value for won vs lost
        won_values = [
            w.metadata.get('quote_value', 0) 
            for w in completed_rfps 
            if w.metadata and w.metadata.get('outcome') == 'won'
        ]
        lost_values = [
            w.metadata.get('quote_value', 0) 
            for w in completed_rfps 
            if w.metadata and w.metadata.get('outcome') == 'lost'
        ]
        
        return {
            'total_completed': total_completed,
            'won_count': won_count,
            'lost_count': lost_count,
            'pending_count': pending_count,
            'win_rate_percent': round(win_rate, 2),
            'customer_win_rates': customer_win_rates,
            'value_range_win_rates': value_win_rates,
            'avg_won_value': round(statistics.mean(won_values), 2) if won_values else 0,
            'avg_lost_value': round(statistics.mean(lost_values), 2) if lost_values else 0,
            'period_days': days
        }
    
    def _calculate_customer_win_rates(self, workflows: List[WorkflowRun]) -> Dict[str, Dict[str, Any]]:
        """Calculate win rates by customer"""
        customer_data = defaultdict(lambda: {'total': 0, 'won': 0})
        
        for workflow in workflows:
            customer = workflow.customer_id
            outcome = (workflow.metadata or {}).get('outcome', 'pending')
            
            customer_data[customer]['total'] += 1
            if outcome == 'won':
                customer_data[customer]['won'] += 1
        
        return {
            customer: {
                'total': data['total'],
                'won': data['won'],
                'win_rate': round(data['won'] / data['total'] * 100, 2) if data['total'] > 0 else 0
            }
            for customer, data in customer_data.items()
        }
    
    def _calculate_value_win_rates(self, workflows: List[WorkflowRun]) -> Dict[str, Dict[str, Any]]:
        """Calculate win rates by quote value ranges"""
        ranges = {
            '0-100k': (0, 100000),
            '100k-500k': (100000, 500000),
            '500k-1M': (500000, 1000000),
            '1M+': (1000000, float('inf'))
        }
        
        range_data = defaultdict(lambda: {'total': 0, 'won': 0})
        
        for workflow in workflows:
            metadata = workflow.metadata or {}
            value = metadata.get('quote_value', 0)
            outcome = metadata.get('outcome', 'pending')
            
            for range_name, (min_val, max_val) in ranges.items():
                if min_val <= value < max_val:
                    range_data[range_name]['total'] += 1
                    if outcome == 'won':
                        range_data[range_name]['won'] += 1
                    break
        
        return {
            range_name: {
                'total': data['total'],
                'won': data['won'],
                'win_rate': round(data['won'] / data['total'] * 100, 2) if data['total'] > 0 else 0
            }
            for range_name, data in range_data.items()
        }
    
    # ==================== Agent Performance Analytics ====================
    
    def get_agent_performance_stats(self, days: int = 30) -> Dict[str, Any]:
        """Analyze agent performance metrics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get agent logs
        agent_logs = self.db.query(AgentLog).filter(
            AgentLog.timestamp >= start_date
        ).all()
        
        agent_stats = defaultdict(lambda: {
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'total_duration': 0,
            'action_types': defaultdict(int)
        })
        
        for log in agent_logs:
            agent_name = log.agent_name
            stats = agent_stats[agent_name]
            
            stats['total_actions'] += 1
            
            if log.status == 'success':
                stats['successful_actions'] += 1
            elif log.status == 'error':
                stats['failed_actions'] += 1
            
            if log.duration:
                stats['total_duration'] += log.duration
            
            stats['action_types'][log.action] += 1
        
        # Calculate metrics
        agent_metrics = {}
        for agent_name, stats in agent_stats.items():
            total = stats['total_actions']
            success_rate = (stats['successful_actions'] / total * 100) if total > 0 else 0
            avg_duration = (stats['total_duration'] / total) if total > 0 else 0
            
            agent_metrics[agent_name] = {
                'total_actions': total,
                'success_rate': round(success_rate, 2),
                'avg_duration_seconds': round(avg_duration, 2),
                'action_types': dict(stats['action_types']),
                'failed_actions': stats['failed_actions']
            }
        
        # Top performing agents
        top_agents = sorted(
            agent_metrics.items(),
            key=lambda x: (x[1]['success_rate'], -x[1]['avg_duration_seconds']),
            reverse=True
        )[:5]
        
        return {
            'agent_metrics': agent_metrics,
            'top_agents': [{'name': name, **metrics} for name, metrics in top_agents],
            'total_agents': len(agent_metrics),
            'total_actions': sum(s['total_actions'] for s in agent_stats.values()),
            'period_days': days
        }
    
    # ==================== System Health Analytics ====================
    
    def get_system_health_stats(self) -> Dict[str, Any]:
        """Get comprehensive system health metrics"""
        import psutil
        import os
        
        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database stats
        db_stats = self._get_database_stats()
        
        # Recent errors (last 24 hours)
        recent_errors = self.db.query(WorkflowRun).filter(
            and_(
                WorkflowRun.status == 'failed',
                WorkflowRun.created_at >= datetime.utcnow() - timedelta(hours=24)
            )
        ).count()
        
        # Active workflows
        active_workflows = self.db.query(WorkflowRun).filter(
            WorkflowRun.status.in_(['submitted', 'in_progress'])
        ).count()
        
        # System uptime (approximation)
        uptime_seconds = (datetime.utcnow() - datetime(2024, 1, 1)).total_seconds()
        
        return {
            'system_resources': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_percent': disk.percent,
                'disk_free_gb': round(disk.free / (1024**3), 2)
            },
            'database': db_stats,
            'error_rate_24h': recent_errors,
            'active_workflows': active_workflows,
            'uptime_hours': round(uptime_seconds / 3600, 2),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        rfp_count = self.db.query(RFP).count()
        product_count = self.db.query(Product).count()
        workflow_count = self.db.query(WorkflowRun).count()
        agent_log_count = self.db.query(AgentLog).count()
        
        # Recent activity (last hour)
        recent_workflows = self.db.query(WorkflowRun).filter(
            WorkflowRun.created_at >= datetime.utcnow() - timedelta(hours=1)
        ).count()
        
        return {
            'total_rfps': rfp_count,
            'total_products': product_count,
            'total_workflows': workflow_count,
            'total_agent_logs': agent_log_count,
            'recent_activity_1h': recent_workflows
        }
    
    # ==================== Dashboard Data Generation ====================
    
    def generate_dashboard_data(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive dashboard data"""
        return {
            'summary': self._generate_summary_stats(days),
            'rfp_processing': self.get_rfp_processing_stats(days),
            'match_accuracy': self.get_match_accuracy_stats(days),
            'win_rates': self.get_win_rate_stats(min(days * 3, 90)),  # Longer period for win rates
            'agent_performance': self.get_agent_performance_stats(days),
            'system_health': self.get_system_health_stats(),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _generate_summary_stats(self, days: int) -> Dict[str, Any]:
        """Generate high-level summary statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        total_rfps = self.db.query(WorkflowRun).filter(
            WorkflowRun.created_at >= start_date
        ).count()
        
        completed = self.db.query(WorkflowRun).filter(
            and_(
                WorkflowRun.status == 'completed',
                WorkflowRun.created_at >= start_date
            )
        ).count()
        
        in_progress = self.db.query(WorkflowRun).filter(
            WorkflowRun.status == 'in_progress'
        ).count()
        
        failed = self.db.query(WorkflowRun).filter(
            and_(
                WorkflowRun.status == 'failed',
                WorkflowRun.created_at >= start_date
            )
        ).count()
        
        # Calculate trends (compare with previous period)
        previous_start = start_date - timedelta(days=days)
        previous_total = self.db.query(WorkflowRun).filter(
            and_(
                WorkflowRun.created_at >= previous_start,
                WorkflowRun.created_at < start_date
            )
        ).count()
        
        trend = ((total_rfps - previous_total) / previous_total * 100) if previous_total > 0 else 0
        
        return {
            'total_rfps': total_rfps,
            'completed': completed,
            'in_progress': in_progress,
            'failed': failed,
            'success_rate': round(completed / total_rfps * 100, 2) if total_rfps > 0 else 0,
            'trend_percent': round(trend, 2),
            'period_days': days
        }
    
    # ==================== Real-time Monitoring ====================
    
    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get real-time system metrics for monitoring"""
        # Current active workflows
        active = self.db.query(WorkflowRun).filter(
            WorkflowRun.status.in_(['submitted', 'in_progress'])
        ).all()
        
        # Recent completions (last 5 minutes)
        recent_completed = self.db.query(WorkflowRun).filter(
            and_(
                WorkflowRun.status == 'completed',
                WorkflowRun.completed_at >= datetime.utcnow() - timedelta(minutes=5)
            )
        ).count()
        
        # Recent errors (last 5 minutes)
        recent_errors = self.db.query(WorkflowRun).filter(
            and_(
                WorkflowRun.status == 'failed',
                WorkflowRun.created_at >= datetime.utcnow() - timedelta(minutes=5)
            )
        ).count()
        
        # Average queue time
        queue_times = [
            (datetime.utcnow() - w.created_at).total_seconds()
            for w in active
            if w.status == 'submitted'
        ]
        avg_queue_time = statistics.mean(queue_times) if queue_times else 0
        
        return {
            'active_workflows': len(active),
            'queued_workflows': sum(1 for w in active if w.status == 'submitted'),
            'processing_workflows': sum(1 for w in active if w.status == 'in_progress'),
            'recent_completed_5m': recent_completed,
            'recent_errors_5m': recent_errors,
            'avg_queue_time_seconds': round(avg_queue_time, 2),
            'timestamp': datetime.utcnow().isoformat()
        }


# Singleton instance
_analytics_service = None

def get_analytics_service(db: Session) -> AnalyticsService:
    """Get analytics service instance"""
    return AnalyticsService(db)
