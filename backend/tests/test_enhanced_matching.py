"""Tests for enhanced matching features: confidence calculation, score aggregation, explanations."""
import pytest
import sys
sys.path.insert(0, 'D:/Haki_FMCG/backend')

from matching import (
    SpecificationMatcher,
    ConfidenceCalculator,
    ScoreAggregator,
    SpecificationMatchResult,
    ParameterMatch,
    ParameterType,
    MatchStatus
)


class TestConfidenceCalculator:
    """Test confidence calculation features."""
    
    @pytest.fixture
    def calculator(self):
        """Create confidence calculator."""
        return ConfidenceCalculator()
    
    @pytest.fixture
    def sample_match_result(self):
        """Create sample match result."""
        result = SpecificationMatchResult()
        result.overall_score = 0.85
        result.technical_score = 0.90
        result.compliance_score = 0.75
        result.match_status = MatchStatus.EXACT_MATCH
        
        # Add parameter matches
        result.critical_matches = [
            ParameterMatch('voltage', '1.1 kV', '1.1 kV', match_score=1.0, is_match=True),
            ParameterMatch('current', '32 A', '35 A', match_score=0.95, is_match=True)
        ]
        result.matched_parameters = ['voltage', 'current', 'size']
        result.missing_parameters = []
        result.exceeded_parameters = ['current']
        result.standard_matches = {'IS 1554': True, 'IS 694': True}
        result.compliance_issues = []
        
        return result
    
    def test_calculate_confidence(self, calculator, sample_match_result):
        """Test confidence score calculation."""
        confidence, factors = calculator.calculate_confidence(
            sample_match_result,
            {'voltage': '1.1 kV', 'current': '32 A'},
            {'voltage': '1.1 kV', 'current': '35 A', 'brand': 'Test'}
        )
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.7  # Should be high confidence
        assert factors.parameter_coverage > 0.9
        assert factors.critical_match_rate == 1.0
    
    def test_confidence_with_missing_parameters(self, calculator):
        """Test confidence with missing parameters."""
        result = SpecificationMatchResult()
        result.overall_score = 0.60
        result.critical_matches = []
        result.matched_parameters = ['voltage']
        result.missing_parameters = ['current', 'size', 'material']
        result.standard_matches = {}
        
        confidence, factors = calculator.calculate_confidence(
            result,
            {'voltage': '1.1 kV', 'current': '32 A', 'size': '4 sq mm', 'material': 'copper'},
            {'voltage': '1.1 kV'}
        )
        
        assert confidence < 0.6  # Low confidence due to missing data
        assert factors.missing_data_penalty > 0
    
    def test_generate_explanation(self, calculator, sample_match_result):
        """Test explanation generation."""
        confidence, factors = calculator.calculate_confidence(
            sample_match_result,
            {'voltage': '1.1 kV'},
            {'voltage': '1.1 kV', 'brand': 'Test'}
        )
        
        explanation = calculator.generate_explanation(
            sample_match_result,
            factors,
            {'voltage': '1.1 kV'},
            {'voltage': '1.1 kV'}
        )
        
        assert explanation.summary != ""
        assert len(explanation.strengths) > 0
        assert isinstance(explanation.confidence_breakdown, dict)
        assert 'Parameter Coverage' in explanation.confidence_breakdown
    
    def test_explanation_with_weaknesses(self, calculator):
        """Test explanation highlights weaknesses."""
        result = SpecificationMatchResult()
        result.overall_score = 0.55
        result.critical_matches = [
            ParameterMatch('voltage', '1.1 kV', '0.66 kV', match_score=0.5, is_match=False)
        ]
        result.matched_parameters = []
        result.missing_parameters = ['current', 'size']
        result.compliance_issues = ['Standard not met']
        
        confidence, factors = calculator.calculate_confidence(
            result,
            {'voltage': '1.1 kV', 'current': '32 A'},
            {'voltage': '0.66 kV'}
        )
        
        explanation = calculator.generate_explanation(result, factors, {}, {})
        
        assert len(explanation.weaknesses) > 0
        assert len(explanation.risk_factors) > 0
        assert len(explanation.recommendations) > 0


class TestScoreAggregator:
    """Test score aggregation features."""
    
    @pytest.fixture
    def aggregator(self):
        """Create score aggregator."""
        return ScoreAggregator()
    
    def test_aggregate_match_scores(self, aggregator):
        """Test basic score aggregation."""
        result = aggregator.aggregate_match_scores(
            technical_score=0.85,
            compliance_score=0.75
        )
        
        assert 0.0 <= result.overall_score <= 1.0
        assert result.overall_score > 0.75
        assert 'technical' in result.component_scores
        assert 'compliance' in result.component_scores
    
    def test_aggregate_with_pricing(self, aggregator):
        """Test aggregation with pricing score."""
        result = aggregator.aggregate_match_scores(
            technical_score=0.85,
            compliance_score=0.75,
            pricing_score=0.90
        )
        
        assert 'pricing' in result.component_scores
        assert 'pricing' in result.weighted_scores
        assert result.overall_score > 0.7
    
    def test_custom_weights(self, aggregator):
        """Test custom weight application."""
        result = aggregator.aggregate_match_scores(
            technical_score=0.80,
            compliance_score=0.60,
            custom_weights={'technical': 0.8, 'compliance': 0.2}
        )
        
        # Technical should dominate due to higher weight
        assert result.overall_score > 0.75
    
    def test_aggregate_parameter_scores(self, aggregator):
        """Test parameter score aggregation."""
        matches = [
            ParameterMatch('voltage', '1.1 kV', '1.1 kV', match_score=1.0, is_match=True),
            ParameterMatch('current', '32 A', '35 A', match_score=0.95, is_match=True),
            ParameterMatch('size', '4 sq mm', '4 sq mm', match_score=1.0, is_match=True)
        ]
        
        stats = aggregator.aggregate_parameter_scores(matches)
        
        assert stats['average_score'] > 0.95
        assert stats['match_rate'] == 1.0
        assert stats['total_parameters'] == 3
        assert stats['matched_parameters'] == 3
    
    def test_normalize_scores_minmax(self, aggregator):
        """Test min-max normalization."""
        scores = [0.5, 0.7, 0.9, 0.6, 0.8]
        normalized = aggregator.normalize_scores(scores, method='minmax')
        
        assert min(normalized) == 0.0
        assert max(normalized) == 1.0
        assert len(normalized) == len(scores)
    
    def test_normalize_scores_decimal(self, aggregator):
        """Test decimal normalization."""
        scores = [50, 70, 90, 60, 80]
        normalized = aggregator.normalize_scores(scores, method='decimal')
        
        assert max(normalized) == 1.0
        assert all(0 <= s <= 1 for s in normalized)
    
    def test_calculate_score_variance(self, aggregator):
        """Test score variance calculation."""
        results = [
            SpecificationMatchResult(overall_score=0.85),
            SpecificationMatchResult(overall_score=0.75),
            SpecificationMatchResult(overall_score=0.80)
        ]
        
        variance = aggregator.calculate_score_variance(results)
        
        assert 'variance' in variance
        assert 'std_dev' in variance
        assert 'mean' in variance
        assert abs(variance['mean'] - 0.80) < 0.001  # Floating point tolerance
    
    def test_rank_by_composite_score(self, aggregator):
        """Test ranking by composite score."""
        results = [
            SpecificationMatchResult(
                product_name='Product A',
                overall_score=0.75,
                technical_score=0.80,
                compliance_score=0.70,
                confidence_level='medium',
                recommended=True
            ),
            SpecificationMatchResult(
                product_name='Product B',
                overall_score=0.85,
                technical_score=0.90,
                compliance_score=0.80,
                confidence_level='high',
                recommended=True
            ),
            SpecificationMatchResult(
                product_name='Product C',
                overall_score=0.60,
                technical_score=0.65,
                compliance_score=0.55,
                confidence_level='low',
                recommended=False
            )
        ]
        
        ranked = aggregator.rank_by_composite_score(results)
        
        assert len(ranked) == 3
        assert ranked[0][0] == 1  # First rank
        assert ranked[0][1].product_name == 'Product B'  # Best product
        assert ranked[2][0] == 3  # Last rank
        assert ranked[2][1].product_name == 'Product C'  # Worst product
    
    def test_apply_business_rules(self, aggregator):
        """Test business rules application."""
        from matching.score_aggregator import AggregatedScore
        
        aggregated = AggregatedScore(
            overall_score=0.75,
            component_scores={'technical': 0.80, 'compliance': 0.70},
            weighted_scores={'technical': 0.56, 'compliance': 0.21},
            normalization_applied=False,
            score_distribution={'min': 0.70, 'max': 0.80, 'mean': 0.75, 'range': 0.10},
            outlier_count=0
        )
        
        result = SpecificationMatchResult(
            exceeded_parameters=['voltage', 'current', 'size'],
            critical_matches=[],
            missing_parameters=[]
        )
        
        adjusted = aggregator.apply_business_rules(aggregated, result)
        
        # Should get bonus for exceeding requirements
        assert adjusted > aggregated.overall_score


class TestEnhancedMatchingIntegration:
    """Integration tests for enhanced matching."""
    
    @pytest.fixture
    def matcher(self):
        """Create specification matcher."""
        return SpecificationMatcher()
    
    def test_full_matching_with_explanation(self, matcher):
        """Test complete matching flow with explanation."""
        rfp = {
            'voltage_rating': '1.1 kV',
            'current_rating': '32 A',
            'conductor_size': '4 sq mm',
            'category': 'cable'
        }
        
        product = {
            'product_name': 'Test Cable',
            'specifications': {
                'voltage_rating': '1.1 kV',
                'current_rating': '35 A',
                'conductor_size': '4 sq mm'
            },
            'standards': ['IS 1554']
        }
        
        result = matcher.match_specifications(rfp, product, category='cable')
        
        # Should have confidence factors attached
        assert hasattr(result, '_confidence_factors')
        assert hasattr(result, '_aggregated_score')
        
        # Generate explanation
        explanation = matcher.generate_detailed_explanation(result, rfp, product)
        
        assert explanation.summary != ""
        assert isinstance(explanation.confidence_breakdown, dict)
        assert len(explanation.confidence_breakdown) > 0
    
    def test_ranking_with_explanations(self, matcher):
        """Test ranking multiple matches."""
        rfp = {'voltage_rating': '1.1 kV', 'current_rating': '32 A'}
        
        products = [
            {
                'product_name': 'Product A',
                'specifications': {'voltage_rating': '1.1 kV', 'current_rating': '32 A'}
            },
            {
                'product_name': 'Product B',
                'specifications': {'voltage_rating': '1.1 kV', 'current_rating': '35 A'}
            },
            {
                'product_name': 'Product C',
                'specifications': {'voltage_rating': '0.66 kV', 'current_rating': '25 A'}
            }
        ]
        
        results = [
            matcher.match_specifications(rfp, product, category='cable')
            for product in products
        ]
        
        ranked = matcher.rank_matches_with_explanations(results)
        
        assert len(ranked) == 3
        # Check ranking structure
        for rank, result, score, explanation in ranked:
            assert 1 <= rank <= 3
            assert isinstance(result, SpecificationMatchResult)
            assert 0.0 <= score <= 2.0  # Composite can exceed 1.0 with bonuses
            assert isinstance(explanation, str)
        
        # Best match should be ranked first
        assert ranked[0][0] == 1
        # Product B (exceeds) or Product A (exact) should be top
        assert ranked[0][1].product_name in ['Product A', 'Product B']


def test_confidence_factors_structure():
    """Test ConfidenceFactors dataclass."""
    from matching.confidence_calculator import ConfidenceFactors
    
    factors = ConfidenceFactors(
        parameter_coverage=0.85,
        critical_match_rate=1.0,
        data_quality=0.90
    )
    
    assert factors.parameter_coverage == 0.85
    assert factors.critical_match_rate == 1.0
    assert factors.data_quality == 0.90
    assert factors.missing_critical_penalty == 0.0


def test_match_explanation_structure():
    """Test MatchExplanation dataclass."""
    from matching.confidence_calculator import MatchExplanation
    
    explanation = MatchExplanation(
        summary="Good match",
        strengths=["High score"],
        weaknesses=["Missing data"],
        recommendations=["Verify specs"],
        confidence_breakdown={'Coverage': 0.85},
        risk_factors=["Low compliance"],
        detailed_analysis="Analysis text"
    )
    
    assert explanation.summary == "Good match"
    assert len(explanation.strengths) == 1
    assert len(explanation.weaknesses) == 1
    assert 'Coverage' in explanation.confidence_breakdown


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
