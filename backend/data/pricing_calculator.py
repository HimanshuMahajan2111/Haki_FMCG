"""Pricing calculation logic."""
from typing import Dict, Any
import structlog

logger = structlog.get_logger()


class PricingCalculator:
    """Calculate pricing for products."""
    
    def __init__(self):
        """Initialize pricing calculator."""
        self.data_service = None
        self.logger = logger.bind(component="PricingCalculator")
    
    def _get_data_service(self):
        """Lazy load data service to avoid circular imports."""
        if self.data_service is None:
            from services.data_service import get_data_service
            self.data_service = get_data_service()
    
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
        self._get_data_service()  # Lazy load service
        
        # Get pricing data from data service if available
        product_code = product.get("product_code")
        pricing_data = None
        if product_code:
            pricing_data = await self.data_service.get_pricing_for_product(product_code)
        
        # Get base price from pricing data or product
        base_price = self._get_base_price(product, strategy, pricing_data)
        
        # Calculate discount based on quantity
        discount_percent = self._calculate_discount(quantity, base_price)
        
        # Calculate discounted price
        discounted_price = base_price * (1 - discount_percent / 100)
        
        # Line total
        line_total = discounted_price * quantity
        
        # Additional costs
        testing_costs = await self._calculate_testing_costs(product, quantity)
        certification_costs = await self._calculate_certification_costs(product)
        
        self.logger.info(
            "Calculated line item pricing",
            product_code=product_code,
            quantity=quantity,
            base_price=base_price,
            line_total=line_total
        )
        
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
        strategy: str,
        pricing_data: Dict[str, Any] = None
    ) -> float:
        """Get base price based on strategy.
        
        Args:
            product: Product dictionary
            strategy: Pricing strategy
            pricing_data: Optional pricing data from data service
            
        Returns:
            Base price
        """
        # Try to get prices from pricing data first, then product
        if pricing_data:
            selling_price = pricing_data.get("selling_price") or product.get("selling_price")
            dealer_price = pricing_data.get("dealer_price") or product.get("dealer_price")
            mrp = pricing_data.get("mrp") or product.get("mrp")
        else:
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
    
    async def _calculate_testing_costs(
        self,
        product: Dict[str, Any],
        quantity: int
    ) -> float:
        """Calculate testing costs using data from testing data loader.
        
        Args:
            product: Product dictionary
            quantity: Quantity
            
        Returns:
            Testing cost
        """
        self._get_data_service()  # Lazy load service
        
        # Get testing data from data service
        testing_data = await self.data_service.get_testing_data()
        
        category = product.get("category", "").lower()
        
        # Look for applicable tests
        estimated_cost = 0.0
        
        if "cable" in category or "wire" in category:
            # Look for type tests in testing data
            type_tests = testing_data.get("type_tests", [])
            if type_tests:
                # Get average cost from test data
                test_costs = [t.get("estimated_cost", 500) for t in type_tests if t.get("estimated_cost")]
                if test_costs:
                    estimated_cost = sum(test_costs) / len(test_costs)
                else:
                    estimated_cost = 500.0
            else:
                estimated_cost = 500.0
        elif quantity > 100:
            # Bulk order testing
            estimated_cost = 800.0
        
        return estimated_cost
    
    async def _calculate_certification_costs(
        self,
        product: Dict[str, Any]
    ) -> float:
        """Calculate certification costs using data from standards.
        
        Args:
            product: Product dictionary
            
        Returns:
            Certification cost
        """
        self._get_data_service()  # Lazy load service
        
        # Get testing data for certifications
        testing_data = await self.data_service.get_testing_data()
        certifications_list = testing_data.get("certifications", [])
        
        # Check if certifications needed
        certifications = product.get("certifications", "")
        
        if "BIS" in certifications or "ISI" in certifications:
            # Look for BIS certification cost in data
            for cert in certifications_list:
                if "BIS" in cert.get("test_name", "") or "ISI" in cert.get("test_name", ""):
                    return cert.get("estimated_cost", 300.0)
            return 300.0
        else:
            return 0.0
