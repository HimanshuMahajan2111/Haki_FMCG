"""Matching engine for RFP requirements and product specifications."""

from matching.specification_matcher import (
    SpecificationMatcher,
    ParameterMatch,
    SpecificationMatchResult,
    ParameterType,
    MatchStatus
)
from matching.weighted_scorer import WeightedScorer, WeightConfig
from matching.parameter_extractor import ParameterExtractor
from matching.confidence_calculator import (
    ConfidenceCalculator,
    ConfidenceFactors,
    MatchExplanation
)
from matching.score_aggregator import ScoreAggregator, AggregatedScore

__all__ = [
    'SpecificationMatcher',
    'ParameterMatch',
    'SpecificationMatchResult',
    'ParameterType',
    'MatchStatus',
    'WeightedScorer',
    'WeightConfig',
    'ParameterExtractor',
    'ConfidenceCalculator',
    'ConfidenceFactors',
    'MatchExplanation',
    'ScoreAggregator',
    'AggregatedScore'
]
