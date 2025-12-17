"""
Pricing Agent Worker - Comprehensive pricing calculation.

Responsibilities:
1. Receives test summary from Main Agent
2. Receives product recommendations from Technical Agent
3. Assigns unit prices using dummy pricing table
4. Assigns test prices using dummy services pricing table
5. Consolidates total material + services costs
6. Sends price breakdown to Main Agent
"""
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import structlog

logger = structlog.get_logger()


@dataclass
class MaterialLineItem:
    """Material line item with pricing."""
    item_number: str
    item_name: str
    manufacturer: str
    model_number: str
    quantity: int
    unit: str
    unit_price: float
    line_total: float
    discount_percent: float = 0.0
    net_price: float = 0.0


@dataclass
class TestLineItem:
    """Test/service line item with pricing."""
    test_name: str
    test_type: str  # 'routine', 'type', 'acceptance'
    description: str
    quantity: int
    unit_price: float
    total_cost: float


@dataclass
class PricingBreakdown:
    """Complete pricing breakdown."""
    # Material costs
    material_line_items: List[MaterialLineItem] = field(default_factory=list)
    material_subtotal: float = 0.0
    material_discount: float = 0.0
    material_net: float = 0.0
    
    # Testing costs
    test_line_items: List[TestLineItem] = field(default_factory=list)
    routine_test_cost: float = 0.0
    type_test_cost: float = 0.0
    acceptance_test_cost: float = 0.0
    total_testing_cost: float = 0.0
    
    # Totals
    subtotal_before_tax: float = 0.0
    gst_percent: float = 18.0
    gst_amount: float = 0.0
    grand_total: float = 0.0
    
    # Payment terms
    payment_terms: str = ""
    delivery_weeks: int = 0


class DummyPricingTable:
    """Dummy pricing table for products and services."""
    
    # Product pricing by category ( per unit)
    PRODUCT_PRICES = {
        'Solar Cables': {
            'default': 2500,
            'Havells': 2800,
            'Polycab': 2700,
            'KEI': 2600,
            'Finolex': 2400
        },
        'Power Cables': {
            'default': 3500,
            'Havells': 3800,
            'Polycab': 3900,
            'KEI': 3700,
            'RR Kabel': 3600
        },
        'Signaling Cables': {
            'default': 1800,
            'Havells': 2000,
            'Polycab': 1950,
            'KEI': 1900
        },
        'Telecom Cables': {
            'default': 2200,
            'Havells': 2500,
            'Polycab': 2400
        },
        'Electrical Products': {
            'default': 5000,
            'Havells': 5500,
            'Polycab': 5300
        }
    }
    
    # Test pricing ( per test)
    TEST_PRICES = {
        'routine': {
            'per_product': 5000,
            'description': 'Routine tests as per IS standards'
        },
        'type': {
            'per_product_type': 25000,
            'description': 'Type tests at NABL accredited lab'
        },
        'acceptance': {
            'per_site': 15000,
            'description': 'Acceptance tests at buyer site'
        },
        'dielectric': {
            'per_sample': 3000,
            'description': 'Dielectric withstand test'
        },
        'insulation_resistance': {
            'per_sample': 2500,
            'description': 'Insulation resistance test'
        },
        'conductor_resistance': {
            'per_sample': 2000,
            'description': 'Conductor resistance test'
        },
        'tensile_strength': {
            'per_sample': 4000,
            'description': 'Tensile strength and elongation test'
        },
        'thermal_aging': {
            'per_sample': 8000,
            'description': 'Thermal aging test'
        },
        'flame_retardant': {
            'per_sample': 6000,
            'description': 'Flame retardant test'
        }
    }
    
    # Discount tiers based on order value
    DISCOUNT_TIERS = [
        {'min_value': 10000000, 'discount_percent': 12.0},  # 1 Cr
        {'min_value': 5000000, 'discount_percent': 8.0},    # 50 L
        {'min_value': 1000000, 'discount_percent': 5.0},    # 10 L
        {'min_value': 500000, 'discount_percent': 3.0},     # 5 L
        {'min_value': 0, 'discount_percent': 0.0}           # Default
    ]
    
    @classmethod
    def get_product_price(cls, category: str, manufacturer: str) -> float:
        """Get product unit price."""
        category_prices = cls.PRODUCT_PRICES.get(category, cls.PRODUCT_PRICES['Electrical Products'])
        return category_prices.get(manufacturer, category_prices['default'])
    
    @classmethod
    def get_test_price(cls, test_type: str) -> Dict[str, Any]:
        """Get test pricing info."""
        return cls.TEST_PRICES.get(test_type, {
            'per_sample': 5000,
            'description': f'{test_type} test'
        })
    
    @classmethod
    def get_discount_percent(cls, order_value: float) -> float:
        """Get discount percentage based on order value."""
        for tier in cls.DISCOUNT_TIERS:
            if order_value >= tier['min_value']:
                return tier['discount_percent']
        return 0.0


class PricingAgentWorker:
    """
    Pricing Agent - Comprehensive pricing calculation.
    
    Workflow:
    1. Receive test summary from Main Agent
    2. Receive product recommendations from Technical Agent
    3. Calculate material costs (products)
    4. Calculate testing costs (services)
    5. Apply discounts based on order value
    6. Calculate GST (18%)
    7. Send consolidated pricing to Main Agent
    """
    
    def __init__(self):
        """Initialize Pricing Agent Worker."""
        self.logger = logger.bind(component="PricingAgentWorker")
        self.pricing_table = DummyPricingTable()
    
    async def calculate_comprehensive_pricing(
        self,
        pricing_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate comprehensive pricing for RFP.
        
        Args:
            pricing_input: Data from Master Agent and Technical Agent containing:
                - rfp_id: RFP identifier
                - tests_required: List of tests from RFP
                - selected_products: Product recommendations from Technical Agent
                - test_summary: Test summary from Master Agent
                - quantity_info: Quantity details
                - payment_terms: Payment terms from RFP
        
        Returns:
            Complete pricing breakdown
        """
        rfp_id = pricing_input['rfp_id']
        
        self.logger.info(
            " Step 1: Receiving test summary from Master Agent",
            rfp_id=rfp_id
        )
        
        self.logger.info(
            " Step 2: Receiving product recommendations from Technical Agent",
            product_count=len(pricing_input.get('selected_products', []))
        )
        
        # Initialize pricing breakdown
        breakdown = PricingBreakdown()
        
        # Step 3: Calculate material costs
        self.logger.info(" Step 3: Calculating material costs")
        material_items, material_subtotal = self._calculate_material_costs(
            pricing_input.get('selected_products', [])
        )
        breakdown.material_line_items = material_items
        breakdown.material_subtotal = material_subtotal
        
        # Apply discount
        discount_percent = self.pricing_table.get_discount_percent(material_subtotal)
        breakdown.material_discount = material_subtotal * (discount_percent / 100)
        breakdown.material_net = material_subtotal - breakdown.material_discount
        
        self.logger.info(
            f" Material subtotal: {material_subtotal:,.2f}, "
            f"Discount: {discount_percent}%, "
            f"Net: {breakdown.material_net:,.2f}"
        )
        
        # Step 4: Calculate testing costs
        self.logger.info(" Step 4: Calculating testing costs")
        test_items, testing_total = self._calculate_testing_costs(
            pricing_input.get('tests_required', []),
            pricing_input.get('test_summary', {}),
            pricing_input.get('selected_products', [])
        )
        breakdown.test_line_items = test_items
        breakdown.total_testing_cost = testing_total
        
        # Break down test costs by type
        breakdown.routine_test_cost = sum(
            t.total_cost for t in test_items if t.test_type == 'routine'
        )
        breakdown.type_test_cost = sum(
            t.total_cost for t in test_items if t.test_type == 'type'
        )
        breakdown.acceptance_test_cost = sum(
            t.total_cost for t in test_items if t.test_type == 'acceptance'
        )
        
        self.logger.info(
            f" Testing costs - Routine: {breakdown.routine_test_cost:,.2f}, "
            f"Type: {breakdown.type_test_cost:,.2f}, "
            f"Acceptance: {breakdown.acceptance_test_cost:,.2f}"
        )
        
        # Step 5: Calculate totals
        self.logger.info(" Step 5: Consolidating total costs")
        breakdown.subtotal_before_tax = breakdown.material_net + breakdown.total_testing_cost
        breakdown.gst_amount = breakdown.subtotal_before_tax * (breakdown.gst_percent / 100)
        breakdown.grand_total = breakdown.subtotal_before_tax + breakdown.gst_amount
        
        # Payment terms
        breakdown.payment_terms = pricing_input.get('payment_terms', 
            self._determine_payment_terms(breakdown.grand_total))
        breakdown.delivery_weeks = self._estimate_delivery(
            pricing_input.get('selected_products', [])
        )
        
        self.logger.info(
            " Pricing calculation complete",
            material_cost=f"{breakdown.material_net:,.2f}",
            testing_cost=f"{breakdown.total_testing_cost:,.2f}",
            gst=f"{breakdown.gst_amount:,.2f}",
            grand_total=f"{breakdown.grand_total:,.2f}"
        )
        
        # Step 6: Prepare response for Main Agent
        response = {
            'rfp_id': rfp_id,
            'pricing_breakdown': self._breakdown_to_dict(breakdown),
            'summary': {
                'material_cost': breakdown.material_net,
                'testing_cost': breakdown.total_testing_cost,
                'subtotal': breakdown.subtotal_before_tax,
                'gst': breakdown.gst_amount,
                'grand_total': breakdown.grand_total
            },
            'payment_terms': breakdown.payment_terms,
            'delivery_weeks': breakdown.delivery_weeks,
            'processed_at': datetime.now().isoformat()
        }
        
        return response
    
    def _calculate_material_costs(
        self,
        selected_products: List[Dict[str, Any]]
    ) -> tuple[List[MaterialLineItem], float]:
        """Calculate material line item costs.
        
        Args:
            selected_products: Selected products from Technical Agent
            
        Returns:
            Tuple of (line_items, subtotal)
        """
        line_items = []
        subtotal = 0.0
        
        for product in selected_products:
            # Get price from dummy table or use existing
            if 'unit_price' in product and product['unit_price'] > 0:
                unit_price = product['unit_price']
            else:
                # Fallback to pricing table
                category = self._determine_category(product['item_name'])
                manufacturer = product.get('manufacturer', 'default')
                unit_price = self.pricing_table.get_product_price(category, manufacturer)
            
            quantity = product.get('quantity', 1)
            line_total = unit_price * quantity
            
            line_item = MaterialLineItem(
                item_number=product.get('item_number', 'ITEM-001'),
                item_name=product.get('item_name', 'Product'),
                manufacturer=product.get('manufacturer', 'OEM'),
                model_number=product.get('model_number', 'MODEL-XXX'),
                quantity=quantity,
                unit=product.get('unit', 'nos'),
                unit_price=unit_price,
                line_total=line_total,
                net_price=line_total  # Will apply discount later
            )
            
            line_items.append(line_item)
            subtotal += line_total
        
        return line_items, subtotal
    
    def _calculate_testing_costs(
        self,
        tests_required: List[str],
        test_summary: Dict[str, Any],
        selected_products: List[Dict[str, Any]]
    ) -> tuple[List[TestLineItem], float]:
        """Calculate testing/service costs.
        
        Args:
            tests_required: List of required tests
            test_summary: Test summary from Master Agent
            selected_products: Products being tested
            
        Returns:
            Tuple of (test_items, total_cost)
        """
        test_items = []
        total_cost = 0.0
        
        # Extract test requirements
        routine_tests = test_summary.get('routine_tests', [])
        type_tests = test_summary.get('type_tests', [])
        acceptance_tests = test_summary.get('acceptance_tests', [])
        
        product_count = len(selected_products)
        
        # Routine tests (per product)
        if routine_tests:
            test_price = self.pricing_table.TEST_PRICES['routine']
            quantity = product_count
            cost = test_price['per_product'] * quantity
            
            test_items.append(TestLineItem(
                test_name='Routine Tests',
                test_type='routine',
                description=test_price['description'],
                quantity=quantity,
                unit_price=test_price['per_product'],
                total_cost=cost
            ))
            total_cost += cost
        
        # Type tests (per product type)
        if type_tests:
            test_price = self.pricing_table.TEST_PRICES['type']
            # Assume 1 type test per unique product type
            unique_types = len(set(p.get('manufacturer', '') for p in selected_products))
            quantity = max(unique_types, 1)
            cost = test_price['per_product_type'] * quantity
            
            test_items.append(TestLineItem(
                test_name='Type Tests',
                test_type='type',
                description=test_price['description'],
                quantity=quantity,
                unit_price=test_price['per_product_type'],
                total_cost=cost
            ))
            total_cost += cost
        
        # Acceptance tests (per site)
        if acceptance_tests:
            test_price = self.pricing_table.TEST_PRICES['acceptance']
            quantity = 1  # Usually 1 site
            cost = test_price['per_site'] * quantity
            
            test_items.append(TestLineItem(
                test_name='Acceptance Tests',
                test_type='acceptance',
                description=test_price['description'],
                quantity=quantity,
                unit_price=test_price['per_site'],
                total_cost=cost
            ))
            total_cost += cost
        
        # Additional specific tests from test summary
        for test_item in tests_required:
            # Handle both string and dict formats
            if isinstance(test_item, str):
                test_name = test_item
            elif isinstance(test_item, dict):
                test_name = test_item.get('test_name', test_item.get('name', 'Unknown Test'))
            else:
                continue
                
            test_key = test_name.lower().replace(' ', '_').replace('-', '_')
            if test_key in self.pricing_table.TEST_PRICES:
                test_price = self.pricing_table.TEST_PRICES[test_key]
                quantity = product_count
                unit_price = test_price.get('per_sample', 5000)
                cost = unit_price * quantity
                
                test_items.append(TestLineItem(
                    test_name=test_name,
                    test_type='specific',
                    description=test_price.get('description', test_name),
                    quantity=quantity,
                    unit_price=unit_price,
                    total_cost=cost
                ))
                total_cost += cost
        
        return test_items, total_cost
    
    def _determine_category(self, item_name: str) -> str:
        """Determine product category from item name."""
        item_lower = item_name.lower()
        
        if 'solar' in item_lower:
            return 'Solar Cables'
        elif 'power' in item_lower:
            return 'Power Cables'
        elif 'signal' in item_lower:
            return 'Signaling Cables'
        elif 'telecom' in item_lower:
            return 'Telecom Cables'
        else:
            return 'Electrical Products'
    
    def _determine_payment_terms(self, grand_total: float) -> str:
        """Determine payment terms based on order value."""
        if grand_total >= 10000000:  # 1 Cr
            return "30% advance, 60% on delivery, 10% after installation"
        elif grand_total >= 5000000:  # 50 L
            return "20% advance, 70% on delivery, 10% after installation"
        else:
            return "10% advance, 80% on delivery, 10% after installation"
    
    def _estimate_delivery(self, selected_products: List[Dict[str, Any]]) -> int:
        """Estimate delivery time in weeks."""
        if not selected_products:
            return 8
        
        max_delivery_days = max(
            p.get('delivery_days', 30) for p in selected_products
        )
        
        # Convert days to weeks (round up)
        weeks = (max_delivery_days + 6) // 7
        return weeks
    
    def _breakdown_to_dict(self, breakdown: PricingBreakdown) -> Dict[str, Any]:
        """Convert PricingBreakdown to dictionary."""
        return {
            'material_line_items': [vars(item) for item in breakdown.material_line_items],
            'material_subtotal': breakdown.material_subtotal,
            'material_discount': breakdown.material_discount,
            'material_net': breakdown.material_net,
            'test_line_items': [vars(item) for item in breakdown.test_line_items],
            'routine_test_cost': breakdown.routine_test_cost,
            'type_test_cost': breakdown.type_test_cost,
            'acceptance_test_cost': breakdown.acceptance_test_cost,
            'total_testing_cost': breakdown.total_testing_cost,
            'subtotal_before_tax': breakdown.subtotal_before_tax,
            'gst_percent': breakdown.gst_percent,
            'gst_amount': breakdown.gst_amount,
            'grand_total': breakdown.grand_total,
            'payment_terms': breakdown.payment_terms,
            'delivery_weeks': breakdown.delivery_weeks
        }

