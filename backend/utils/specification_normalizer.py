"""Specification normalization utilities for standardizing product specifications."""
from typing import Dict, Any, Optional, List, Union
import re
from decimal import Decimal, InvalidOperation
import structlog

logger = structlog.get_logger()


class SpecificationNormalizer:
    """Normalize and standardize product specifications."""
    
    def __init__(self):
        """Initialize normalizer."""
        self.logger = logger.bind(component="SpecificationNormalizer")
    
    def normalize_specifications(
        self,
        specs: Dict[str, Any],
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Normalize all specifications in a dictionary.
        
        Args:
            specs: Dictionary of specifications
            category: Product category for context-aware normalization
            
        Returns:
            Normalized specifications dictionary
        """
        normalized = {}
        
        for key, value in specs.items():
            norm_key = self.normalize_key(key)
            norm_value = self.normalize_value(value, norm_key, category)
            normalized[norm_key] = norm_value
        
        return normalized
    
    def normalize_key(self, key: str) -> str:
        """Normalize specification key names.
        
        Args:
            key: Original key name
            
        Returns:
            Normalized key name
        """
        if not isinstance(key, str):
            return str(key)
        
        # Convert to lowercase
        key = key.lower().strip()
        
        # Remove special characters except underscore
        key = re.sub(r'[^\w\s-]', '', key)
        
        # Replace spaces and hyphens with underscores
        key = re.sub(r'[-\s]+', '_', key)
        
        # Remove multiple underscores
        key = re.sub(r'_+', '_', key)
        
        # Remove leading/trailing underscores
        key = key.strip('_')
        
        # Map common variations to standard names
        key_mappings = {
            'volt': 'voltage',
            'volts': 'voltage',
            'amp': 'amperage',
            'amps': 'amperage',
            'ampere': 'amperage',
            'amperes': 'amperage',
            'current': 'amperage',
            'watt': 'wattage',
            'watts': 'wattage',
            'power': 'wattage',
            'freq': 'frequency',
            'hz': 'frequency',
            'temp': 'temperature',
            'conductor': 'conductors',
            'core': 'cores',
            'diameter': 'dia',
            'length': 'len',
            'weight': 'wt',
            'colour': 'color',
            'colour_code': 'color_code',
            'insulation': 'insulation_material',
            'sheath': 'sheath_material',
        }
        
        return key_mappings.get(key, key)
    
    def normalize_value(
        self,
        value: Any,
        key: str,
        category: Optional[str] = None
    ) -> Any:
        """Normalize specification values.
        
        Args:
            value: Original value
            key: Normalized key name
            category: Product category
            
        Returns:
            Normalized value
        """
        if value is None or value == '':
            return None
        
        # Convert to string for processing
        if not isinstance(value, str):
            return value
        
        value = value.strip()
        
        # Normalize based on key type
        if any(k in key for k in ['voltage', 'volt']):
            return self._normalize_voltage(value)
        elif any(k in key for k in ['amperage', 'current', 'amp']):
            return self._normalize_amperage(value)
        elif any(k in key for k in ['wattage', 'power', 'watt']):
            return self._normalize_wattage(value)
        elif any(k in key for k in ['frequency', 'freq']):
            return self._normalize_frequency(value)
        elif any(k in key for k in ['temperature', 'temp']):
            return self._normalize_temperature(value)
        elif any(k in key for k in ['length', 'width', 'height', 'depth', 'diameter', 'dia']):
            return self._normalize_dimension(value)
        elif any(k in key for k in ['weight', 'wt']):
            return self._normalize_weight(value)
        elif any(k in key for k in ['color', 'colour']):
            return self._normalize_color(value)
        elif key in ['conductors', 'cores', 'poles', 'ways']:
            return self._normalize_count(value)
        else:
            return self._normalize_text(value)
    
    def _normalize_voltage(self, value: str) -> Dict[str, Any]:
        """Normalize voltage values.
        
        Args:
            value: Voltage string (e.g., '230V', '415V', '11kV')
            
        Returns:
            Normalized voltage dict with value and unit
        """
        # Extract numeric value and unit
        match = re.search(r'([\d.]+)\s*([kKmM]?)[vV]?', value)
        if not match:
            return {'raw': value, 'normalized': None}
        
        num_value = float(match.group(1))
        unit_prefix = match.group(2).upper() if match.group(2) else ''
        
        # Convert to base unit (Volts)
        multipliers = {'K': 1000, 'M': 1000000, '': 1}
        base_value = num_value * multipliers.get(unit_prefix, 1)
        
        return {
            'value': base_value,
            'unit': 'V',
            'display': f"{base_value:.0f}V" if base_value < 1000 else f"{base_value/1000:.1f}kV",
            'raw': value
        }
    
    def _normalize_amperage(self, value: str) -> Dict[str, Any]:
        """Normalize current/amperage values.
        
        Args:
            value: Current string (e.g., '16A', '32 Amp', '100mA')
            
        Returns:
            Normalized current dict
        """
        match = re.search(r'([\d.]+)\s*([mM]?)[aA](?:mp)?', value)
        if not match:
            return {'raw': value, 'normalized': None}
        
        num_value = float(match.group(1))
        unit_prefix = match.group(2).upper() if match.group(2) else ''
        
        # Convert to base unit (Amperes)
        multipliers = {'M': 0.001, '': 1}
        base_value = num_value * multipliers.get(unit_prefix, 1)
        
        return {
            'value': base_value,
            'unit': 'A',
            'display': f"{base_value:.1f}A" if base_value >= 1 else f"{base_value*1000:.0f}mA",
            'raw': value
        }
    
    def _normalize_wattage(self, value: str) -> Dict[str, Any]:
        """Normalize power/wattage values.
        
        Args:
            value: Power string (e.g., '1000W', '1.5kW', '100 Watts')
            
        Returns:
            Normalized power dict
        """
        match = re.search(r'([\d.]+)\s*([kKmM]?)[wW](?:att)?s?', value)
        if not match:
            return {'raw': value, 'normalized': None}
        
        num_value = float(match.group(1))
        unit_prefix = match.group(2).upper() if match.group(2) else ''
        
        # Convert to base unit (Watts)
        multipliers = {'K': 1000, 'M': 1000000, 'M': 0.001, '': 1}
        base_value = num_value * multipliers.get(unit_prefix, 1)
        
        return {
            'value': base_value,
            'unit': 'W',
            'display': f"{base_value:.0f}W" if base_value < 1000 else f"{base_value/1000:.2f}kW",
            'raw': value
        }
    
    def _normalize_frequency(self, value: str) -> Dict[str, Any]:
        """Normalize frequency values.
        
        Args:
            value: Frequency string (e.g., '50Hz', '60 Hz')
            
        Returns:
            Normalized frequency dict
        """
        match = re.search(r'([\d.]+)\s*([kKmMgG]?)[hH][zZ]?', value)
        if not match:
            return {'raw': value, 'normalized': None}
        
        num_value = float(match.group(1))
        unit_prefix = match.group(2).upper() if match.group(2) else ''
        
        multipliers = {'K': 1000, 'M': 1000000, 'G': 1000000000, '': 1}
        base_value = num_value * multipliers.get(unit_prefix, 1)
        
        return {
            'value': base_value,
            'unit': 'Hz',
            'display': f"{base_value:.0f}Hz",
            'raw': value
        }
    
    def _normalize_temperature(self, value: str) -> Dict[str, Any]:
        """Normalize temperature values.
        
        Args:
            value: Temperature string (e.g., '70°C', '158F', '343K')
            
        Returns:
            Normalized temperature dict in Celsius
        """
        # Try different patterns
        match = re.search(r'([\d.]+)\s*°?([CcFfKk])', value)
        if not match:
            return {'raw': value, 'normalized': None}
        
        num_value = float(match.group(1))
        unit = match.group(2).upper()
        
        # Convert to Celsius
        if unit == 'F':
            celsius = (num_value - 32) * 5/9
        elif unit == 'K':
            celsius = num_value - 273.15
        else:
            celsius = num_value
        
        return {
            'value': celsius,
            'unit': '°C',
            'display': f"{celsius:.1f}°C",
            'raw': value
        }
    
    def _normalize_dimension(self, value: str) -> Dict[str, Any]:
        """Normalize dimension values (length, width, etc.).
        
        Args:
            value: Dimension string (e.g., '100mm', '2.5m', '10 inches')
            
        Returns:
            Normalized dimension dict in millimeters
        """
        # Try various patterns
        patterns = [
            r'([\d.]+)\s*mm',
            r'([\d.]+)\s*cm',
            r'([\d.]+)\s*m(?!m)',
            r'([\d.]+)\s*inch(?:es)?',
            r'([\d.]+)\s*ft',
            r'([\d.]+)\s*\'',
            r'([\d.]+)\s*"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, value, re.IGNORECASE)
            if match:
                num_value = float(match.group(1))
                matched_text = match.group(0).lower()
                
                # Convert to mm
                if 'mm' in matched_text:
                    mm_value = num_value
                elif 'cm' in matched_text:
                    mm_value = num_value * 10
                elif 'm' in matched_text and 'mm' not in matched_text:
                    mm_value = num_value * 1000
                elif 'inch' in matched_text or '"' in matched_text:
                    mm_value = num_value * 25.4
                elif 'ft' in matched_text or "'" in matched_text:
                    mm_value = num_value * 304.8
                else:
                    mm_value = num_value
                
                return {
                    'value': mm_value,
                    'unit': 'mm',
                    'display': f"{mm_value:.1f}mm" if mm_value < 1000 else f"{mm_value/1000:.2f}m",
                    'raw': value
                }
        
        return {'raw': value, 'normalized': None}
    
    def _normalize_weight(self, value: str) -> Dict[str, Any]:
        """Normalize weight values.
        
        Args:
            value: Weight string (e.g., '100g', '2.5kg', '10 lbs')
            
        Returns:
            Normalized weight dict in kilograms
        """
        patterns = [
            (r'([\d.]+)\s*kg', 1),
            (r'([\d.]+)\s*g(?!s)', 0.001),
            (r'([\d.]+)\s*mg', 0.000001),
            (r'([\d.]+)\s*lbs?', 0.453592),
            (r'([\d.]+)\s*oz', 0.0283495),
        ]
        
        for pattern, multiplier in patterns:
            match = re.search(pattern, value, re.IGNORECASE)
            if match:
                num_value = float(match.group(1))
                kg_value = num_value * multiplier
                
                return {
                    'value': kg_value,
                    'unit': 'kg',
                    'display': f"{kg_value:.3f}kg" if kg_value < 1 else f"{kg_value:.2f}kg",
                    'raw': value
                }
        
        return {'raw': value, 'normalized': None}
    
    def _normalize_color(self, value: str) -> str:
        """Normalize color names.
        
        Args:
            value: Color string
            
        Returns:
            Normalized color name
        """
        color_map = {
            'red': 'red',
            'blue': 'blue',
            'green': 'green',
            'yellow': 'yellow',
            'black': 'black',
            'white': 'white',
            'brown': 'brown',
            'grey': 'gray',
            'gray': 'gray',
            'orange': 'orange',
            'purple': 'purple',
            'violet': 'purple',
            'pink': 'pink',
        }
        
        value_lower = value.lower().strip()
        for key, normalized in color_map.items():
            if key in value_lower:
                return normalized
        
        return value.strip().title()
    
    def _normalize_count(self, value: str) -> int:
        """Normalize count values (cores, poles, etc.).
        
        Args:
            value: Count string
            
        Returns:
            Integer count
        """
        # Extract first number
        match = re.search(r'(\d+)', value)
        if match:
            return int(match.group(1))
        return None
    
    def _normalize_text(self, value: str) -> str:
        """Normalize general text values.
        
        Args:
            value: Text string
            
        Returns:
            Normalized text
        """
        # Remove extra whitespace
        value = re.sub(r'\s+', ' ', value).strip()
        
        # Capitalize appropriately
        if len(value) > 0 and value.isupper():
            # Keep acronyms uppercase
            if len(value) <= 5:
                return value
            # Title case for longer strings
            return value.title()
        
        return value
    
    def extract_numeric_value(self, text: str) -> Optional[float]:
        """Extract first numeric value from text.
        
        Args:
            text: Text containing numbers
            
        Returns:
            First numeric value found or None
        """
        match = re.search(r'([\d,]+\.?\d*)', str(text))
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except ValueError:
                return None
        return None
    
    def compare_specifications(
        self,
        spec1: Dict[str, Any],
        spec2: Dict[str, Any],
        tolerance: float = 0.05
    ) -> Dict[str, Any]:
        """Compare two specification dictionaries.
        
        Args:
            spec1: First specification dict
            spec2: Second specification dict
            tolerance: Tolerance for numeric comparisons (5% default)
            
        Returns:
            Comparison result with match score
        """
        # Normalize both specs
        norm_spec1 = self.normalize_specifications(spec1)
        norm_spec2 = self.normalize_specifications(spec2)
        
        all_keys = set(norm_spec1.keys()) | set(norm_spec2.keys())
        matches = 0
        mismatches = []
        
        for key in all_keys:
            val1 = norm_spec1.get(key)
            val2 = norm_spec2.get(key)
            
            if val1 is None or val2 is None:
                mismatches.append({
                    'key': key,
                    'reason': 'missing_in_one',
                    'value1': val1,
                    'value2': val2
                })
                continue
            
            # Compare based on type
            if isinstance(val1, dict) and 'value' in val1:
                # Compare normalized numeric values
                if isinstance(val2, dict) and 'value' in val2:
                    diff = abs(val1['value'] - val2['value'])
                    threshold = val1['value'] * tolerance
                    if diff <= threshold:
                        matches += 1
                    else:
                        mismatches.append({
                            'key': key,
                            'reason': 'value_mismatch',
                            'value1': val1,
                            'value2': val2,
                            'difference': diff
                        })
            else:
                # Direct comparison
                if str(val1).lower() == str(val2).lower():
                    matches += 1
                else:
                    mismatches.append({
                        'key': key,
                        'reason': 'value_mismatch',
                        'value1': val1,
                        'value2': val2
                    })
        
        match_score = (matches / len(all_keys) * 100) if all_keys else 0
        
        return {
            'match_score': match_score,
            'matches': matches,
            'total_keys': len(all_keys),
            'mismatches': mismatches,
            'spec1_normalized': norm_spec1,
            'spec2_normalized': norm_spec2
        }


# Global instance
_normalizer_instance = None


def get_normalizer() -> SpecificationNormalizer:
    """Get global normalizer instance.
    
    Returns:
        SpecificationNormalizer instance
    """
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = SpecificationNormalizer()
    return _normalizer_instance
