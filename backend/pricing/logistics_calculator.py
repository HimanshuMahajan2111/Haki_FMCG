"""
Logistics Cost Calculator - Calculates shipping, packaging, and delivery costs.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from decimal import Decimal
import structlog

from pricing.base_calculator import PriceCalculator

logger = structlog.get_logger()


@dataclass
class LogisticsCost:
    """Logistics cost breakdown."""
    shipping_cost: Decimal
    packaging_cost: Decimal
    handling_cost: Decimal
    insurance_cost: Decimal
    
    # Delivery details
    delivery_method: str = "standard"
    destination: Optional[str] = None
    estimated_days: Optional[int] = None
    
    def total_cost(self) -> Decimal:
        """Calculate total logistics cost."""
        return (
            self.shipping_cost +
            self.packaging_cost +
            self.handling_cost +
            self.insurance_cost
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'shipping_cost': float(self.shipping_cost),
            'packaging_cost': float(self.packaging_cost),
            'handling_cost': float(self.handling_cost),
            'insurance_cost': float(self.insurance_cost),
            'total_cost': float(self.total_cost()),
            'delivery_method': self.delivery_method,
            'destination': self.destination,
            'estimated_days': self.estimated_days
        }


class LogisticsCalculator(PriceCalculator):
    """Calculate logistics, shipping, and delivery costs."""
    
    def __init__(self):
        """Initialize logistics calculator."""
        super().__init__()
        self.logger = logger.bind(component="LogisticsCalculator")
        
        # Base rates per kg (in INR)
        self.shipping_rates = {
            'standard': Decimal('50'),
            'express': Decimal('100'),
            'overnight': Decimal('150'),
            'international': Decimal('500')
        }
        
        # Distance-based multipliers
        self.distance_multipliers = {
            'local': Decimal('1.0'),        # < 50 km
            'regional': Decimal('1.5'),     # 50-300 km
            'national': Decimal('2.0'),     # 300-1500 km
            'distant': Decimal('2.5'),      # > 1500 km
            'international': Decimal('5.0')
        }
        
        # Packaging costs per item based on size
        self.packaging_costs = {
            'small': Decimal('50'),
            'medium': Decimal('150'),
            'large': Decimal('300'),
            'xlarge': Decimal('500'),
            'custom': Decimal('1000')
        }
        
        # Insurance rates (% of product value)
        self.insurance_rates = {
            'basic': Decimal('0.5'),
            'standard': Decimal('1.0'),
            'comprehensive': Decimal('2.0')
        }
    
    def calculate(
        self,
        weight_kg: float,
        delivery_method: str = 'standard',
        distance_category: str = 'regional',
        product_value: Optional[Decimal] = None,
        insurance_type: str = 'standard',
        packaging_size: str = 'medium',
        quantity: int = 1
    ) -> Decimal:
        """Calculate logistics cost.
        
        Args:
            weight_kg: Total weight in kg
            delivery_method: Delivery method ('standard', 'express', etc.)
            distance_category: Distance category
            product_value: Product value for insurance calculation
            insurance_type: Insurance type
            packaging_size: Packaging size category
            quantity: Number of items
            
        Returns:
            Total logistics cost
        """
        # Calculate shipping cost
        base_rate = self.shipping_rates.get(delivery_method, Decimal('50'))
        distance_mult = self.distance_multipliers.get(distance_category, Decimal('1.5'))
        shipping_cost = base_rate * Decimal(str(weight_kg)) * distance_mult
        
        # Calculate packaging cost
        packaging_cost = self.packaging_costs.get(packaging_size, Decimal('150'))
        packaging_cost *= Decimal(quantity)
        
        # Calculate handling cost (5% of shipping)
        handling_cost = shipping_cost * Decimal('0.05')
        
        # Calculate insurance cost
        if product_value:
            insurance_rate = self.insurance_rates.get(insurance_type, Decimal('1.0'))
            insurance_cost = product_value * insurance_rate / Decimal('100')
        else:
            insurance_cost = Decimal('0')
        
        total = shipping_cost + packaging_cost + handling_cost + insurance_cost
        
        self.logger.info(
            "Logistics cost calculated",
            weight_kg=weight_kg,
            method=delivery_method,
            distance=distance_category,
            total=float(total)
        )
        
        return self.round_price(total)
    
    def calculate_detailed(
        self,
        weight_kg: float,
        delivery_method: str = 'standard',
        distance_category: str = 'regional',
        product_value: Optional[Decimal] = None,
        insurance_type: str = 'standard',
        packaging_size: str = 'medium',
        quantity: int = 1,
        destination: Optional[str] = None
    ) -> LogisticsCost:
        """Calculate logistics cost with detailed breakdown.
        
        Returns:
            LogisticsCost object with breakdown
        """
        # Calculate individual components
        base_rate = self.shipping_rates.get(delivery_method, Decimal('50'))
        distance_mult = self.distance_multipliers.get(distance_category, Decimal('1.5'))
        shipping_cost = base_rate * Decimal(str(weight_kg)) * distance_mult
        
        packaging_cost = self.packaging_costs.get(packaging_size, Decimal('150'))
        packaging_cost *= Decimal(quantity)
        
        handling_cost = shipping_cost * Decimal('0.05')
        
        if product_value:
            insurance_rate = self.insurance_rates.get(insurance_type, Decimal('1.0'))
            insurance_cost = product_value * insurance_rate / Decimal('100')
        else:
            insurance_cost = Decimal('0')
        
        # Estimate delivery days
        delivery_days = self._estimate_delivery_days(delivery_method, distance_category)
        
        return LogisticsCost(
            shipping_cost=self.round_price(shipping_cost),
            packaging_cost=self.round_price(packaging_cost),
            handling_cost=self.round_price(handling_cost),
            insurance_cost=self.round_price(insurance_cost),
            delivery_method=delivery_method,
            destination=destination,
            estimated_days=delivery_days
        )
    
    def calculate_multi_location(
        self,
        locations: list,
        weight_per_location: Dict[str, float],
        delivery_method: str = 'standard'
    ) -> Dict[str, Any]:
        """Calculate logistics costs for multiple delivery locations.
        
        Args:
            locations: List of location dicts with 'name' and 'distance_category'
            weight_per_location: Dictionary mapping location names to weights
            delivery_method: Delivery method
            
        Returns:
            Dictionary with total and per-location breakdown
        """
        total_cost = Decimal('0')
        location_breakdown = []
        
        for location in locations:
            location_name = location.get('name')
            distance_category = location.get('distance_category', 'regional')
            weight = weight_per_location.get(location_name, 10.0)
            
            cost = self.calculate(
                weight_kg=weight,
                delivery_method=delivery_method,
                distance_category=distance_category
            )
            
            location_breakdown.append({
                'location': location_name,
                'weight_kg': weight,
                'distance_category': distance_category,
                'cost': float(cost)
            })
            
            total_cost += cost
        
        return {
            'total_cost': float(total_cost),
            'location_count': len(location_breakdown),
            'locations': location_breakdown
        }
    
    def estimate_by_distance(
        self,
        distance_km: float,
        weight_kg: float,
        delivery_method: str = 'standard'
    ) -> Decimal:
        """Estimate cost based on distance in km.
        
        Args:
            distance_km: Distance in kilometers
            weight_kg: Weight in kg
            delivery_method: Delivery method
            
        Returns:
            Estimated cost
        """
        # Determine distance category
        if distance_km < 50:
            distance_category = 'local'
        elif distance_km < 300:
            distance_category = 'regional'
        elif distance_km < 1500:
            distance_category = 'national'
        else:
            distance_category = 'distant'
        
        return self.calculate(
            weight_kg=weight_kg,
            delivery_method=delivery_method,
            distance_category=distance_category
        )
    
    def _estimate_delivery_days(
        self,
        delivery_method: str,
        distance_category: str
    ) -> int:
        """Estimate delivery days.
        
        Args:
            delivery_method: Delivery method
            distance_category: Distance category
            
        Returns:
            Estimated delivery days
        """
        base_days = {
            'overnight': 1,
            'express': 2,
            'standard': 5,
            'international': 15
        }
        
        distance_addition = {
            'local': 0,
            'regional': 1,
            'national': 2,
            'distant': 3,
            'international': 7
        }
        
        days = base_days.get(delivery_method, 5)
        days += distance_addition.get(distance_category, 1)
        
        return days
    
    def calculate_packaging_only(
        self,
        items: list,
        custom_sizes: Optional[Dict[str, str]] = None
    ) -> Decimal:
        """Calculate packaging cost for multiple items.
        
        Args:
            items: List of item dicts with 'product_id' and 'quantity'
            custom_sizes: Optional dict mapping product_ids to sizes
            
        Returns:
            Total packaging cost
        """
        total_cost = Decimal('0')
        
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            
            # Determine size
            if custom_sizes and product_id in custom_sizes:
                size = custom_sizes[product_id]
            else:
                size = 'medium'  # Default
            
            cost = self.packaging_costs.get(size, Decimal('150'))
            total_cost += cost * Decimal(quantity)
        
        return self.round_price(total_cost)
