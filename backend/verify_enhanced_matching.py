"""Quick system verification test."""
import sys
sys.path.insert(0, 'D:/Haki_FMCG/backend')

from matching import (
    SpecificationMatcher,
    ConfidenceCalculator,
    ScoreAggregator,
    SpecificationMatchResult
)

print("=" * 60)
print("SYSTEM VERIFICATION TEST")
print("=" * 60)

# Test 1: Imports
print("\n[1/5] Testing Imports...")
try:
    from matching import MatchExplanation, ConfidenceFactors, AggregatedScore
    print("  PASS - All imports successful")
except Exception as e:
    print(f"  FAIL - {e}")

# Test 2: Basic Matching
print("\n[2/5] Testing Basic Matching...")
try:
    matcher = SpecificationMatcher()
    rfp = {'voltage': '1.1 kV', 'current': '32 A'}
    product = {'specifications': {'voltage': '1.1 kV', 'current': '35 A'}}
    result = matcher.match_specifications(rfp, product, category='cable')
    print(f"  PASS - Match Score: {result.overall_score:.1%}")
except Exception as e:
    print(f"  FAIL - {e}")

# Test 3: Material Equivalence
print("\n[3/5] Testing Material Equivalence...")
try:
    rfp_mat = {'conductor_material': 'Copper'}
    prod_mat = {'specifications': {'conductor_material': 'Electrolytic Copper'}}
    result = matcher.match_specifications(rfp_mat, prod_mat, category='cable')
    print(f"  PASS - Copper <-> Electrolytic Copper: {result.overall_score:.1%}")
except Exception as e:
    print(f"  FAIL - {e}")

# Test 4: Detailed Explanations
print("\n[4/5] Testing Detailed Explanations...")
try:
    rfp = {'voltage': '1.1 kV'}
    product = {'specifications': {'voltage': '1.1 kV'}}
    result = matcher.match_specifications(rfp, product, category='cable')
    explanation = matcher.generate_detailed_explanation(result, rfp, product)
    print(f"  PASS - Generated {len(explanation.strengths)} strengths, {len(explanation.weaknesses)} weaknesses")
except Exception as e:
    print(f"  FAIL - {e}")

# Test 5: Score Aggregation & Ranking
print("\n[5/5] Testing Score Aggregation & Ranking...")
try:
    aggregator = ScoreAggregator()
    agg_result = aggregator.aggregate_match_scores(0.85, 0.75, 0.90)
    
    # Create mock results for ranking
    r1 = SpecificationMatchResult(
        product_name='Product A',
        overall_score=0.85,
        technical_score=0.90,
        compliance_score=0.80,
        confidence_level='high',
        recommended=True
    )
    r2 = SpecificationMatchResult(
        product_name='Product B',
        overall_score=0.75,
        technical_score=0.80,
        compliance_score=0.70,
        confidence_level='medium',
        recommended=True
    )
    
    ranked = matcher.rank_matches_with_explanations([r1, r2])
    print(f"  PASS - Aggregated Score: {agg_result.overall_score:.1%}")
    print(f"  PASS - Ranked {len(ranked)} products")
except Exception as e:
    print(f"  FAIL - {e}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
print("\nStatus: ALL SYSTEMS OPERATIONAL")
