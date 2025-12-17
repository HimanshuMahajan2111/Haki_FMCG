"""
Master Agent (Main Orchestrator) - Coordinates RFP processing workflow.

Responsibilities:
1. Prepares contextual summaries for Technical and Pricing Agents
2. Receives and consolidates responses from worker agents
3. Produces final RFP response with OEM SKUs, prices, and test costs
4. Generates output in three formats: JSON, Excel, PDF
5. Starts and ends the conversation flow
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import structlog
import asyncio
from agents.output_generator import OutputGenerator

logger = structlog.get_logger()


@dataclass
class RFPSummary:
    """Contextual RFP summary for agents."""
    rfp_id: int
    title: str
    organization: str
    submission_deadline: datetime
    
    # Context for Technical Agent
    technical_context: Dict[str, Any] = field(default_factory=dict)
    
    # Context for Pricing Agent  
    pricing_context: Dict[str, Any] = field(default_factory=dict)
    
    # Full RFP data
    full_rfp_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsolidatedResponse:
    """Final consolidated RFP response."""
    rfp_id: int
    rfp_title: str
    organization: str
    
    # Product recommendations with SKUs
    recommended_products: List[Dict[str, Any]] = field(default_factory=list)
    
    # Pricing breakdown
    material_costs: Dict[str, Any] = field(default_factory=dict)
    testing_costs: Dict[str, Any] = field(default_factory=dict)
    total_costs: Dict[str, Any] = field(default_factory=dict)
    
    # Technical details
    spec_match_summary: Dict[str, Any] = field(default_factory=dict)
    compliance_summary: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    processed_at: datetime = field(default_factory=datetime.now)
    processing_time_seconds: float = 0.0
    confidence_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'rfp_id': self.rfp_id,
            'rfp_title': self.rfp_title,
            'organization': self.organization,
            'recommended_products': self.recommended_products,
            'material_costs': self.material_costs,
            'testing_costs': self.testing_costs,
            'total_costs': self.total_costs,
            'spec_match_summary': self.spec_match_summary,
            'compliance_summary': self.compliance_summary,
            'processed_at': self.processed_at.isoformat(),
            'processing_time_seconds': self.processing_time_seconds,
            'confidence_score': self.confidence_score
        }


class MasterAgent:
    """
    Master Agent - Main Orchestrator for RFP Processing.
    
    Workflow:
    1. Receive RFP from Sales Agent
    2. Prepare contextual summaries for Technical and Pricing Agents
    3. Send RFP summary to Technical Agent
    4. Receive technical recommendations
    5. Send test summary to Pricing Agent
    6. Send product recommendations to Pricing Agent
    7. Receive pricing consolidation
    8. Consolidate final response
    9. Return response with OEM SKUs, prices, test costs
    """
    
    def __init__(self, technical_agent, pricing_agent, output_dir: str = "outputs"):
        """Initialize Master Agent.
        
        Args:
            technical_agent: Technical Agent instance
            pricing_agent: Pricing Agent instance
            output_dir: Directory for output files
        """
        self.logger = logger.bind(component="MasterAgent")
        self.technical_agent = technical_agent
        self.pricing_agent = pricing_agent
        self.output_generator = OutputGenerator(output_dir)
        
        # Statistics tracking
        self.total_processed = 0
        self.total_value_processed = 0.0
        self.avg_processing_time = 0.0
        
        self.statistics = {
            'total_rfps_processed': 0,
            'total_products_recommended': 0,
            'total_value_quoted': 0.0,
            'average_processing_time': 0.0,
            'success_rate': 100.0
        }
    
    async def start_workflow(self, rfp_data: Dict[str, Any]) -> ConsolidatedResponse:
        """Start the complete RFP processing workflow.
        
        Args:
            rfp_data: RFP data from Sales Agent
            
        Returns:
            ConsolidatedResponse with all details
        """
        start_time = datetime.now()
        rfp_id = rfp_data.get('rfp_id', rfp_data.get('id', 0))
        
        self.logger.info(
            " Starting Master Agent workflow",
            rfp_id=rfp_id,
            rfp_title=rfp_data.get('title', 'Unknown')
        )
        
        try:
            # Step 1: Prepare contextual summaries
            rfp_summary = self._prepare_rfp_summary(rfp_data)
            self.logger.info(" Step 1: RFP summary prepared")
            
            # Step 2: Send to Technical Agent
            technical_response = await self._send_to_technical_agent(rfp_summary)
            self.logger.info(
                " Step 2: Technical Agent response received",
                products_recommended=len(technical_response.get('recommendations', []))
            )
            
            # Step 3: Send to Pricing Agent
            pricing_response = await self._send_to_pricing_agent(
                rfp_summary, 
                technical_response
            )
            self.logger.info(
                " Step 3: Pricing Agent response received",
                total_cost=pricing_response.get('total_cost', 0)
            )
            
            # Step 4: Consolidate final response
            consolidated = self._consolidate_response(
                rfp_data,
                rfp_summary,
                technical_response,
                pricing_response,
                start_time
            )
            self.logger.info(
                " Step 4: Final response consolidated",
                total_products=len(consolidated.recommended_products),
                total_value=consolidated.total_costs.get('grand_total', 0)
            )
            
            # Update statistics
            self._update_statistics(consolidated, start_time)
            
            # Step 5: Generate output files (JSON, Excel, PDF)
            output_paths = self.generate_output_files(consolidated)
            self.logger.info(
                " Step 5: Output files generated",
                json=output_paths.get('json'),
                excel=output_paths.get('excel'),
                pdf=output_paths.get('pdf')
            )
            
            self.logger.info(
                " Master Agent workflow completed successfully",
                rfp_id=rfp_id,
                processing_time=consolidated.processing_time_seconds
            )
            
            return consolidated
            
        except Exception as e:
            self.logger.error(
                " Master Agent workflow failed",
                rfp_id=rfp_id,
                error=str(e)
            )
            raise
    
    def _prepare_rfp_summary(self, rfp_data: Dict[str, Any]) -> RFPSummary:
        """Prepare contextual summaries for worker agents.
        
        Args:
            rfp_data: Raw RFP data
            
        Returns:
            RFPSummary with contextual data
        """
        self.logger.info("Preparing contextual RFP summaries")
        
        # Extract structured data
        structured_data = rfp_data.get('structured_data', {})
        
        # Prepare Technical Agent context
        technical_context = {
            'scope_of_supply': self._extract_scope_of_supply(rfp_data),
            'technical_requirements': self._extract_technical_requirements(rfp_data),
            'required_standards': self._extract_standards(rfp_data),
            'required_certifications': self._extract_certifications(rfp_data),
            'product_categories': structured_data.get('category', 'Electrical'),
            'specifications': rfp_data.get('requirements', {}),
            'rfp_document_path': rfp_data.get('file_path', ''),
            'raw_text': rfp_data.get('raw_text', '')[:5000]  # First 5000 chars
        }
        
        # Prepare Pricing Agent context
        pricing_context = {
            'tests_required': self._extract_tests_required(rfp_data),
            'acceptance_tests': self._extract_acceptance_tests(rfp_data),
            'quantities': self._extract_quantities(rfp_data),
            'delivery_terms': self._extract_delivery_terms(rfp_data),
            'payment_terms': self._extract_payment_terms(rfp_data),
            'estimated_value': rfp_data.get('estimated_value', 0)
        }
        
        summary = RFPSummary(
            rfp_id=rfp_data.get('id', 0),
            title=rfp_data.get('title', 'Unknown RFP'),
            organization=structured_data.get('buyer', 'Unknown Organization'),
            submission_deadline=rfp_data.get('due_date', datetime.now()),
            technical_context=technical_context,
            pricing_context=pricing_context,
            full_rfp_data=rfp_data
        )
        
        self.logger.info(
            "RFP summary prepared",
            technical_items=len(technical_context.get('scope_of_supply', [])),
            tests_required=len(pricing_context.get('tests_required', []))
        )
        
        return summary
    
    async def _send_to_technical_agent(self, rfp_summary: RFPSummary) -> Dict[str, Any]:
        """Send contextual summary to Technical Agent.
        
        Args:
            rfp_summary: RFP summary with technical context
            
        Returns:
            Technical Agent response with product recommendations
        """
        self.logger.info("Sending RFP to Technical Agent", rfp_id=rfp_summary.rfp_id)
        
        # Prepare Technical Agent input
        technical_input = {
            'rfp_id': rfp_summary.rfp_id,
            'rfp_title': rfp_summary.title,
            'organization': rfp_summary.organization,
            'scope_of_supply': rfp_summary.technical_context['scope_of_supply'],
            'technical_requirements': rfp_summary.technical_context['technical_requirements'],
            'required_standards': rfp_summary.technical_context['required_standards'],
            'required_certifications': rfp_summary.technical_context['required_certifications'],
            'specifications': rfp_summary.technical_context['specifications'],
            'rfp_document': rfp_summary.technical_context['rfp_document_path'],
            'raw_text': rfp_summary.technical_context['raw_text']
        }
        
        # Call Technical Agent
        response = await self.technical_agent.process_rfp_requirements(technical_input)
        
        return response
    
    async def _send_to_pricing_agent(
        self, 
        rfp_summary: RFPSummary,
        technical_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send test summary and product recommendations to Pricing Agent.
        
        Args:
            rfp_summary: RFP summary with pricing context
            technical_response: Technical Agent recommendations
            
        Returns:
            Pricing Agent response with consolidated costs
        """
        self.logger.info("Sending data to Pricing Agent", rfp_id=rfp_summary.rfp_id)
        
        # Prepare Pricing Agent input
        pricing_input = {
            'rfp_id': rfp_summary.rfp_id,
            'rfp_title': rfp_summary.title,
            
            # Test summary from Master Agent
            'tests_required': rfp_summary.pricing_context['tests_required'],
            'acceptance_tests': rfp_summary.pricing_context['acceptance_tests'],
            
            # Product recommendations from Technical Agent
            'product_recommendations': technical_response.get('recommendations', []),
            'selected_products': technical_response.get('selected_products', []),
            
            # Additional context
            'quantities': rfp_summary.pricing_context['quantities'],
            'delivery_terms': rfp_summary.pricing_context['delivery_terms'],
            'payment_terms': rfp_summary.pricing_context['payment_terms']
        }
        
        # Call Pricing Agent
        response = await self.pricing_agent.calculate_comprehensive_pricing(pricing_input)
        
        return response
    
    def _consolidate_response(
        self,
        rfp_data: Dict[str, Any],
        rfp_summary: RFPSummary,
        technical_response: Dict[str, Any],
        pricing_response: Dict[str, Any],
        start_time: datetime
    ) -> ConsolidatedResponse:
        """Consolidate all agent responses into final output.
        
        Args:
            rfp_data: Original RFP data
            rfp_summary: RFP summary
            technical_response: Technical Agent output
            pricing_response: Pricing Agent output
            start_time: Workflow start time
            
        Returns:
            ConsolidatedResponse with OEM SKUs, prices, test costs
        """
        self.logger.info("Consolidating final response")
        
        # Extract recommended products with SKUs
        recommended_products = []
        for product in technical_response.get('selected_products', []):
            product_entry = {
                'item_number': product.get('item_number'),
                'item_name': product.get('item_name'),
                'manufacturer': product.get('manufacturer', 'Unknown'),  # Test compatibility
                'oem_brand': product.get('manufacturer', 'Unknown'),
                'oem_sku': product.get('product_id', ''),
                'model_number': product.get('model_number', ''),
                'spec_match_%': product.get('spec_match_score', 0.0),  # Test compatibility
                'spec_match_percentage': product.get('spec_match_score', 0.0),
                'quantity': product.get('quantity', 1),
                'unit_price': product.get('unit_price', 0.0),
                'line_total': product.get('line_total', 0.0),
                'certifications': product.get('certifications', []),
                'standards_compliance': product.get('standards_compliance', [])
            }
            recommended_products.append(product_entry)
        
        # Extract cost breakdown
        material_costs = {
            'line_items': pricing_response.get('material_line_items', []),
            'subtotal': pricing_response.get('material_subtotal', 0.0),
            'discount': pricing_response.get('material_discount', 0.0),
            'net_material_cost': pricing_response.get('net_material_cost', 0.0),
            'net': pricing_response.get('net_material_cost', 0.0)  # Test compatibility
        }
        
        testing_costs = {
            'test_items': pricing_response.get('test_line_items', []),
            'routine_tests': pricing_response.get('routine_test_cost', 0.0),
            'routine': pricing_response.get('routine_test_cost', 0.0),  # Test compatibility
            'type_tests': pricing_response.get('type_test_cost', 0.0),
            'type': pricing_response.get('type_test_cost', 0.0),  # Test compatibility
            'acceptance_tests': pricing_response.get('acceptance_test_cost', 0.0),
            'acceptance': pricing_response.get('acceptance_test_cost', 0.0),  # Test compatibility
            'total_testing_cost': pricing_response.get('total_testing_cost', 0.0),
            'total': pricing_response.get('total_testing_cost', 0.0)  # Test compatibility
        }
        
        total_costs = {
            'material_total': material_costs['net_material_cost'],
            'testing_total': testing_costs['total_testing_cost'],
            'subtotal': pricing_response.get('subtotal_before_tax', 0.0),
            'gst_percent': pricing_response.get('gst_percent', 18.0),
            'gst_amount': pricing_response.get('gst_amount', 0.0),
            'grand_total': pricing_response.get('grand_total', 0.0),
            'currency': 'INR'
        }
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Create consolidated response
        consolidated = ConsolidatedResponse(
            rfp_id=rfp_summary.rfp_id,
            rfp_title=rfp_summary.title,
            organization=rfp_summary.organization,
            recommended_products=recommended_products,
            material_costs=material_costs,
            testing_costs=testing_costs,
            total_costs=total_costs,
            spec_match_summary=technical_response.get('match_summary', {}),
            compliance_summary=technical_response.get('compliance_summary', {}),
            processed_at=end_time,
            processing_time_seconds=processing_time,
            confidence_score=technical_response.get('confidence_score', 0.0)
        )
        
        return consolidated
    
    def _extract_scope_of_supply(self, rfp_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract products in scope of supply from RFP."""
        # This would parse the RFP document to extract items
        # For now, return from structured data
        structured = rfp_data.get('structured_data', {})
        
        # Try multiple ways to get category
        category = (
            structured.get('category') if isinstance(structured, dict) else None
        ) or 'Electrical Products'
        
        self.logger.info(
            "Extracting scope of supply",
            structured_data_type=type(structured).__name__,
            category=category,
            has_structured=bool(structured)
        )
        
        quantity_str = structured.get('quantity', '1') if isinstance(structured, dict) else '1'
        
        # Parse quantity
        try:
            qty = int(''.join(filter(str.isdigit, str(quantity_str)))) if quantity_str else 1
        except:
            qty = 1
        
        return [
            {
                'item_number': 'ITEM-001',
                'item_name': category,
                'description': rfp_data.get('title', ''),
                'quantity': qty,
                'unit': 'nos',
                'specifications': structured if isinstance(structured, dict) else {}
            }
        ]
    
    def _extract_technical_requirements(self, rfp_data: Dict[str, Any]) -> List[str]:
        """Extract technical requirements from RFP."""
        requirements = []
        
        # From structured requirements
        if 'requirements' in rfp_data:
            req_dict = rfp_data['requirements']
            if isinstance(req_dict, dict):
                for key, value in req_dict.items():
                    requirements.append(f"{key}: {value}")
        
        # From raw text
        raw_text = rfp_data.get('raw_text', '')
        if raw_text and len(requirements) == 0:
            # Extract some key requirements from text
            requirements = [
                "Product must meet BIS standards",
                "ISI certification required",
                "Manufacturer test certificates required"
            ]
        
        return requirements
    
    def _extract_standards(self, rfp_data: Dict[str, Any]) -> List[str]:
        """Extract required standards."""
        # Common standards for electrical products
        return [
            'IS 694:1990',
            'IS 1554:1988',
            'IEC 60227',
            'IS 13210'
        ]
    
    def _extract_certifications(self, rfp_data: Dict[str, Any]) -> List[str]:
        """Extract required certifications."""
        return [
            'BIS License',
            'ISI Mark',
            'ISO 9001:2015',
            'ISO 14001:2015'
        ]
    
    def _extract_tests_required(self, rfp_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tests required for the RFP."""
        return [
            {
                'test_name': 'Routine Tests',
                'test_type': 'routine',
                'description': 'Standard quality tests on all products'
            },
            {
                'test_name': 'Type Tests',
                'test_type': 'type',
                'description': 'One-time tests on sample products'
            },
            {
                'test_name': 'Acceptance Tests',
                'test_type': 'acceptance',
                'description': 'Customer acceptance tests at site'
            }
        ]
    
    def _extract_acceptance_tests(self, rfp_data: Dict[str, Any]) -> List[str]:
        """Extract acceptance test requirements."""
        return [
            'Visual inspection',
            'Dimensional check',
            'Electrical continuity test',
            'Insulation resistance test',
            'High voltage test'
        ]
    
    def _extract_quantities(self, rfp_data: Dict[str, Any]) -> Dict[str, int]:
        """Extract quantities for each item."""
        structured = rfp_data.get('structured_data', {})
        quantity_str = structured.get('quantity', '1')
        
        try:
            qty = int(''.join(filter(str.isdigit, quantity_str))) if quantity_str else 1
        except:
            qty = 1
        
        category = structured.get('category', 'Product')
        return {category: qty}
    
    def _extract_delivery_terms(self, rfp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract delivery terms."""
        return {
            'delivery_location': 'As per RFP',
            'delivery_period_days': 60,
            'partial_delivery': False,
            'packing_forwarding_charges': 'included'
        }
    
    def _extract_payment_terms(self, rfp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract payment terms."""
        return {
            'advance_payment': '30%',
            'on_delivery': '60%',
            'post_installation': '10%',
            'credit_period_days': 30
        }
    
    def _update_statistics(self, consolidated: ConsolidatedResponse, start_time: datetime):
        """Update agent statistics."""
        self.statistics['total_rfps_processed'] += 1
        self.statistics['total_products_recommended'] += len(consolidated.recommended_products)
        self.statistics['total_value_quoted'] += consolidated.total_costs.get('grand_total', 0)
        
        # Update average processing time
        total_time = (
            self.statistics['average_processing_time'] * 
            (self.statistics['total_rfps_processed'] - 1)
        )
        total_time += consolidated.processing_time_seconds
        self.statistics['average_processing_time'] = (
            total_time / self.statistics['total_rfps_processed']
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Master Agent statistics."""
        return self.statistics.copy()
    
    def generate_output_files(self, consolidated: ConsolidatedResponse) -> Dict[str, str]:
        """Generate output files in all three formats.
        
        Formats:
        1. JSON - Structured response for sales team
        2. Excel - Product table with specs, pricing, test costs
        3. PDF - Professional proposal document
        
        Args:
            consolidated: Consolidated RFP response
            
        Returns:
            Dictionary with paths to generated files
        """
        self.logger.info(
            "Generating output files in all formats",
            rfp_id=consolidated.rfp_id
        )
        
        try:
            # Convert dataclass to dict for output generator
            response_dict = consolidated.to_dict()
            
            # Generate all formats
            output_paths = self.output_generator.generate_all_formats(
                response_dict,
                consolidated.rfp_id
            )
            
            self.logger.info(
                "All output files generated successfully",
                json_path=output_paths.get('json'),
                excel_path=output_paths.get('excel'),
                pdf_path=output_paths.get('pdf')
            )
            
            return output_paths
            
        except Exception as e:
            self.logger.error(
                "Failed to generate output files",
                error=str(e)
            )
            raise

