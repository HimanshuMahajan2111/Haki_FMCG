"""Parameter extraction and normalization utilities."""
from typing import Dict, Any, List, Optional
import re
import structlog

logger = structlog.get_logger()


class ParameterExtractor:
    """Extract and normalize parameters from specifications."""
    
    def __init__(self):
        """Initialize parameter extractor."""
        self.logger = logger.bind(component="ParameterExtractor")
        
        # Common parameter name mappings
        self.parameter_aliases = {
            'voltage': ['voltage_rating', 'rated_voltage', 'nominal_voltage', 'voltage', 'volt'],
            'current': ['current_rating', 'rated_current', 'amperage', 'current', 'amp'],
            'power': ['power_rating', 'rated_power', 'wattage', 'power', 'watt'],
            'frequency': ['frequency', 'freq', 'hz'],
            'phase': ['phase', 'phases', 'no_of_phases'],
            'conductor_size': ['conductor_size', 'core_size', 'cable_size', 'size'],
            'core_count': ['core_count', 'number_of_cores', 'cores', 'no_of_cores'],
            'insulation': ['insulation_type', 'insulation', 'insulation_material'],
            'conductor_material': ['conductor_material', 'conductor', 'conductor_type', 'material'],
            'sheath_material': ['sheath_material', 'sheath', 'sheath_type', 'outer_sheath'],
            'armour_material': ['armour_material', 'armour', 'armour_type', 'armouring'],
            'standard': ['standard', 'standards', 'compliance_standard'],
            'certification': ['certification', 'certifications', 'bis', 'bis_registration']
        }
        
        # Units to extract and normalize
        self.unit_patterns = {
            'voltage': r'(\d+(?:\.\d+)?)\s*(?:kV|kv|KV|V|v|volt|volts)',
            'current': r'(\d+(?:\.\d+)?)\s*(?:A|a|amp|amps|ampere|amperes|mA|ma)',
            'power': r'(\d+(?:\.\d+)?)\s*(?:kW|kw|KW|W|w|watt|watts|HP|hp)',
            'frequency': r'(\d+(?:\.\d+)?)\s*(?:Hz|hz|HZ)',
            'temperature': r'(\d+(?:\.\d+)?)\s*(?:°C|C|celsius)',
            'size': r'(\d+(?:\.\d+)?)\s*(?:mm|cm|m|sq\.?mm)'
        }
    
    def extract_parameters(
        self,
        specs: Dict[str, Any],
        category: str = "default"
    ) -> Dict[str, Any]:
        """Extract and normalize parameters from specifications.
        
        Args:
            specs: Specification dictionary
            category: Product category for specialized extraction
            
        Returns:
            Dictionary of normalized parameters
        """
        extracted = {}
        
        # Direct extraction from known fields
        for canonical_name, aliases in self.parameter_aliases.items():
            for alias in aliases:
                if alias in specs:
                    value = specs[alias]
                    if value is not None:
                        extracted[canonical_name] = self._normalize_parameter_value(
                            canonical_name,
                            value
                        )
                        break
        
        # Extract from nested specifications dict
        if 'specifications' in specs and isinstance(specs['specifications'], dict):
            nested_params = self.extract_parameters(specs['specifications'], category)
            extracted.update(nested_params)
        
        # Extract from text fields
        text_fields = ['description', 'technical_details', 'features']
        for field in text_fields:
            if field in specs and isinstance(specs[field], str):
                text_params = self._extract_from_text(specs[field])
                # Only add if not already present
                for key, value in text_params.items():
                    if key not in extracted:
                        extracted[key] = value
        
        # Category-specific extraction
        if category != "default":
            extracted = self._apply_category_specific_rules(extracted, specs, category)
        
        self.logger.debug(
            "Extracted parameters",
            count=len(extracted),
            category=category
        )
        
        return extracted
    
    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """Extract parameters from text using patterns.
        
        Args:
            text: Text to extract from
            
        Returns:
            Dictionary of extracted parameters
        """
        extracted = {}
        
        for param_name, pattern in self.unit_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = float(match.group(1))
                unit = match.group(0).replace(match.group(1), '').strip()
                
                # Store with unit information
                if param_name not in extracted:
                    extracted[param_name] = {
                        'value': value,
                        'unit': unit,
                        'raw': match.group(0)
                    }
        
        return extracted
    
    def _normalize_parameter_value(
        self,
        param_name: str,
        value: Any
    ) -> Any:
        """Normalize a parameter value.
        
        Args:
            param_name: Name of parameter
            value: Value to normalize
            
        Returns:
            Normalized value
        """
        if value is None:
            return None
        
        # Handle dictionary values (with units)
        if isinstance(value, dict):
            if 'value' in value:
                return value['value']
            return value
        
        # Handle numeric strings with units
        if isinstance(value, str):
            value_str = value.strip()
            
            # Try to extract number from strings like "32 A", "1.1 kV", "10 sq.mm"
            match = re.search(r'[-+]?[0-9]*\.?[0-9]+', value_str)
            if match:
                try:
                    numeric_value = float(match.group())
                    
                    # Check for units in the string
                    unit_match = re.search(r'[a-zA-Z]+', value_str)
                    
                    # For voltage, current, power parameters, return just the numeric value
                    # The unit conversion will be handled separately
                    if any(keyword in param_name.lower() for keyword in ['voltage', 'current', 'power', 'frequency', 'size', 'watt', 'amp', 'volt']):
                        return numeric_value
                    
                    # For other parameters with units, return as dict
                    if unit_match:
                        return {
                            'value': numeric_value,
                            'unit': unit_match.group(),
                            'raw': value_str
                        }
                    
                    # Just numeric value without unit
                    return numeric_value
                except ValueError:
                    pass
            
            # Return cleaned string
            return value_str.lower()
        
        return value
    
    def _apply_category_specific_rules(
        self,
        extracted: Dict[str, Any],
        specs: Dict[str, Any],
        category: str
    ) -> Dict[str, Any]:
        """Apply category-specific extraction rules.
        
        Args:
            extracted: Already extracted parameters
            specs: Original specifications
            category: Product category
            
        Returns:
            Enhanced parameter dictionary
        """
        if category == 'cable':
            # Extract cable-specific parameters
            if 'cable_type' in specs:
                extracted['cable_type'] = specs['cable_type']
            
            if 'armoured' in specs:
                extracted['armoured'] = specs['armoured']
            
            # Derive parameters
            if 'core_count' in extracted and 'conductor_size' in extracted:
                extracted['cable_designation'] = f"{extracted['core_count']}C x {extracted['conductor_size']}"
        
        elif category == 'motor':
            # Extract motor-specific parameters
            if 'rpm' in specs:
                extracted['rpm'] = specs['rpm']
            
            if 'efficiency_class' in specs:
                extracted['efficiency_class'] = specs['efficiency_class']
            
            if 'mounting_type' in specs:
                extracted['mounting_type'] = specs['mounting_type']
        
        elif category == 'switchgear':
            # Extract switchgear-specific parameters
            if 'breaking_capacity' in specs:
                extracted['breaking_capacity'] = specs['breaking_capacity']
            
            if 'poles' in specs:
                extracted['poles'] = specs['poles']
            
            if 'trip_curve' in specs:
                extracted['trip_curve'] = specs['trip_curve']
        
        return extracted
    
    def extract_critical_parameters(
        self,
        specs: Dict[str, Any],
        category: str
    ) -> List[str]:
        """Extract list of critical parameter names.
        
        Args:
            specs: Specifications dictionary
            category: Product category
            
        Returns:
            List of critical parameter names
        """
        # Define critical parameters by category
        critical_by_category = {
            'cable': ['voltage', 'conductor_size', 'core_count'],
            'motor': ['power', 'voltage', 'frequency', 'rpm'],
            'switchgear': ['voltage', 'current', 'breaking_capacity'],
            'fan': ['sweep_size', 'power'],
            'lighting': ['wattage', 'voltage'],
            'default': ['voltage', 'current', 'power']
        }
        
        critical_params = critical_by_category.get(category, critical_by_category['default'])
        
        # Return only those that exist in specs
        extracted = self.extract_parameters(specs, category)
        return [param for param in critical_params if param in extracted]
    
    def validate_extracted_parameters(
        self,
        params: Dict[str, Any],
        required_params: List[str]
    ) -> Dict[str, Any]:
        """Validate that required parameters are present.
        
        Args:
            params: Extracted parameters
            required_params: List of required parameter names
            
        Returns:
            Validation result dictionary
        """
        missing = [p for p in required_params if p not in params]
        present = [p for p in required_params if p in params]
        
        return {
            'valid': len(missing) == 0,
            'missing': missing,
            'present': present,
            'completeness': len(present) / len(required_params) if required_params else 1.0
        }
