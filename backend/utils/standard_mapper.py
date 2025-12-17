"""Standard mapping utilities for electrical and industrial standards."""
from typing import Dict, List, Optional, Set, Any
import re
import structlog

logger = structlog.get_logger()


class StandardMapper:
    """Map and compare electrical and industrial standards."""
    
    def __init__(self):
        """Initialize standard mapper."""
        self.logger = logger.bind(component="StandardMapper")
        
        # Indian Standards (IS) to IEC mappings
        self.is_to_iec_map = {
            'IS 694': ['IEC 60227'],
            'IS 1554': ['IEC 60502'],
            'IS 5578': ['IEC 60227-3'],
            'IS 8130': ['IEC 60227-5'],
            'IS 9968': ['IEC 60502-1'],
            'IS 10810': ['IEC 60331'],
            'IS 13573': ['IEC 60332-1', 'IEC 60332-3'],
            'IS 14494': ['IEC 60092-350'],
            'IS 15652': ['IEC 60269'],
            'IS 15368': ['IEC 61439-1', 'IEC 61439-2'],
            'IS/IEC 60898': ['IEC 60898'],
            'IS/IEC 60947': ['IEC 60947'],
            'IS 302': ['IEC 60227', 'IEC 60245'],
            'IS 732': ['IEC 60092-353'],
            'IS 1885': ['IEC 60502-2'],
            'IS 3961': ['IEC 60245-4'],
            'IS 7098': ['IEC 60364'],
            'IS 3043': ['IEC 60309'],
        }
        
        # Reverse mapping (IEC to IS)
        self.iec_to_is_map = {}
        for is_std, iec_list in self.is_to_iec_map.items():
            for iec_std in iec_list:
                if iec_std not in self.iec_to_is_map:
                    self.iec_to_is_map[iec_std] = []
                self.iec_to_is_map[iec_std].append(is_std)
        
        # Standard categories
        self.standard_categories = {
            'cables_low_voltage': [
                'IS 694', 'IS 1554', 'IS 5578', 'IS 8130', 'IS 302',
                'IEC 60227', 'IEC 60502', 'IEC 60245'
            ],
            'cables_medium_voltage': [
                'IS 1554', 'IS 9968', 'IS 1885',
                'IEC 60502-1', 'IEC 60502-2'
            ],
            'cables_high_voltage': [
                'IS 7098', 'IEC 60840', 'IEC 62067'
            ],
            'fire_resistance': [
                'IS 10810', 'IS 13573',
                'IEC 60331', 'IEC 60332-1', 'IEC 60332-3'
            ],
            'switchgear': [
                'IS 15368', 'IS/IEC 60947',
                'IEC 61439-1', 'IEC 61439-2', 'IEC 60947'
            ],
            'circuit_breakers': [
                'IS/IEC 60898', 'IS 15652',
                'IEC 60898', 'IEC 60269'
            ],
            'plugs_sockets': [
                'IS 3043', 'IEC 60309'
            ],
            'marine_cables': [
                'IS 732', 'IS 14494',
                'IEC 60092-350', 'IEC 60092-353'
            ],
            'installation': [
                'IS 732', 'IEC 60364'
            ],
        }
        
        # Standard aliases and variations
        self.standard_aliases = {
            'IS694': 'IS 694',
            'IS-694': 'IS 694',
            'IS 694-2010': 'IS 694',
            'IEC60227': 'IEC 60227',
            'IEC-60227': 'IEC 60227',
            'IEC 60227-1': 'IEC 60227',
            'BS6004': 'BS 6004',
            'BS-6004': 'BS 6004',
        }
    
    def normalize_standard(self, standard: str) -> str:
        """Normalize standard notation.
        
        Args:
            standard: Standard string (e.g., "IS694", "IEC-60227")
            
        Returns:
            Normalized standard notation
        """
        if not standard:
            return ''
        
        # Clean up
        standard = standard.strip().upper()
        
        # Check aliases
        if standard in self.standard_aliases:
            return self.standard_aliases[standard]
        
        # Try to parse and normalize
        # Pattern: IS/IEC followed by optional separator and number
        match = re.match(r'(IS|IEC|BS|EN)\s*[-/]?\s*(\d+)', standard, re.IGNORECASE)
        if match:
            prefix = match.group(1).upper()
            number = match.group(2)
            return f"{prefix} {number}"
        
        return standard
    
    def find_equivalent_standards(
        self,
        standard: str,
        direction: str = 'both'
    ) -> List[str]:
        """Find equivalent standards.
        
        Args:
            standard: Standard to find equivalents for
            direction: 'is_to_iec', 'iec_to_is', or 'both'
            
        Returns:
            List of equivalent standards
        """
        standard = self.normalize_standard(standard)
        equivalents = []
        
        if direction in ['is_to_iec', 'both']:
            if standard in self.is_to_iec_map:
                equivalents.extend(self.is_to_iec_map[standard])
        
        if direction in ['iec_to_is', 'both']:
            if standard in self.iec_to_is_map:
                equivalents.extend(self.iec_to_is_map[standard])
        
        return list(set(equivalents))  # Remove duplicates
    
    def check_standard_match(
        self,
        required: str,
        available: List[str],
        allow_equivalents: bool = True
    ) -> Dict[str, Any]:
        """Check if required standard is met by available standards.
        
        Args:
            required: Required standard
            available: List of available standards
            allow_equivalents: Whether to accept equivalent standards
            
        Returns:
            Match result dictionary
        """
        required_norm = self.normalize_standard(required)
        available_norm = [self.normalize_standard(s) for s in available]
        
        # Direct match
        if required_norm in available_norm:
            return {
                'matched': True,
                'match_type': 'exact',
                'matched_standard': required_norm,
                'confidence': 1.0
            }
        
        # Check equivalents
        if allow_equivalents:
            equivalents = self.find_equivalent_standards(required_norm)
            for equiv in equivalents:
                if equiv in available_norm:
                    return {
                        'matched': True,
                        'match_type': 'equivalent',
                        'matched_standard': equiv,
                        'required_standard': required_norm,
                        'confidence': 0.95
                    }
        
        # Check partial matches (e.g., IS 694 matches IS 694-2010)
        for avail in available_norm:
            if required_norm in avail or avail in required_norm:
                return {
                    'matched': True,
                    'match_type': 'partial',
                    'matched_standard': avail,
                    'required_standard': required_norm,
                    'confidence': 0.85
                }
        
        return {
            'matched': False,
            'match_type': 'none',
            'required_standard': required_norm,
            'available_standards': available_norm,
            'confidence': 0.0
        }
    
    def get_standard_category(self, standard: str) -> Optional[str]:
        """Get category for a standard.
        
        Args:
            standard: Standard string
            
        Returns:
            Category name or None
        """
        standard_norm = self.normalize_standard(standard)
        
        for category, standards in self.standard_categories.items():
            if standard_norm in standards:
                return category
        
        return None
    
    def get_standards_by_category(self, category: str) -> List[str]:
        """Get all standards in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of standards in that category
        """
        return self.standard_categories.get(category, [])
    
    def compare_standard_sets(
        self,
        required: List[str],
        available: List[str]
    ) -> Dict[str, Any]:
        """Compare two sets of standards.
        
        Args:
            required: List of required standards
            available: List of available standards
            
        Returns:
            Comparison result
        """
        matched = []
        unmatched = []
        
        for req in required:
            result = self.check_standard_match(req, available)
            if result['matched']:
                matched.append(result)
            else:
                unmatched.append(req)
        
        coverage = len(matched) / len(required) * 100 if required else 100
        
        return {
            'matched_count': len(matched),
            'unmatched_count': len(unmatched),
            'total_required': len(required),
            'coverage_percentage': coverage,
            'matched_standards': matched,
            'unmatched_standards': unmatched,
            'fully_compliant': len(unmatched) == 0
        }
    
    def extract_standards_from_text(self, text: str) -> List[str]:
        """Extract standard references from text.
        
        Args:
            text: Text containing standard references
            
        Returns:
            List of extracted standards
        """
        if not text:
            return []
        
        standards = []
        
        # Pattern for IS/IEC/BS/EN standards
        patterns = [
            r'\b(IS|IEC|BS|EN)\s*[-/]?\s*(\d+)(?:\s*[-:]\s*(\d+))?\b',
            r'\b(IS|IEC|BS|EN)(\d+)\b',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                prefix = match.group(1).upper()
                number = match.group(2)
                part = match.group(3) if len(match.groups()) > 2 else None
                
                if part:
                    standard = f"{prefix} {number}-{part}"
                else:
                    standard = f"{prefix} {number}"
                
                standards.append(self.normalize_standard(standard))
        
        return list(set(standards))  # Remove duplicates
    
    def get_standard_info(self, standard: str) -> Dict[str, Any]:
        """Get information about a standard.
        
        Args:
            standard: Standard string
            
        Returns:
            Standard information dictionary
        """
        standard_norm = self.normalize_standard(standard)
        
        info = {
            'standard': standard_norm,
            'category': self.get_standard_category(standard_norm),
            'equivalents': self.find_equivalent_standards(standard_norm),
            'type': 'Indian' if standard_norm.startswith('IS') else 'International',
        }
        
        return info
    
    def validate_standard_compliance(
        self,
        product_standards: List[str],
        required_standards: List[str],
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate product compliance with required standards.
        
        Args:
            product_standards: Standards the product complies with
            required_standards: Standards required by RFP/specification
            category: Product category for context
            
        Returns:
            Validation result
        """
        comparison = self.compare_standard_sets(required_standards, product_standards)
        
        # Add category-specific validation
        if category:
            category_standards = self.get_standards_by_category(category)
            has_category_standard = any(
                self.normalize_standard(s) in category_standards
                for s in product_standards
            )
        else:
            has_category_standard = None
        
        validation = {
            'is_compliant': comparison['fully_compliant'],
            'compliance_score': comparison['coverage_percentage'],
            'matched_standards': comparison['matched_standards'],
            'missing_standards': comparison['unmatched_standards'],
            'total_required': comparison['total_required'],
            'total_matched': comparison['matched_count'],
            'category': category,
            'has_category_standard': has_category_standard,
            'recommendation': self._generate_compliance_recommendation(comparison, category)
        }
        
        return validation
    
    def _generate_compliance_recommendation(
        self,
        comparison: Dict[str, Any],
        category: Optional[str]
    ) -> str:
        """Generate compliance recommendation.
        
        Args:
            comparison: Comparison result
            category: Product category
            
        Returns:
            Recommendation text
        """
        if comparison['fully_compliant']:
            return "Product meets all required standards."
        
        coverage = comparison['coverage_percentage']
        
        if coverage >= 80:
            return f"Product meets {coverage:.0f}% of required standards. Minor gaps exist."
        elif coverage >= 50:
            return f"Product meets {coverage:.0f}% of required standards. Significant gaps need attention."
        else:
            return f"Product meets only {coverage:.0f}% of required standards. Major compliance issues."


# Global instance
_mapper_instance = None


def get_standard_mapper() -> StandardMapper:
    """Get global standard mapper instance.
    
    Returns:
        StandardMapper instance
    """
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = StandardMapper()
    return _mapper_instance
