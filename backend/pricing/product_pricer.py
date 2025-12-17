"""
Product Pricer - Looks up product prices from catalog and applies pricing rules.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from decimal import Decimal
import structlog

from pricing.base_calculator import PriceCalculator

logger = structlog.get_logger()


@dataclass
class ProductPrice:
    """Product pricing information."""
    product_id: str
    product_name: str
    base_price: Decimal
    unit: str = "unit"
    
    # Pricing details
    list_price: Optional[Decimal] = None
    dealer_price: Optional[Decimal] = None
    bulk_price: Optional[Decimal] = None
    
    # Volume discounts
    volume_breaks: Dict[int, Decimal] = None  # quantity -> discount %
    
    # Metadata
    manufacturer: Optional[str] = None
    category: Optional[str] = None
    last_updated: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'product_id': self.product_id,
            'product_name': self.product_name,
            'base_price': float(self.base_price),
            'unit': self.unit,
            'list_price': float(self.list_price) if self.list_price else None,
            'dealer_price': float(self.dealer_price) if self.dealer_price else None,
            'bulk_price': float(self.bulk_price) if self.bulk_price else None,
            'volume_breaks': {k: float(v) for k, v in (self.volume_breaks or {}).items()},
            'manufacturer': self.manufacturer,
            'category': self.category
        }


class ProductPricer(PriceCalculator):
    """Look up and calculate product prices."""
    
    def __init__(self, price_catalog: Optional[Dict[str, ProductPrice]] = None):
        """Initialize product pricer.
        
        Args:
            price_catalog: Dictionary mapping product IDs to ProductPrice objects
        """
        super().__init__()
        self.price_catalog = price_catalog or {}
        self.logger = logger.bind(component="ProductPricer")
    
    def load_price_catalog(self, catalog: Dict[str, ProductPrice]):
        """Load price catalog.
        
        Args:
            catalog: Price catalog dictionary
        """
        self.price_catalog = catalog
        self.logger.info("Price catalog loaded", products=len(catalog))
    
    def add_product_price(self, product: ProductPrice):
        """Add product price to catalog.
        
        Args:
            product: ProductPrice object
        """
        self.price_catalog[product.product_id] = product
        self.logger.debug("Product price added", product_id=product.product_id)
    
    def get_product_price(self, product_id: str) -> Optional[ProductPrice]:
        """Get product price from catalog.
        
        Args:
            product_id: Product ID
            
        Returns:
            ProductPrice or None if not found
        """
        return self.price_catalog.get(product_id)
    
    def calculate(
        self,
        product_id: str,
        quantity: int,
        price_type: str = 'base',
        apply_volume_discount: bool = True
    ) -> Decimal:
        """Calculate product price for given quantity.
        
        Args:
            product_id: Product ID
            quantity: Quantity
            price_type: Type of price ('base', 'list', 'dealer', 'bulk')
            apply_volume_discount: Whether to apply volume discounts
            
        Returns:
            Total price as Decimal
        """
        product = self.get_product_price(product_id)
        
        if not product:
            self.logger.error("Product not found in catalog", product_id=product_id)
            raise ValueError(f"Product {product_id} not found in catalog")
        
        # Get base price based on type
        if price_type == 'list' and product.list_price:
            unit_price = product.list_price
        elif price_type == 'dealer' and product.dealer_price:
            unit_price = product.dealer_price
        elif price_type == 'bulk' and product.bulk_price:
            unit_price = product.bulk_price
        else:
            unit_price = product.base_price
        
        # Calculate subtotal
        subtotal = unit_price * Decimal(quantity)
        
        # Apply volume discount if enabled
        if apply_volume_discount and product.volume_breaks:
            discount_rate = self._get_volume_discount(quantity, product.volume_breaks)
            discount_amount = subtotal * discount_rate / Decimal('100')
            subtotal -= discount_amount
            
            self.logger.debug(
                "Volume discount applied",
                quantity=quantity,
                discount_rate=float(discount_rate),
                discount_amount=float(discount_amount)
            )
        
        self.logger.info(
            "Product price calculated",
            product_id=product_id,
            quantity=quantity,
            unit_price=float(unit_price),
            total=float(subtotal)
        )
        
        return self.round_price(subtotal)
    
    def calculate_multi_product(
        self,
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate prices for multiple products.
        
        Args:
            items: List of dicts with 'product_id', 'quantity', 'price_type' (optional)
            
        Returns:
            Dictionary with total and item-wise breakdown
        """
        total = Decimal('0')
        item_breakdown = []
        
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            price_type = item.get('price_type', 'base')
            
            try:
                item_total = self.calculate(
                    product_id,
                    quantity,
                    price_type=price_type
                )
                
                product = self.get_product_price(product_id)
                
                item_breakdown.append({
                    'product_id': product_id,
                    'product_name': product.product_name if product else 'Unknown',
                    'quantity': quantity,
                    'unit_price': float(item_total / Decimal(quantity)),
                    'total': float(item_total)
                })
                
                total += item_total
                
            except Exception as e:
                self.logger.error(
                    "Failed to calculate item price",
                    product_id=product_id,
                    error=str(e)
                )
        
        return {
            'total': float(total),
            'items': item_breakdown,
            'item_count': len(item_breakdown)
        }
    
    def _get_volume_discount(
        self,
        quantity: int,
        volume_breaks: Dict[int, Decimal]
    ) -> Decimal:
        """Get volume discount rate for quantity.
        
        Args:
            quantity: Order quantity
            volume_breaks: Dictionary of quantity breaks to discount rates
            
        Returns:
            Discount rate as Decimal
        """
        # Sort breaks by quantity (descending)
        sorted_breaks = sorted(volume_breaks.items(), key=lambda x: x[0], reverse=True)
        
        # Find applicable discount
        for break_qty, discount_rate in sorted_breaks:
            if quantity >= break_qty:
                return discount_rate
        
        return Decimal('0')
    
    def estimate_price_range(
        self,
        product_id: str,
        min_quantity: int,
        max_quantity: int
    ) -> Dict[str, Any]:
        """Estimate price range for quantity range.
        
        Args:
            product_id: Product ID
            min_quantity: Minimum quantity
            max_quantity: Maximum quantity
            
        Returns:
            Dictionary with min and max prices
        """
        min_price = self.calculate(product_id, min_quantity)
        max_price = self.calculate(product_id, max_quantity)
        
        product = self.get_product_price(product_id)
        
        return {
            'product_id': product_id,
            'product_name': product.product_name if product else 'Unknown',
            'min_quantity': min_quantity,
            'max_quantity': max_quantity,
            'min_total': float(min_price),
            'max_total': float(max_price),
            'min_unit_price': float(min_price / Decimal(min_quantity)),
            'max_unit_price': float(max_price / Decimal(max_quantity))
        }
