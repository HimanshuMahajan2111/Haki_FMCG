"""Pricing Agent - Handles cost estimation and pricing strategy."""
from typing import Any, Dict, List
import structlog

from agents.base_agent import BaseAgent
from data.pricing_calculator import PricingCalculator

logger = structlog.get_logger()


class PricingAgent(BaseAgent):
    """Agent responsible for pricing calculations and cost estimation."""
    
    def __init__(self, model: str = None):
        """Initialize Pricing Agent."""
        super().__init__(
            agent_name="PricingAgent",
            agent_type="pricing",
            model=model
        )
        self.pricing_calculator = PricingCalculator()
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process matched products and calculate pricing.
        
        Args:
            input_data: Dictionary containing:
                - matched_products: Products matched by technical agent
                - quantities: Required quantities
                - pricing_strategy: Strategy to use (competitive, premium, etc.)
                
        Returns:
            Dictionary containing pricing breakdown and totals
        """
        self.logger.info("Starting pricing calculation")
        
        matched_products = input_data.get("matched_products", [])
        quantities = input_data.get("quantities", {})
        strategy = input_data.get("pricing_strategy", "competitive")
        
        line_items = []
        subtotal = 0.0
        
        for match in matched_products:
            product = match.get("matched_product", {})
            requirement = match.get("requirement", {})
            
            item_name = requirement.get("item_name", "Unknown Item")
            quantity = quantities.get(item_name, requirement.get("quantity", 1))
            
            # Calculate pricing for this line item
            pricing = await self.pricing_calculator.calculate_line_item(
                product=product,
                quantity=quantity,
                strategy=strategy
            )
            
            line_items.append({
                "item_name": item_name,
                "product_code": product.get("product_code"),
                "product_name": product.get("product_name"),
                "quantity": quantity,
                "unit_price": pricing["unit_price"],
                "discount_percent": pricing["discount_percent"],
                "discounted_price": pricing["discounted_price"],
                "line_total": pricing["line_total"],
                "testing_costs": pricing.get("testing_costs", 0),
                "certification_costs": pricing.get("certification_costs", 0),
            })
            
            subtotal += pricing["line_total"]
        
        # Calculate additional costs
        testing_total = sum(item["testing_costs"] for item in line_items)
        certification_total = sum(item["certification_costs"] for item in line_items)
        
        # Calculate taxes and final total
        gst_percent = 18.0  # GST for electrical products
        gst_amount = (subtotal + testing_total + certification_total) * (gst_percent / 100)
        
        total_before_tax = subtotal + testing_total + certification_total
        grand_total = total_before_tax + gst_amount
        
        result = {
            "line_items": line_items,
            "pricing_summary": {
                "subtotal": round(subtotal, 2),
                "testing_costs": round(testing_total, 2),
                "certification_costs": round(certification_total, 2),
                "total_before_tax": round(total_before_tax, 2),
                "gst_percent": gst_percent,
                "gst_amount": round(gst_amount, 2),
                "grand_total": round(grand_total, 2),
            },
            "pricing_strategy": strategy,
            "currency": "INR",
            "validity_days": 90,
            "payment_terms": self._get_payment_terms(grand_total),
        }
        
        self.logger.info(
            "Pricing calculation completed",
            line_items=len(line_items),
            grand_total=grand_total
        )
        
        return result
    
    def _get_payment_terms(self, total_amount: float) -> Dict[str, Any]:
        """Determine payment terms based on total amount.
        
        Args:
            total_amount: Total order value
            
        Returns:
            Payment terms dictionary
        """
        # Standard payment terms for B2B electrical products
        if total_amount < 100000:  # Less than 1 Lakh
            return {
                "advance_percent": 50,
                "on_delivery_percent": 50,
                "credit_days": 0,
            }
        elif total_amount < 1000000:  # Less than 10 Lakhs
            return {
                "advance_percent": 30,
                "on_delivery_percent": 50,
                "credit_days": 30,
            }
        else:  # 10 Lakhs and above
            return {
                "advance_percent": 20,
                "on_delivery_percent": 50,
                "credit_days": 45,
            }
