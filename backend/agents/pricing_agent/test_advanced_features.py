"""
Test all advanced pricing features
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from advanced_features import (
    WinProbabilityEstimator,
    CostComparisonGenerator,
    SensitivityAnalyzer,
    WhatIfScenarioGenerator,
    PricingApprovalWorkflow,
    PricingAPI,
    ApprovalStatus
)


def test_win_probability():
    """Test win probability estimator."""
    print("\n" + "="*80)
    print("TEST: Win Probability Estimator")
    print("="*80)
    
    estimator = WinProbabilityEstimator()
    
    # Sample bid
    our_bid = {
        'bid_summary': {
            'grand_total': 900000,  # ₹9L
            'products_subtotal': 800000,
            'total_discounts': 50000,
            'testing_costs_total': 25000,
            'logistics_total': 15000,
            'installation_total': 20000,
            'gst_total': 90000,
            'payment_terms': 'Letter of Credit - 90 days',
            'validity_days': 60
        },
        'product_pricings': [
            {'delivery_days': 20}
        ]
    }
    
    market_data = {
        'market_average': 1000000  # ₹10L market average
    }
    
    customer_info = {
        'type': 'Enterprise',
        'existing_customer': True
    }
    
    result = estimator.estimate_win_probability(our_bid, market_data, customer_info)
    
    print(f"\nWin Probability: {result.probability * 100:.1f}%")
    print(f"Confidence Level: {result.confidence}")
    print("\nFactors:")
    for factor, value in result.factors.items():
        print(f"  - {factor}: {value}")
    
    if result.recommendations:
        print("\nRecommendations:")
        for rec in result.recommendations:
            print(f"  • {rec}")
    
    assert result.probability > 0.5, "Win probability should be > 50%"
    print("\n✅ Win probability estimation passed!")
    return True


def test_cost_comparison():
    """Test cost comparison generator."""
    print("\n" + "="*80)
    print("TEST: Cost Comparison Generator")
    print("="*80)
    
    comparator = CostComparisonGenerator()
    
    our_bid = {
        'bid_summary': {
            'products_subtotal': 800000,
            'total_discounts': 50000,
            'testing_costs_total': 25000,
            'logistics_total': 15000,
            'installation_total': 20000,
            'gst_total': 90000,
            'grand_total': 900000,
            'payment_terms': 'Net 30 days',
            'validity_days': 60
        }
    }
    
    competitor_bids = [
        {
            'subtotal': 820000,
            'discounts': 30000,
            'testing': 20000,
            'logistics': 18000,
            'installation': 25000,
            'gst': 93000,
            'grand_total': 946000,
            'payment_terms': 'Net 45 days',
            'validity_days': 45
        },
        {
            'subtotal': 780000,
            'discounts': 40000,
            'testing': 30000,
            'logistics': 20000,
            'installation': 15000,
            'gst': 85000,
            'grand_total': 890000,
            'payment_terms': 'Advance 30%',
            'validity_days': 30
        }
    ]
    
    comparison_df = comparator.generate_comparison(our_bid, competitor_bids)
    
    print("\nCost Comparison Table:")
    print(comparison_df.to_string(index=False))
    
    assert len(comparison_df) == 3, "Should have 3 bids in comparison"
    print("\n✅ Cost comparison generation passed!")
    return True


def test_sensitivity_analysis():
    """Test sensitivity analyzer."""
    print("\n" + "="*80)
    print("TEST: Sensitivity Analysis")
    print("="*80)
    
    analyzer = SensitivityAnalyzer()
    
    base_bid = {
        'bid_summary': {
            'grand_total': 1000000,
            'margin_percent': 20,
            'total_discounts': 50000,
            'logistics_total': 20000
        }
    }
    
    # Test margin sensitivity
    analysis = analyzer.analyze_parameter(
        base_bid,
        'margin',
        variation_range=[-20, -10, 0, 10, 20]
    )
    
    print(f"\nParameter: {analysis.parameter}")
    print(f"Base Value: ₹{analysis.base_value:,.2f}")
    print("\nVariations:")
    for var, impact_total, impact_margin in zip(
        analysis.variations,
        analysis.impact_on_total,
        analysis.impact_on_margin
    ):
        print(f"  {var['variation_pct']:+3d}%: "
              f"New Total = ₹{var['new_value']:,.2f}, "
              f"Impact = ₹{impact_total:+,.2f}")
    
    assert len(analysis.variations) == 5, "Should have 5 variations"
    print("\n✅ Sensitivity analysis passed!")
    return True


def test_what_if_scenarios():
    """Test what-if scenario generator."""
    print("\n" + "="*80)
    print("TEST: What-If Scenario Generator")
    print("="*80)
    
    generator = WhatIfScenarioGenerator()
    
    base_bid = {
        'bid_summary': {
            'grand_total': 1000000,
            'logistics_total': 20000,
            'installation_total': 30000
        }
    }
    
    # Scenario 1: Reduce margin by 5%
    scenario1 = generator.generate_scenario(
        base_bid,
        "Competitive Pricing",
        {'margin_adjustment': -5}
    )
    
    print(f"\nScenario: {scenario1.scenario_name}")
    print(f"Changes: {scenario1.changes}")
    print(f"Original Total: ₹{scenario1.original_total:,.2f}")
    print(f"New Total: ₹{scenario1.new_total:,.2f}")
    print(f"Difference: ₹{scenario1.difference:+,.2f} ({scenario1.difference_percent:+.2f}%)")
    
    # Scenario 2: Add 10% discount
    scenario2 = generator.generate_scenario(
        base_bid,
        "Special Discount Offer",
        {'additional_discount': 10}
    )
    
    print(f"\nScenario: {scenario2.scenario_name}")
    print(f"Changes: {scenario2.changes}")
    print(f"Original Total: ₹{scenario2.original_total:,.2f}")
    print(f"New Total: ₹{scenario2.new_total:,.2f}")
    print(f"Difference: ₹{scenario2.difference:+,.2f} ({scenario2.difference_percent:+.2f}%)")
    
    # Scenario 3: Remove installation
    scenario3 = generator.generate_scenario(
        base_bid,
        "Ex-Works Pricing",
        {'remove_installation': True}
    )
    
    print(f"\nScenario: {scenario3.scenario_name}")
    print(f"Changes: {scenario3.changes}")
    print(f"Original Total: ₹{scenario3.original_total:,.2f}")
    print(f"New Total: ₹{scenario3.new_total:,.2f}")
    print(f"Difference: ₹{scenario3.difference:+,.2f} ({scenario3.difference_percent:+.2f}%)")
    
    assert scenario1.new_total < scenario1.original_total, "Margin reduction should decrease total"
    assert scenario2.new_total < scenario2.original_total, "Discount should decrease total"
    assert scenario3.new_total < scenario3.original_total, "Removing installation should decrease total"
    print("\n✅ What-if scenario generation passed!")
    return True


def test_approval_workflow():
    """Test pricing approval workflow."""
    print("\n" + "="*80)
    print("TEST: Pricing Approval Workflow")
    print("="*80)
    
    workflow = PricingApprovalWorkflow()
    
    # Test 1: Small bid (auto-approved)
    bid_summary_small = {
        'grand_total': 50000,  # ₹50K
        'margin_percent': 20
    }
    
    approval1 = workflow.submit_for_approval('BID-001', bid_summary_small, 'Sales Rep')
    print(f"\nBid BID-001 (₹50K):")
    print(f"  Status: {approval1['status']}")
    print(f"  Required Approvals: {approval1['required_approvals']}")
    assert approval1['status'] == ApprovalStatus.APPROVED.value, "Small bids should be auto-approved"
    
    # Test 2: Medium bid (manager approval)
    bid_summary_medium = {
        'grand_total': 500000,  # ₹5L
        'margin_percent': 18
    }
    
    approval2 = workflow.submit_for_approval('BID-002', bid_summary_medium, 'Sales Rep')
    print(f"\nBid BID-002 (₹5L):")
    print(f"  Status: {approval2['status']}")
    print(f"  Required Approvals: {approval2['required_approvals']}")
    assert ApprovalStatus.PENDING.value in approval2['status'], "Medium bids need approval"
    assert 'Manager' in approval2['required_approvals']
    
    # Approve by manager
    approval2_updated = workflow.approve('BID-002', 'Manager', 'Approved - good pricing')
    print(f"  After Manager Approval: {approval2_updated['status']}")
    assert approval2_updated['status'] == ApprovalStatus.APPROVED.value
    
    # Test 3: Large bid (multiple approvals)
    bid_summary_large = {
        'grand_total': 5000000,  # ₹50L
        'margin_percent': 18
    }
    
    approval3 = workflow.submit_for_approval('BID-003', bid_summary_large, 'Sales Rep')
    print(f"\nBid BID-003 (₹50L):")
    print(f"  Status: {approval3['status']}")
    print(f"  Required Approvals: {approval3['required_approvals']}")
    assert 'Manager' in approval3['required_approvals']
    assert 'Director' in approval3['required_approvals']
    
    # Partial approval
    workflow.approve('BID-003', 'Manager', 'Looks good')
    approval3_partial = workflow.get_approval_status('BID-003')
    print(f"  After Manager Approval: {approval3_partial['status']}")
    assert approval3_partial['status'] == ApprovalStatus.PENDING.value, "Still needs Director"
    
    # Complete approval
    workflow.approve('BID-003', 'Director', 'Approved')
    approval3_final = workflow.get_approval_status('BID-003')
    print(f"  After Director Approval: {approval3_final['status']}")
    assert approval3_final['status'] == ApprovalStatus.APPROVED.value
    
    # Test 4: Rejection
    bid_summary_reject = {
        'grand_total': 2000000,  # ₹20L
        'margin_percent': 10  # Low margin
    }
    
    approval4 = workflow.submit_for_approval('BID-004', bid_summary_reject, 'Sales Rep')
    print(f"\nBid BID-004 (₹20L, 10% margin):")
    print(f"  Status: {approval4['status']}")
    print(f"  Required Approvals: {approval4['required_approvals']}")
    assert 'CFO' in approval4['required_approvals'], "Low margin needs CFO approval"
    
    # Reject
    approval4_rejected = workflow.reject('BID-004', 'CFO', 'Margin too low - not sustainable')
    print(f"  After CFO Review: {approval4_rejected['status']}")
    print(f"  Rejection Reason: {approval4_rejected['comments'][0]['message']}")
    assert approval4_rejected['status'] == ApprovalStatus.REJECTED.value
    
    # Test 5: Request revision
    bid_summary_revision = {
        'grand_total': 3000000,  # ₹30L
        'margin_percent': 16
    }
    
    approval5 = workflow.submit_for_approval('BID-005', bid_summary_revision, 'Sales Rep')
    approval5_revision = workflow.request_revision(
        'BID-005',
        'Director',
        'Please review logistics costs - seem high'
    )
    print(f"\nBid BID-005 (₹30L):")
    print(f"  Status: {approval5_revision['status']}")
    print(f"  Revision Request: {approval5_revision['comments'][0]['message']}")
    assert approval5_revision['status'] == ApprovalStatus.NEEDS_REVISION.value
    
    print("\n✅ Pricing approval workflow passed!")
    return True


def run_all_advanced_tests():
    """Run all advanced feature tests."""
    print("\n" + "🚀"*40)
    print("ADVANCED PRICING FEATURES - COMPREHENSIVE TEST SUITE")
    print("🚀"*40)
    
    tests = [
        ("Win Probability Estimator", test_win_probability),
        ("Cost Comparison Generator", test_cost_comparison),
        ("Sensitivity Analysis", test_sensitivity_analysis),
        ("What-If Scenario Generator", test_what_if_scenarios),
        ("Approval Workflow", test_approval_workflow)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} FAILED: {str(e)}")
            failed += 1
    
    print("\n" + "="*80)
    print("ADVANCED FEATURES TEST SUMMARY")
    print("="*80)
    print(f"Total Tests:  {len(tests)}")
    print(f"✅ Passed:    {passed}")
    print(f"❌ Failed:    {failed}")
    print(f"Pass Rate:    {passed/len(tests)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL ADVANCED FEATURES TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️ {failed} test(s) failed - please review")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    run_all_advanced_tests()
