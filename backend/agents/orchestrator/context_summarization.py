"""
Context-Aware Summarization and Response Formatting
Generates role-specific summaries and formats responses appropriately.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import structlog

logger = structlog.get_logger()


class SummaryType(Enum):
    """Types of summaries."""
    EXECUTIVE = "executive"  # High-level overview for executives
    TECHNICAL = "technical"  # Detailed technical summary
    COMMERCIAL = "commercial"  # Financial and commercial summary
    OPERATIONAL = "operational"  # Operational details
    COMPLIANCE = "compliance"  # Compliance and regulatory summary


class AudienceRole(Enum):
    """Target audience roles."""
    EXECUTIVE = "executive"
    TECHNICAL_MANAGER = "technical_manager"
    PROCUREMENT = "procurement"
    FINANCE = "finance"
    OPERATIONS = "operations"


@dataclass
class FormattedResponse:
    """Formatted response for specific audience."""
    audience_role: AudienceRole
    summary: str
    key_points: List[str]
    recommendations: List[str]
    next_steps: List[str]
    metadata: Dict[str, Any]


class ContextAwareSummarizer:
    """
    Context-Aware Summarization System
    
    Features:
    - Role-specific summaries
    - Intelligent content extraction
    - Key points identification
    - Recommendations generation
    - Multi-level summarization
    """
    
    def __init__(self):
        """Initialize summarizer."""
        self.logger = logger.bind(component="ContextSummarizer")
        self.logger.info("Context-Aware Summarizer initialized")
    
    def generate_executive_summary(
        self,
        consolidated_data: Dict[str, Any],
        customer_info: Dict[str, Any]
    ) -> str:
        """Generate executive summary.
        
        Args:
            consolidated_data: Consolidated agent data
            customer_info: Customer information
            
        Returns:
            Executive summary text
        """
        sales_analysis = consolidated_data.get('sales_analysis', {})
        technical_proposal = consolidated_data.get('technical_proposal', {})
        commercial_proposal = consolidated_data.get('commercial_proposal', {})
        
        # Extract key information
        customer_name = customer_info.get('name', 'Valued Customer')
        rfp_analysis = sales_analysis.get('rfp_analysis', {})
        rfp_type = rfp_analysis.get('rfp_type', 'Standard')
        estimated_value = rfp_analysis.get('estimated_value', 0)
        
        bid_summary = commercial_proposal.get('bid_summary', {})
        grand_total = bid_summary.get('grand_total', 0)
        payment_terms = bid_summary.get('payment_terms', 'Net 30 days')
        validity_days = bid_summary.get('validity_days', 90)
        
        technical_summary = technical_proposal.get('technical_summary', {})
        compliance_level = technical_summary.get('compliance_level', 'Full Compliance')
        
        # Generate summary
        summary = f"""EXECUTIVE SUMMARY

CUSTOMER: {customer_name}
RFP TYPE: {rfp_type}

PROPOSAL OVERVIEW:
We are pleased to present our comprehensive proposal in response to your Request for Proposal. 
This proposal demonstrates our capability to meet all technical requirements while delivering 
exceptional value and reliable service.

KEY HIGHLIGHTS:
• Total Proposal Value: ₹{grand_total:,.2f}
• Technical Compliance: {compliance_level}
• Payment Terms: {payment_terms}
• Proposal Validity: {validity_days} days
• Quality Certifications: ISO 9001, BIS Certified

VALUE PROPOSITION:
Our proposal offers a balanced combination of technical excellence, competitive pricing, 
and proven delivery capabilities. We have carefully analyzed your requirements and selected 
products that meet or exceed all specified standards.

COMPETITIVE ADVANTAGES:
1. Technical Expertise: Complete compliance with all technical specifications
2. Quality Assurance: Comprehensive testing and certification program
3. Reliable Delivery: Proven track record of on-time delivery
4. After-Sales Support: Dedicated support team for ongoing assistance
5. Competitive Pricing: Optimized pricing structure for best value

RISK MITIGATION:
• All products from certified manufacturers
• Comprehensive warranty and quality guarantees
• Flexible payment and delivery terms
• Established supply chain relationships

NEXT STEPS:
We are confident that our proposal represents an excellent solution for your requirements.
We look forward to discussing this proposal in detail and answering any questions you may have.

Our team is ready to begin work immediately upon approval, ensuring timely delivery and 
successful project completion.
"""
        
        self.logger.info("Executive summary generated")
        return summary
    
    def generate_technical_summary(
        self,
        technical_data: Dict[str, Any]
    ) -> str:
        """Generate technical summary.
        
        Args:
            technical_data: Technical proposal data
            
        Returns:
            Technical summary text
        """
        comparisons = technical_data.get('comparisons', [])
        technical_summary = technical_data.get('technical_summary', {})
        
        total_products = technical_summary.get('total_products', len(comparisons))
        standards_met = technical_summary.get('standards_met', [])
        certifications = technical_summary.get('certifications', [])
        
        summary = f"""TECHNICAL SUMMARY

SCOPE:
Total Products Offered: {total_products}

STANDARDS COMPLIANCE:
Our proposed products comply with the following standards:
"""
        
        for standard in standards_met:
            summary += f"• {standard}\n"
        
        summary += f"""
CERTIFICATIONS:
All products are certified by recognized authorities:
"""
        
        for cert in certifications:
            summary += f"• {cert}\n"
        
        summary += """
QUALITY ASSURANCE:
All products undergo rigorous quality testing including:
• Type tests as per applicable standards
• Routine tests for every batch
• Special tests where specified
• Third-party laboratory certification

TECHNICAL SUPPORT:
• Pre-sales technical consultation
• Installation guidance
• After-sales technical support
• Warranty service
"""
        
        self.logger.info("Technical summary generated")
        return summary
    
    def generate_commercial_summary(
        self,
        pricing_data: Dict[str, Any]
    ) -> str:
        """Generate commercial summary.
        
        Args:
            pricing_data: Pricing data
            
        Returns:
            Commercial summary text
        """
        bid_summary = pricing_data.get('bid_summary', {})
        
        products_subtotal = bid_summary.get('products_subtotal', 0)
        total_discounts = bid_summary.get('total_discounts', 0)
        testing_costs = bid_summary.get('testing_costs_total', 0)
        logistics = bid_summary.get('logistics_total', 0)
        installation = bid_summary.get('installation_total', 0)
        gst_total = bid_summary.get('gst_total', 0)
        grand_total = bid_summary.get('grand_total', 0)
        payment_terms = bid_summary.get('payment_terms', 'Net 30 days')
        validity_days = bid_summary.get('validity_days', 90)
        
        summary = f"""COMMERCIAL SUMMARY

PRICING BREAKDOWN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Products Subtotal:          ₹{products_subtotal:,.2f}
Less: Discounts:           -₹{total_discounts:,.2f}
Add: Testing Costs:         ₹{testing_costs:,.2f}
Add: Logistics:             ₹{logistics:,.2f}
Add: Installation:          ₹{installation:,.2f}
Add: GST (18%):             ₹{gst_total:,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GRAND TOTAL:                ₹{grand_total:,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PAYMENT TERMS:
{payment_terms}

PRICE VALIDITY:
This pricing is valid for {validity_days} days from the date of submission.

TERMS AND CONDITIONS:
• Prices include standard packaging and delivery
• GST at applicable rates (currently 18%)
• Payment as per agreed terms
• Delivery as per agreed schedule
• Standard warranty: 12 months from delivery

NOTES:
• Prices are ex-works/FOB as specified
• Any special requirements to be quoted separately
• Prices subject to change after validity period
"""
        
        self.logger.info("Commercial summary generated")
        return summary
    
    def format_for_audience(
        self,
        consolidated_data: Dict[str, Any],
        audience_role: AudienceRole,
        customer_info: Dict[str, Any]
    ) -> FormattedResponse:
        """Format response for specific audience role.
        
        Args:
            consolidated_data: Consolidated data
            audience_role: Target audience role
            customer_info: Customer information
            
        Returns:
            FormattedResponse
        """
        if audience_role == AudienceRole.EXECUTIVE:
            return self._format_for_executive(consolidated_data, customer_info)
        elif audience_role == AudienceRole.TECHNICAL_MANAGER:
            return self._format_for_technical(consolidated_data, customer_info)
        elif audience_role == AudienceRole.PROCUREMENT:
            return self._format_for_procurement(consolidated_data, customer_info)
        elif audience_role == AudienceRole.FINANCE:
            return self._format_for_finance(consolidated_data, customer_info)
        else:
            return self._format_for_operations(consolidated_data, customer_info)
    
    def _format_for_executive(
        self,
        consolidated_data: Dict[str, Any],
        customer_info: Dict[str, Any]
    ) -> FormattedResponse:
        """Format for executive audience."""
        summary = self.generate_executive_summary(consolidated_data, customer_info)
        
        bid_summary = consolidated_data.get('commercial_proposal', {}).get('bid_summary', {})
        grand_total = bid_summary.get('grand_total', 0)
        
        key_points = [
            f"Total Bid Value: ₹{grand_total:,.2f}",
            "Full technical compliance achieved",
            "Competitive pricing with quality focus",
            "Proven delivery capabilities",
            "Comprehensive after-sales support"
        ]
        
        recommendations = [
            "Approve proposal for detailed technical review",
            "Schedule clarification meeting if needed",
            "Initiate contract negotiations"
        ]
        
        next_steps = [
            "Review proposal with technical team",
            "Clarify any commercial terms",
            "Finalize contract and timeline"
        ]
        
        return FormattedResponse(
            audience_role=AudienceRole.EXECUTIVE,
            summary=summary,
            key_points=key_points,
            recommendations=recommendations,
            next_steps=next_steps,
            metadata={'format': 'executive', 'detail_level': 'high_level'}
        )
    
    def _format_for_technical(
        self,
        consolidated_data: Dict[str, Any],
        customer_info: Dict[str, Any]
    ) -> FormattedResponse:
        """Format for technical manager audience."""
        technical_data = consolidated_data.get('technical_proposal', {})
        summary = self.generate_technical_summary(technical_data)
        
        technical_summary = technical_data.get('technical_summary', {})
        standards = technical_summary.get('standards_met', [])
        certifications = technical_summary.get('certifications', [])
        
        key_points = [
            f"Standards Compliance: {', '.join(standards[:3])}",
            f"Certifications: {', '.join(certifications[:3])}",
            "All products from certified manufacturers",
            "Comprehensive testing program included",
            "Technical documentation provided"
        ]
        
        recommendations = [
            "Review detailed technical specifications",
            "Verify standards compliance certificates",
            "Validate testing requirements"
        ]
        
        next_steps = [
            "Technical evaluation of proposed products",
            "Review test certificates and documentation",
            "Confirm installation and commissioning plan"
        ]
        
        return FormattedResponse(
            audience_role=AudienceRole.TECHNICAL_MANAGER,
            summary=summary,
            key_points=key_points,
            recommendations=recommendations,
            next_steps=next_steps,
            metadata={'format': 'technical', 'detail_level': 'detailed'}
        )
    
    def _format_for_procurement(
        self,
        consolidated_data: Dict[str, Any],
        customer_info: Dict[str, Any]
    ) -> FormattedResponse:
        """Format for procurement audience."""
        pricing_data = consolidated_data.get('commercial_proposal', {})
        summary = self.generate_commercial_summary(pricing_data)
        
        bid_summary = pricing_data.get('bid_summary', {})
        
        key_points = [
            f"Total Value: ₹{bid_summary.get('grand_total', 0):,.2f}",
            f"Payment Terms: {bid_summary.get('payment_terms', 'Net 30 days')}",
            f"Validity: {bid_summary.get('validity_days', 90)} days",
            "Competitive pricing structure",
            "Transparent cost breakdown"
        ]
        
        recommendations = [
            "Compare pricing with budget allocation",
            "Negotiate payment terms if needed",
            "Verify delivery schedules"
        ]
        
        next_steps = [
            "Commercial evaluation and comparison",
            "Negotiate terms and conditions",
            "Prepare purchase order"
        ]
        
        return FormattedResponse(
            audience_role=AudienceRole.PROCUREMENT,
            summary=summary,
            key_points=key_points,
            recommendations=recommendations,
            next_steps=next_steps,
            metadata={'format': 'commercial', 'detail_level': 'detailed'}
        )
    
    def _format_for_finance(
        self,
        consolidated_data: Dict[str, Any],
        customer_info: Dict[str, Any]
    ) -> FormattedResponse:
        """Format for finance audience."""
        pricing_data = consolidated_data.get('commercial_proposal', {})
        bid_summary = pricing_data.get('bid_summary', {})
        
        summary = f"""FINANCIAL SUMMARY

Total Contract Value: ₹{bid_summary.get('grand_total', 0):,.2f}
GST Component: ₹{bid_summary.get('gst_total', 0):,.2f}
Payment Terms: {bid_summary.get('payment_terms', 'Net 30 days')}
Validity Period: {bid_summary.get('validity_days', 90)} days

This proposal represents a significant investment in quality infrastructure
with competitive pricing and favorable payment terms.
"""
        
        key_points = [
            f"Contract Value: ₹{bid_summary.get('grand_total', 0):,.2f}",
            f"GST: ₹{bid_summary.get('gst_total', 0):,.2f}",
            f"Payment Terms: {bid_summary.get('payment_terms', '')}",
            "Price breakdown available",
            "Standard warranty included"
        ]
        
        recommendations = [
            "Verify budget availability",
            "Review payment schedule",
            "Confirm GST compliance"
        ]
        
        next_steps = [
            "Budget allocation approval",
            "Payment terms confirmation",
            "Financial approval processing"
        ]
        
        return FormattedResponse(
            audience_role=AudienceRole.FINANCE,
            summary=summary,
            key_points=key_points,
            recommendations=recommendations,
            next_steps=next_steps,
            metadata={'format': 'financial', 'detail_level': 'summary'}
        )
    
    def _format_for_operations(
        self,
        consolidated_data: Dict[str, Any],
        customer_info: Dict[str, Any]
    ) -> FormattedResponse:
        """Format for operations audience."""
        technical_data = consolidated_data.get('technical_proposal', {})
        
        summary = """OPERATIONAL SUMMARY

This proposal includes all necessary products, installation support, and ongoing
maintenance requirements. Delivery and commissioning timelines have been optimized
for minimal operational disruption.

Key operational considerations:
• Coordinated delivery schedule
• Installation support included
• Training for operational staff
• Maintenance guidelines provided
• After-sales support available
"""
        
        key_points = [
            "Coordinated delivery schedule",
            "Installation support included",
            "Staff training available",
            "Maintenance support provided",
            "24/7 helpline access"
        ]
        
        recommendations = [
            "Review delivery logistics",
            "Plan installation schedule",
            "Arrange staff training"
        ]
        
        next_steps = [
            "Coordinate delivery schedule",
            "Prepare installation sites",
            "Arrange training sessions"
        ]
        
        return FormattedResponse(
            audience_role=AudienceRole.OPERATIONS,
            summary=summary,
            key_points=key_points,
            recommendations=recommendations,
            next_steps=next_steps,
            metadata={'format': 'operational', 'detail_level': 'practical'}
        )
