"""
RFP Summary Generator - NLP-based summarization and key point extraction.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import structlog

logger = structlog.get_logger()


@dataclass
class RFPSummary:
    """RFP summary with key information."""
    rfp_id: str
    executive_summary: str
    key_points: List[str]
    technical_requirements: List[str]
    critical_dates: List[str]
    estimated_scope: str
    risk_factors: List[str]
    opportunity_score: float  # 0-10
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'rfp_id': self.rfp_id,
            'executive_summary': self.executive_summary,
            'key_points': self.key_points,
            'technical_requirements': self.technical_requirements,
            'critical_dates': self.critical_dates,
            'estimated_scope': self.estimated_scope,
            'risk_factors': self.risk_factors,
            'opportunity_score': self.opportunity_score
        }


class RFPSummarizer:
    """Generate summaries and extract key points from RFPs."""
    
    def __init__(self, use_transformers: bool = False):
        """Initialize summarizer.
        
        Args:
            use_transformers: Whether to use Hugging Face transformers
        """
        self.logger = logger.bind(component="RFPSummarizer")
        self.use_transformers = use_transformers
        self.summarizer = None
        
        if use_transformers:
            self._init_transformer()
        
        self.logger.info("RFP summarizer initialized", use_transformers=use_transformers)
    
    def _init_transformer(self):
        """Initialize transformer model."""
        try:
            from transformers import pipeline
            self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            self.logger.info("Transformer model loaded")
        except Exception as e:
            self.logger.warning("Failed to load transformer", error=str(e))
            self.use_transformers = False
    
    def generate_summary(self, scraped_rfp) -> RFPSummary:
        """Generate comprehensive summary for an RFP.
        
        Args:
            scraped_rfp: ScrapedRFP object
            
        Returns:
            RFPSummary object
        """
        self.logger.info("Generating RFP summary", title=scraped_rfp.title)
        
        # Create executive summary
        executive_summary = self._create_executive_summary(scraped_rfp)
        
        # Extract key points
        key_points = self._extract_key_points(scraped_rfp)
        
        # Extract technical requirements
        tech_requirements = scraped_rfp.technical_requirements or []
        
        # Extract critical dates
        critical_dates = self._extract_critical_dates(scraped_rfp)
        
        # Estimate scope
        scope = self._estimate_scope(scraped_rfp)
        
        # Identify risk factors
        risks = self._identify_risks(scraped_rfp)
        
        # Calculate opportunity score
        opportunity_score = self._calculate_opportunity_score(scraped_rfp)
        
        return RFPSummary(
            rfp_id=scraped_rfp.tender_number or scraped_rfp.url,
            executive_summary=executive_summary,
            key_points=key_points,
            technical_requirements=tech_requirements,
            critical_dates=critical_dates,
            estimated_scope=scope,
            risk_factors=risks,
            opportunity_score=opportunity_score
        )
    
    def _create_executive_summary(self, scraped_rfp) -> str:
        """Create executive summary."""
        if self.use_transformers and self.summarizer:
            # Use transformer for summarization
            text = f"{scraped_rfp.title}. {scraped_rfp.description}"
            if len(text) > 100:
                try:
                    result = self.summarizer(text[:1024], max_length=150, min_length=50, do_sample=False)
                    return result[0]['summary_text']
                except:
                    pass
        
        # Fallback: Rule-based summarization
        summary_parts = []
        
        summary_parts.append(f"Organization: {scraped_rfp.organization}")
        
        if scraped_rfp.categories:
            summary_parts.append(f"Categories: {', '.join(scraped_rfp.categories)}")
        
        if scraped_rfp.estimated_value:
            summary_parts.append(f"Estimated Value: INR {scraped_rfp.estimated_value:,.0f}")
        
        if scraped_rfp.submission_deadline:
            summary_parts.append(f"Deadline: {scraped_rfp.submission_deadline.strftime('%B %d, %Y')}")
        
        # Add first sentence of description
        if scraped_rfp.description:
            first_sentence = scraped_rfp.description.split('.')[0] + '.'
            if len(first_sentence) < 200:
                summary_parts.append(first_sentence)
        
        return " | ".join(summary_parts)
    
    def _extract_key_points(self, scraped_rfp) -> List[str]:
        """Extract key points from RFP."""
        key_points = []
        
        # Title as first key point
        key_points.append(f"Project: {scraped_rfp.title}")
        
        # Value and scale
        if scraped_rfp.estimated_value:
            if scraped_rfp.estimated_value > 10000000:
                scale = "Large-scale"
            elif scraped_rfp.estimated_value > 1000000:
                scale = "Medium-scale"
            else:
                scale = "Small-scale"
            key_points.append(f"{scale} project valued at INR {scraped_rfp.estimated_value:,.0f}")
        
        # Categories
        if scraped_rfp.categories:
            key_points.append(f"Focus areas: {', '.join(scraped_rfp.categories)}")
        
        # Certifications required
        if scraped_rfp.certifications:
            key_points.append(f"Certifications required: {', '.join(scraped_rfp.certifications)}")
        
        # Technical requirements
        if scraped_rfp.technical_requirements:
            key_points.append(f"{len(scraped_rfp.technical_requirements)} technical requirements specified")
        
        # Documents
        if scraped_rfp.document_urls:
            key_points.append(f"{len(scraped_rfp.document_urls)} supporting documents available")
        
        return key_points
    
    def _extract_critical_dates(self, scraped_rfp) -> List[str]:
        """Extract critical dates."""
        dates = []
        
        if scraped_rfp.published_date:
            dates.append(f"Published: {scraped_rfp.published_date.strftime('%B %d, %Y')}")
        
        if scraped_rfp.submission_deadline:
            dates.append(f"Submission Deadline: {scraped_rfp.submission_deadline.strftime('%B %d, %Y')}")
            
            # Calculate days remaining
            from datetime import datetime
            days_remaining = (scraped_rfp.submission_deadline - datetime.now()).days
            if days_remaining > 0:
                dates.append(f"Days Remaining: {days_remaining}")
            else:
                dates.append("DEADLINE PASSED")
        
        if scraped_rfp.opening_date:
            dates.append(f"Opening Date: {scraped_rfp.opening_date.strftime('%B %d, %Y')}")
        
        return dates
    
    def _estimate_scope(self, scraped_rfp) -> str:
        """Estimate project scope."""
        scope_indicators = []
        
        # Value-based scope
        if scraped_rfp.estimated_value:
            if scraped_rfp.estimated_value > 10000000:
                scope_indicators.append("High-value")
            if scraped_rfp.estimated_value > 50000000:
                scope_indicators.append("Strategic")
        
        # Complexity indicators
        if scraped_rfp.technical_requirements and len(scraped_rfp.technical_requirements) > 10:
            scope_indicators.append("Complex technical requirements")
        
        if scraped_rfp.certifications and len(scraped_rfp.certifications) > 3:
            scope_indicators.append("Multiple certifications needed")
        
        # Category-based scope
        if scraped_rfp.categories:
            if len(scraped_rfp.categories) > 3:
                scope_indicators.append("Multi-domain")
        
        if not scope_indicators:
            return "Standard scope project"
        
        return ", ".join(scope_indicators)
    
    def _identify_risks(self, scraped_rfp) -> List[str]:
        """Identify potential risk factors."""
        risks = []
        
        # Deadline risk
        if scraped_rfp.submission_deadline:
            from datetime import datetime
            days_remaining = (scraped_rfp.submission_deadline - datetime.now()).days
            if days_remaining < 7:
                risks.append("CRITICAL: Less than 7 days to submit")
            elif days_remaining < 14:
                risks.append("SHORT DEADLINE: Less than 2 weeks")
        
        # Certification risk
        if scraped_rfp.certifications:
            high_barrier_certs = ['ISI', 'BIS', 'ISO', 'CE', 'UL']
            required_high_barrier = [c for c in scraped_rfp.certifications if any(hb in c for hb in high_barrier_certs)]
            if len(required_high_barrier) > 2:
                risks.append(f"Multiple high-barrier certifications: {', '.join(required_high_barrier)}")
        
        # Complexity risk
        if scraped_rfp.technical_requirements:
            if len(scraped_rfp.technical_requirements) > 15:
                risks.append("High technical complexity with 15+ requirements")
        
        # Value risk
        if scraped_rfp.estimated_value:
            if scraped_rfp.estimated_value > 100000000:
                risks.append("Very high value project (>10 Crores) - increased competition")
        
        # Documentation risk
        if not scraped_rfp.document_urls:
            risks.append("No supporting documents found - may be incomplete RFP")
        
        if not risks:
            risks.append("No significant risks identified")
        
        return risks
    
    def _calculate_opportunity_score(self, scraped_rfp) -> float:
        """Calculate opportunity score (0-10).
        
        Scoring factors:
        - Value: 3 points max
        - Time availability: 2 points max
        - Category match: 2 points max
        - Documentation: 1 point max
        - Certifications (feasibility): 2 points max
        """
        score = 0.0
        
        # Value score (0-3)
        if scraped_rfp.estimated_value:
            if scraped_rfp.estimated_value > 50000000:
                score += 3
            elif scraped_rfp.estimated_value > 10000000:
                score += 2.5
            elif scraped_rfp.estimated_value > 1000000:
                score += 2
            else:
                score += 1
        
        # Time availability (0-2)
        if scraped_rfp.submission_deadline:
            from datetime import datetime
            days_remaining = (scraped_rfp.submission_deadline - datetime.now()).days
            if days_remaining > 30:
                score += 2
            elif days_remaining > 14:
                score += 1.5
            elif days_remaining > 7:
                score += 1
            elif days_remaining > 0:
                score += 0.5
        
        # Category match (0-2)
        target_categories = ['Electrical', 'Electronics', 'Lighting', 'Cables', 'Switchgear']
        if scraped_rfp.categories:
            matching = sum(1 for cat in scraped_rfp.categories if any(t in cat for t in target_categories))
            score += min(matching * 0.5, 2)
        
        # Documentation (0-1)
        if scraped_rfp.document_urls and len(scraped_rfp.document_urls) > 0:
            score += 1
        
        # Certification feasibility (0-2)
        if scraped_rfp.certifications:
            feasible_certs = ['ISI', 'ISO', 'BEE']
            feasible_count = sum(1 for cert in scraped_rfp.certifications if any(f in cert for f in feasible_certs))
            score += min(feasible_count * 0.5, 2)
        elif not scraped_rfp.certifications:
            score += 1  # No certifications = easier
        
        return round(min(score, 10.0), 2)
    
    def generate_comparison(self, rfp_summaries: List[RFPSummary]) -> Dict[str, Any]:
        """Generate comparison report for multiple RFPs.
        
        Args:
            rfp_summaries: List of RFPSummary objects
            
        Returns:
            Comparison dictionary
        """
        if not rfp_summaries:
            return {}
        
        # Sort by opportunity score
        sorted_summaries = sorted(rfp_summaries, key=lambda x: x.opportunity_score, reverse=True)
        
        # Extract statistics
        scores = [s.opportunity_score for s in rfp_summaries]
        avg_score = sum(scores) / len(scores)
        
        # Top recommendations
        top_3 = sorted_summaries[:3]
        
        return {
            'total_rfps': len(rfp_summaries),
            'average_opportunity_score': round(avg_score, 2),
            'top_recommendations': [
                {
                    'rfp_id': s.rfp_id,
                    'score': s.opportunity_score,
                    'summary': s.executive_summary,
                    'key_points': s.key_points
                }
                for s in top_3
            ],
            'high_risk_rfps': [
                {
                    'rfp_id': s.rfp_id,
                    'risks': s.risk_factors
                }
                for s in rfp_summaries if len(s.risk_factors) > 2
            ]
        }
