"""
Comprehensive Pricing Engine - Main orchestration class with all features.
"""
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
import structlog

from pricing.product_pricer import ProductPricer, ProductPrice
from pricing.test_calculator import TestCostCalculator
from pricing.logistics_calculator import LogisticsCalculator
from pricing.margin_calculator import MarginCalculator
from pricing.bid_generator import BidGenerator, CommercialBid

logger = structlog.get_logger()


@dataclass
class PriceOptimizationSuggestion:
    """Price optimization suggestion."""
    category: str
    suggestion: str
    potential_savings: Decimal
    risk_level: str  # low, medium, high
    implementation_effort: str  # easy, moderate, complex


@dataclass
class CostComparison:
    """Cost comparison between scenarios."""
    scenario_name: str
    product_cost: Decimal
    testing_cost: Decimal
    logistics_cost: Decimal
    total_cost: Decimal
    margin_amount: Decimal
    grand_total: Decimal
    notes: List[str]


@dataclass
class TestingFrequencyAnalysis:
    """Testing frequency analysis results."""
    test_type: str
    recommended_frequency: int
    cost_per_test: Decimal
    annual_cost: Decimal
    compliance_level: str  # minimal, standard, comprehensive
    rationale: str


class PricingEngine:
    """
    Main pricing engine that orchestrates all pricing calculations.
    Provides unified interface for product pricing, testing costs, logistics,
    margins, and bid generation with advanced features.
    """
    
    # Exchange rates (base: INR)
    EXCHANGE_RATES = {
        'INR': Decimal('1.0'),
        'USD': Decimal('0.012'),
        'EUR': Decimal('0.011'),
        'GBP': Decimal('0.0095'),
        'AED': Decimal('0.044'),
        'SGD': Decimal('0.016')
    }
    
    def __init__(
        self,
        product_catalog: Optional[Dict[str, ProductPrice]] = None,
        base_currency: str = 'INR'
    ):
        """Initialize pricing engine.
        
        Args:
            product_catalog: Product catalog
            base_currency: Base currency for calculations
        """
        self.product_pricer = ProductPricer(product_catalog or {})
        self.test_calculator = TestCostCalculator()
        self.logistics_calculator = LogisticsCalculator()
        self.margin_calculator = MarginCalculator()
        self.bid_generator = BidGenerator(
            self.product_pricer,
            self.test_calculator,
            self.logistics_calculator,
            self.margin_calculator
        )
        
        self.base_currency = base_currency
        self.logger = logger.bind(component="PricingEngine")
    
    # Feature 1: Product Price Lookup (in ProductPricer)
    def lookup_product_price(
        self,
        product_id: str,
        quantity: int = 1,
        price_type: str = 'base'
    ) -> Decimal:
        """Look up product price with quantity discounts."""
        return self.product_pricer.calculate(
            product_id=product_id,
            quantity=quantity,
            price_type=price_type,
            apply_volume_discount=True
        )
    
    # Feature 2: Quantity-Based Discounts (in ProductPricer)
    def calculate_volume_discount(
        self,
        product_id: str,
        quantity: int
    ) -> Dict[str, Any]:
        """Calculate volume discount for product."""
        product = self.product_pricer.get_product_price(product_id)
        if not product or not product.volume_breaks:
            return {'discount_rate': Decimal('0'), 'discount_amount': Decimal('0')}
        
        # Find applicable discount
        discount_rate = Decimal('0')
        for qty_threshold in sorted(product.volume_breaks.keys(), reverse=True):
            if quantity >= qty_threshold:
                discount_rate = product.volume_breaks[qty_threshold]
                break
        
        base_total = product.base_price * quantity
        discount_amount = base_total * discount_rate / Decimal('100')
        
        return {
            'quantity': quantity,
            'base_price': product.base_price,
            'discount_rate': discount_rate,
            'discount_amount': discount_amount,
            'final_price': base_total - discount_amount
        }
    
    # Feature 3: Testing Frequency Analyzer
    def analyze_testing_frequency(
        self,
        product_category: str,
        production_volume: int,
        compliance_level: str = 'standard'
    ) -> List[TestingFrequencyAnalysis]:
        """Analyze recommended testing frequency based on production volume.
        
        Args:
            product_category: Product category (electrical, electronics, etc.)
            production_volume: Annual production volume
            compliance_level: minimal, standard, or comprehensive
            
        Returns:
            List of testing frequency recommendations
        """
        self.logger.info(
            "Analyzing testing frequency",
            category=product_category,
            volume=production_volume,
            compliance=compliance_level
        )
        
        recommendations = []
        
        # Type tests (one-time or periodic)
        if compliance_level in ['standard', 'comprehensive']:
            freq = 1 if production_volume < 10000 else 2
            cost_per = self.test_calculator.calculate('type_test_electrical', 1)
            recommendations.append(TestingFrequencyAnalysis(
                test_type='Type Test',
                recommended_frequency=freq,
                cost_per_test=cost_per,
                annual_cost=cost_per * freq,
                compliance_level=compliance_level,
                rationale=f'Required {freq}x per year for {compliance_level} compliance'
            ))
        
        # Routine tests (batch-based)
        batch_size = 1000
        batches = max(1, production_volume // batch_size)
        routine_freq = min(batches, 52) if compliance_level == 'comprehensive' else min(batches, 12)
        routine_cost = self.test_calculator.calculate('routine_test_electrical', 1)
        recommendations.append(TestingFrequencyAnalysis(
            test_type='Routine Test',
            recommended_frequency=routine_freq,
            cost_per_test=routine_cost,
            annual_cost=routine_cost * routine_freq,
            compliance_level=compliance_level,
            rationale=f'Test every batch ({batch_size} units) or monthly minimum'
        ))
        
        # Performance tests
        if compliance_level == 'comprehensive':
            perf_freq = 4  # Quarterly
            perf_cost = self.test_calculator.calculate('performance_test', 1)
            recommendations.append(TestingFrequencyAnalysis(
                test_type='Performance Test',
                recommended_frequency=perf_freq,
                cost_per_test=perf_cost,
                annual_cost=perf_cost * perf_freq,
                compliance_level=compliance_level,
                rationale='Quarterly performance validation for comprehensive compliance'
            ))
        
        total_annual_cost = sum(r.annual_cost for r in recommendations)
        self.logger.info(
            "Testing frequency analyzed",
            recommendations=len(recommendations),
            total_annual_cost=float(total_annual_cost)
        )
        
        return recommendations
    
    # Feature 4: Price Optimization Suggestions
    def generate_price_optimization(
        self,
        bid: CommercialBid,
        target_margin: Optional[Decimal] = None
    ) -> List[PriceOptimizationSuggestion]:
        """Generate price optimization suggestions for a bid.
        
        Args:
            bid: Commercial bid to optimize
            target_margin: Target margin percentage
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        # Analyze product cost
        if bid.product_cost > bid.subtotal * Decimal('0.6'):
            # Product cost is >60% of subtotal - look for volume discounts
            potential_savings = bid.product_cost * Decimal('0.05')
            suggestions.append(PriceOptimizationSuggestion(
                category='Product Cost',
                suggestion='Negotiate higher volume discounts with suppliers (current: 60%+ of total cost)',
                potential_savings=potential_savings,
                risk_level='low',
                implementation_effort='easy'
            ))
        
        # Analyze testing cost
        if bid.testing_cost > bid.subtotal * Decimal('0.25'):
            # Testing cost is >25% - optimize testing strategy
            potential_savings = bid.testing_cost * Decimal('0.15')
            suggestions.append(PriceOptimizationSuggestion(
                category='Testing Cost',
                suggestion='Consolidate testing requirements or negotiate bundled testing rates',
                potential_savings=potential_savings,
                risk_level='medium',
                implementation_effort='moderate'
            ))
        
        # Analyze logistics cost
        if bid.logistics_cost > bid.subtotal * Decimal('0.15'):
            # Logistics cost is >15%
            potential_savings = bid.logistics_cost * Decimal('0.10')
            suggestions.append(PriceOptimizationSuggestion(
                category='Logistics Cost',
                suggestion='Explore alternative shipping methods or consolidate shipments',
                potential_savings=potential_savings,
                risk_level='low',
                implementation_effort='easy'
            ))
        
        # Analyze margin
        if target_margin and bid.margin_rate < target_margin:
            margin_gap = target_margin - bid.margin_rate
            required_increase = bid.subtotal * margin_gap / Decimal('100')
            suggestions.append(PriceOptimizationSuggestion(
                category='Margin',
                suggestion=f'Increase selling price by {float(margin_gap):.1f}% to reach target margin',
                potential_savings=required_increase,
                risk_level='high',
                implementation_effort='easy'
            ))
        
        # Overhead optimization
        if bid.overhead_cost > bid.subtotal * Decimal('0.10'):
            potential_savings = bid.overhead_cost * Decimal('0.20')
            suggestions.append(PriceOptimizationSuggestion(
                category='Overhead',
                suggestion='Review overhead allocation - currently >10% of subtotal',
                potential_savings=potential_savings,
                risk_level='low',
                implementation_effort='moderate'
            ))
        
        self.logger.info(
            "Price optimization generated",
            bid_id=bid.bid_id,
            suggestions=len(suggestions),
            total_potential_savings=float(sum(s.potential_savings for s in suggestions))
        )
        
        return suggestions
    
    # Feature 5: Cost Comparison Generator
    def generate_cost_comparison(
        self,
        rfp_reference: str,
        items: List[Dict[str, Any]],
        scenarios: List[Dict[str, Any]]
    ) -> List[CostComparison]:
        """Generate cost comparison across multiple scenarios.
        
        Args:
            rfp_reference: RFP reference
            items: Items list
            scenarios: List of scenario configurations
            
        Returns:
            List of cost comparisons
        """
        comparisons = []
        
        for scenario in scenarios:
            # Generate bid for this scenario
            bid = self.bid_generator.generate_bid(
                rfp_reference=rfp_reference,
                items=items,
                testing_requirements=scenario.get('testing_requirements'),
                logistics_params=scenario.get('logistics_params'),
                margin_rate=scenario.get('margin_rate', Decimal('20')),
                tax_rate=scenario.get('tax_rate', Decimal('18')),
                discount_rate=scenario.get('discount_rate', Decimal('0'))
            )
            
            comparison = CostComparison(
                scenario_name=scenario.get('name', 'Unnamed Scenario'),
                product_cost=bid.product_cost,
                testing_cost=bid.testing_cost,
                logistics_cost=bid.logistics_cost,
                total_cost=bid.subtotal,
                margin_amount=bid.margin_amount,
                grand_total=bid.grand_total,
                notes=scenario.get('notes', [])
            )
            comparisons.append(comparison)
        
        self.logger.info(
            "Cost comparison generated",
            rfp_ref=rfp_reference,
            scenarios=len(scenarios)
        )
        
        return comparisons
    
    # Feature 6: Currency Conversion
    def convert_currency(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str
    ) -> Decimal:
        """Convert amount between currencies.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Converted amount
        """
        if from_currency not in self.EXCHANGE_RATES:
            raise ValueError(f"Unsupported currency: {from_currency}")
        if to_currency not in self.EXCHANGE_RATES:
            raise ValueError(f"Unsupported currency: {to_currency}")
        
        # Convert to INR first, then to target currency
        inr_amount = amount / self.EXCHANGE_RATES[from_currency]
        converted = inr_amount * self.EXCHANGE_RATES[to_currency]
        
        self.logger.debug(
            "Currency converted",
            amount=float(amount),
            from_currency=from_currency,
            to_currency=to_currency,
            converted=float(converted)
        )
        
        return converted.quantize(Decimal('0.01'))
    
    def convert_bid_currency(
        self,
        bid: CommercialBid,
        target_currency: str
    ) -> CommercialBid:
        """Convert entire bid to different currency.
        
        Args:
            bid: Original bid
            target_currency: Target currency code
            
        Returns:
            New bid with converted amounts
        """
        # Create copy and convert all amounts
        from copy import deepcopy
        converted_bid = deepcopy(bid)
        
        converted_bid.product_cost = self.convert_currency(
            bid.product_cost, self.base_currency, target_currency
        )
        converted_bid.testing_cost = self.convert_currency(
            bid.testing_cost, self.base_currency, target_currency
        )
        converted_bid.logistics_cost = self.convert_currency(
            bid.logistics_cost, self.base_currency, target_currency
        )
        converted_bid.packaging_cost = self.convert_currency(
            bid.packaging_cost, self.base_currency, target_currency
        )
        converted_bid.overhead_cost = self.convert_currency(
            bid.overhead_cost, self.base_currency, target_currency
        )
        converted_bid.currency = target_currency
        
        # Recalculate totals
        converted_bid.calculate_totals()
        
        self.logger.info(
            "Bid currency converted",
            bid_id=bid.bid_id,
            from_currency=self.base_currency,
            to_currency=target_currency,
            original_total=float(bid.grand_total),
            converted_total=float(converted_bid.grand_total)
        )
        
        return converted_bid
    
    # Feature 7: Pricing Report Formatter
    def format_pricing_report(
        self,
        bid: CommercialBid,
        include_optimization: bool = True,
        format_type: str = 'detailed'  # detailed, summary, executive
    ) -> str:
        """Format comprehensive pricing report.
        
        Args:
            bid: Commercial bid
            include_optimization: Include optimization suggestions
            format_type: Report format type
            
        Returns:
            Formatted report string
        """
        if format_type == 'summary':
            return self._format_summary_report(bid)
        elif format_type == 'executive':
            return self._format_executive_report(bid)
        else:
            return self._format_detailed_report(bid, include_optimization)
    
    def _format_detailed_report(
        self,
        bid: CommercialBid,
        include_optimization: bool
    ) -> str:
        """Format detailed pricing report."""
        report = self.bid_generator.generate_bid_summary(bid)
        
        if include_optimization:
            suggestions = self.generate_price_optimization(bid)
            if suggestions:
                report += "\n\nPRICE OPTIMIZATION SUGGESTIONS\n"
                report += "=" * 80 + "\n"
                for i, suggestion in enumerate(suggestions, 1):
                    report += f"\n{i}. {suggestion.category}\n"
                    report += f"   {suggestion.suggestion}\n"
                    report += f"   Potential Savings: {bid.currency} {float(suggestion.potential_savings):,.2f}\n"
                    report += f"   Risk: {suggestion.risk_level.upper()} | "
                    report += f"Effort: {suggestion.implementation_effort.upper()}\n"
        
        return report
    
    def _format_summary_report(self, bid: CommercialBid) -> str:
        """Format summary pricing report."""
        return f"""
PRICING SUMMARY
===============

Bid: {bid.bid_id}
RFP: {bid.rfp_reference}
Customer: {bid.customer_name or 'N/A'}

Total Cost: {bid.currency} {float(bid.subtotal):,.2f}
Margin: {float(bid.margin_rate)}% ({bid.currency} {float(bid.margin_amount):,.2f})
Tax: {float(bid.tax_rate)}% ({bid.currency} {float(bid.tax_amount):,.2f})

GRAND TOTAL: {bid.currency} {float(bid.grand_total):,.2f}

Valid until: {bid.validity_days} days
"""
    
    def _format_executive_report(self, bid: CommercialBid) -> str:
        """Format executive pricing report."""
        margin_pct = (bid.margin_amount / bid.grand_total * 100) if bid.grand_total > 0 else 0
        
        return f"""
EXECUTIVE PRICING SUMMARY
=========================

Project: {bid.rfp_reference}
Client: {bid.customer_name or 'N/A'}

FINANCIAL OVERVIEW
------------------
Project Value:        {bid.currency} {float(bid.grand_total):,.2f}
Gross Margin:         {float(margin_pct):.1f}%
Expected Profit:      {bid.currency} {float(bid.margin_amount):,.2f}

KEY COMPONENTS
--------------
Products:             {bid.currency} {float(bid.product_cost):,.2f}
Testing/Certification: {bid.currency} {float(bid.testing_cost):,.2f}
Logistics:            {bid.currency} {float(bid.logistics_cost):,.2f}

TERMS
-----
Payment: {bid.payment_terms}
Delivery: {bid.delivery_terms}
Warranty: {bid.warranty_period}

Quote Valid: {bid.validity_days} days from {bid.created_date[:10]}
"""
    
    # Unified bid generation
    def generate_complete_bid(
        self,
        rfp_reference: str,
        items: List[Dict[str, Any]],
        **kwargs
    ) -> CommercialBid:
        """Generate complete commercial bid with all features.
        
        This is the main method that orchestrates all pricing calculations.
        """
        return self.bid_generator.generate_bid(
            rfp_reference=rfp_reference,
            items=items,
            **kwargs
        )
    
    def generate_bid_from_rfp(
        self,
        rfp_document: Dict[str, Any],
        pricing_params: Optional[Dict[str, Any]] = None
    ) -> CommercialBid:
        """Generate bid directly from parsed RFP document."""
        return self.bid_generator.generate_from_rfp(
            rfp_document=rfp_document,
            pricing_params=pricing_params
        )
