"""Confidence calculation and match explanation generator."""
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class ConfidenceFactors:
    """Factors affecting match confidence."""
    parameter_coverage: float = 0.0  # Percentage of RFP params matched
    critical_match_rate: float = 0.0  # Percentage of critical params matched
    data_quality: float = 0.0  # Quality of product data
    standards_compliance: float = 0.0  # Standards match rate
    specification_completeness: float = 0.0  # How complete the specs are
    tolerance_usage: float = 0.0  # How much tolerance was needed
    
    # Penalties
    missing_critical_penalty: float = 0.0
    missing_data_penalty: float = 0.0
    low_quality_penalty: float = 0.0


@dataclass
class MatchExplanation:
    """Detailed explanation of a match result."""
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    confidence_breakdown: Dict[str, float]
    risk_factors: List[str]
    detailed_analysis: str


class ConfidenceCalculator:
    """Calculate confidence scores and generate detailed explanations."""
    
    def __init__(self):
        """Initialize confidence calculator."""
        self.logger = logger.bind(component="ConfidenceCalculator")
        
        # Confidence weights
        self.weights = {
            'parameter_coverage': 0.25,
            'critical_match_rate': 0.30,
            'data_quality': 0.15,
            'standards_compliance': 0.20,
            'specification_completeness': 0.10
        }
    
    def calculate_confidence(
        self,
        match_result: Any,
        rfp_requirements: Dict[str, Any],
        product_specs: Dict[str, Any]
    ) -> Tuple[float, ConfidenceFactors]:
        """Calculate comprehensive confidence score.
        
        Args:
            match_result: SpecificationMatchResult object
            rfp_requirements: RFP requirements
            product_specs: Product specifications
            
        Returns:
            Tuple of (confidence_score, confidence_factors)
        """
        factors = ConfidenceFactors()
        
        # Calculate parameter coverage
        total_params = len(match_result.matched_parameters) + len(match_result.missing_parameters)
        factors.parameter_coverage = (
            len(match_result.matched_parameters) / total_params if total_params > 0 else 0.0
        )
        
        # Calculate critical match rate
        critical_matches = match_result.critical_matches
        if critical_matches:
            matched_critical = sum(1 for m in critical_matches if m.is_match)
            factors.critical_match_rate = matched_critical / len(critical_matches)
        else:
            factors.critical_match_rate = 1.0  # No critical params required
        
        # Calculate data quality
        factors.data_quality = self._calculate_data_quality(product_specs)
        
        # Calculate standards compliance
        if match_result.standard_matches:
            matched_standards = sum(1 for match in match_result.standard_matches.values() if match)
            factors.standards_compliance = matched_standards / len(match_result.standard_matches)
        else:
            factors.standards_compliance = 1.0  # No standards required
        
        # Calculate specification completeness
        factors.specification_completeness = self._calculate_completeness(product_specs)
        
        # Calculate tolerance usage (penalty for relying heavily on tolerance)
        tolerance_count = sum(
            1 for m in (match_result.critical_matches + match_result.important_matches + match_result.optional_matches)
            if m.tolerance_applied
        )
        total_matches = len(match_result.critical_matches) + len(match_result.important_matches) + len(match_result.optional_matches)
        factors.tolerance_usage = tolerance_count / total_matches if total_matches > 0 else 0.0
        
        # Apply penalties
        if len(match_result.missing_parameters) > 0:
            factors.missing_data_penalty = len(match_result.missing_parameters) * 0.05
        
        if factors.critical_match_rate < 1.0:
            factors.missing_critical_penalty = (1.0 - factors.critical_match_rate) * 0.3
        
        if factors.data_quality < 0.7:
            factors.low_quality_penalty = (0.7 - factors.data_quality) * 0.2
        
        # Calculate weighted confidence score
        confidence = (
            factors.parameter_coverage * self.weights['parameter_coverage'] +
            factors.critical_match_rate * self.weights['critical_match_rate'] +
            factors.data_quality * self.weights['data_quality'] +
            factors.standards_compliance * self.weights['standards_compliance'] +
            factors.specification_completeness * self.weights['specification_completeness']
        )
        
        # Apply tolerance penalty (reduces confidence if heavily relying on tolerance)
        confidence *= (1.0 - factors.tolerance_usage * 0.1)
        
        # Apply other penalties
        confidence -= factors.missing_data_penalty
        confidence -= factors.missing_critical_penalty
        confidence -= factors.low_quality_penalty
        
        # Clamp to [0, 1]
        confidence = max(0.0, min(1.0, confidence))
        
        self.logger.debug(
            "Calculated confidence",
            confidence=round(confidence, 3),
            parameter_coverage=round(factors.parameter_coverage, 3),
            critical_match_rate=round(factors.critical_match_rate, 3)
        )
        
        return confidence, factors
    
    def generate_explanation(
        self,
        match_result: Any,
        confidence_factors: ConfidenceFactors,
        rfp_requirements: Dict[str, Any],
        product_specs: Dict[str, Any]
    ) -> MatchExplanation:
        """Generate detailed match explanation.
        
        Args:
            match_result: SpecificationMatchResult object
            confidence_factors: ConfidenceFactors object
            rfp_requirements: RFP requirements
            product_specs: Product specifications
            
        Returns:
            MatchExplanation with detailed analysis
        """
        strengths = []
        weaknesses = []
        recommendations = []
        risk_factors = []
        
        # Analyze strengths
        if confidence_factors.critical_match_rate >= 0.9:
            strengths.append("All critical parameters are well-matched")
        
        if confidence_factors.parameter_coverage >= 0.9:
            strengths.append(f"Excellent parameter coverage ({confidence_factors.parameter_coverage:.0%})")
        
        if confidence_factors.standards_compliance >= 0.9:
            strengths.append("Full standards compliance achieved")
        
        if len(match_result.exceeded_parameters) > 0:
            strengths.append(f"Product exceeds requirements in {len(match_result.exceeded_parameters)} parameters")
        
        if confidence_factors.data_quality >= 0.8:
            strengths.append("High-quality product data available")
        
        # Analyze weaknesses with more detail
        if confidence_factors.critical_match_rate < 0.9:
            missing_critical = len([m for m in match_result.critical_matches if not m.is_match])
            if missing_critical > 0:
                weaknesses.append(f"{missing_critical} critical parameter(s) not fully matched")
                # Add specific critical parameters that failed
                failed_critical = [m.parameter_name for m in match_result.critical_matches if not m.is_match][:3]
                if failed_critical:
                    weaknesses.append(f"Failed critical checks: {', '.join(failed_critical)}")
        
        if len(match_result.missing_parameters) > 0:
            count = len(match_result.missing_parameters)
            weaknesses.append(f"{count} required parameter{'s' if count > 1 else ''} missing from product data")
            # List first few missing parameters
            if count <= 3:
                weaknesses.append(f"Missing: {', '.join(match_result.missing_parameters)}")
            else:
                weaknesses.append(f"Missing: {', '.join(match_result.missing_parameters[:3])} and {count-3} more")
        
        if len(match_result.compliance_issues) > 0:
            weaknesses.append(f"{len(match_result.compliance_issues)} compliance issue{'s' if len(match_result.compliance_issues) > 1 else ''} detected")
        
        if confidence_factors.tolerance_usage > 0.3:
            weaknesses.append(f"High tolerance usage ({confidence_factors.tolerance_usage:.0%}) - borderline match")
        
        if confidence_factors.data_quality < 0.7:
            weaknesses.append(f"Product data quality below standard ({confidence_factors.data_quality:.0%})")
        
        if confidence_factors.specification_completeness < 0.6:
            weaknesses.append(f"Incomplete specifications ({confidence_factors.specification_completeness:.0%} complete)")
        
        # Check for low scores in important areas
        if match_result.technical_score < 0.7:
            weaknesses.append(f"Technical score below threshold ({match_result.technical_score:.0%})")
        
        if match_result.compliance_score < 0.7:
            weaknesses.append(f"Compliance score below threshold ({match_result.compliance_score:.0%})")
        
        # Generate recommendations
        if len(match_result.missing_parameters) > 0:
            recommendations.append(
                f"Request additional specifications for: {', '.join(match_result.missing_parameters[:3])}"
            )
        
        if match_result.compliance_issues:
            recommendations.append("Verify compliance requirements with vendor")
        
        if confidence_factors.critical_match_rate < 1.0:
            recommendations.append("Review critical parameter mismatches before proceeding")
        
        if confidence_factors.tolerance_usage > 0.5:
            recommendations.append("Confirm with vendor that tolerance-based matches are acceptable")
        
        # Identify risk factors
        if match_result.match_status.value == "no_match":
            risk_factors.append("Critical parameters do not meet requirements")
        
        if confidence_factors.standards_compliance < 0.8:
            risk_factors.append("Standards compliance below acceptable threshold")
        
        if len(match_result.missing_parameters) > 5:
            risk_factors.append("Significant data gaps in product specifications")
        
        if confidence_factors.missing_critical_penalty > 0.1:
            risk_factors.append("Missing or mismatched critical parameters pose high risk")
        
        # Generate summary
        summary = self._generate_summary(match_result, confidence_factors)
        
        # Generate detailed analysis
        detailed_analysis = self._generate_detailed_analysis(
            match_result, confidence_factors, strengths, weaknesses
        )
        
        # Create confidence breakdown
        confidence_breakdown = {
            'Parameter Coverage': confidence_factors.parameter_coverage,
            'Critical Match Rate': confidence_factors.critical_match_rate,
            'Data Quality': confidence_factors.data_quality,
            'Standards Compliance': confidence_factors.standards_compliance,
            'Specification Completeness': confidence_factors.specification_completeness,
            'Tolerance Penalty': -confidence_factors.tolerance_usage * 0.1,
            'Missing Data Penalty': -confidence_factors.missing_data_penalty,
            'Missing Critical Penalty': -confidence_factors.missing_critical_penalty,
            'Data Quality Penalty': -confidence_factors.low_quality_penalty
        }
        
        return MatchExplanation(
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            confidence_breakdown=confidence_breakdown,
            risk_factors=risk_factors,
            detailed_analysis=detailed_analysis
        )
    
    def _calculate_data_quality(self, specs: Dict[str, Any]) -> float:
        """Calculate data quality score.
        
        Args:
            specs: Product specifications
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        quality_score = 0.0
        checks = 0
        
        # Check for essential fields
        essential_fields = ['product_name', 'brand', 'category']
        for field in essential_fields:
            checks += 1
            if field in specs and specs[field]:
                quality_score += 1.0
        
        # Check for specifications dict
        if 'specifications' in specs:
            checks += 1
            if isinstance(specs['specifications'], dict) and specs['specifications']:
                quality_score += 1.0
        
        # Check for standards/certifications
        for field in ['standards', 'certifications', 'standard', 'certification']:
            if field in specs and specs[field]:
                checks += 1
                quality_score += 1.0
                break
        
        # Check for pricing data
        if any(field in specs for field in ['mrp', 'selling_price', 'price']):
            checks += 1
            quality_score += 1.0
        
        return quality_score / checks if checks > 0 else 0.5
    
    def _calculate_completeness(self, specs: Dict[str, Any]) -> float:
        """Calculate specification completeness.
        
        Args:
            specs: Product specifications
            
        Returns:
            Completeness score (0.0 to 1.0)
        """
        # Count non-null fields
        total_fields = len(specs)
        if total_fields == 0:
            return 0.0
        
        filled_fields = sum(1 for v in specs.values() if v is not None and v != '')
        
        return filled_fields / total_fields
    
    def _generate_summary(
        self,
        match_result: Any,
        confidence_factors: ConfidenceFactors
    ) -> str:
        """Generate summary text.
        
        Args:
            match_result: Match result
            confidence_factors: Confidence factors
            
        Returns:
            Summary string
        """
        status = match_result.match_status.value.replace('_', ' ').title()
        score = match_result.overall_score
        
        if score >= 0.9:
            quality = "Excellent"
        elif score >= 0.75:
            quality = "Good"
        elif score >= 0.6:
            quality = "Fair"
        else:
            quality = "Poor"
        
        summary = f"{quality} match with {score:.0%} overall score. "
        summary += f"Status: {status}. "
        
        if confidence_factors.critical_match_rate >= 0.9:
            summary += "All critical requirements met. "
        else:
            summary += f"Critical match rate: {confidence_factors.critical_match_rate:.0%}. "
        
        if match_result.recommended:
            summary += "Recommended for consideration."
        else:
            summary += "Review required before proceeding."
        
        return summary
    
    def _generate_detailed_analysis(
        self,
        match_result: Any,
        confidence_factors: ConfidenceFactors,
        strengths: List[str],
        weaknesses: List[str]
    ) -> str:
        """Generate detailed analysis text.
        
        Args:
            match_result: Match result
            confidence_factors: Confidence factors
            strengths: List of strengths
            weaknesses: List of weaknesses
            
        Returns:
            Detailed analysis string
        """
        lines = []
        
        lines.append("DETAILED MATCH ANALYSIS")
        lines.append("=" * 60)
        lines.append("")
        
        # Overall assessment
        lines.append("Overall Assessment:")
        lines.append(f"  • Match Score: {match_result.overall_score:.1%}")
        lines.append(f"  • Technical Score: {match_result.technical_score:.1%}")
        lines.append(f"  • Compliance Score: {match_result.compliance_score:.1%}")
        lines.append(f"  • Confidence Level: {match_result.confidence_level.upper()}")
        lines.append("")
        
        # Parameter analysis
        lines.append("Parameter Analysis:")
        lines.append(f"  • Matched: {len(match_result.matched_parameters)}")
        lines.append(f"  • Missing: {len(match_result.missing_parameters)}")
        lines.append(f"  • Exceeded: {len(match_result.exceeded_parameters)}")
        lines.append(f"  • Critical Matches: {len(match_result.critical_matches)}")
        lines.append(f"  • Important Matches: {len(match_result.important_matches)}")
        lines.append("")
        
        # Strengths
        if strengths:
            lines.append("Strengths:")
            for strength in strengths:
                lines.append(f"  ✓ {strength}")
            lines.append("")
        
        # Weaknesses
        if weaknesses:
            lines.append("Weaknesses:")
            for weakness in weaknesses:
                lines.append(f"  ✗ {weakness}")
            lines.append("")
        
        # Confidence factors
        lines.append("Confidence Factors:")
        lines.append(f"  • Parameter Coverage: {confidence_factors.parameter_coverage:.0%}")
        lines.append(f"  • Critical Match Rate: {confidence_factors.critical_match_rate:.0%}")
        lines.append(f"  • Data Quality: {confidence_factors.data_quality:.0%}")
        lines.append(f"  • Standards Compliance: {confidence_factors.standards_compliance:.0%}")
        lines.append(f"  • Specification Completeness: {confidence_factors.specification_completeness:.0%}")
        
        return "\n".join(lines)
