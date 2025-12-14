"""Pricing calculation logic."""
from typing import Dict, Any
import structlog

logger = structlog.get_logger()


class PricingCalculator:
    """Calculate pricing for products."""
    
    def __init__(self):
        """Initialize pricing calculator."""
        self.logger = logger.bind(component="PricingCalculator")
    
    async def calculate_line_item(
        self,
        product: Dict[str, Any],
        quantity: int,
        strategy: str = "competitive"
    ) -> Dict[str, Any]:
        """Calculate pricing for a line item.
        
        Args:
            product: Product dictionary
            quantity: Quantity required
            strategy: Pricing strategy (competitive, premium, budget)
            
        Returns:
            Pricing breakdown
        """
        # Get base price
        base_price = self._get_base_price(product, strategy)
        
        # Calculate discount based on quantity
        discount_percent = self._calculate_discount(quantity, base_price)
        
        # Calculate discounted price
        discounted_price = base_price * (1 - discount_percent / 100)
        
        # Line total
        line_total = discounted_price * quantity
        
        # Additional costs
        testing_costs = self._calculate_testing_costs(product, quantity)
        certification_costs = self._calculate_certification_costs(product)
        
        return {
            "base_price": base_price,
            "unit_price": base_price,
            "discount_percent": discount_percent,
            "discounted_price": discounted_price,
            "quantity": quantity,
            "line_total": line_total,
            "testing_costs": testing_costs,
            "certification_costs": certification_costs,
        }
    
    def _get_base_price(
        self,
        product: Dict[str, Any],
        strategy: str
    ) -> float:
        """Get base price based on strategy.
        
        Args:
            product: Product dictionary
            strategy: Pricing strategy
            
        Returns:
            Base price
        """
        # Try different price fields
        selling_price = product.get("selling_price")
        dealer_price = product.get("dealer_price")
        mrp = product.get("mrp")
        
        if strategy == "competitive":
            # Use selling price or 85% of MRP
            return selling_price or (mrp * 0.85 if mrp else 0)
        elif strategy == "premium":
            # Use MRP or 1.15x selling price
            return mrp or (selling_price * 1.15 if selling_price else 0)
        elif strategy == "budget":
            # Use dealer price or 75% of MRP
            return dealer_price or (mrp * 0.75 if mrp else 0)
        else:
            return selling_price or mrp or 0
    
    def _calculate_discount(self, quantity: int, unit_price: float) -> float:
        """Calculate quantity discount.
        
        Args:
            quantity: Order quantity
            unit_price: Unit price
            
        Returns:
            Discount percentage
        """
        order_value = quantity * unit_price
        
        # Discount tiers based on order value
        if order_value > 1000000:  # > 10 Lakhs
            return 15.0
        elif order_value > 500000:  # > 5 Lakhs
            return 10.0
        elif order_value > 100000:  # > 1 Lakh
            return 5.0
        else:
            return 0.0
    
    def _calculate_testing_costs(
        self,
        product: Dict[str, Any],
        quantity: int
    ) -> float:
        """Calculate testing costs.
        
        Args:
            product: Product dictionary
            quantity: Quantity
            
        Returns:
            Testing cost
        """
        # Standard testing costs for electrical products
        # Typically ₹500-1000 per batch
        
        category = product.get("category", "").lower()
        
        if "cable" in category or "wire" in category:
            # Cable testing required
            return 500.0
        elif quantity > 100:
            # Bulk order testing
            return 800.0
        else:
            return 0.0
    
    def _calculate_certification_costs(
        self,
        product: Dict[str, Any]
    ) -> float:
        """Calculate certification costs.
        
        Args:
            product: Product dictionary
            
        Returns:
            Certification cost
        """
        # Check if certifications needed
        certifications = product.get("certifications", "")
        
        if "BIS" in certifications or "ISI" in certifications:
            # BIS/ISI certification documentation
            return 300.0
        else:
            return 0.0
