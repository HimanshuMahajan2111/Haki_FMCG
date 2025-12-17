"""
Advanced Pricing Agent Features
- Win probability estimator
- Cost comparison generator
- Sensitivity analysis
- What-if scenario generator
- Competitive analysis
- Pricing approval workflow
- API interface
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import pandas as pd
from enum import Enum


class ApprovalStatus(Enum):
    """Approval status for bids."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


@dataclass
class WinProbability:
    """Win probability estimate."""
    probability: float  # 0.0 to 1.0
    confidence: str  # 'Low', 'Medium', 'High'
    factors: Dict[str, Any]
    recommendations: List[str]


@dataclass
class SensitivityAnalysis:
    """Sensitivity analysis results."""
    parameter: str
    base_value: float
    variations: List[Dict[str, float]]
    impact_on_total: List[float]
    impact_on_margin: List[float]


@dataclass
class WhatIfScenario:
    """What-if scenario result."""
    scenario_name: str
    changes: Dict[str, Any]
    original_total: float
    new_total: float
    difference: float
    difference_percent: float


class WinProbabilityEstimator:
    """Estimates win probability for bids."""
    
    def estimate_win_probability(
        self,
        our_bid: Dict[str, Any],
        market_data: Dict[str, Any],
        customer_info: Dict[str, Any]
    ) -> WinProbability:
        """Estimate probability of winning the bid.
        
        Args:
            our_bid: Our bid details
            market_data: Market pricing data
            customer_info: Customer information
            
        Returns:
            WinProbability object
        """
        factors = {}
        probability = 0.5  # Base probability
        
        # Factor 1: Price competitiveness (40% weight)
        if 'market_average' in market_data:
            our_price = our_bid['bid_summary']['grand_total']
            market_avg = market_data['market_average']
            
            if our_price <= market_avg * 0.90:  # 10% below market
                price_score = 0.4
                factors['price_competitiveness'] = 'Excellent (10% below market)'
            elif our_price <= market_avg * 0.95:  # 5% below market
                price_score = 0.3
                factors['price_competitiveness'] = 'Good (5% below market)'
            elif our_price <= market_avg:
                price_score = 0.2
                factors['price_competitiveness'] = 'Fair (at market)'
            elif our_price <= market_avg * 1.05:
                price_score = 0.1
                factors['price_competitiveness'] = 'Below Average (5% above market)'
            else:
                price_score = 0.0
                factors['price_competitiveness'] = 'Poor (>5% above market)'
            
            probability += price_score
        
        # Factor 2: Customer relationship (20% weight)
        customer_type = customer_info.get('type', '').lower()
        if 'government' in customer_type:
            # Government: Price is king
            relationship_score = 0.1
            factors['relationship'] = 'Government tender (price-focused)'
        elif customer_info.get('existing_customer', False):
            relationship_score = 0.2
            factors['relationship'] = 'Existing customer (strong relationship)'
        else:
            relationship_score = 0.0
            factors['relationship'] = 'New customer'
        
        probability += relationship_score
        
        # Factor 3: Delivery terms (15% weight)
        delivery_days = min(
            p.get('delivery_days', 30) 
            for p in our_bid.get('product_pricings', [])
        )
        if delivery_days <= 15:
            delivery_score = 0.15
            factors['delivery'] = f'Excellent ({delivery_days} days)'
        elif delivery_days <= 30:
            delivery_score = 0.1
            factors['delivery'] = f'Good ({delivery_days} days)'
        else:
            delivery_score = 0.05
            factors['delivery'] = f'Standard ({delivery_days} days)'
        
        probability += delivery_score
        
        # Factor 4: Payment terms (15% weight)
        payment_terms = our_bid['bid_summary']['payment_terms']
        if 'LC' in payment_terms or 'Letter of Credit' in payment_terms:
            payment_score = 0.15
            factors['payment_terms'] = 'Excellent (LC accepted)'
        elif 'Advance' in payment_terms:
            payment_score = 0.1
            factors['payment_terms'] = 'Good (Advance payment)'
        else:
            payment_score = 0.05
            factors['payment_terms'] = 'Standard (Net terms)'
        
        probability += payment_score
        
        # Factor 5: Completeness (10% weight)
        testing_included = our_bid['bid_summary']['testing_costs_total'] > 0
        if testing_included:
            completeness_score = 0.1
            factors['completeness'] = 'Complete (testing included)'
        else:
            completeness_score = 0.05
            factors['completeness'] = 'Basic (no testing costs)'
        
        probability += completeness_score
        
        # Determine confidence level
        if probability >= 0.75:
            confidence = 'High'
        elif probability >= 0.50:
            confidence = 'Medium'
        else:
            confidence = 'Low'
        
        # Generate recommendations
        recommendations = []
        if probability < 0.6:
            if factors.get('price_competitiveness', '').startswith('Poor'):
                recommendations.append('Consider reducing margin to improve price competitiveness')
            if not testing_included:
                recommendations.append('Include testing costs to make bid more complete')
            if delivery_days > 30:
                recommendations.append('Explore options to reduce delivery time')
        
        return WinProbability(
            probability=round(probability, 2),
            confidence=confidence,
            factors=factors,
            recommendations=recommendations
        )


class CostComparisonGenerator:
    """Generates cost comparison tables."""
    
    def generate_comparison(
        self,
        our_bid: Dict[str, Any],
        competitor_bids: List[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """Generate cost comparison table.
        
        Args:
            our_bid: Our bid details
            competitor_bids: List of competitor bid details (optional)
            
        Returns:
            pandas DataFrame with comparison
        """
        comparison_data = []
        
        # Our bid
        our_summary = our_bid['bid_summary']
        comparison_data.append({
            'Vendor': 'Our Bid',
            'Subtotal (₹)': f"₹{our_summary['products_subtotal']:,.2f}",
            'Discounts (₹)': f"-₹{our_summary['total_discounts']:,.2f}",
            'Testing (₹)': f"₹{our_summary['testing_costs_total']:,.2f}",
            'Logistics (₹)': f"₹{our_summary['logistics_total']:,.2f}",
            'Installation (₹)': f"₹{our_summary['installation_total']:,.2f}",
            'GST (₹)': f"₹{our_summary['gst_total']:,.2f}",
            'Grand Total (₹)': f"₹{our_summary['grand_total']:,.2f}",
            'Payment Terms': our_summary['payment_terms'],
            'Validity (days)': our_summary['validity_days']
        })
        
        # Competitor bids (if provided)
        if competitor_bids:
            for idx, comp in enumerate(competitor_bids, 1):
                comparison_data.append({
                    'Vendor': f"Competitor {idx}",
                    'Subtotal (₹)': f"₹{comp.get('subtotal', 0):,.2f}",
                    'Discounts (₹)': f"-₹{comp.get('discounts', 0):,.2f}",
                    'Testing (₹)': f"₹{comp.get('testing', 0):,.2f}",
                    'Logistics (₹)': f"₹{comp.get('logistics', 0):,.2f}",
                    'Installation (₹)': f"₹{comp.get('installation', 0):,.2f}",
                    'GST (₹)': f"₹{comp.get('gst', 0):,.2f}",
                    'Grand Total (₹)': f"₹{comp.get('grand_total', 0):,.2f}",
                    'Payment Terms': comp.get('payment_terms', 'N/A'),
                    'Validity (days)': comp.get('validity_days', 'N/A')
                })
        
        return pd.DataFrame(comparison_data)


class SensitivityAnalyzer:
    """Performs sensitivity analysis on pricing."""
    
    def analyze_parameter(
        self,
        base_bid: Dict[str, Any],
        parameter: str,
        variation_range: List[float] = [-20, -10, 0, 10, 20]
    ) -> SensitivityAnalysis:
        """Analyze sensitivity to parameter changes.
        
        Args:
            base_bid: Base bid details
            parameter: Parameter to vary ('margin', 'discount', 'logistics', etc.)
            variation_range: List of percentage variations
            
        Returns:
            SensitivityAnalysis object
        """
        base_value = base_bid['bid_summary']['grand_total']
        base_margin = base_bid['bid_summary']['margin_percent']
        
        variations = []
        impact_on_total = []
        impact_on_margin = []
        
        for var_pct in variation_range:
            # Simulate change
            multiplier = 1 + (var_pct / 100)
            
            if parameter == 'margin':
                new_margin = base_margin * multiplier
                new_total = base_value * (1 + ((new_margin - base_margin) / 100))
            elif parameter == 'discount':
                discount_change = base_bid['bid_summary']['total_discounts'] * (multiplier - 1)
                new_total = base_value - discount_change
                new_margin = base_margin
            elif parameter == 'logistics':
                logistics_change = base_bid['bid_summary']['logistics_total'] * (multiplier - 1)
                new_total = base_value + logistics_change
                new_margin = base_margin
            else:
                new_total = base_value
                new_margin = base_margin
            
            variations.append({
                'variation_pct': var_pct,
                'multiplier': multiplier,
                'new_value': new_total
            })
            
            impact_on_total.append(new_total - base_value)
            impact_on_margin.append(new_margin - base_margin)
        
        return SensitivityAnalysis(
            parameter=parameter,
            base_value=base_value,
            variations=variations,
            impact_on_total=impact_on_total,
            impact_on_margin=impact_on_margin
        )


class WhatIfScenarioGenerator:
    """Generates what-if scenarios."""
    
    def generate_scenario(
        self,
        base_bid: Dict[str, Any],
        scenario_name: str,
        changes: Dict[str, Any]
    ) -> WhatIfScenario:
        """Generate a what-if scenario.
        
        Args:
            base_bid: Base bid details
            scenario_name: Name of scenario
            changes: Dictionary of changes to apply
            
        Returns:
            WhatIfScenario object
        """
        original_total = base_bid['bid_summary']['grand_total']
        new_total = original_total
        
        # Apply changes
        if 'margin_adjustment' in changes:
            margin_change = changes['margin_adjustment']
            new_total *= (1 + margin_change / 100)
        
        if 'additional_discount' in changes:
            discount = changes['additional_discount']
            new_total *= (1 - discount / 100)
        
        if 'logistics_factor' in changes:
            logistics_base = base_bid['bid_summary']['logistics_total']
            logistics_change = logistics_base * (changes['logistics_factor'] - 1)
            new_total += logistics_change
        
        if 'remove_installation' in changes and changes['remove_installation']:
            new_total -= base_bid['bid_summary']['installation_total']
        
        difference = new_total - original_total
        difference_percent = (difference / original_total * 100) if original_total > 0 else 0
        
        return WhatIfScenario(
            scenario_name=scenario_name,
            changes=changes,
            original_total=original_total,
            new_total=new_total,
            difference=difference,
            difference_percent=difference_percent
        )


class PricingApprovalWorkflow:
    """Manages pricing approval workflow."""
    
    def __init__(self):
        self.approvals = {}
    
    def submit_for_approval(
        self,
        bid_id: str,
        bid_summary: Dict[str, Any],
        submitter: str
    ) -> Dict[str, Any]:
        """Submit bid for approval.
        
        Args:
            bid_id: Bid ID
            bid_summary: Bid summary
            submitter: Person submitting
            
        Returns:
            Approval record
        """
        # Determine required approvals based on value
        grand_total = bid_summary['grand_total']
        margin_pct = bid_summary['margin_percent']
        
        required_approvals = []
        if grand_total >= 10000000:  # ≥ ₹1 Cr
            required_approvals = ['Manager', 'Director', 'CFO']
        elif grand_total >= 1000000:  # ≥ ₹10 L
            required_approvals = ['Manager', 'Director']
        elif grand_total >= 100000:  # ≥ ₹1 L
            required_approvals = ['Manager']
        else:
            required_approvals = []  # Auto-approved
        
        # Lower margins need additional approval
        if margin_pct < 15:
            if 'CFO' not in required_approvals:
                required_approvals.append('CFO')
        
        approval_record = {
            'bid_id': bid_id,
            'status': ApprovalStatus.PENDING.value if required_approvals else ApprovalStatus.APPROVED.value,
            'submitter': submitter,
            'required_approvals': required_approvals,
            'approvals_received': [],
            'comments': [],
            'submitted_at': pd.Timestamp.now().isoformat()
        }
        
        self.approvals[bid_id] = approval_record
        return approval_record
    
    def approve(
        self,
        bid_id: str,
        approver: str,
        comments: str = ""
    ) -> Dict[str, Any]:
        """Approve a bid.
        
        Args:
            bid_id: Bid ID
            approver: Person approving
            comments: Optional comments
            
        Returns:
            Updated approval record
        """
        if bid_id not in self.approvals:
            raise ValueError(f"Bid {bid_id} not found in approval workflow")
        
        record = self.approvals[bid_id]
        
        if approver in record['required_approvals']:
            record['approvals_received'].append({
                'approver': approver,
                'approved_at': pd.Timestamp.now().isoformat(),
                'comments': comments
            })
            
            # Check if all approvals received
            approved_by = [a['approver'] for a in record['approvals_received']]
            if all(req in approved_by for req in record['required_approvals']):
                record['status'] = ApprovalStatus.APPROVED.value
        
        return record
    
    def reject(
        self,
        bid_id: str,
        rejector: str,
        reason: str
    ) -> Dict[str, Any]:
        """Reject a bid.
        
        Args:
            bid_id: Bid ID
            rejector: Person rejecting
            reason: Rejection reason
            
        Returns:
            Updated approval record
        """
        if bid_id not in self.approvals:
            raise ValueError(f"Bid {bid_id} not found in approval workflow")
        
        record = self.approvals[bid_id]
        record['status'] = ApprovalStatus.REJECTED.value
        record['comments'].append({
            'from': rejector,
            'type': 'rejection',
            'message': reason,
            'at': pd.Timestamp.now().isoformat()
        })
        
        return record
    
    def request_revision(
        self,
        bid_id: str,
        requester: str,
        requested_changes: str
    ) -> Dict[str, Any]:
        """Request revisions to bid.
        
        Args:
            bid_id: Bid ID
            requester: Person requesting changes
            requested_changes: Description of changes
            
        Returns:
            Updated approval record
        """
        if bid_id not in self.approvals:
            raise ValueError(f"Bid {bid_id} not found in approval workflow")
        
        record = self.approvals[bid_id]
        record['status'] = ApprovalStatus.NEEDS_REVISION.value
        record['comments'].append({
            'from': requester,
            'type': 'revision_request',
            'message': requested_changes,
            'at': pd.Timestamp.now().isoformat()
        })
        
        return record
    
    def get_approval_status(self, bid_id: str) -> Dict[str, Any]:
        """Get approval status for a bid."""
        return self.approvals.get(bid_id, {'status': 'not_found'})


class PricingAPI:
    """API interface for pricing agent."""
    
    def __init__(self, pricing_agent):
        """Initialize API with pricing agent."""
        self.agent = pricing_agent
        self.win_estimator = WinProbabilityEstimator()
        self.cost_comparator = CostComparisonGenerator()
        self.sensitivity_analyzer = SensitivityAnalyzer()
        self.scenario_generator = WhatIfScenarioGenerator()
        self.approval_workflow = PricingApprovalWorkflow()
    
    def create_bid(
        self,
        technical_recommendations: Dict[str, Any],
        customer_info: Dict[str, Any],
        rfp_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """API endpoint: Create a new bid."""
        return self.agent.process_pricing_request(
            technical_recommendations,
            customer_info,
            rfp_details
        )
    
    def estimate_win_probability(
        self,
        bid_id: str,
        bid_data: Dict[str, Any],
        market_data: Dict[str, Any],
        customer_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """API endpoint: Estimate win probability."""
        win_prob = self.win_estimator.estimate_win_probability(
            bid_data,
            market_data,
            customer_info
        )
        return {
            'bid_id': bid_id,
            'win_probability': win_prob.probability,
            'confidence': win_prob.confidence,
            'factors': win_prob.factors,
            'recommendations': win_prob.recommendations
        }
    
    def generate_comparison(
        self,
        bid_data: Dict[str, Any],
        competitor_bids: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """API endpoint: Generate cost comparison."""
        comparison_df = self.cost_comparator.generate_comparison(
            bid_data,
            competitor_bids
        )
        return {
            'comparison_table': comparison_df.to_dict('records')
        }
    
    def run_sensitivity_analysis(
        self,
        bid_data: Dict[str, Any],
        parameter: str
    ) -> Dict[str, Any]:
        """API endpoint: Run sensitivity analysis."""
        analysis = self.sensitivity_analyzer.analyze_parameter(
            bid_data,
            parameter
        )
        return {
            'parameter': analysis.parameter,
            'base_value': analysis.base_value,
            'variations': analysis.variations,
            'impact_on_total': analysis.impact_on_total,
            'impact_on_margin': analysis.impact_on_margin
        }
    
    def generate_what_if_scenario(
        self,
        bid_data: Dict[str, Any],
        scenario_name: str,
        changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """API endpoint: Generate what-if scenario."""
        scenario = self.scenario_generator.generate_scenario(
            bid_data,
            scenario_name,
            changes
        )
        return {
            'scenario_name': scenario.scenario_name,
            'changes': scenario.changes,
            'original_total': scenario.original_total,
            'new_total': scenario.new_total,
            'difference': scenario.difference,
            'difference_percent': scenario.difference_percent
        }
    
    def submit_for_approval(
        self,
        bid_id: str,
        bid_summary: Dict[str, Any],
        submitter: str
    ) -> Dict[str, Any]:
        """API endpoint: Submit bid for approval."""
        return self.approval_workflow.submit_for_approval(
            bid_id,
            bid_summary,
            submitter
        )
    
    def approve_bid(
        self,
        bid_id: str,
        approver: str,
        comments: str = ""
    ) -> Dict[str, Any]:
        """API endpoint: Approve bid."""
        return self.approval_workflow.approve(bid_id, approver, comments)
    
    def reject_bid(
        self,
        bid_id: str,
        rejector: str,
        reason: str
    ) -> Dict[str, Any]:
        """API endpoint: Reject bid."""
        return self.approval_workflow.reject(bid_id, rejector, reason)
    
    def get_statistics(self) -> Dict[str, Any]:
        """API endpoint: Get agent statistics."""
        return self.agent.get_statistics()
