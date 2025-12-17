"""Workflow templates, branching, and advanced features."""
import asyncio
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class WorkflowTemplateType(Enum):
    """Predefined workflow template types."""
    STANDARD_RFP = "standard_rfp"
    FAST_TRACK_RFP = "fast_track_rfp"
    COMPLEX_RFP = "complex_rfp"
    SIMPLE_QUOTE = "simple_quote"
    CUSTOM = "custom"


class BranchCondition(Enum):
    """Conditions for workflow branching."""
    SKIP_IF_LOW_VALUE = "skip_if_low_value"
    SKIP_IF_STANDARD_PRODUCT = "skip_if_standard_product"
    REQUIRES_APPROVAL = "requires_approval"
    FAST_TRACK = "fast_track"
    COMPLEX_VALIDATION = "complex_validation"


@dataclass
class StageConfig:
    """Configuration for a workflow stage."""
    stage_name: str
    agent_id: str
    timeout: float
    required: bool = True
    skip_conditions: List[BranchCondition] = field(default_factory=list)
    approval_required: bool = False
    approval_roles: List[str] = field(default_factory=list)
    parallel_with: List[str] = field(default_factory=list)


@dataclass
class WorkflowTemplate:
    """Template defining a complete workflow."""
    template_id: str
    name: str
    description: str
    stages: List[StageConfig]
    estimated_duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalRequest:
    """Request for human approval."""
    approval_id: str
    workflow_id: str
    stage_name: str
    requested_at: datetime
    required_roles: List[str]
    context_data: Dict[str, Any]
    status: str = "pending"  # pending, approved, rejected
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


class TimeEstimator:
    """Estimates workflow completion times based on historical data."""
    
    def __init__(self):
        self.stage_history: Dict[str, List[float]] = {}
        self.workflow_history: List[float] = []
        logger.info("Initialized TimeEstimator")
    
    def record_stage_time(self, stage_name: str, duration: float):
        """Record actual stage execution time."""
        if stage_name not in self.stage_history:
            self.stage_history[stage_name] = []
        self.stage_history[stage_name].append(duration)
        # Keep last 100 records
        if len(self.stage_history[stage_name]) > 100:
            self.stage_history[stage_name] = self.stage_history[stage_name][-100:]
    
    def record_workflow_time(self, duration: float):
        """Record total workflow execution time."""
        self.workflow_history.append(duration)
        if len(self.workflow_history) > 100:
            self.workflow_history = self.workflow_history[-100:]
    
    def estimate_stage_time(self, stage_name: str) -> float:
        """Estimate time for a stage based on history."""
        if stage_name not in self.stage_history or not self.stage_history[stage_name]:
            return 1.0  # Default 1 second
        
        times = self.stage_history[stage_name]
        # Use 90th percentile for conservative estimate
        sorted_times = sorted(times)
        p90_index = int(len(sorted_times) * 0.9)
        return sorted_times[p90_index]
    
    def estimate_workflow_time(self, stage_names: List[str]) -> float:
        """Estimate total workflow time."""
        if self.workflow_history:
            sorted_times = sorted(self.workflow_history)
            p90_index = int(len(sorted_times) * 0.9)
            return sorted_times[p90_index]
        
        # Fallback to sum of stage estimates
        return sum(self.estimate_stage_time(name) for name in stage_names)
    
    def get_confidence_level(self, stage_name: str) -> float:
        """Get confidence level for estimate (0.0 - 1.0)."""
        if stage_name not in self.stage_history:
            return 0.0
        
        count = len(self.stage_history[stage_name])
        # More data = higher confidence
        return min(1.0, count / 20.0)


class WorkflowVisualizer:
    """Creates visual representations of workflow execution."""
    
    @staticmethod
    def generate_ascii_flow(stages: List[str], current_stage: Optional[str] = None,
                           completed_stages: List[str] = None) -> str:
        """Generate ASCII art workflow visualization."""
        completed_stages = completed_stages or []
        lines = []
        
        lines.append("┌" + "─" * 60 + "┐")
        lines.append("│" + "WORKFLOW EXECUTION FLOW".center(60) + "│")
        lines.append("└" + "─" * 60 + "┘")
        lines.append("")
        
        for i, stage in enumerate(stages):
            # Determine stage status
            if stage in completed_stages:
                status = "✓"
                marker = "●"
            elif stage == current_stage:
                status = "→"
                marker = "◉"
            else:
                status = " "
                marker = "○"
            
            # Stage box
            stage_display = f"{i+1}. {stage.upper().replace('_', ' ')}"
            lines.append(f"  {marker} [{status}] {stage_display}")
            
            # Connector
            if i < len(stages) - 1:
                lines.append("      │")
                lines.append("      ↓")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_mermaid_diagram(stages: List[str], 
                                completed_stages: List[str] = None,
                                failed_stage: Optional[str] = None) -> str:
        """Generate Mermaid diagram syntax."""
        completed_stages = completed_stages or []
        lines = ["graph TD"]
        lines.append("    Start([Start]) --> Stage1")
        
        for i, stage in enumerate(stages):
            stage_id = f"Stage{i+1}"
            next_stage_id = f"Stage{i+2}" if i < len(stages) - 1 else "End"
            
            # Node style based on status
            if stage in completed_stages:
                node_style = f"{stage_id}[✓ {stage.replace('_', ' ').title()}]"
                lines.append(f"    {node_style}")
                lines.append(f"    style {stage_id} fill:#90EE90")
            elif stage == failed_stage:
                node_style = f"{stage_id}[✗ {stage.replace('_', ' ').title()}]"
                lines.append(f"    {node_style}")
                lines.append(f"    style {stage_id} fill:#FFB6C6")
            else:
                node_style = f"{stage_id}[{stage.replace('_', ' ').title()}]"
                lines.append(f"    {node_style}")
            
            # Connection
            if i < len(stages) - 1:
                lines.append(f"    {stage_id} --> {next_stage_id}")
        
        lines.append(f"    Stage{len(stages)} --> End([End])")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_timeline(stage_results: Dict[str, Any]) -> str:
        """Generate timeline visualization of stage execution."""
        lines = []
        lines.append("┌" + "─" * 70 + "┐")
        lines.append("│" + "EXECUTION TIMELINE".center(70) + "│")
        lines.append("└" + "─" * 70 + "┘")
        lines.append("")
        
        total_time = sum(r.get('duration', 0) for r in stage_results.values())
        
        for stage_name, result in stage_results.items():
            duration = result.get('duration', 0)
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            
            # Progress bar
            bar_length = int(percentage / 2)  # Scale to 50 chars max
            bar = "█" * bar_length + "░" * (50 - bar_length)
            
            lines.append(f"{stage_name:25} │{bar}│ {duration:.2f}s ({percentage:.1f}%)")
        
        lines.append("")
        lines.append(f"{'TOTAL TIME':25} │{'█' * 50}│ {total_time:.2f}s (100%)")
        
        return "\n".join(lines)


class ApprovalManager:
    """Manages human-in-the-loop approval workflows."""
    
    def __init__(self):
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.approval_callbacks: Dict[str, asyncio.Future] = {}
        logger.info("Initialized ApprovalManager")
    
    async def request_approval(self, workflow_id: str, stage_name: str,
                              required_roles: List[str],
                              context_data: Dict[str, Any],
                              timeout: Optional[float] = None) -> bool:
        """Request human approval for workflow continuation."""
        approval_id = f"approval_{workflow_id}_{stage_name}"
        
        approval_request = ApprovalRequest(
            approval_id=approval_id,
            workflow_id=workflow_id,
            stage_name=stage_name,
            requested_at=datetime.utcnow(),
            required_roles=required_roles,
            context_data=context_data
        )
        
        self.pending_approvals[approval_id] = approval_request
        
        # Create future for approval
        future = asyncio.Future()
        self.approval_callbacks[approval_id] = future
        
        logger.info("Approval requested",
                   approval_id=approval_id,
                   stage=stage_name,
                   roles=required_roles)
        
        try:
            # Wait for approval with timeout
            if timeout:
                approved = await asyncio.wait_for(future, timeout=timeout)
            else:
                approved = await future
            
            return approved
            
        except asyncio.TimeoutError:
            logger.warning("Approval timeout", approval_id=approval_id)
            approval_request.status = "timeout"
            return False
    
    def approve(self, approval_id: str, approver: str) -> bool:
        """Approve a pending request."""
        if approval_id not in self.pending_approvals:
            return False
        
        approval = self.pending_approvals[approval_id]
        approval.status = "approved"
        approval.approved_by = approver
        approval.approved_at = datetime.utcnow()
        
        # Resolve future
        if approval_id in self.approval_callbacks:
            future = self.approval_callbacks[approval_id]
            if not future.done():
                future.set_result(True)
        
        logger.info("Approval granted",
                   approval_id=approval_id,
                   approver=approver)
        
        return True
    
    def reject(self, approval_id: str, approver: str, reason: str) -> bool:
        """Reject a pending request."""
        if approval_id not in self.pending_approvals:
            return False
        
        approval = self.pending_approvals[approval_id]
        approval.status = "rejected"
        approval.approved_by = approver
        approval.approved_at = datetime.utcnow()
        approval.rejection_reason = reason
        
        # Resolve future
        if approval_id in self.approval_callbacks:
            future = self.approval_callbacks[approval_id]
            if not future.done():
                future.set_result(False)
        
        logger.warning("Approval rejected",
                      approval_id=approval_id,
                      approver=approver,
                      reason=reason)
        
        return True
    
    def get_pending_approvals(self, workflow_id: Optional[str] = None) -> List[ApprovalRequest]:
        """Get pending approval requests."""
        approvals = list(self.pending_approvals.values())
        
        if workflow_id:
            approvals = [a for a in approvals if a.workflow_id == workflow_id]
        
        return [a for a in approvals if a.status == "pending"]


class WorkflowTemplateManager:
    """Manages workflow templates."""
    
    def __init__(self):
        self.templates: Dict[str, WorkflowTemplate] = {}
        self._initialize_default_templates()
        logger.info("Initialized WorkflowTemplateManager")
    
    def _initialize_default_templates(self):
        """Create default workflow templates."""
        
        # Standard RFP workflow
        standard_rfp = WorkflowTemplate(
            template_id="standard_rfp",
            name="Standard RFP Processing",
            description="Complete RFP processing with all validation steps",
            stages=[
                StageConfig("parsing", "rfp_parser_agent", 60.0),
                StageConfig("sales_analysis", "sales_agent", 90.0),
                StageConfig("technical_validation", "technical_agent", 120.0),
                StageConfig("pricing_calculation", "pricing_agent", 60.0),
                StageConfig("response_generation", "response_generator_agent", 90.0),
            ],
            estimated_duration=7.0
        )
        
        # Fast track for simple quotes
        fast_track = WorkflowTemplate(
            template_id="fast_track_rfp",
            name="Fast Track RFP",
            description="Expedited processing for standard products",
            stages=[
                StageConfig("parsing", "rfp_parser_agent", 30.0),
                StageConfig("sales_analysis", "sales_agent", 45.0),
                StageConfig("technical_validation", "technical_agent", 60.0,
                          skip_conditions=[BranchCondition.SKIP_IF_STANDARD_PRODUCT]),
                StageConfig("pricing_calculation", "pricing_agent", 30.0),
                StageConfig("response_generation", "response_generator_agent", 45.0),
            ],
            estimated_duration=3.5
        )
        
        # Complex RFP with approvals
        complex_rfp = WorkflowTemplate(
            template_id="complex_rfp",
            name="Complex RFP with Approvals",
            description="Detailed processing with manual approval checkpoints",
            stages=[
                StageConfig("parsing", "rfp_parser_agent", 90.0),
                StageConfig("sales_analysis", "sales_agent", 120.0,
                          approval_required=True,
                          approval_roles=["sales_manager"]),
                StageConfig("technical_validation", "technical_agent", 180.0,
                          approval_required=True,
                          approval_roles=["technical_lead", "compliance_officer"]),
                StageConfig("pricing_calculation", "pricing_agent", 90.0,
                          approval_required=True,
                          approval_roles=["pricing_manager"]),
                StageConfig("response_generation", "response_generator_agent", 120.0),
            ],
            estimated_duration=12.0
        )
        
        # Simple quote
        simple_quote = WorkflowTemplate(
            template_id="simple_quote",
            name="Simple Quote Generation",
            description="Basic quote for standard products without technical validation",
            stages=[
                StageConfig("parsing", "rfp_parser_agent", 30.0),
                StageConfig("sales_analysis", "sales_agent", 45.0),
                StageConfig("pricing_calculation", "pricing_agent", 30.0),
                StageConfig("response_generation", "response_generator_agent", 30.0),
            ],
            estimated_duration=2.5
        )
        
        self.templates[standard_rfp.template_id] = standard_rfp
        self.templates[fast_track.template_id] = fast_track
        self.templates[complex_rfp.template_id] = complex_rfp
        self.templates[simple_quote.template_id] = simple_quote
    
    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get template by ID."""
        return self.templates.get(template_id)
    
    def create_template(self, template: WorkflowTemplate):
        """Register a new template."""
        self.templates[template.template_id] = template
        logger.info("Template created", template_id=template.template_id)
    
    def list_templates(self) -> List[WorkflowTemplate]:
        """List all available templates."""
        return list(self.templates.values())
    
    def select_template(self, rfp_data: Dict[str, Any]) -> str:
        """Auto-select best template based on RFP characteristics."""
        priority = rfp_data.get('priority', 'normal')
        complexity = rfp_data.get('complexity', 'standard')
        value = rfp_data.get('estimated_value', 0)
        
        # Selection logic
        if priority == 'urgent' and complexity == 'simple':
            return "fast_track_rfp"
        elif complexity == 'complex' or value > 1000000:
            return "complex_rfp"
        elif complexity == 'simple' and value < 50000:
            return "simple_quote"
        else:
            return "standard_rfp"


class ConditionalRouter:
    """Handles conditional branching in workflows."""
    
    @staticmethod
    def should_skip_stage(stage_config: StageConfig, 
                         context_data: Dict[str, Any]) -> bool:
        """Determine if stage should be skipped based on conditions."""
        if not stage_config.skip_conditions:
            return False
        
        for condition in stage_config.skip_conditions:
            if condition == BranchCondition.SKIP_IF_LOW_VALUE:
                value = context_data.get('estimated_value', 0)
                if value < 10000:
                    return True
            
            elif condition == BranchCondition.SKIP_IF_STANDARD_PRODUCT:
                is_standard = context_data.get('is_standard_product', False)
                if is_standard:
                    return True
            
            elif condition == BranchCondition.FAST_TRACK:
                priority = context_data.get('priority', 'normal')
                if priority == 'urgent':
                    return True
        
        return False
    
    @staticmethod
    def get_next_stages(current_stage: str,
                       all_stages: List[StageConfig],
                       context_data: Dict[str, Any]) -> List[str]:
        """Determine next stages to execute (supports parallel execution)."""
        current_idx = next((i for i, s in enumerate(all_stages) 
                           if s.stage_name == current_stage), -1)
        
        if current_idx == -1 or current_idx >= len(all_stages) - 1:
            return []
        
        next_stages = []
        for i in range(current_idx + 1, len(all_stages)):
            stage = all_stages[i]
            
            # Skip if conditions met
            if ConditionalRouter.should_skip_stage(stage, context_data):
                logger.info("Stage skipped", stage=stage.stage_name, 
                          conditions=stage.skip_conditions)
                continue
            
            next_stages.append(stage.stage_name)
            
            # Check if next stage runs in parallel
            if not stage.parallel_with:
                break
        
        return next_stages if next_stages else []
