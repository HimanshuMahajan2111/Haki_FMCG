"""
Test Cost Calculator - Calculates costs for testing and certifications.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from decimal import Decimal
import structlog

from pricing.base_calculator import PriceCalculator

logger = structlog.get_logger()


@dataclass
class TestCost:
    """Testing cost breakdown."""
    test_type: str
    test_name: str
    cost: Decimal
    
    # Details
    laboratory: Optional[str] = None
    duration_days: Optional[int] = None
    standard: Optional[str] = None
    is_mandatory: bool = True
    
    # Additional costs
    sample_preparation_cost: Decimal = Decimal('0')
    documentation_cost: Decimal = Decimal('0')
    rush_fee: Decimal = Decimal('0')
    
    def total_cost(self) -> Decimal:
        """Calculate total test cost."""
        return (
            self.cost +
            self.sample_preparation_cost +
            self.documentation_cost +
            self.rush_fee
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'test_type': self.test_type,
            'test_name': self.test_name,
            'cost': float(self.cost),
            'laboratory': self.laboratory,
            'duration_days': self.duration_days,
            'standard': self.standard,
            'is_mandatory': self.is_mandatory,
            'sample_preparation_cost': float(self.sample_preparation_cost),
            'documentation_cost': float(self.documentation_cost),
            'rush_fee': float(self.rush_fee),
            'total_cost': float(self.total_cost())
        }


class TestCostCalculator(PriceCalculator):
    """Calculate testing and certification costs."""
    
    def __init__(self):
        """Initialize test cost calculator."""
        super().__init__()
        self.logger = logger.bind(component="TestCostCalculator")
        
        # Default test costs (in INR)
        self.test_costs = {
            # Type tests
            'type_test_electrical': Decimal('25000'),
            'type_test_mechanical': Decimal('20000'),
            'type_test_thermal': Decimal('15000'),
            
            # Routine tests
            'routine_test_electrical': Decimal('5000'),
            'routine_test_mechanical': Decimal('4000'),
            
            # Performance tests
            'performance_test_standard': Decimal('10000'),
            'performance_test_extended': Decimal('18000'),
            
            # Certifications
            'ce_certification': Decimal('50000'),
            'ul_certification': Decimal('75000'),
            'isi_certification': Decimal('40000'),
            'rohs_certification': Decimal('30000'),
            'iso_certification': Decimal('60000'),
            
            # Inspections
            'factory_acceptance_test': Decimal('15000'),
            'site_acceptance_test': Decimal('20000'),
            'third_party_inspection': Decimal('25000'),
            
            # Sample testing
            'sample_test_basic': Decimal('8000'),
            'sample_test_comprehensive': Decimal('15000'),
        }
        
        # Laboratory rates
        self.laboratory_rates = {
            'nabl_accredited': Decimal('1.2'),  # 20% premium
            'government_lab': Decimal('1.0'),
            'private_lab': Decimal('1.15'),
            'international_lab': Decimal('1.5')
        }
    
    def calculate(
        self,
        test_type: str,
        quantity: int = 1,
        laboratory_type: str = 'government_lab',
        rush_service: bool = False
    ) -> Decimal:
        """Calculate test cost.
        
        Args:
            test_type: Type of test
            quantity: Number of samples
            laboratory_type: Type of laboratory
            rush_service: Whether rush service is needed
            
        Returns:
            Total test cost
        """
        # Get base test cost
        base_cost = self.test_costs.get(test_type, Decimal('10000'))
        
        # Apply laboratory rate multiplier
        lab_multiplier = self.laboratory_rates.get(laboratory_type, Decimal('1.0'))
        test_cost = base_cost * lab_multiplier
        
        # Multiply by quantity
        total_cost = test_cost * Decimal(quantity)
        
        # Add rush fee (50% extra)
        if rush_service:
            rush_fee = total_cost * Decimal('0.5')
            total_cost += rush_fee
            self.logger.debug("Rush service fee applied", fee=float(rush_fee))
        
        self.logger.info(
            "Test cost calculated",
            test_type=test_type,
            quantity=quantity,
            laboratory=laboratory_type,
            total=float(total_cost)
        )
        
        return self.round_price(total_cost)
    
    def calculate_testing_requirements(
        self,
        requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate costs for multiple testing requirements.
        
        Args:
            requirements: List of test requirement dicts with:
                - test_type: Type of test
                - quantity: Number of samples (default: 1)
                - laboratory_type: Lab type (optional)
                - is_mandatory: Whether test is mandatory (default: True)
                - rush_service: Rush service needed (default: False)
            
        Returns:
            Dictionary with total cost and breakdown
        """
        total_cost = Decimal('0')
        mandatory_cost = Decimal('0')
        optional_cost = Decimal('0')
        test_breakdown = []
        
        for req in requirements:
            test_type = req.get('test_type')
            quantity = req.get('quantity', 1)
            laboratory_type = req.get('laboratory_type', 'government_lab')
            is_mandatory = req.get('is_mandatory', True)
            rush_service = req.get('rush_service', False)
            
            try:
                cost = self.calculate(
                    test_type,
                    quantity=quantity,
                    laboratory_type=laboratory_type,
                    rush_service=rush_service
                )
                
                test_cost = TestCost(
                    test_type='test',
                    test_name=test_type,
                    cost=cost,
                    laboratory=laboratory_type,
                    is_mandatory=is_mandatory,
                    rush_fee=cost * Decimal('0.5') if rush_service else Decimal('0')
                )
                
                test_breakdown.append(test_cost.to_dict())
                total_cost += cost
                
                if is_mandatory:
                    mandatory_cost += cost
                else:
                    optional_cost += cost
                
            except Exception as e:
                self.logger.error(
                    "Failed to calculate test cost",
                    test_type=test_type,
                    error=str(e)
                )
        
        return {
            'total_cost': float(total_cost),
            'mandatory_cost': float(mandatory_cost),
            'optional_cost': float(optional_cost),
            'test_count': len(test_breakdown),
            'tests': test_breakdown
        }
    
    def estimate_certification_cost(
        self,
        certifications: List[str]
    ) -> Dict[str, Any]:
        """Estimate total certification costs.
        
        Args:
            certifications: List of certification names
            
        Returns:
            Dictionary with cost breakdown
        """
        total_cost = Decimal('0')
        cert_breakdown = []
        
        # Map certification names to test types
        cert_mapping = {
            'CE': 'ce_certification',
            'UL': 'ul_certification',
            'ISI': 'isi_certification',
            'RoHS': 'rohs_certification',
            'ISO': 'iso_certification'
        }
        
        for cert in certifications:
            # Try to find matching test type
            test_type = None
            for key, value in cert_mapping.items():
                if key.lower() in cert.lower():
                    test_type = value
                    break
            
            if test_type:
                cost = self.test_costs.get(test_type, Decimal('40000'))
                total_cost += cost
                
                cert_breakdown.append({
                    'certification': cert,
                    'cost': float(cost)
                })
            else:
                # Default cost for unknown certifications
                default_cost = Decimal('40000')
                total_cost += default_cost
                
                cert_breakdown.append({
                    'certification': cert,
                    'cost': float(default_cost),
                    'note': 'Estimated cost'
                })
        
        return {
            'total_cost': float(total_cost),
            'certification_count': len(cert_breakdown),
            'certifications': cert_breakdown
        }
    
    def calculate_rfp_testing_costs(
        self,
        rfp_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate testing costs from RFP requirements.
        
        Args:
            rfp_requirements: RFP testing requirements from TestingRequirementExtractor
            
        Returns:
            Complete testing cost breakdown
        """
        total_cost = Decimal('0')
        breakdown = {
            'tests': [],
            'certifications': [],
            'standards': []
        }
        
        # Calculate test costs
        if 'testing_requirements' in rfp_requirements:
            test_reqs = []
            for req in rfp_requirements['testing_requirements']:
                test_type = self._map_requirement_to_test_type(req.get('name', ''))
                test_reqs.append({
                    'test_type': test_type,
                    'quantity': 1,
                    'is_mandatory': req.get('is_mandatory', True)
                })
            
            test_costs = self.calculate_testing_requirements(test_reqs)
            breakdown['tests'] = test_costs['tests']
            total_cost += Decimal(str(test_costs['total_cost']))
        
        # Calculate certification costs
        if 'certifications' in rfp_requirements:
            cert_costs = self.estimate_certification_cost(
                rfp_requirements['certifications']
            )
            breakdown['certifications'] = cert_costs['certifications']
            total_cost += Decimal(str(cert_costs['total_cost']))
        
        # Standards typically don't have direct costs, but note them
        if 'standards' in rfp_requirements:
            breakdown['standards'] = rfp_requirements['standards']
        
        return {
            'total_testing_cost': float(total_cost),
            'breakdown': breakdown,
            'summary': {
                'test_count': len(breakdown['tests']),
                'certification_count': len(breakdown['certifications']),
                'standard_count': len(breakdown['standards'])
            }
        }
    
    def _map_requirement_to_test_type(self, requirement_name: str) -> str:
        """Map requirement name to test type.
        
        Args:
            requirement_name: Name of requirement
            
        Returns:
            Test type key
        """
        name_lower = requirement_name.lower()
        
        if 'type test' in name_lower:
            return 'type_test_electrical'
        elif 'routine test' in name_lower:
            return 'routine_test_electrical'
        elif 'performance' in name_lower:
            return 'performance_test_standard'
        elif 'fat' in name_lower or 'factory acceptance' in name_lower:
            return 'factory_acceptance_test'
        elif 'sat' in name_lower or 'site acceptance' in name_lower:
            return 'site_acceptance_test'
        elif 'sample' in name_lower:
            return 'sample_test_basic'
        else:
            return 'routine_test_electrical'  # Default
