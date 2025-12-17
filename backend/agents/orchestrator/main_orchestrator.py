"""
Main Orchestrator Agent
Coordinates all worker agents, manages workflow, and generates final RFP responses.

Workflow:
1. Sales Agent: Analyzes RFP and identifies requirements
2. Technical Agent: Provides product recommendations and technical specifications
3. Pricing Agent: Generates commercial bid with pricing
4. Orchestrator: Consolidates all outputs and generates final documents
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import structlog
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

# Setup logging
logger = structlog.get_logger()


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    SALES_ANALYSIS = "sales_analysis"
    TECHNICAL_REVIEW = "technical_review"
    PRICING_CALCULATION = "pricing_calculation"
    CONSOLIDATION = "consolidation"
    DOCUMENT_GENERATION = "document_generation"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentStatus(Enum):
    """Individual agent execution status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class AgentResult:
    """Result from an agent execution."""
    agent_name: str
    status: AgentStatus
    data: Dict[str, Any]
    execution_time_seconds: float
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class WorkflowState:
    """Current state of the workflow."""
    rfp_id: str
    workflow_id: str
    status: WorkflowStatus
    started_at: str
    completed_at: Optional[str] = None
    
    # Agent results
    sales_result: Optional[AgentResult] = None
    technical_result: Optional[AgentResult] = None
    pricing_result: Optional[AgentResult] = None
    
    # Consolidated data
    consolidated_response: Optional[Dict[str, Any]] = None
    
    # Metadata
    total_execution_time: float = 0.0
    error_count: int = 0
    warning_count: int = 0


@dataclass
class RFPResponse:
    """Final RFP response document."""
    rfp_id: str
    response_id: str
    generated_at: str
    
    # Customer information
    customer_name: str
    customer_type: str
    
    # Executive summary
    executive_summary: str
    
    # Technical proposal
    technical_proposal: Dict[str, Any]
    
    # Commercial proposal
    commercial_proposal: Dict[str, Any]
    
    # Compliance matrix
    compliance_matrix: pd.DataFrame
    
    # Terms and conditions
    terms_and_conditions: str
    
    # Appendices
    appendices: Dict[str, Any]
    
    # Metadata
    prepared_by: str = "Haki FMCG RFP System"
    validity_days: int = 90
    valid_until: str = ""


class MainOrchestrator:
    """
    Main Orchestrator Agent
    
    Responsibilities:
    1. Receive RFP input
    2. Orchestrate worker agents (Sales, Technical, Pricing)
    3. Manage workflow and state
    4. Consolidate agent responses
    5. Generate final RFP response documents
    6. Handle errors and retries
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Main Orchestrator."""
        self.logger = logger.bind(component="MainOrchestrator")
        self.config = config or {}
        
        # Worker agents (to be injected)
        self.sales_agent = None
        self.technical_agent = None
        self.pricing_agent = None
        
        # Workflow tracking
        self.workflows: Dict[str, WorkflowState] = {}
        
        # Statistics
        self.statistics = {
            'total_rfps_processed': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'average_execution_time': 0.0,
            'total_value_quoted': 0.0
        }
        
        self.logger.info("Main Orchestrator initialized")
    
    def register_agents(
        self,
        sales_agent: Any,
        technical_agent: Any,
        pricing_agent: Any
    ):
        """Register worker agents.
        
        Args:
            sales_agent: Sales Agent instance
            technical_agent: Technical Agent instance
            pricing_agent: Pricing Agent instance
        """
        self.sales_agent = sales_agent
        self.technical_agent = technical_agent
        self.pricing_agent = pricing_agent
        
        self.logger.info(
            "Worker agents registered",
            sales=bool(sales_agent),
            technical=bool(technical_agent),
            pricing=bool(pricing_agent)
        )
    
    def process_rfp(
        self,
        rfp_document: Dict[str, Any],
        customer_info: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, WorkflowState, Optional[RFPResponse]]:
        """Process RFP through complete workflow.
        
        Args:
            rfp_document: RFP document content
            customer_info: Customer information
            options: Processing options
            
        Returns:
            Tuple of (success, workflow_state, rfp_response)
        """
        options = options or {}
        rfp_id = rfp_document.get('rfp_id', f"RFP-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        
        # Initialize workflow
        workflow_id = f"WF-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        workflow_state = WorkflowState(
            rfp_id=rfp_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            started_at=datetime.now().isoformat()
        )
        
        self.workflows[workflow_id] = workflow_state
        
        self.logger.info(
            "Starting RFP processing workflow",
            rfp_id=rfp_id,
            workflow_id=workflow_id
        )
        
        start_time = datetime.now()
        
        try:
            # Step 1: Sales Agent Analysis
            workflow_state.status = WorkflowStatus.SALES_ANALYSIS
            sales_success, sales_result = self._execute_sales_agent(
                rfp_document,
                customer_info
            )
            workflow_state.sales_result = sales_result
            
            if not sales_success:
                workflow_state.status = WorkflowStatus.FAILED
                workflow_state.error_count += 1
                self.statistics['failed_responses'] += 1
                return False, workflow_state, None
            
            # Step 2: Technical Agent Review
            workflow_state.status = WorkflowStatus.TECHNICAL_REVIEW
            technical_success, technical_result = self._execute_technical_agent(
                sales_result.data,
                customer_info
            )
            workflow_state.technical_result = technical_result
            
            if not technical_success:
                workflow_state.status = WorkflowStatus.FAILED
                workflow_state.error_count += 1
                self.statistics['failed_responses'] += 1
                return False, workflow_state, None
            
            # Step 3: Pricing Agent Calculation
            workflow_state.status = WorkflowStatus.PRICING_CALCULATION
            pricing_success, pricing_result = self._execute_pricing_agent(
                technical_result.data,
                customer_info,
                rfp_document
            )
            workflow_state.pricing_result = pricing_result
            
            if not pricing_success:
                workflow_state.status = WorkflowStatus.FAILED
                workflow_state.error_count += 1
                self.statistics['failed_responses'] += 1
                return False, workflow_state, None
            
            # Step 4: Consolidate Results
            workflow_state.status = WorkflowStatus.CONSOLIDATION
            consolidated = self._consolidate_results(
                sales_result,
                technical_result,
                pricing_result,
                customer_info
            )
            workflow_state.consolidated_response = consolidated
            
            # Step 5: Generate Final Documents
            workflow_state.status = WorkflowStatus.DOCUMENT_GENERATION
            rfp_response = self._generate_rfp_response(
                rfp_id,
                consolidated,
                customer_info
            )
            
            # Complete workflow
            end_time = datetime.now()
            workflow_state.status = WorkflowStatus.COMPLETED
            workflow_state.completed_at = end_time.isoformat()
            workflow_state.total_execution_time = (end_time - start_time).total_seconds()
            
            # Update statistics
            self.statistics['total_rfps_processed'] += 1
            self.statistics['successful_responses'] += 1
            self.statistics['total_value_quoted'] += pricing_result.data.get('bid_summary', {}).get('grand_total', 0)
            
            # Update average execution time
            total_time = (
                self.statistics['average_execution_time'] * (self.statistics['total_rfps_processed'] - 1) +
                workflow_state.total_execution_time
            ) / self.statistics['total_rfps_processed']
            self.statistics['average_execution_time'] = total_time
            
            self.logger.info(
                "RFP processing completed successfully",
                rfp_id=rfp_id,
                workflow_id=workflow_id,
                execution_time=workflow_state.total_execution_time
            )
            
            return True, workflow_state, rfp_response
            
        except Exception as e:
            self.logger.error(
                "RFP processing failed",
                rfp_id=rfp_id,
                workflow_id=workflow_id,
                error=str(e),
                exc_info=True
            )
            
            workflow_state.status = WorkflowStatus.FAILED
            workflow_state.error_count += 1
            workflow_state.completed_at = datetime.now().isoformat()
            
            self.statistics['failed_responses'] += 1
            
            return False, workflow_state, None
    
    def _execute_sales_agent(
        self,
        rfp_document: Dict[str, Any],
        customer_info: Dict[str, Any]
    ) -> Tuple[bool, AgentResult]:
        """Execute Sales Agent analysis.
        
        Args:
            rfp_document: RFP document
            customer_info: Customer information
            
        Returns:
            Tuple of (success, agent_result)
        """
        self.logger.info("Executing Sales Agent")
        start_time = datetime.now()
        
        try:
            # Mock Sales Agent execution
            # In production, call: self.sales_agent.analyze_rfp(rfp_document, customer_info)
            
            sales_data = {
                'rfp_analysis': {
                    'customer_name': customer_info.get('name', 'Unknown'),
                    'customer_type': customer_info.get('type', 'Standard'),
                    'rfp_type': rfp_document.get('type', 'Standard'),
                    'urgency': rfp_document.get('urgency', 'Normal'),
                    'estimated_value': rfp_document.get('estimated_value', 0)
                },
                'requirements': rfp_document.get('requirements', []),
                'key_decision_factors': [
                    'Price competitiveness',
                    'Technical compliance',
                    'Delivery timeline',
                    'Quality certifications'
                ],
                'win_strategy': {
                    'approach': 'Competitive pricing with quality focus',
                    'key_strengths': ['Technical expertise', 'Reliable delivery', 'Quality products'],
                    'differentiators': ['Comprehensive testing', 'After-sales support']
                }
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = AgentResult(
                agent_name="Sales Agent",
                status=AgentStatus.COMPLETED,
                data=sales_data,
                execution_time_seconds=execution_time
            )
            
            self.logger.info(
                "Sales Agent completed",
                execution_time=execution_time
            )
            
            return True, result
            
        except Exception as e:
            self.logger.error("Sales Agent failed", error=str(e))
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = AgentResult(
                agent_name="Sales Agent",
                status=AgentStatus.FAILED,
                data={},
                execution_time_seconds=execution_time,
                error_message=str(e)
            )
            
            return False, result
    
    def _execute_technical_agent(
        self,
        sales_analysis: Dict[str, Any],
        customer_info: Dict[str, Any]
    ) -> Tuple[bool, AgentResult]:
        """Execute Technical Agent review.
        
        Args:
            sales_analysis: Sales agent output
            customer_info: Customer information
            
        Returns:
            Tuple of (success, agent_result)
        """
        self.logger.info("Executing Technical Agent")
        start_time = datetime.now()
        
        try:
            # Mock Technical Agent execution
            # In production, call: self.technical_agent.analyze_requirements(sales_analysis)
            
            requirements = sales_analysis.get('requirements', [])
            
            technical_data = {
                'comparisons': [
                    {
                        'requirement': req,
                        'products': [
                            {
                                'name': f"{req.get('product_name', 'Product')}",
                                'brand': 'Havells',
                                'unit_price': req.get('unit_price', 100.0),
                                'category': 'Electrical Cables',
                                'standards_compliance': ['IS 694:2010'],
                                'certifications': ['BIS', 'ISO 9001']
                            }
                        ]
                    }
                    for req in requirements
                ],
                'technical_summary': {
                    'total_products': len(requirements),
                    'standards_met': ['IS 694', 'IEC 60502'],
                    'certifications': ['BIS', 'ISO 9001', 'CPRI'],
                    'compliance_level': 'Full Compliance'
                }
            }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = AgentResult(
                agent_name="Technical Agent",
                status=AgentStatus.COMPLETED,
                data=technical_data,
                execution_time_seconds=execution_time
            )
            
            self.logger.info(
                "Technical Agent completed",
                execution_time=execution_time
            )
            
            return True, result
            
        except Exception as e:
            self.logger.error("Technical Agent failed", error=str(e))
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = AgentResult(
                agent_name="Technical Agent",
                status=AgentStatus.FAILED,
                data={},
                execution_time_seconds=execution_time,
                error_message=str(e)
            )
            
            return False, result
    
    def _execute_pricing_agent(
        self,
        technical_recommendations: Dict[str, Any],
        customer_info: Dict[str, Any],
        rfp_details: Dict[str, Any]
    ) -> Tuple[bool, AgentResult]:
        """Execute Pricing Agent calculation.
        
        Args:
            technical_recommendations: Technical agent output
            customer_info: Customer information
            rfp_details: RFP details
            
        Returns:
            Tuple of (success, agent_result)
        """
        self.logger.info("Executing Pricing Agent")
        start_time = datetime.now()
        
        try:
            # If pricing agent is registered, use it
            if self.pricing_agent:
                pricing_data = self.pricing_agent.process_pricing_request(
                    technical_recommendations,
                    customer_info,
                    rfp_details
                )
            else:
                # Mock pricing data
                pricing_data = {
                    'bid_id': f"BID-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    'product_pricings': [],
                    'bid_summary': {
                        'grand_total': 1000000.0,
                        'margin_percent': 20.0,
                        'payment_terms': 'Net 30 days',
                        'validity_days': 90
                    },
                    'documents': {}
                }
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = AgentResult(
                agent_name="Pricing Agent",
                status=AgentStatus.COMPLETED,
                data=pricing_data,
                execution_time_seconds=execution_time
            )
            
            self.logger.info(
                "Pricing Agent completed",
                execution_time=execution_time,
                total_value=pricing_data.get('bid_summary', {}).get('grand_total', 0)
            )
            
            return True, result
            
        except Exception as e:
            self.logger.error("Pricing Agent failed", error=str(e))
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = AgentResult(
                agent_name="Pricing Agent",
                status=AgentStatus.FAILED,
                data={},
                execution_time_seconds=execution_time,
                error_message=str(e)
            )
            
            return False, result
    
    def _consolidate_results(
        self,
        sales_result: AgentResult,
        technical_result: AgentResult,
        pricing_result: AgentResult,
        customer_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Consolidate results from all agents.
        
        Args:
            sales_result: Sales agent result
            technical_result: Technical agent result
            pricing_result: Pricing agent result
            customer_info: Customer information
            
        Returns:
            Consolidated response data
        """
        self.logger.info("Consolidating agent results")
        
        consolidated = {
            'customer': {
                'name': customer_info.get('name', 'Unknown'),
                'type': customer_info.get('type', 'Standard'),
                'contact': customer_info.get('contact', {})
            },
            'sales_analysis': sales_result.data,
            'technical_proposal': technical_result.data,
            'commercial_proposal': pricing_result.data,
            'execution_summary': {
                'sales_agent': {
                    'status': sales_result.status.value,
                    'execution_time': sales_result.execution_time_seconds
                },
                'technical_agent': {
                    'status': technical_result.status.value,
                    'execution_time': technical_result.execution_time_seconds
                },
                'pricing_agent': {
                    'status': pricing_result.status.value,
                    'execution_time': pricing_result.execution_time_seconds
                }
            }
        }
        
        return consolidated
    
    def _generate_rfp_response(
        self,
        rfp_id: str,
        consolidated_data: Dict[str, Any],
        customer_info: Dict[str, Any]
    ) -> RFPResponse:
        """Generate final RFP response document.
        
        Args:
            rfp_id: RFP ID
            consolidated_data: Consolidated agent data
            customer_info: Customer information
            
        Returns:
            RFPResponse object
        """
        self.logger.info("Generating final RFP response")
        
        response_id = f"RESP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Generate executive summary
        exec_summary = self._generate_executive_summary(consolidated_data)
        
        # Generate compliance matrix
        compliance_matrix = self._generate_compliance_matrix(consolidated_data)
        
        # Generate terms and conditions
        terms = self._generate_terms_and_conditions(consolidated_data)
        
        # Create response
        rfp_response = RFPResponse(
            rfp_id=rfp_id,
            response_id=response_id,
            generated_at=datetime.now().isoformat(),
            customer_name=customer_info.get('name', 'Unknown'),
            customer_type=customer_info.get('type', 'Standard'),
            executive_summary=exec_summary,
            technical_proposal=consolidated_data.get('technical_proposal', {}),
            commercial_proposal=consolidated_data.get('commercial_proposal', {}),
            compliance_matrix=compliance_matrix,
            terms_and_conditions=terms,
            appendices={
                'sales_analysis': consolidated_data.get('sales_analysis', {}),
                'execution_summary': consolidated_data.get('execution_summary', {})
            }
        )
        
        # Calculate valid until date
        valid_until = datetime.now()
        from datetime import timedelta
        valid_until = valid_until + timedelta(days=rfp_response.validity_days)
        rfp_response.valid_until = valid_until.strftime('%Y-%m-%d')
        
        return rfp_response
    
    def _generate_executive_summary(self, consolidated_data: Dict[str, Any]) -> str:
        """Generate executive summary."""
        commercial = consolidated_data.get('commercial_proposal', {})
        bid_summary = commercial.get('bid_summary', {})
        
        grand_total = bid_summary.get('grand_total', 0)
        margin = bid_summary.get('margin_percent', 0)
        payment_terms = bid_summary.get('payment_terms', 'Net 30 days')
        
        summary = f"""EXECUTIVE SUMMARY

We are pleased to submit our proposal in response to your Request for Proposal (RFP).

OVERVIEW:
Our proposal offers a comprehensive solution that meets all technical requirements while providing competitive pricing and reliable delivery.

KEY HIGHLIGHTS:
- Total Bid Value: ₹{grand_total:,.2f}
- Payment Terms: {payment_terms}
- Delivery Timeline: As per RFP requirements
- Warranty: 12 months from date of delivery
- Quality Certifications: ISO 9001, BIS certified

COMPETITIVE ADVANTAGES:
1. Technical Compliance: Full compliance with all specified standards
2. Quality Assurance: Comprehensive testing program included
3. Reliable Delivery: Proven track record of on-time delivery
4. After-Sales Support: Dedicated support team

We are confident that our proposal represents excellent value and look forward to the opportunity to serve you.
"""
        return summary
    
    def _generate_compliance_matrix(self, consolidated_data: Dict[str, Any]) -> pd.DataFrame:
        """Generate compliance matrix."""
        requirements = consolidated_data.get('sales_analysis', {}).get('requirements', [])
        
        compliance_data = []
        for idx, req in enumerate(requirements, 1):
            compliance_data.append({
                'S.No': idx,
                'Requirement': req.get('product_name', 'Not specified'),
                'Specification': req.get('specifications', 'As per RFP'),
                'Our Offering': 'Compliant',
                'Standards': 'IS 694, IEC 60502',
                'Compliance Status': 'YES',
                'Remarks': 'Fully compliant'
            })
        
        if not compliance_data:
            compliance_data.append({
                'S.No': 1,
                'Requirement': 'General Requirements',
                'Specification': 'As per RFP',
                'Our Offering': 'Compliant',
                'Standards': 'Applicable Indian Standards',
                'Compliance Status': 'YES',
                'Remarks': 'Fully compliant'
            })
        
        return pd.DataFrame(compliance_data)
    
    def _generate_terms_and_conditions(self, consolidated_data: Dict[str, Any]) -> str:
        """Generate terms and conditions."""
        commercial = consolidated_data.get('commercial_proposal', {})
        bid_summary = commercial.get('bid_summary', {})
        
        payment_terms = bid_summary.get('payment_terms', 'Net 30 days')
        validity_days = bid_summary.get('validity_days', 90)
        
        terms = f"""TERMS AND CONDITIONS

1. VALIDITY OF OFFER
   This proposal is valid for {validity_days} days from the date of submission.

2. PAYMENT TERMS
   {payment_terms}

3. DELIVERY TERMS
   - Delivery: Ex-Works / FOB as specified
   - Lead Time: As per agreement
   - Packaging: Standard export packaging

4. QUALITY ASSURANCE
   - All products meet specified Indian Standards
   - Test certificates provided
   - Quality warranty: 12 months

5. TAXES
   - GST at applicable rates (currently 18%)
   - All other statutory taxes as applicable

6. FORCE MAJEURE
   Neither party shall be liable for delays due to circumstances beyond reasonable control.

7. GOVERNING LAW
   This agreement shall be governed by the laws of India.

8. DISPUTE RESOLUTION
   Any disputes shall be resolved through arbitration in accordance with Indian Arbitration Act.
"""
        return terms
    
    def export_rfp_response(
        self,
        rfp_response: RFPResponse,
        output_dir: str = "rfp_responses"
    ) -> str:
        """Export RFP response to Excel.
        
        Args:
            rfp_response: RFP response object
            output_dir: Output directory
            
        Returns:
            Path to exported file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{rfp_response.response_id}_{timestamp}.xlsx"
        filepath = output_path / filename
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Cover Page
            cover_data = {
                'Field': [
                    'RFP ID',
                    'Response ID',
                    'Customer Name',
                    'Generated Date',
                    'Valid Until',
                    'Prepared By',
                    'Total Bid Value'
                ],
                'Value': [
                    rfp_response.rfp_id,
                    rfp_response.response_id,
                    rfp_response.customer_name,
                    rfp_response.generated_at,
                    rfp_response.valid_until,
                    rfp_response.prepared_by,
                    f"₹{rfp_response.commercial_proposal.get('bid_summary', {}).get('grand_total', 0):,.2f}"
                ]
            }
            pd.DataFrame(cover_data).to_excel(writer, sheet_name='Cover', index=False)
            
            # Executive Summary
            exec_summary_df = pd.DataFrame({
                'Executive Summary': [rfp_response.executive_summary]
            })
            exec_summary_df.to_excel(writer, sheet_name='Executive Summary', index=False)
            
            # Compliance Matrix
            rfp_response.compliance_matrix.to_excel(
                writer,
                sheet_name='Compliance Matrix',
                index=False
            )
            
            # Commercial Proposal (if available)
            if rfp_response.commercial_proposal:
                bid_summary = rfp_response.commercial_proposal.get('bid_summary', {})
                commercial_data = {
                    'Item': [
                        'Products Subtotal',
                        'Total Discounts',
                        'Testing Costs',
                        'Logistics',
                        'Installation',
                        'GST (18%)',
                        'Grand Total',
                        'Payment Terms',
                        'Validity Days'
                    ],
                    'Value': [
                        f"₹{bid_summary.get('products_subtotal', 0):,.2f}",
                        f"-₹{bid_summary.get('total_discounts', 0):,.2f}",
                        f"₹{bid_summary.get('testing_costs_total', 0):,.2f}",
                        f"₹{bid_summary.get('logistics_total', 0):,.2f}",
                        f"₹{bid_summary.get('installation_total', 0):,.2f}",
                        f"₹{bid_summary.get('gst_total', 0):,.2f}",
                        f"₹{bid_summary.get('grand_total', 0):,.2f}",
                        bid_summary.get('payment_terms', 'Net 30 days'),
                        str(bid_summary.get('validity_days', 90))
                    ]
                }
                pd.DataFrame(commercial_data).to_excel(
                    writer,
                    sheet_name='Commercial Proposal',
                    index=False
                )
            
            # Terms & Conditions
            terms_df = pd.DataFrame({
                'Terms and Conditions': [rfp_response.terms_and_conditions]
            })
            terms_df.to_excel(writer, sheet_name='Terms & Conditions', index=False)
        
        self.logger.info(f"RFP response exported to: {filepath}")
        return str(filepath)
    
    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow status.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            WorkflowState or None
        """
        return self.workflows.get(workflow_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return self.statistics.copy()
    
    def get_active_workflows(self) -> List[WorkflowState]:
        """Get all active workflows."""
        return [
            wf for wf in self.workflows.values()
            if wf.status not in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
        ]
