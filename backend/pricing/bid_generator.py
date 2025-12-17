"""
Bid Generator - Generates complete commercial bids with all cost components.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, date
import structlog

from pricing.product_pricer import ProductPricer, ProductPrice
from pricing.test_calculator import TestCostCalculator
from pricing.logistics_calculator import LogisticsCalculator
from pricing.margin_calculator import MarginCalculator, MarginBreakdown
from pricing.base_calculator import PriceBreakdown

logger = structlog.get_logger()


@dataclass
class CommercialBid:
    """Complete commercial bid."""
    bid_id: str
    rfp_reference: str
    created_date: str
    validity_days: int = 90
    
    # Customer info
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    
    # Items
    items: List[Dict[str, Any]] = field(default_factory=list)
    
    # Cost breakdown
    product_cost: Decimal = Decimal('0')
    testing_cost: Decimal = Decimal('0')
    logistics_cost: Decimal = Decimal('0')
    packaging_cost: Decimal = Decimal('0')
    overhead_cost: Decimal = Decimal('0')
    
    # Pricing
    subtotal: Decimal = Decimal('0')
    margin_rate: Decimal = Decimal('0')
    margin_amount: Decimal = Decimal('0')
    
    # Taxes and discounts
    tax_rate: Decimal = Decimal('18')  # GST
    tax_amount: Decimal = Decimal('0')
    discount_rate: Decimal = Decimal('0')
    discount_amount: Decimal = Decimal('0')
    
    # Final pricing
    total_before_tax: Decimal = Decimal('0')
    grand_total: Decimal = Decimal('0')
    
    # Terms
    payment_terms: str = "30 days net"
    delivery_terms: str = "Ex-works"
    warranty_period: str = "12 months"
    
    # Additional info
    notes: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    exclusions: List[str] = field(default_factory=list)
    
    currency: str = "INR"
    
    def calculate_totals(self):
        """Calculate all totals."""
        # Subtotal
        self.subtotal = (
            self.product_cost +
            self.testing_cost +
            self.logistics_cost +
            self.packaging_cost +
            self.overhead_cost
        )
        
        # Apply margin
        self.total_before_tax = self.subtotal + self.margin_amount
        
        # Apply discount
        if self.discount_rate > 0:
            self.discount_amount = self.total_before_tax * self.discount_rate / Decimal('100')
            self.total_before_tax -= self.discount_amount
        
        # Apply tax
        self.tax_amount = self.total_before_tax * self.tax_rate / Decimal('100')
        
        # Grand total
        self.grand_total = self.total_before_tax + self.tax_amount
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'bid_id': self.bid_id,
            'rfp_reference': self.rfp_reference,
            'created_date': self.created_date,
            'validity_days': self.validity_days,
            'customer_name': self.customer_name,
            'customer_address': self.customer_address,
            'items': self.items,
            'cost_breakdown': {
                'product_cost': float(self.product_cost),
                'testing_cost': float(self.testing_cost),
                'logistics_cost': float(self.logistics_cost),
                'packaging_cost': float(self.packaging_cost),
                'overhead_cost': float(self.overhead_cost),
                'subtotal': float(self.subtotal)
            },
            'pricing': {
                'margin_rate': float(self.margin_rate),
                'margin_amount': float(self.margin_amount),
                'tax_rate': float(self.tax_rate),
                'tax_amount': float(self.tax_amount),
                'discount_rate': float(self.discount_rate),
                'discount_amount': float(self.discount_amount),
                'total_before_tax': float(self.total_before_tax),
                'grand_total': float(self.grand_total)
            },
            'terms': {
                'payment': self.payment_terms,
                'delivery': self.delivery_terms,
                'warranty': self.warranty_period
            },
            'currency': self.currency,
            'notes': self.notes,
            'assumptions': self.assumptions,
            'exclusions': self.exclusions
        }


class BidGenerator:
    """Generate complete commercial bids."""
    
    def __init__(
        self,
        product_pricer: Optional[ProductPricer] = None,
        test_calculator: Optional[TestCostCalculator] = None,
        logistics_calculator: Optional[LogisticsCalculator] = None,
        margin_calculator: Optional[MarginCalculator] = None
    ):
        """Initialize bid generator.
        
        Args:
            product_pricer: Product pricing engine
            test_calculator: Testing cost calculator
            logistics_calculator: Logistics cost calculator
            margin_calculator: Margin calculator
        """
        self.product_pricer = product_pricer or ProductPricer()
        self.test_calculator = test_calculator or TestCostCalculator()
        self.logistics_calculator = logistics_calculator or LogisticsCalculator()
        self.margin_calculator = margin_calculator or MarginCalculator()
        
        self.logger = logger.bind(component="BidGenerator")
    
    def generate_bid(
        self,
        rfp_reference: str,
        items: List[Dict[str, Any]],
        testing_requirements: Optional[List[Dict[str, Any]]] = None,
        logistics_params: Optional[Dict[str, Any]] = None,
        margin_rate: Optional[Decimal] = None,
        customer_info: Optional[Dict[str, Any]] = None,
        tax_rate: Decimal = Decimal('18'),
        discount_rate: Decimal = Decimal('0')
    ) -> CommercialBid:
        """Generate complete commercial bid.
        
        Args:
            rfp_reference: RFP reference number
            items: List of items with product_id, quantity
            testing_requirements: Testing requirements
            logistics_params: Logistics parameters
            margin_rate: Desired margin rate
            customer_info: Customer information
            tax_rate: Tax rate (GST)
            discount_rate: Discount rate
            
        Returns:
            CommercialBid object
        """
        self.logger.info("Generating commercial bid", rfp_ref=rfp_reference)
        
        # Generate bid ID
        bid_id = f"BID-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Initialize bid
        bid = CommercialBid(
            bid_id=bid_id,
            rfp_reference=rfp_reference,
            created_date=datetime.now().isoformat(),
            tax_rate=tax_rate,
            discount_rate=discount_rate
        )
        
        # Add customer info
        if customer_info:
            bid.customer_name = customer_info.get('name')
            bid.customer_address = customer_info.get('address')
        
        # Calculate product costs
        product_result = self.product_pricer.calculate_multi_product(items)
        bid.product_cost = Decimal(str(product_result['total']))
        bid.items = product_result['items']
        
        # Calculate testing costs
        if testing_requirements:
            test_result = self.test_calculator.calculate_testing_requirements(
                testing_requirements
            )
            bid.testing_cost = Decimal(str(test_result['total_cost']))
        
        # Calculate logistics costs
        if logistics_params:
            logistics_cost = self.logistics_calculator.calculate(
                weight_kg=logistics_params.get('weight_kg', 100),
                delivery_method=logistics_params.get('delivery_method', 'standard'),
                distance_category=logistics_params.get('distance_category', 'regional'),
                product_value=bid.product_cost,
                packaging_size=logistics_params.get('packaging_size', 'medium'),
                quantity=len(items)
            )
            bid.logistics_cost = logistics_cost
        
        # Calculate margin
        margin_breakdown = self.margin_calculator.calculate_detailed(
            product_cost=bid.product_cost,
            testing_cost=bid.testing_cost,
            logistics_cost=bid.logistics_cost,
            margin_rate=margin_rate
        )
        
        bid.overhead_cost = margin_breakdown.overhead_cost
        bid.margin_rate = margin_breakdown.margin_rate
        bid.margin_amount = margin_breakdown.margin_amount
        
        # Calculate totals
        bid.calculate_totals()
        
        # Add standard assumptions
        bid.assumptions = [
            "Prices are valid for {} days from date of quote".format(bid.validity_days),
            "Prices are subject to change based on raw material costs",
            "All products meet specified technical requirements",
            "Testing costs are estimates and subject to actual laboratory charges"
        ]
        
        # Add standard exclusions
        bid.exclusions = [
            "Installation and commissioning charges",
            "Site preparation costs",
            "Customs and import duties (if applicable)",
            "Any costs not explicitly mentioned in this quotation"
        ]
        
        self.logger.info(
            "Bid generated successfully",
            bid_id=bid_id,
            items=len(items),
            grand_total=float(bid.grand_total)
        )
        
        return bid
    
    def generate_from_rfp(
        self,
        rfp_document: Dict[str, Any],
        pricing_params: Optional[Dict[str, Any]] = None
    ) -> CommercialBid:
        """Generate bid directly from RFP document.
        
        Args:
            rfp_document: Parsed RFP document from RFPPipeline
            pricing_params: Additional pricing parameters
            
        Returns:
            CommercialBid object
        """
        pricing_params = pricing_params or {}
        
        # Extract RFP reference
        rfp_reference = rfp_document.get('file_path', 'Unknown')
        
        # Extract BOQ items
        boq_items = rfp_document.get('boq_items', [])
        items = []
        for boq_item in boq_items:
            items.append({
                'product_id': boq_item.get('item_no', 'UNKNOWN'),
                'quantity': int(boq_item.get('quantity', 1)),
                'description': boq_item.get('description', '')
            })
        
        # Extract testing requirements
        testing_reqs = rfp_document.get('testing_requirements', [])
        test_items = []
        for req in testing_reqs:
            test_items.append({
                'test_type': req.get('name', '').lower().replace(' ', '_'),
                'is_mandatory': req.get('is_mandatory', True)
            })
        
        # Default logistics params
        logistics_params = pricing_params.get('logistics', {
            'weight_kg': 100,
            'delivery_method': 'standard',
            'distance_category': 'regional'
        })
        
        # Generate bid
        return self.generate_bid(
            rfp_reference=rfp_reference,
            items=items,
            testing_requirements=test_items if test_items else None,
            logistics_params=logistics_params,
            margin_rate=pricing_params.get('margin_rate'),
            tax_rate=Decimal(str(pricing_params.get('tax_rate', 18))),
            discount_rate=Decimal(str(pricing_params.get('discount_rate', 0)))
        )
    
    def generate_comparative_bids(
        self,
        rfp_reference: str,
        items: List[Dict[str, Any]],
        margin_scenarios: List[Decimal]
    ) -> List[CommercialBid]:
        """Generate multiple bids with different margin scenarios.
        
        Args:
            rfp_reference: RFP reference
            items: Items list
            margin_scenarios: List of margin rates to test
            
        Returns:
            List of CommercialBid objects
        """
        bids = []
        
        for margin_rate in margin_scenarios:
            bid = self.generate_bid(
                rfp_reference=rfp_reference,
                items=items,
                margin_rate=margin_rate
            )
            bid.notes.append(f"Scenario with {float(margin_rate)}% margin")
            bids.append(bid)
        
        return bids
    
    def export_bid_to_dict(self, bid: CommercialBid) -> Dict[str, Any]:
        """Export bid to detailed dictionary format.
        
        Args:
            bid: CommercialBid object
            
        Returns:
            Detailed dictionary
        """
        return bid.to_dict()
    
    def generate_bid_summary(self, bid: CommercialBid) -> str:
        """Generate human-readable bid summary.
        
        Args:
            bid: CommercialBid object
            
        Returns:
            Summary string
        """
        summary = f"""
COMMERCIAL BID SUMMARY
=====================

Bid ID: {bid.bid_id}
RFP Reference: {bid.rfp_reference}
Date: {bid.created_date}
Valid for: {bid.validity_days} days

CUSTOMER INFORMATION
-------------------
Name: {bid.customer_name or 'N/A'}
Address: {bid.customer_address or 'N/A'}

COST BREAKDOWN
-------------
Product Cost:    {bid.currency} {float(bid.product_cost):,.2f}
Testing Cost:    {bid.currency} {float(bid.testing_cost):,.2f}
Logistics Cost:  {bid.currency} {float(bid.logistics_cost):,.2f}
Overhead Cost:   {bid.currency} {float(bid.overhead_cost):,.2f}
--------------
Subtotal:        {bid.currency} {float(bid.subtotal):,.2f}

PRICING
-------
Margin ({float(bid.margin_rate)}%):     {bid.currency} {float(bid.margin_amount):,.2f}
Total before tax: {bid.currency} {float(bid.total_before_tax):,.2f}
GST ({float(bid.tax_rate)}%):          {bid.currency} {float(bid.tax_amount):,.2f}
--------------
GRAND TOTAL:      {bid.currency} {float(bid.grand_total):,.2f}

ITEMS
-----
Total Items: {len(bid.items)}

TERMS & CONDITIONS
-----------------
Payment: {bid.payment_terms}
Delivery: {bid.delivery_terms}
Warranty: {bid.warranty_period}
"""
        return summary
