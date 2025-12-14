"""Standards compliance checker."""
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger()


class StandardsChecker:
    """Check product compliance with standards."""
    
    def __init__(self):
        """Initialize standards checker."""
        self.logger = logger.bind(component="StandardsChecker")
        self.standards_map = self._load_standards_map()
    
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
            passed = self._check_standard(required_std, product_standards)
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
    
    def _check_standard(
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
        
        # Check equivalents
        equivalents = self.standards_map.get(required, [])
        for std in product_standards:
            if std in equivalents:
                return True
        
        return False
    
    def _load_standards_map(self) -> Dict[str, List[str]]:
        """Load standards equivalency map.
        
        Returns:
            Standards mapping
        """
        # TODO: Load from standards CSV files
        # For now, return basic mappings
        return {
            "IS 694": ["IEC 60227", "BS 6004"],
            "IS 1554": ["IEC 60227"],
            "IS 7098": ["IEC 60502"],
            "IEC 60227": ["IS 694", "IS 1554"],
            "IEC 60502": ["IS 7098"],
        }
