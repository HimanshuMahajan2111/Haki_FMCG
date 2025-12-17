"""
Audit Trail Generator
Tracks and logs all activities, decisions, and data transformations.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
import json
import structlog

logger = structlog.get_logger()


class AuditEventType(Enum):
    """Types of audit events."""
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    DATA_RECEIVED = "data_received"
    DATA_TRANSFORMED = "data_transformed"
    DATA_VALIDATED = "data_validated"
    DECISION_MADE = "decision_made"
    ERROR_OCCURRED = "error_occurred"
    DOCUMENT_GENERATED = "document_generated"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event record."""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: str
    component: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    related_events: List[str] = field(default_factory=list)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    workflow_id: Optional[str] = None
    agent_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return data


@dataclass
class AuditTrail:
    """Complete audit trail for a workflow."""
    trail_id: str
    workflow_id: str
    started_at: str
    completed_at: Optional[str] = None
    events: List[AuditEvent] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'trail_id': self.trail_id,
            'workflow_id': self.workflow_id,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'events': [event.to_dict() for event in self.events],
            'summary': self.summary
        }


class AuditTrailGenerator:
    """
    Audit Trail Generator
    
    Features:
    - Event tracking and logging
    - Decision recording
    - Data lineage tracking
    - Compliance audit support
    - Export capabilities
    - Search and filtering
    """
    
    def __init__(self, storage_dir: str = "audit_trails"):
        """Initialize audit trail generator.
        
        Args:
            storage_dir: Directory for storing audit trails
        """
        self.logger = logger.bind(component="AuditTrail")
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Active audit trails
        self._active_trails: Dict[str, AuditTrail] = {}
        
        # Event counter
        self._event_counter = 0
        
        self.logger.info("Audit Trail Generator initialized")
    
    def start_audit_trail(
        self,
        workflow_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new audit trail for a workflow.
        
        Args:
            workflow_id: Workflow ID
            metadata: Optional metadata
            
        Returns:
            Trail ID
        """
        trail_id = f"TRAIL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{workflow_id}"
        
        audit_trail = AuditTrail(
            trail_id=trail_id,
            workflow_id=workflow_id,
            started_at=datetime.now().isoformat(),
            summary={'metadata': metadata or {}}
        )
        
        self._active_trails[trail_id] = audit_trail
        
        # Log workflow start event
        self.log_event(
            trail_id=trail_id,
            event_type=AuditEventType.WORKFLOW_STARTED,
            severity=AuditSeverity.INFO,
            component="Orchestrator",
            description=f"Workflow {workflow_id} started",
            details=metadata or {}
        )
        
        self.logger.info(
            "Audit trail started",
            trail_id=trail_id,
            workflow_id=workflow_id
        )
        
        return trail_id
    
    def log_event(
        self,
        trail_id: str,
        event_type: AuditEventType,
        severity: AuditSeverity,
        component: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        related_events: Optional[List[str]] = None,
        agent_id: Optional[str] = None
    ) -> str:
        """Log an audit event.
        
        Args:
            trail_id: Audit trail ID
            event_type: Type of event
            severity: Event severity
            component: Component generating event
            description: Event description
            details: Additional details
            related_events: Related event IDs
            agent_id: Agent ID if applicable
            
        Returns:
            Event ID
        """
        if trail_id not in self._active_trails:
            self.logger.warning(
                "Trail not found",
                trail_id=trail_id
            )
            return ""
        
        # Generate event ID
        self._event_counter += 1
        event_id = f"EVT-{self._event_counter:06d}"
        
        # Create event
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now().isoformat(),
            component=component,
            description=description,
            details=details or {},
            related_events=related_events or [],
            workflow_id=self._active_trails[trail_id].workflow_id,
            agent_id=agent_id
        )
        
        # Add to trail
        self._active_trails[trail_id].events.append(event)
        
        self.logger.debug(
            "Event logged",
            trail_id=trail_id,
            event_id=event_id,
            event_type=event_type.value
        )
        
        return event_id
    
    def log_agent_start(
        self,
        trail_id: str,
        agent_name: str,
        agent_id: str,
        input_data: Dict[str, Any]
    ) -> str:
        """Log agent start event.
        
        Args:
            trail_id: Audit trail ID
            agent_name: Agent name
            agent_id: Agent ID
            input_data: Input data (will be sanitized)
            
        Returns:
            Event ID
        """
        return self.log_event(
            trail_id=trail_id,
            event_type=AuditEventType.AGENT_STARTED,
            severity=AuditSeverity.INFO,
            component=agent_name,
            description=f"Agent {agent_name} started processing",
            details={
                'agent_id': agent_id,
                'input_keys': list(input_data.keys()) if isinstance(input_data, dict) else []
            },
            agent_id=agent_id
        )
    
    def log_agent_completion(
        self,
        trail_id: str,
        agent_name: str,
        agent_id: str,
        output_data: Dict[str, Any],
        execution_time: float
    ) -> str:
        """Log agent completion event.
        
        Args:
            trail_id: Audit trail ID
            agent_name: Agent name
            agent_id: Agent ID
            output_data: Output data (will be sanitized)
            execution_time: Execution time in seconds
            
        Returns:
            Event ID
        """
        return self.log_event(
            trail_id=trail_id,
            event_type=AuditEventType.AGENT_COMPLETED,
            severity=AuditSeverity.INFO,
            component=agent_name,
            description=f"Agent {agent_name} completed successfully",
            details={
                'agent_id': agent_id,
                'execution_time': execution_time,
                'output_keys': list(output_data.keys()) if isinstance(output_data, dict) else []
            },
            agent_id=agent_id
        )
    
    def log_agent_failure(
        self,
        trail_id: str,
        agent_name: str,
        agent_id: str,
        error_message: str,
        execution_time: float
    ) -> str:
        """Log agent failure event.
        
        Args:
            trail_id: Audit trail ID
            agent_name: Agent name
            agent_id: Agent ID
            error_message: Error message
            execution_time: Execution time in seconds
            
        Returns:
            Event ID
        """
        return self.log_event(
            trail_id=trail_id,
            event_type=AuditEventType.AGENT_FAILED,
            severity=AuditSeverity.ERROR,
            component=agent_name,
            description=f"Agent {agent_name} failed",
            details={
                'agent_id': agent_id,
                'error_message': error_message,
                'execution_time': execution_time
            },
            agent_id=agent_id
        )
    
    def log_decision(
        self,
        trail_id: str,
        component: str,
        decision: str,
        rationale: str,
        alternatives: Optional[List[str]] = None,
        data_used: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a decision point.
        
        Args:
            trail_id: Audit trail ID
            component: Component making decision
            decision: Decision made
            rationale: Rationale for decision
            alternatives: Alternative options considered
            data_used: Data used for decision
            
        Returns:
            Event ID
        """
        return self.log_event(
            trail_id=trail_id,
            event_type=AuditEventType.DECISION_MADE,
            severity=AuditSeverity.INFO,
            component=component,
            description=f"Decision made: {decision}",
            details={
                'decision': decision,
                'rationale': rationale,
                'alternatives': alternatives or [],
                'data_used_keys': list(data_used.keys()) if data_used else []
            }
        )
    
    def log_validation(
        self,
        trail_id: str,
        component: str,
        validation_type: str,
        is_valid: bool,
        score: float,
        issues: List[str]
    ) -> str:
        """Log validation result.
        
        Args:
            trail_id: Audit trail ID
            component: Component performing validation
            validation_type: Type of validation
            is_valid: Whether data is valid
            score: Validation score
            issues: List of issues found
            
        Returns:
            Event ID
        """
        return self.log_event(
            trail_id=trail_id,
            event_type=AuditEventType.DATA_VALIDATED,
            severity=AuditSeverity.WARNING if not is_valid else AuditSeverity.INFO,
            component=component,
            description=f"Validation completed: {validation_type}",
            details={
                'validation_type': validation_type,
                'is_valid': is_valid,
                'score': score,
                'issue_count': len(issues),
                'issues': issues[:10]  # Limit to first 10
            }
        )
    
    def log_document_generation(
        self,
        trail_id: str,
        document_type: str,
        document_id: str,
        file_path: str
    ) -> str:
        """Log document generation.
        
        Args:
            trail_id: Audit trail ID
            document_type: Type of document
            document_id: Document ID
            file_path: Path to generated file
            
        Returns:
            Event ID
        """
        return self.log_event(
            trail_id=trail_id,
            event_type=AuditEventType.DOCUMENT_GENERATED,
            severity=AuditSeverity.INFO,
            component="DocumentGenerator",
            description=f"Document generated: {document_type}",
            details={
                'document_type': document_type,
                'document_id': document_id,
                'file_path': file_path
            }
        )
    
    def complete_audit_trail(
        self,
        trail_id: str,
        success: bool,
        final_summary: Optional[Dict[str, Any]] = None
    ):
        """Complete an audit trail.
        
        Args:
            trail_id: Audit trail ID
            success: Whether workflow succeeded
            final_summary: Final summary data
        """
        if trail_id not in self._active_trails:
            self.logger.warning("Trail not found", trail_id=trail_id)
            return
        
        trail = self._active_trails[trail_id]
        trail.completed_at = datetime.now().isoformat()
        
        # Update summary
        trail.summary.update({
            'success': success,
            'total_events': len(trail.events),
            'event_types': self._count_event_types(trail.events),
            'severity_counts': self._count_severities(trail.events),
            'total_duration': self._calculate_duration(trail),
            **(final_summary or {})
        })
        
        # Log completion event
        self.log_event(
            trail_id=trail_id,
            event_type=AuditEventType.WORKFLOW_COMPLETED if success else AuditEventType.WORKFLOW_FAILED,
            severity=AuditSeverity.INFO if success else AuditSeverity.ERROR,
            component="Orchestrator",
            description=f"Workflow {'completed successfully' if success else 'failed'}",
            details=trail.summary
        )
        
        # Save trail
        self._save_trail(trail)
        
        # Remove from active trails
        del self._active_trails[trail_id]
        
        self.logger.info(
            "Audit trail completed",
            trail_id=trail_id,
            success=success,
            total_events=len(trail.events)
        )
    
    def _count_event_types(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Count events by type."""
        counts = {}
        for event in events:
            event_type = event.event_type.value
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts
    
    def _count_severities(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Count events by severity."""
        counts = {}
        for event in events:
            severity = event.severity.value
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def _calculate_duration(self, trail: AuditTrail) -> float:
        """Calculate trail duration in seconds."""
        if not trail.completed_at:
            return 0.0
        
        start = datetime.fromisoformat(trail.started_at)
        end = datetime.fromisoformat(trail.completed_at)
        return (end - start).total_seconds()
    
    def _save_trail(self, trail: AuditTrail):
        """Save audit trail to file."""
        filename = f"{trail.trail_id}.json"
        filepath = self.storage_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(trail.to_dict(), f, indent=2)
        
        self.logger.info(f"Audit trail saved: {filepath}")
    
    def load_trail(self, trail_id: str) -> Optional[AuditTrail]:
        """Load audit trail from file.
        
        Args:
            trail_id: Trail ID
            
        Returns:
            AuditTrail or None
        """
        filename = f"{trail_id}.json"
        filepath = self.storage_dir / filename
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Reconstruct trail (simplified)
        trail = AuditTrail(
            trail_id=data['trail_id'],
            workflow_id=data['workflow_id'],
            started_at=data['started_at'],
            completed_at=data.get('completed_at'),
            summary=data.get('summary', {})
        )
        
        return trail
    
    def generate_audit_report(
        self,
        trail_id: str,
        include_details: bool = True
    ) -> str:
        """Generate human-readable audit report.
        
        Args:
            trail_id: Trail ID
            include_details: Include detailed events
            
        Returns:
            Formatted report string
        """
        # Try to get from active or load from file
        trail = self._active_trails.get(trail_id)
        if not trail:
            trail = self.load_trail(trail_id)
        
        if not trail:
            return f"Audit trail {trail_id} not found"
        
        report = f"""
AUDIT TRAIL REPORT
==================

Trail ID: {trail.trail_id}
Workflow ID: {trail.workflow_id}
Started: {trail.started_at}
Completed: {trail.completed_at or 'In Progress'}

SUMMARY:
--------
Total Events: {len(trail.events)}
Success: {trail.summary.get('success', 'Unknown')}
"""
        
        if 'event_types' in trail.summary:
            report += "\nEvent Types:\n"
            for event_type, count in trail.summary['event_types'].items():
                report += f"  {event_type}: {count}\n"
        
        if 'severity_counts' in trail.summary:
            report += "\nSeverity Counts:\n"
            for severity, count in trail.summary['severity_counts'].items():
                report += f"  {severity}: {count}\n"
        
        if include_details:
            report += "\n\nDETAILED EVENTS:\n"
            report += "="*50 + "\n"
            
            for event in trail.events:
                report += f"\n[{event.timestamp}] {event.event_type.value}\n"
                report += f"  Component: {event.component}\n"
                report += f"  Severity: {event.severity.value}\n"
                report += f"  Description: {event.description}\n"
                if event.agent_id:
                    report += f"  Agent: {event.agent_id}\n"
        
        return report
    
    def search_events(
        self,
        trail_id: str,
        event_type: Optional[AuditEventType] = None,
        component: Optional[str] = None,
        severity: Optional[AuditSeverity] = None
    ) -> List[AuditEvent]:
        """Search events in audit trail.
        
        Args:
            trail_id: Trail ID
            event_type: Filter by event type
            component: Filter by component
            severity: Filter by severity
            
        Returns:
            Filtered list of events
        """
        trail = self._active_trails.get(trail_id)
        if not trail:
            trail = self.load_trail(trail_id)
        
        if not trail:
            return []
        
        events = trail.events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if component:
            events = [e for e in events if e.component == component]
        
        if severity:
            events = [e for e in events if e.severity == severity]
        
        return events
