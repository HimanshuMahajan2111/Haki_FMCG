"""
Enhanced Pricing Agent - Commercial bid generation with comprehensive cost calculation.

This agent:
1. Receives technical recommendations from Technical Agent
2. Receives testing requirements
3. Calculates all costs (products, testing, logistics, installation, taxes)
4. Applies profit margins and contingencies
5. Generates commercial bid documents
6. Outputs pricing tables and terms
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import json
import structlog
import pandas as pd
from enum import Enum

logger = structlog.get_logger()


class PricingTier(Enum):
    """Pricing tier based on order value."""
    STANDARD = "standard"
    VOLUME = "volume"
    ENTERPRISE = "enterprise"
    GOVERNMENT = "government"


class PaymentTerms(Enum):
    """Standard payment terms."""
    NET_30 = "Net 30 days"
    NET_45 = "Net 45 days"
    NET_60 = "Net 60 days"
    ADVANCE_50 = "50% Advance, 50% on Delivery"
    ADVANCE_30 = "30% Advance, 70% on Delivery"
    LC_90 = "Letter of Credit - 90 days"


@dataclass
class TestingCost:
    """Testing cost item."""
    test_name: str
    test_type: str  # routine, type, special
    laboratory: str
    standard: str
    unit_cost: float
    quantity: int
    total_cost: float
    duration_days: int
    mandatory: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProductPricing:
    """Detailed pricing for a product."""
    product_id: str
    product_name: str
    manufacturer: str
    
    # Base pricing
    unit_price: float
    quantity: int
    subtotal: float
    
    # Discounts
    volume_discount_percent: float = 0.0
    volume_discount_amount: float = 0.0
    negotiated_discount_percent: float = 0.0
    negotiated_discount_amount: float = 0.0
    
    # After discounts
    discounted_price: float = 0.0
    
    # Additional costs
    packaging_cost: float = 0.0
    handling_cost: float = 0.0
    logistics_cost: float = 0.0
    installation_cost: float = 0.0
    
    # Testing costs
    testing_costs: List[TestingCost] = field(default_factory=list)
    testing_total: float = 0.0
    
    # Taxes
    gst_percent: float = 18.0
    gst_amount: float = 0.0
    
    # Final totals
    total_before_tax: float = 0.0
    total_after_tax: float = 0.0
    
    # Delivery
    delivery_days: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['testing_costs'] = [tc.to_dict() for tc in self.testing_costs]
        return data


@dataclass
class BidSummary:
    """Overall bid summary."""
    bid_id: str
    rfp_id: str
    rfp_title: str
    customer_name: str
    
    # Dates
    bid_date: str
    validity_days: int = 90
    valid_until: str = ""
    
    # Totals
    products_subtotal: float = 0.0
    total_discounts: float = 0.0
    testing_costs_total: float = 0.0
    logistics_total: float = 0.0
    installation_total: float = 0.0
    
    # Tax
    taxable_amount: float = 0.0
    gst_total: float = 0.0
    
    # Grand total
    grand_total: float = 0.0
    
    # Margins
    cost_base: float = 0.0
    margin_percent: float = 0.0
    margin_amount: float = 0.0
    profit_percent: float = 0.0
    
    # Terms
    payment_terms: str = PaymentTerms.NET_30.value
    delivery_terms: str = "Ex-Works"
    warranty_period_months: int = 12
    pricing_tier: str = PricingTier.STANDARD.value
    
    # Metadata
    prepared_by: str = "Pricing Agent"
    approved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CostCalculator:
    """Calculate various cost components."""
    
    def __init__(self):
        """Initialize cost calculator."""
        self.logger = logger.bind(component="CostCalculator")
        
        # Cost multipliers (configurable)
        self.packaging_rate = 0.02  # 2% of product value
        self.handling_rate = 0.01  # 1% of product value
        self.logistics_rate_per_kg = 50  # ₹50 per kg
        self.installation_rate = 0.05  # 5% of product value
        
        # GST rates by category
        self.gst_rates = {
            'Cable': 18.0,
            'Switchgear': 18.0,
            'Lighting': 18.0,
            'Electrical': 18.0,
            'Testing': 18.0,
            'default': 18.0
        }
    
    def calculate_volume_discount(self, quantity: int, unit_price: float) -> Tuple[float, float]:
        """Calculate volume discount based on quantity.
        
        Args:
            quantity: Order quantity
            unit_price: Unit price
            
        Returns:
            Tuple of (discount_percent, discount_amount)
        """
        total_value = quantity * unit_price
        
        if total_value >= 10000000:  # ≥ ₹1 Cr
            discount_percent = 15.0
        elif total_value >= 5000000:  # ≥ ₹50 L
            discount_percent = 12.0
        elif total_value >= 1000000:  # ≥ ₹10 L
            discount_percent = 10.0
        elif total_value >= 500000:  # ≥ ₹5 L
            discount_percent = 7.0
        elif total_value >= 100000:  # ≥ ₹1 L
            discount_percent = 5.0
        else:
            discount_percent = 0.0
        
        discount_amount = (quantity * unit_price * discount_percent) / 100
        
        self.logger.debug(
            "Volume discount calculated",
            quantity=quantity,
            total_value=total_value,
            discount_percent=discount_percent
        )
        
        return discount_percent, discount_amount
    
    def calculate_packaging_cost(self, product_value: float, quantity: int) -> float:
        """Calculate packaging cost."""
        return product_value * self.packaging_rate
    
    def calculate_handling_cost(self, product_value: float, quantity: int) -> float:
        """Calculate handling cost."""
        return product_value * self.handling_rate
    
    def calculate_logistics_cost(
        self,
        quantity: int,
        estimated_weight_kg: float = 10.0,
        distance_km: float = 500
    ) -> float:
        """Calculate logistics/freight cost."""
        total_weight = quantity * estimated_weight_kg
        base_cost = total_weight * self.logistics_rate_per_kg
        
        # Distance factor
        if distance_km > 1000:
            distance_factor = 1.5
        elif distance_km > 500:
            distance_factor = 1.2
        else:
            distance_factor = 1.0
        
        return base_cost * distance_factor
    
    def calculate_installation_cost(self, product_value: float, requires_installation: bool = True) -> float:
        """Calculate installation cost."""
        if not requires_installation:
            return 0.0
        return product_value * self.installation_rate
    
    def calculate_gst(self, taxable_amount: float, category: str = 'default') -> Tuple[float, float]:
        """Calculate GST.
        
        Args:
            taxable_amount: Amount before tax
            category: Product category
            
        Returns:
            Tuple of (gst_percent, gst_amount)
        """
        gst_percent = self.gst_rates.get(category, self.gst_rates['default'])
        gst_amount = (taxable_amount * gst_percent) / 100
        
        return gst_percent, gst_amount


class TestingCostCalculator:
    """Calculate testing costs."""
    
    def __init__(self):
        """Initialize testing cost calculator."""
        self.logger = logger.bind(component="TestingCostCalculator")
        
        # Standard test costs (sample data)
        self.test_catalogue = {
            # Routine tests
            'conductor_resistance': {
                'type': 'routine',
                'cost': 5000,
                'duration_days': 2,
                'standard': 'IS 694'
            },
            'voltage_withstand': {
                'type': 'routine',
                'cost': 8000,
                'duration_days': 1,
                'standard': 'IS 694'
            },
            'insulation_resistance': {
                'type': 'routine',
                'cost': 6000,
                'duration_days': 1,
                'standard': 'IS 1554'
            },
            
            # Type tests
            'mechanical_test': {
                'type': 'type',
                'cost': 25000,
                'duration_days': 5,
                'standard': 'IS 694'
            },
            'thermal_test': {
                'type': 'type',
                'cost': 30000,
                'duration_days': 7,
                'standard': 'IEC 60502'
            },
            'flame_retardant_test': {
                'type': 'type',
                'cost': 35000,
                'duration_days': 5,
                'standard': 'IEC 60332'
            },
            
            # Special tests
            'aging_test': {
                'type': 'special',
                'cost': 75000,
                'duration_days': 30,
                'standard': 'IEC 60502'
            },
            'emi_emc_test': {
                'type': 'special',
                'cost': 100000,
                'duration_days': 14,
                'standard': 'IEC 61000'
            }
        }
    
    def get_required_tests(
        self,
        product_category: str,
        standards: List[str],
        certifications: List[str]
    ) -> List[TestingCost]:
        """Get required tests for product.
        
        Args:
            product_category: Product category
            standards: Required standards
            certifications: Required certifications
            
        Returns:
            List of TestingCost objects
        """
        required_tests = []
        
        # Mandatory routine tests for all electrical products
        if product_category in ['Cable', 'Switchgear', 'Electrical']:
            routine_tests = ['conductor_resistance', 'voltage_withstand', 'insulation_resistance']
            
            for test_name in routine_tests:
                if test_name in self.test_catalogue:
                    test_info = self.test_catalogue[test_name]
                    
                    test_cost = TestingCost(
                        test_name=test_name.replace('_', ' ').title(),
                        test_type=test_info['type'],
                        laboratory='NABL Accredited Lab',
                        standard=test_info['standard'],
                        unit_cost=test_info['cost'],
                        quantity=1,
                        total_cost=test_info['cost'],
                        duration_days=test_info['duration_days'],
                        mandatory=True
                    )
                    required_tests.append(test_cost)
        
        # Type tests if specific standards mentioned
        if any('IS 694' in std or 'IEC' in std for std in standards):
            type_tests = ['mechanical_test', 'thermal_test']
            
            for test_name in type_tests:
                if test_name in self.test_catalogue:
                    test_info = self.test_catalogue[test_name]
                    
                    test_cost = TestingCost(
                        test_name=test_name.replace('_', ' ').title(),
                        test_type=test_info['type'],
                        laboratory='CPRI/ERDA',
                        standard=test_info['standard'],
                        unit_cost=test_info['cost'],
                        quantity=1,
                        total_cost=test_info['cost'],
                        duration_days=test_info['duration_days'],
                        mandatory=False
                    )
                    required_tests.append(test_cost)
        
        self.logger.info(
            "Testing requirements identified",
            product_category=product_category,
            test_count=len(required_tests)
        )
        
        return required_tests
    
    def calculate_total_testing_cost(self, tests: List[TestingCost]) -> float:
        """Calculate total testing cost."""
        return sum(test.total_cost for test in tests)
    
    def calculate_total_testing_duration(self, tests: List[TestingCost]) -> int:
        """Calculate total testing duration (max of parallel tests)."""
        if not tests:
            return 0
        return max(test.duration_days for test in tests)


class MarginCalculator:
    """Calculate profit margins and pricing tiers."""
    
    def __init__(self):
        """Initialize margin calculator."""
        self.logger = logger.bind(component="MarginCalculator")
        
        # Margin rates by pricing tier
        self.margin_rates = {
            PricingTier.STANDARD: 25.0,      # 25% margin
            PricingTier.VOLUME: 20.0,        # 20% margin for volume
            PricingTier.ENTERPRISE: 18.0,    # 18% margin for enterprise
            PricingTier.GOVERNMENT: 15.0     # 15% margin for government
        }
        
        # Contingency rates
        self.contingency_rate = 5.0  # 5% contingency
    
    def determine_pricing_tier(
        self,
        customer_type: str,
        order_value: float,
        customer_segment: str = "standard"
    ) -> PricingTier:
        """Determine pricing tier based on customer and order.
        
        Args:
            customer_type: Type of customer
            order_value: Total order value
            customer_segment: Customer segment
            
        Returns:
            PricingTier enum
        """
        customer_lower = customer_type.lower()
        
        # Government/PSU gets special tier
        if any(keyword in customer_lower for keyword in ['government', 'psu', 'railway', 'defence']):
            return PricingTier.GOVERNMENT
        
        # Enterprise tier for large orders or enterprise customers
        if order_value >= 10000000 or customer_segment == 'enterprise':
            return PricingTier.ENTERPRISE
        
        # Volume tier for medium-large orders
        if order_value >= 5000000:
            return PricingTier.VOLUME
        
        return PricingTier.STANDARD
    
    def calculate_margin(
        self,
        cost_base: float,
        pricing_tier: PricingTier
    ) -> Tuple[float, float]:
        """Calculate profit margin.
        
        Args:
            cost_base: Base cost amount
            pricing_tier: Pricing tier
            
        Returns:
            Tuple of (margin_percent, margin_amount)
        """
        margin_percent = self.margin_rates[pricing_tier]
        margin_amount = (cost_base * margin_percent) / 100
        
        self.logger.info(
            "Margin calculated",
            cost_base=cost_base,
            tier=pricing_tier.value,
            margin_percent=margin_percent
        )
        
        return margin_percent, margin_amount
    
    def apply_contingency(self, amount: float) -> Tuple[float, float]:
        """Apply contingency buffer.
        
        Args:
            amount: Base amount
            
        Returns:
            Tuple of (contingency_percent, contingency_amount)
        """
        contingency_amount = (amount * self.contingency_rate) / 100
        return self.contingency_rate, contingency_amount


class BidDocumentGenerator:
    """Generate commercial bid documents."""
    
    def __init__(self):
        """Initialize bid document generator."""
        self.logger = logger.bind(component="BidDocumentGenerator")
    
    def generate_pricing_table(self, product_pricings: List[ProductPricing]) -> pd.DataFrame:
        """Generate pricing table DataFrame.
        
        Args:
            product_pricings: List of product pricing details
            
        Returns:
            pandas DataFrame with pricing table
        """
        data = []
        
        for idx, pricing in enumerate(product_pricings, 1):
            row = {
                'S.No': idx,
                'Product': pricing.product_name,
                'Manufacturer': pricing.manufacturer,
                'Qty': pricing.quantity,
                'Unit Price (₹)': f"₹{pricing.unit_price:,.2f}",
                'Subtotal (₹)': f"₹{pricing.subtotal:,.2f}",
                'Discount (%)': f"{pricing.volume_discount_percent + pricing.negotiated_discount_percent:.1f}%",
                'Discount Amt (₹)': f"₹{pricing.volume_discount_amount + pricing.negotiated_discount_amount:,.2f}",
                'After Discount (₹)': f"₹{pricing.discounted_price:,.2f}",
                'Testing (₹)': f"₹{pricing.testing_total:,.2f}",
                'Logistics (₹)': f"₹{pricing.logistics_cost:,.2f}",
                'Installation (₹)': f"₹{pricing.installation_cost:,.2f}",
                'GST @ {:.0f}% (₹)'.format(pricing.gst_percent): f"₹{pricing.gst_amount:,.2f}",
                'Total (₹)': f"₹{pricing.total_after_tax:,.2f}",
                'Delivery': f"{pricing.delivery_days} days"
            }
            data.append(row)
        
        return pd.DataFrame(data)
    
    def generate_testing_breakdown(self, product_pricings: List[ProductPricing]) -> pd.DataFrame:
        """Generate testing cost breakdown.
        
        Args:
            product_pricings: List of product pricing details
            
        Returns:
            pandas DataFrame with testing breakdown
        """
        data = []
        
        for pricing in product_pricings:
            for test in pricing.testing_costs:
                row = {
                    'Product': pricing.product_name,
                    'Test Name': test.test_name,
                    'Test Type': test.test_type.title(),
                    'Laboratory': test.laboratory,
                    'Standard': test.standard,
                    'Duration (days)': test.duration_days,
                    'Unit Cost (₹)': f"₹{test.unit_cost:,.2f}",
                    'Quantity': test.quantity,
                    'Total Cost (₹)': f"₹{test.total_cost:,.2f}",
                    'Mandatory': 'Yes' if test.mandatory else 'Optional'
                }
                data.append(row)
        
        if not data:
            return pd.DataFrame()
        
        return pd.DataFrame(data)
    
    def generate_summary_table(self, bid_summary: BidSummary) -> pd.DataFrame:
        """Generate bid summary table.
        
        Args:
            bid_summary: Bid summary object
            
        Returns:
            pandas DataFrame with summary
        """
        data = [
            {'Description': 'Products Subtotal', 'Amount (₹)': f"₹{bid_summary.products_subtotal:,.2f}"},
            {'Description': 'Total Discounts', 'Amount (₹)': f"-₹{bid_summary.total_discounts:,.2f}"},
            {'Description': 'Testing Costs', 'Amount (₹)': f"₹{bid_summary.testing_costs_total:,.2f}"},
            {'Description': 'Logistics & Handling', 'Amount (₹)': f"₹{bid_summary.logistics_total:,.2f}"},
            {'Description': 'Installation', 'Amount (₹)': f"₹{bid_summary.installation_total:,.2f}"},
            {'Description': 'Taxable Amount', 'Amount (₹)': f"₹{bid_summary.taxable_amount:,.2f}"},
            {'Description': 'GST (18%)', 'Amount (₹)': f"₹{bid_summary.gst_total:,.2f}"},
            {'Description': '═══════════════', 'Amount (₹)': '═══════════════'},
            {'Description': 'GRAND TOTAL', 'Amount (₹)': f"₹{bid_summary.grand_total:,.2f}"}
        ]
        
        return pd.DataFrame(data)
    
    def generate_terms_and_conditions(self, bid_summary: BidSummary) -> str:
        """Generate terms and conditions text.
        
        Args:
            bid_summary: Bid summary object
            
        Returns:
            Formatted terms and conditions
        """
        terms = f"""
COMMERCIAL TERMS & CONDITIONS

1. VALIDITY
   - This quotation is valid for {bid_summary.validity_days} days from date of issue
   - Valid until: {bid_summary.valid_until}

2. PAYMENT TERMS
   - {bid_summary.payment_terms}
   - All payments in Indian Rupees (INR)
   - Bank charges to be borne by buyer

3. DELIVERY TERMS
   - {bid_summary.delivery_terms}
   - Delivery timeline: As specified per item
   - Partial deliveries: Permitted with prior approval

4. WARRANTY
   - Manufacturer's standard warranty: {bid_summary.warranty_period_months} months
   - Warranty commences from date of delivery
   - Covers manufacturing defects only

5. TAXES & DUTIES
   - GST @ 18% included in quoted price
   - Any other taxes/duties as applicable will be charged extra

6. TESTING & CERTIFICATION
   - All testing costs included in quotation
   - Testing at NABL/CPRI accredited laboratories
   - Test reports provided with delivery

7. INSTALLATION
   - Installation charges included as specified
   - Customer to provide necessary access and facilities
   - Commissioning support included

8. FORCE MAJEURE
   - Neither party liable for delays due to force majeure
   - Includes natural disasters, strikes, government actions

9. PRICE VARIATION
   - Prices firm during validity period
   - Subject to change after validity expires

10. ACCEPTANCE
    - Purchase Order required within validity period
    - Amendment charges may apply after PO

PRICING TIER: {bid_summary.pricing_tier.upper()}
PREPARED BY: {bid_summary.prepared_by}
BID DATE: {bid_summary.bid_date}
"""
        return terms.strip()


class EnhancedPricingAgent:
    """
    Enhanced Pricing Agent for commercial bid generation.
    
    Capabilities:
    1. Receives technical recommendations
    2. Calculates product costs with discounts
    3. Calculates testing costs
    4. Adds logistics, installation, taxes
    5. Applies profit margins
    6. Generates commercial bid documents
    """
    
    def __init__(self):
        """Initialize Enhanced Pricing Agent."""
        self.logger = logger.bind(component="EnhancedPricingAgent")
        
        # Initialize calculators
        self.cost_calculator = CostCalculator()
        self.testing_calculator = TestingCostCalculator()
        self.margin_calculator = MarginCalculator()
        self.document_generator = BidDocumentGenerator()
        
        # Statistics
        self.statistics = {
            'total_bids_generated': 0,
            'total_value_quoted': 0.0,
            'average_margin_percent': 0.0,
            'total_testing_costs': 0.0
        }
        
        self.logger.info("Enhanced Pricing Agent initialized")
    
    def process_pricing_request(
        self,
        technical_recommendations: Dict[str, Any],
        customer_info: Dict[str, Any],
        rfp_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process pricing request and generate bid.
        
        Args:
            technical_recommendations: Output from Technical Agent
            customer_info: Customer information
            rfp_details: RFP details
            
        Returns:
            Complete pricing response with bid documents
        """
        self.logger.info(
            "Processing pricing request",
            rfp_id=rfp_details.get('rfp_id', 'unknown')
        )
        
        # Extract product recommendations
        comparisons = technical_recommendations.get('comparisons', [])
        
        if not comparisons:
            self.logger.warning("No product recommendations found")
            return {
                'success': False,
                'error': 'No product recommendations to price',
                'bid_summary': None
            }
        
        # Generate pricing for each product
        product_pricings = []
        
        for comparison in comparisons:
            # Get top recommended product
            products = comparison.get('products', [])
            if not products:
                continue
            
            top_product = products[0]  # Top recommendation
            requirement = comparison.get('requirement', {})
            
            # Calculate pricing
            pricing = self._calculate_product_pricing(
                top_product,
                requirement,
                customer_info
            )
            
            product_pricings.append(pricing)
        
        # Generate bid summary
        bid_summary = self._generate_bid_summary(
            product_pricings,
            customer_info,
            rfp_details
        )
        
        # Generate documents
        documents = self._generate_documents(product_pricings, bid_summary)
        
        # Update statistics
        self._update_statistics(bid_summary)
        
        result = {
            'success': True,
            'bid_id': bid_summary.bid_id,
            'rfp_id': bid_summary.rfp_id,
            'generated_at': datetime.now().isoformat(),
            'bid_summary': bid_summary.to_dict(),
            'product_pricings': [p.to_dict() for p in product_pricings],
            'documents': documents,
            'statistics': self.statistics.copy()
        }
        
        self.logger.info(
            "Pricing request processed",
            bid_id=bid_summary.bid_id,
            grand_total=bid_summary.grand_total,
            products=len(product_pricings)
        )
        
        return result
    
    def _calculate_product_pricing(
        self,
        product: Dict[str, Any],
        requirement: Dict[str, Any],
        customer_info: Dict[str, Any]
    ) -> ProductPricing:
        """Calculate detailed pricing for a product.
        
        Args:
            product: Product details from technical recommendation
            requirement: Requirement details
            customer_info: Customer information
            
        Returns:
            ProductPricing object with all costs
        """
        # Initialize pricing object
        pricing = ProductPricing(
            product_id=product.get('product_id', product.get('product_code', 'unknown')),
            product_name=product.get('product_name', 'Unknown Product'),
            manufacturer=product.get('manufacturer', 'Unknown'),
            unit_price=product.get('unit_price', 0.0),
            quantity=requirement.get('quantity', 1),
            subtotal=0.0
        )
        
        # Calculate subtotal
        pricing.subtotal = pricing.unit_price * pricing.quantity
        
        # Calculate volume discount
        pricing.volume_discount_percent, pricing.volume_discount_amount = \
            self.cost_calculator.calculate_volume_discount(pricing.quantity, pricing.unit_price)
        
        # Apply negotiated discount if any
        pricing.negotiated_discount_percent = customer_info.get('negotiated_discount_percent', 0.0)
        pricing.negotiated_discount_amount = (pricing.subtotal * pricing.negotiated_discount_percent) / 100
        
        # Calculate discounted price
        total_discount = pricing.volume_discount_amount + pricing.negotiated_discount_amount
        pricing.discounted_price = pricing.subtotal - total_discount
        
        # Calculate additional costs
        pricing.packaging_cost = self.cost_calculator.calculate_packaging_cost(
            pricing.discounted_price,
            pricing.quantity
        )
        
        pricing.handling_cost = self.cost_calculator.calculate_handling_cost(
            pricing.discounted_price,
            pricing.quantity
        )
        
        pricing.logistics_cost = self.cost_calculator.calculate_logistics_cost(
            pricing.quantity,
            estimated_weight_kg=10.0,
            distance_km=customer_info.get('distance_km', 500)
        )
        
        pricing.installation_cost = self.cost_calculator.calculate_installation_cost(
            pricing.discounted_price,
            requires_installation=requirement.get('requires_installation', True)
        )
        
        # Calculate testing costs
        pricing.testing_costs = self.testing_calculator.get_required_tests(
            product_category=product.get('category', 'Electrical'),
            standards=product.get('standards_compliance', []),
            certifications=product.get('certifications', [])
        )
        pricing.testing_total = self.testing_calculator.calculate_total_testing_cost(
            pricing.testing_costs
        )
        
        # Calculate total before tax
        pricing.total_before_tax = (
            pricing.discounted_price +
            pricing.packaging_cost +
            pricing.handling_cost +
            pricing.logistics_cost +
            pricing.installation_cost +
            pricing.testing_total
        )
        
        # Calculate GST
        pricing.gst_percent, pricing.gst_amount = self.cost_calculator.calculate_gst(
            pricing.total_before_tax,
            product.get('category', 'default')
        )
        
        # Calculate final total
        pricing.total_after_tax = pricing.total_before_tax + pricing.gst_amount
        
        # Set delivery days
        pricing.delivery_days = product.get('delivery_days', 30)
        
        return pricing
    
    def _generate_bid_summary(
        self,
        product_pricings: List[ProductPricing],
        customer_info: Dict[str, Any],
        rfp_details: Dict[str, Any]
    ) -> BidSummary:
        """Generate overall bid summary.
        
        Args:
            product_pricings: List of product pricings
            customer_info: Customer information
            rfp_details: RFP details
            
        Returns:
            BidSummary object
        """
        # Calculate totals
        products_subtotal = sum(p.subtotal for p in product_pricings)
        total_discounts = sum(
            p.volume_discount_amount + p.negotiated_discount_amount
            for p in product_pricings
        )
        testing_costs_total = sum(p.testing_total for p in product_pricings)
        logistics_total = sum(
            p.packaging_cost + p.handling_cost + p.logistics_cost
            for p in product_pricings
        )
        installation_total = sum(p.installation_cost for p in product_pricings)
        
        taxable_amount = sum(p.total_before_tax for p in product_pricings)
        gst_total = sum(p.gst_amount for p in product_pricings)
        grand_total = sum(p.total_after_tax for p in product_pricings)
        
        # Determine pricing tier
        pricing_tier = self.margin_calculator.determine_pricing_tier(
            customer_type=customer_info.get('type', 'standard'),
            order_value=grand_total,
            customer_segment=customer_info.get('segment', 'standard')
        )
        
        # Calculate margin
        cost_base = grand_total  # Simplified - in reality would use actual costs
        margin_percent, margin_amount = self.margin_calculator.calculate_margin(
            cost_base * 0.7,  # Assuming 70% is cost
            pricing_tier
        )
        
        # Profit calculation
        profit_percent = (margin_amount / grand_total) * 100 if grand_total > 0 else 0
        
        # Generate bid ID
        bid_date = datetime.now()
        bid_id = f"BID-{bid_date.strftime('%Y%m%d')}-{rfp_details.get('rfp_id', 'XXX')}"
        
        # Create bid summary
        bid_summary = BidSummary(
            bid_id=bid_id,
            rfp_id=rfp_details.get('rfp_id', 'unknown'),
            rfp_title=rfp_details.get('title', 'Unknown RFP'),
            customer_name=customer_info.get('name', 'Unknown Customer'),
            bid_date=bid_date.strftime('%Y-%m-%d'),
            validity_days=90,
            valid_until=(bid_date + timedelta(days=90)).strftime('%Y-%m-%d'),
            products_subtotal=products_subtotal,
            total_discounts=total_discounts,
            testing_costs_total=testing_costs_total,
            logistics_total=logistics_total,
            installation_total=installation_total,
            taxable_amount=taxable_amount,
            gst_total=gst_total,
            grand_total=grand_total,
            cost_base=cost_base * 0.7,
            margin_percent=margin_percent,
            margin_amount=margin_amount,
            profit_percent=round(profit_percent, 2),
            payment_terms=self._determine_payment_terms(grand_total, customer_info),
            delivery_terms="Ex-Works",
            warranty_period_months=12,
            pricing_tier=pricing_tier.value,
            prepared_by="Enhanced Pricing Agent",
            approved=False
        )
        
        return bid_summary
    
    def _determine_payment_terms(self, order_value: float, customer_info: Dict[str, Any]) -> str:
        """Determine payment terms based on order value and customer."""
        customer_type = customer_info.get('type', 'standard').lower()
        
        if 'government' in customer_type or 'psu' in customer_type:
            return PaymentTerms.LC_90.value
        elif order_value >= 10000000:
            return PaymentTerms.ADVANCE_30.value
        elif order_value >= 5000000:
            return PaymentTerms.ADVANCE_50.value
        elif order_value >= 1000000:
            return PaymentTerms.NET_45.value
        else:
            return PaymentTerms.NET_30.value
    
    def _generate_documents(
        self,
        product_pricings: List[ProductPricing],
        bid_summary: BidSummary
    ) -> Dict[str, Any]:
        """Generate all bid documents.
        
        Args:
            product_pricings: List of product pricings
            bid_summary: Bid summary
            
        Returns:
            Dictionary with all documents
        """
        documents = {
            'pricing_table': self.document_generator.generate_pricing_table(product_pricings).to_dict(),
            'testing_breakdown': self.document_generator.generate_testing_breakdown(product_pricings).to_dict(),
            'summary_table': self.document_generator.generate_summary_table(bid_summary).to_dict(),
            'terms_and_conditions': self.document_generator.generate_terms_and_conditions(bid_summary)
        }
        
        return documents
    
    def _update_statistics(self, bid_summary: BidSummary):
        """Update agent statistics."""
        self.statistics['total_bids_generated'] += 1
        self.statistics['total_value_quoted'] += bid_summary.grand_total
        
        # Update average margin
        total_margin = (
            self.statistics['average_margin_percent'] * (self.statistics['total_bids_generated'] - 1) +
            bid_summary.margin_percent
        )
        self.statistics['average_margin_percent'] = total_margin / self.statistics['total_bids_generated']
        
        self.statistics['total_testing_costs'] += bid_summary.testing_costs_total
    
    def export_bid_documents(
        self,
        pricing_result: Dict[str, Any],
        output_dir: str = './outputs'
    ) -> str:
        """Export bid documents to Excel.
        
        Args:
            pricing_result: Result from process_pricing_request
            output_dir: Output directory
            
        Returns:
            Path to exported file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        bid_id = pricing_result['bid_id']
        
        # Create Excel file
        excel_path = output_path / f"{bid_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Cover sheet
            cover_data = {
                'Field': ['Bid ID', 'RFP ID', 'Customer', 'Bid Date', 'Valid Until', 'Grand Total (₹)', 'Status'],
                'Value': [
                    pricing_result['bid_summary']['bid_id'],
                    pricing_result['bid_summary']['rfp_id'],
                    pricing_result['bid_summary']['customer_name'],
                    pricing_result['bid_summary']['bid_date'],
                    pricing_result['bid_summary']['valid_until'],
                    f"₹{pricing_result['bid_summary']['grand_total']:,.2f}",
                    'DRAFT' if not pricing_result['bid_summary']['approved'] else 'APPROVED'
                ]
            }
            pd.DataFrame(cover_data).to_excel(writer, sheet_name='Cover', index=False)
            
            # Pricing table
            pd.DataFrame(pricing_result['documents']['pricing_table']).to_excel(
                writer,
                sheet_name='Pricing Details',
                index=False
            )
            
            # Testing breakdown
            if pricing_result['documents']['testing_breakdown']:
                pd.DataFrame(pricing_result['documents']['testing_breakdown']).to_excel(
                    writer,
                    sheet_name='Testing Costs',
                    index=False
                )
            
            # Summary
            pd.DataFrame(pricing_result['documents']['summary_table']).to_excel(
                writer,
                sheet_name='Summary',
                index=False
            )
            
            # Terms & Conditions
            terms_df = pd.DataFrame({
                'Terms and Conditions': [pricing_result['documents']['terms_and_conditions']]
            })
            terms_df.to_excel(writer, sheet_name='Terms', index=False)
        
        self.logger.info(f"Bid documents exported to: {excel_path}")
        
        return str(excel_path)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return self.statistics.copy()
