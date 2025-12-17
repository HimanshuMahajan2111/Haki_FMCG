"""
Specification Matcher
Matches RFP requirements with product specifications
"""
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger()


class SpecificationMatcher:
    """Match product specifications against RFP requirements."""
    
    def __init__(self):
        self.weight_exact_match = 1.0
        self.weight_partial_match = 0.5
        self.weight_standards = 0.3
        self.weight_certifications = 0.2
    
    def calculate_match_score(
        self,
        rfp_specs: List[Dict[str, Any]],
        product_specs: Dict[str, Any],
        rfp_standards: List[str],
        product_certs: List[str]
    ) -> float:
        """
        Calculate match score between RFP and product.
        Returns score between 0.0 and 1.0
        """
        if not rfp_specs:
            return 0.0
        
        total_score = 0.0
        max_score = 0.0
        
        # Score specification matches
        for rfp_spec in rfp_specs:
            param = rfp_spec.get("parameter", "").lower()
            rfp_value = str(rfp_spec.get("value", "")).lower()
            is_mandatory = rfp_spec.get("requirement_type") == "mandatory"
            
            weight = self.weight_exact_match if is_mandatory else self.weight_partial_match
            max_score += weight
            
            # Check if product has this parameter
            product_value = None
            for key, value in product_specs.items():
                if param in key.lower() or key.lower() in param:
                    product_value = str(value).lower()
                    break
            
            if product_value:
                if product_value == rfp_value:
                    # Exact match
                    total_score += weight
                elif rfp_value in product_value or product_value in rfp_value:
                    # Partial match
                    total_score += weight * 0.7
                elif self._are_values_compatible(rfp_value, product_value):
                    # Compatible values (e.g., numeric ranges)
                    total_score += weight * 0.5
        
        # Score standards compliance
        if rfp_standards:
            max_score += self.weight_standards
            matching_standards = sum(
                1 for std in rfp_standards
                if any(std.lower() in cert.lower() for cert in product_certs)
            )
            if matching_standards > 0:
                total_score += self.weight_standards * (matching_standards / len(rfp_standards))
        
        # Score certifications
        if product_certs and rfp_standards:
            max_score += self.weight_certifications
            if any(cert for cert in product_certs if cert.strip()):
                total_score += self.weight_certifications * 0.8
        
        return total_score / max_score if max_score > 0 else 0.0
    
    def _are_values_compatible(self, rfp_value: str, product_value: str) -> bool:
        """Check if two values are compatible (numeric comparisons, etc.)."""
        try:
            # Try numeric comparison
            rfp_num = float(''.join(c for c in rfp_value if c.isdigit() or c == '.'))
            prod_num = float(''.join(c for c in product_value if c.isdigit() or c == '.'))
            
            # Product value should meet or exceed requirement
            return prod_num >= rfp_num * 0.9  # Allow 10% tolerance
        except:
            return False
    
    def get_detailed_match_report(
        self,
        rfp_specs: List[Dict[str, Any]],
        product_specs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get detailed match report for debugging/display."""
        matches = []
        mismatches = []
        
        for rfp_spec in rfp_specs:
            param = rfp_spec.get("parameter", "")
            rfp_value = rfp_spec.get("value", "")
            
            product_value = product_specs.get(param)
            
            if product_value and str(product_value).lower() == str(rfp_value).lower():
                matches.append({"parameter": param, "rfp": rfp_value, "product": product_value})
            else:
                mismatches.append({"parameter": param, "rfp": rfp_value, "product": product_value or "N/A"})
        
        return {
            "total_specs": len(rfp_specs),
            "matches": len(matches),
            "mismatches": len(mismatches),
            "match_percentage": (len(matches) / len(rfp_specs) * 100) if rfp_specs else 0,
            "detailed_matches": matches,
            "detailed_mismatches": mismatches
        }
