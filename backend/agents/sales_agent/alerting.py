"""
Alert System - Multi-channel notification system.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import structlog
import json

logger = structlog.get_logger()


class AlertChannel(Enum):
    """Alert delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    WEBHOOK = "webhook"
    CONSOLE = "console"


class AlertPriority(Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert message."""
    alert_id: str
    title: str
    message: str
    priority: AlertPriority
    channels: List[AlertChannel]
    data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamps."""
        if not self.created_at:
            self.created_at = datetime.now()
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'alert_id': self.alert_id,
            'title': self.title,
            'message': self.message,
            'priority': self.priority.value,
            'channels': [c.value for c in self.channels],
            'data': self.data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }


@dataclass
class ChannelConfig:
    """Channel configuration."""
    channel: AlertChannel
    enabled: bool = True
    
    # Email
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[str] = None
    to_emails: Optional[List[str]] = None
    
    # SMS
    sms_api_key: Optional[str] = None
    sms_api_url: Optional[str] = None
    to_phones: Optional[List[str]] = None
    
    # Slack
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    
    # Webhook
    webhook_url: Optional[str] = None
    webhook_headers: Optional[Dict[str, str]] = None


class AlertSystem:
    """Multi-channel alert and notification system."""
    
    def __init__(self):
        """Initialize alert system."""
        self.logger = logger.bind(component="AlertSystem")
        self.channels: Dict[AlertChannel, ChannelConfig] = {}
        self.alert_history: List[Alert] = []
        self.templates: Dict[str, str] = {}
        
        # Load default templates
        self._load_default_templates()
        
        self.logger.info("Alert system initialized")
    
    def _load_default_templates(self):
        """Load default alert templates."""
        self.templates = {
            'rfp_discovered': """
🔔 New RFP Discovered

Title: {title}
Organization: {organization}
Value: {value}
Deadline: {deadline}

Relevance Score: {score}/100
URL: {url}
""",
            'high_value_rfp': """
💰 High-Value RFP Alert

Title: {title}
Organization: {organization}
Estimated Value: INR {value:,.2f}
Deadline: {deadline}

This is a HIGH VALUE opportunity!
Relevance Score: {score}/100

URL: {url}
""",
            'bid_generated': """
✅ Bid Generated Successfully

RFP: {title}
Bid ID: {bid_id}
Bid Amount: INR {bid_amount:,.2f}

Workflow ID: {workflow_id}
Generated At: {generated_at}
""",
            'workflow_failed': """
❌ Workflow Failed

RFP: {title}
Workflow ID: {workflow_id}
Error: {error}

Please review and take action.
"""
        }
    
    def configure_channel(self, config: ChannelConfig):
        """Configure an alert channel.
        
        Args:
            config: Channel configuration
        """
        self.channels[config.channel] = config
        self.logger.info(
            "Channel configured",
            channel=config.channel.value,
            enabled=config.enabled
        )
    
    def send_alert(self, alert: Alert) -> Dict[str, bool]:
        """Send alert through configured channels.
        
        Args:
            alert: Alert to send
            
        Returns:
            Dictionary of channel results
        """
        self.logger.info(
            "Sending alert",
            alert_id=alert.alert_id,
            priority=alert.priority.value,
            channels=[c.value for c in alert.channels]
        )
        
        results = {}
        
        for channel in alert.channels:
            try:
                if channel not in self.channels or not self.channels[channel].enabled:
                    results[channel.value] = False
                    continue
                
                # Send through channel
                if channel == AlertChannel.CONSOLE:
                    success = self._send_console(alert)
                elif channel == AlertChannel.EMAIL:
                    success = self._send_email(alert)
                elif channel == AlertChannel.SMS:
                    success = self._send_sms(alert)
                elif channel == AlertChannel.SLACK:
                    success = self._send_slack(alert)
                elif channel == AlertChannel.WEBHOOK:
                    success = self._send_webhook(alert)
                else:
                    success = False
                
                results[channel.value] = success
                
            except Exception as e:
                self.logger.error(
                    "Failed to send alert",
                    channel=channel.value,
                    error=str(e)
                )
                results[channel.value] = False
        
        # Store in history
        alert.sent_at = datetime.now()
        self.alert_history.append(alert)
        
        return results
    
    def _send_console(self, alert: Alert) -> bool:
        """Send alert to console.
        
        Args:
            alert: Alert to send
            
        Returns:
            Success status
        """
        priority_emoji = {
            AlertPriority.LOW: "ℹ️",
            AlertPriority.MEDIUM: "⚠️",
            AlertPriority.HIGH: "🔥",
            AlertPriority.CRITICAL: "🚨"
        }
        
        emoji = priority_emoji.get(alert.priority, "📢")
        
        print(f"\n{emoji} {alert.title}")
        print(f"Priority: {alert.priority.value.upper()}")
        print(f"Message: {alert.message}")
        if alert.data:
            print(f"Data: {json.dumps(alert.data, indent=2)}")
        print("-" * 50)
        
        return True
    
    def _send_email(self, alert: Alert) -> bool:
        """Send alert via email.
        
        Args:
            alert: Alert to send
            
        Returns:
            Success status
        """
        # Placeholder - would integrate with SMTP
        self.logger.info("Email alert sent (simulated)", alert_id=alert.alert_id)
        return True
    
    def _send_sms(self, alert: Alert) -> bool:
        """Send alert via SMS.
        
        Args:
            alert: Alert to send
            
        Returns:
            Success status
        """
        # Placeholder - would integrate with SMS API
        self.logger.info("SMS alert sent (simulated)", alert_id=alert.alert_id)
        return True
    
    def _send_slack(self, alert: Alert) -> bool:
        """Send alert to Slack.
        
        Args:
            alert: Alert to send
            
        Returns:
            Success status
        """
        # Placeholder - would integrate with Slack API
        self.logger.info("Slack alert sent (simulated)", alert_id=alert.alert_id)
        return True
    
    def _send_webhook(self, alert: Alert) -> bool:
        """Send alert via webhook.
        
        Args:
            alert: Alert to send
            
        Returns:
            Success status
        """
        # Placeholder - would make HTTP POST request
        self.logger.info("Webhook alert sent (simulated)", alert_id=alert.alert_id)
        return True
    
    def get_template(self, template_name: str) -> Optional[str]:
        """Get alert template.
        
        Args:
            template_name: Template name
            
        Returns:
            Template string or None
        """
        return self.templates.get(template_name)
    
    def format_alert(self, template_name: str, **kwargs) -> str:
        """Format alert using template.
        
        Args:
            template_name: Template name
            **kwargs: Template variables
            
        Returns:
            Formatted message
        """
        template = self.get_template(template_name)
        if not template:
            return f"Template '{template_name}' not found"
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            return f"Missing template variable: {e}"
    
    def get_alert_history(self, limit: int = 50) -> List[Alert]:
        """Get recent alert history.
        
        Args:
            limit: Maximum number of alerts
            
        Returns:
            List of recent alerts
        """
        return self.alert_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get alert statistics.
        
        Returns:
            Statistics dictionary
        """
        stats = {
            'total_alerts': len(self.alert_history),
            'by_priority': {},
            'by_channel': {},
            'recent_24h': 0
        }
        
        now = datetime.now()
        
        for alert in self.alert_history:
            # By priority
            priority = alert.priority.value
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
            
            # By channel
            for channel in alert.channels:
                channel_name = channel.value
                stats['by_channel'][channel_name] = stats['by_channel'].get(channel_name, 0) + 1
            
            # Recent 24h
            if alert.sent_at and (now - alert.sent_at).total_seconds() < 86400:
                stats['recent_24h'] += 1
        
        return stats
