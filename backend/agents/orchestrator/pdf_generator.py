"""
PDF Report Generator and Detailed Response Compiler
Generates professional PDF reports from RFP responses.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import structlog

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, PageBreak, Image, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger = structlog.get_logger()
    logger.warning("ReportLab not available - PDF generation will be disabled")

logger = structlog.get_logger()


class PDFReportGenerator:
    """
    PDF Report Generator
    
    Features:
    - Professional PDF layouts
    - Cover page generation
    - Table of contents
    - Formatted tables
    - Charts and graphs
    - Headers and footers
    - Multi-page support
    """
    
    def __init__(self, output_dir: str = "pdf_reports"):
        """Initialize PDF generator.
        
        Args:
            output_dir: Output directory for PDF files
        """
        self.logger = logger.bind(component="PDFGenerator")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if not REPORTLAB_AVAILABLE:
            self.logger.error("ReportLab not installed - PDF generation disabled")
            self.enabled = False
        else:
            self.enabled = True
            self.logger.info("PDF Report Generator initialized")
    
    def generate_rfp_response_pdf(
        self,
        rfp_response: Dict[str, Any],
        consolidated_data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """Generate PDF report for RFP response.
        
        Args:
            rfp_response: RFP response data
            consolidated_data: Consolidated agent data
            filename: Optional custom filename
            
        Returns:
            Path to generated PDF file
        """
        if not self.enabled:
            raise RuntimeError("PDF generation not available - install reportlab")
        
        # Generate filename
        if not filename:
            response_id = rfp_response.get('response_id', 'RESPONSE')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{response_id}_{timestamp}.pdf"
        
        filepath = self.output_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        # Build content
        story = []
        styles = getSampleStyleSheet()
        
        # Add custom styles
        self._add_custom_styles(styles)
        
        # Cover Page
        story.extend(self._create_cover_page(rfp_response, styles))
        story.append(PageBreak())
        
        # Table of Contents
        story.extend(self._create_table_of_contents(styles))
        story.append(PageBreak())
        
        # Executive Summary
        story.extend(self._create_executive_summary_section(rfp_response, styles))
        story.append(PageBreak())
        
        # Technical Proposal
        story.extend(self._create_technical_section(rfp_response, styles))
        story.append(PageBreak())
        
        # Commercial Proposal
        story.extend(self._create_commercial_section(rfp_response, styles))
        story.append(PageBreak())
        
        # Compliance Matrix
        story.extend(self._create_compliance_section(rfp_response, styles))
        story.append(PageBreak())
        
        # Terms and Conditions
        story.extend(self._create_terms_section(rfp_response, styles))
        
        # Build PDF
        doc.build(story)
        
        self.logger.info(f"PDF report generated: {filepath}")
        return str(filepath)
    
    def _add_custom_styles(self, styles):
        """Add custom paragraph styles."""
        # Title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Section heading
        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # Subsection heading
        styles.add(ParagraphStyle(
            name='SubsectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2e5090'),
            spaceAfter=10,
            spaceBefore=10
        ))
    
    def _create_cover_page(self, rfp_response: Dict[str, Any], styles) -> List:
        """Create cover page."""
        content = []
        
        # Add spacing
        content.append(Spacer(1, 2*inch))
        
        # Title
        title = Paragraph("RFP RESPONSE PROPOSAL", styles['CustomTitle'])
        content.append(title)
        content.append(Spacer(1, 0.5*inch))
        
        # Response info
        rfp_id = rfp_response.get('rfp_id', 'N/A')
        response_id = rfp_response.get('response_id', 'N/A')
        customer = rfp_response.get('customer_name', 'N/A')
        generated_date = rfp_response.get('generated_at', '')
        
        if generated_date:
            try:
                dt = datetime.fromisoformat(generated_date.replace('Z', '+00:00'))
                generated_date = dt.strftime('%B %d, %Y')
            except:
                pass
        
        info_text = f"""
        <para align=center>
        <b>RFP ID:</b> {rfp_id}<br/>
        <b>Response ID:</b> {response_id}<br/>
        <b>Customer:</b> {customer}<br/>
        <b>Date:</b> {generated_date}<br/>
        </para>
        """
        
        content.append(Paragraph(info_text, styles['Normal']))
        content.append(Spacer(1, inch))
        
        # Company info
        company_text = """
        <para align=center>
        <b>Prepared by:</b><br/>
        Haki FMCG Solutions<br/>
        Automated RFP Response System<br/>
        </para>
        """
        content.append(Paragraph(company_text, styles['Normal']))
        
        return content
    
    def _create_table_of_contents(self, styles) -> List:
        """Create table of contents."""
        content = []
        
        content.append(Paragraph("TABLE OF CONTENTS", styles['SectionHeading']))
        content.append(Spacer(1, 0.3*inch))
        
        toc_items = [
            "1. Executive Summary",
            "2. Technical Proposal",
            "3. Commercial Proposal",
            "4. Compliance Matrix",
            "5. Terms and Conditions"
        ]
        
        for item in toc_items:
            content.append(Paragraph(item, styles['Normal']))
            content.append(Spacer(1, 0.1*inch))
        
        return content
    
    def _create_executive_summary_section(
        self,
        rfp_response: Dict[str, Any],
        styles
    ) -> List:
        """Create executive summary section."""
        content = []
        
        content.append(Paragraph("1. EXECUTIVE SUMMARY", styles['SectionHeading']))
        content.append(Spacer(1, 0.2*inch))
        
        # Get executive summary text
        exec_summary = rfp_response.get('executive_summary', 'Not available')
        
        # Convert to paragraphs
        for para in exec_summary.split('\n\n'):
            if para.strip():
                content.append(Paragraph(para.strip(), styles['Normal']))
                content.append(Spacer(1, 0.1*inch))
        
        return content
    
    def _create_technical_section(
        self,
        rfp_response: Dict[str, Any],
        styles
    ) -> List:
        """Create technical proposal section."""
        content = []
        
        content.append(Paragraph("2. TECHNICAL PROPOSAL", styles['SectionHeading']))
        content.append(Spacer(1, 0.2*inch))
        
        technical_proposal = rfp_response.get('technical_proposal', {})
        technical_summary = technical_proposal.get('technical_summary', {})
        
        # Standards compliance
        content.append(Paragraph("2.1 Standards Compliance", styles['SubsectionHeading']))
        
        standards = technical_summary.get('standards_met', [])
        if standards:
            standards_text = "Our products comply with the following standards:<br/>" + \
                           "<br/>".join(f"• {std}" for std in standards)
            content.append(Paragraph(standards_text, styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        # Certifications
        content.append(Paragraph("2.2 Certifications", styles['SubsectionHeading']))
        
        certifications = technical_summary.get('certifications', [])
        if certifications:
            certs_text = "All products are certified by:<br/>" + \
                        "<br/>".join(f"• {cert}" for cert in certifications)
            content.append(Paragraph(certs_text, styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        return content
    
    def _create_commercial_section(
        self,
        rfp_response: Dict[str, Any],
        styles
    ) -> List:
        """Create commercial proposal section."""
        content = []
        
        content.append(Paragraph("3. COMMERCIAL PROPOSAL", styles['SectionHeading']))
        content.append(Spacer(1, 0.2*inch))
        
        commercial_proposal = rfp_response.get('commercial_proposal', {})
        bid_summary = commercial_proposal.get('bid_summary', {})
        
        # Pricing table
        pricing_data = [
            ['Description', 'Amount (₹)'],
            ['Products Subtotal', f"{bid_summary.get('products_subtotal', 0):,.2f}"],
            ['Less: Discounts', f"-{bid_summary.get('total_discounts', 0):,.2f}"],
            ['Add: Testing Costs', f"{bid_summary.get('testing_costs_total', 0):,.2f}"],
            ['Add: Logistics', f"{bid_summary.get('logistics_total', 0):,.2f}"],
            ['Add: Installation', f"{bid_summary.get('installation_total', 0):,.2f}"],
            ['Add: GST (18%)', f"{bid_summary.get('gst_total', 0):,.2f}"],
            ['GRAND TOTAL', f"{bid_summary.get('grand_total', 0):,.2f}"]
        ]
        
        table = Table(pricing_data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e6f2ff')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(table)
        content.append(Spacer(1, 0.3*inch))
        
        # Payment terms
        payment_terms = bid_summary.get('payment_terms', 'Net 30 days')
        validity_days = bid_summary.get('validity_days', 90)
        
        terms_text = f"""
        <b>Payment Terms:</b> {payment_terms}<br/>
        <b>Price Validity:</b> {validity_days} days from date of submission
        """
        content.append(Paragraph(terms_text, styles['Normal']))
        
        return content
    
    def _create_compliance_section(
        self,
        rfp_response: Dict[str, Any],
        styles
    ) -> List:
        """Create compliance matrix section."""
        content = []
        
        content.append(Paragraph("4. COMPLIANCE MATRIX", styles['SectionHeading']))
        content.append(Spacer(1, 0.2*inch))
        
        # Note: In full implementation, would convert DataFrame to table
        content.append(Paragraph(
            "Please refer to the detailed compliance matrix in the Excel document.",
            styles['Normal']
        ))
        
        return content
    
    def _create_terms_section(
        self,
        rfp_response: Dict[str, Any],
        styles
    ) -> List:
        """Create terms and conditions section."""
        content = []
        
        content.append(Paragraph("5. TERMS AND CONDITIONS", styles['SectionHeading']))
        content.append(Spacer(1, 0.2*inch))
        
        terms = rfp_response.get('terms_and_conditions', 'Standard terms apply')
        
        # Convert to paragraphs
        for para in terms.split('\n\n'):
            if para.strip():
                content.append(Paragraph(para.strip(), styles['Normal']))
                content.append(Spacer(1, 0.1*inch))
        
        return content


class DetailedResponseCompiler:
    """
    Detailed Response Compiler
    
    Compiles comprehensive detailed responses including all supporting data.
    """
    
    def __init__(self):
        """Initialize compiler."""
        self.logger = logger.bind(component="ResponseCompiler")
        self.logger.info("Detailed Response Compiler initialized")
    
    def compile_detailed_response(
        self,
        rfp_response: Dict[str, Any],
        consolidated_data: Dict[str, Any],
        workflow_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compile detailed response with all supporting data.
        
        Args:
            rfp_response: Final RFP response
            consolidated_data: Consolidated agent data
            workflow_state: Workflow execution state
            
        Returns:
            Comprehensive detailed response
        """
        detailed_response = {
            'response_metadata': {
                'rfp_id': rfp_response.get('rfp_id'),
                'response_id': rfp_response.get('response_id'),
                'generated_at': rfp_response.get('generated_at'),
                'workflow_id': workflow_state.get('workflow_id'),
                'compilation_timestamp': datetime.now().isoformat()
            },
            
            'rfp_response': rfp_response,
            
            'agent_outputs': {
                'sales_analysis': consolidated_data.get('sales_analysis', {}),
                'technical_proposal': consolidated_data.get('technical_proposal', {}),
                'commercial_proposal': consolidated_data.get('commercial_proposal', {})
            },
            
            'execution_details': {
                'workflow_status': workflow_state.get('status'),
                'started_at': workflow_state.get('started_at'),
                'completed_at': workflow_state.get('completed_at'),
                'total_execution_time': workflow_state.get('total_execution_time'),
                'agent_execution_summary': consolidated_data.get('execution_summary', {})
            },
            
            'quality_metrics': {
                'error_count': workflow_state.get('error_count', 0),
                'warning_count': workflow_state.get('warning_count', 0)
            },
            
            'appendices': rfp_response.get('appendices', {})
        }
        
        self.logger.info("Detailed response compiled")
        return detailed_response
