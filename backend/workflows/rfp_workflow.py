"""End-to-End RFP Processing Workflow.

Complete workflow from RFP identification to final response generation,
including all agent interactions, data flows, and error handling.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
import structlog

from agents.communication import CommunicationManager
from agents.communication.communication_manager import AgentMessage, AgentMessageType
from workflows.workflow_extensions import (
    TimeEstimator, WorkflowVisualizer, ApprovalManager,
    WorkflowTemplateManager, ConditionalRouter
)

logger = structlog.get_logger()


class WorkflowStage(Enum):
    """Stages in RFP processing workflow."""
    RECEIVED = "received"
    PARSING = "parsing"
    SALES_ANALYSIS = "sales_analysis"
    TECHNICAL_VALIDATION = "technical_validation"
    PRICING_CALCULATION = "pricing_calculation"
    RESPONSE_GENERATION = "response_generation"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStatus(Enum):
    """Status of workflow execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StageResult:
    """Result from a workflow stage."""
    stage: WorkflowStage
    status: str
    data: Dict[str, Any]
    error: Optional[str] = None
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowContext:
    """Context maintained throughout workflow execution."""
    workflow_id: str
    rfp_id: str
    customer_id: str
    current_stage: WorkflowStage
    status: WorkflowStatus
    stage_results: Dict[WorkflowStage, StageResult] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RFPWorkflowOrchestrator:
    """Orchestrates complete RFP processing workflow."""
    
    def __init__(self, comm_manager: CommunicationManager,
                 enable_approvals: bool = False,
                 enable_visualization: bool = True):
        self.comm_manager = comm_manager
        self.agent_id = "rfp_workflow_orchestrator"
        self.active_workflows: Dict[str, WorkflowContext] = {}
        
        # Advanced features
        self.time_estimator = TimeEstimator()
        self.visualizer = WorkflowVisualizer()
        self.approval_manager = ApprovalManager() if enable_approvals else None
        self.template_manager = WorkflowTemplateManager()
        self.enable_visualization = enable_visualization
        
        logger.info("Initialized RFPWorkflowOrchestrator",
                   approvals=enable_approvals,
                   visualization=enable_visualization)
    
    async def initialize(self):
        """Initialize orchestrator and register with communication system."""
        await self.comm_manager.register_agent(
            self.agent_id,
            "orchestrator",
            capabilities=[
                "workflow_management",
                "agent_coordination",
                "error_recovery"
            ]
        )
        
        # Register message handlers
        await self.comm_manager.register_handler(
            self.agent_id,
            "response",
            self._handle_agent_response
        )
        
        await self.comm_manager.register_handler(
            self.agent_id,
            "error",
            self._handle_agent_error
        )
        
        logger.info("RFPWorkflowOrchestrator initialized and registered")
    
    async def process_rfp(self, rfp_data: Dict[str, Any],
                         template_id: Optional[str] = None) -> Dict[str, Any]:
        """Process RFP through complete workflow.
        
        Args:
            rfp_data: Raw RFP data containing:
                - rfp_id: Unique identifier
                - customer_id: Customer identifier
                - document: RFP document content
                - deadline: Response deadline
                - priority: Request priority
                - template_id: Optional template to use
                
        Returns:
            Complete response with quote, compliance, and timeline
        """
        # Select template
        if not template_id:
            template_id = self.template_manager.select_template(rfp_data)
        
        template = self.template_manager.get_template(template_id)
        if not template:
            template_id = "standard_rfp"
            template = self.template_manager.get_template(template_id)
        
        # Initialize workflow context
        workflow_id = str(uuid.uuid4())
        context = WorkflowContext(
            workflow_id=workflow_id,
            rfp_id=rfp_data.get('rfp_id', 'unknown'),
            customer_id=rfp_data.get('customer_id', 'unknown'),
            current_stage=WorkflowStage.RECEIVED,
            status=WorkflowStatus.PENDING,
            metadata={
                'deadline': rfp_data.get('deadline'),
                'priority': rfp_data.get('priority', 'normal'),
                'source': rfp_data.get('source', 'manual'),
                'template_id': template_id,
                'template_name': template.name,
                'estimated_duration': self.time_estimator.estimate_workflow_time(
                    [s.stage_name for s in template.stages]
                )
            }
        )
        
        self.active_workflows[workflow_id] = context
        
        logger.info("Starting RFP workflow",
                   workflow_id=workflow_id,
                   rfp_id=context.rfp_id,
                   template=template_id,
                   estimated_duration=context.metadata['estimated_duration'])
        
        # Display visualization
        if self.enable_visualization:
            try:
                viz = self.visualizer.generate_ascii_flow(
                    [s.stage_name for s in template.stages]
                )
                print("\n" + viz + "\n", flush=True)
            except UnicodeEncodeError:
                # Skip visualization if terminal doesn't support Unicode
                logger.debug("Skipping visualization - terminal doesn't support Unicode")
        
        try:
            # Stage 1: RFP Identification & Parsing
            parsing_result = await self._stage_parsing(context, rfp_data)
            if parsing_result.status == "failed":
                return await self._handle_workflow_failure(context, parsing_result)
            
            # Stage 2: Sales Analysis
            sales_result = await self._stage_sales_analysis(context, parsing_result.data)
            if sales_result.status == "failed":
                return await self._handle_workflow_failure(context, sales_result)
            
            # Stage 3: Technical Validation
            technical_result = await self._stage_technical_validation(
                context,
                sales_result.data
            )
            if technical_result.status == "failed":
                return await self._handle_workflow_failure(context, technical_result)
            
            # Stage 4: Pricing Calculation
            pricing_result = await self._stage_pricing_calculation(
                context,
                sales_result.data,
                technical_result.data
            )
            if pricing_result.status == "failed":
                return await self._handle_workflow_failure(context, pricing_result)
            
            # Stage 5: Response Generation
            response_result = await self._stage_response_generation(
                context,
                parsing_result.data,
                sales_result.data,
                technical_result.data,
                pricing_result.data
            )
            if response_result.status == "failed":
                return await self._handle_workflow_failure(context, response_result)
            
            # Stage 6: Review & Finalization
            final_result = await self._stage_review(context, response_result.data)
            
            # Mark workflow as completed
            context.status = WorkflowStatus.COMPLETED
            context.current_stage = WorkflowStage.COMPLETED
            context.end_time = datetime.utcnow()
            
            # Broadcast completion
            await self.comm_manager.broadcast(
                self.agent_id,
                {
                    'event': 'workflow_completed',
                    'workflow_id': workflow_id,
                    'rfp_id': context.rfp_id,
                    'duration': (context.end_time - context.start_time).total_seconds()
                }
            )
            
            logger.info("RFP workflow completed",
                       workflow_id=workflow_id,
                       duration=(context.end_time - context.start_time).total_seconds())
            
            # Add workflow_info to result
            result = final_result.data.copy()
            result['workflow_info'] = {
                'workflow_id': workflow_id,
                'rfp_id': context.rfp_id,
                'customer_id': context.customer_id,
                'template_id': context.metadata.get('template_id'),
                'template_name': context.metadata.get('template_name'),
                'status': context.status.value,
                'estimated_duration': context.metadata.get('estimated_duration'),
                'actual_duration': (context.end_time - context.start_time).total_seconds()
            }
            
            return result
            
        except Exception as e:
            logger.error("Workflow execution failed",
                        workflow_id=workflow_id,
                        error=str(e))
            context.status = WorkflowStatus.FAILED
            context.errors.append(str(e))
            return await self._handle_workflow_failure(context, None)
    
    async def _stage_parsing(self, context: WorkflowContext, 
                            rfp_data: Dict[str, Any]) -> StageResult:
        """Stage 1: Parse and extract RFP content."""
        import time
        start_time = time.time()
        
        context.current_stage = WorkflowStage.PARSING
        await self.comm_manager.set_agent_state(
            self.agent_id,
            "current_stage",
            WorkflowStage.PARSING.value
        )
        
        logger.info("Stage 1: Parsing RFP", workflow_id=context.workflow_id)
        
        try:
            # Request parsing agent to process document
            response = await self.comm_manager.send_request(
                sender=self.agent_id,
                recipient="rfp_parser_agent",
                payload={
                    'workflow_id': context.workflow_id,
                    'rfp_id': context.rfp_id,
                    'document': rfp_data.get('document'),
                    'document_type': rfp_data.get('document_type', 'pdf')
                },
                timeout=60.0
            )
            
            if not response or response.get('status') != 'success':
                raise Exception(f"Parsing failed: {response.get('error', 'Unknown error')}")
            
            result = StageResult(
                stage=WorkflowStage.PARSING,
                status="success",
                data={
                    'parsed_sections': response.get('sections', []),
                    'extracted_requirements': response.get('requirements', []),
                    'metadata': response.get('metadata', {}),
                    'confidence_score': response.get('confidence_score', 0.0)
                },
                duration=time.time() - start_time
            )
            
            context.stage_results[WorkflowStage.PARSING] = result
            
            # Record timing for estimates
            self.time_estimator.record_stage_time('parsing', result.duration)
            
            logger.info("Parsing completed", 
                       workflow_id=context.workflow_id,
                       sections=len(result.data['parsed_sections']))
            
            return result
            
        except Exception as e:
            logger.error("Parsing stage failed",
                        workflow_id=context.workflow_id,
                        error=str(e))
            return StageResult(
                stage=WorkflowStage.PARSING,
                status="failed",
                data={},
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def _stage_sales_analysis(self, context: WorkflowContext,
                                   parsed_data: Dict[str, Any]) -> StageResult:
        """Stage 2: Sales agent analyzes requirements and customer context."""
        import time
        start_time = time.time()
        
        context.current_stage = WorkflowStage.SALES_ANALYSIS
        await self.comm_manager.set_agent_state(
            self.agent_id,
            "current_stage",
            WorkflowStage.SALES_ANALYSIS.value
        )
        
        # Check if approval required (for complex RFP template)
        if self.approval_manager and context.metadata.get('template_id') == 'complex_rfp':
            logger.info("Requesting approval for sales analysis",
                       workflow_id=context.workflow_id)
            
            approved = await self.approval_manager.request_approval(
                workflow_id=context.workflow_id,
                stage_name="sales_analysis",
                required_roles=["sales_manager"],
                context_data={
                    'rfp_id': context.rfp_id,
                    'customer_id': context.customer_id,
                    'parsed_data': parsed_data
                },
                timeout=300.0  # 5 minutes
            )
            
            if not approved:
                return StageResult(
                    stage=WorkflowStage.SALES_ANALYSIS,
                    status="failed",
                    data={},
                    error="Approval rejected or timed out",
                    duration=time.time() - start_time
                )
        
        logger.info("Stage 2: Sales Analysis", workflow_id=context.workflow_id)
        
        try:
            response = await self.comm_manager.send_request(
                sender=self.agent_id,
                recipient="sales_agent",
                payload={
                    'workflow_id': context.workflow_id,
                    'rfp_id': context.rfp_id,
                    'customer_id': context.customer_id,
                    'requirements': parsed_data.get('extracted_requirements', []),
                    'sections': parsed_data.get('parsed_sections', [])
                },
                timeout=90.0
            )
            
            if not response or response.get('status') != 'success':
                raise Exception(f"Sales analysis failed: {response.get('error')}")
            
            result = StageResult(
                stage=WorkflowStage.SALES_ANALYSIS,
                status="success",
                data={
                    'line_items': response.get('line_items', []),
                    'customer_context': response.get('customer_context', {}),
                    'opportunity_score': response.get('opportunity_score', 0.0),
                    'recommended_products': response.get('recommended_products', []),
                    'delivery_terms': response.get('delivery_terms', {}),
                    'payment_terms': response.get('payment_terms', {})
                },
                duration=time.time() - start_time
            )
            
            context.stage_results[WorkflowStage.SALES_ANALYSIS] = result
            
            # Record timing for estimates
            self.time_estimator.record_stage_time('sales_analysis', result.duration)
            
            logger.info("Sales analysis completed",
                       workflow_id=context.workflow_id,
                       line_items=len(result.data['line_items']))
            
            return result
            
        except Exception as e:
            logger.error("Sales analysis failed",
                        workflow_id=context.workflow_id,
                        error=str(e))
            return StageResult(
                stage=WorkflowStage.SALES_ANALYSIS,
                status="failed",
                data={},
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def _stage_technical_validation(self, context: WorkflowContext,
                                         sales_data: Dict[str, Any]) -> StageResult:
        """Stage 3: Technical agent validates specifications and compliance."""
        import time
        start_time = time.time()
        
        context.current_stage = WorkflowStage.TECHNICAL_VALIDATION
        await self.comm_manager.set_agent_state(
            self.agent_id,
            "current_stage",
            WorkflowStage.TECHNICAL_VALIDATION.value
        )
        
        logger.info("Stage 3: Technical Validation", workflow_id=context.workflow_id)
        
        try:
            response = await self.comm_manager.send_request(
                sender=self.agent_id,
                recipient="technical_agent",
                payload={
                    'workflow_id': context.workflow_id,
                    'rfp_id': context.rfp_id,
                    'line_items': sales_data.get('line_items', []),
                    'recommended_products': sales_data.get('recommended_products', [])
                },
                timeout=120.0
            )
            
            if not response or response.get('status') != 'success':
                raise Exception(f"Technical validation failed: {response.get('error')}")
            
            result = StageResult(
                stage=WorkflowStage.TECHNICAL_VALIDATION,
                status="success",
                data={
                    'validated_products': response.get('validated_products', []),
                    'compliance_report': response.get('compliance_report', {}),
                    'standards_met': response.get('standards_met', []),
                    'certifications': response.get('certifications', []),
                    'technical_notes': response.get('technical_notes', []),
                    'compliance_score': response.get('compliance_score', 0.0)
                },
                duration=time.time() - start_time
            )            
            # Record timing for estimates
            self.time_estimator.record_stage_time('technical_validation', result.duration)
                        
            context.stage_results[WorkflowStage.TECHNICAL_VALIDATION] = result
            logger.info("Technical validation completed",
                       workflow_id=context.workflow_id,
                       compliance_score=result.data['compliance_score'])
            
            return result
            
        except Exception as e:
            logger.error("Technical validation failed",
                        workflow_id=context.workflow_id,
                        error=str(e))
            return StageResult(
                stage=WorkflowStage.TECHNICAL_VALIDATION,
                status="failed",
                data={},
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def _stage_pricing_calculation(self, context: WorkflowContext,
                                        sales_data: Dict[str, Any],
                                        technical_data: Dict[str, Any]) -> StageResult:
        """Stage 4: Pricing agent calculates quote."""
        import time
        start_time = time.time()
        
        context.current_stage = WorkflowStage.PRICING_CALCULATION
        await self.comm_manager.set_agent_state(
            self.agent_id,
            "current_stage",
            WorkflowStage.PRICING_CALCULATION.value
        )
        
        logger.info("Stage 4: Pricing Calculation", workflow_id=context.workflow_id)
        
        try:
            response = await self.comm_manager.send_request(
                sender=self.agent_id,
                recipient="pricing_agent",
                payload={
                    'workflow_id': context.workflow_id,
                    'rfp_id': context.rfp_id,
                    'customer_id': context.customer_id,
                    'line_items': sales_data.get('line_items', []),
                    'validated_products': technical_data.get('validated_products', []),
                    'customer_context': sales_data.get('customer_context', {})
                },
                timeout=60.0
            )
            
            if not response or response.get('status') != 'success':
                raise Exception(f"Pricing calculation failed: {response.get('error')}")
            
            result = StageResult(
                stage=WorkflowStage.PRICING_CALCULATION,
                status="success",
                data={
                    'quote_id': response.get('quote_id'),
                    'line_item_prices': response.get('line_item_prices', []),
                    'subtotal': response.get('subtotal', 0.0),
                    'taxes': response.get('taxes', 0.0),
                    'total': response.get('total', 0.0),
                    'discounts_applied': response.get('discounts_applied', []),
                    'payment_terms': response.get('payment_terms', {}),
                    'validity_period': response.get('validity_period', 30)
                },
                duration=time.time() - start_time
            )
            
            context.stage_results[WorkflowStage.PRICING_CALCULATION] = result
            
            # Record timing for estimates
            self.time_estimator.record_stage_time('pricing_calculation', result.duration)
            
            logger.info("Pricing calculation completed",
                       workflow_id=context.workflow_id,
                       total=result.data['total'])
            
            return result
            
        except Exception as e:
            logger.error("Pricing calculation failed",
                        workflow_id=context.workflow_id,
                        error=str(e))
            return StageResult(
                stage=WorkflowStage.PRICING_CALCULATION,
                status="failed",
                data={},
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def _stage_response_generation(self, context: WorkflowContext,
                                        parsed_data: Dict[str, Any],
                                        sales_data: Dict[str, Any],
                                        technical_data: Dict[str, Any],
                                        pricing_data: Dict[str, Any]) -> StageResult:
        """Stage 5: Generate final RFP response document."""
        import time
        start_time = time.time()
        
        context.current_stage = WorkflowStage.RESPONSE_GENERATION
        await self.comm_manager.set_agent_state(
            self.agent_id,
            "current_stage",
            WorkflowStage.RESPONSE_GENERATION.value
        )
        
        logger.info("Stage 5: Response Generation", workflow_id=context.workflow_id)
        
        try:
            # Compile all data for response generation
            response_payload = {
                'workflow_id': context.workflow_id,
                'rfp_id': context.rfp_id,
                'customer_id': context.customer_id,
                'parsed_content': parsed_data,
                'sales_analysis': sales_data,
                'technical_validation': technical_data,
                'pricing': pricing_data,
                'deadline': context.metadata.get('deadline')
            }
            
            response = await self.comm_manager.send_request(
                sender=self.agent_id,
                recipient="response_generator_agent",
                payload=response_payload,
                timeout=90.0
            )
            
            if not response or response.get('status') != 'success':
                raise Exception(f"Response generation failed: {response.get('error')}")
            
            result = StageResult(
                stage=WorkflowStage.RESPONSE_GENERATION,
                status="success",
                data={
                    'response_document': response.get('document', {}),
                    'executive_summary': response.get('executive_summary', ''),
                    'technical_section': response.get('technical_section', {}),
                    'pricing_section': response.get('pricing_section', {}),
                    'terms_conditions': response.get('terms_conditions', {}),
                    'document_format': response.get('format', 'pdf')
                },
                duration=time.time() - start_time
            )
            
            context.stage_results[WorkflowStage.RESPONSE_GENERATION] = result
            
            # Record timing for estimates
            self.time_estimator.record_stage_time('response_generation', result.duration)
            
            logger.info("Response generation completed",
                       workflow_id=context.workflow_id)
            
            return result
            
        except Exception as e:
            logger.error("Response generation failed",
                        workflow_id=context.workflow_id,
                        error=str(e))
            return StageResult(
                stage=WorkflowStage.RESPONSE_GENERATION,
                status="failed",
                data={},
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def _stage_review(self, context: WorkflowContext,
                          response_data: Dict[str, Any]) -> StageResult:
        """Stage 6: Final review and quality assurance."""
        import time
        start_time = time.time()
        
        context.current_stage = WorkflowStage.REVIEW
        await self.comm_manager.set_agent_state(
            self.agent_id,
            "current_stage",
            WorkflowStage.REVIEW.value
        )
        
        logger.info("Stage 6: Final Review", workflow_id=context.workflow_id)
        
        try:
            # Compile final response with all workflow data
            final_response = {
                'workflow_id': context.workflow_id,
                'rfp_id': context.rfp_id,
                'customer_id': context.customer_id,
                'status': 'completed',
                'response_document': response_data.get('response_document'),
                'executive_summary': response_data.get('executive_summary'),
                'quote': {
                    'quote_id': context.stage_results[WorkflowStage.PRICING_CALCULATION].data.get('quote_id'),
                    'total': context.stage_results[WorkflowStage.PRICING_CALCULATION].data.get('total'),
                    'line_items': context.stage_results[WorkflowStage.PRICING_CALCULATION].data.get('line_item_prices'),
                    'validity_days': context.stage_results[WorkflowStage.PRICING_CALCULATION].data.get('validity_period')
                },
                'compliance': {
                    'score': context.stage_results[WorkflowStage.TECHNICAL_VALIDATION].data.get('compliance_score'),
                    'standards_met': context.stage_results[WorkflowStage.TECHNICAL_VALIDATION].data.get('standards_met'),
                    'certifications': context.stage_results[WorkflowStage.TECHNICAL_VALIDATION].data.get('certifications')
                },
                'timeline': {
                    'processing_started': context.start_time.isoformat(),
                    'processing_completed': datetime.utcnow().isoformat(),
                    'total_duration_seconds': (datetime.utcnow() - context.start_time).total_seconds(),
                    'stage_durations': {
                        stage.value: result.duration
                        for stage, result in context.stage_results.items()
                    }
                },
                'metadata': {
                    'workflow_stages_completed': len(context.stage_results),
                    'confidence_scores': {
                        'parsing': context.stage_results[WorkflowStage.PARSING].data.get('confidence_score', 0.0),
                        'opportunity': context.stage_results[WorkflowStage.SALES_ANALYSIS].data.get('opportunity_score', 0.0),
                        'compliance': context.stage_results[WorkflowStage.TECHNICAL_VALIDATION].data.get('compliance_score', 0.0)
                    }
                }
            }
            
            result = StageResult(
                stage=WorkflowStage.REVIEW,
                status="success",
                data=final_response,
                duration=time.time() - start_time
            )
            
            context.stage_results[WorkflowStage.REVIEW] = result
            logger.info("Final review completed",
                       workflow_id=context.workflow_id)
            
            return result
            
        except Exception as e:
            logger.error("Final review failed",
                        workflow_id=context.workflow_id,
                        error=str(e))
            return StageResult(
                stage=WorkflowStage.REVIEW,
                status="failed",
                data={},
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def _handle_workflow_failure(self, context: WorkflowContext,
                                      failed_stage: Optional[StageResult]) -> Dict[str, Any]:
        """Handle workflow failure and generate error response."""
        context.status = WorkflowStatus.FAILED
        context.current_stage = WorkflowStage.FAILED
        context.end_time = datetime.utcnow()
        
        if failed_stage:
            context.errors.append(f"Stage {failed_stage.stage.value} failed: {failed_stage.error}")
        
        # Broadcast failure
        await self.comm_manager.broadcast(
            self.agent_id,
            {
                'event': 'workflow_failed',
                'workflow_id': context.workflow_id,
                'rfp_id': context.rfp_id,
                'failed_stage': context.current_stage.value,
                'errors': context.errors
            }
        )
        
        logger.error("Workflow failed",
                    workflow_id=context.workflow_id,
                    errors=context.errors)
        
        return {
            'workflow_id': context.workflow_id,
            'rfp_id': context.rfp_id,
            'status': 'failed',
            'failed_stage': context.current_stage.value,
            'errors': context.errors,
            'completed_stages': [stage.value for stage in context.stage_results.keys()],
            'duration': (context.end_time - context.start_time).total_seconds()
        }
    
    async def _handle_agent_response(self, message):
        """Handle response messages from agents."""
        logger.debug("Received agent response",
                    from_agent=message.sender,
                    correlation_id=message.correlation_id)
    
    async def _handle_agent_error(self, message):
        """Handle error messages from agents."""
        logger.error("Received agent error",
                    from_agent=message.sender,
                    error=message.payload.get('error'))
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow."""
        context = self.active_workflows.get(workflow_id)
        if not context:
            return None
        
        return {
            'workflow_id': workflow_id,
            'rfp_id': context.rfp_id,
            'current_stage': context.current_stage.value,
            'status': context.status.value,
            'completed_stages': [stage.value for stage in context.stage_results.keys()],
            'errors': context.errors,
            'start_time': context.start_time.isoformat(),
            'end_time': context.end_time.isoformat() if context.end_time else None
        }
    
    def get_all_active_workflows(self) -> List[Dict[str, Any]]:
        """Get status of all active workflows."""
        return [
            self.get_workflow_status(wf_id)
            for wf_id in self.active_workflows.keys()
        ]
    
    def get_time_estimates(self) -> Dict[str, Any]:
        """Get time estimates for workflow stages."""
        stages = ['parsing', 'sales_analysis', 'technical_validation',
                 'pricing_calculation', 'response_generation']
        
        estimates = {}
        for stage in stages:
            estimates[stage] = {
                'estimated_time': self.time_estimator.estimate_stage_time(stage),
                'confidence': self.time_estimator.get_confidence_level(stage),
                'sample_count': len(self.time_estimator.stage_history.get(stage, []))
            }
        
        estimates['total_workflow'] = {
            'estimated_time': self.time_estimator.estimate_workflow_time(stages),
            'sample_count': len(self.time_estimator.workflow_history)
        }
        
        return estimates
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available workflow templates."""
        templates = self.template_manager.list_templates()
        return [
            {
                'template_id': t.template_id,
                'name': t.name,
                'description': t.description,
                'stages': [s.stage_name for s in t.stages],
                'estimated_duration': t.estimated_duration
            }
            for t in templates
        ]
    
    def visualize_workflow(self, workflow_id: str) -> str:
        """Generate visualization for a workflow."""
        context = self.active_workflows.get(workflow_id)
        if not context:
            return "Workflow not found"
        
        template = self.template_manager.get_template(
            context.metadata.get('template_id', 'standard_rfp')
        )
        
        stage_names = [s.stage_name for s in template.stages]
        completed = [s.value for s in context.stage_results.keys()]
        current = context.current_stage.value if context.status == WorkflowStatus.IN_PROGRESS else None
        
        return self.visualizer.generate_ascii_flow(stage_names, current, completed)
    
    def generate_mermaid_diagram(self, workflow_id: str) -> str:
        """Generate Mermaid diagram for a workflow."""
        context = self.active_workflows.get(workflow_id)
        if not context:
            return "Workflow not found"
        
        template = self.template_manager.get_template(
            context.metadata.get('template_id', 'standard_rfp')
        )
        
        stage_names = [s.stage_name for s in template.stages]
        completed = [s.value for s in context.stage_results.keys()]
        failed = context.current_stage.value if context.status == WorkflowStatus.FAILED else None
        
        return self.visualizer.generate_mermaid_diagram(stage_names, completed, failed)