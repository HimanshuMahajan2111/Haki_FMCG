"""Standards compliance checker."""
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger()


class StandardsChecker:
    """Check product compliance with standards."""
    
    def __init__(self):
        """Initialize standards checker."""
        self.data_service = None
        self.logger = logger.bind(component="StandardsChecker")
        self.standards_map = None
    
    def _get_data_service(self):
        """Lazy load data service to avoid circular imports."""
        if self.data_service is None:
            from services.data_service import get_data_service
            self.data_service = get_data_service()
    
    async def check_compliance(
        self,
        product: Dict[str, Any],
        required_standards: List[str]
    ) -> Dict[str, Any]:
        """Check if product meets required standards.
        
        Args:
            product: Product dictionary
            required_standards: List of required standards
            
        Returns:
            Compliance result
        """
        product_standards = self._extract_standards(product)
        
        checks = []
        for required_std in required_standards:
            passed = await self._check_standard(required_std, product_standards)
            checks.append({
                "standard": required_std,
                "passed": passed,
                "product_standards": product_standards,
            })
        
        passed_count = sum(1 for c in checks if c["passed"])
        total_count = len(checks)
        
        return {
            "checks": checks,
            "passed_checks": passed_count,
            "total_checks": total_count,
            "overall_score": (passed_count / total_count * 100) if total_count > 0 else 0,
            "compliant": passed_count == total_count,
        }
    
    def _extract_standards(self, product: Dict[str, Any]) -> List[str]:
        """Extract standards from product.
        
        Args:
            product: Product dictionary
            
        Returns:
            List of standards
        """
        standards = []
        
        # Check standard field
        if product.get("standard"):
            standards.append(product["standard"])
        
        # Check specifications
        specs = product.get("specifications", {})
        if "standard" in specs:
            standards.append(specs["standard"])
        
        return standards
    
    async def _check_standard(
        self,
        required: str,
        product_standards: List[str]
    ) -> bool:
        """Check if required standard is met.
        
        Args:
            required: Required standard
            product_standards: Product's standards
            
        Returns:
            True if compliant
        """
        # Exact match
        if required in product_standards:
            return True
        
        # Load standards map if not already loaded
        standards_map = await self._load_standards_map()
        
        # Check equivalents
        equivalents = standards_map.get(required, [])
        for std in product_standards:
            if std in equivalents:
                return True
        
        return False
    
    async def _load_standards_map(self) -> Dict[str, List[str]]:
        """Load standards equivalency map from data service.
        
        Returns:
            Standards mapping
        """
        if self.standards_map is not None:
            return self.standards_map
        
        self._get_data_service()  # Lazy load service
        
        # Load standards data
        standards_data = await self.data_service.get_standards_data()
        comparisons = standards_data.get("comparisons", [])
        
        # Build equivalency map
        standards_map = {}
        
        for comparison in comparisons:
            indian_std = comparison.get("indian_standard") or comparison.get("standard_code")
            international_eq = comparison.get("international_equivalent")
            
            if indian_std and international_eq:
                # Add both directions
                if indian_std not in standards_map:
                    standards_map[indian_std] = []
                standards_map[indian_std].append(international_eq)
                
                if international_eq not in standards_map:
                    standards_map[international_eq] = []
                standards_map[international_eq].append(indian_std)
        
        # Add default mappings if not found
        if not standards_map:
            standards_map = {
                "IS 694": ["IEC 60227", "BS 6004"],
                "IS 1554": ["IEC 60227"],
                "IS 7098": ["IEC 60502"],
                "IEC 60227": ["IS 694", "IS 1554"],
                "IEC 60502": ["IS 7098"],
            }
        
        self.standards_map = standards_map
        self.logger.info("Standards map loaded", total_standards=len(standards_map))
        
        return standards_map
