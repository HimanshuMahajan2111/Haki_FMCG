"""
Specification Parser - Parse technical specifications from RFP text.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import re
import structlog

logger = structlog.get_logger()


@dataclass
class Specification:
    """Technical specification."""
    category: str
    parameter: str
    value: str
    unit: Optional[str] = None
    requirement_type: str = "mandatory"  # mandatory, preferred, optional
    source_text: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'category': self.category,
            'parameter': self.parameter,
            'value': self.value,
            'unit': self.unit,
            'requirement_type': self.requirement_type,
            'source_text': self.source_text
        }


class SpecificationParser:
    """Parse technical specifications from RFP text."""
    
    def __init__(self):
        """Initialize specification parser."""
        self.logger = logger.bind(component="SpecificationParser")
        
        # Common specification patterns
        self.spec_patterns = {
            'voltage': r'(?:voltage|rated\s*voltage)[:\s]*(\d+)\s*(V|volts?)',
            'power': r'(?:power|wattage)[:\s]*(\d+\.?\d*)\s*(W|KW|watts?|kilowatts?)',
            'current': r'(?:current|amperage)[:\s]*(\d+\.?\d*)\s*(A|amps?)',
            'frequency': r'(?:frequency)[:\s]*(\d+)\s*(Hz)',
            'capacity': r'(?:capacity|volume)[:\s]*(\d+\.?\d*)\s*(L|litre|liter|ton)',
            'size': r'(?:size|dimensions?)[:\s]*(\d+\.?\d*)\s*(?:x\s*\d+\.?\d*)?\s*(mm|cm|m|inch)',
            'temperature': r'(?:temperature|temp)[:\s]*(-?\d+\.?\d*)\s*(?:to\s*-?\d+\.?\d*)?\s*(°C|C|celsius)',
            'pressure': r'(?:pressure)[:\s]*(\d+\.?\d*)\s*(bar|psi|kpa)',
            'rating': r'(\d+)\s*star\s*rating',
            'efficiency': r'(?:efficiency)[:\s]*(\d+\.?\d*)\s*(%|percent)',
        }
        
        # Requirement keywords
        self.requirement_keywords = {
            'mandatory': ['must', 'shall', 'required', 'mandatory', 'essential'],
            'preferred': ['should', 'preferred', 'desirable', 'recommended'],
            'optional': ['may', 'optional', 'can', 'if possible']
        }
    
    def parse(self, text: str, category: str = "general") -> List[Specification]:
        """Parse specifications from text.
        
        Args:
            text: Text content containing specifications
            category: Category of specifications
            
        Returns:
            List of Specification objects
        """
        self.logger.info("Parsing specifications", category=category, text_length=len(text))
        
        specifications = []
        
        # Extract specifications using patterns
        for param_name, pattern in self.spec_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                value = match.group(1)
                unit = match.group(2) if match.lastindex >= 2 else None
                
                # Determine requirement type from context
                requirement_type = self._determine_requirement_type(text, match.start())
                
                spec = Specification(
                    category=category,
                    parameter=param_name,
                    value=value,
                    unit=unit,
                    requirement_type=requirement_type,
                    source_text=match.group(0)
                )
                
                specifications.append(spec)
        
        # Extract custom specifications (key: value format)
        custom_specs = self._extract_custom_specs(text, category)
        specifications.extend(custom_specs)
        
        self.logger.info("Specifications parsed", count=len(specifications))
        
        return specifications
    
    def _determine_requirement_type(self, text: str, position: int) -> str:
        """Determine requirement type from context.
        
        Args:
            text: Full text
            position: Position of specification in text
            
        Returns:
            Requirement type: mandatory, preferred, or optional
        """
        # Look at surrounding text (100 chars before)
        start = max(0, position - 100)
        context = text[start:position].lower()
        
        # Check for requirement keywords
        for req_type, keywords in self.requirement_keywords.items():
            if any(keyword in context for keyword in keywords):
                return req_type
        
        return "mandatory"  # Default
    
    def _extract_custom_specs(self, text: str, category: str) -> List[Specification]:
        """Extract custom specifications in key-value format.
        
        Args:
            text: Text content
            category: Category name
            
        Returns:
            List of Specification objects
        """
        specs = []
        
        # Pattern: "Parameter: Value" or "Parameter - Value"
        pattern = r'([A-Z][A-Za-z\s]+?)[:\-]\s*(.+?)(?:\n|$)'
        matches = re.finditer(pattern, text, re.MULTILINE)
        
        for match in matches:
            parameter = match.group(1).strip()
            value_text = match.group(2).strip()
            
            # Skip if it looks like a section heading or too long
            if len(parameter) > 50 or len(value_text) > 200:
                continue
            
            # Try to extract unit from value
            unit_match = re.search(r'(\d+\.?\d*)\s*([A-Za-z%]+)$', value_text)
            if unit_match:
                value = unit_match.group(1)
                unit = unit_match.group(2)
            else:
                value = value_text
                unit = None
            
            requirement_type = self._determine_requirement_type(text, match.start())
            
            spec = Specification(
                category=category,
                parameter=parameter,
                value=value,
                unit=unit,
                requirement_type=requirement_type,
                source_text=match.group(0)
            )
            
            specs.append(spec)
        
        return specs
    
    def parse_by_sections(
        self,
        text: str,
        section_headings: List[str]
    ) -> Dict[str, List[Specification]]:
        """Parse specifications organized by sections.
        
        Args:
            text: Full RFP text
            section_headings: List of section headings to look for
            
        Returns:
            Dictionary mapping section names to specifications
        """
        sections_specs = {}
        
        for section_name in section_headings:
            # Find section text
            section_text = self._extract_section(text, section_name)
            
            if section_text:
                specs = self.parse(section_text, category=section_name)
                if specs:
                    sections_specs[section_name] = specs
        
        return sections_specs
    
    def _extract_section(self, text: str, section_name: str) -> Optional[str]:
        """Extract a section from text.
        
        Args:
            text: Full text
            section_name: Section heading
            
        Returns:
            Section text or None
        """
        # Try various heading patterns
        patterns = [
            rf"(?i)^{re.escape(section_name)}[\s:]*$",
            rf"(?i)\n{re.escape(section_name)}[\s:]*\n",
            rf"(?i)^\d+\.?\s*{re.escape(section_name)}",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                start_pos = match.end()
                
                # Find next section
                next_section = re.search(r'\n\d+\.?\s+[A-Z]', text[start_pos:])
                
                if next_section:
                    end_pos = start_pos + next_section.start()
                    return text[start_pos:end_pos].strip()
                else:
                    return text[start_pos:].strip()
        
        return None
    
    def group_by_category(
        self,
        specifications: List[Specification]
    ) -> Dict[str, List[Specification]]:
        """Group specifications by category.
        
        Args:
            specifications: List of specifications
            
        Returns:
            Dictionary mapping categories to specifications
        """
        grouped = {}
        
        for spec in specifications:
            category = spec.category
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(spec)
        
        return grouped
    
    def filter_by_requirement(
        self,
        specifications: List[Specification],
        requirement_type: str
    ) -> List[Specification]:
        """Filter specifications by requirement type.
        
        Args:
            specifications: List of specifications
            requirement_type: Type to filter (mandatory, preferred, optional)
            
        Returns:
            Filtered specifications
        """
        return [spec for spec in specifications if spec.requirement_type == requirement_type]
    
    def to_dict_list(self, specifications: List[Specification]) -> List[Dict[str, Any]]:
        """Convert specifications to list of dictionaries.
        
        Args:
            specifications: List of Specification objects
            
        Returns:
            List of dictionaries
        """
        return [spec.to_dict() for spec in specifications]
