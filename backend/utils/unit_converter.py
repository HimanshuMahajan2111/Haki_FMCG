"""Unit conversion utilities for various measurement types."""
from typing import Dict, Optional, Tuple
from decimal import Decimal, InvalidOperation
import re
import structlog

logger = structlog.get_logger()


class UnitConverter:
    """Convert between different units of measurement."""
    
    def __init__(self):
        """Initialize converter with conversion factors."""
        self.logger = logger.bind(component="UnitConverter")
        
        # Conversion factors to base units
        self.conversions = {
            'length': {
                'base_unit': 'mm',
                'factors': {
                    'mm': 1,
                    'cm': 10,
                    'm': 1000,
                    'km': 1000000,
                    'in': 25.4,
                    'inch': 25.4,
                    'ft': 304.8,
                    'feet': 304.8,
                    'yd': 914.4,
                    'yard': 914.4,
                    'mile': 1609344,
                }
            },
            'weight': {
                'base_unit': 'kg',
                'factors': {
                    'mg': 0.000001,
                    'g': 0.001,
                    'kg': 1,
                    'ton': 1000,
                    'tonne': 1000,
                    'oz': 0.0283495,
                    'lb': 0.453592,
                    'lbs': 0.453592,
                }
            },
            'voltage': {
                'base_unit': 'V',
                'factors': {
                    'mV': 0.001,
                    'V': 1,
                    'kV': 1000,
                }
            },
            'current': {
                'base_unit': 'A',
                'factors': {
                    'mA': 0.001,
                    'A': 1,
                    'kA': 1000,
                }
            },
            'power': {
                'base_unit': 'W',
                'factors': {
                    'mW': 0.001,
                    'W': 1,
                    'kW': 1000,
                    'MW': 1000000,
                    'hp': 745.7,  # horsepower
                }
            },
            'frequency': {
                'base_unit': 'Hz',
                'factors': {
                    'Hz': 1,
                    'kHz': 1000,
                    'MHz': 1000000,
                    'GHz': 1000000000,
                }
            },
            'temperature': {
                'base_unit': 'C',
                'factors': {
                    'C': None,  # Special conversion
                    'F': None,  # Special conversion
                    'K': None,  # Special conversion
                }
            },
            'area': {
                'base_unit': 'mm2',
                'factors': {
                    'mm2': 1,
                    'cm2': 100,
                    'm2': 1000000,
                    'sqmm': 1,
                    'sqcm': 100,
                    'sqm': 1000000,
                }
            },
            'resistance': {
                'base_unit': 'ohm',
                'factors': {
                    'mohm': 0.001,
                    'ohm': 1,
                    'kohm': 1000,
                    'Mohm': 1000000,
                }
            },
            'capacitance': {
                'base_unit': 'F',
                'factors': {
                    'pF': 1e-12,
                    'nF': 1e-9,
                    'uF': 1e-6,
                    'mF': 0.001,
                    'F': 1,
                }
            }
        }
    
    def convert(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
        measurement_type: Optional[str] = None
    ) -> Optional[float]:
        """Convert value from one unit to another.
        
        Args:
            value: Numeric value to convert
            from_unit: Source unit
            to_unit: Target unit
            measurement_type: Type of measurement (length, weight, etc.)
                             If None, will attempt to detect
            
        Returns:
            Converted value or None if conversion fails
        """
        try:
            # Detect measurement type if not provided
            if measurement_type is None:
                measurement_type = self._detect_measurement_type(from_unit, to_unit)
            
            if measurement_type is None:
                self.logger.warning(
                    "Could not detect measurement type",
                    from_unit=from_unit,
                    to_unit=to_unit
                )
                return None
            
            # Special handling for temperature
            if measurement_type == 'temperature':
                return self._convert_temperature(value, from_unit, to_unit)
            
            # Get conversion factors
            conversion_info = self.conversions.get(measurement_type)
            if not conversion_info:
                return None
            
            factors = conversion_info['factors']
            
            # Normalize unit names
            from_unit = self._normalize_unit(from_unit)
            to_unit = self._normalize_unit(to_unit)
            
            # Get factors
            from_factor = factors.get(from_unit)
            to_factor = factors.get(to_unit)
            
            if from_factor is None or to_factor is None:
                self.logger.warning(
                    "Unknown unit",
                    from_unit=from_unit,
                    to_unit=to_unit,
                    measurement_type=measurement_type
                )
                return None
            
            # Convert to base unit, then to target unit
            base_value = value * from_factor
            result = base_value / to_factor
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Conversion failed",
                error=str(e),
                value=value,
                from_unit=from_unit,
                to_unit=to_unit
            )
            return None
    
    def _convert_temperature(
        self,
        value: float,
        from_unit: str,
        to_unit: str
    ) -> float:
        """Convert temperature between C, F, and K.
        
        Args:
            value: Temperature value
            from_unit: Source unit (C, F, or K)
            to_unit: Target unit (C, F, or K)
            
        Returns:
            Converted temperature
        """
        from_unit = from_unit.upper()
        to_unit = to_unit.upper()
        
        # Convert to Celsius first
        if from_unit == 'C':
            celsius = value
        elif from_unit == 'F':
            celsius = (value - 32) * 5/9
        elif from_unit == 'K':
            celsius = value - 273.15
        else:
            return None
        
        # Convert from Celsius to target
        if to_unit == 'C':
            return celsius
        elif to_unit == 'F':
            return celsius * 9/5 + 32
        elif to_unit == 'K':
            return celsius + 273.15
        else:
            return None
    
    def _detect_measurement_type(
        self,
        from_unit: str,
        to_unit: str
    ) -> Optional[str]:
        """Detect measurement type from units.
        
        Args:
            from_unit: Source unit
            to_unit: Target unit
            
        Returns:
            Measurement type or None
        """
        from_unit = self._normalize_unit(from_unit)
        to_unit = self._normalize_unit(to_unit)
        
        for mtype, info in self.conversions.items():
            factors = info['factors']
            if from_unit in factors and to_unit in factors:
                return mtype
        
        return None
    
    def _normalize_unit(self, unit: str) -> str:
        """Normalize unit string.
        
        Args:
            unit: Unit string
            
        Returns:
            Normalized unit
        """
        # Remove spaces and special characters
        unit = unit.strip().replace(' ', '')
        
        # Handle common variations
        unit_map = {
            'volt': 'V',
            'volts': 'V',
            'amp': 'A',
            'amps': 'A',
            'ampere': 'A',
            'amperes': 'A',
            'watt': 'W',
            'watts': 'W',
            'hertz': 'Hz',
            'meter': 'm',
            'meters': 'm',
            'metre': 'm',
            'metres': 'm',
            'kilogram': 'kg',
            'kilograms': 'kg',
            'gram': 'g',
            'grams': 'g',
            'celsius': 'C',
            'fahrenheit': 'F',
            'kelvin': 'K',
            'inch': 'in',
            'inches': 'in',
            'foot': 'ft',
            'pound': 'lb',
            'pounds': 'lbs',
            'ω': 'ohm',
            '°c': 'C',
            '°f': 'F',
        }
        
        unit_lower = unit.lower()
        return unit_map.get(unit_lower, unit)
    
    def parse_value_with_unit(
        self,
        text: str
    ) -> Optional[Tuple[float, str, str]]:
        """Parse text to extract value, unit, and measurement type.
        
        Args:
            text: Text containing value and unit (e.g., "230V", "2.5 kg")
            
        Returns:
            Tuple of (value, unit, measurement_type) or None
        """
        # Pattern to match number with optional unit
        pattern = r'([\d.,]+)\s*([a-zA-Z°Ωµ]+)?'
        match = re.search(pattern, str(text))
        
        if not match:
            return None
        
        try:
            value = float(match.group(1).replace(',', ''))
            unit = match.group(2) if match.group(2) else ''
            
            if not unit:
                return (value, '', None)
            
            # Normalize unit
            normalized_unit = self._normalize_unit(unit)
            
            # Detect measurement type
            for mtype, info in self.conversions.items():
                if normalized_unit in info['factors']:
                    return (value, normalized_unit, mtype)
            
            return (value, normalized_unit, None)
            
        except ValueError:
            return None
    
    def convert_text(
        self,
        text: str,
        to_unit: str,
        measurement_type: Optional[str] = None
    ) -> Optional[str]:
        """Convert value with unit in text form to another unit.
        
        Args:
            text: Text with value and unit (e.g., "230V")
            to_unit: Target unit
            measurement_type: Type of measurement
            
        Returns:
            Converted text (e.g., "0.23kV") or None
        """
        parsed = self.parse_value_with_unit(text)
        if not parsed:
            return None
        
        value, from_unit, detected_type = parsed
        
        if not from_unit:
            return None
        
        mtype = measurement_type or detected_type
        converted = self.convert(value, from_unit, to_unit, mtype)
        
        if converted is None:
            return None
        
        # Format result
        if abs(converted) >= 1000:
            return f"{converted:.2f}{to_unit}"
        elif abs(converted) >= 10:
            return f"{converted:.1f}{to_unit}"
        else:
            return f"{converted:.3f}{to_unit}"
    
    def get_display_unit(
        self,
        value: float,
        measurement_type: str
    ) -> Tuple[float, str]:
        """Get appropriate display unit for a value.
        
        Args:
            value: Value in base unit
            measurement_type: Type of measurement
            
        Returns:
            Tuple of (converted_value, unit) for display
        """
        conversion_info = self.conversions.get(measurement_type)
        if not conversion_info:
            return (value, '')
        
        base_unit = conversion_info['base_unit']
        factors = conversion_info['factors']
        
        # Find best unit for display (closest to 1-1000 range)
        best_unit = base_unit
        best_value = value
        best_score = float('inf')
        
        for unit, factor in factors.items():
            if factor is None:  # Skip special conversions
                continue
            
            converted = value / factor
            
            # Score based on closeness to 1-1000 range
            if 1 <= abs(converted) < 1000:
                score = 0
            elif abs(converted) < 1:
                score = 1 / abs(converted) if converted != 0 else float('inf')
            else:
                score = abs(converted) / 1000
            
            if score < best_score:
                best_score = score
                best_value = converted
                best_unit = unit
        
        return (best_value, best_unit)
    
    def standardize_to_base_unit(
        self,
        value: float,
        unit: str,
        measurement_type: str
    ) -> Optional[float]:
        """Convert any unit to the base unit for that measurement type.
        
        Args:
            value: Numeric value
            unit: Current unit
            measurement_type: Type of measurement
            
        Returns:
            Value in base unit or None
        """
        conversion_info = self.conversions.get(measurement_type)
        if not conversion_info:
            return None
        
        base_unit = conversion_info['base_unit']
        return self.convert(value, unit, base_unit, measurement_type)


# Global instance
_converter_instance = None


def get_converter() -> UnitConverter:
    """Get global converter instance.
    
    Returns:
        UnitConverter instance
    """
    global _converter_instance
    if _converter_instance is None:
        _converter_instance = UnitConverter()
    return _converter_instance
