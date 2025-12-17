"""
Enhanced Main Orchestrator - Integrates All Components
Comprehensive orchestration system with full feature support.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import structlog

from agents.orchestrator.agent_registry import (
    AgentRegistry, AgentType, AgentCapability, get_global_registry
)
from agents.orchestrator.message_queue import (
    AgentMessageQueue, MessagePriority, get_global_message_queue
)
from agents.orchestrator.communication_protocol import (
    AgentCommunicationProtocol, ProtocolMessageType, get_global_protocol
)
from agents.orchestrator.quality_validation import QualityValidationSystem
from agents.orchestrator.context_summarization import (
    ContextAwareSummarizer, AudienceRole
)
from agents.orchestrator.pdf_generator import (
    PDFReportGenerator, DetailedResponseCompiler
)
from agents.orchestrator.audit_trail import (
    AuditTrailGenerator, AuditEventType, AuditSeverity
)
from agents.orchestrator.main_orchestrator import (
    MainOrchestrator, WorkflowStatus, AgentStatus, WorkflowState, RFPResponse
)

logger = structlog.get_logger()


class EnhancedMainOrchestrator(MainOrchestrator):
    """
    Enhanced Main Orchestrator
    
    Extends MainOrchestrator with:
    - Agent registry integration
    - Message queue system
    - Communication protocol
    - Quality validation
    - Context-aware summarization
    - PDF report generation
    - Audit trail tracking
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        use_global_registry: bool = True,
        output_dir: str = "orchestrator_outputs"
    ):
        """Initialize Enhanced Main Orchestrator.
        
        Args:
            config: Configuration dictionary
            use_global_registry: Use global agent registry
            output_dir: Output directory for generated files
        """
        super().__init__(config)
        
        self.logger = logger.bind(component="EnhancedOrchestrator")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize subsystems
        self.agent_registry = get_global_registry() if use_global_registry else AgentRegistry()
        self.message_queue = get_global_message_queue()
        self.protocol = get_global_protocol()
        self.quality_validator = QualityValidationSystem()
        self.summarizer = ContextAwareSummarizer()
        self.pdf_generator = PDFReportGenerator(
            output_dir=str(self.output_dir / "pdf_reports")
        )
        self.response_compiler = DetailedResponseCompiler()
        self.audit_generator = AuditTrailGenerator(
            storage_dir=str(self.output_dir / "audit_trails")
        )
        
        self.logger.info("Enhanced Main Orchestrator initialized")
    
    def register_agent_with_registry(
        self,
        agent_instance: Any,
        agent_name: str,
        agent_type: AgentType,
        capabilities: List[AgentCapability],
        priority: int = 100
    ) -> str:
        """Register agent in registry and setup message queue.
        
        Args:
            agent_instance: Agent instance
            agent_name: Agent name
            agent_type: Agent type
            capabilities: List of capabilities
            priority: Agent priority
            
        Returns:
            Agent ID
        """
        agent_id = self.agent_registry.register_agent(
            agent_instance=agent_instance,
            agent_name=agent_name,
            agent_type=agent_type,
            capabilities=capabilities,
            priority=priority,
            description=f"{agent_name} - {agent_type.value}"
        )
        
        # Setup message queue for agent
        self.message_queue.register_agent_queue(agent_id)
        
        self.logger.info(
            "Agent registered",
            agent_id=agent_id,
            agent_name=agent_name
        )
        
        return agent_id
    
    def process_rfp_enhanced(
        self,
        rfp_document: Dict[str, Any],
        customer_info: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, WorkflowState, Optional[RFPResponse], Dict[str, Any]]:
        """Process RFP with enhanced features.
        
        Args:
            rfp_document: RFP document content
            customer_info: Customer information
            options: Processing options
            
        Returns:
            Tuple of (success, workflow_state, rfp_response, enhanced_data)
        """
        options = options or {}
        rfp_id = rfp_document.get('rfp_id', f"RFP-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        
        # Start audit trail
        trail_id = self.audit_generator.start_audit_trail(
            workflow_id=rfp_id,
            metadata={
                'customer': customer_info.get('name'),
                'rfp_type': rfp_document.get('type')
            }
        )
        
        try:
            # Run standard workflow
            success, workflow_state, rfp_response = self.process_rfp(
                rfp_document,
                customer_info,
                options
            )
            
            if not success:
                self.audit_generator.complete_audit_trail(trail_id, False)
                return False, workflow_state, None, {}
            
            # Enhanced processing
            consolidated_data = workflow_state.consolidated_response
            
            # Quality validation
            self.audit_generator.log_event(
                trail_id=trail_id,
                event_type=AuditEventType.DATA_VALIDATED,
                severity=AuditSeverity.INFO,
                component="QualityValidator",
                description="Starting quality validation"
            )
            
            validation_result = self.quality_validator.validate_rfp_response(
                rfp_response.__dict__ if hasattr(rfp_response, '__dict__') else rfp_response,
                consolidated_data
            )
            
            self.audit_generator.log_validation(
                trail_id=trail_id,
                component="QualityValidator",
                validation_type="rfp_response",
                is_valid=validation_result.is_valid,
                score=validation_result.score,
                issues=[issue.message for issue in validation_result.issues]
            )
            
            # Generate role-specific summaries
            role_summaries = {}
            for role in AudienceRole:
                formatted_response = self.summarizer.format_for_audience(
                    consolidated_data,
                    role,
                    customer_info
                )
                role_summaries[role.value] = formatted_response
            
            # Compile detailed response
            detailed_response = self.response_compiler.compile_detailed_response(
                rfp_response.__dict__ if hasattr(rfp_response, '__dict__') else rfp_response,
                consolidated_data,
                workflow_state.__dict__ if hasattr(workflow_state, '__dict__') else workflow_state
            )
            
            # Generate PDF report (if enabled)
            pdf_path = None
            if self.pdf_generator.enabled and options.get('generate_pdf', True):
                try:
                    pdf_path = self.pdf_generator.generate_rfp_response_pdf(
                        rfp_response.__dict__ if hasattr(rfp_response, '__dict__') else rfp_response,
                        consolidated_data
                    )
                    
                    self.audit_generator.log_document_generation(
                        trail_id=trail_id,
                        document_type="PDF Report",
                        document_id=rfp_response.response_id if hasattr(rfp_response, 'response_id') else 'unknown',
                        file_path=pdf_path
                    )
                except Exception as e:
                    self.logger.warning(f"PDF generation failed: {e}")
            
            # Complete audit trail
            self.audit_generator.complete_audit_trail(
                trail_id=trail_id,
                success=True,
                final_summary={
                    'rfp_id': rfp_id,
                    'response_id': rfp_response.response_id if hasattr(rfp_response, 'response_id') else 'unknown',
                    'validation_score': validation_result.score,
                    'validation_issues': len(validation_result.issues),
                    'pdf_generated': pdf_path is not None
                }
            )
            
            # Generate audit report
            audit_report = self.audit_generator.generate_audit_report(
                trail_id=trail_id,
                include_details=options.get('detailed_audit', False)
            )
            
            # Compile enhanced data
            enhanced_data = {
                'validation_result': {
                    'is_valid': validation_result.is_valid,
                    'score': validation_result.score,
                    'issues': [
                        {
                            'category': issue.category.value,
                            'severity': issue.severity.value,
                            'message': issue.message,
                            'field': issue.field
                        }
                        for issue in validation_result.issues
                    ]
                },
                'role_summaries': {
                    role: {
                        'summary': formatted.summary[:500],  # Truncate for response
                        'key_points': formatted.key_points,
                        'recommendations': formatted.recommendations
                    }
                    for role, formatted in role_summaries.items()
                },
                'detailed_response': detailed_response,
                'audit_trail_id': trail_id,
                'audit_report': audit_report,
                'pdf_report_path': pdf_path,
                'registry_status': self.agent_registry.get_registry_status(),
                'queue_stats': self.message_queue.get_statistics()
            }
            
            self.logger.info(
                "Enhanced RFP processing completed",
                rfp_id=rfp_id,
                validation_score=validation_result.score,
                pdf_generated=pdf_path is not None
            )
            
            return True, workflow_state, rfp_response, enhanced_data
            
        except Exception as e:
            self.logger.error(
                "Enhanced RFP processing failed",
                rfp_id=rfp_id,
                error=str(e),
                exc_info=True
            )
            
            self.audit_generator.log_event(
                trail_id=trail_id,
                event_type=AuditEventType.ERROR_OCCURRED,
                severity=AuditSeverity.CRITICAL,
                component="EnhancedOrchestrator",
                description=f"Processing failed: {str(e)}"
            )
            
            self.audit_generator.complete_audit_trail(trail_id, False)
            
            return False, workflow_state, None, {}
    
    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics.
        
        Returns:
            Enhanced statistics dictionary
        """
        base_stats = self.get_statistics()
        
        return {
            'orchestrator_stats': base_stats,
            'registry_stats': self.agent_registry.get_registry_status(),
            'queue_stats': self.message_queue.get_statistics(),
            'active_workflows': len(self.workflows),
            'registered_agents': self.agent_registry.active_agents
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check.
        
        Returns:
            Health check results
        """
        health_results = self.agent_registry.perform_health_checks()
        
        return {
            'status': 'healthy' if all(health_results.values()) else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'agent_health': health_results,
            'registry_active': self.agent_registry.active_agents > 0,
            'queue_operational': True,
            'statistics': self.get_enhanced_statistics()
        }
