"""
Dashboard Data - Monitoring and analytics data export.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class DashboardDataExporter:
    """Export data for monitoring dashboard."""
    
    def __init__(self, agent):
        """Initialize exporter.
        
        Args:
            agent: SalesAgent instance
        """
        self.logger = logger.bind(component="DashboardDataExporter")
        self.agent = agent
    
    def export_overview(self) -> Dict[str, Any]:
        """Export overview dashboard data.
        
        Returns:
            Overview data
        """
        stats = self.agent.get_statistics()
        
        return {
            'agent_status': self.agent.state.value,
            'last_updated': datetime.now().isoformat(),
            'statistics': stats,
            'active_schedules': len(self.agent.scheduler.schedules) if hasattr(self.agent, 'scheduler') else 0,
            'monitored_sites': len(self.agent.url_monitor.monitored_sites) if hasattr(self.agent, 'url_monitor') else 0
        }
    
    def export_opportunities(self, limit: int = 100) -> Dict[str, Any]:
        """Export opportunities data.
        
        Args:
            limit: Maximum opportunities to return
            
        Returns:
            Opportunities data
        """
        recent = self.agent.get_recent_opportunities(limit=limit)
        relevant = self.agent.get_relevant_opportunities(limit=20)
        
        return {
            'recent': [opp.to_dict() for opp in recent],
            'relevant': [opp.to_dict() for opp in relevant],
            'total': len(self.agent.opportunities)
        }
    
    def export_workflows(self) -> Dict[str, Any]:
        """Export workflow data.
        
        Returns:
            Workflow data
        """
        if not hasattr(self.agent, 'workflow_trigger'):
            return {'active': [], 'completed': [], 'total': 0}
        
        active = self.agent.workflow_trigger.get_active_workflows()
        completed = self.agent.workflow_trigger.completed_workflows
        
        return {
            'active': [w['result'].to_dict() for w in active],
            'completed': [w.to_dict() for w in completed[-50:]],
            'total': len(active) + len(completed)
        }
    
    def export_time_series(self, days: int = 7) -> Dict[str, Any]:
        """Export time-series metrics.
        
        Args:
            days: Number of days to export
            
        Returns:
            Time-series data
        """
        # Calculate daily statistics
        daily_stats = self._calculate_daily_stats(days)
        
        return {
            'period': f"last_{days}_days",
            'daily': daily_stats,
            'trends': self._calculate_trends(daily_stats)
        }
    
    def _calculate_daily_stats(self, days: int) -> List[Dict[str, Any]]:
        """Calculate daily statistics.
        
        Args:
            days: Number of days
            
        Returns:
            List of daily stats
        """
        now = datetime.now()
        daily_stats = []
        
        for i in range(days):
            date = now - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # Count opportunities discovered on this date
            discovered = 0
            relevant = 0
            
            for opp in self.agent.opportunities:
                if opp.discovered_date.date() == date.date():
                    discovered += 1
                    if opp.status == "relevant":
                        relevant += 1
            
            daily_stats.append({
                'date': date_str,
                'discovered': discovered,
                'relevant': relevant,
                'relevance_rate': relevant / discovered if discovered > 0 else 0
            })
        
        return list(reversed(daily_stats))
    
    def _calculate_trends(self, daily_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trends from daily stats.
        
        Args:
            daily_stats: Daily statistics
            
        Returns:
            Trends data
        """
        if len(daily_stats) < 2:
            return {}
        
        # Calculate averages
        recent_3 = daily_stats[-3:]
        previous_3 = daily_stats[-6:-3] if len(daily_stats) >= 6 else daily_stats[:-3]
        
        recent_avg = sum(d['discovered'] for d in recent_3) / len(recent_3)
        previous_avg = sum(d['discovered'] for d in previous_3) / len(previous_3) if previous_3 else recent_avg
        
        # Calculate trend
        trend_pct = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
        
        return {
            'discovery_trend': 'up' if trend_pct > 5 else 'down' if trend_pct < -5 else 'stable',
            'trend_percentage': round(trend_pct, 2),
            'recent_average': round(recent_avg, 2),
            'previous_average': round(previous_avg, 2)
        }
    
    def export_alerts(self, limit: int = 50) -> Dict[str, Any]:
        """Export alerts data.
        
        Args:
            limit: Maximum alerts to return
            
        Returns:
            Alerts data
        """
        if not hasattr(self.agent, 'alert_system'):
            return {'recent': [], 'statistics': {}}
        
        history = self.agent.alert_system.get_alert_history(limit=limit)
        stats = self.agent.alert_system.get_statistics()
        
        return {
            'recent': [alert.to_dict() for alert in history],
            'statistics': stats
        }
    
    def export_full_dashboard(self) -> Dict[str, Any]:
        """Export complete dashboard data.
        
        Returns:
            Full dashboard data
        """
        return {
            'overview': self.export_overview(),
            'opportunities': self.export_opportunities(),
            'workflows': self.export_workflows(),
            'time_series': self.export_time_series(),
            'alerts': self.export_alerts(),
            'exported_at': datetime.now().isoformat()
        }
