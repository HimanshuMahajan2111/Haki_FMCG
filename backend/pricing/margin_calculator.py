"""
Margin Calculator - Calculates profit margins and markup.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from decimal import Decimal
import structlog

from pricing.base_calculator import PriceCalculator

logger = structlog.get_logger()


@dataclass
class MarginBreakdown:
    """Margin calculation breakdown."""
    total_cost: Decimal
    margin_rate: Decimal
    margin_amount: Decimal
    selling_price: Decimal
    
    # Cost components
    product_cost: Decimal = Decimal('0')
    testing_cost: Decimal = Decimal('0')
    logistics_cost: Decimal = Decimal('0')
    overhead_cost: Decimal = Decimal('0')
    
    # Margin metrics
    gross_profit: Optional[Decimal] = None
    gross_profit_margin: Optional[Decimal] = None
    net_profit: Optional[Decimal] = None
    net_profit_margin: Optional[Decimal] = None
    
    def calculate_metrics(self):
        """Calculate profit metrics."""
        self.gross_profit = self.selling_price - self.total_cost
        self.gross_profit_margin = (self.gross_profit / self.selling_price * Decimal('100')) if self.selling_price > 0 else Decimal('0')
        
        # Net profit (after overhead)
        self.net_profit = self.gross_profit - self.overhead_cost
        self.net_profit_margin = (self.net_profit / self.selling_price * Decimal('100')) if self.selling_price > 0 else Decimal('0')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        self.calculate_metrics()
        return {
            'total_cost': float(self.total_cost),
            'margin_rate': float(self.margin_rate),
            'margin_amount': float(self.margin_amount),
            'selling_price': float(self.selling_price),
            'product_cost': float(self.product_cost),
            'testing_cost': float(self.testing_cost),
            'logistics_cost': float(self.logistics_cost),
            'overhead_cost': float(self.overhead_cost),
            'gross_profit': float(self.gross_profit) if self.gross_profit else 0,
            'gross_profit_margin': float(self.gross_profit_margin) if self.gross_profit_margin else 0,
            'net_profit': float(self.net_profit) if self.net_profit else 0,
            'net_profit_margin': float(self.net_profit_margin) if self.net_profit_margin else 0
        }


class MarginCalculator(PriceCalculator):
    """Calculate profit margins and final selling prices."""
    
    def __init__(self):
        """Initialize margin calculator."""
        super().__init__()
        self.logger = logger.bind(component="MarginCalculator")
        
        # Default margin rates by product category (in %)
        self.category_margins = {
            'electrical': Decimal('20'),
            'mechanical': Decimal('18'),
            'electronics': Decimal('25'),
            'cables': Decimal('15'),
            'lighting': Decimal('22'),
            'hvac': Decimal('20'),
            'plumbing': Decimal('18'),
            'safety': Decimal('25'),
            'default': Decimal('20')
        }
        
        # Overhead rates (% of cost)
        self.overhead_rates = {
            'small_project': Decimal('5'),
            'medium_project': Decimal('8'),
            'large_project': Decimal('10'),
            'default': Decimal('8')
        }
    
    def calculate(
        self,
        total_cost: Decimal,
        margin_rate: Optional[Decimal] = None,
        category: str = 'default'
    ) -> Decimal:
        """Calculate selling price with margin.
        
        Args:
            total_cost: Total cost
            margin_rate: Margin rate in % (if None, use category default)
            category: Product category
            
        Returns:
            Selling price with margin
        """
        if margin_rate is None:
            margin_rate = self.category_margins.get(category, Decimal('20'))
        
        margin_amount = total_cost * margin_rate / Decimal('100')
        selling_price = total_cost + margin_amount
        
        self.logger.info(
            "Margin calculated",
            cost=float(total_cost),
            margin_rate=float(margin_rate),
            selling_price=float(selling_price)
        )
        
        return self.round_price(selling_price)
    
    def calculate_detailed(
        self,
        product_cost: Decimal,
        testing_cost: Decimal = Decimal('0'),
        logistics_cost: Decimal = Decimal('0'),
        margin_rate: Optional[Decimal] = None,
        category: str = 'default',
        project_size: str = 'medium_project'
    ) -> MarginBreakdown:
        """Calculate margin with detailed breakdown.
        
        Args:
            product_cost: Cost of products
            testing_cost: Testing costs
            logistics_cost: Logistics costs
            margin_rate: Desired margin rate
            category: Product category
            project_size: Project size for overhead calculation
            
        Returns:
            MarginBreakdown object
        """
        # Calculate total cost
        total_cost = product_cost + testing_cost + logistics_cost
        
        # Calculate overhead
        overhead_rate = self.overhead_rates.get(project_size, Decimal('8'))
        overhead_cost = total_cost * overhead_rate / Decimal('100')
        
        # Add overhead to total cost
        total_cost_with_overhead = total_cost + overhead_cost
        
        # Get margin rate
        if margin_rate is None:
            margin_rate = self.category_margins.get(category, Decimal('20'))
        
        # Calculate margin and selling price
        margin_amount = total_cost_with_overhead * margin_rate / Decimal('100')
        selling_price = total_cost_with_overhead + margin_amount
        
        breakdown = MarginBreakdown(
            total_cost=total_cost_with_overhead,
            margin_rate=margin_rate,
            margin_amount=margin_amount,
            selling_price=selling_price,
            product_cost=product_cost,
            testing_cost=testing_cost,
            logistics_cost=logistics_cost,
            overhead_cost=overhead_cost
        )
        
        breakdown.calculate_metrics()
        
        return breakdown
    
    def calculate_reverse_margin(
        self,
        selling_price: Decimal,
        total_cost: Decimal
    ) -> Dict[str, Any]:
        """Calculate margin from selling price and cost.
        
        Args:
            selling_price: Desired selling price
            total_cost: Total cost
            
        Returns:
            Dictionary with margin metrics
        """
        margin_amount = selling_price - total_cost
        margin_rate = (margin_amount / total_cost * Decimal('100')) if total_cost > 0 else Decimal('0')
        profit_margin = (margin_amount / selling_price * Decimal('100')) if selling_price > 0 else Decimal('0')
        
        return {
            'selling_price': float(selling_price),
            'total_cost': float(total_cost),
            'margin_amount': float(margin_amount),
            'margin_rate': float(margin_rate),
            'profit_margin': float(profit_margin)
        }
    
    def calculate_target_price(
        self,
        total_cost: Decimal,
        target_profit_margin: Decimal
    ) -> Decimal:
        """Calculate selling price to achieve target profit margin.
        
        Args:
            total_cost: Total cost
            target_profit_margin: Target profit margin in %
            
        Returns:
            Required selling price
        """
        # Selling price = Cost / (1 - Profit Margin%)
        selling_price = total_cost / (Decimal('1') - target_profit_margin / Decimal('100'))
        
        return self.round_price(selling_price)
    
    def compare_margin_scenarios(
        self,
        total_cost: Decimal,
        margin_scenarios: list
    ) -> Dict[str, Any]:
        """Compare different margin scenarios.
        
        Args:
            total_cost: Total cost
            margin_scenarios: List of margin rates to compare
            
        Returns:
            Dictionary with scenario comparisons
        """
        scenarios = []
        
        for margin_rate in margin_scenarios:
            selling_price = self.calculate(total_cost, margin_rate)
            profit = selling_price - total_cost
            profit_margin = (profit / selling_price * Decimal('100'))
            
            scenarios.append({
                'margin_rate': float(margin_rate),
                'selling_price': float(selling_price),
                'profit_amount': float(profit),
                'profit_margin': float(profit_margin)
            })
        
        return {
            'total_cost': float(total_cost),
            'scenarios': scenarios
        }
    
    def calculate_competitive_pricing(
        self,
        total_cost: Decimal,
        competitor_prices: list,
        min_margin: Decimal = Decimal('10')
    ) -> Dict[str, Any]:
        """Calculate competitive pricing strategy.
        
        Args:
            total_cost: Our total cost
            competitor_prices: List of competitor prices
            min_margin: Minimum acceptable margin %
            
        Returns:
            Pricing recommendations
        """
        if not competitor_prices:
            return {
                'recommendation': 'No competitor data',
                'suggested_price': float(self.calculate(total_cost))
            }
        
        avg_competitor_price = Decimal(str(sum(competitor_prices) / len(competitor_prices)))
        min_competitor_price = Decimal(str(min(competitor_prices)))
        max_competitor_price = Decimal(str(max(competitor_prices)))
        
        # Calculate minimum acceptable price
        min_acceptable_price = total_cost * (Decimal('1') + min_margin / Decimal('100'))
        
        # Pricing strategies
        strategies = {}
        
        # Competitive strategy (match average)
        if avg_competitor_price >= min_acceptable_price:
            strategies['competitive'] = {
                'price': float(avg_competitor_price),
                'margin': float((avg_competitor_price - total_cost) / total_cost * Decimal('100')),
                'viable': True
            }
        else:
            strategies['competitive'] = {
                'price': float(avg_competitor_price),
                'margin': float((avg_competitor_price - total_cost) / total_cost * Decimal('100')),
                'viable': False,
                'reason': 'Below minimum margin'
            }
        
        # Aggressive strategy (undercut by 5%)
        aggressive_price = min_competitor_price * Decimal('0.95')
        strategies['aggressive'] = {
            'price': float(aggressive_price),
            'margin': float((aggressive_price - total_cost) / total_cost * Decimal('100')),
            'viable': aggressive_price >= min_acceptable_price
        }
        
        # Premium strategy (above average by 10%)
        premium_price = avg_competitor_price * Decimal('1.10')
        strategies['premium'] = {
            'price': float(premium_price),
            'margin': float((premium_price - total_cost) / total_cost * Decimal('100')),
            'viable': True
        }
        
        return {
            'total_cost': float(total_cost),
            'min_acceptable_price': float(min_acceptable_price),
            'competitor_analysis': {
                'average': float(avg_competitor_price),
                'min': float(min_competitor_price),
                'max': float(max_competitor_price)
            },
            'strategies': strategies
        }
