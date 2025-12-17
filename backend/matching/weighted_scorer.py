"""Weighted scoring system for parameter matching."""
from typing import Dict, List, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class WeightConfig:
    """Configuration for parameter weights."""
    critical_weight: float = 1.0
    important_weight: float = 0.7
    optional_weight: float = 0.3
    compliance_weight: float = 0.9
    
    # Scoring components
    technical_weight: float = 0.7
    compliance_component_weight: float = 0.3
    
    # Bonus/penalty factors
    exceeds_requirement_bonus: float = 0.1
    missing_critical_penalty: float = -0.5
    tolerance_penalty: float = -0.05


class WeightedScorer:
    """Weighted scoring system for specification matching."""
    
    def __init__(self, config: Optional[WeightConfig] = None):
        """Initialize weighted scorer.
        
        Args:
            config: Optional weight configuration
        """
        self.config = config or WeightConfig()
        self.logger = logger.bind(component="WeightedScorer")
    
    def calculate_weighted_score(
        self,
        matches: List[Dict],
        parameter_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Calculate weighted score from parameter matches.
        
        Args:
            matches: List of parameter match dictionaries
            parameter_weights: Optional custom parameter weights
            
        Returns:
            Dictionary with score breakdown
        """
        total_score = 0.0
        total_weight = 0.0
        
        scores = {
            'critical_score': 0.0,
            'important_score': 0.0,
            'optional_score': 0.0,
            'weighted_score': 0.0,
            'bonus': 0.0,
            'penalty': 0.0
        }
        
        critical_count = 0
        critical_matched = 0
        
        for match in matches:
            param_type = match.get('parameter_type', 'optional')
            match_score = match.get('match_score', 0.0)
            is_match = match.get('is_match', False)
            
            # Get weight for this parameter
            if parameter_weights and match['parameter_name'] in parameter_weights:
                weight = parameter_weights[match['parameter_name']]
            elif param_type == 'critical':
                weight = self.config.critical_weight
                critical_count += 1
                if is_match:
                    critical_matched += 1
            elif param_type == 'important':
                weight = self.config.important_weight
            else:
                weight = self.config.optional_weight
            
            # Add to total
            weighted_value = match_score * weight
            total_score += weighted_value
            total_weight += weight
            
            # Track by type
            if param_type == 'critical':
                scores['critical_score'] += match_score
            elif param_type == 'important':
                scores['important_score'] += match_score
            else:
                scores['optional_score'] += match_score
            
            # Apply bonuses/penalties
            if match.get('exceeded_requirement', False):
                scores['bonus'] += self.config.exceeds_requirement_bonus
            
            if param_type == 'critical' and not is_match:
                scores['penalty'] += self.config.missing_critical_penalty
            
            if match.get('tolerance_applied', False):
                scores['penalty'] += self.config.tolerance_penalty
        
        # Calculate final weighted score
        if total_weight > 0:
            scores['weighted_score'] = (total_score / total_weight) + scores['bonus'] + scores['penalty']
            scores['weighted_score'] = max(0.0, min(1.0, scores['weighted_score']))  # Clamp to [0, 1]
        
        # Normalize sub-scores
        if critical_count > 0:
            scores['critical_score'] /= critical_count
        
        scores['critical_pass_rate'] = critical_matched / critical_count if critical_count > 0 else 1.0
        
        self.logger.debug(
            "Calculated weighted score",
            weighted_score=round(scores['weighted_score'], 3),
            critical_pass_rate=round(scores['critical_pass_rate'], 3)
        )
        
        return scores
    
    def calculate_composite_score(
        self,
        technical_score: float,
        compliance_score: float,
        pricing_score: Optional[float] = None
    ) -> Dict[str, float]:
        """Calculate composite score from multiple dimensions.
        
        Args:
            technical_score: Technical matching score
            compliance_score: Standards compliance score
            pricing_score: Optional pricing competitiveness score
            
        Returns:
            Dictionary with composite scores
        """
        # Base composite (technical + compliance)
        composite = (
            technical_score * self.config.technical_weight +
            compliance_score * self.config.compliance_component_weight
        )
        
        result = {
            'technical_score': technical_score,
            'compliance_score': compliance_score,
            'composite_score': composite
        }
        
        # If pricing included, recalculate with 3-way split
        if pricing_score is not None:
            result['pricing_score'] = pricing_score
            result['composite_score'] = (
                technical_score * 0.5 +
                compliance_score * 0.25 +
                pricing_score * 0.25
            )
        
        return result
    
    def rank_matches(
        self,
        match_results: List[Dict],
        sort_by: str = 'overall_score'
    ) -> List[Dict]:
        """Rank match results by score.
        
        Args:
            match_results: List of match result dictionaries
            sort_by: Score field to sort by
            
        Returns:
            Sorted list of match results with rankings
        """
        # Sort by specified score
        sorted_results = sorted(
            match_results,
            key=lambda x: x.get(sort_by, 0.0),
            reverse=True
        )
        
        # Add rank to each result
        for rank, result in enumerate(sorted_results, 1):
            result['rank'] = rank
        
        return sorted_results
    
    def apply_business_rules(
        self,
        score: float,
        match_result: Dict
    ) -> float:
        """Apply business rules to adjust final score.
        
        Args:
            score: Base score
            match_result: Match result dictionary
            
        Returns:
            Adjusted score
        """
        adjusted_score = score
        
        # Rule 1: Boost score if all critical parameters match
        critical_matches = match_result.get('critical_matches', [])
        if critical_matches and all(m.get('is_match', False) for m in critical_matches):
            adjusted_score *= 1.1
        
        # Rule 2: Penalize if compliance issues exist
        compliance_issues = match_result.get('compliance_issues', [])
        if compliance_issues:
            penalty = len(compliance_issues) * 0.05
            adjusted_score *= (1 - penalty)
        
        # Rule 3: Boost if product exceeds requirements
        exceeded_params = match_result.get('exceeded_parameters', [])
        if len(exceeded_params) >= 3:
            adjusted_score *= 1.05
        
        # Clamp to valid range
        return max(0.0, min(1.0, adjusted_score))
