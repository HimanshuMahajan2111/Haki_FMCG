"""Score aggregation and normalization utilities."""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class AggregatedScore:
    """Aggregated score with breakdown."""
    overall_score: float
    component_scores: Dict[str, float]
    weighted_scores: Dict[str, float]
    normalization_applied: bool
    score_distribution: Dict[str, float]  # Min, max, mean, std
    outlier_count: int


class ScoreAggregator:
    """Aggregate and normalize scores from multiple sources."""
    
    def __init__(self):
        """Initialize score aggregator."""
        self.logger = logger.bind(component="ScoreAggregator")
    
    def aggregate_match_scores(
        self,
        technical_score: float,
        compliance_score: float,
        pricing_score: Optional[float] = None,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> AggregatedScore:
        """Aggregate multiple score dimensions.
        
        Args:
            technical_score: Technical specification match score
            compliance_score: Standards compliance score
            pricing_score: Optional pricing competitiveness score
            custom_weights: Optional custom weights for each dimension
            
        Returns:
            AggregatedScore with breakdown
        """
        # Default weights
        if pricing_score is not None:
            default_weights = {
                'technical': 0.50,
                'compliance': 0.30,
                'pricing': 0.20
            }
        else:
            default_weights = {
                'technical': 0.70,
                'compliance': 0.30
            }
        
        weights = custom_weights or default_weights
        
        # Normalize weights to sum to 1.0
        total_weight = sum(weights.values())
        normalized_weights = {k: v/total_weight for k, v in weights.items()}
        
        # Component scores
        component_scores = {
            'technical': technical_score,
            'compliance': compliance_score
        }
        
        if pricing_score is not None:
            component_scores['pricing'] = pricing_score
        
        # Calculate weighted scores
        weighted_scores = {
            key: score * normalized_weights.get(key, 0)
            for key, score in component_scores.items()
        }
        
        # Overall score
        overall = sum(weighted_scores.values())
        
        # Score distribution stats
        scores_list = list(component_scores.values())
        distribution = {
            'min': min(scores_list),
            'max': max(scores_list),
            'mean': sum(scores_list) / len(scores_list),
            'range': max(scores_list) - min(scores_list)
        }
        
        # Detect outliers (scores more than 0.3 away from mean)
        mean = distribution['mean']
        outliers = sum(1 for s in scores_list if abs(s - mean) > 0.3)
        
        self.logger.debug(
            "Aggregated scores",
            overall=round(overall, 3),
            technical=round(technical_score, 3),
            compliance=round(compliance_score, 3)
        )
        
        return AggregatedScore(
            overall_score=overall,
            component_scores=component_scores,
            weighted_scores=weighted_scores,
            normalization_applied=total_weight != 1.0,
            score_distribution=distribution,
            outlier_count=outliers
        )
    
    def aggregate_parameter_scores(
        self,
        parameter_matches: List[Any],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Aggregate scores from multiple parameter matches.
        
        Args:
            parameter_matches: List of ParameterMatch objects
            weights: Optional parameter-specific weights
            
        Returns:
            Dictionary with aggregated statistics
        """
        if not parameter_matches:
            return {
                'average_score': 0.0,
                'median_score': 0.0,
                'min_score': 0.0,
                'max_score': 0.0,
                'match_rate': 0.0
            }
        
        scores = [m.match_score for m in parameter_matches]
        matched_count = sum(1 for m in parameter_matches if m.is_match)
        
        # Calculate weighted average if weights provided
        if weights:
            weighted_sum = sum(
                m.match_score * weights.get(m.parameter_name, 1.0)
                for m in parameter_matches
            )
            weight_sum = sum(
                weights.get(m.parameter_name, 1.0)
                for m in parameter_matches
            )
            average = weighted_sum / weight_sum if weight_sum > 0 else 0.0
        else:
            average = sum(scores) / len(scores)
        
        # Median
        sorted_scores = sorted(scores)
        mid = len(sorted_scores) // 2
        if len(sorted_scores) % 2 == 0:
            median = (sorted_scores[mid-1] + sorted_scores[mid]) / 2
        else:
            median = sorted_scores[mid]
        
        return {
            'average_score': average,
            'median_score': median,
            'min_score': min(scores),
            'max_score': max(scores),
            'match_rate': matched_count / len(parameter_matches),
            'total_parameters': len(parameter_matches),
            'matched_parameters': matched_count
        }
    
    def normalize_scores(
        self,
        scores: List[float],
        method: str = 'minmax'
    ) -> List[float]:
        """Normalize a list of scores.
        
        Args:
            scores: List of scores to normalize
            method: Normalization method ('minmax', 'zscore', 'decimal')
            
        Returns:
            List of normalized scores
        """
        if not scores:
            return []
        
        if method == 'minmax':
            min_score = min(scores)
            max_score = max(scores)
            if max_score == min_score:
                return [1.0] * len(scores)
            return [(s - min_score) / (max_score - min_score) for s in scores]
        
        elif method == 'zscore':
            mean = sum(scores) / len(scores)
            variance = sum((s - mean) ** 2 for s in scores) / len(scores)
            std = variance ** 0.5
            if std == 0:
                return [0.5] * len(scores)
            return [(s - mean) / std for s in scores]
        
        elif method == 'decimal':
            max_score = max(scores)
            if max_score == 0:
                return [0.0] * len(scores)
            return [s / max_score for s in scores]
        
        else:
            raise ValueError(f"Unknown normalization method: {method}")
    
    def calculate_score_variance(
        self,
        match_results: List[Any]
    ) -> Dict[str, float]:
        """Calculate variance in scores across multiple matches.
        
        Args:
            match_results: List of SpecificationMatchResult objects
            
        Returns:
            Dictionary with variance statistics
        """
        if not match_results:
            return {'variance': 0.0, 'std_dev': 0.0, 'coefficient_of_variation': 0.0}
        
        scores = [r.overall_score for r in match_results]
        mean = sum(scores) / len(scores)
        
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        
        # Coefficient of variation (relative std dev)
        cv = (std_dev / mean) if mean > 0 else 0.0
        
        return {
            'variance': variance,
            'std_dev': std_dev,
            'coefficient_of_variation': cv,
            'mean': mean,
            'score_spread': max(scores) - min(scores)
        }
    
    def rank_by_composite_score(
        self,
        match_results: List[Any],
        ranking_criteria: Optional[Dict[str, float]] = None
    ) -> List[tuple]:
        """Rank matches by composite score with custom criteria.
        
        Args:
            match_results: List of match results
            ranking_criteria: Optional criteria weights
            
        Returns:
            List of (rank, match_result, composite_score) tuples
        """
        if not match_results:
            return []
        
        # Enhanced default ranking criteria
        if ranking_criteria is None:
            ranking_criteria = {
                'overall_score': 0.35,
                'technical_score': 0.25,
                'compliance_score': 0.20,
                'confidence': 0.12,
                'exceeded_params': 0.05,
                'critical_pass': 0.03
            }
        
        # Calculate composite score for each result
        ranked = []
        for result in match_results:
            composite = 0.0
            
            # Map confidence level to numeric value
            confidence_map = {'high': 1.0, 'medium': 0.7, 'low': 0.4}
            confidence_value = confidence_map.get(getattr(result, 'confidence_level', 'medium'), 0.5)
            
            # Base scores
            composite += result.overall_score * ranking_criteria.get('overall_score', 0)
            composite += result.technical_score * ranking_criteria.get('technical_score', 0)
            composite += result.compliance_score * ranking_criteria.get('compliance_score', 0)
            composite += confidence_value * ranking_criteria.get('confidence', 0)
            
            # Bonus for exceeded parameters
            if hasattr(result, 'exceeded_parameters'):
                exceeded_bonus = min(len(result.exceeded_parameters) * 0.02, 0.1)
                composite += exceeded_bonus * ranking_criteria.get('exceeded_params', 0) * 20
            
            # Critical parameters pass rate
            if hasattr(result, 'critical_matches') and result.critical_matches:
                critical_pass = sum(1 for m in result.critical_matches if m.is_match) / len(result.critical_matches)
                composite += critical_pass * ranking_criteria.get('critical_pass', 0)
            
            # Penalty for missing parameters
            if hasattr(result, 'missing_parameters'):
                missing_penalty = len(result.missing_parameters) * 0.02
                composite -= missing_penalty
            
            # Penalty for compliance issues
            if hasattr(result, 'compliance_issues'):
                compliance_penalty = len(result.compliance_issues) * 0.03
                composite -= compliance_penalty
            
            # Bonus for recommended products
            if getattr(result, 'recommended', False):
                composite *= 1.05
            
            # Ensure composite score stays reasonable
            composite = max(0.0, min(1.5, composite))
            
            ranked.append((result, composite))
        
        # Sort by composite score (descending)
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        # Add rank numbers
        return [(i+1, result, score) for i, (result, score) in enumerate(ranked)]
    
    def apply_business_rules(
        self,
        aggregated_score: AggregatedScore,
        match_result: Any
    ) -> float:
        """Apply business rules to adjust final score.
        
        Args:
            aggregated_score: Aggregated score object
            match_result: Match result
            
        Returns:
            Adjusted score
        """
        score = aggregated_score.overall_score
        
        # Rule 1: Bonus for high variance (well-rounded match)
        if aggregated_score.score_distribution['range'] < 0.2:
            score *= 1.05
            self.logger.debug("Applied bonus: well-rounded match")
        
        # Rule 2: Penalty for outliers
        if aggregated_score.outlier_count > 0:
            penalty = aggregated_score.outlier_count * 0.03
            score *= (1 - penalty)
            self.logger.debug(f"Applied penalty: {aggregated_score.outlier_count} outliers")
        
        # Rule 3: Boost for exceeded requirements
        if len(match_result.exceeded_parameters) >= 3:
            score *= 1.08
            self.logger.debug("Applied bonus: exceeds multiple requirements")
        
        # Rule 4: Penalty for missing critical
        missing_critical = len([m for m in match_result.critical_matches if not m.is_match])
        if missing_critical > 0:
            score *= (1 - missing_critical * 0.15)
            self.logger.debug(f"Applied penalty: {missing_critical} missing critical params")
        
        # Rule 5: Compliance threshold
        if aggregated_score.component_scores.get('compliance', 1.0) < 0.7:
            score *= 0.85
            self.logger.debug("Applied penalty: low compliance score")
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))
