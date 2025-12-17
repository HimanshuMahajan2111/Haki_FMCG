"""
Base Calculator - Abstract base class for all pricing calculators.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from decimal import Decimal
import structlog

logger = structlog.get_logger()


@dataclass
class PriceBreakdown:
    """Detailed price breakdown."""
    base_price: Decimal
    quantity: int
    subtotal: Decimal
    
    # Additional costs
    testing_cost: Decimal = Decimal('0')
    logistics_cost: Decimal = Decimal('0')
    packaging_cost: Decimal = Decimal('0')
    installation_cost: Decimal = Decimal('0')
    warranty_cost: Decimal = Decimal('0')
    
    # Taxes and duties
    tax_rate: Decimal = Decimal('0')
    tax_amount: Decimal = Decimal('0')
    
    # Discounts
    discount_rate: Decimal = Decimal('0')
    discount_amount: Decimal = Decimal('0')
    
    # Margin
    margin_rate: Decimal = Decimal('0')
    margin_amount: Decimal = Decimal('0')
    
    # Final totals
    total_cost: Decimal = Decimal('0')
    final_price: Decimal = Decimal('0')
    
    # Metadata
    currency: str = "INR"
    notes: List[str] = field(default_factory=list)
    breakdown_details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'base_price': float(self.base_price),
            'quantity': self.quantity,
            'subtotal': float(self.subtotal),
            'testing_cost': float(self.testing_cost),
            'logistics_cost': float(self.logistics_cost),
            'packaging_cost': float(self.packaging_cost),
            'installation_cost': float(self.installation_cost),
            'warranty_cost': float(self.warranty_cost),
            'tax_rate': float(self.tax_rate),
            'tax_amount': float(self.tax_amount),
            'discount_rate': float(self.discount_rate),
            'discount_amount': float(self.discount_amount),
            'margin_rate': float(self.margin_rate),
            'margin_amount': float(self.margin_amount),
            'total_cost': float(self.total_cost),
            'final_price': float(self.final_price),
            'currency': self.currency,
            'notes': self.notes,
            'breakdown_details': self.breakdown_details
        }
    
    def calculate_total_cost(self) -> Decimal:
        """Calculate total cost before margin."""
        self.total_cost = (
            self.subtotal +
            self.testing_cost +
            self.logistics_cost +
            self.packaging_cost +
            self.installation_cost +
            self.warranty_cost
        )
        return self.total_cost
    
    def calculate_final_price(self) -> Decimal:
        """Calculate final price with margin, tax, and discount."""
        # Apply margin
        price_with_margin = self.total_cost + self.margin_amount
        
        # Apply discount
        price_after_discount = price_with_margin - self.discount_amount
        
        # Apply tax
        self.final_price = price_after_discount + self.tax_amount
        
        return self.final_price


class PriceCalculator(ABC):
    """Abstract base class for price calculators."""
    
    def __init__(self):
        """Initialize price calculator."""
        self.logger = logger.bind(component=self.__class__.__name__)
    
    @abstractmethod
    def calculate(self, **kwargs) -> Decimal:
        """Calculate price.
        
        Returns:
            Calculated price as Decimal
        """
        pass
    
    def validate_inputs(self, **kwargs) -> bool:
        """Validate calculation inputs.
        
        Returns:
            True if inputs are valid
        """
        return True
    
    def to_decimal(self, value: Any) -> Decimal:
        """Convert value to Decimal safely.
        
        Args:
            value: Value to convert
            
        Returns:
            Decimal value
        """
        if isinstance(value, Decimal):
            return value
        
        try:
            return Decimal(str(value))
        except Exception as e:
            self.logger.warning("Failed to convert to Decimal", value=value, error=str(e))
            return Decimal('0')
    
    def round_price(self, price: Decimal, decimals: int = 2) -> Decimal:
        """Round price to specified decimals.
        
        Args:
            price: Price to round
            decimals: Number of decimal places
            
        Returns:
            Rounded price
        """
        return price.quantize(Decimal(10) ** -decimals)
